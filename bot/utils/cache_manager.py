"""Cache manager using Redis for the Моя половинка bot."""
import json
from typing import Any, Callable, Optional

from redis.asyncio import Redis

# Global Redis instance (set by main.py)
_redis_instance: Optional[Redis] = None


def set_redis_instance(redis: Redis) -> None:
    """Set the global Redis instance for CacheManager."""
    global _redis_instance
    _redis_instance = redis


class CacheManager:
    def __init__(self, redis: Optional[Redis] = None) -> None:
        self.redis = redis or _redis_instance
        if self.redis is None:
            raise RuntimeError("Redis instance not provided and global instance not set")

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        result = await self.redis.set(key, json.dumps(value), ex=ttl)
        return bool(result)

    async def delete(self, key: str) -> bool:
        result = await self.redis.delete(key)
        return bool(result)

    async def invalidate_pattern(self, pattern: str) -> int:
        count = 0
        async for key in self.redis.scan_iter(pattern):
            await self.redis.delete(key)
            count += 1
        return count

    async def get_or_set(self, key: str, factory: Callable, ttl: int = 3600) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl)
        return value

    async def exists(self, key: str) -> bool:
        return bool(await self.redis.exists(key))
