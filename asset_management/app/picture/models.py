import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.assets.models import Asset
    from asset_management.app.user.models import User
    from asset_management.app.category.models import Category


class Picture(Base):
    __tablename__ = "picture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    assets_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    uploaded_user: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="pictures")
    uploaded_user: Mapped["User"] = relationship(back_populates="uploaded_pictures")
    category: Mapped["Category"] = relationship(back_populates="pictures")