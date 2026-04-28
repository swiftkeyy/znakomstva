"""Story service — create, view, and clean up user stories."""
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import structlog

from database.models.story import Story
from database.repositories.story_repository import StoryRepository

logger = structlog.get_logger(__name__)

_FREE_STORY_LIMIT = 1
_PREMIUM_STORY_LIMIT = 5
_STORY_TTL_HOURS = 24


class StoryService:
    def __init__(self, story_repo: StoryRepository) -> None:
        self.story_repo = story_repo

    async def create_story(
        self,
        user_id: int,
        file_id: str,
        media_type: str,
        is_premium: bool,
    ) -> Tuple[bool, str]:
        """Create a story with 24h expiry. Enforces per-user limits."""
        try:
            limit = _PREMIUM_STORY_LIMIT if is_premium else _FREE_STORY_LIMIT
            current_count = await self.story_repo.count_active_stories(user_id)

            if current_count >= limit:
                if is_premium:
                    return False, f"Достигнут лимит активных историй ({limit} для Premium)."
                return (
                    False,
                    f"Бесплатный аккаунт позволяет иметь {limit} активную историю. "
                    "Оформите Premium для публикации до 5 историй.",
                )

            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=_STORY_TTL_HOURS)
            await self.story_repo.create_story(
                user_id=user_id,
                file_id=file_id,
                media_type=media_type,
                expires_at=expires_at,
            )
            logger.info("story_created", user_id=user_id, media_type=media_type)
            return True, "История опубликована и будет доступна 24 часа."
        except Exception as e:
            logger.error("create_story_error", user_id=user_id, error=str(e))
            return False, "Ошибка при создании истории. Попробуйте позже."

    async def get_user_stories(self, user_id: int) -> List[Story]:
        """Return all active (non-expired) stories for a user."""
        try:
            return await self.story_repo.get_active_stories(user_id)
        except Exception as e:
            logger.error("get_user_stories_error", user_id=user_id, error=str(e))
            return []

    async def view_story(self, story_id: int, viewer_id: int) -> Story:
        """Increment view count and return the story."""
        story = await self.story_repo.get_by_id(story_id)
        if story is None:
            raise ValueError(f"Story {story_id} not found")
        await self.story_repo.increment_view_count(story_id)
        await self.story_repo.session.refresh(story)
        logger.debug("story_viewed", story_id=story_id, viewer_id=viewer_id)
        return story

    async def cleanup_expired(self) -> int:
        """Delete expired stories and return the count removed."""
        try:
            count = await self.story_repo.delete_expired_stories()
            logger.info("expired_stories_cleaned", count=count)
            return count
        except Exception as e:
            logger.error("cleanup_expired_error", error=str(e))
            return 0
