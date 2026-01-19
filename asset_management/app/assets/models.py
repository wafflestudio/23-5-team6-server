from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.club.models import Club
    from asset_management.app.category.models import Category
    from asset_management.app.schedule.models import Schedule
    from asset_management.app.favorite.models import Favorite
    from asset_management.app.picture.models import Picture

from datetime import datetime

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)
    # picture_id: Mapped[Optional[int]] = mapped_column(ForeignKey("picture.id"), nullable=True)

    # Relationships
    club: Mapped["Club"] = relationship(back_populates="assets")
    category: Mapped["Category"] = relationship(back_populates="assets")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="asset")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="asset")
    # main_picture: Mapped[Optional["Picture"]] = relationship(
    #     foreign_keys=[picture_id]
    # )
    # pictures: Mapped[List["Picture"]] = relationship(
    #     back_populates="asset",
    #     foreign_keys="[Picture.assets_id]"
    # )
    pictures: Mapped[List["Picture"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan"
    )