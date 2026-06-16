from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    webhook_url: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    webhook_url: str | None = None
    status: str | None = None


class AgentResponse(BaseModel):
    id: UUID
    developer_id: UUID
    name: str
    description: str | None
    webhook_url: str | None
    status: str
    rating: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentServiceCreate(BaseModel):
    service_type: str
    language: str = "ru"
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    supports_files: bool = True
    supports_revisions: bool = True
    is_active: bool = True


class AgentServiceResponse(BaseModel):
    id: UUID
    agent_id: UUID
    service_type: str
    language: str
    min_price: Decimal | None
    max_price: Decimal | None
    supports_files: bool
    supports_revisions: bool
    is_active: bool

    model_config = {"from_attributes": True}


class ApiKeyResponse(BaseModel):
    api_key: str
    prefix: str
    message: str = "Store this key securely. It will not be shown again."


class AgentStatsResponse(BaseModel):
    total_orders: int
    completed_orders: int
    total_revenue: Decimal
    average_rating: Decimal
