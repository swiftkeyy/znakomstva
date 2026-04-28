from typing import Generic, List, Optional, Type, TypeVar

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import Base

T = TypeVar("T", bound=Base)
logger = structlog.get_logger(__name__)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[T]:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.debug("created", model=self.model.__name__, id=obj.id)
        return obj

    async def update(self, id: int, **kwargs) -> Optional[T]:
        obj = await self.get_by_id(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.debug("updated", model=self.model.__name__, id=id)
        return obj

    async def delete(self, id: int) -> bool:
        obj = await self.get_by_id(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        logger.debug("deleted", model=self.model.__name__, id=id)
        return True

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
