"""Unit tests for service layer with mocked dependencies."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from bot.services.rate_limiter import RateLimiter
from bot.services.daily_report_service import DailyReportService


@pytest.mark.asyncio
@pytest.mark.unit
class TestRateLimiter:
    """Test RateLimiter service."""
    
    async def test_check_swipe_limit_free_user_within_limit(self, mock_redis, test_settings):
        """Test swipe limit check for free user within limit."""
        mock_redis.get.return_value = b"50"
        limiter = RateLimiter(mock_redis, test_settings)
        
        allowed, remaining = await limiter.check_swipe_limit(user_id=1, is_premium=False)
        
        assert allowed is True
        assert remaining is not None
        mock_redis.incr.assert_called_once()
    
    async def test_check_swipe_limit_free_user_exceeded(self, mock_redis, test_settings):
        """Test swipe limit check for free user who exceeded limit."""
        mock_redis.get.return_value = b"100"
        mock_redis.ttl.return_value = 1800
        limiter = RateLimiter(mock_redis, test_settings)
        
        allowed, ttl = await limiter.check_swipe_limit(user_id=1, is_premium=False)
        
        assert allowed is False
        assert ttl == 1800
        mock_redis.incr.assert_not_called()
    
    async def test_check_swipe_limit_premium_user_higher_limit(self, mock_redis, test_settings):
        """Test swipe limit check for premium user has higher limit."""
        mock_redis.get.return_value = b"200"
        limiter = RateLimiter(mock_redis, test_settings)
        
        allowed, remaining = await limiter.check_swipe_limit(user_id=1, is_premium=True)
        
        assert allowed is True
        mock_redis.incr.assert_called_once()
    
    async def test_check_message_limit_within_limit(self, mock_redis, test_settings):
        """Test message limit check within limit."""
        mock_redis.get.return_value = None
        limiter = RateLimiter(mock_redis, test_settings)
        
        allowed, remaining = await limiter.check_message_limit(
            user_id=1, chat_id=2, is_premium=False
        )
        
        assert allowed is True
        mock_redis.setex.assert_called_once()
    
    async def test_check_ai_suggestion_limit_premium_unlimited(self, mock_redis, test_settings):
        """Test AI suggestion limit for premium user is unlimited."""
        limiter = RateLimiter(mock_redis, test_settings)
        
        allowed, remaining = await limiter.check_ai_suggestion_limit(
            user_id=1, is_premium=True
        )
        
        assert allowed is True
        assert remaining is None
        mock_redis.get.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
class TestDailyReportService:
    """Test DailyReportService."""
    
    async def test_generate_report(self, test_session, sample_user):
        """Test generating daily report for user."""
        # Mock repositories
        user_repo = MagicMock()
        swipe_repo = MagicMock()
        swipe_repo.count_swipes_today = AsyncMock(return_value=15)
        
        match_repo = MagicMock()
        match_repo.get_user_matches = AsyncMock(return_value=[])
        
        message_repo = MagicMock()
        message_repo.count_messages_today = AsyncMock(return_value=25)
        
        story_repo = MagicMock()
        story_repo.get_active_stories = AsyncMock(return_value=[])
        
        service = DailyReportService(
            user_repo, swipe_repo, match_repo, message_repo, story_repo
        )
        
        report = await service.generate_report(sample_user.id)
        
        assert report["user_id"] == sample_user.id
        assert report["likes_sent"] == 15
        assert report["messages_sent"] == 25
        assert "generated_at" in report
    
    async def test_format_report(self):
        """Test report formatting."""
        report = {
            "story_views": 10,
            "likes_sent": 5,
            "new_matches": 2,
            "messages_sent": 15,
        }
        
        text = DailyReportService._format_report(report)
        
        assert "10" in text
        assert "5" in text
        assert "2" in text
        assert "15" in text
        assert "статистика" in text.lower()


@pytest.mark.asyncio
@pytest.mark.unit
class TestMatchingService:
    """Test MatchingService."""
    
    async def test_calculate_distance(self):
        """Test Haversine distance calculation."""
        from bot.services.matching_service import MatchingService
        
        # Mock dependencies
        user_repo = MagicMock()
        swipe_repo = MagicMock()
        ai_service = MagicMock()
        
        service = MatchingService(user_repo, swipe_repo, ai_service)
        
        # Moscow to Saint Petersburg (approx 635 km)
        profile1 = MagicMock()
        profile1.latitude = 55.7558
        profile1.longitude = 37.6173
        
        profile2 = MagicMock()
        profile2.latitude = 59.9311
        profile2.longitude = 30.3609
        
        distance = service._calculate_distance(profile1, profile2)
        
        # Allow 10% margin of error
        assert 570 < distance < 700
    
    async def test_check_mutual_match_both_liked(self):
        """Test mutual match detection when both users liked."""
        from bot.services.matching_service import MatchingService
        
        user_repo = MagicMock()
        swipe_repo = MagicMock()
        swipe_repo.has_liked = AsyncMock(return_value=True)
        ai_service = MagicMock()
        
        service = MatchingService(user_repo, swipe_repo, ai_service)
        
        is_match = await service.check_mutual_match(user_id=1, target_user_id=2)
        
        assert is_match is True
    
    async def test_check_mutual_match_one_sided(self):
        """Test mutual match detection when only one user liked."""
        from bot.services.matching_service import MatchingService
        
        user_repo = MagicMock()
        swipe_repo = MagicMock()
        swipe_repo.has_liked = AsyncMock(side_effect=[True, False])
        ai_service = MagicMock()
        
        service = MatchingService(user_repo, swipe_repo, ai_service)
        
        is_match = await service.check_mutual_match(user_id=1, target_user_id=2)
        
        assert is_match is False


@pytest.mark.asyncio
@pytest.mark.unit
class TestVerificationService:
    """Test VerificationService."""
    
    async def test_verify_level_1_success(self):
        """Test level 1 verification success."""
        from bot.services.verification_service import VerificationService
        
        ai_service = MagicMock()
        ai_service.analyze_image = AsyncMock(return_value={
            "has_face": True,
            "appropriate": True,
        })
        ai_service._call_ollama_vision = AsyncMock(return_value="yes, circle gesture detected")
        
        verification_repo = MagicMock()
        verification_repo.mark_verified = AsyncMock()
        
        service = VerificationService(ai_service, verification_repo)
        
        user = MagicMock()
        user.id = 1
        
        success, message = await service.verify_level_1_circle(user, b"fake_photo_bytes")
        
        assert success is True
        assert "пройдена" in message.lower()
        verification_repo.mark_verified.assert_called_once_with(1, level=1)
    
    async def test_verify_level_1_no_face(self):
        """Test level 1 verification fails when no face detected."""
        from bot.services.verification_service import VerificationService
        
        ai_service = MagicMock()
        ai_service.analyze_image = AsyncMock(return_value={
            "has_face": False,
            "appropriate": True,
        })
        
        verification_repo = MagicMock()
        service = VerificationService(ai_service, verification_repo)
        
        user = MagicMock()
        user.id = 1
        
        success, message = await service.verify_level_1_circle(user, b"fake_photo_bytes")
        
        assert success is False
        assert "не обнаружено" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
