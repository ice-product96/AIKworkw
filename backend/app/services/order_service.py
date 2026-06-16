from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import User
from app.models.domain import (
    Agent,
    AgentStatus,
    Estimate,
    EstimateStatus,
    Message,
    ModerationViolation,
    Order,
    OrderStatus,
    SenderType,
    Task,
    TaskStatus,
    TaskType,
)
from app.services.audit import log_action
from app.services.matching import publish_order, push_task_to_agent
from app.services.moderation import check_message
from app.services.webhook import enqueue_webhook

settings = get_settings()


async def get_order_for_client(db: AsyncSession, order_id: UUID, user: User) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.client_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return order


async def create_message(
    db: AsyncSession,
    order: Order,
    sender_type: SenderType,
    sender_id: str,
    text: str,
) -> Message:
    is_blocked, reason = check_message(text)
    msg = Message(
        order_id=order.id,
        sender_type=sender_type,
        sender_id=sender_id,
        text=text,
        is_blocked=is_blocked,
        moderation_reason=reason,
    )
    db.add(msg)
    await db.flush()

    if is_blocked:
        violation = ModerationViolation(
            message_id=msg.id,
            order_id=order.id,
            sender_type=sender_type.value,
            sender_id=sender_id,
            reason=reason or "blocked",
        )
        db.add(violation)
        await log_action(
            db,
            actor_type=sender_type.value,
            actor_id=sender_id,
            action="message.blocked",
            resource_type="message",
            resource_id=str(msg.id),
            details={"reason": reason},
        )
    return msg


async def select_estimate(db: AsyncSession, order: Order, estimate_id: UUID) -> Order:
    if order.status not in (OrderStatus.awaiting_estimate, OrderStatus.estimated):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status")

    result = await db.execute(
        select(Estimate).where(Estimate.id == estimate_id, Estimate.order_id == order.id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.status != EstimateStatus.submitted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estimate not available")

    estimate.status = EstimateStatus.selected
    order.selected_estimate_id = estimate.id
    order.selected_agent_id = estimate.agent_id
    order.status = OrderStatus.awaiting_payment

    await log_action(
        db,
        actor_type="client",
        actor_id=str(order.client_id),
        action="estimate.selected",
        resource_type="order",
        resource_id=str(order.id),
        details={"estimate_id": str(estimate_id)},
    )
    return order


async def mock_pay_order(db: AsyncSession, order: Order) -> Order:
    if order.status != OrderStatus.awaiting_payment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not awaiting payment")
    if not order.selected_agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No agent selected")

    order.status = OrderStatus.in_progress

    agent_result = await db.execute(select(Agent).where(Agent.id == order.selected_agent_id))
    agent = agent_result.scalar_one()

    payload = {
        "order_id": str(order.id),
        "title": order.title,
        "description": order.description,
        "service_type": order.service_type,
    }
    task = Task(
        order_id=order.id,
        agent_id=agent.id,
        type=TaskType.assigned,
        status=TaskStatus.pending,
        payload_json=payload,
    )
    db.add(task)
    await db.flush()
    await push_task_to_agent(str(agent.id), str(task.id))

    if agent.webhook_url:
        await enqueue_webhook(
            db,
            agent,
            "task.assigned",
            {"task_id": str(task.id), "order_id": str(order.id), "type": "assigned", **payload},
        )

    await log_action(
        db,
        actor_type="client",
        actor_id=str(order.client_id),
        action="order.paid",
        resource_type="order",
        resource_id=str(order.id),
    )
    return order


async def accept_order(db: AsyncSession, order: Order) -> Order:
    if order.status != OrderStatus.submitted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not submitted")
    order.status = OrderStatus.completed
    await log_action(
        db,
        actor_type="client",
        actor_id=str(order.client_id),
        action="order.accepted",
        resource_type="order",
        resource_id=str(order.id),
    )
    return order


async def request_revision(db: AsyncSession, order: Order, message: str) -> Order:
    if order.status != OrderStatus.submitted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not submitted")
    order.status = OrderStatus.revision_requested
    await create_message(db, order, SenderType.client, str(order.client_id), message)

    if order.selected_agent_id:
        agent_result = await db.execute(select(Agent).where(Agent.id == order.selected_agent_id))
        agent = agent_result.scalar_one_or_none()
        if agent:
            payload = {"order_id": str(order.id), "message": message}
            task = Task(
                order_id=order.id,
                agent_id=agent.id,
                type=TaskType.revision_requested,
                status=TaskStatus.pending,
                payload_json=payload,
            )
            db.add(task)
            await db.flush()
            await push_task_to_agent(str(agent.id), str(task.id))
            if agent.webhook_url:
                await enqueue_webhook(db, agent, "task.revision_requested", {"task_id": str(task.id), **payload})

    return order


async def open_dispute(db: AsyncSession, order: Order, reason: str) -> Order:
    if order.status not in (OrderStatus.submitted, OrderStatus.revision_requested, OrderStatus.in_progress):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot dispute in current status")
    order.status = OrderStatus.disputed
    order.dispute_reason = reason
    await log_action(
        db,
        actor_type="client",
        actor_id=str(order.client_id),
        action="order.disputed",
        resource_type="order",
        resource_id=str(order.id),
        details={"reason": reason},
    )
    return order


async def update_order_estimated_status(db: AsyncSession, order_id: UUID) -> None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status != OrderStatus.awaiting_estimate:
        return
    count_result = await db.execute(
        select(func.count()).select_from(Estimate).where(
            Estimate.order_id == order_id,
            Estimate.status == EstimateStatus.submitted,
        )
    )
    if count_result.scalar_one() > 0:
        order.status = OrderStatus.estimated
