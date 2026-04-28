"""Scheduled tasks for the Моя половинка bot."""
from datetime import datetime, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = structlog.get_logger(__name__)


def setup_all_jobs(scheduler: AsyncIOScheduler, bot, session_factory) -> None:
    """Register all scheduled jobs."""

    # Daily reports - check every hour for users whose local time is 9:00 AM
    scheduler.add_job(
        _send_daily_reports,
        trigger="cron",
        minute=0,  # Run at the start of every hour
        args=[bot, session_factory],
        id="daily_reports",
        replace_existing=True,
    )

    # Story cleanup every hour
    scheduler.add_job(
        _cleanup_expired_stories,
        trigger="interval",
        hours=1,
        args=[session_factory],
        id="story_cleanup",
        replace_existing=True,
    )

    # Boost expiry check every 30 minutes
    scheduler.add_job(
        _check_boost_expiry,
        trigger="interval",
        minutes=30,
        args=[session_factory],
        id="boost_expiry",
        replace_existing=True,
    )

    # Premium expiry notifications daily at 10:00 AM
    scheduler.add_job(
        _notify_premium_expiry,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot, session_factory],
        id="premium_expiry_notify",
        replace_existing=True,
    )

    # Speed dating sessions at 20:00 UTC (evenings)
    scheduler.add_job(
        _create_speed_dating_session,
        trigger="cron",
        hour=20,
        minute=0,
        args=[session_factory],
        id="speed_dating_session",
        replace_existing=True,
    )

    logger.info("all_scheduled_jobs_registered")


async def _send_daily_reports(bot, session_factory) -> None:
    """Send daily reports to users for whom it's 9:00 AM in their timezone."""
    try:
        from zoneinfo import ZoneInfo
        
        async with session_factory() as session:
            from bot.services.daily_report_service import DailyReportService
            from database.repositories.match_repository import MatchRepository
            from database.repositories.message_repository import MessageRepository
            from database.repositories.story_repository import StoryRepository
            from database.repositories.swipe_repository import SwipeRepository
            from database.repositories.user_repository import UserRepository

            user_repo = UserRepository(session)
            service = DailyReportService(
                user_repo,
                SwipeRepository(session),
                MatchRepository(session),
                MessageRepository(session),
                StoryRepository(session),
            )
            
            # Get all active users with daily reports enabled
            users = await user_repo.get_all_active_users(exclude_user_id=0, limit=10000)
            sent = 0
            
            for user in users:
                if not user.daily_reports_enabled:
                    continue
                
                try:
                    # Get current time in user's timezone
                    user_tz = ZoneInfo(user.timezone)
                    now_user_tz = datetime.now(tz=user_tz)
                    
                    # Check if it's 9:00 AM (hour 9) in user's timezone
                    if now_user_tz.hour == 9:
                        report = await service.generate_report(user.id)
                        text = service._format_report(report)
                        await bot.send_message(chat_id=user.telegram_id, text=text)
                        sent += 1
                except Exception as e:
                    logger.warning(
                        "send_report_failed",
                        user_id=user.id,
                        timezone=user.timezone,
                        error=str(e),
                    )
            
            if sent > 0:
                logger.info("daily_reports_sent", count=sent)
    except Exception as e:
        logger.error("daily_reports_error", error=str(e))


async def _cleanup_expired_stories(session_factory) -> None:
    try:
        async with session_factory() as session:
            from database.repositories.story_repository import StoryRepository
            repo = StoryRepository(session)
            count = await repo.delete_expired_stories()
            await session.commit()
            logger.info("stories_cleaned", count=count)
    except Exception as e:
        logger.error("story_cleanup_error", error=str(e))


async def _check_boost_expiry(session_factory) -> None:
    try:
        async with session_factory() as session:
            from sqlalchemy import update
            from database.models.profile import Profile
            now = datetime.now(tz=timezone.utc)
            await session.execute(
                update(Profile)
                .where(Profile.boost_expires_at <= now)
                .values(boost_expires_at=None)
            )
            await session.commit()
            logger.debug("boost_expiry_checked")
    except Exception as e:
        logger.error("boost_expiry_error", error=str(e))


async def _notify_premium_expiry(bot, session_factory) -> None:
    try:
        from datetime import timedelta
        async with session_factory() as session:
            from sqlalchemy import select
            from database.models.user import User
            now = datetime.now(tz=timezone.utc)
            in_3_days = now + timedelta(days=3)

            result = await session.execute(
                select(User).where(
                    User.is_premium.is_(True),
                    User.premium_expires_at <= in_3_days,
                    User.premium_expires_at > now,
                )
            )
            users = result.scalars().all()

            for user in users:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "⚠️ Твоя Premium подписка истекает через 3 дня!\n"
                        "Продли её, чтобы не потерять доступ к функциям.",
                    )
                except Exception:
                    pass

            logger.info("premium_expiry_notified", count=len(users))
    except Exception as e:
        logger.error("premium_expiry_notify_error", error=str(e))


async def _create_speed_dating_session(session_factory) -> None:
    try:
        from datetime import timedelta
        async with session_factory() as session:
            from database.repositories.speed_dating_repository import SpeedDatingRepository
            repo = SpeedDatingRepository(session)
            scheduled_time = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
            session_obj = await repo.create_session(scheduled_time, duration_minutes=60)
            await session.commit()
            logger.info("speed_dating_session_created", session_id=session_obj.id)
    except Exception as e:
        logger.error("create_speed_dating_error", error=str(e))
