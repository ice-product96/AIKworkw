from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.feed import ChatOrderItem, NotificationEvent, NotificationPollResponse
from app.schemas.order import MessageCreate, MessageResponse, OrderResponse
from app.services.chat_service import (
    get_chat_messages,
    get_chat_order,
    list_chat_orders,
    post_chat_message,
    assert_chat_access,
)
from app.services.feed import poll_notifications

router = APIRouter(tags=["chat", "notifications"])


@router.get("/chat/orders", response_model=list[ChatOrderItem])
async def chat_orders(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_chat_orders(db, user, q=q)
    return [ChatOrderItem(**row) for row in rows]


@router.get("/chat/orders/{order_id}", response_model=OrderResponse)
async def chat_order_meta(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await get_chat_order(db, order_id)
    await assert_chat_access(db, user, order)
    return order


@router.get("/chat/orders/{order_id}/messages", response_model=list[MessageResponse])
async def chat_get_messages(
    order_id: UUID,
    since: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await get_chat_messages(db, user, order_id, since=since)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/chat/orders/{order_id}/messages", response_model=MessageResponse)
async def chat_post_message(
    order_id: UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await post_chat_message(db, user, order_id, data.text)
    response = MessageResponse.model_validate(msg)
    if msg.is_blocked:
        response.warning = "Сообщение заблокировано: обмен контактами вне платформы запрещён."
    return response


@router.get("/notifications/poll", response_model=NotificationPollResponse)
async def notifications_poll(
    since: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    if since and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    if not since:
        since = now
    events = await poll_notifications(db, user, since)
    return NotificationPollResponse(
        events=[NotificationEvent(**e) for e in events],
        server_time=now,
    )
