from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import User, UserRole
from app.schemas.content import (
    AiSettingsResponse,
    AiSettingsUpdate,
    BlogPostResponse,
    GenerateActivityRequest,
    GenerateActivityResponse,
    GenerateBlogBatchRequest,
    GenerateBlogRequest,
    GenerateLandingRequest,
)
from app.services.audit import log_action
from app.services.content_agent import generate_blog_batch, generate_blog_post, generate_landing_content
from app.services.llm import LLMError, test_connection
from app.services.platform_settings import (
    SETTING_DEEPSEEK_API_KEY,
    SETTING_DEEPSEEK_BASE_URL,
    SETTING_DEEPSEEK_MODEL,
    get_ai_settings_public,
    get_deepseek_config,
    mask_api_key,
    set_setting,
)
from app.services.seed_generator import generate_platform_activity

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])


@router.get("/settings", response_model=AiSettingsResponse)
async def get_settings(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    info = await get_ai_settings_public(db)
    cfg = await get_deepseek_config(db)
    return AiSettingsResponse(
        **info,
        api_key_masked=mask_api_key(cfg["api_key"]),
    )


@router.patch("/settings", response_model=AiSettingsResponse)
async def update_settings(
    data: AiSettingsUpdate,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    if data.api_key is not None:
        await set_setting(db, SETTING_DEEPSEEK_API_KEY, data.api_key)
    if data.base_url is not None:
        await set_setting(db, SETTING_DEEPSEEK_BASE_URL, data.base_url)
    if data.model is not None:
        await set_setting(db, SETTING_DEEPSEEK_MODEL, data.model)
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="ai.settings.updated")
    cfg = await get_deepseek_config(db)
    info = await get_ai_settings_public(db)
    return AiSettingsResponse(**info, api_key_masked=mask_api_key(cfg["api_key"]))


@router.post("/test")
async def test_ai(
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    try:
        reply = await test_connection(db)
        await log_action(db, actor_type="admin", actor_id=str(admin.id), action="ai.test.success")
        return {"status": "ok", "reply": reply}
    except LLMError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/generate-activity", response_model=GenerateActivityResponse)
async def generate_activity(
    data: GenerateActivityRequest,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await generate_platform_activity(
        db,
        admin_id=admin.id,
        num_clients=data.num_clients,
        num_developers=data.num_developers,
        num_agents=data.num_agents,
        num_orders=data.num_orders,
        complete_ratio=data.complete_ratio,
    )
    return GenerateActivityResponse(**result)


@router.post("/generate-landing")
async def ai_generate_landing(
    data: GenerateLandingRequest,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    page = await generate_landing_content(db, topic=data.topic)
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="ai.landing.generated")
    return {"slug": page.slug, "title": page.title}


@router.post("/generate-blog", response_model=BlogPostResponse)
async def ai_generate_blog(
    data: GenerateBlogRequest,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    post = await generate_blog_post(db, topic=data.topic, author_id=admin.id, publish=data.publish)
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="ai.blog.generated", resource_id=str(post.id))
    return post


@router.post("/generate-blog-batch", response_model=list[BlogPostResponse])
async def ai_generate_blog_batch(
    data: GenerateBlogBatchRequest,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    posts = await generate_blog_batch(
        db, topics=data.topics, author_id=admin.id, publish=data.publish
    )
    await log_action(
        db,
        actor_type="admin",
        actor_id=str(admin.id),
        action="ai.blog.batch_generated",
        details={"count": len(posts)},
    )
    return posts
