"""Integration tests for geo-search functionality with PostGIS.

Note: These tests require PostGIS extension. For full integration testing,
use testcontainers-python with PostGIS image or a test database with PostGIS enabled.
"""
import pytest
from sqlalchemy import text

from database.models.user import User
from database.models.profile import Profile
from database.repositories.user_repository import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeoSearch:
    """Test geo-search functionality with PostGIS."""
    
    @pytest.mark.skip(reason="Requires PostGIS extension - enable for full integration testing")
    async def test_postgis_extension_available(self, test_session):
        """Test that PostGIS extension is available."""
        result = await test_session.execute(
            text("SELECT PostGIS_Version();")
        )
        version = result.scalar()
        
        assert version is not None
    
    @pytest.mark.skip(reason="Requires PostGIS extension - enable for full integration testing")
    async def test_find_nearby_users(self, test_session):
        """Test finding users within specified distance."""
        # Create test users with locations
        user1 = User(
            telegram_id=111,
            username="user1",
            first_name="User1",
            is_active=True,
        )
        test_session.add(user1)
        await test_session.flush()
        
        profile1 = Profile(
            user_id=user1.id,
            age=25,
            city="Moscow",
            latitude=55.7558,  # Moscow center
            longitude=37.6173,
        )
        test_session.add(profile1)
        
        user2 = User(
            telegram_id=222,
            username="user2",
            first_name="User2",
            is_active=True,
        )
        test_session.add(user2)
        await test_session.flush()
        
        profile2 = Profile(
            user_id=user2.id,
            age=26,
            city="Moscow",
            latitude=55.7500,  # ~600m from center
            longitude=37.6200,
        )
        test_session.add(profile2)
        
        user3 = User(
            telegram_id=333,
            username="user3",
            first_name="User3",
            is_active=True,
        )
        test_session.add(user3)
        await test_session.flush()
        
        profile3 = Profile(
            user_id=user3.id,
            age=27,
            city="Saint Petersburg",
            latitude=59.9311,  # ~635 km away
            longitude=30.3609,
        )
        test_session.add(profile3)
        
        await test_session.commit()
        
        # Search for users within 10 km of Moscow center
        repo = UserRepository(test_session)
        nearby = await repo.get_candidates_for_swipe(
            user_id=user1.id,
            lat=55.7558,
            lon=37.6173,
            max_distance_km=10,
            limit=10,
        )
        
        # Should find user2 but not user3
        nearby_ids = [u.id for u in nearby]
        assert user2.id in nearby_ids
        assert user3.id not in nearby_ids
    
    @pytest.mark.skip(reason="Requires PostGIS extension - enable for full integration testing")
    async def test_distance_calculation_accuracy(self, test_session):
        """Test that distance calculations are accurate."""
        # Create two users at known distance
        user1 = User(
            telegram_id=444,
            username="user4",
            first_name="User4",
            is_active=True,
        )
        test_session.add(user1)
        await test_session.flush()
        
        profile1 = Profile(
            user_id=user1.id,
            age=25,
            city="Moscow",
            latitude=55.7558,
            longitude=37.6173,
        )
        test_session.add(profile1)
        
        user2 = User(
            telegram_id=555,
            username="user5",
            first_name="User5",
            is_active=True,
        )
        test_session.add(user2)
        await test_session.flush()
        
        profile2 = Profile(
            user_id=user2.id,
            age=26,
            city="Moscow Region",
            latitude=55.8558,  # ~11 km north
            longitude=37.6173,
        )
        test_session.add(profile2)
        
        await test_session.commit()
        
        # Search with 15 km radius - should find
        repo = UserRepository(test_session)
        nearby_15km = await repo.get_candidates_for_swipe(
            user_id=user1.id,
            lat=55.7558,
            lon=37.6173,
            max_distance_km=15,
            limit=10,
        )
        
        # Search with 5 km radius - should not find
        nearby_5km = await repo.get_candidates_for_swipe(
            user_id=user1.id,
            lat=55.7558,
            lon=37.6173,
            max_distance_km=5,
            limit=10,
        )
        
        nearby_15km_ids = [u.id for u in nearby_15km]
        nearby_5km_ids = [u.id for u in nearby_5km]
        
        assert user2.id in nearby_15km_ids
        assert user2.id not in nearby_5km_ids


@pytest.mark.integration
class TestGeoSearchSetup:
    """Test geo-search setup and configuration."""
    
    def test_geoalchemy2_import(self):
        """Test that GeoAlchemy2 can be imported."""
        from geoalchemy2 import Geography
        from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
        
        assert Geography is not None
        assert ST_DWithin is not None
    
    def test_profile_model_has_location(self):
        """Test that Profile model has location field."""
        from database.models.profile import Profile
        
        assert hasattr(Profile, 'location')
        assert hasattr(Profile, 'latitude')
        assert hasattr(Profile, 'longitude')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
