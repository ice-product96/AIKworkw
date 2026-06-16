import json
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import sign_webhook_payload
from app.models.domain import Agent, AgentStatus, WebhookEvent, WebhookEventStatus

RETRY_DELAYS = [60, 300, 900, 3600]


async def enqueue_webhook(
    db: AsyncSession,
    agent: Agent,
    event_type: str,
    payload: dict,
) -> WebhookEvent | None:
    if not agent.webhook_url:
        return None
    event = WebhookEvent(
        agent_id=agent.id,
        event_type=event_type,
        payload=payload,
        status=WebhookEventStatus.pending,
    )
    db.add(event)
    await db.flush()

    from app.workers.tasks import deliver_webhook

    deliver_webhook.delay(str(event.id))
    return event


async def deliver_webhook_event(db: AsyncSession, event_id: uuid.UUID) -> bool:
    from sqlalchemy import select

    result = await db.execute(
        select(WebhookEvent).where(WebhookEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return False

    agent_result = await db.execute(select(Agent).where(Agent.id == event.agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent or not agent.webhook_url or not agent.webhook_secret:
        event.status = WebhookEventStatus.failed
        event.last_error = "Agent webhook not configured"
        return False

    body = json.dumps(event.payload, ensure_ascii=False).encode()
    timestamp = str(int(datetime.now(UTC).timestamp()))
    signature = sign_webhook_payload(agent.webhook_secret, timestamp, body)

    headers = {
        "Content-Type": "application/json",
        "X-Agent-Event-Id": str(event.id),
        "X-Agent-Timestamp": timestamp,
        "X-Agent-Signature": signature,
    }

    event.attempts += 1
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(agent.webhook_url, content=body, headers=headers)
            response.raise_for_status()
        event.status = WebhookEventStatus.delivered
        event.delivered_at = datetime.now(UTC)
        event.last_error = None
        return True
    except Exception as exc:
        event.last_error = str(exc)
        if event.attempts >= len(RETRY_DELAYS):
            event.status = WebhookEventStatus.failed
            agent.status = AgentStatus.degraded
        else:
            from app.workers.tasks import deliver_webhook

            delay = RETRY_DELAYS[event.attempts - 1]
            deliver_webhook.apply_async(args=[str(event.id)], countdown=delay)
        return False
