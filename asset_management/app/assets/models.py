from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.club.models import Club
    from asset_management.app.category.models import Category
    from asset_management.app.schedule.models import Schedule
    from asset_management.app.favorite.models import Favorite
    from asset_management.app.picture.models import Picture


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    # Relationships
    club: Mapped["Club"] = relationship(back_populates="assets")
    category: Mapped["Category"] = relationship(back_populates="assets")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="asset")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="asset")
    pictures: Mapped[List["Picture"]] = relationship(back_populates="asset")