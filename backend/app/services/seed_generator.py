import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, UserRole
from app.models.domain import (
    Agent,
    AgentService,
    AgentStatus,
    Estimate,
    EstimateStatus,
    Order,
    OrderStatus,
    SenderType,
    Task,
    TaskStatus,
    TaskType,
)
from app.services.audit import log_action
from app.services.llm import LLMError, chat_json
from app.services.order_service import create_message, update_order_estimated_status
from app.services.matching import publish_order

SERVICE_TYPES = [
    "landing_page",
    "seo_audit",
    "python_script",
    "telegram_bot",
    "copywriting",
    "design_banner",
    "data_processing",
    "document_analysis",
]

DEMO_PASSWORD = "demo123456"


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:80] or f"item-{uuid.uuid4().hex[:8]}"


async def _generate_batch_data(db: AsyncSession, params: dict[str, int]) -> dict[str, Any] | None:
    try:
        return await chat_json(
            db,
            system=(
                "Ты генератор демо-данных для маркетплейса AI-агентов AIKworkw. "
                "Отвечай только валидным JSON на русском языке."
            ),
            user=f"""Сгенерируй демо-данные для платформы:
- {params['clients']} клиентов (имя, email @demo.aikworkw.local, компания)
- {params['developers']} разработчиков (имя, email @demo.aikworkw.local)
- {params['agents']} AI-агентов (name, description, service_types из списка {SERVICE_TYPES}, developer_index 0..{params['developers']-1})
- {params['orders']} заказов (title, description 2-4 предложения, service_type, budget_min, budget_max, client_index)

JSON формат:
{{
  "clients": [{{"name": "...", "email": "...", "company": "..."}}],
  "developers": [{{"name": "...", "email": "..."}}],
  "agents": [{{"name": "...", "description": "...", "service_types": ["..."], "developer_index": 0}}],
  "orders": [{{"title": "...", "description": "...", "service_type": "...", "budget_min": 5000, "budget_max": 15000, "client_index": 0}}]
}}""",
        )
    except LLMError:
        return None


def _fallback_data(params: dict[str, int]) -> dict[str, Any]:
    clients = [
        {"name": f"Клиент {i+1}", "email": f"demo.client{i+1}@demo.aikworkw.local", "company": f"Компания {i+1}"}
        for i in range(params["clients"])
    ]
    developers = [
        {"name": f"Разработчик {i+1}", "email": f"demo.dev{i+1}@demo.aikworkw.local"}
        for i in range(params["developers"])
    ]
    agents = []
    for i in range(params["agents"]):
        st = SERVICE_TYPES[i % len(SERVICE_TYPES)]
        agents.append({
            "name": f"AI Agent {st.replace('_', ' ').title()} #{i+1}",
            "description": f"Специализированный агент для услуги {st}. Быстрые оценки и качественное выполнение.",
            "service_types": [st],
            "developer_index": i % max(params["developers"], 1),
        })
    orders = []
    for i in range(params["orders"]):
        st = SERVICE_TYPES[i % len(SERVICE_TYPES)]
        orders.append({
            "title": f"Заказ: {st.replace('_', ' ')} #{i+1}",
            "description": f"Нужна услуга {st}. Подробное ТЗ для демонстрации активности на площадке AIKworkw.",
            "service_type": st,
            "budget_min": 3000 + i * 500,
            "budget_max": 8000 + i * 1000,
            "client_index": i % max(params["clients"], 1),
        })
    return {"clients": clients, "developers": developers, "agents": agents, "orders": orders}


async def _llm_estimate(db: AsyncSession, order: Order, agent: Agent) -> dict[str, Any]:
    try:
        return await chat_json(
            db,
            system="Ты AI-агент на маркетплейсе. Сгенерируй оценку заказа. JSON только.",
            user=f"""Заказ: {order.title}
Описание: {order.description}
Услуга: {order.service_type}
Бюджет: {order.budget_min}-{order.budget_max}

Агент: {agent.name}
{agent.description}

Верни JSON: {{"price": 7500, "deadline_hours": 48, "confidence": 0.85, "message": "текст оценки 2-3 предложения"}}""",
        )
    except LLMError:
        return {
            "price": float(order.budget_min or 5000),
            "deadline_hours": 48,
            "confidence": 0.8,
            "message": f"Готов выполнить «{order.title}» в срок до 48 часов. Имею опыт в {order.service_type}.",
        }


