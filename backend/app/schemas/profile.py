from uuid import UUID

from pydantic import BaseModel, Field


class ClientPublicInfo(BaseModel):
    id: UUID
    display_name: str
    avatar_url: str | None = None
    level: int = 1
    projects_posted: int = 0
    hire_rate_percent: int = 0
    company: str | None = None


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    role: str
    display_name: str | None
    bio: str | None
    company: str | None
    location: str | None
    website: str | None
    developer_title: str | None
    avatar_url: str | None
    level: int = 1
    projects_posted: int = 0
    hire_rate_percent: int = 0
    agents_count: int = 0
    completed_as_client: int = 0
    completed_as_developer: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=2, max_length=100)
    bio: str | None = Field(None, max_length=2000)
    company: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=500)
    developer_title: str | None = Field(None, max_length=255)
