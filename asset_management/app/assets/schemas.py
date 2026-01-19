from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class AssetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    # Schedule 기반 대여 상태 (0: 대여 가능, 1: 대여 중)
    status: int = 0

    category_id: Optional[int] = None
    category_name: Optional[str] = None

    total_quantity: int
    available_quantity: int

    location: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssetCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    club_id: int = Field(...)
    category_id: Optional[int] = Field(None)
    quantity: int = Field(..., ge=1)
    location: Optional[str] = Field(None, max_length=100)

class AssetUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    club_id: int = Field(...)
    category_id: Optional[int] = Field(None)
    quantity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = Field(None, max_length=100)

