"""Swipe handler — candidate browsing, like/pass/super_like/write, matches."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.fsm import SwipeStates
from bot.keyboards import SwipeCallback, swipe_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="swipe")


def _expand_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="swipe:expand_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="swipe:expand_no"),
        ]
    ])


async def _build_matching(session):
    from database.repositories.match_repository import MatchRepository
    from database.repositories.swipe_repository import SwipeRepository
    from database.repositories.user_repository import UserRepository
    from database.repositories.profile_repository import ProfileRepository
    from bot.services.ai_service import AIService
    from bot.services.matching_service import MatchingService
    from bot.groq_client import GroqClient
    from bot.utils.cache_manager import CacheManager
    return MatchingService(
        UserRepository(session), ProfileRepository(session),
        SwipeRepository(session), MatchRepository(session),
        AIService(GroqClient(), CacheManager()),
    )


async def _send_candidate(message, state, candidate, session):
    from database.repositories.profile_repository import ProfileRepository
    from sqlalchemy import select
    from database.models.profile import Profile, ProfilePhoto

    profile_repo = ProfileRepository(session)
    cand_profile = await profile_repo.get_by_user_id(candidate.id)

    text = (
        f"👤 <b>{candidate.first_name}</b>"
        + (f", {cand_profile.age} лет" if cand_profile and cand_profile.age else "")
        + (f"\n📍 {cand_profile.city}" if cand_profile and cand_profile.city else "")
        + (f"\n💬 {cand_profile.about_me}" if cand_profile and cand_profile.about_me else "")
    )

    kb = swipe_keyboard(candidate.id)
    await state.set_state(SwipeStates.viewing)

    # Try to send with photo
    if cand_profile:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select as sa_select
        try:
            result = await session.execute(
                sa_select(ProfilePhoto).where(ProfilePhoto.profile_id == cand_profile.id).order_by(ProfilePhoto.position).limit(1)
            )
            photo = result.scalar_one_or_none()
            if photo:
                await message.answer_photo(photo.file_id, caption=text, parse_mode="HTML", reply_markup=kb)
                return
        except Exception:
            pass

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


async def _show_next_candidate(message, state, user, session):
    fsm_data = await state.get_data()
    expand = fsm_data.get("expand_search", False)
    try:
        matching = await _build_matching(session)

        if expand:
            result = await matching.get_next_candidate_expanded(user)
        else:
            result = await matching.get_next_candidate(user)

        if result is None:
            if not expand:
                # Local candidates exhausted - ask user
                from database.repositories.profile_repository import ProfileRepository
                profile = await ProfileRepository(session).get_by_user_id(user.id)
                city = profile.city if profile and profile.city else "твоего города"
                await message.answer(
                    f"😔 Анкеты из <b>{city}</b> закончились.\n\nПоказать анкеты из других городов?",
                    parse_mode="HTML",
                    reply_markup=_expand_keyboard(),
                )
            else:
                await message.answer("😔 Пока нет новых анкет. Загляни позже!")
            return

        candidate, score, explanation = result
        await _send_candidate(message, state, candidate, session)
    except Exception as e:
        logger.error("show_candidate_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить анкеты. Попробуй позже.")


@router.message(F.text == "❤️ Поиск")
async def swipe_start(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await _show_next_candidate(message, state, user, session)


@router.callback_query(F.data == "swipe:expand_yes")
async def swipe_expand_yes(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.update_data(expand_search=True)
    await callback.message.edit_reply_markup(reply_markup=None)
    await _show_next_candidate(callback.message, state, user, session)


@router.callback_query(F.data == "swipe:expand_no")
async def swipe_expand_no(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("⏳ Хорошо! Как только появятся новые анкеты из твоего города — сразу покажем. Загляни позже!")


@router.callback_query(SwipeCallback.filter(F.action == "like"))
async def swipe_like(callback: CallbackQuery, callback_data: SwipeCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("❤️")
    if user is None:
        return
    target_id = callback_data.user_id
    try:
        from database.repositories.swipe_repository import SwipeRepository
        from database.repositories.match_repository import MatchRepository
        from database.repositories.user_repository import UserRepository
        from database.repositories.profile_repository import ProfileRepository
        from bot.services.ai_service import AIService
        from bot.services.matching_service import MatchingService
        from bot.groq_client import GroqClient
        from bot.utils.cache_manager import CacheManager

        swipe_repo = SwipeRepository(session)
        await swipe_repo.create_swipe(user.id, target_id, "like")

        matching = MatchingService(
            UserRepository(session), ProfileRepository(session),
            swipe_repo, MatchRepository(session),
            AIService(GroqClient(), CacheManager()),
        )
        match = await matching.check_and_create_match(user.id, target_id)
        if match:
            await callback.message.answer("🎉 <b>Взаимная симпатия!</b>\nТеперь вы можете общаться.", parse_mode="HTML")
            try:
                await callback.bot.send_message(target_id, f"🎉 <b>Взаимная симпатия!</b>\n{user.first_name} тоже лайкнул(а) тебя!", parse_mode="HTML")
            except Exception:
                pass
        else:
            await callback.message.edit_reply_markup(reply_markup=None)
        await _show_next_candidate(callback.message, state, user, session)
    except Exception as e:
        logger.error("swipe_like_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")


@router.callback_query(SwipeCallback.filter(F.action == "pass"))
async def swipe_pass(callback: CallbackQuery, callback_data: SwipeCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("❌")
    if user is None:
        return
    try:
        from database.repositories.swipe_repository import SwipeRepository
        await SwipeRepository(session).create_swipe(user.id, callback_data.user_id, "pass")
        await callback.message.edit_reply_markup(reply_markup=None)
        await _show_next_candidate(callback.message, state, user, session)
    except Exception as e:
        logger.error("swipe_pass_error", user_id=user.id, error=str(e))


@router.callback_query(SwipeCallback.filter(F.action == "super_like"))
async def swipe_super_like(callback: CallbackQuery, callback_data: SwipeCallback, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from bot.config import settings as cfg
        from database.repositories.user_repository import UserRepository
        from database.repositories.swipe_repository import SwipeRepository

        if user.crystals < cfg.superswipe_cost:
            await callback.answer(f"Недостаточно кристаллов! Нужно {cfg.superswipe_cost} 💠", show_alert=True)
            return

        await UserRepository(session).spend_crystals(user.id, cfg.superswipe_cost)
        await SwipeRepository(session).create_swipe(user.id, callback_data.user_id, "super_like")
        await callback.answer("⭐ SuperSwipe отправлен!")
        try:
            await callback.bot.send_message(callback_data.user_id, f"⭐ <b>{user.first_name}</b> отправил(а) тебе SuperSwipe!", parse_mode="HTML")
        except Exception:
            pass
        await callback.message.edit_reply_markup(reply_markup=None)
        await _show_next_candidate(callback.message, state, user, session)
    except Exception as e:
        logger.error("super_like_error", user_id=user.id, error=str(e))


@router.callback_query(SwipeCallback.filter(F.action == "write"))
async def swipe_write(callback: CallbackQuery, callback_data: SwipeCallback, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    try:
        from database.repositories.match_repository import MatchRepository
        match = await MatchRepository(session).get_match(user.id, callback_data.user_id)
        if match is None:
            await callback.message.answer("💬 Чтобы написать напрямую, нужна взаимная симпатия.")
            return
        from bot.keyboards import chat_keyboard
        await callback.message.answer("💬 Напиши своё сообщение:", reply_markup=chat_keyboard(match.id))
    except Exception as e:
        logger.error("swipe_write_error", user_id=user.id, error=str(e))


@router.message(F.text == "🔍 Глубокий поиск")
async def toggle_deep_search(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    fsm_data = await state.get_data()
    deep = not fsm_data.get("deep_search", False)
    await state.update_data(deep_search=deep)
    status = "включён 🔍" if deep else "выключен"
    await message.answer(f"Режим глубокого поиска {status}.")
    logger.info("deep_search_toggled", user_id=user.id, enabled=deep)



