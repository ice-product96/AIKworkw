import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.content import PlatformSetting

SETTING_DEEPSEEK_API_KEY = "deepseek_api_key"
SETTING_DEEPSEEK_BASE_URL = "deepseek_base_url"
SETTING_DEEPSEEK_MODEL = "deepseek_model"


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
    else:
        db.add(PlatformSetting(key=key, value=value))


async def get_deepseek_config(db: AsyncSession) -> dict[str, str]:
    settings = get_settings()
    api_key = await get_setting(db, SETTING_DEEPSEEK_API_KEY, settings.deepseek_api_key)
    base_url = await get_setting(db, SETTING_DEEPSEEK_BASE_URL, settings.deepseek_base_url)
    model = await get_setting(db, SETTING_DEEPSEEK_MODEL, settings.deepseek_model)
    return {"api_key": api_key, "base_url": base_url.rstrip("/"), "model": model}


async def get_ai_settings_public(db: AsyncSession) -> dict[str, Any]:
    cfg = await get_deepseek_config(db)
    return {
        "configured": bool(cfg["api_key"]),
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "has_api_key": bool(cfg["api_key"]),
    }


def mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"
