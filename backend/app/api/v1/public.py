from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.content import BlogPost, PostStatus, SitePage
from app.schemas.content import BlogPostListItem, BlogPostResponse, SitePageResponse
from app.services.content_agent import ensure_home_page

router = APIRouter(tags=["public"])


@router.get("/pages/{slug}", response_model=SitePageResponse)
async def get_page(slug: str, db: AsyncSession = Depends(get_db)):
    if slug == "home":
        page = await ensure_home_page(db)
        return page
    result = await db.execute(select(SitePage).where(SitePage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


@router.get("/blog/posts", response_model=list[BlogPostListItem])
async def list_blog_posts(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlogPost)
        .where(BlogPost.status == PostStatus.published)
        .order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.get("/blog/posts/{slug}", response_model=BlogPostResponse)
async def get_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BlogPost).where(BlogPost.slug == slug, BlogPost.status == PostStatus.published)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post
