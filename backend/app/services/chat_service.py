from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.models.domain import Message, Order, OrderStatus, SenderType
from app.services.order_service import create_message

CHAT_EXCLUDED = {OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed}


async def get_chat_order(db: AsyncSession, order_id: UUID) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status in CHAT_EXCLUDED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


async def assert_chat_access(db: AsyncSession, user: User, order: Order) -> None:
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.client:
        if order.client_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return
    if user.role == UserRole.developer:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _sender_type_for_user(user: User) -> SenderType:
    if user.role == UserRole.developer:
        return SenderType.developer
    return SenderType.client


async def list_chat_orders(db: AsyncSession, user: User, q: str | None = None) -> list[dict]:
    query = select(Order).where(Order.status.not_in(list(CHAT_EXCLUDED)))

    if user.role == UserRole.client:
        query = query.where(Order.client_id == user.id)
    elif user.role == UserRole.developer:
        pass
    elif user.role == UserRole.admin:
        pass
    else:
        return []

    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Order.title.ilike(pattern), Order.description.ilike(pattern)))

    orders = list((await db.execute(query.limit(200))).scalars().all())
    if not orders:
        return []

    ids = [o.id for o in orders]
    msg_counts = await db.execute(
        select(Message.order_id, func.count(Message.id), func.max(Message.created_at))
        .where(Message.order_id.in_(ids), Message.is_blocked.is_(False))
        .group_by(Message.order_id)
    )
    stats_map = {row[0]: (row[1], row[2]) for row in msg_counts.all()}

    last_msgs = await db.execute(
        select(Message)
        .where(Message.order_id.in_(ids), Message.is_blocked.is_(False))
        .order_by(Message.created_at.desc())
    )
    preview_map: dict[UUID, Message] = {}
    for msg in last_msgs.scalars().all():
        if msg.order_id not in preview_map:
            preview_map[msg.order_id] = msg

    items = []
    for order in orders:
        count, last_at = stats_map.get(order.id, (0, None))
        last = preview_map.get(order.id)
        items.append(
            {
                "order_id": order.id,
                "title": order.title,
                "status": order.status.value,
                "service_type": order.service_type,
                "is_mine": order.client_id == user.id,
                "message_count": count,
                "last_message_at": last_at,
                "last_message_preview": last.text[:120] if last else None,
                "last_sender_type": last.sender_type.value if last else None,
            }
        )

    items.sort(
        key=lambda x: x["last_message_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items


async def get_chat_messages(
    db: AsyncSession,
    user: User,
    order_id: UUID,
    since: datetime | None = None,
) -> list[Message]:
    order = await get_chat_order(db, order_id)
    await assert_chat_access(db, user, order)
    query = select(Message).where(Message.order_id == order_id, Message.is_blocked.is_(False))
    if since:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        query = query.where(Message.created_at > since)
    query = query.order_by(Message.created_at)
    return list((await db.execute(query)).scalars().all())


async def post_chat_message(db: AsyncSession, user: User, order_id: UUID, text: str) -> Message:
    order = await get_chat_order(db, order_id)
    await assert_chat_access(db, user, order)
    if user.role not in (UserRole.client, UserRole.developer, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot send messages")
    sender = _sender_type_for_user(user) if user.role != UserRole.admin else SenderType.admin
    return await create_message(db, order, sender, str(user.id), text)
