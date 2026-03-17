import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str | None = Field(default=None, min_length=8, max_length=72)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=72)
    remember_me: bool = False
    oauth_id_token: str | None = None
    oauth_code: str | None = None
    oauth_redirect_uri: str | None = None
    oauth_code_verifier: str | None = None

    @model_validator(mode="after")
    def validate_signup_credentials(self) -> "SignupRequest":
        if self.oauth_id_token or self.oauth_code:
            return self

        if not self.password or not self.confirm_password:
            msg = "Password and confirm_password are required when OAuth is not provided"
            raise ValueError(msg)

        if self.password != self.confirm_password:
            msg = "Password and confirm_password must match"
            raise ValueError(msg)

        return self


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    remember_me: bool = False
    oauth_id_token: str | None = None
    oauth_code: str | None = None
    oauth_redirect_uri: str | None = None
    oauth_code_verifier: str | None = None

    @model_validator(mode="after")
    def validate_login_credentials(self) -> "LoginRequest":
        if self.oauth_id_token or self.oauth_code:
            return self

        if not self.email or not self.password:
            msg = "Email and password are required when OAuth is not provided"
            raise ValueError(msg)

        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    oauth_provider: str | None
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    remember_me: bool
    user: UserResponse
