"""Async OpenRouter HTTP client with retry logic and exponential backoff."""
import asyncio
import base64
import json
from typing import Any, Optional

import aiohttp
import structlog

from bot.config import settings

logger = structlog.get_logger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API - free tier with various models."""
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": settings.bot_username or "https://ultradating.bot",
                "X-Title": "UltraDating Bot",
            }
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=headers,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        model: str = "meta-llama/llama-3.2-3b-instruct:free",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        max_retries: int = 3,
    ) -> str:
        """Generate text response from OpenRouter with retry logic."""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        return await self._post_with_retry("/chat/completions", payload, max_retries)

    async def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        model: str = "meta-llama/llama-3.2-11b-vision-instruct:free",
        max_retries: int = 3,
    ) -> str:
        """Generate response from vision model with image input."""
        image_b64 = base64.b64encode(image_bytes).decode()
        image_url = f"data:image/jpeg;base64,{image_b64}"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "max_tokens": 500,
        }
        return await self._post_with_retry("/chat/completions", payload, max_retries)

    async def generate_reasoning(
        self,
        prompt: str,
        model: str = "meta-llama/llama-3.2-3b-instruct:free",
        max_retries: int = 3,
    ) -> str:
        """Use reasoning model for complex tasks."""
        return await self.generate(
            prompt, model=model, temperature=0.2, max_tokens=1500, max_retries=max_retries
        )

    async def _post_with_retry(self, path: str, payload: dict, max_retries: int) -> str:
        session = await self._get_session()
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(max_retries):
            try:
                async with session.post(f"{self.base_url}{path}", json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0]["message"]["content"]
                        logger.debug("openrouter_response", model=payload.get("model"), attempt=attempt + 1)
                        return response_text
                    else:
                        raise ValueError("Invalid response format from OpenRouter")
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
                last_error = e
                delay = 2 ** attempt
                logger.warning("openrouter_retry", attempt=attempt + 1, delay=delay, error=str(e))
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        logger.error("openrouter_failed", error=str(last_error))
        raise RuntimeError(f"OpenRouter unavailable after {max_retries} attempts: {last_error}")

    async def is_healthy(self) -> bool:
        """Check if OpenRouter service is available."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False


# Singleton instance
openrouter_client = OpenRouterClient()
