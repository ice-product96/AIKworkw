from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.feed import ChatOrderItem, NotificationEvent, NotificationPollResponse
from app.services.feed import list_chat_orders, poll_notifications

router = APIRouter(tags=["chat", "notifications"])


@router.get("/chat/orders", response_model=list[ChatOrderItem])
async def chat_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_chat_orders(db, user)
    return [ChatOrderItem(**row) for row in rows]


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
