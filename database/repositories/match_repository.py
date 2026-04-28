from typing import List, Optional

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.match import Match

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Match)

    async def create_match(self, user1_id: int, user2_id: int) -> Match:
        # Normalise order so user1_id < user2_id for consistency
        u1, u2 = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)
        match = Match(user1_id=u1, user2_id=u2)
        self.session.add(match)
        await self.session.flush()
        await self.session.refresh(match)
        logger.info("match_created", user1_id=u1, user2_id=u2, match_id=match.id)
        return match

    async def get_match(self, user1_id: int, user2_id: int) -> Optional[Match]:
        u1, u2 = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)
        result = await self.session.execute(
            select(Match).where(Match.user1_id == u1, Match.user2_id == u2)
        )
        return result.scalar_one_or_none()

    async def get_user_matches(self, user_id: int) -> List[Match]:
        result = await self.session.execute(
            select(Match).where(
                Match.is_active.is_(True),
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
            )
        )
        return list(result.scalars().all())

    async def match_exists(self, user1_id: int, user2_id: int) -> bool:
        return await self.get_match(user1_id, user2_id) is not None
