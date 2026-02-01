from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional


class RentalBorrowRequest(BaseModel):
    """물품 대여 요청"""
    item_id: int
    expected_return_date: Optional[date] = None


class RentalResponse(BaseModel):
    """물품 대여 응답"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int  # schedule id
    item_id: int
    user_id: str
    status: str  # borrowed, returned, overdue
    borrowed_at: datetime
    expected_return_date: Optional[date] = None
    returned_at: Optional[datetime] = None