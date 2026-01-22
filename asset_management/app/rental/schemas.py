from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional


class RentalBorrowRequest(BaseModel):
    """물품 대여 요청"""
    item_id: int
    expected_return_date: Optional[date] = None


class RentalReturnRequest(BaseModel):
    """물품 반납 요청 (GPS 포함)"""
    location_lat: int = Field(
        ...,
        ge=-90_000_000,
        le=90_000_000,
        description="Return latitude (degrees * 1,000,000)",
    )
    location_lng: int = Field(
        ...,
        ge=-180_000_000,
        le=180_000_000,
        description="Return longitude (degrees * 1,000,000)",
    )


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


class RentalReturnRequest(BaseModel):
    """물품 반납 요청 (GPS 선택)"""
    location_lat: Optional[int] = Field(
        None,
        ge=-90_000_000,
        le=90_000_000,
        description="Return latitude (degrees * 1,000,000)",
    )
    location_lng: Optional[int] = Field(
        None,
        ge=-180_000_000,
        le=180_000_000,
        description="Return longitude (degrees * 1,000,000)",
    )
