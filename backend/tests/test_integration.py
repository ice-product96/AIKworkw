from decimal import Decimal

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.services.moderation import check_message


def test_moderation_blocks_email():
    blocked, reason = check_message("Напишите на test@example.com")
    assert blocked is True
    assert reason == "email"


def test_moderation_blocks_contact_phrase():
    blocked, reason = check_message("Свяжись со мной вне платформы")
    assert blocked is True


def test_moderation_allows_normal_text():
    blocked, _ = check_message("Когда будет готов первый макет?")
    assert blocked is False


@pytest.mark.asyncio
async def test_order_flow(client: AsyncClient):
    # Register client
    await client.post("/api/v1/auth/register", json={"email": "c@t.com", "password": "password123", "role": "client"})
    cl = await client.post("/api/v1/auth/login", json={"email": "c@t.com", "password": "password123"})
    ctoken = cl.json()["access_token"]
    headers = {"Authorization": f"Bearer {ctoken}"}

    # Register developer + agent
    await client.post("/api/v1/auth/register", json={"email": "d@t.com", "password": "password123", "role": "developer"})
    dl = await client.post("/api/v1/auth/login", json={"email": "d@t.com", "password": "password123"})
    dtoken = dl.json()["access_token"]
    dheaders = {"Authorization": f"Bearer {dtoken}"}

    agent = await client.post("/api/v1/developer/agents", json={"name": "Bot"}, headers=dheaders)
    agent_id = agent.json()["id"]
    await client.post(
        f"/api/v1/developer/agents/{agent_id}/services",
        json={"service_type": "landing_page"},
        headers=dheaders,
    )
    key_resp = await client.post(f"/api/v1/developer/agents/{agent_id}/api-key", headers=dheaders)
    api_key = key_resp.json()["api_key"]
    aheaders = {"Authorization": f"Bearer {api_key}"}

    # Create and publish order
    order = await client.post(
        "/api/v1/orders",
        json={
            "title": "Landing page",
            "description": "Need a landing page for course",
            "service_type": "landing_page",
            "budget_min": 10000,
            "budget_max": 30000,
        },
        headers=headers,
    )
    order_id = order.json()["id"]
    with patch("app.services.webhook.enqueue_webhook", new_callable=AsyncMock, return_value=None), patch(
        "app.workers.tasks.deliver_webhook.delay"
    ):
        pub = await client.post(f"/api/v1/orders/{order_id}/publish", headers=headers)
    assert pub.status_code == 200

    # Agent polls and estimates
    poll = await client.get("/api/v1/agent/tasks/poll", headers=aheaders)
    assert poll.status_code == 200
    tasks = poll.json()["tasks"]
    assert len(tasks) >= 1
    task_id = tasks[0]["task_id"]

    est = await client.post(
        f"/api/v1/agent/tasks/{task_id}/estimate",
        json={"price": 15000, "deadline_hours": 48, "confidence": 0.9, "message": "OK", "questions": []},
        headers=aheaders,
    )
    assert est.status_code == 200

    # Client selects estimate
    estimates = await client.get(f"/api/v1/orders/{order_id}/estimates", headers=headers)
    estimate_id = estimates.json()[0]["id"]
    sel = await client.post(f"/api/v1/orders/{order_id}/estimates/{estimate_id}/select", headers=headers)
    assert sel.json()["status"] == "awaiting_payment"

    # Mock pay
    with patch("app.services.webhook.enqueue_webhook", new_callable=AsyncMock, return_value=None), patch(
        "app.workers.tasks.deliver_webhook.delay"
    ):
        pay = await client.post(f"/api/v1/orders/{order_id}/pay", headers=headers)
    assert pay.json()["status"] == "in_progress"

    # Agent submits result
    with patch("app.services.webhook.enqueue_webhook", new_callable=AsyncMock, return_value=None):
        poll2 = await client.get("/api/v1/agent/tasks/poll", headers=aheaders)
    assigned = [t for t in poll2.json()["tasks"] if t["type"] == "assigned"]
    assert assigned
    result = await client.post(
        f"/api/v1/agent/tasks/{assigned[0]['task_id']}/result",
        json={"text": "Done", "files": []},
        headers=aheaders,
    )
    assert result.json()["status"] == "submitted"

    accept = await client.post(f"/api/v1/orders/{order_id}/accept", headers=headers)
    assert accept.json()["status"] == "completed"