async def _llm_result(db: AsyncSession, order: Order, agent: Agent) -> str:
    try:
        data = await chat_json(
            db,
            system="Ты AI-агент. Сгенерируй результат выполнения заказа. JSON: {\"result\": \"...\"}",
            user=f"Заказ: {order.title}\nОписание: {order.description}\nАгент: {agent.name}",
        )
        return data.get("result", "Работа выполнена согласно ТЗ.")
    except LLMError:
        return f"## Результат\n\nЗаказ «{order.title}» выполнен.\n\nПодготовлено решение по услуге {order.service_type}."


async def _llm_chat(db: AsyncSession, order: Order, role: str) -> str:
    try:
        data = await chat_json(
            db,
            system="Сгенерируй одно короткое сообщение в чате заказа. JSON: {\"text\": \"...\"}",
            user=f"Роль: {role}. Заказ: {order.title}. Статус: {order.status.value}",
        )
        return data.get("text", "Здравствуйте! Готов обсудить детали.")
    except LLMError:
        if role == "client":
            return "Добрый день! Подскажите, когда сможете начать работу?"
        return "Здравствуйте! Могу приступить после подтверждения оплаты."


async def generate_platform_activity(
    db: AsyncSession,
    *,
    admin_id: uuid.UUID,
    num_clients: int = 3,
    num_developers: int = 2,
    num_agents: int = 5,
    num_orders: int = 8,
    complete_ratio: float = 0.4,
) -> dict[str, Any]:
    num_clients = min(max(num_clients, 1), 20)
    num_developers = min(max(num_developers, 1), 10)
    num_agents = min(max(num_agents, 1), 30)
    num_orders = min(max(num_orders, 1), 30)

    params = {
        "clients": num_clients,
        "developers": num_developers,
        "agents": num_agents,
        "orders": num_orders,
    }
    batch = await _generate_batch_data(db, params) or _fallback_data(params)

    created_users: list[User] = []
    created_agents: list[Agent] = []
    created_orders: list[Order] = []

    for dev in batch.get("developers", []):
        email = dev.get("email", f"demo.dev{uuid.uuid4().hex[:6]}@demo.aikworkw.local")
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            continue
        user = User(
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=UserRole.developer,
        )
        db.add(user)
        await db.flush()
        created_users.append(user)

    dev_users = [u for u in created_users if u.role == UserRole.developer]
    if not dev_users:
        result = await db.execute(select(User).where(User.role == UserRole.developer).limit(num_developers))
        dev_users = list(result.scalars().all())

    for client in batch.get("clients", []):
        email = client.get("email", f"demo.client{uuid.uuid4().hex[:6]}@demo.aikworkw.local")
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            continue
        user = User(
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=UserRole.client,
        )
        db.add(user)
        await db.flush()
        created_users.append(user)

    client_users = [u for u in created_users if u.role == UserRole.client]
    if not client_users:
        result = await db.execute(select(User).where(User.role == UserRole.client).limit(num_clients))
        client_users = list(result.scalars().all())

    for i, ag in enumerate(batch.get("agents", [])):
        if not dev_users:
            break
        dev_idx = min(ag.get("developer_index", 0), len(dev_users) - 1)
        agent = Agent(
            developer_id=dev_users[dev_idx].id,
            name=ag.get("name", f"Demo Agent {i+1}"),
            description=ag.get("description", "Демо-агент платформы"),
            status=AgentStatus.active,
            rating=Decimal("4.50") + Decimal(str((i % 5) * 0.1)),
        )
        db.add(agent)
        await db.flush()
        for st in ag.get("service_types", [SERVICE_TYPES[i % len(SERVICE_TYPES)]]):
            if st not in SERVICE_TYPES:
                st = SERVICE_TYPES[0]
            db.add(AgentService(agent_id=agent.id, service_type=st, min_price=Decimal("1000"), max_price=Decimal("50000")))
        created_agents.append(agent)

    for i, ord_data in enumerate(batch.get("orders", [])):
        if not client_users:
            break
        c_idx = min(ord_data.get("client_index", 0), len(client_users) - 1)
        st = ord_data.get("service_type", SERVICE_TYPES[i % len(SERVICE_TYPES)])
        if st not in SERVICE_TYPES:
            st = SERVICE_TYPES[0]
        order = Order(
            client_id=client_users[c_idx].id,
            title=ord_data.get("title", f"Демо-заказ {i+1}"),
            description=ord_data.get("description", "Демо-описание заказа"),
            service_type=st,
            budget_min=Decimal(str(ord_data.get("budget_min", 5000))),
            budget_max=Decimal(str(ord_data.get("budget_max", 15000))),
            status=OrderStatus.draft,
        )
        db.add(order)
        await db.flush()
        created_orders.append(order)

    estimates_count = 0
    messages_count = 0
    completed_count = 0

    for idx, order in enumerate(created_orders):
        try:
            await publish_order(db, order)
        except ValueError:
            continue

        await create_message(
            db, order, SenderType.client, str(order.client_id),
            await _llm_chat(db, order, "client"),
        )
        messages_count += 1

        est_result = await db.execute(
            select(Estimate).where(Estimate.order_id == order.id, Estimate.status == EstimateStatus.pending)
        )
        estimates = list(est_result.scalars().all())
        submitted: list[Estimate] = []

        for est in estimates[:3]:
            agent_result = await db.execute(select(Agent).where(Agent.id == est.agent_id))
            agent = agent_result.scalar_one()
            est_data = await _llm_estimate(db, order, agent)
            est.price = Decimal(str(est_data.get("price", 5000)))
            est.deadline_hours = int(est_data.get("deadline_hours", 48))
            est.confidence = Decimal(str(est_data.get("confidence", 0.8)))
            est.message = est_data.get("message", "Готов выполнить заказ.")
            est.status = EstimateStatus.submitted
            task_result = await db.execute(
                select(Task).where(
                    Task.order_id == order.id,
                    Task.agent_id == agent.id,
                    Task.type == TaskType.estimate_requested,
                )
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.status = TaskStatus.completed
            await create_message(db, order, SenderType.agent, str(agent.id), est.message)
            messages_count += 1
            estimates_count += 1
            submitted.append(est)

        await update_order_estimated_status(db, order.id)
        await db.refresh(order)

        if submitted and idx / max(len(created_orders), 1) < complete_ratio:
            chosen = submitted[0]
            chosen.status = EstimateStatus.selected
            order.selected_estimate_id = chosen.id
            order.selected_agent_id = chosen.agent_id
            order.status = OrderStatus.awaiting_payment

            order.status = OrderStatus.in_progress
            agent_result = await db.execute(select(Agent).where(Agent.id == chosen.agent_id))
            agent = agent_result.scalar_one()
            result_text = await _llm_result(db, order, agent)
            order.result_text = result_text
            order.status = OrderStatus.submitted
            await create_message(db, order, SenderType.agent, str(agent.id), "Работа сдана. Жду вашего подтверждения.")
            messages_count += 1
            order.status = OrderStatus.completed
            completed_count += 1

    await log_action(
        db,
        actor_type="admin",
        actor_id=str(admin_id),
        action="ai.generate_activity",
        details={
            "users": len(created_users),
            "agents": len(created_agents),
            "orders": len(created_orders),
            "estimates": estimates_count,
            "messages": messages_count,
            "completed": completed_count,
        },
    )

    return {
        "users_created": len(created_users),
        "agents_created": len(created_agents),
        "orders_created": len(created_orders),
        "estimates_created": estimates_count,
        "messages_created": messages_count,
        "orders_completed": completed_count,
        "demo_password": DEMO_PASSWORD,
    }
