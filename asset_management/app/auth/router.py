from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, status, Response
from sqlalchemy.orm import Session
from asset_management.app.auth.schemas import UserSignin, TokenResponse
from asset_management.app.auth.services import AuthServices
from asset_management.app.auth.utils import (
  issue_token,
  login_with_header,
  refresh_token,
  get_header_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

blocked_token = {}


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
  request: UserSignin, auth_service: Annotated[AuthServices, Depends()]
) -> TokenResponse:
  token = auth_service.login_user(request.email, request.password)
  return TokenResponse(**token)


@router.get("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(
  auth_service: Annotated[AuthServices, Depends()],
  refresh_token: Annotated[str, Depends(get_header_token)],
  user_id: str = Depends(refresh_token),
):
  tokens = auth_service.refresh_user_token(refresh_token)
  return TokenResponse(**tokens)


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
  auth_service: Annotated[AuthServices, Depends()],
  token: Annotated[str, Depends(get_header_token)]
):
  auth_service.logout_user(token)
  response = Response()
  response.status_code = status.HTTP_204_NO_CONTENT
  return response
