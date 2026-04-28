from typing import List, Optional

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.profile import Profile, ProfileInterest, ProfilePhoto

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Profile)

    async def get_by_user_id(self, user_id: int) -> Optional[Profile]:
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs) -> Profile:
        # Extract interests separately as they need special handling
        interests = kwargs.pop('interests', None)
        
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = Profile(user_id=user_id, **kwargs)
            self.session.add(profile)
            await self.session.flush()
            await self.session.refresh(profile)
            logger.info("profile_created", user_id=user_id)
        else:
            for key, value in kwargs.items():
                setattr(profile, key, value)
            await self.session.flush()
            await self.session.refresh(profile)
            logger.debug("profile_updated", user_id=user_id)
        
        # Handle interests if provided
        if interests is not None:
            await self.set_interests(profile.id, interests)
        
        return profile

    async def add_photo(
        self, profile_id: int, file_id: str, position: int
    ) -> ProfilePhoto:
        photo = ProfilePhoto(profile_id=profile_id, file_id=file_id, position=position)
        self.session.add(photo)
        await self.session.flush()
        await self.session.refresh(photo)
        logger.debug("photo_added", profile_id=profile_id, position=position)
        return photo

    async def get_photos(self, profile_id: int) -> List[ProfilePhoto]:
        result = await self.session.execute(
            select(ProfilePhoto)
            .where(ProfilePhoto.profile_id == profile_id)
            .order_by(ProfilePhoto.position)
        )
        return list(result.scalars().all())

    async def delete_photo(self, photo_id: int) -> None:
        await self.session.execute(
            delete(ProfilePhoto).where(ProfilePhoto.id == photo_id)
        )
        await self.session.flush()
        logger.debug("photo_deleted", photo_id=photo_id)

    async def add_interest(self, profile_id: int, interest: str) -> ProfileInterest:
        obj = ProfileInterest(profile_id=profile_id, interest=interest)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def set_interests(self, profile_id: int, interests: List[str]) -> None:
        await self.session.execute(
            delete(ProfileInterest).where(ProfileInterest.profile_id == profile_id)
        )
        for interest in interests:
            self.session.add(ProfileInterest(profile_id=profile_id, interest=interest))
        await self.session.flush()
        logger.debug("interests_set", profile_id=profile_id, count=len(interests))

    async def update_location(self, user_id: int, lat: float, lon: float) -> None:
        """Update profile location by user_id."""
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            return
        profile.latitude = lat
        profile.longitude = lon
        await self.session.flush()
        logger.debug("location_updated", user_id=user_id, lat=lat, lon=lon)
