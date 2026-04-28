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
        self, user: User, mode: str = "normal"
    ) -> Optional[Tuple[User, float, str]]:
        """Return (candidate, score, explanation) or None."""
        try:
            profile = await self.profile_repo.get_by_user_id(user.id)
            if profile is None or profile.latitude is None or profile.longitude is None:
                logger.warning("no_location_for_user", user_id=user.id)
                return None

            user_dict = {
                "id": user.id,
                "first_name": user.first_name,
                "is_premium": user.is_premium,
                "about_me": profile.about_me,
                "age": profile.age,
                "city": profile.city,
                "relationship_goals": profile.relationship_goals,
                "mbti_type": profile.mbti_type,
                "attachment_style": profile.attachment_style,
                "latitude": profile.latitude,
                "longitude": profile.longitude,
            }

            if mode == "deep":
                candidates = await self.user_repo.get_all_active_users(
                    exclude_user_id=user.id, limit=50
                )
                if not candidates:
                    return None
                candidate_dicts = await self._build_candidate_dicts(candidates)
                top_matches = await self.ai_service.deep_search(user_dict, candidate_dicts)
                if not top_matches:
                    return None
                top = top_matches[0]
                top_user = next(
                    (c for c in candidates if c.id == top.get("user_id")), None
                )
                if top_user is None:
                    return None
                score = float(top.get("score", 50))
                explanation = top.get("explanation", "")
                logger.info("deep_search_candidate", user_id=user.id, candidate_id=top_user.id, score=score)
                return top_user, score, explanation

            # Normal mode
            max_distance = 50.0
            geo_candidates = await self.user_repo.get_candidates_for_swipe(
                user_id=user.id,
                lat=profile.latitude,
                lon=profile.longitude,
                max_distance_km=max_distance,
                limit=20,
            )
            if not geo_candidates:
                return None

            best_candidate: Optional[User] = None
            best_score = -1.0
            best_explanation = ""

            for candidate in geo_candidates:
                cand_profile = await self.profile_repo.get_by_user_id(candidate.id)
                if cand_profile is None:
                    continue

                cand_dict = {
                    "id": candidate.id,
                    "first_name": candidate.first_name,
                    "is_premium": candidate.is_premium,
                    "about_me": cand_profile.about_me,
                    "age": cand_profile.age,
                    "city": cand_profile.city,
                    "relationship_goals": cand_profile.relationship_goals,
                    "mbti_type": cand_profile.mbti_type,
                    "attachment_style": cand_profile.attachment_style,
                }

                compat = await self.ai_service.calculate_compatibility(user_dict, cand_dict)
                compat_score = float(compat.get("score", 50)) / 100.0

                if cand_profile.latitude is not None and cand_profile.longitude is not None:
                    dist_km = self._calculate_distance(
                        profile.latitude, profile.longitude,
                        cand_profile.latitude, cand_profile.longitude,
                    )
                    distance_factor = max(0.0, 1.0 - dist_km / max_distance)
                else:
                    distance_factor = 0.5

                hybrid = 0.7 * compat_score + 0.3 * distance_factor

                if hybrid > best_score:
                    best_score = hybrid
                    best_candidate = candidate
                    best_explanation = compat.get("explanation", "")

            if best_candidate is None:
                return None

            logger.info(
                "next_candidate_found",
                user_id=user.id,
                candidate_id=best_candidate.id,
                score=round(best_score, 3),
            )
            return best_candidate, round(best_score * 100, 1), best_explanation

        except Exception as e:
            logger.error("get_next_candidate_error", user_id=user.id, error=str(e))
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
