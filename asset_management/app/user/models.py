import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.club.models import Club
    from asset_management.app.schedule.models import Schedule
    from asset_management.app.favorite.models import Favorite
    from asset_management.app.picture.models import Picture


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    social_email: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Relationships
    user_clublists: Mapped[List["UserClublist"]] = relationship(back_populates="user")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="user")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="user")
    uploaded_pictures: Mapped[List["Picture"]] = relationship(back_populates="uploaded_user")


class UserClublist(Base):
    __tablename__ = "user_clublist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)
    permission: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_clublists")
    club: Mapped["Club"] = relationship(back_populates="user_clublists")
    