from datetime import datetime, timedelta, timezone
from typing import List, Optional

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.speed_dating import (
    SpeedDatingPair,
    SpeedDatingParticipant,
    SpeedDatingSession,
)
from database.models.user import User

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class SpeedDatingRepository(BaseRepository[SpeedDatingSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SpeedDatingSession)

    async def create_session(
        self, scheduled_time: datetime, duration_minutes: int = 3
    ) -> SpeedDatingSession:
        sess = SpeedDatingSession(
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
        )
        self.session.add(sess)
        await self.session.flush()
        await self.session.refresh(sess)
        logger.info("speed_dating_session_created", session_id=sess.id)
        return sess

    async def add_participant(self, session_id: int, user_id: int) -> None:
        participant = SpeedDatingParticipant(session_id=session_id, user_id=user_id)
        self.session.add(participant)
        await self.session.flush()
        logger.debug("participant_added", session_id=session_id, user_id=user_id)

    async def get_participants(self, session_id: int) -> List[User]:
        result = await self.session.execute(
            select(User)
            .join(
                SpeedDatingParticipant,
                SpeedDatingParticipant.user_id == User.id,
            )
            .where(SpeedDatingParticipant.session_id == session_id)
        )
        return list(result.scalars().all())

    async def create_pair(
        self, session_id: int, user1_id: int, user2_id: int
    ) -> SpeedDatingPair:
        pair = SpeedDatingPair(
            session_id=session_id, user1_id=user1_id, user2_id=user2_id
        )
        self.session.add(pair)
        await self.session.flush()
        await self.session.refresh(pair)
        logger.debug("pair_created", session_id=session_id, u1=user1_id, u2=user2_id)
        return pair

    async def record_decision(
        self, pair_id: int, user_id: int, wants_match: bool
    ) -> None:
        pair = await self.session.get(SpeedDatingPair, pair_id)
        if pair is None:
            return
        if pair.user1_id == user_id:
            pair.user1_wants_match = wants_match
        elif pair.user2_id == user_id:
            pair.user2_wants_match = wants_match
        await self.session.flush()
        logger.debug("decision_recorded", pair_id=pair_id, user_id=user_id, wants_match=wants_match)

    async def get_pair(self, pair_id: int) -> Optional[SpeedDatingPair]:
        return await self.session.get(SpeedDatingPair, pair_id)

    async def count_user_sessions_this_week(self, user_id: int) -> int:
        now = datetime.now(tz=timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(SpeedDatingParticipant.id)).where(
                SpeedDatingParticipant.user_id == user_id,
                SpeedDatingParticipant.joined_at >= week_start,
            )
        )
        return result.scalar_one() or 0

    async def update_session_status(self, session_id: int, status: str) -> None:
        await self.session.execute(
            update(SpeedDatingSession)
            .where(SpeedDatingSession.id == session_id)
            .values(status=status)
        )
        await self.session.flush()
        logger.info("session_status_updated", session_id=session_id, status=status)

    async def get_active_sessions(self) -> List[SpeedDatingSession]:
        """Get all active or scheduled speed dating sessions."""
        result = await self.session.execute(
            select(SpeedDatingSession)
            .where(SpeedDatingSession.status.in_(["scheduled", "active"]))
            .order_by(SpeedDatingSession.scheduled_time)
        )
        return list(result.scalars().all())
