"""Referral service — referral tracking and crystal rewards."""
from typing import Any, Dict

import structlog

from database.repositories.referral_repository import ReferralRepository
from database.repositories.user_repository import UserRepository
from bot.config import settings

logger = structlog.get_logger(__name__)


class ReferralService:
    def __init__(
        self,
        referral_repo: ReferralRepository,
        user_repo: UserRepository,
    ) -> None:
        self.referral_repo = referral_repo
        self.user_repo = user_repo

    async def process_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Create referral record and reward referrer with 100 crystals."""
        try:
            existing = await self.referral_repo.get_referral_by_referred(referred_id)
            if existing is not None:
                logger.info("referral_already_exists", referred_id=referred_id)
                return False

            await self.referral_repo.create_referral(referrer_id, referred_id)
            await self.user_repo.add_crystals(
                referrer_id, settings.referral_crystals_registration
            )
            logger.info(
                "referral_processed",
                referrer_id=referrer_id,
                referred_id=referred_id,
                crystals=settings.referral_crystals_registration,
            )
            return True
        except Exception as e:
            logger.error(
                "process_referral_error",
                referrer_id=referrer_id,
                referred_id=referred_id,
                error=str(e),
            )
            return False

    async def process_premium_bonus(self, referred_id: int) -> None:
        """Add 500 crystals to referrer when referred user buys premium."""
        try:
            referral = await self.referral_repo.get_referral_by_referred(referred_id)
            if referral is None:
                return
            if referral.premium_bonus_paid:
                logger.debug("premium_bonus_already_paid", referred_id=referred_id)
                return

            await self.user_repo.add_crystals(
                referral.referrer_id, settings.referral_crystals_premium
            )
            await self.referral_repo.mark_premium_bonus_paid(referral.id)
            logger.info(
                "premium_bonus_paid",
                referrer_id=referral.referrer_id,
                referred_id=referred_id,
                crystals=settings.referral_crystals_premium,
            )
        except Exception as e:
            logger.error("process_premium_bonus_error", referred_id=referred_id, error=str(e))

    def get_referral_link(self, user_id: int) -> str:
        """Return the referral deep-link for the given user."""
        bot_username = settings.bot_username or "your_bot"
        return f"https://t.me/{bot_username}?start=ref_{user_id}"

    async def get_stats(self, user_id: int) -> Dict[str, Any]:
        """Return referral stats: total referrals and crystals earned."""
        try:
            total = await self.referral_repo.count_referrals_this_month(user_id)
            # Crystals earned = registrations * 100 + premium bonuses * 500
            # We approximate from the count; a more precise query could sum crystals_earned
            crystals_earned = total * settings.referral_crystals_registration
            return {
                "total_referrals": total,
                "crystals_earned": crystals_earned,
                "referral_link": self.get_referral_link(user_id),
            }
        except Exception as e:
            logger.error("get_stats_error", user_id=user_id, error=str(e))
            return {"total_referrals": 0, "crystals_earned": 0, "referral_link": self.get_referral_link(user_id)}
