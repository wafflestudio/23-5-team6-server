from datetime import datetime
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from asset_management.database.session import get_session
from asset_management.app.user.models import User, UserClublist
from asset_management.app.auth.models import RefreshToken


class AuthRepository:
    def __init__(self, db_session: Annotated[Session, Depends(get_session)]):
        self.db_session = db_session
    
    def get_user(self, user_id: str) -> User | None:
        return self.db_session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> User | None:
        return self.db_session.query(User).filter(User.email == email).first()

    def get_user_by_social_email(self, email: str) -> User | None:
        return self.db_session.query(User).filter(User.social_email == email).first()
    
    def add_refresh_token(self, token: str, user_id: str, expires_at) -> None:
      refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
      )
      self.db_session.add(refresh_token)
      self.db_session.commit()
    
    def delete_token(self, token: str) -> None:
      self.db_session.query(RefreshToken).filter(RefreshToken.token == token).delete()
      self.db_session.commit()
    
    def verify_refresh_token(self, token: str) -> bool:
      return self.db_session.query(RefreshToken).filter(RefreshToken.token == token).first() is not None
    
    def club_permission(self, user_club_id: int, resource_club_id: int) -> UserClublist | None:
      return self.db_session.query(UserClublist).filter(UserClublist.user_id == user_club_id, UserClublist.club_id == resource_club_id).first()