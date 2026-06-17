from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AiSettingsResponse(BaseModel):
    configured: bool
    base_url: str
    model: str
    has_api_key: bool
    api_key_masked: str = ""


class AiSettingsUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class GenerateActivityRequest(BaseModel):
    num_clients: int = Field(default=3, ge=1, le=20)
    num_developers: int = Field(default=2, ge=1, le=10)
    num_agents: int = Field(default=5, ge=1, le=30)
    num_orders: int = Field(default=8, ge=1, le=30)
    complete_ratio: float = Field(default=0.4, ge=0, le=1)


class GenerateActivityResponse(BaseModel):
    users_created: int
    agents_created: int
    orders_created: int
    estimates_created: int
    messages_created: int
    orders_completed: int
    demo_password: str


class GenerateLandingRequest(BaseModel):
    topic: str = "маркетплейс AI-агентов для бизнеса"


class GenerateBlogRequest(BaseModel):
    topic: str
    publish: bool = False


class GenerateBlogBatchRequest(BaseModel):
    topics: list[str] = Field(min_length=1, max_length=10)
    publish: bool = True


class BlogPostCreate(BaseModel):
    slug: str
    title: str
    excerpt: str | None = None
    content: str
    meta_title: str | None = None
    meta_description: str | None = None
    status: str = "draft"


class BlogPostUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    status: str | None = None


class BlogPostResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    excerpt: str | None
    content: str
    meta_title: str | None
    meta_description: str | None
    status: str
    is_ai_generated: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BlogPostListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    excerpt: str | None
    meta_title: str | None
    meta_description: str | None
    status: str
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SitePageResponse(BaseModel):
    slug: str
    title: str
    content_json: dict
    meta_title: str | None
    meta_description: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SitePageUpdate(BaseModel):
    title: str | None = None
    content_json: dict | None = None
    meta_title: str | None = None
    meta_description: str | None = None
