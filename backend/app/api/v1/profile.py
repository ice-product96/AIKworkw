from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.audit import log_action
from app.services.profile import build_profile_response
from app.services.storage import content_type_for_path, get_file, upload_file

router = APIRouter(prefix="/profile", tags=["profile"])

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await build_profile_response(db, user)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await log_action(db, actor_type="user", actor_id=str(user.id), action="profile.updated")
    return await build_profile_response(db, user)


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый формат изображения")
    data = await file.read()
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл слишком большой (макс. 2 МБ)")
    ext = content_type.split("/")[-1].replace("jpeg", "jpg")
    path = f"avatars/{user.id}.{ext}"
    upload_file(path, data, content_type)
    user.avatar_path = path
    user.updated_at = datetime.now(timezone.utc)
    await log_action(db, actor_type="user", actor_id=str(user.id), action="profile.avatar_updated")
    return await build_profile_response(db, user)


@router.get("/avatars/{user_id}")
async def get_avatar(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.avatar_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аватар не найден")
    try:
        data = get_file(user.avatar_path)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аватар не найден") from exc
    return Response(
        content=data,
        media_type=content_type_for_path(user.avatar_path),
        headers={"Cache-Control": "public, max-age=3600"},
    )
