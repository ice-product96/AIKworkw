from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.domain import Agent, Order, OrderStatus
from app.schemas.profile import ClientPublicInfo, ProfileResponse

PUBLISHED_STATUSES = {
    OrderStatus.awaiting_estimate,
    OrderStatus.estimated,
    OrderStatus.awaiting_payment,
    OrderStatus.in_progress,
    OrderStatus.submitted,
    OrderStatus.revision_requested,
    OrderStatus.completed,
    OrderStatus.disputed,
}


def default_display_name(user: User) -> str:
    if user.display_name:
        return user.display_name
    return user.email.split("@")[0]


def avatar_url_for(user: User) -> str | None:
    if not user.avatar_path:
        return None
    version = int(user.updated_at.timestamp()) if user.updated_at else 0
    return f"/api/v1/profile/avatars/{user.id}?v={version}"


def compute_level(projects_posted: int, completed: int) -> int:
    score = projects_posted + completed * 2
    if score >= 50:
        return 5
    if score >= 25:
        return 4
    if score >= 10:
        return 3
    if score >= 3:
        return 2
    return 1


async def _client_stats(db: AsyncSession, client_id: UUID) -> tuple[int, int, int]:
    posted = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.client_id == client_id, Order.status.in_(list(PUBLISHED_STATUSES)))
        )
    ).scalar_one()
    completed = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.client_id == client_id, Order.status == OrderStatus.completed)
        )
    ).scalar_one()
    hire_rate = round(completed / posted * 100) if posted else 0
    return posted, completed, hire_rate


async def _developer_stats(db: AsyncSession, user_id: UUID) -> tuple[int, int]:
    agents = (
        await db.execute(select(func.count()).select_from(Agent).where(Agent.developer_id == user_id))
    ).scalar_one()
    completed = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .join(Agent, Agent.id == Order.selected_agent_id)
            .where(Agent.developer_id == user_id, Order.status == OrderStatus.completed)
        )
    ).scalar_one()
    return agents, completed


async def build_profile_response(db: AsyncSession, user: User) -> ProfileResponse:
    posted, completed_client, hire_rate = await _client_stats(db, user.id)
    agents_count, completed_dev = (0, 0)
    if user.role.value == "developer":
        agents_count, completed_dev = await _developer_stats(db, user.id)
    level = compute_level(posted if user.role.value == "client" else agents_count, completed_client + completed_dev)
    return ProfileResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        display_name=user.display_name,
        bio=user.bio,
        company=user.company,
        location=user.location,
        website=user.website,
        developer_title=user.developer_title,
        avatar_url=avatar_url_for(user),
        level=level,
        projects_posted=posted,
        hire_rate_percent=hire_rate,
        agents_count=agents_count,
        completed_as_client=completed_client,
        completed_as_developer=completed_dev,
        created_at=user.created_at.isoformat(),
    )


async def build_client_public_map(db: AsyncSession, client_ids: list[UUID]) -> dict[UUID, ClientPublicInfo]:
    if not client_ids:
        return {}
    unique_ids = list(set(client_ids))
    result = await db.execute(select(User).where(User.id.in_(unique_ids)))
    users = {u.id: u for u in result.scalars().all()}

    posted_q = (
        select(Order.client_id, func.count())
        .where(Order.client_id.in_(unique_ids), Order.status.in_(list(PUBLISHED_STATUSES)))
        .group_by(Order.client_id)
    )
    posted_map = {row[0]: row[1] for row in (await db.execute(posted_q)).all()}

    completed_q = (
        select(Order.client_id, func.count())
        .where(Order.client_id.in_(unique_ids), Order.status == OrderStatus.completed)
        .group_by(Order.client_id)
    )
    completed_map = {row[0]: row[1] for row in (await db.execute(completed_q)).all()}

    out: dict[UUID, ClientPublicInfo] = {}
    for cid in unique_ids:
        user = users.get(cid)
        if not user:
            continue
        posted = posted_map.get(cid, 0)
        completed = completed_map.get(cid, 0)
        hire_rate = round(completed / posted * 100) if posted else 0
        out[cid] = ClientPublicInfo(
            id=cid,
            display_name=default_display_name(user),
            avatar_url=avatar_url_for(user),
            level=compute_level(posted, completed),
            projects_posted=posted,
            hire_rate_percent=hire_rate,
            company=user.company,
        )
    return out
