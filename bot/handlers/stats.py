"""Stats handler — show user statistics."""
import structlog
from aiogram import F, Router
from aiogram.types import Message

logger = structlog.get_logger(__name__)
router = Router(name="stats")


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, user=None, session=None) -> None:
        
    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.message_repository import MessageRepository
        from database.repositories.profile_repository import ProfileRepository
        from database.repositories.referral_repository import ReferralRepository

        match_repo = MatchRepository(session)
        msg_repo = MessageRepository(session)
        profile_repo = ProfileRepository(session)
        ref_repo = ReferralRepository(session)

        matches_count = await match_repo.count_user_matches(user.id)
        messages_count = await msg_repo.count_user_messages(user.id)
        profile = await profile_repo.get_by_user_id(user.id)
        profile_views = profile.view_count if profile else 0
        referrals_count = await ref_repo.count_referrals_this_month(user.id)

        premium_badge = "💎 Premium" if user.is_premium else "🆓 Бесплатный"

        await message.answer(
            f"📊 <b>Твоя статистика</b>\n\n"
            f"👤 Статус: {premium_badge}\n"
            f"💠 Кристаллов: {user.crystals}\n\n"
            f"❤️ Совпадений: {matches_count}\n"
            f"💬 Сообщений отправлено: {messages_count}\n"
            f"👁 Просмотров профиля: {profile_views}\n"
            f"👥 Рефералов (этот месяц): {referrals_count}",
            parse_mode="HTML",
        )
        logger.info("stats_shown", user_id=user.id)
    except Exception as e:
        logger.error("show_stats_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить статистику. Попробуй позже.")



