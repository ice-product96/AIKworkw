from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TaskFileInfo(BaseModel):
    file_id: UUID
    filename: str
    url: str


class PollTaskResponse(BaseModel):
    task_id: UUID
    order_id: UUID | None
    type: str
    service_type: str | None = None
    title: str | None = None
    description: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    files: list[TaskFileInfo] = []


class PollResponse(BaseModel):
    tasks: list[PollTaskResponse]


class EstimateSubmit(BaseModel):
    price: Decimal = Field(gt=0)
    deadline_hours: int = Field(gt=0, le=720)
    confidence: Decimal = Field(ge=0, le=1)
    message: str = Field(min_length=1)
    questions: list[str] = []


class DeclineRequest(BaseModel):
    reason: str = Field(min_length=3)


class StatusUpdate(BaseModel):
    status: str
    progress: int = Field(ge=0, le=100)
    message: str | None = None


class AgentMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class ResultSubmit(BaseModel):
    text: str = Field(min_length=1)
    files: list[UUID] = []
    result_url: str | None = None
