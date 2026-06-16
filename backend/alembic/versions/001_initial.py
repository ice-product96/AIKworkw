"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("client", "developer", "admin", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(100)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("developer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("api_key_hash", sa.String(255)),
        sa.Column("api_key_prefix", sa.String(20)),
        sa.Column("webhook_url", sa.String(500)),
        sa.Column("webhook_secret", sa.String(255)),
        sa.Column("status", sa.Enum("draft", "testing", "active", "paused", "degraded", "blocked", name="agent_status"), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_agents_developer_id", "agents", ["developer_id"])
    op.create_index("ix_agents_api_key_prefix", "agents", ["api_key_prefix"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("service_type", sa.String(100), nullable=False),
        sa.Column("budget_min", sa.Numeric(12, 2)),
        sa.Column("budget_max", sa.Numeric(12, 2)),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Enum("draft", "awaiting_estimate", "estimated", "awaiting_payment", "in_progress", "submitted", "revision_requested", "completed", "disputed", "cancelled", "failed", name="order_status"), nullable=False),
        sa.Column("selected_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("selected_estimate_id", postgresql.UUID(as_uuid=True)),
        sa.Column("result_text", sa.Text()),
        sa.Column("dispute_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_orders_client_id", "orders", ["client_id"])
    op.create_index("ix_orders_service_type", "orders", ["service_type"])
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "agent_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("service_type", sa.String(100), nullable=False),
        sa.Column("language", sa.String(10), server_default="ru"),
        sa.Column("min_price", sa.Numeric(12, 2)),
        sa.Column("max_price", sa.Numeric(12, 2)),
        sa.Column("supports_files", sa.Boolean(), server_default="true"),
        sa.Column("supports_revisions", sa.Boolean(), server_default="true"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.UniqueConstraint("agent_id", "service_type", "language", name="uq_agent_service"),
    )

    op.create_table(
        "estimates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("deadline_hours", sa.Integer()),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("message", sa.Text()),
        sa.Column("questions", postgresql.JSONB()),
        sa.Column("decline_reason", sa.Text()),
        sa.Column("status", sa.Enum("pending", "submitted", "declined", "expired", "selected", name="estimate_status"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_foreign_key("fk_orders_selected_estimate", "orders", "estimates", ["selected_estimate_id"], ["id"])

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("type", sa.Enum("estimate_requested", "assigned", "revision_requested", "cancelled", "agent.test_requested", name="task_type"), nullable=False),
        sa.Column("status", sa.Enum("pending", "delivered", "completed", "declined", "expired", name="task_status"), nullable=False),
        sa.Column("payload_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("sender_type", sa.Enum("client", "agent", "developer", "admin", "system", name="sender_type"), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default="false"),
        sa.Column("moderation_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Enum("pending", "delivered", "failed", name="webhook_event_status"), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "moderation_violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("sender_type", sa.String(50), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("moderation_violations")
    op.drop_table("webhook_events")
    op.drop_table("files")
    op.drop_table("messages")
    op.drop_table("tasks")
    op.drop_constraint("fk_orders_selected_estimate", "orders", type_="foreignkey")
    op.drop_table("estimates")
    op.drop_table("agent_services")
    op.drop_table("orders")
    op.drop_table("agents")
    op.drop_table("audit_logs")
    op.drop_table("users")
    for name in ["user_role", "agent_status", "order_status", "estimate_status", "task_type", "task_status", "sender_type", "webhook_event_status"]:
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
