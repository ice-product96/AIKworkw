from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_agent
from app.core.redis_client import get_redis_pool
from app.models.domain import (
    Agent,
    Estimate,
    EstimateStatus,
    File,
    Message,
    Order,
    OrderStatus,
    SenderType,
    Task,
    TaskStatus,
    TaskType,
)
from app.schemas.agent_api import (
    AgentMessageCreate,
    DeclineRequest,
    EstimateSubmit,
    PollResponse,
    PollTaskResponse,
    ResultSubmit,
    StatusUpdate,
    TaskFileInfo,
)
from app.services.audit import log_action
from app.services.matching import pop_agent_tasks
from app.services.order_service import create_message, update_order_estimated_status
from app.services.storage import generate_presigned_url

router = APIRouter(prefix="/agent", tags=["agent"])


async def get_agent_task(db: AsyncSession, task_id: UUID, agent: Agent) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.agent_id == agent.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/tasks/poll", response_model=PollResponse)
async def poll_tasks(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis_pool()
    rate_key = f"ratelimit:agent:{agent.id}"
    if await redis.get(rate_key):
        return PollResponse(tasks=[])
    await redis.setex(rate_key, 1, "1")

    task_ids = await pop_agent_tasks(str(agent.id))
    if not task_ids:
        result = await db.execute(
            select(Task).where(Task.agent_id == agent.id, Task.status == TaskStatus.pending).limit(10)
        )
        pending = list(result.scalars().all())
        task_ids = [str(t.id) for t in pending]

    tasks_out: list[PollTaskResponse] = []
    for tid in task_ids:
        result = await db.execute(select(Task).where(Task.id == UUID(tid), Task.agent_id == agent.id))
        task = result.scalar_one_or_none()
        if not task or task.status != TaskStatus.pending:
            continue
        task.status = TaskStatus.delivered
        payload = task.payload_json or {}
        files: list[TaskFileInfo] = []
        if task.order_id:
            file_result = await db.execute(select(File).where(File.order_id == task.order_id))
            for f in file_result.scalars().all():
                files.append(
                    TaskFileInfo(
                        file_id=f.id,
                        filename=f.filename,
                        url=generate_presigned_url(f.storage_path),
                    )
                )
        order_result = await db.execute(select(Order).where(Order.id == task.order_id)) if task.order_id else None
        order = order_result.scalar_one_or_none() if order_result else None
        tasks_out.append(
            PollTaskResponse(
                task_id=task.id,
                order_id=task.order_id,
                type=task.type.value,
                service_type=payload.get("service_type") or (order.service_type if order else None),
                title=payload.get("title") or (order.title if order else None),
                description=payload.get("description") or (order.description if order else None),
                budget_min=payload.get("budget_min"),
                budget_max=payload.get("budget_max"),
                files=files,
            )
        )
    return PollResponse(tasks=tasks_out)


@router.post("/tasks/{task_id}/estimate")
async def submit_estimate(
    task_id: UUID,
    data: EstimateSubmit,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    if task.type != TaskType.estimate_requested:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task type")

    result = await db.execute(
        select(Estimate).where(Estimate.order_id == task.order_id, Estimate.agent_id == agent.id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")

    estimate.price = data.price
    estimate.deadline_hours = data.deadline_hours
    estimate.confidence = data.confidence
    estimate.message = data.message
    estimate.questions = data.questions
    estimate.status = EstimateStatus.submitted
    task.status = TaskStatus.completed

    if task.order_id:
        await update_order_estimated_status(db, task.order_id)

    await log_action(db, actor_type="agent", actor_id=str(agent.id), action="estimate.submitted", resource_type="task", resource_id=str(task_id))
    return {"status": "ok", "estimate_id": str(estimate.id)}


@router.post("/tasks/{task_id}/decline")
async def decline_task(
    task_id: UUID,
    data: DeclineRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    task.status = TaskStatus.declined

    if task.order_id:
        result = await db.execute(
            select(Estimate).where(Estimate.order_id == task.order_id, Estimate.agent_id == agent.id)
        )
        estimate = result.scalar_one_or_none()
        if estimate:
            estimate.status = EstimateStatus.declined
            estimate.decline_reason = data.reason

    await log_action(db, actor_type="agent", actor_id=str(agent.id), action="task.declined", resource_type="task", resource_id=str(task_id))
    return {"status": "declined"}


@router.post("/tasks/{task_id}/accept")
async def accept_task(
    task_id: UUID,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    if task.type != TaskType.assigned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not an assignment")
    task.status = TaskStatus.completed
    return {"status": "accepted"}


@router.post("/tasks/{task_id}/status")
async def update_status(
    task_id: UUID,
    data: StatusUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    if not task.order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No order linked")
    await log_action(
        db,
        actor_type="agent",
        actor_id=str(agent.id),
        action="task.status",
        resource_type="task",
        resource_id=str(task_id),
        details={"status": data.status, "progress": data.progress, "message": data.message},
    )
    return {"status": "ok"}


@router.post("/tasks/{task_id}/message")
async def agent_message(
    task_id: UUID,
    data: AgentMessageCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    if not task.order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No order linked")
    order_result = await db.execute(select(Order).where(Order.id == task.order_id))
    order = order_result.scalar_one()
    msg = await create_message(db, order, SenderType.agent, str(agent.id), data.text)
    response = {"id": str(msg.id), "is_blocked": msg.is_blocked}
    if msg.is_blocked:
        response["warning"] = "Message blocked by moderation filter"
    return response


@router.post("/tasks/{task_id}/result")
async def submit_result(
    task_id: UUID,
    data: ResultSubmit,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    task = await get_agent_task(db, task_id, agent)
    if not task.order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No order linked")

    order_result = await db.execute(select(Order).where(Order.id == task.order_id))
    order = order_result.scalar_one()
    if order.status not in (OrderStatus.in_progress, OrderStatus.revision_requested):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not in progress")

    order.result_text = data.text
    order.status = OrderStatus.submitted
    task.status = TaskStatus.completed

    await create_message(db, order, SenderType.agent, str(agent.id), data.text)
    await log_action(db, actor_type="agent", actor_id=str(agent.id), action="result.submitted", resource_type="order", resource_id=str(order.id))
    return {"status": "submitted", "order_status": order.status.value}
