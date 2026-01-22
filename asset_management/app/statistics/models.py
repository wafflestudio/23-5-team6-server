from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.assets.models import Asset

class Statistic(Base):
    __tablename__ = "statistics"

    # Primary Key (동시에 Foreign Key)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), primary_key=True)
    
    # 전체 기간 통계
    total_rental_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_rental_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 초 단위
    
    # 최근 30일 통계
    recent_rental_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 30일
    recent_avg_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 30일, 초 단위
    
    # 사용 패턴
    unique_borrower_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  
    # 타임스탬프
    last_borrowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="statistics")