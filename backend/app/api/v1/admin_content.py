from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import User, UserRole
from app.models.content import BlogPost, PostStatus, SitePage
from app.schemas.content import (
    BlogPostCreate,
    BlogPostListItem,
    BlogPostResponse,
    BlogPostUpdate,
    SitePageResponse,
    SitePageUpdate,
)
from app.services.audit import log_action
from app.services.content_agent import ensure_home_page

router = APIRouter(prefix="/admin/content", tags=["admin-content"])


@router.get("/pages/{slug}", response_model=SitePageResponse)
async def get_page(
    slug: str,
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    if slug == "home":
        return await ensure_home_page(db)
    result = await db.execute(select(SitePage).where(SitePage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


@router.patch("/pages/{slug}", response_model=SitePageResponse)
async def update_page(
    slug: str,
    data: SitePageUpdate,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    if slug == "home":
        page = await ensure_home_page(db)
    else:
        result = await db.execute(select(SitePage).where(SitePage.slug == slug))
        page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    if data.title is not None:
        page.title = data.title
    if data.content_json is not None:
        page.content_json = data.content_json
    if data.meta_title is not None:
        page.meta_title = data.meta_title
    if data.meta_description is not None:
        page.meta_description = data.meta_description
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="content.page.updated", resource_id=slug)
    return page


@router.get("/posts", response_model=list[BlogPostListItem])
async def list_posts(
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).order_by(BlogPost.created_at.desc()))
    return list(result.scalars().all())


@router.post("/posts", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: BlogPostCreate,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(BlogPost).where(BlogPost.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
    post = BlogPost(
        slug=data.slug,
        title=data.title,
        excerpt=data.excerpt,
        content=data.content,
        meta_title=data.meta_title,
        meta_description=data.meta_description,
        status=PostStatus(data.status),
        author_id=admin.id,
        published_at=datetime.now(UTC) if data.status == "published" else None,
    )
    db.add(post)
    await db.flush()
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="content.post.created", resource_id=str(post.id))
    return post


@router.get("/posts/{post_id}", response_model=BlogPostResponse)
async def get_post(
    post_id: UUID,
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.patch("/posts/{post_id}", response_model=BlogPostResponse)
async def update_post(
    post_id: UUID,
    data: BlogPostUpdate,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if data.slug is not None and data.slug != post.slug:
        dup = await db.execute(select(BlogPost).where(BlogPost.slug == data.slug))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
        post.slug = data.slug
    if data.title is not None:
        post.title = data.title
    if data.excerpt is not None:
        post.excerpt = data.excerpt
    if data.content is not None:
        post.content = data.content
    if data.meta_title is not None:
        post.meta_title = data.meta_title
    if data.meta_description is not None:
        post.meta_description = data.meta_description
    if data.status is not None:
        new_status = PostStatus(data.status)
        if new_status == PostStatus.published and post.status != PostStatus.published:
            post.published_at = datetime.now(UTC)
        post.status = new_status
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="content.post.updated", resource_id=str(post_id))
    return post


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: UUID,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    await db.delete(post)
    await log_action(db, actor_type="admin", actor_id=str(admin.id), action="content.post.deleted", resource_id=str(post_id))
    return {"status": "deleted"}
