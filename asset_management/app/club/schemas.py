from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClubBase(BaseModel):
    name: str = Field(..., max_length=30)
    description: Optional[str] = Field(None, max_length=255)


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=255)


class ClubResponse(ClubBase):
    id: int
    club_code: str
    location_lat: Optional[int] = None
    location_lng: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ClubApplicationRequest(BaseModel):
    club_code: str = Field(..., min_length=1, description="Club invitation code")


class ClubApplicationResponse(BaseModel):
    application_id: int
    club_name: str
    status: str  # "pending"
    
