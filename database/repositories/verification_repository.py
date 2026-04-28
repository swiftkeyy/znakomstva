from typing import Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.verification import VerificationAttempt

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class VerificationRepository(BaseRepository[VerificationAttempt]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VerificationAttempt)

    async def create_attempt(
        self, user_id: int, level: int, file_id: str
    ) -> VerificationAttempt:
        attempt = VerificationAttempt(user_id=user_id, level=level, file_id=file_id)
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)
        logger.info("verification_attempt_created", user_id=user_id, level=level)
        return attempt

    async def get_latest_attempt(
        self, user_id: int, level: int
    ) -> Optional[VerificationAttempt]:
        result = await self.session.execute(
            select(VerificationAttempt)
            .where(
                VerificationAttempt.user_id == user_id,
                VerificationAttempt.level == level,
            )
            .order_by(VerificationAttempt.attempted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_verified(self, user_id: int, level: int) -> None:
        from database.models.profile import Profile

        # Approve the latest attempt
        await self.session.execute(
            update(VerificationAttempt)
            .where(
                VerificationAttempt.user_id == user_id,
                VerificationAttempt.level == level,
            )
            .values(status="approved")
        )
        # Bump verification_level on profile if needed
        await self.session.execute(
            update(Profile)
            .where(Profile.user_id == user_id, Profile.verification_level < level)
            .values(verification_level=level)
        )
        await self.session.flush()
        logger.info("user_verified", user_id=user_id, level=level)

    async def update_attempt(
        self,
        attempt_id: int,
        status: str,
        confidence_score: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> None:
        values: dict = {"status": status}
        if confidence_score is not None:
            values["confidence_score"] = confidence_score
        if reason is not None:
            values["reason"] = reason
        await self.session.execute(
            update(VerificationAttempt)
            .where(VerificationAttempt.id == attempt_id)
            .values(**values)
        )
        await self.session.flush()
        logger.debug("verification_attempt_updated", attempt_id=attempt_id, status=status)
