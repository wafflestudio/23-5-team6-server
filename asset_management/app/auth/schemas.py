from pydantic import BaseModel, EmailStr

class UserSignin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str