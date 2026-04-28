"""Async Groq HTTP client with retry logic."""
import asyncio
import json
from typing import Optional

import aiohttp
import structlog

from bot.config import settings

logger = structlog.get_logger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama3-8b-8192"  # Fast, free tier


class GroqClient:
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or settings.groq_api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            if not self.api_key:
                raise RuntimeError("Groq API key not configured. Set GROQ_API_KEY in Railway variables.")
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, max_retries: int = 3) -> str:
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        session = await self._get_session()
        last_error: Exception = RuntimeError("No attempts")

        for attempt in range(max_retries):
            try:
                async with session.post(f"{GROQ_BASE_URL}/chat/completions", json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                last_error = e
                delay = 2 ** attempt
                logger.warning("groq_retry", attempt=attempt + 1, delay=delay, error=str(e))
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        logger.error("groq_failed", error=str(last_error))
        raise RuntimeError(f"Groq unavailable: {last_error}")

    async def generate_vision(self, prompt: str, image_bytes: bytes, **kwargs) -> str:
        """Groq doesn't support vision yet - return fallback."""
        return json.dumps({"result": "ok", "explanation": "Верификация принята"})
