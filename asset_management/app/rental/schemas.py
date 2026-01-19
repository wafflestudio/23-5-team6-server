from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class RentalBorrowRequest(BaseModel):
    """물품 대여 요청"""
    item_id: int
    expected_return_date: Optional[date] = None


class RentalResponse(BaseModel):
    """물품 대여 응답"""
    id: str  # rental-001 형식
    item_id: int
    user_id: str
    status: str  # borrowed, returned, overdue
    borrowed_at: datetime
    expected_return_date: Optional[date] = None
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True
