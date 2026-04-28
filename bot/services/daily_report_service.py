"""Daily report service — per-user 24h stats and scheduled delivery."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import structlog

from database.repositories.match_repository import MatchRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.story_repository import StoryRepository
from database.repositories.swipe_repository import SwipeRepository
from database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class DailyReportService:
    def __init__(
        self,
        user_repo: UserRepository,
        swipe_repo: SwipeRepository,
        match_repo: MatchRepository,
        message_repo: MessageRepository,
        story_repo: StoryRepository,
    ) -> None:
        self.user_repo = user_repo
        self.swipe_repo = swipe_repo
        self.match_repo = match_repo
        self.message_repo = message_repo
        self.story_repo = story_repo

    async def generate_report(self, user_id: int) -> Dict[str, Any]:
        """Collect stats for the last 24 hours for a single user."""
        try:
            now = datetime.now(tz=timezone.utc)
            since = now - timedelta(hours=24)

            # Story views — sum view_count of active stories
            active_stories = await self.story_repo.get_active_stories(user_id)
            story_views = sum(s.view_count for s in active_stories)

            # Likes received — swipes where target_user_id == user_id and action in like/super_like
            # We reuse count_swipes_today as a proxy for sent swipes; for received we query directly
            likes_sent = await self.swipe_repo.count_swipes_today(user_id)

            # Matches
            matches = await self.match_repo.get_user_matches(user_id)
            new_matches = [
                m for m in matches
                if m.created_at and (
                    m.created_at.replace(tzinfo=timezone.utc)
                    if m.created_at.tzinfo is None
                    else m.created_at
                ) >= since
            ]

            # Messages sent today
            messages_sent = await self.message_repo.count_messages_today(user_id)

            report = {
                "user_id": user_id,
                "period": "24h",
                "generated_at": now.isoformat(),
                "story_views": story_views,
                "likes_sent": likes_sent,
                "new_matches": len(new_matches),
                "messages_sent": messages_sent,
            }
            logger.debug("report_generated", user_id=user_id, report=report)
            return report
        except Exception as e:
            logger.error("generate_report_error", user_id=user_id, error=str(e))
            return {
                "user_id": user_id,
                "period": "24h",
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "story_views": 0,
                "likes_sent": 0,
                "new_matches": 0,
                "messages_sent": 0,
            }

    async def send_reports(self, bot: Any) -> int:
        """Send daily reports to all active users who have reports enabled. Returns count of reports sent."""
        sent = 0
        try:
            users = await self.user_repo.get_all_active_users(
                exclude_user_id=0, limit=10000
            )
            for user in users:
                # Skip if user disabled daily reports
                if not user.daily_reports_enabled:
                    continue
                    
                try:
                    report = await self.generate_report(user.id)
                    text = self._format_report(report)
                    await bot.send_message(chat_id=user.telegram_id, text=text)
                    sent += 1
                except Exception as e:
                    logger.warning(
                        "send_report_failed",
                        user_id=user.id,
                        telegram_id=user.telegram_id,
                        error=str(e),
                    )
            logger.info("daily_reports_sent", count=sent)
        except Exception as e:
            logger.error("send_reports_error", error=str(e))
        return sent

    @staticmethod
    def _format_report(report: Dict[str, Any]) -> str:
        return (
            "📊 Ваша статистика за последние 24 часа:\n\n"
            f"👁 Просмотры историй: {report['story_views']}\n"
            f"❤️ Лайков отправлено: {report['likes_sent']}\n"
            f"🎉 Новых совпадений: {report['new_matches']}\n"
            f"💬 Сообщений отправлено: {report['messages_sent']}"
        )


def setup_scheduler(scheduler: Any, report_service: "DailyReportService", bot: Any) -> None:
    """Register the daily report job with APScheduler at 9:00 AM UTC."""
    scheduler.add_job(
        report_service.send_reports,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )
    logger.info("daily_report_scheduler_registered")
