from datetime import datetime, timedelta
from typing import Annotated
import json
import urllib.parse
import urllib.request
from asset_management.app.auth.repositories import AuthRepository
from asset_management.app.auth.settings import AUTH_SETTINGS
from asset_management.app.auth.utils import issue_token, verify_password, verify_token, needs_password_migration, hash_password
from fastapi import Depends, HTTPException, Header, status
from asset_management.app.user.models import User


class AuthServices:
  def __init__(self, auth_repository: Annotated[AuthRepository, Depends()]):
    self.auth_repository = auth_repository
    
  def issue_token(self, user_id: int):
    tokens = issue_token(user_id)
    self.auth_repository.add_refresh_token(
      tokens["refresh_token"],
      user_id,
      datetime.now() + timedelta(minutes=AUTH_SETTINGS.LONG_SESSION_LIFESPAN),
    )
    return tokens
  
  def login_user(self, email: str, password: str):
    user = self.auth_repository.get_user_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
      )
    
    # SHA-256에서 argon2로 점진적 마이그레이션
    if needs_password_migration(user.hashed_password):
      user.hashed_password = hash_password(password)
      self.auth_repository.db_session.commit()
    
    user_name = user.name
    user_type = user.is_admin
    return {"user_name": user_name, "user_type": user_type, "tokens": self.issue_token(user.id)}

  def _verify_google_id_token(self, id_token: str) -> dict:
    if not AUTH_SETTINGS.GOOGLE_CLIENT_ID:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Google client ID not configured",
      )

    tokeninfo_url = "https://oauth2.googleapis.com/tokeninfo"
    url = f"{tokeninfo_url}?id_token={urllib.parse.quote(id_token)}"
    try:
      with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    except Exception:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Google ID token",
      )

    if data.get("aud") != AUTH_SETTINGS.GOOGLE_CLIENT_ID:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Google token audience",
      )
    if data.get("email_verified") not in ["true", True]:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Google email not verified",
      )
    if "email" not in data:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Google email missing",
      )
    return data

  def _exchange_google_code_for_tokens(self, code: str, code_verifier: str, redirect_uri: str) -> dict:
    if not AUTH_SETTINGS.GOOGLE_CLIENT_ID:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Google client ID not configured",
      )
    if not AUTH_SETTINGS.GOOGLE_CLIENT_SECRET:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Google client secret not configured",
      )

    token_url = "https://oauth2.googleapis.com/token"
    payload = urllib.parse.urlencode(
      {
        "code": code,
        "client_id": AUTH_SETTINGS.GOOGLE_CLIENT_ID,
        "client_secret": AUTH_SETTINGS.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
      }
    ).encode("utf-8")
    request = urllib.request.Request(
      token_url,
      data=payload,
      headers={"Content-Type": "application/x-www-form-urlencoded"},
      method="POST",
    )
    try:
      with urllib.request.urlopen(request, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    except Exception:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Google authorization code",
      )
    if "error" in data:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Google token exchange failed",
      )
    return data

  def login_google(self, code: str, code_verifier: str, redirect_uri: str):
    try:
      token_data = self._exchange_google_code_for_tokens(code, code_verifier, redirect_uri)
    except HTTPException as exc:
      if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=exc.detail,
        )
      raise
    id_token = token_data.get("id_token")
    if not id_token:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Google ID token missing",
      )
    data = self._verify_google_id_token(id_token)
    email = data["email"]

    user = self.auth_repository.get_user_by_social_email(email)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Linked Google account not found",
      )

    if user:
      if user.is_admin:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Admin account cannot use social login",
        )
      return {
        "user_name": user.name,
        "user_type": user.is_admin,
        "tokens": self.issue_token(user.id),
      }

  def link_google(self, user: User, code: str, code_verifier: str, redirect_uri: str):
    if user.is_admin:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Admin account cannot use social login",
      )
    if user.social_email:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Google account already linked",
      )
    token_data = self._exchange_google_code_for_tokens(code, code_verifier, redirect_uri)
    id_token = token_data.get("id_token")
    if not id_token:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Google ID token missing",
      )
    data = self._verify_google_id_token(id_token)
    email = data["email"]
    existing = self.auth_repository.get_user_by_social_email(email)
    if existing and existing.id != user.id:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Google account already linked",
      )
    other_user = self.auth_repository.get_user_by_email(email)
    if other_user and other_user.id != user.id:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Google account already linked",
      )
    user.social_email = email
    user.social_linked_at = datetime.now()
    self.auth_repository.db_session.commit()
    return {"google_email": email, "linked_at": user.social_linked_at.isoformat()}

  def unlink_google(self, user: User):
    if not user.social_email:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Google account not linked",
      )
    user.social_email = None
    user.social_linked_at = None
    self.auth_repository.db_session.commit()

  def refresh_user_token(self, refresh_token: str):
    user_id = verify_token(refresh_token, AUTH_SETTINGS.REFRESH_TOKEN_SECRET, "refresh")
    if not self.auth_repository.verify_refresh_token(refresh_token):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
      )
    self.auth_repository.delete_token(refresh_token)
    return self.issue_token(user_id)
  
  def logout_user(self, refresh_token: str):
    self.auth_repository.delete_token(refresh_token)

  def withdraw_user(self, user: User):
    """회원탈퇴 - 사용자 계정 및 관련 데이터 삭제"""
    # 관리자는 동아리 삭제를 먼저 해야 함
    if user.is_admin:
      # 관리 중인 동아리가 있는지 확인
      admin_clubs = [uc for uc in user.user_clublists if uc.permission == 1]
      if admin_clubs:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="관리자는 동아리 삭제를 통해 탈퇴해야 합니다",
        )
    
    # 사용자의 모든 refresh token 삭제
    self.auth_repository.delete_all_user_tokens(user.id)
    
    # 사용자 삭제 (cascade로 UserClublist, Schedule 등 삭제)
    self.auth_repository.db_session.delete(user)
    self.auth_repository.db_session.commit()

  def change_password(self, user: User, current_password: str, new_password: str):
    """비밀번호 변경 - 현재 비밀번호 확인 후 새 비밀번호로 변경"""
    # 현재 비밀번호 확인
    if not verify_password(current_password, user.hashed_password):
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="현재 비밀번호가 일치하지 않습니다.",
      )
    
    # 새 비밀번호로 변경
    user.hashed_password = hash_password(new_password)
    self.auth_repository.db_session.commit()
