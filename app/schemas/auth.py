from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    cefr_level: str | None = None
    learning_goal: str | None = None
    learning_frequency: str | None = None
    streak_count: int = 0
    total_xp: int = 0


class AuthRegisterResponse(BaseModel):
    user_id: UUID
    token: str


class AuthLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserRead
