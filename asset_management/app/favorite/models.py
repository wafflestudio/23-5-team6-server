import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.user.models import User
    from asset_management.app.assets.models import Asset


class Favorite(Base):
    __tablename__ = "favorite"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="favorites")
    asset: Mapped["Asset"] = relationship(back_populates="favorites")