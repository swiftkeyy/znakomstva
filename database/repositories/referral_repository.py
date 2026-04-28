from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.referral import Referral

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class ReferralRepository(BaseRepository[Referral]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Referral)

    async def create_referral(self, referrer_id: int, referred_id: int) -> Referral:
        referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(referral)
        await self.session.flush()
        await self.session.refresh(referral)
        logger.info("referral_created", referrer_id=referrer_id, referred_id=referred_id)
        return referral

    async def get_referral_by_referred(self, referred_id: int) -> Optional[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()

    async def count_referrals_this_month(self, referrer_id: int) -> int:
        now = datetime.now(tz=timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == referrer_id,
                Referral.created_at >= month_start,
            )
        )
        return result.scalar_one() or 0

    async def mark_premium_bonus_paid(self, referral_id: int) -> None:
        await self.session.execute(
            update(Referral)
            .where(Referral.id == referral_id)
            .values(premium_bonus_paid=True)
        )
        await self.session.flush()
        logger.debug("premium_bonus_marked_paid", referral_id=referral_id)
