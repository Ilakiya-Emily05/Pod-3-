from pydantic import BaseModel, EmailStr, Field


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class AdminAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_email: EmailStr
