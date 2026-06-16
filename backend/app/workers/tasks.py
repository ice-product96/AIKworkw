import asyncio

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aikworkw",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="deliver_webhook")
def deliver_webhook(event_id: str) -> bool:
    from app.core.database import async_session_factory
    from app.services.webhook import deliver_webhook_event

    async def _run():
        async with async_session_factory() as session:
            try:
                result = await deliver_webhook_event(session, __import__("uuid").UUID(event_id))
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    return run_async(_run())


@celery_app.task(name="expire_estimates")
def expire_estimates() -> int:
    from datetime import UTC, datetime

    from sqlalchemy import select, update

    from app.core.database import async_session_factory
    from app.models.domain import Estimate, EstimateStatus, Order, OrderStatus

    async def _run():
        now = datetime.now(UTC)
        async with async_session_factory() as session:
            result = await session.execute(
                select(Estimate).where(
                    Estimate.status == EstimateStatus.pending,
                    Estimate.expires_at <= now,
                )
            )
            estimates = result.scalars().all()
            count = 0
            for est in estimates:
                est.status = EstimateStatus.expired
                count += 1
            await session.commit()
            return count

    return run_async(_run())


@celery_app.task(name="check_deadlines")
def check_deadlines() -> int:
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.domain import Order, OrderStatus

    async def _run():
        now = datetime.now(UTC)
        async with async_session_factory() as session:
            result = await session.execute(
                select(Order).where(
                    Order.deadline <= now,
                    Order.status.in_([OrderStatus.in_progress, OrderStatus.revision_requested]),
                )
            )
            orders = result.scalars().all()
            for order in orders:
                await __import__("app.services.audit", fromlist=["log_action"]).log_action(
                    session,
                    actor_type="system",
                    actor_id=None,
                    action="order.deadline_passed",
                    resource_type="order",
                    resource_id=str(order.id),
                )
            await session.commit()
            return len(orders)

    return run_async(_run())
