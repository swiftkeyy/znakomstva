"""Auth middleware — auto-create user on first request."""
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        session = data.get("session")

        if tg_user and session:
            from database.repositories.user_repository import UserRepository
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(tg_user.id)

            if not user:
                user = await user_repo.create(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name or "Пользователь",
                )
                logger.info("new_user_created", telegram_id=tg_user.id)
            else:
                await user_repo.update_last_active(user.id)

            data["user"] = user

        return await handler(event, data)
