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
        min_length=1,
        max_length=50,
        description="Custom club invitation code",
    )


class AdminSignupResponse(BaseModel):
    id: str
    name: str
    email: str
    club_id: int
    club_name: str
    club_code: str


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
    club_code: str = Field(..., min_length=1, max_length=50, description="New club code")


class ClubCodeUpdateResponse(BaseModel):
    club_id: int
    club_code: str
