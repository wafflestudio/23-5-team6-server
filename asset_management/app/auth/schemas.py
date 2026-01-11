from pydantic import BaseModel, EmailStr

class UserSignin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
class LoginResponse(BaseModel):
    user_name: str
    user_type: int
    tokens: TokenResponse