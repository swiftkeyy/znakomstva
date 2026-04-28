from datetime import date, datetime, timezone
from typing import List

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.message import Message

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def create_message(
        self,
        match_id: int,
        sender_id: int,
        content: str,
        message_type: str = "text",
    ) -> Message:
        msg = Message(
            match_id=match_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        logger.debug("message_created", match_id=match_id, sender_id=sender_id)
        return msg

    async def get_chat_history(
        self, match_id: int, limit: int = 50, offset: int = 0
    ) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.match_id == match_id)
            .order_by(Message.sent_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def mark_as_read(self, match_id: int, user_id: int) -> None:
        """Mark all messages in a match as read for the given recipient."""
        await self.session.execute(
            update(Message)
            .where(
                Message.match_id == match_id,
                Message.sender_id != user_id,
                Message.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.session.flush()

    async def count_messages_today(self, user_id: int) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.sender_id == user_id,
                Message.sent_at >= today_start,
            )
        )
        return result.scalar_one() or 0

    async def create(self, match_id: int, sender_id: int, content: str, message_type: str = "text") -> Message:
        """Alias for create_message."""
        return await self.create_message(match_id, sender_id, content, message_type)

    async def get_recent(self, match_id: int, limit: int = 10) -> List[Message]:
        return await self.get_chat_history(match_id, limit=limit)

    async def count_user_messages(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Message.id)).where(Message.sender_id == user_id)
        )
        return result.scalar_one() or 0
