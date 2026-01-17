from asset_management.app.auth.repositories import AuthRepository
from asset_management.app.auth.settings import AUTH_SETTINGS
from datetime import datetime, timedelta
from authlib.jose import jwt
from authlib.jose.errors import JoseError
from fastapi import Depends, Header, HTTPException, status
from typing import Annotated
import hashlib
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


def issue_token(user_id: int) -> str:
  header = {"alg": "HS256"}
  payload_acc = {
    "sub": user_id,
    "type": "access",
    "exp": datetime.now() + timedelta(minutes=AUTH_SETTINGS.SHORT_SESSION_LIFESPAN),
  }
  payload_ref = {
    "sub": user_id,
    "type": "refresh",
    "exp": datetime.now() + timedelta(minutes=AUTH_SETTINGS.LONG_SESSION_LIFESPAN),
  }
  access_token = jwt.encode(header, payload_acc, AUTH_SETTINGS.ACCESS_TOKEN_SECRET)
  refresh_token = jwt.encode(header, payload_ref, AUTH_SETTINGS.REFRESH_TOKEN_SECRET)
  
  # Convert bytes to string if necessary
  if isinstance(access_token, bytes):
    access_token = access_token.decode('utf-8')
  if isinstance(refresh_token, bytes):
    refresh_token = refresh_token.decode('utf-8')

  return {"access_token": access_token, "refresh_token": refresh_token}

# Security scheme for Swagger UI
security = HTTPBearer()

def get_header_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
  return credentials.credentials

def login_with_header(token: Annotated[str | None, Depends(get_header_token)] = None):
  return verify_token(token, AUTH_SETTINGS.ACCESS_TOKEN_SECRET, "access")

def verify_token(token: str, secret: str, expected_type: str) -> str:
  try:
    claims = jwt.decode(token, secret)
    claims.validate_exp(now=datetime.now().timestamp(), leeway=0)
    if claims.get("type") != expected_type:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token type",
        headers={"WWW-Authenticate": "Bearer"},
      )
    return claims.get("sub")
  except JoseError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"},
    )

def refresh_token(token: Annotated[str | None, Depends(get_header_token)] = None):
  return verify_token(token, AUTH_SETTINGS.REFRESH_TOKEN_SECRET, "refresh")

def verify_password(plain_password: str, hashed_password: str) -> bool:
  return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed_password

def check_club_permission(user_club_id: int, resource_club_id: int, auth_repository: Annotated[AuthRepository, Depends()]) -> int:
  """Check if the user has permission for the club resource.
  Args:
      user_club_id (int): The ID of the user's club.
      resource_club_id (int): The ID of the resource's club.
      auth_repository (AuthRepository): The authentication repository.
  Returns:
          int: The permission level of the user for the club resource.
              0: user
              1: admin
  Raises:
      HTTPException(403): If the user does not have any permission for the club resource.
  """
  userclubinfo = auth_repository.club_permission(user_club_id, resource_club_id)
  
  if userclubinfo is None:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User does not have permission for this club resource",
    )
  
  return userclubinfo.permission

def hash_password(password: str) -> str:
  """Hash the password using SHA-256.
  
  Args:
      password (str): The plain text password.
  
  Returns:
      str: The hashed password.
  """
  return hashlib.sha256(password.encode("utf-8")).hexdigest()
