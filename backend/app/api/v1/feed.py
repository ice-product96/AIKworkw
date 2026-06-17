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
from app.schemas.order import OrderDetailResponse
from app.services.feed import list_feed_orders, poll_notifications
from app.services.profile import build_client_public_map

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
            client=row.get("client"),
        )
        for row in rows
    ]
    return FeedOrderListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def feed_order_detail(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.domain import Estimate, EstimateStatus

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status in (OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    proposals = (
        await db.execute(
            select(func.count())
            .select_from(Estimate)
            .where(
                Estimate.order_id == order.id,
                Estimate.status.in_([EstimateStatus.submitted, EstimateStatus.selected]),
            )
        )
    ).scalar_one()
    client_map = await build_client_public_map(db, [order.client_id])
    return OrderDetailResponse(
        id=order.id,
        client_id=order.client_id,
        title=order.title,
        description=order.description,
        service_type=order.service_type,
        budget_min=order.budget_min,
        budget_max=order.budget_max,
        deadline=order.deadline,
        status=order.status.value,
        selected_agent_id=order.selected_agent_id,
        selected_estimate_id=order.selected_estimate_id,
        result_text=order.result_text,
        dispute_reason=order.dispute_reason,
        created_at=order.created_at,
        updated_at=order.updated_at,
        proposals_count=proposals,
        client=client_map.get(order.client_id),
    )
