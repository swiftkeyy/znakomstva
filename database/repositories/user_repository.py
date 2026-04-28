from datetime import datetime
from typing import List, Optional

import structlog
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, telegram_id: int, username: Optional[str], first_name: str) -> User:
        """Create a new user."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            is_active=True,
            is_registered=False,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        logger.info("user_created", telegram_id=telegram_id)
        return user

    async def get_candidates_for_swipe(
        self,
        user_id: int,
        lat: float,
        lon: float,
        max_distance_km: float,
        limit: int = 20,
    ) -> List[User]:
        from database.models.profile import Profile
        from database.models.swipe import Swipe

        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        max_distance_m = max_distance_km * 1000

        already_swiped = select(Swipe.target_user_id).where(Swipe.user_id == user_id)

        stmt = (
            select(User)
            .join(Profile, Profile.user_id == User.id)
            .where(
                User.id != user_id,
                User.is_active.is_(True),
                User.is_suspended.is_(False),
                User.id.not_in(already_swiped),
                ST_DWithin(Profile.location, point, max_distance_m),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_users(
        self, exclude_user_id: int, limit: int = 50
    ) -> List[User]:
        result = await self.session.execute(
            select(User)
            .where(
                User.id != exclude_user_id,
                User.is_active.is_(True),
                User.is_suspended.is_(False),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_active(self, user_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=func.now())
        )
        await self.session.flush()

    async def add_crystals(self, user_id: int, amount: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(crystal_balance=User.crystal_balance + amount)
        )
        await self.session.flush()
        logger.info("crystals_added", user_id=user_id, amount=amount)

    async def deduct_crystals(self, user_id: int, amount: int) -> bool:
        user = await self.get_by_id(user_id)
        if user is None or user.crystal_balance < amount:
            logger.warning("insufficient_crystals", user_id=user_id, amount=amount)
            return False
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(crystal_balance=User.crystal_balance - amount)
        )
        await self.session.flush()
        logger.info("crystals_deducted", user_id=user_id, amount=amount)
        return True

    async def spend_crystals(self, user_id: int, amount: int) -> bool:
        """Alias for deduct_crystals for backward compatibility."""
        return await self.deduct_crystals(user_id, amount)

    async def set_premium(self, user_id: int, expires_at: datetime) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_premium=True, premium_expires_at=expires_at)
        )
        await self.session.flush()
        logger.info("premium_set", user_id=user_id, expires_at=expires_at)

    async def add_warning(self, user_id: int) -> int:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(warnings_count=User.warnings_count + 1)
        )
        await self.session.flush()
        user = await self.get_by_id(user_id)
        count = user.warnings_count if user else 0
        logger.warning("warning_added", user_id=user_id, warnings_count=count)
        return count

    async def suspend_user(self, user_id: int, until: datetime) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_suspended=True, suspended_until=until)
        )
        await self.session.flush()
        logger.warning("user_suspended", user_id=user_id, until=until)

    async def update_timezone(self, user_id: int, timezone: str) -> None:
        """Update user's timezone."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(timezone=timezone)
        )
        await self.session.flush()
        logger.info("timezone_updated", user_id=user_id, timezone=timezone)

    async def mark_registered(self, user_id: int) -> None:
        """Mark user as registered (has completed profile setup)."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_registered=True)
        )
        await self.session.flush()
        logger.info("user_registered", user_id=user_id)

    async def toggle_daily_reports(self, user_id: int, enabled: bool) -> None:
        """Toggle daily reports for a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(daily_reports_enabled=enabled)
        )
        await self.session.flush()
        logger.info("daily_reports_toggled", user_id=user_id, enabled=enabled)
