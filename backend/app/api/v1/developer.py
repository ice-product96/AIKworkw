from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import generate_api_key, generate_webhook_secret, hash_api_key
from app.models import User, UserRole
from app.models.domain import Agent, AgentService, AgentStatus, Estimate, EstimateStatus, Order, OrderStatus, Task, TaskStatus, TaskType
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentServiceCreate,
    AgentServiceResponse,
    AgentStatsResponse,
    AgentUpdate,
    ApiKeyResponse,
)
from app.services.audit import log_action
from app.services.matching import push_task_to_agent
from app.services.webhook import enqueue_webhook

router = APIRouter(prefix="/developer/agents", tags=["developer"])


async def get_owned_agent(db: AsyncSession, agent_id: UUID, user: User) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.developer_id == user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = Agent(
        developer_id=user.id,
        name=data.name,
        description=data.description,
        webhook_url=data.webhook_url,
        webhook_secret=generate_webhook_secret(),
        status=AgentStatus.draft,
    )
    db.add(agent)
    await db.flush()
    await log_action(db, actor_type="developer", actor_id=str(user.id), action="agent.created", resource_type="agent", resource_id=str(agent.id))
    return agent


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.developer_id == user.id).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned_agent(db, agent_id, user)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    if data.name is not None:
        agent.name = data.name
    if data.description is not None:
        agent.description = data.description
    if data.webhook_url is not None:
        agent.webhook_url = data.webhook_url
    if data.status is not None:
        try:
            agent.status = AgentStatus(data.status)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc
    return agent


@router.post("/{agent_id}/services", response_model=AgentServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_service(
    agent_id: UUID,
    data: AgentServiceCreate,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    service = AgentService(
        agent_id=agent.id,
        service_type=data.service_type,
        language=data.language,
        min_price=data.min_price,
        max_price=data.max_price,
        supports_files=data.supports_files,
        supports_revisions=data.supports_revisions,
        is_active=data.is_active,
    )
    db.add(service)
    await db.flush()
    if agent.status == AgentStatus.draft:
        agent.status = AgentStatus.active
    return service


@router.get("/{agent_id}/services", response_model=list[AgentServiceResponse])
async def list_services(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    result = await db.execute(select(AgentService).where(AgentService.agent_id == agent.id))
    return list(result.scalars().all())


@router.post("/{agent_id}/api-key", response_model=ApiKeyResponse)
async def generate_key(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    full_key, prefix, key_hash = generate_api_key()
    agent.api_key_hash = key_hash
    agent.api_key_prefix = prefix
    return ApiKeyResponse(api_key=full_key, prefix=prefix)


@router.get("/{agent_id}/api-key", response_model=dict)
async def get_key_info(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    return {
        "has_api_key": bool(agent.api_key_hash),
        "prefix": agent.api_key_prefix,
        "message": "Full key is only shown once at generation/rotation.",
    }


@router.post("/{agent_id}/rotate-api-key", response_model=ApiKeyResponse)
async def rotate_key(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    full_key, prefix, key_hash = generate_api_key()
    agent.api_key_hash = key_hash
    agent.api_key_prefix = prefix
    return ApiKeyResponse(api_key=full_key, prefix=prefix)


@router.post("/{agent_id}/test")
async def test_agent(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    payload = {"agent_id": str(agent.id), "message": "Test task from platform"}
    task = Task(
        agent_id=agent.id,
        type=TaskType.agent_test_requested,
        status=TaskStatus.pending,
        payload_json=payload,
    )
    db.add(task)
    await db.flush()
    await push_task_to_agent(str(agent.id), str(task.id))
    if agent.webhook_url:
        await enqueue_webhook(db, agent, "agent.test_requested", {"task_id": str(task.id), **payload})
    return {"task_id": str(task.id), "status": "queued"}


@router.get("/{agent_id}/stats", response_model=AgentStatsResponse)
async def agent_stats(
    agent_id: UUID,
    user: User = Depends(require_roles(UserRole.developer)),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_owned_agent(db, agent_id, user)
    total = await db.execute(
        select(func.count()).select_from(Estimate).where(Estimate.agent_id == agent.id)
    )
    completed = await db.execute(
        select(func.count()).select_from(Order).where(
            Order.selected_agent_id == agent.id,
            Order.status == OrderStatus.completed,
        )
    )
    revenue = await db.execute(
        select(func.coalesce(func.sum(Estimate.price), 0)).where(
            Estimate.agent_id == agent.id,
            Estimate.status == EstimateStatus.selected,
        )
    )
    return AgentStatsResponse(
        total_orders=total.scalar_one(),
        completed_orders=completed.scalar_one(),
        total_revenue=Decimal(str(revenue.scalar_one())),
        average_rating=agent.rating,
    )
