"""Pytest configuration and shared fixtures for all tests."""
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from database.models.base import Base
from database.models.user import User
from database.models.profile import Profile
from bot.config import Settings


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database engine
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


# Test database session
@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


# Mock Redis client
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=3600)
    redis.aclose = AsyncMock()
    return redis


# Mock bot instance
@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot instance."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_media_group = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot


# Mock Ollama client
@pytest.fixture
def mock_ollama():
    """Create a mock Ollama client."""
    ollama = MagicMock()
    ollama.generate = AsyncMock(return_value={
        "response": "Test AI response",
        "model": "qwen3:32b",
    })
    ollama.analyze_image = AsyncMock(return_value={
        "has_face": True,
        "appropriate": True,
        "concerns": [],
    })
    return ollama


# Test settings
@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        bot_token="test_token",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        ollama_url="http://localhost:11434",
        log_level="DEBUG",
        sentry_dsn=None,
    )


# Sample user fixture
@pytest_asyncio.fixture
async def sample_user(test_session: AsyncSession) -> User:
    """Create a sample user for testing."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        is_active=True,
        is_premium=False,
        crystal_balance=100,
        timezone="Europe/Moscow",
        daily_reports_enabled=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


# Sample premium user fixture
@pytest_asyncio.fixture
async def sample_premium_user(test_session: AsyncSession) -> User:
    """Create a sample premium user for testing."""
    from datetime import datetime, timedelta, timezone
    
    user = User(
        telegram_id=987654321,
        username="premiumuser",
        first_name="Premium",
        is_active=True,
        is_premium=True,
        premium_expires_at=datetime.now(tz=timezone.utc) + timedelta(days=30),
        crystal_balance=500,
        timezone="Europe/Moscow",
        daily_reports_enabled=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


# Sample profile fixture
@pytest_asyncio.fixture
async def sample_profile(test_session: AsyncSession, sample_user: User) -> Profile:
    """Create a sample profile for testing."""
    profile = Profile(
        user_id=sample_user.id,
        age=25,
        city="Moscow",
        height=175,
        relationship_goals="serious",
        mbti_type="INTJ",
        attachment_style="secure",
        about_me="Test bio",
        latitude=55.7558,
        longitude=37.6173,
        verification_level=0,
    )
    test_session.add(profile)
    await test_session.commit()
    await test_session.refresh(profile)
    return profile


# Mock FSM context
@pytest.fixture
def mock_fsm_context():
    """Create a mock FSM context."""
    context = MagicMock()
    context.get_state = AsyncMock(return_value=None)
    context.set_state = AsyncMock()
    context.clear = AsyncMock()
    context.get_data = AsyncMock(return_value={})
    context.set_data = AsyncMock()
    context.update_data = AsyncMock()
    return context


# Mock message
@pytest.fixture
def mock_message():
    """Create a mock Telegram message."""
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.chat = MagicMock()
    message.chat.id = 123456789
    message.text = "Test message"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.edit_text = AsyncMock()
    return message


# Mock callback query
@pytest.fixture
def mock_callback_query():
    """Create a mock Telegram callback query."""
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 123456789
    callback.from_user.username = "testuser"
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123456789
    callback.data = "test_callback"
    callback.answer = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    return callback


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "property: mark test as property-based test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
