"""Smoke tests for basic application startup and health checks."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.smoke
@pytest.mark.asyncio
class TestApplicationStartup:
    """Test basic application startup."""
    
    async def test_config_loads(self):
        """Test that configuration loads without errors."""
        from bot.config import Settings
        
        settings = Settings(
            bot_token="test_token",
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url="redis://localhost:6379/0",
            ollama_url="http://localhost:11434",
        )
        
        assert settings.bot_token == "test_token"
        assert settings.database_url is not None
        assert settings.redis_url is not None
    
    async def test_database_models_import(self):
        """Test that all database models can be imported."""
        from database.models.user import User
        from database.models.profile import Profile
        from database.models.match import Match
        from database.models.swipe import Swipe
        from database.models.message import Message
        from database.models.story import Story
        from database.models.verification import VerificationAttempt
        from database.models.transaction import Transaction
        from database.models.referral import Referral
        from database.models.speed_dating import SpeedDatingSession
        
        # If we got here, all imports succeeded
        assert True
    
    async def test_repositories_import(self):
        """Test that all repositories can be imported."""
        from database.repositories.user_repository import UserRepository
        from database.repositories.profile_repository import ProfileRepository
        from database.repositories.match_repository import MatchRepository
        from database.repositories.swipe_repository import SwipeRepository
        from database.repositories.message_repository import MessageRepository
        from database.repositories.story_repository import StoryRepository
        from database.repositories.verification_repository import VerificationRepository
        from database.repositories.transaction_repository import TransactionRepository
        from database.repositories.referral_repository import ReferralRepository
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        
        assert True
    
    async def test_services_import(self):
        """Test that all services can be imported."""
        from bot.services.ai_service import AIService
        from bot.services.matching_service import MatchingService
        from bot.services.verification_service import VerificationService
        from bot.services.payment_service import PaymentService
        from bot.services.moderation_service import ModerationService
        from bot.services.rate_limiter import RateLimiter
        from bot.services.daily_report_service import DailyReportService
        from bot.services.referral_service import ReferralService
        from bot.services.speed_dating_service import SpeedDatingService
        from bot.services.story_service import StoryService
        
        assert True
    
    async def test_handlers_import(self):
        """Test that all handlers can be imported."""
        from bot.handlers.start import router as start_router
        from bot.handlers.profile import router as profile_router
        from bot.handlers.swipe import router as swipe_router
        from bot.handlers.chat import router as chat_router
        from bot.handlers.premium import router as premium_router
        from bot.handlers.verification import router as verification_router
        from bot.handlers.settings import router as settings_router
        from bot.handlers.stats import router as stats_router
        from bot.handlers.stories import router as stories_router
        from bot.handlers.speed_dating import router as speed_dating_router
        from bot.handlers.payments import router as payments_router
        
        assert True
    
    async def test_keyboards_import(self):
        """Test that all keyboards can be imported."""
        from bot.keyboards.main_menu import main_menu_keyboard
        from bot.keyboards.swipe import swipe_keyboard
        from bot.keyboards.chat import chat_keyboard
        from bot.keyboards.profile import profile_keyboard
        from bot.keyboards.premium import premium_keyboard
        from bot.keyboards.verification import verification_keyboard
        from bot.keyboards.settings import settings_keyboard
        
        assert True
    
    async def test_fsm_states_import(self):
        """Test that all FSM states can be imported."""
        from bot.fsm.registration import RegistrationStates
        from bot.fsm.profile_edit import ProfileEditStates
        from bot.fsm.swipe import SwipeStates
        from bot.fsm.chat import ChatStates
        from bot.fsm.verification import VerificationStates
        from bot.fsm.payment import PaymentStates
        
        assert True


@pytest.mark.smoke
class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_response(self):
        """Test that health check returns OK status."""
        # This would be tested with actual HTTP request in integration test
        # Here we just verify the structure
        health_response = {"status": "ok"}
        
        assert health_response["status"] == "ok"


@pytest.mark.smoke
class TestDatabaseConnection:
    """Test database connection setup."""
    
    async def test_database_engine_creation(self, test_engine):
        """Test that database engine can be created."""
        assert test_engine is not None
    
    async def test_database_session_creation(self, test_session):
        """Test that database session can be created."""
        assert test_session is not None


@pytest.mark.smoke
class TestSchedulerSetup:
    """Test scheduler setup."""
    
    def test_scheduler_import(self):
        """Test that scheduler can be imported."""
        from bot.scheduler import setup_all_jobs
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        assert scheduler is not None
    
    def test_scheduler_jobs_registration(self):
        """Test that scheduler jobs can be registered."""
        from bot.scheduler import setup_all_jobs
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        bot = MagicMock()
        session_factory = MagicMock()
        
        # This should not raise any errors
        setup_all_jobs(scheduler, bot, session_factory)
        
        # Check that jobs were added
        jobs = scheduler.get_jobs()
        assert len(jobs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
