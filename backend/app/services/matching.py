from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis_client import get_redis_pool
from app.models.domain import Agent, AgentService, AgentStatus, Estimate, EstimateStatus, Order, OrderStatus, Task, TaskStatus, TaskType
from app.services.audit import log_action
from app.services.webhook import enqueue_webhook

settings = get_settings()
AGENT_TASK_QUEUE = "agent:{agent_id}:tasks"
AGENT_CACHE_KEY = "cache:agents:service:{service_type}"


async def find_matching_agents(db: AsyncSession, service_type: str, limit: int = 10) -> list[Agent]:
    redis = get_redis_pool()
    cache_key = AGENT_CACHE_KEY.format(service_type=service_type)
    cached = await redis.smembers(cache_key)
    agent_ids: list[str] = list(cached) if cached else []

    if not agent_ids:
        stmt = (
            select(Agent)
            .join(AgentService, AgentService.agent_id == Agent.id)
            .where(
                Agent.status == AgentStatus.active,
                AgentService.service_type == service_type,
                AgentService.is_active.is_(True),
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        agents = list(result.scalars().unique().all())
        if agents:
            pipe = redis.pipeline()
            for a in agents:
                pipe.sadd(cache_key, str(a.id))
            pipe.expire(cache_key, 60)
            await pipe.execute()
        return agents

    stmt = select(Agent).where(Agent.id.in_(agent_ids), Agent.status == AgentStatus.active).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def publish_order(db: AsyncSession, order: Order) -> list[Task]:
    if order.status != OrderStatus.draft:
        raise ValueError("Only draft orders can be published")

    agents = await find_matching_agents(db, order.service_type)
    if not agents:
        agents = await find_matching_agents(db, order.service_type, limit=3)

    order.status = OrderStatus.awaiting_estimate
    tasks: list[Task] = []
    redis = get_redis_pool()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.estimate_expire_hours)

    for agent in agents[:10]:
        estimate = Estimate(
            order_id=order.id,
            agent_id=agent.id,
            status=EstimateStatus.pending,
            expires_at=expires_at,
        )
        db.add(estimate)
        await db.flush()

        payload = {
            "order_id": str(order.id),
            "title": order.title,
            "description": order.description,
            "service_type": order.service_type,
            "budget_min": float(order.budget_min) if order.budget_min else None,
            "budget_max": float(order.budget_max) if order.budget_max else None,
            "files": [],
        }
        task = Task(
            order_id=order.id,
            agent_id=agent.id,
            type=TaskType.estimate_requested,
            status=TaskStatus.pending,
            payload_json=payload,
            expires_at=expires_at,
        )
        db.add(task)
        await db.flush()
        tasks.append(task)

        queue_key = AGENT_TASK_QUEUE.format(agent_id=agent.id)
        await redis.lpush(queue_key, str(task.id))

        if agent.webhook_url:
            await enqueue_webhook(
                db,
                agent,
                "task.estimate_requested",
                {
                    "task_id": str(task.id),
                    "order_id": str(order.id),
                    "type": "estimate_requested",
                    **payload,
                },
            )

    await log_action(
        db,
        actor_type="system",
        actor_id=None,
        action="order.published",
        resource_type="order",
        resource_id=str(order.id),
        details={"agent_count": len(tasks)},
    )
    return tasks


async def push_task_to_agent(agent_id: str, task_id: str) -> None:
    redis = get_redis_pool()
    await redis.lpush(AGENT_TASK_QUEUE.format(agent_id=agent_id), task_id)


async def pop_agent_tasks(agent_id: str, limit: int = 10) -> list[str]:
    redis = get_redis_pool()
    queue_key = AGENT_TASK_QUEUE.format(agent_id=agent_id)
    task_ids: list[str] = []
    for _ in range(limit):
        task_id = await redis.rpop(queue_key)
        if not task_id:
            break
        task_ids.append(task_id)
    return task_ids
