from datetime import datetime, timedelta
from typing import Annotated
import json
import urllib.parse
import urllib.request
from asset_management.app.auth.repositories import AuthRepository
from asset_management.app.auth.settings import AUTH_SETTINGS
from asset_management.app.auth.utils import issue_token, verify_password, verify_token
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

  def login_google(self, id_token: str):
    data = self._verify_google_id_token(id_token)
    email = data["email"]

    user = self.auth_repository.get_user_by_social_email(email)
    if not user:
      user = self.auth_repository.get_user_by_email(email)

    if user:
      if user.is_admin:
        raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Admin account cannot use social login",
        )
      if not user.social_email:
        user.social_email = email
        self.auth_repository.db_session.commit()
      return {
        "user_name": user.name,
        "user_type": user.is_admin,
        "tokens": self.issue_token(user.id),
      }

    name = data.get("name") or email.split("@")[0]
    user = User(
      name=name,
      email=email,
      social_email=email,
      hashed_password=None,
      is_admin=False,
    )
    self.auth_repository.db_session.add(user)
    self.auth_repository.db_session.commit()
    self.auth_repository.db_session.refresh(user)
    return {
      "user_name": user.name,
      "user_type": user.is_admin,
      "tokens": self.issue_token(user.id),
    }

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