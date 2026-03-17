import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OnboardingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mobile: str = Field(min_length=10, max_length=20)
    dob: str = Field(pattern=r"^\d{2}/\d{2}/\d{4}$")
    college: str = Field(min_length=2, max_length=255)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    mobile: str
    dob: str
    college: str
    created_at: datetime
    updated_at: datetime


class OnboardingResponse(BaseModel):
    profile: UserProfileResponse
    message: str = "Profile completed successfully"
