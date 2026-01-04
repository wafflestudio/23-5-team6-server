from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., max_length=30)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64)


class UserResponse(UserBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
