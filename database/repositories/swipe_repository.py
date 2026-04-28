from datetime import date, datetime, timezone
from typing import Set

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.swipe import Swipe

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class SwipeRepository(BaseRepository[Swipe]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Swipe)

    async def create_swipe(
        self,
        user_id: int,
        target_user_id: int,
        action: str,
        is_super_swipe: bool = False,
    ) -> Swipe:
        swipe = Swipe(
            user_id=user_id,
            target_user_id=target_user_id,
            action=action,
            is_super_swipe=is_super_swipe,
        )
        self.session.add(swipe)
        await self.session.flush()
        await self.session.refresh(swipe)
        logger.debug("swipe_created", user_id=user_id, target=target_user_id, action=action)
        return swipe

    async def has_liked(self, user_id: int, target_user_id: int) -> bool:
        result = await self.session.execute(
            select(Swipe.id).where(
                Swipe.user_id == user_id,
                Swipe.target_user_id == target_user_id,
                Swipe.action.in_(["like", "super_like"]),
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_swiped_user_ids(self, user_id: int) -> Set[int]:
        result = await self.session.execute(
            select(Swipe.target_user_id).where(Swipe.user_id == user_id)
        )
        return set(result.scalars().all())

    async def count_swipes_today(self, user_id: int) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await self.session.execute(
            select(func.count(Swipe.id)).where(
                Swipe.user_id == user_id,
                Swipe.created_at >= today_start,
            )
        )
        return result.scalar_one() or 0
