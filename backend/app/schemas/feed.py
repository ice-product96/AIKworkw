from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.profile import ClientPublicInfo


class FeedOrderItem(BaseModel):
    id: UUID
    client_id: UUID
    title: str
    description: str
    service_type: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    deadline: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime
    is_mine: bool = False
    message_count: int = 0
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    proposals_count: int = 0
    client: ClientPublicInfo | None = None


class FeedOrderListResponse(BaseModel):
    items: list[FeedOrderItem]
    total: int
    limit: int
    offset: int


class ChatOrderItem(BaseModel):
    order_id: UUID
    title: str
    status: str
    service_type: str | None = None
    is_mine: bool = False
    message_count: int = 0
    last_message_at: datetime | None
    last_message_preview: str | None
    last_sender_type: str | None


class NotificationEvent(BaseModel):
    type: str
    order_id: UUID
    title: str
    body: str
    created_at: datetime


class NotificationPollResponse(BaseModel):
    events: list[NotificationEvent]
    server_time: datetime


class OrderListFilters(BaseModel):
    status: str | None = None
    service_type: str | None = None
    q: str | None = Field(default=None, max_length=200)
