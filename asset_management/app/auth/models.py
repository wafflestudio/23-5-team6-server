from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column
from datetime import datetime
from asset_management.database.common import Base

if TYPE_CHECKING:
    from asset_management.app.user.models import User

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True) # 토큰 값으로 조회를 많이 하므로 Index 필수
    expires_at = Column(DateTime, nullable=False) # 만료 시간
    created_at = Column(DateTime, default=datetime.now())
    
    # 외래키 설정
    user_id = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    
    # 관계 설정
    user = relationship("User", back_populates="refresh_tokens")