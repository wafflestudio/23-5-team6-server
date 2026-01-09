from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.user.models import UserClublist
    from asset_management.app.assets.models import Asset


class Club(Base):
    __tablename__ = "club"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    club_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Relationships
    user_clublists: Mapped[List["UserClublist"]] = relationship(back_populates="club")
    assets: Mapped[List["Asset"]] = relationship(back_populates="club")