from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, UserRole
from app.models.domain import Message, Order, OrderStatus, SenderType
from app.schemas.feed import (
    ChatOrderItem,
    FeedOrderItem,
    FeedOrderListResponse,
    NotificationEvent,
    NotificationPollResponse,
)
from app.schemas.order import OrderResponse
from app.services.feed import list_chat_orders, list_feed_orders, poll_notifications
from app.services.order_service import get_order_for_client

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/orders", response_model=FeedOrderListResponse)
async def feed_orders(
    status_filter: str | None = Query(None, alias="status"),
    service_type: str | None = None,
    category: str | None = None,
    q: str | None = None,
    sort: str = Query("created_at_desc", pattern="^(created_at_desc|created_at_asc|updated_at_desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await list_feed_orders(
        db,
        user,
        status=status_filter,
        service_type=service_type,
        category=category,
        q=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    items = [
        FeedOrderItem(
            id=row["order"].id,
            client_id=row["order"].client_id,
            title=row["order"].title,
            description=row["order"].description,
            service_type=row["order"].service_type,
            budget_min=row["order"].budget_min,
            budget_max=row["order"].budget_max,
            deadline=row["order"].deadline,
            status=row["order"].status.value,
            created_at=row["order"].created_at,
            updated_at=row["order"].updated_at,
            is_mine=row["is_mine"],
            message_count=row["message_count"],
            last_message_at=row["last_message_at"],
            last_message_preview=row["last_message_preview"],
            proposals_count=row["proposals_count"],
        )
        for row in rows
    ]
    return FeedOrderListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def feed_order_detail(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status in (OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if user.role == UserRole.client and order.client_id != user.id:
        pass
    return order
