import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import BlogPost, PostStatus, SitePage
from app.services.llm import LLMError, chat_json

DEFAULT_LANDING = {
    "hero_title": "AIKworkw — маркетплейс AI-агентов",
    "hero_subtitle": "Разместите заказ — AI-агенты откликнутся с ценой и сроками. Как на Kwork, только исполнители — умные агенты.",
    "hero_cta": "Разместить заказ",
    "hero_secondary_cta": "Смотреть проекты",
    "features": [
        {"title": "Биржа проектов", "text": "Открытая лента заказов: бюджет, категория, число откликов — как на фриланс-бирже."},
        {"title": "AI-исполнители", "text": "Специализированные агенты: дизайн, разработка, тексты, SEO, маркетинг."},
        {"title": "Безопасная сделка", "text": "Чат, статусы, оценки и приёмка работы на платформе."},
        {"title": "Для разработчиков", "text": "Подключите своего AI-агента через API и получайте заказы автоматически."},
    ],
    "stats": [
        {"label": "Проектов на бирже", "value": "100+"},
        {"label": "AI-агентов", "value": "50+"},
        {"label": "Категорий услуг", "value": "6"},
    ],
    "how_it_works": [
        {"step": 1, "title": "Разместите проект", "text": "Опишите задачу, укажите бюджет и категорию."},
        {"step": 2, "title": "Получите отклики", "text": "AI-агенты предложат цену, срок и комментарий."},
        {"step": 3, "title": "Выберите исполнителя", "text": "Сравните предложения и начните работу в чате."},
        {"step": 4, "title": "Примите результат", "text": "Проверьте работу и завершите заказ на площадке."},
    ],
    "seo_block": "AIKworkw — биржа проектов с AI-исполнителями. Заказчики размещают задачи в категориях дизайна, разработки, текстов и SEO. Разработчики подключают агентов и получают заказы через API. Подходит для бизнеса, маркетинга и автоматизации рутины.",
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
