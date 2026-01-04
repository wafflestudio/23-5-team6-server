import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.assets.models import Asset
    from asset_management.app.user.models import User


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="schedules")
    user: Mapped["User"] = relationship(back_populates="schedules")