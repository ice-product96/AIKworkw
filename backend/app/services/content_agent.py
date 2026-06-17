import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import BlogPost, PostStatus, SitePage
from app.services.llm import LLMError, chat_json

DEFAULT_LANDING = {
    "hero_title": "AIKworkw — маркетплейс AI-агентов для бизнеса",
    "hero_subtitle": "Размещайте заказы и получайте оценки от специализированных AI-агентов за минуты. Лендинги, SEO, скрипты, боты и многое другое.",
    "hero_cta": "Начать бесплатно",
    "features": [
        {"title": "Быстрые оценки", "text": "Несколько AI-агентов откликаются на заказ и предлагают цену и сроки."},
        {"title": "Прозрачный процесс", "text": "Чат, статусы заказа и контроль качества на одной платформе."},
        {"title": "Специализация", "text": "Агенты заточены под конкретные задачи: от копирайтинга до Python-скриптов."},
    ],
    "stats": [
        {"label": "Типов услуг", "value": "8+"},
        {"label": "AI-агентов", "value": "50+"},
        {"label": "Среднее время оценки", "value": "< 1 час"},
    ],
    "seo_block": "AIKworkw объединяет заказчиков и разработчиков AI-агентов. Платформа подходит для малого бизнеса, маркетологов и продуктовых команд, которым нужны быстрые и предсказуемые AI-услуги.",
}


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:80] or f"post-{uuid.uuid4().hex[:8]}"


async def ensure_home_page(db: AsyncSession) -> SitePage:
    result = await db.execute(select(SitePage).where(SitePage.slug == "home"))
    page = result.scalar_one_or_none()
    if page:
        return page
    page = SitePage(
        slug="home",
        title="AIKworkw — маркетплейс AI-агентов",
        content_json=DEFAULT_LANDING,
        meta_title="AIKworkw — заказы AI-агентам для бизнеса",
        meta_description="Размещайте задачи AI-агентам: лендинги, SEO, боты, скрипты. Быстрые оценки и прозрачный процесс.",
    )
    db.add(page)
    await db.flush()
    return page


async def generate_landing_content(db: AsyncSession, topic: str = "маркетплейс AI-агентов") -> SitePage:
    page = await ensure_home_page(db)
    try:
        data = await chat_json(
            db,
            system=(
                "Ты SEO-копирайтер. Сгенерируй контент главной страницы маркетплейса AI-агентов AIKworkw на русском. "
                "JSON формат как в примере."
            ),
            user=f"""Тема: {topic}

Верни JSON:
{{
  "hero_title": "...",
  "hero_subtitle": "...",
  "hero_cta": "...",
  "features": [{{"title": "...", "text": "..."}}],
  "stats": [{{"label": "...", "value": "..."}}],
  "seo_block": "абзац 3-4 предложения для SEO",
  "meta_title": "...",
  "meta_description": "..."
}}""",
        )
        page.content_json = {
            "hero_title": data.get("hero_title", DEFAULT_LANDING["hero_title"]),
            "hero_subtitle": data.get("hero_subtitle", DEFAULT_LANDING["hero_subtitle"]),
            "hero_cta": data.get("hero_cta", DEFAULT_LANDING["hero_cta"]),
            "features": data.get("features", DEFAULT_LANDING["features"]),
            "stats": data.get("stats", DEFAULT_LANDING["stats"]),
            "seo_block": data.get("seo_block", DEFAULT_LANDING["seo_block"]),
        }
        page.meta_title = data.get("meta_title", page.meta_title)
        page.meta_description = data.get("meta_description", page.meta_description)
        page.title = data.get("hero_title", page.title)[:300]
    except LLMError:
        page.content_json = DEFAULT_LANDING
    await db.flush()
    return page


async def generate_blog_post(
    db: AsyncSession,
    *,
    topic: str,
    author_id: uuid.UUID | None = None,
    publish: bool = False,
) -> BlogPost:
    try:
        data = await chat_json(
            db,
            system=(
                "Ты SEO-копирайтер для блога маркетплейса AI-агентов AIKworkw. "
                "Пиши полезные статьи на русском в Markdown. JSON только."
            ),
            user=f"""Напиши SEO-статью на тему: {topic}

JSON:
{{
  "title": "...",
  "slug": "latin-slug",
  "excerpt": "2 предложения",
  "content": "markdown 800-1200 слов с заголовками ##",
  "meta_title": "...",
  "meta_description": "..."
}}""",
        )
    except LLMError:
        slug = _slugify(topic)
        data = {
            "title": topic,
            "slug": slug,
            "excerpt": f"Статья о {topic} на платформе AIKworkw.",
            "content": f"# {topic}\n\nAI-агенты помогают бизнесу автоматизировать задачи. На AIKworkw вы найдёте специализированных агентов для разных услуг.",
            "meta_title": topic,
            "meta_description": f"{topic} — AIKworkw блог",
        }

    slug = _slugify(data.get("slug") or data.get("title", topic))
    existing = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    post = BlogPost(
        slug=slug,
        title=data.get("title", topic)[:300],
        excerpt=data.get("excerpt"),
        content=data.get("content", ""),
        meta_title=data.get("meta_title"),
        meta_description=data.get("meta_description"),
        status=PostStatus.published if publish else PostStatus.draft,
        author_id=author_id,
        is_ai_generated=True,
        published_at=datetime.now(UTC) if publish else None,
    )
    db.add(post)
    await db.flush()
    return post


async def generate_blog_batch(
    db: AsyncSession,
    *,
    topics: list[str],
    author_id: uuid.UUID | None = None,
    publish: bool = True,
) -> list[BlogPost]:
    posts: list[BlogPost] = []
    for topic in topics[:10]:
        posts.append(await generate_blog_post(db, topic=topic, author_id=author_id, publish=publish))
    return posts
