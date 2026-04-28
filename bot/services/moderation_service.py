"""Moderation service — text and image content moderation."""
from datetime import datetime, timedelta, timezone
from typing import Tuple

import structlog

from database.repositories.user_repository import UserRepository
from bot.services.ai_service import AIService

logger = structlog.get_logger(__name__)

_SUSPENSION_HOURS = 24


class ModerationService:
    def __init__(
        self,
        user_repo: UserRepository,
        ai_service: AIService,
    ) -> None:
        self.user_repo = user_repo
        self.ai_service = ai_service

    async def check_image(
        self, user_id: int, image_bytes: bytes
    ) -> Tuple[bool, str]:
        """Moderate image via AI. Returns (is_ok, reason)."""
        try:
            result = await self.ai_service.moderate_image(image_bytes)
            appropriate = result.get("appropriate", True)
            concerns = result.get("concerns", [])
            reason = ", ".join(concerns) if concerns else ""

            if appropriate:
                logger.info("image_moderation_passed", user_id=user_id)
                return True, ""
            else:
                logger.warning("image_moderation_failed", user_id=user_id, concerns=concerns)
                return False, reason or "Изображение не соответствует правилам сервиса"
        except Exception as e:
            logger.error("check_image_error", user_id=user_id, error=str(e))
            # Fail open — don't block on AI errors
            return True, ""

    async def check_text(
        self, user_id: int, text: str
    ) -> Tuple[bool, str]:
        """Moderate text via AI. Issues warning if needed, suspends after 3 warnings."""
        try:
            result = await self.ai_service.moderate_text(text)
            appropriate = result.get("appropriate", True)
            reason = result.get("reason") or ""

            if appropriate:
                return True, ""

            severity = result.get("severity", "low")
            warnings = await self._issue_warning(user_id)
            logger.warning(
                "text_moderation_failed",
                user_id=user_id,
                reason=reason,
                severity=severity,
                warnings=warnings,
            )

            if warnings >= 3:
                return False, f"Ваш аккаунт заблокирован за нарушение правил. Причина: {reason}"
            return False, f"Сообщение нарушает правила сервиса. Предупреждение {warnings}/3. Причина: {reason}"

        except Exception as e:
            logger.error("check_text_error", user_id=user_id, error=str(e))
            return True, ""

    async def _issue_warning(self, user_id: int) -> int:
        """Increment warnings counter. Suspend user if >= 3 warnings."""
        count = await self.user_repo.add_warning(user_id)
        if count >= 3:
            suspended_until = datetime.now(tz=timezone.utc) + timedelta(hours=_SUSPENSION_HOURS)
            await self.user_repo.suspend_user(user_id, suspended_until)
            logger.warning("user_suspended_after_warnings", user_id=user_id, warnings=count)
        return count
