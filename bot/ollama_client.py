"""Async Ollama HTTP client with retry logic and exponential backoff."""
import asyncio
import base64
import json
import logging
from typing import Any, Optional

import aiohttp
import structlog

from bot.config import OLLAMA_MODEL_REASONING, OLLAMA_MODEL_TEXT, OLLAMA_MODEL_VISION, settings

logger = structlog.get_logger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = settings.ollama_url, timeout: int = settings.ollama_timeout) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        model: str = OLLAMA_MODEL_TEXT,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> str:
        """Generate text response from Ollama with retry logic."""
        payload = {"model": model, "prompt": prompt, "temperature": temperature, "stream": False}
        return await self._post_with_retry("/api/generate", payload, max_retries)

    async def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        model: str = OLLAMA_MODEL_VISION,
        max_retries: int = 3,
    ) -> str:
        """Generate response from vision model with image input."""
        image_b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }
        return await self._post_with_retry("/api/generate", payload, max_retries)

    async def generate_reasoning(
        self,
        prompt: str,
        model: str = OLLAMA_MODEL_REASONING,
        max_retries: int = 3,
    ) -> str:
        """Use deepseek-r1 for complex reasoning tasks."""
        return await self.generate(prompt, model=model, temperature=0.2, max_retries=max_retries)

    async def _post_with_retry(self, path: str, payload: dict, max_retries: int) -> str:
        session = await self._get_session()
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(max_retries):
            try:
                async with session.post(f"{self.base_url}{path}", json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    response_text = data.get("response", "")
                    logger.debug("ollama_response", model=payload.get("model"), attempt=attempt + 1)
                    return response_text
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                delay = 2 ** attempt
                logger.warning("ollama_retry", attempt=attempt + 1, delay=delay, error=str(e))
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        logger.error("ollama_failed", error=str(last_error))
        raise RuntimeError(f"Ollama unavailable after {max_retries} attempts: {last_error}")

    async def is_healthy(self) -> bool:
        """Check if Ollama service is available."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
        except Exception:
            return False


# Singleton instance
ollama_client = OllamaClient()
