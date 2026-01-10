from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClubBase(BaseModel):
    name: str = Field(..., max_length=30)


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=30)


class ClubResponse(ClubBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
