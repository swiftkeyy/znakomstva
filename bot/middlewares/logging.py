"""Logging middleware — structlog JSON logging for all requests."""
import time
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("user")
        user_id = user.id if user else None
        event_type = type(event).__name__
        start = time.monotonic()

        logger.info("request_started", user_id=user_id, event_type=event_type)

        try:
            result = await handler(event, data)
            duration = round(time.monotonic() - start, 3)
            logger.info("request_completed", user_id=user_id, event_type=event_type, duration=duration)
            return result
        except Exception as e:
            duration = round(time.monotonic() - start, 3)
            logger.error(
                "request_failed",
                user_id=user_id,
                event_type=event_type,
                duration=duration,
                error=str(e),
                exc_info=True,
            )
            raise
