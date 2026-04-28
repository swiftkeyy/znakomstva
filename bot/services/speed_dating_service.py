"""Speed dating service — session management, pairing, and decisions."""
import random
from typing import Any, List, Optional, Tuple

import structlog

from database.models.user import User
from database.repositories.speed_dating_repository import SpeedDatingRepository
from database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)

_FREE_WEEKLY_LIMIT = 3


class SpeedDatingService:
    def __init__(
        self,
        speed_dating_repo: SpeedDatingRepository,
        user_repo: UserRepository,
    ) -> None:
        self.speed_dating_repo = speed_dating_repo
        self.user_repo = user_repo

    async def register_user(
        self, session_id: int, user: User
    ) -> Tuple[bool, str]:
        """Register user for a speed dating session. Free users limited to 3/week."""
        try:
            if not user.is_premium:
                sessions_this_week = await self.speed_dating_repo.count_user_sessions_this_week(
                    user.id
                )
                if sessions_this_week >= _FREE_WEEKLY_LIMIT:
                    return (
                        False,
                        f"Вы достигли лимита {_FREE_WEEKLY_LIMIT} сессий в неделю. "
                        "Оформите Premium для безлимитного участия.",
                    )

            await self.speed_dating_repo.add_participant(session_id, user.id)
            logger.info("speed_dating_registered", session_id=session_id, user_id=user.id)
            return True, "Вы успешно зарегистрированы на сессию знакомств!"
        except Exception as e:
            logger.error("register_user_error", session_id=session_id, user_id=user.id, error=str(e))
            return False, "Ошибка при регистрации. Попробуйте позже."

    async def start_session(
        self, session_id: int
    ) -> List[Tuple[User, User]]:
        """Create initial pairs and update session status to active."""
        try:
            await self.speed_dating_repo.update_session_status(session_id, "active")
            participants = await self.speed_dating_repo.get_participants(session_id)
            pairs = self._make_pairs(participants)

            for user1, user2 in pairs:
                await self.speed_dating_repo.create_pair(session_id, user1.id, user2.id)

            logger.info("speed_dating_started", session_id=session_id, pairs=len(pairs))
            return pairs
        except Exception as e:
            logger.error("start_session_error", session_id=session_id, error=str(e))
            return []

    async def rotate_pairs(
        self, session_id: int
    ) -> List[Tuple[User, User]]:
        """Create a new round of pairs (shuffle participants)."""
        try:
            participants = await self.speed_dating_repo.get_participants(session_id)
            pairs = self._make_pairs(participants)

            for user1, user2 in pairs:
                await self.speed_dating_repo.create_pair(session_id, user1.id, user2.id)

            logger.info("speed_dating_rotated", session_id=session_id, pairs=len(pairs))
            return pairs
        except Exception as e:
            logger.error("rotate_pairs_error", session_id=session_id, error=str(e))
            return []

    async def record_decision(
        self, pair_id: int, user_id: int, wants_match: bool
    ) -> Optional[bool]:
        """Record a user's decision. Returns True if mutual match, False if not, None if pending."""
        try:
            await self.speed_dating_repo.record_decision(pair_id, user_id, wants_match)
            pair = await self.speed_dating_repo.get_pair(pair_id)
            if pair is None:
                return None

            if pair.user1_wants_match is None or pair.user2_wants_match is None:
                return None  # Still waiting for the other user

            mutual = pair.user1_wants_match and pair.user2_wants_match
            logger.info(
                "speed_dating_decision",
                pair_id=pair_id,
                user_id=user_id,
                mutual=mutual,
            )
            return mutual
        except Exception as e:
            logger.error("record_decision_error", pair_id=pair_id, user_id=user_id, error=str(e))
            return None

    @staticmethod
    def _make_pairs(participants: List[User]) -> List[Tuple[User, User]]:
        """Shuffle participants and create sequential pairs."""
        shuffled = list(participants)
        random.shuffle(shuffled)
        pairs = []
        for i in range(0, len(shuffled) - 1, 2):
            pairs.append((shuffled[i], shuffled[i + 1]))
        return pairs
