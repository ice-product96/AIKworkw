from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.models.domain import Estimate, File as OrderFile, Message, Order, OrderStatus, SenderType
from app.schemas.order import (
    DisputeRequest,
    EstimateResponse,
    FileResponse,
    MessageCreate,
    MessageResponse,
    OrderCreate,
    OrderResponse,
    RevisionRequest,
)
from app.services.audit import log_action
from app.services.matching import publish_order
from app.services.order_service import (
    accept_order,
    create_message,
    get_order_for_client,
    mock_pay_order,
    open_dispute,
    request_revision,
    select_estimate,
    update_order_estimated_status,
)
from app.services.storage import generate_presigned_url, upload_file

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = Order(
        client_id=user.id,
        title=data.title,
        description=data.description,
        service_type=data.service_type,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        deadline=data.deadline,
        status=OrderStatus.draft,
    )
    db.add(order)
    await db.flush()
    await log_action(db, actor_type="client", actor_id=str(user.id), action="order.created", resource_type="order", resource_id=str(order.id))
    return order


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = Query(None, alias="status"),
    service_type: str | None = None,
    q: str | None = None,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order).where(Order.client_id == user.id)
    if status_filter:
        query = query.where(Order.status == OrderStatus(status_filter))
    if service_type:
        query = query.where(Order.service_type == service_type)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Order.title.ilike(pattern), Order.description.ilike(pattern)))
    query = query.order_by(Order.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    return await get_order_for_client(db, order_id, user)


@router.post("/{order_id}/publish", response_model=OrderResponse)
async def publish_order_endpoint(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    try:
        await publish_order(db, order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.refresh(order)
    return order


@router.get("/{order_id}/estimates", response_model=list[EstimateResponse])
async def list_estimates(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    await get_order_for_client(db, order_id, user)
    result = await db.execute(select(Estimate).where(Estimate.order_id == order_id))
    return list(result.scalars().all())


@router.post("/{order_id}/estimates/{estimate_id}/select", response_model=OrderResponse)
async def select_estimate_endpoint(
    order_id: UUID,
    estimate_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    return await select_estimate(db, order, estimate_id)


@router.post("/{order_id}/pay", response_model=OrderResponse)
async def pay_order(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    return await mock_pay_order(db, order)


@router.post("/{order_id}/messages", response_model=MessageResponse)
async def post_message(
    order_id: UUID,
    data: MessageCreate,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    msg = await create_message(db, order, SenderType.client, str(user.id), data.text)
    response = MessageResponse.model_validate(msg)
    if msg.is_blocked:
        response.warning = "Сообщение заблокировано: обмен контактами вне платформы запрещён."
    return response


@router.get("/{order_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    order_id: UUID,
    since: datetime | None = None,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    await get_order_for_client(db, order_id, user)
    query = select(Message).where(Message.order_id == order_id, Message.is_blocked.is_(False))
    if since:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        query = query.where(Message.created_at > since)
    query = query.order_by(Message.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{order_id}/files", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_order_file(
    order_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    content = await file.read()
    storage_path = f"orders/{order_id}/{file.filename}"
    upload_file(storage_path, content, file.content_type or "application/octet-stream")
    record = OrderFile(
        order_id=order.id,
        uploaded_by=user.id,
        filename=file.filename or "file",
        storage_path=storage_path,
        mime_type=file.content_type or "application/octet-stream",
        size=len(content),
    )
    db.add(record)
    await db.flush()
    return record


@router.get("/{order_id}/files", response_model=list[FileResponse])
async def list_files(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    await get_order_for_client(db, order_id, user)
    result = await db.execute(select(OrderFile).where(OrderFile.order_id == order_id))
    return list(result.scalars().all())


@router.post("/{order_id}/accept", response_model=OrderResponse)
async def accept_order_endpoint(
    order_id: UUID,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    return await accept_order(db, order)


@router.post("/{order_id}/revision", response_model=OrderResponse)
async def revision_endpoint(
    order_id: UUID,
    data: RevisionRequest,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    return await request_revision(db, order, data.message)


@router.post("/{order_id}/dispute", response_model=OrderResponse)
async def dispute_endpoint(
    order_id: UUID,
    data: DisputeRequest,
    user: User = Depends(require_roles(UserRole.client)),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_for_client(db, order_id, user)
    return await open_dispute(db, order, data.reason)
