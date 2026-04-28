"""Rate limiter using Redis INCR+EXPIRE pattern."""
from typing import Tuple

from redis.asyncio import Redis

from bot.config import Settings

_HOUR = 3600
_MINUTE = 60
_DAY = 86400


class RateLimiter:
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    async def _check_limit(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window_seconds)
        if count <= limit:
            return True, limit - count
        ttl = await self.redis.ttl(key)
        return False, max(ttl, 0)

    async def check_swipe_limit(self, user_id: int, is_premium: bool) -> Tuple[bool, int]:
        limit = self.settings.rate_limit_swipes_premium if is_premium else self.settings.rate_limit_swipes_free
        return await self._check_limit(f"rate:swipe:{user_id}", limit, _HOUR)

    async def check_message_limit(self, user_id: int, chat_id: int, is_premium: bool) -> Tuple[bool, int]:
        limit = self.settings.rate_limit_messages_premium if is_premium else self.settings.rate_limit_messages_free
        return await self._check_limit(f"rate:msg:{user_id}:{chat_id}", limit, _HOUR)

    async def check_ai_limit(self, user_id: int, is_premium: bool) -> Tuple[bool, int]:
        if is_premium:
            return True, -1
        return await self._check_limit(f"rate:ai:{user_id}", self.settings.rate_limit_ai_suggestions_free, _DAY)

    async def check_global_limit(self, user_id: int) -> Tuple[bool, int]:
        return await self._check_limit(f"rate:global:{user_id}", 100, _MINUTE)
