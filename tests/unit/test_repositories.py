"""Unit tests for repository layer with mocked database."""
import pytest
from datetime import datetime, timedelta, timezone

from database.models.user import User
from database.models.profile import Profile
from database.repositories.user_repository import UserRepository
from database.repositories.profile_repository import ProfileRepository


@pytest.mark.asyncio
@pytest.mark.unit
class TestUserRepository:
    """Test UserRepository methods."""
    
    async def test_get_by_telegram_id(self, test_session, sample_user):
        """Test getting user by Telegram ID."""
        repo = UserRepository(test_session)
        
        user = await repo.get_by_telegram_id(sample_user.telegram_id)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.telegram_id == sample_user.telegram_id
        assert user.username == sample_user.username
    
    async def test_get_by_telegram_id_not_found(self, test_session):
        """Test getting non-existent user returns None."""
        repo = UserRepository(test_session)
        
        user = await repo.get_by_telegram_id(999999999)
        
        assert user is None
    
    async def test_add_crystals(self, test_session, sample_user):
        """Test adding crystals to user balance."""
        repo = UserRepository(test_session)
        initial_balance = sample_user.crystal_balance
        
        await repo.add_crystals(sample_user.id, 50)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert sample_user.crystal_balance == initial_balance + 50
    
    async def test_deduct_crystals_sufficient_balance(self, test_session, sample_user):
        """Test deducting crystals with sufficient balance."""
        repo = UserRepository(test_session)
        initial_balance = sample_user.crystal_balance
        
        success = await repo.deduct_crystals(sample_user.id, 30)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert success is True
        assert sample_user.crystal_balance == initial_balance - 30
    
    async def test_deduct_crystals_insufficient_balance(self, test_session, sample_user):
        """Test deducting crystals with insufficient balance."""
        repo = UserRepository(test_session)
        initial_balance = sample_user.crystal_balance
        
        success = await repo.deduct_crystals(sample_user.id, initial_balance + 100)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert success is False
        assert sample_user.crystal_balance == initial_balance
    
    async def test_set_premium(self, test_session, sample_user):
        """Test setting premium status."""
        repo = UserRepository(test_session)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=30)
        
        await repo.set_premium(sample_user.id, expires_at)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert sample_user.is_premium is True
        assert sample_user.premium_expires_at is not None
    
    async def test_add_warning(self, test_session, sample_user):
        """Test adding warning to user."""
        repo = UserRepository(test_session)
        initial_warnings = sample_user.warnings_count
        
        count = await repo.add_warning(sample_user.id)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert count == initial_warnings + 1
        assert sample_user.warnings_count == initial_warnings + 1
    
    async def test_suspend_user(self, test_session, sample_user):
        """Test suspending user."""
        repo = UserRepository(test_session)
        until = datetime.now(tz=timezone.utc) + timedelta(hours=24)
        
        await repo.suspend_user(sample_user.id, until)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert sample_user.is_suspended is True
        assert sample_user.suspended_until is not None
    
    async def test_update_timezone(self, test_session, sample_user):
        """Test updating user timezone."""
        repo = UserRepository(test_session)
        new_timezone = "Asia/Tokyo"
        
        await repo.update_timezone(sample_user.id, new_timezone)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert sample_user.timezone == new_timezone
    
    async def test_toggle_daily_reports(self, test_session, sample_user):
        """Test toggling daily reports setting."""
        repo = UserRepository(test_session)
        initial_state = sample_user.daily_reports_enabled
        
        await repo.toggle_daily_reports(sample_user.id, not initial_state)
        await test_session.commit()
        await test_session.refresh(sample_user)
        
        assert sample_user.daily_reports_enabled == (not initial_state)


@pytest.mark.asyncio
@pytest.mark.unit
class TestProfileRepository:
    """Test ProfileRepository methods."""
    
    async def test_get_by_user_id(self, test_session, sample_profile):
        """Test getting profile by user ID."""
        repo = ProfileRepository(test_session)
        
        profile = await repo.get_by_user_id(sample_profile.user_id)
        
        assert profile is not None
        assert profile.id == sample_profile.id
        assert profile.user_id == sample_profile.user_id
        assert profile.city == sample_profile.city
    
    async def test_get_by_user_id_not_found(self, test_session):
        """Test getting non-existent profile returns None."""
        repo = ProfileRepository(test_session)
        
        profile = await repo.get_by_user_id(999999)
        
        assert profile is None
    
    async def test_create_or_update_new_profile(self, test_session, sample_user):
        """Test creating new profile."""
        repo = ProfileRepository(test_session)
        
        profile = await repo.create_or_update(
            user_id=sample_user.id,
            age=28,
            city="Saint Petersburg",
            height=180,
            relationship_goals="friendship",
            mbti_type="ENFP",
            attachment_style="anxious",
            interests=["music", "travel"],
            about_me="Test bio",
        )
        await test_session.commit()
        
        assert profile is not None
        assert profile.user_id == sample_user.id
        assert profile.age == 28
        assert profile.city == "Saint Petersburg"
    
    async def test_update_existing_profile(self, test_session, sample_profile):
        """Test updating existing profile."""
        repo = ProfileRepository(test_session)
        
        updated = await repo.create_or_update(
            user_id=sample_profile.user_id,
            age=30,
            city="Kazan",
            height=sample_profile.height,
            relationship_goals=sample_profile.relationship_goals,
            mbti_type=sample_profile.mbti_type,
            attachment_style=sample_profile.attachment_style,
            interests=["sports"],
            about_me="Updated bio",
        )
        await test_session.commit()
        await test_session.refresh(sample_profile)
        
        assert updated.id == sample_profile.id
        assert sample_profile.age == 30
        assert sample_profile.city == "Kazan"
        assert sample_profile.about_me == "Updated bio"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
