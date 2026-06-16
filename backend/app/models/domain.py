import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    draft = "draft"
    awaiting_estimate = "awaiting_estimate"
    estimated = "estimated"
    awaiting_payment = "awaiting_payment"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_requested = "revision_requested"
    completed = "completed"
    disputed = "disputed"
    cancelled = "cancelled"
    failed = "failed"


class AgentStatus(str, enum.Enum):
    draft = "draft"
    testing = "testing"
    active = "active"
    paused = "paused"
    degraded = "degraded"
    blocked = "blocked"


class EstimateStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    declined = "declined"
    expired = "expired"
    selected = "selected"


class TaskType(str, enum.Enum):
    estimate_requested = "estimate_requested"
    assigned = "assigned"
    revision_requested = "revision_requested"
    cancelled = "cancelled"
    agent_test_requested = "agent.test_requested"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    delivered = "delivered"
    completed = "completed"
    declined = "declined"
    expired = "expired"


class SenderType(str, enum.Enum):
    client = "client"
    agent = "agent"
    developer = "developer"
    admin = "admin"
    system = "system"


class WebhookEventStatus(str, enum.Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.draft, index=True
    )
    selected_agent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agents.id"), nullable=True)
    selected_estimate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estimates.id"), nullable=True)
    result_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    developer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status"), default=AgentStatus.draft, index=True
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    services: Mapped[list["AgentService"]] = relationship(back_populates="agent", cascade="all, delete-orphan")


class AgentService(Base):
    __tablename__ = "agent_services"
    __table_args__ = (UniqueConstraint("agent_id", "service_type", "language", name="uq_agent_service"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    supports_files: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_revisions: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    agent: Mapped["Agent"] = relationship(back_populates="services")


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    deadline_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EstimateStatus] = mapped_column(
        Enum(EstimateStatus, name="estimate_status"), default=EstimateStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType, name="task_type"), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status"), default=TaskStatus.pending)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType, name="sender_type"), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus, name="webhook_event_status"), default=WebhookEventStatus.pending
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModerationViolation(Base):
    __tablename__ = "moderation_violations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id"))
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
