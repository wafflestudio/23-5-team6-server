from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class AdminSignupRequest(BaseModel):
    name: str = Field(..., max_length=30, description="Admin name")
    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., min_length=8, max_length=64, description="Password")
    club_name: str = Field(..., max_length=30, description="Club name")
    club_description: Optional[str] = Field(None, max_length=255, description="Club description")
    club_code: Optional[str] = Field(
        None,
        min_length=0,
        max_length=50,
        description="Custom club invitation code",
    )
    location_lat: Optional[int] = Field(
        None,
        ge=-90_000_000,
        le=90_000_000,
        description="Club latitude (degrees * 1,000,000)",
    )
    location_lng: Optional[int] = Field(
        None,
        ge=-180_000_000,
        le=180_000_000,
        description="Club longitude (degrees * 1,000,000)",
    )


class AdminSignupResponse(BaseModel):
    id: str
    name: str
    email: str
    club_id: int
    club_name: str
    club_code: str
    location_lat: Optional[int] = None
    location_lng: Optional[int] = None


class PendingUserDetail(BaseModel):
    id: str
    name: str
    email: str
    student_id: Optional[str]


class PendingUsersResponse(BaseModel):
    users: List[PendingUserDetail]


class UserApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True to approve, False to reject")


class UserApprovalResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str  # "approved" or "rejected"


class ClubCodeUpdateRequest(BaseModel):
    club_code: str = Field(..., min_length=0, max_length=50, description="New club code")


class ClubCodeUpdateResponse(BaseModel):
    club_id: int
    club_code: str


class AdminMyClubResponse(BaseModel):
    club_id: int
    club_name: str
    club_code: str
