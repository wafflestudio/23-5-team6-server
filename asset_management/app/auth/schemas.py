from pydantic import BaseModel, EmailStr


class UserSignin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str

class GoogleLinkResponse(BaseModel):
    google_email: EmailStr
    linked_at: str

class GoogleStatusResponse(BaseModel):
    is_linked: bool
    google_email: EmailStr | None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    user_name: str
    user_type: int
    tokens: TokenResponse


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
