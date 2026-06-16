from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import AuditLog, User, UserRole
from app.models.domain import Agent, AgentStatus, ModerationViolation, Order, WebhookEvent
from app.schemas.agent import AgentResponse
from app.schemas.auth import UserResponse
from app.schemas.order import MessageResponse, OrderResponse
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/block")
async def block_user(
    user_id: UUID,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="user.blocked", resource_type="user", resource_id=str(user_id))
    return {"status": "blocked"}


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/agents/{agent_id}/block")
async def block_agent(
    agent_id: UUID,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    agent.status = AgentStatus.blocked
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="agent.blocked", resource_type="agent", resource_id=str(agent_id))
    return {"status": "blocked"}


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return list(result.scalars().all())


@router.get("/violations", response_model=list[dict])
async def list_violations(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ModerationViolation).order_by(ModerationViolation.created_at.desc()).limit(100))
    violations = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "order_id": str(v.order_id),
            "sender_type": v.sender_type,
            "sender_id": v.sender_id,
            "reason": v.reason,
            "created_at": v.created_at.isoformat(),
        }
        for v in violations
    ]


@router.get("/webhooks", response_model=list[dict])
async def list_webhooks(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(100))
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "agent_id": str(e.agent_id),
            "event_type": e.event_type,
            "status": e.status.value,
            "attempts": e.attempts,
            "last_error": e.last_error,
            "created_at": e.created_at.isoformat(),
            "delivered_at": e.delivered_at.isoformat() if e.delivered_at else None,
        }
        for e in events
    ]


@router.get("/logs", response_model=list[dict])
async def list_logs(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "actor_type": log.actor_type,
            "actor_id": log.actor_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.post("/disputes/{order_id}/resolve")
async def resolve_dispute(
    order_id: UUID,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.domain import OrderStatus

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.status = OrderStatus.completed
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="dispute.resolved", resource_type="order", resource_id=str(order_id))
    return {"status": "resolved"}
