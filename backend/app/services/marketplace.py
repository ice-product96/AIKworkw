from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Agent, AgentStatus, Estimate, EstimateStatus, Order, OrderStatus

from app.services.profile import build_client_public_map

FEED_EXCLUDED = {OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed}

CATEGORY_MAP: dict[str, list[str]] = {
    "design": ["landing_page", "design_banner"],
    "development": ["python_script", "telegram_bot", "data_processing"],
    "texts": ["copywriting", "document_analysis"],
    "seo": ["seo_audit"],
    "marketing": ["copywriting", "design_banner", "landing_page"],
    "business": ["document_analysis", "data_processing"],
}


def _apply_public_filters(query, *, category: str | None, service_type: str | None, q: str | None):
    query = query.where(Order.status.not_in(list(FEED_EXCLUDED)))
    if category and category in CATEGORY_MAP:
        query = query.where(Order.service_type.in_(CATEGORY_MAP[category]))
    if service_type:
        query = query.where(Order.service_type == service_type)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Order.title.ilike(pattern), Order.description.ilike(pattern)))
    return query


async def get_marketplace_stats(db: AsyncSession) -> dict:
    orders_count = (
        await db.execute(
            select(func.count()).select_from(Order).where(Order.status.not_in(list(FEED_EXCLUDED)))
        )
    ).scalar_one()
    agents_count = (
        await db.execute(select(func.count()).select_from(Agent).where(Agent.status == AgentStatus.active))
    ).scalar_one()

    last_order = (
        await db.execute(
            select(Order.created_at)
            .where(Order.status.not_in(list(FEED_EXCLUDED)))
            .order_by(Order.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    last_seconds = None
    if last_order:
        last_seconds = max(0, int((datetime.now(UTC) - last_order).total_seconds()))

    # Имитация «онлайн» как на Kwork — база + небольшой разброс по времени суток
    hour = datetime.now(UTC).hour
    online_base = 40 + (hour % 12) * 15
    users_online = online_base + (orders_count % 37)

    category_counts: list[dict] = []
    for slug, types in CATEGORY_MAP.items():
        cnt = (
            await db.execute(
                select(func.count())
                .select_from(Order)
                .where(Order.status.not_in(list(FEED_EXCLUDED)), Order.service_type.in_(types))
            )
        ).scalar_one()
        category_counts.append({"slug": slug, "orders_count": cnt})

    return {
        "users_online": users_online,
        "last_order_seconds_ago": last_seconds,
        "total_orders": orders_count,
        "active_agents": agents_count,
        "categories": category_counts,
    }


async def list_public_projects(
    db: AsyncSession,
    *,
    category: str | None = None,
    service_type: str | None = None,
    q: str | None = None,
    sort: str = "created_at_desc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    base = select(Order)
    base = _apply_public_filters(base, category=category, service_type=service_type, q=q)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    if sort == "created_at_asc":
        base = base.order_by(Order.created_at.asc())
    elif sort == "updated_at_desc":
        base = base.order_by(Order.updated_at.desc())
    elif sort == "budget_desc":
        base = base.order_by(Order.budget_max.desc().nullslast(), Order.created_at.desc())
    else:
        base = base.order_by(Order.created_at.desc())

    orders = list((await db.execute(base.limit(limit).offset(offset))).scalars().all())
    if not orders:
        return [], total

    order_ids = [o.id for o in orders]
    est_stats = await db.execute(
        select(Estimate.order_id, func.count(Estimate.id))
        .where(
            Estimate.order_id.in_(order_ids),
            Estimate.status.in_([EstimateStatus.submitted, EstimateStatus.selected]),
        )
        .group_by(Estimate.order_id)
    )
    proposals_map = {row[0]: row[1] for row in est_stats.all()}

    client_map = await build_client_public_map(db, [o.client_id for o in orders])

    items = []
    for order in orders:
        desc = order.description.strip()
        items.append(
            {
                "id": order.id,
                "title": order.title,
                "description": order.description,
                "description_preview": desc[:220] + ("…" if len(desc) > 220 else ""),
                "service_type": order.service_type,
                "budget_min": order.budget_min,
                "budget_max": order.budget_max,
                "status": order.status.value,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "proposals_count": proposals_map.get(order.id, 0),
                "client": client_map.get(order.client_id),
            }
        )
    return items, total
