from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.content import BlogPost, PostStatus, SitePage
from app.models.domain import Estimate, EstimateStatus, Order, OrderStatus
from app.schemas.content import BlogPostListItem, BlogPostResponse, SitePageResponse
from app.schemas.marketplace import (
    MarketplaceStatsResponse,
    PublicProjectDetail,
    PublicProjectListResponse,
    PublicProjectItem,
)
from app.services.content_agent import ensure_home_page
from app.services.marketplace import get_marketplace_stats, list_public_projects
from app.services.profile import build_client_public_map

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


@router.get("/marketplace/stats", response_model=MarketplaceStatsResponse)
async def marketplace_stats(db: AsyncSession = Depends(get_db)):
    return await get_marketplace_stats(db)


@router.get("/projects", response_model=PublicProjectListResponse)
async def public_projects(
    category: str | None = None,
    service_type: str | None = None,
    q: str | None = None,
    sort: str = Query("created_at_desc", pattern="^(created_at_desc|created_at_asc|updated_at_desc|budget_desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await list_public_projects(
        db,
        category=category,
        service_type=service_type,
        q=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return PublicProjectListResponse(
        items=[PublicProjectItem(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{order_id}", response_model=PublicProjectDetail)
async def public_project_detail(order_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status in (OrderStatus.draft, OrderStatus.cancelled, OrderStatus.failed):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    proposals = (
        await db.execute(
            select(func.count())
            .select_from(Estimate)
            .where(
                Estimate.order_id == order.id,
                Estimate.status.in_([EstimateStatus.submitted, EstimateStatus.selected]),
            )
        )
    ).scalar_one()
    client_map = await build_client_public_map(db, [order.client_id])
    return PublicProjectDetail(
        id=order.id,
        title=order.title,
        description=order.description,
        service_type=order.service_type,
        budget_min=order.budget_min,
        budget_max=order.budget_max,
        status=order.status.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
        proposals_count=proposals,
        client=client_map.get(order.client_id),
    )
