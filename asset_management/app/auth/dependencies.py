from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from asset_management.app.auth.settings import AUTH_SETTINGS
from asset_management.app.auth.utils import get_header_token, verify_token
from asset_management.app.user.models import User
from asset_management.database.session import get_session


def get_current_user(
    token: Annotated[str, Depends(get_header_token)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    user_id = verify_token(token, AUTH_SETTINGS.ACCESS_TOKEN_SECRET, "access")
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
