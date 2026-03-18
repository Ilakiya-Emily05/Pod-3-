import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OnboardingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mobile: str = Field(min_length=10, max_length=20)
    dob: date
    college: str = Field(min_length=2, max_length=255)

    @field_validator("dob", mode="before")
    @classmethod
    def parse_dob(cls, value: date | str) -> date:
        if isinstance(value, date):
            return value

        if isinstance(value, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        msg = "dob must be in DD/MM/YYYY or YYYY-MM-DD format"
        raise ValueError(msg)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    mobile: str
    dob: date
    college: str
    created_at: datetime
    updated_at: datetime


class OnboardingResponse(BaseModel):
    profile: UserProfileResponse
    message: str = "Profile completed successfully"
