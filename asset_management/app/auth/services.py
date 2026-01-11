from datetime import datetime, timedelta
from typing import Annotated
from asset_management.app.auth.repositories import AuthRepository
from asset_management.app.auth.settings import AUTH_SETTINGS
from asset_management.app.auth.utils import issue_token, verify_password, verify_token
from fastapi import Depends, HTTPException, Header, status


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