from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    service_type: str
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    deadline: datetime | None = None


class OrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    deadline: datetime | None = None


class OrderResponse(BaseModel):
    id: UUID
    client_id: UUID
    title: str
    description: str
    service_type: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    deadline: datetime | None
    status: str
    selected_agent_id: UUID | None
    selected_estimate_id: UUID | None
    result_text: str | None
    dispute_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EstimateResponse(BaseModel):
    id: UUID
    order_id: UUID
    agent_id: UUID
    price: Decimal | None
    deadline_hours: int | None
    confidence: Decimal | None
    message: str | None
    questions: list | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: UUID
    order_id: UUID
    sender_type: str
    sender_id: str
    text: str
    is_blocked: bool
    moderation_reason: str | None
    created_at: datetime
    warning: str | None = None

    model_config = {"from_attributes": True}


class RevisionRequest(BaseModel):
    message: str = Field(min_length=5)


class DisputeRequest(BaseModel):
    reason: str = Field(min_length=5)


class FileResponse(BaseModel):
    id: UUID
    order_id: UUID
    filename: str
    mime_type: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}
