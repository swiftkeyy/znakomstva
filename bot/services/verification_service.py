"""Verification service — levels 1-3 photo/video verification."""
from datetime import datetime, timedelta, timezone
from typing import Tuple

import structlog

from database.repositories.verification_repository import VerificationRepository
from bot.services.ai_service import AIService

logger = structlog.get_logger(__name__)

_RETRY_HOURS = 24


class VerificationService:
    def __init__(
        self,
        verification_repo: VerificationRepository,
        ai_service: AIService,
    ) -> None:
        self.verification_repo = verification_repo
        self.ai_service = ai_service

    async def verify_level_1(
        self, user_id: int, image_bytes: bytes
    ) -> Tuple[bool, str]:
        """Circle gesture check via AI."""
        attempt = await self.verification_repo.create_attempt(
            user_id=user_id, level=1, file_id=""
        )
        try:
            result = await self.ai_service.verify_circle_gesture(image_bytes)
            passed = (
                result.get("has_person", False)
                and result.get("has_circle_gesture", False)
                and result.get("face_visible", False)
            )
            status = "approved" if passed else "rejected"
            reason = None if passed else "Жест круга не обнаружен или лицо не видно"
            await self.verification_repo.update_attempt(
                attempt.id, status=status, reason=reason
            )
            if passed:
                await self.verification_repo.mark_verified(user_id, level=1)
                logger.info("verification_level1_passed", user_id=user_id)
                return True, "Верификация уровня 1 пройдена"
            logger.info("verification_level1_failed", user_id=user_id)
            return False, reason or "Верификация не пройдена"
        except Exception as e:
            logger.error("verify_level_1_error", user_id=user_id, error=str(e))
            await self.verification_repo.update_attempt(
                attempt.id, status="rejected", reason="Ошибка обработки"
            )
            return False, "Ошибка при проверке. Попробуйте позже."

    async def verify_level_2(
        self, user_id: int, video_bytes: bytes
    ) -> Tuple[bool, str]:
        """Basic video check — file size and duration validation."""
        attempt = await self.verification_repo.create_attempt(
            user_id=user_id, level=2, file_id=""
        )
        try:
            max_size_mb = 50
            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > max_size_mb:
                reason = f"Видео слишком большое ({size_mb:.1f} МБ). Максимум {max_size_mb} МБ."
                await self.verification_repo.update_attempt(
                    attempt.id, status="rejected", reason=reason
                )
                return False, reason

            # Minimum size check — at least 10 KB to be a real video
            if len(video_bytes) < 10 * 1024:
                reason = "Видео слишком короткое или повреждено."
                await self.verification_repo.update_attempt(
                    attempt.id, status="rejected", reason=reason
                )
                return False, reason

            await self.verification_repo.update_attempt(attempt.id, status="approved")
            await self.verification_repo.mark_verified(user_id, level=2)
            logger.info("verification_level2_passed", user_id=user_id)
            return True, "Верификация уровня 2 пройдена"
        except Exception as e:
            logger.error("verify_level_2_error", user_id=user_id, error=str(e))
            await self.verification_repo.update_attempt(
                attempt.id, status="rejected", reason="Ошибка обработки"
            )
            return False, "Ошибка при проверке. Попробуйте позже."

    async def verify_level_3(
        self,
        user_id: int,
        verification_image_bytes: bytes,
        profile_image_bytes: bytes,
    ) -> Tuple[bool, str]:
        """Face matching via AI — confidence >= 85%."""
        attempt = await self.verification_repo.create_attempt(
            user_id=user_id, level=3, file_id=""
        )
        try:
            result = await self.ai_service.verify_face_match(
                profile_image=profile_image_bytes,
                verification_image=verification_image_bytes,
            )
            confidence = float(result.get("confidence", 0))
            passed = result.get("match", False) and confidence >= 85.0
            status = "approved" if passed else "rejected"
            reason = result.get("reasoning") if not passed else None
            if not passed and not reason:
                reason = f"Совпадение лиц: {confidence:.0f}% (требуется 85%)"

            await self.verification_repo.update_attempt(
                attempt.id,
                status=status,
                confidence_score=confidence,
                reason=reason,
            )
            if passed:
                await self.verification_repo.mark_verified(user_id, level=3)
                logger.info("verification_level3_passed", user_id=user_id, confidence=confidence)
                return True, "Верификация уровня 3 пройдена"
            logger.info("verification_level3_failed", user_id=user_id, confidence=confidence)
            return False, reason or "Верификация не пройдена"
        except Exception as e:
            logger.error("verify_level_3_error", user_id=user_id, error=str(e))
            await self.verification_repo.update_attempt(
                attempt.id, status="rejected", reason="Ошибка обработки"
            )
            return False, "Ошибка при проверке. Попробуйте позже."

    async def can_retry(self, user_id: int, level: int) -> bool:
        """Return True if 24h have passed since the last failed attempt."""
        try:
            latest = await self.verification_repo.get_latest_attempt(user_id, level)
            if latest is None:
                return True
            if latest.status == "approved":
                return False  # Already verified at this level
            cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=_RETRY_HOURS)
            attempted_at = latest.attempted_at
            if attempted_at.tzinfo is None:
                attempted_at = attempted_at.replace(tzinfo=timezone.utc)
            return attempted_at < cutoff
        except Exception as e:
            logger.error("can_retry_error", user_id=user_id, level=level, error=str(e))
            return False
