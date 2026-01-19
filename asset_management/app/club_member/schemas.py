from pydantic import BaseModel, Field


class ClubMemberBase(BaseModel):
    user_id: str
    club_id: int
    permission: int


class ClubMember(ClubMemberBase):
    id: int
    name: str


class ClubMemberResponse(BaseModel):
    total: int = 0
    page: int = 1
    size: int = 10
    pages: int = 1
    items: list[ClubMember]


class ClubMemberCreate(BaseModel):
    user_id: str
    permission: int
    club_id: int | None = None
    club_code: str | None = None


class ClubMemberUpdate(BaseModel):
    permission: int
