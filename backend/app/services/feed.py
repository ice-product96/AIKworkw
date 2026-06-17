from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, User, UserRole
from app.models.domain import AgentService, Estimate, EstimateStatus, Message, Order, OrderStatus
from app.services.marketplace import CATEGORY_MAP


FEED_EXCLUDED = {OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed}


async def _developer_service_types(db: AsyncSession, user_id: UUID) -> list[str]:
    result = await db.execute(
        select(AgentService.service_type)
        .join(Agent, Agent.id == AgentService.agent_id)
        .where(Agent.developer_id == user_id)
        .distinct()
    )
    return [row[0] for row in result.all()]


def _apply_feed_filters(
    query,
    *,
    status: str | None,
    service_type: str | None,
    q: str | None,
):
    query = query.where(Order.status.not_in(list(FEED_EXCLUDED)))
    if status:
        query = query.where(Order.status == OrderStatus(status))
    if service_type:
        query = query.where(Order.service_type == service_type)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Order.title.ilike(pattern), Order.description.ilike(pattern)))
    return query


async def list_feed_orders(
    db: AsyncSession,
    user: User,
    *,
    status: str | None = None,
    service_type: str | None = None,
    category: str | None = None,
    q: str | None = None,
    sort: str = "created_at_desc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    base = select(Order)
    base = _apply_feed_filters(base, status=status, service_type=service_type, q=q)
    if category and category in CATEGORY_MAP:
        base = base.where(Order.service_type.in_(CATEGORY_MAP[category]))

    if user.role == UserRole.developer:
        types = await _developer_service_types(db, user.id)
        if types:
            base = base.where(Order.service_type.in_(types))
        else:
            return [], 0

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if sort == "created_at_asc":
        base = base.order_by(Order.created_at.asc())
    elif sort == "updated_at_desc":
        base = base.order_by(Order.updated_at.desc())
    else:
        base = base.order_by(Order.created_at.desc())

    result = await db.execute(base.limit(limit).offset(offset))
    orders = list(result.scalars().all())
    if not orders:
        return [], total

    order_ids = [o.id for o in orders]
    msg_stats = await db.execute(
        select(
            Message.order_id,
            func.count(Message.id),
            func.max(Message.created_at),
        )
        .where(Message.order_id.in_(order_ids), Message.is_blocked.is_(False))
        .group_by(Message.order_id)
    )
    stats_map = {row[0]: (row[1], row[2]) for row in msg_stats.all()}

    last_msgs = await db.execute(
        select(Message)
        .where(Message.order_id.in_(order_ids), Message.is_blocked.is_(False))
        .order_by(Message.created_at.desc())
    )
    preview_map: dict[UUID, str] = {}
    for msg in last_msgs.scalars().all():
        if msg.order_id not in preview_map:
            preview_map[msg.order_id] = msg.text[:120]

    est_stats = await db.execute(
        select(Estimate.order_id, func.count(Estimate.id))
        .where(
            Estimate.order_id.in_(order_ids),
            Estimate.status.in_([EstimateStatus.submitted, EstimateStatus.selected]),
        )
        .group_by(Estimate.order_id)
    )
    proposals_map = {row[0]: row[1] for row in est_stats.all()}

    items = []
    for order in orders:
        count, last_at = stats_map.get(order.id, (0, None))
        items.append(
            {
                "order": order,
                "is_mine": order.client_id == user.id,
                "message_count": count,
                "last_message_at": last_at,
                "last_message_preview": preview_map.get(order.id),
                "proposals_count": proposals_map.get(order.id, 0),
            }
        )
    return items, total


async def accessible_order_ids(db: AsyncSession, user: User) -> list[UUID] | None:
    if user.role == UserRole.admin:
        return None
    if user.role == UserRole.client:
        result = await db.execute(select(Order.id).where(Order.client_id == user.id))
        return [row[0] for row in result.all()]
    if user.role == UserRole.developer:
        return None
    return []


async def poll_notifications(
    db: AsyncSession,
    user: User,
    since: datetime,
) -> list[dict]:
    events: list[dict] = []
    order_ids = await accessible_order_ids(db, user)

    msg_q = (
        select(Message, Order.title)
        .join(Order, Order.id == Message.order_id)
        .where(Message.created_at > since, Message.is_blocked.is_(False))
    )
    if user.role == UserRole.client:
        msg_q = msg_q.where(Message.sender_type != SenderType.client)
    elif user.role == UserRole.developer:
        msg_q = msg_q.where(
            Message.sender_type.in_([SenderType.client, SenderType.agent, SenderType.system, SenderType.admin])
        )
    if order_ids is not None:
        msg_q = msg_q.where(Message.order_id.in_(order_ids))

    for msg, title in (await db.execute(msg_q.order_by(Message.created_at))).all():
        events.append(
            {
                "type": "new_message",
                "order_id": msg.order_id,
                "title": title,
                "body": msg.text[:200],
                "created_at": msg.created_at,
            }
        )

    status_q = select(Order).where(Order.updated_at > since)
    if order_ids is not None:
        status_q = status_q.where(Order.id.in_(order_ids))
    elif user.role != UserRole.admin:
        status_q = status_q.where(Order.client_id == user.id)

    for order in (await db.execute(status_q)).scalars().all():
        events.append(
            {
                "type": "order_status",
                "order_id": order.id,
                "title": order.title,
                "body": f"Статус: {order.status.value}",
                "created_at": order.updated_at,
            }
        )

    events.sort(key=lambda e: e["created_at"])
    return events
