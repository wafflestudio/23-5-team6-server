import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.assets.models import Asset
    from asset_management.app.user.models import User
from enum import Enum

class Status(Enum):
    PENDING = "pending"  # 승인 대기
    APPROVED = "approved"  # 승인됨
    IN_USE = "in_use"  # 사용 중
    RETURNED = "returned"  # 반납 완료
    CANCELLED = "cancelled"  # 취소됨

class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=Status.PENDING.value) 

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="schedules")
    user: Mapped["User"] = relationship(back_populates="schedules")