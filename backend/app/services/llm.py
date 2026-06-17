import json
import re
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.platform_settings import get_deepseek_config


class LLMError(Exception):
    pass


async def chat_completion(
    db: AsyncSession,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str:
    cfg = await get_deepseek_config(db)
    if not cfg["api_key"]:
        raise LLMError("DeepSeek API key not configured")

    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = f"{cfg['base_url']}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            raise LLMError(f"DeepSeek API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def test_connection(db: AsyncSession) -> str:
    text = await chat_completion(
        db,
        [{"role": "user", "content": "Ответь одним словом: OK"}],
        temperature=0,
    )
    return text.strip()


async def chat_json(db: AsyncSession, system: str, user: str) -> dict[str, Any]:
    content = await chat_completion(
        db,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        json_mode=True,
    )
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Invalid JSON from LLM: {e}") from e
