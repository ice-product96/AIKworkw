from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.profile import ClientPublicInfo


class MarketplaceStatsResponse(BaseModel):
    users_online: int
    last_order_seconds_ago: int | None
    total_orders: int
    active_agents: int
    categories: list[dict]


class PublicProjectItem(BaseModel):
    id: UUID
    title: str
    description_preview: str
    service_type: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    status: str
    created_at: datetime
    updated_at: datetime
    proposals_count: int = 0
    client: ClientPublicInfo | None = None


class PublicProjectListResponse(BaseModel):
    items: list[PublicProjectItem]
    total: int
    limit: int
    offset: int


class PublicProjectDetail(BaseModel):
    id: UUID
    title: str
    description: str
    service_type: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    status: str
    created_at: datetime
    updated_at: datetime
    proposals_count: int = 0
    client: ClientPublicInfo | None = None
