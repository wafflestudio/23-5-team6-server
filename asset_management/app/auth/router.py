from typing import Annotated
from fastapi import APIRouter, Depends, status, Response
from asset_management.app.auth.schemas import (
  LoginResponse,
  UserSignin,
  TokenResponse,
  GoogleAuthRequest,
  GoogleLinkResponse,
  GoogleStatusResponse,
)
from asset_management.app.auth.services import AuthServices
from asset_management.app.auth.utils import (
  refresh_token,
  get_header_token,
)
from asset_management.app.auth.dependencies import get_current_user
from asset_management.app.user.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

blocked_token = {}


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
  request: UserSignin, auth_service: Annotated[AuthServices, Depends()]
) -> LoginResponse:
  login_info = auth_service.login_user(request.email, request.password)
  return LoginResponse(**login_info)


@router.get("/google/status", status_code=status.HTTP_200_OK)
def google_status(
  user: Annotated[User, Depends(get_current_user)],
) -> GoogleStatusResponse:
  return GoogleStatusResponse(
    is_linked=bool(user.social_email),
    google_email=user.social_email,
  )


@router.post("/google/link", status_code=status.HTTP_200_OK)
def google_link(
  request: GoogleAuthRequest,
  auth_service: Annotated[AuthServices, Depends()],
  user: Annotated[User, Depends(get_current_user)],
) -> GoogleLinkResponse:
  link_info = auth_service.link_google(
    user,
    request.code,
    request.code_verifier,
    request.redirect_uri,
  )
  return GoogleLinkResponse(**link_info)


@router.delete("/google/link", status_code=status.HTTP_204_NO_CONTENT)
def google_unlink(
  auth_service: Annotated[AuthServices, Depends()],
  user: Annotated[User, Depends(get_current_user)],
):
  auth_service.unlink_google(user)
  response = Response()
  response.status_code = status.HTTP_204_NO_CONTENT
  return response


@router.post("/google/login", status_code=status.HTTP_200_OK)
def google_login(
  request: GoogleAuthRequest, auth_service: Annotated[AuthServices, Depends()]
) -> LoginResponse:
  login_info = auth_service.login_google(
    request.code,
    request.code_verifier,
    request.redirect_uri,
  )
  return LoginResponse(**login_info)


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
