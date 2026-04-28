from datetime import datetime, timezone
from typing import List

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.story import Story

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class StoryRepository(BaseRepository[Story]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Story)

    async def create_story(
        self,
        user_id: int,
        file_id: str,
        media_type: str,
        expires_at: datetime,
    ) -> Story:
        story = Story(
            user_id=user_id,
            file_id=file_id,
            media_type=media_type,
            expires_at=expires_at,
        )
        self.session.add(story)
        await self.session.flush()
        await self.session.refresh(story)
        logger.debug("story_created", user_id=user_id, media_type=media_type)
        return story

    async def get_active_stories(self, user_id: int) -> List[Story]:
        now = datetime.now(tz=timezone.utc)
        result = await self.session.execute(
            select(Story).where(
                Story.user_id == user_id,
                Story.expires_at > now,
            )
        )
        return list(result.scalars().all())

    async def increment_view_count(self, story_id: int) -> None:
        await self.session.execute(
            update(Story)
            .where(Story.id == story_id)
            .values(view_count=Story.view_count + 1)
        )
        await self.session.flush()

    async def delete_expired_stories(self) -> int:
        now = datetime.now(tz=timezone.utc)
        result = await self.session.execute(
            select(Story).where(Story.expires_at <= now)
        )
        expired = list(result.scalars().all())
        for story in expired:
            await self.session.delete(story)
        await self.session.flush()
        logger.info("expired_stories_deleted", count=len(expired))
        return len(expired)

    async def count_active_stories(self, user_id: int) -> int:
        now = datetime.now(tz=timezone.utc)
        result = await self.session.execute(
            select(func.count(Story.id)).where(
                Story.user_id == user_id,
                Story.expires_at > now,
            )
        )
        return result.scalar_one() or 0
