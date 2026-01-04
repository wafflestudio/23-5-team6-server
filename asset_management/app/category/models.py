from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.assets.models import Asset
    from asset_management.app.picture.models import Picture


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    assets: Mapped[List["Asset"]] = relationship(back_populates="category")
    pictures: Mapped[List["Picture"]] = relationship(back_populates="category")