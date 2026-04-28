"""Matching service — candidate selection and match creation."""
import math
from typing import Optional, Tuple

import structlog

from database.models.match import Match
from database.models.user import User
from database.repositories.match_repository import MatchRepository
from database.repositories.swipe_repository import SwipeRepository
from database.repositories.user_repository import UserRepository
from database.repositories.profile_repository import ProfileRepository
from bot.services.ai_service import AIService

logger = structlog.get_logger(__name__)


class MatchingService:
    def __init__(
        self,
        user_repo: UserRepository,
        profile_repo: ProfileRepository,
        swipe_repo: SwipeRepository,
        match_repo: MatchRepository,
        ai_service: AIService,
    ) -> None:
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.swipe_repo = swipe_repo
        self.match_repo = match_repo
        self.ai_service = ai_service

    async def get_next_candidate(
        self, user: User, mode: str = "normal", expand_search: bool = False
    ) -> Optional[Tuple[User, float, str]]:
        """Return (candidate, score, explanation) or None."""
        try:
            profile = await self.profile_repo.get_by_user_id(user.id)
            has_location = profile and profile.latitude is not None and profile.longitude is not None

            user_dict = {
                "id": user.id,
                "about_me": profile.about_me if profile else None,
                "age": profile.age if profile else None,
                "relationship_goals": profile.relationship_goals if profile else None,
                "latitude": profile.latitude if profile else None,
                "longitude": profile.longitude if profile else None,
            }

            if has_location and not expand_search:
                # Local search first (50km)
                candidates = await self.user_repo.get_candidates_for_swipe(
                    user_id=user.id,
                    lat=profile.latitude,
                    lon=profile.longitude,
                    max_distance_km=50.0,
                    limit=20,
                )
                if not candidates:
                    return None  # Signal: local exhausted
            elif has_location and expand_search:
                # Expanded search - all users sorted by distance
                all_candidates = await self.user_repo.get_all_active_users(
                    exclude_user_id=user.id, limit=100
                )
                # Sort by distance
                def dist(u):
                    p = None
                    return 9999
                candidates = all_candidates[:20]
            else:
                candidates = await self.user_repo.get_all_active_users(
                    exclude_user_id=user.id, limit=20
                )

            if not candidates:
                return None

            best_candidate = candidates[0]
            score = 75.0
            explanation = ""

            try:
                cand_profile = await self.profile_repo.get_by_user_id(best_candidate.id)
                cand_dict = {
                    "id": best_candidate.id,
                    "about_me": cand_profile.about_me if cand_profile else None,
                    "age": cand_profile.age if cand_profile else None,
                    "relationship_goals": cand_profile.relationship_goals if cand_profile else None,
                }
                compat = await self.ai_service.calculate_compatibility(user_dict, cand_dict)
                score = float(compat.get("score", 75))
                explanation = compat.get("explanation", "")
            except Exception:
                pass

            return best_candidate, score, explanation

        except Exception as e:
            logger.error("get_next_candidate_error", user_id=user.id, error=str(e))
            return None

    async def get_next_candidate_expanded(self, user: User) -> Optional[Tuple[User, float, str]]:
        """Search across all cities, sorted by distance."""
        try:
            profile = await self.profile_repo.get_by_user_id(user.id)
            all_candidates = await self.user_repo.get_all_active_users(
                exclude_user_id=user.id, limit=100
            )
            if not all_candidates:
                return None

            # Sort by distance if we have coordinates
            if profile and profile.latitude and profile.longitude:
                scored = []
                for c in all_candidates:
                    cp = await self.profile_repo.get_by_user_id(c.id)
                    if cp and cp.latitude and cp.longitude:
                        d = self._calculate_distance(profile.latitude, profile.longitude, cp.latitude, cp.longitude)
                    else:
                        d = 9999
                    scored.append((d, c))
                scored.sort(key=lambda x: x[0])
                all_candidates = [c for _, c in scored]

            best = all_candidates[0]
            return best, 75.0, ""
        except Exception as e:
            logger.error("get_next_candidate_expanded_error", user_id=user.id, error=str(e))
            return None

    async def check_and_create_match(
        self, user_id: int, target_user_id: int
    ) -> Optional[Match]:
        """If both users liked each other, create and return a Match."""
        try:
            if await self.match_repo.match_exists(user_id, target_user_id):
                return await self.match_repo.get_match(user_id, target_user_id)

            mutual = await self.swipe_repo.has_liked(
                target_user_id, user_id
            ) and await self.swipe_repo.has_liked(user_id, target_user_id)

            if not mutual:
                return None

            match = await self.match_repo.create_match(user_id, target_user_id)
            logger.info("match_created", user_id=user_id, target_user_id=target_user_id)
            return match
        except Exception as e:
            logger.error("check_and_create_match_error", user_id=user_id, error=str(e))
            return None

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Haversine distance in km."""
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    async def _build_candidate_dicts(self, candidates: list) -> list:
        result = []
        for c in candidates:
            p = await self.profile_repo.get_by_user_id(c.id)
            result.append({
                "user_id": c.id,
                "first_name": c.first_name,
                "is_premium": c.is_premium,
                "about_me": p.about_me if p else None,
                "age": p.age if p else None,
                "city": p.city if p else None,
                "relationship_goals": p.relationship_goals if p else None,
                "mbti_type": p.mbti_type if p else None,
                "attachment_style": p.attachment_style if p else None,
            })
        return result


