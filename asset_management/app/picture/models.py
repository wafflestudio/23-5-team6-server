import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, DateTime, ForeignKey, String, Boolean, func, LargeBinary
from sqlalchemy.dialects.mysql import LONGBLOB
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
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"), nullable=True)

    data: Mapped[bytes] = mapped_column(LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="pictures")
    user: Mapped["User"] = relationship(back_populates="uploaded_pictures")
    category: Mapped[Optional["Category"]] = relationship(back_populates="pictures")