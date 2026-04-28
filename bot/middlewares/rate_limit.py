"""Rate limit middleware — global per-user request throttling."""
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter) -> None:
        self.rate_limiter = rate_limiter

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("user")

        if user:
            allowed, ttl = await self.rate_limiter.check_global_limit(user.id)
            if not allowed:
                logger.warning("rate_limit_exceeded", user_id=user.id, ttl=ttl)
                if isinstance(event, Message):
                    await event.answer(f"⏱ Слишком много запросов. Подождите {ttl} сек.")
                return

        return await handler(event, data)
