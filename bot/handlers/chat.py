"""Chat handler — message forwarding between matched users, AI hints, compatibility."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.fsm import ChatStates
from bot.keyboards import AISuggestionCallback, ChatCallback

logger = structlog.get_logger(__name__)
router = Router(name="chat")


@router.message(ChatStates.messaging)
async def forward_message(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    fsm_data = await state.get_data()
    match_id = fsm_data.get("active_match_id")
    if match_id is None:
        await message.answer("Нет активного чата. Найди совпадение через поиск.")
        return
    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.message_repository import MessageRepository
        match = await MatchRepository(session).get_by_id(match_id)
        if match is None:
            await message.answer("Чат не найден.")
            return
        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        await MessageRepository(session).create(match_id=match_id, sender_id=user.id, content=message.text or "", message_type="text")
        from bot.keyboards import chat_keyboard
        try:
            await message.bot.send_message(partner_id, f"💬 <b>{user.first_name}:</b> {message.text}", parse_mode="HTML", reply_markup=chat_keyboard(match_id))
        except Exception:
            pass
    except Exception as e:
        logger.error("forward_message_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось отправить сообщение. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "ai_hint"))
async def chat_ai_hint(callback: CallbackQuery, callback_data: ChatCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("⏳ Генерирую подсказки…")
    if user is None:
        return
    match_id = callback_data.match_id
    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.profile_repository import ProfileRepository
        from database.repositories.message_repository import MessageRepository
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager

        match = await MatchRepository(session).get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return
        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        profile_repo = ProfileRepository(session)
        user_profile = await profile_repo.get_by_user_id(user.id)
        partner_profile = await profile_repo.get_by_user_id(partner_id)
        history = await MessageRepository(session).get_recent(match_id, limit=10)
        history_dicts = [{"sender_id": m.sender_id, "content": m.content} for m in history]
        ai = AIService(OpenRouterClient(), CacheManager())
        user_dict = {"id": user.id, "about_me": user_profile.about_me if user_profile else ""}
        partner_dict = {"id": partner_id, "about_me": partner_profile.about_me if partner_profile else ""}
        bold, warm, playful = await ai.generate_chat_suggestions(history_dicts, user_dict, partner_dict)

        def _btn(text, action):
            label = f"{text[:30]}…" if len(text) > 30 else text
            return InlineKeyboardButton(text=label, callback_data=AISuggestionCallback(action=action, match_id=match_id).pack())

        kb = InlineKeyboardMarkup(inline_keyboard=[[_btn(f"😏 {bold}", "bold")], [_btn(f"❤️ {warm}", "warm")], [_btn(f"😄 {playful}", "playful")]])
        await state.set_state(ChatStates.ai_suggestion_pending)
        await state.update_data(ai_suggestions={"bold": bold, "warm": warm, "playful": playful}, active_match_id=match_id)
        await callback.message.answer("💡 Выбери вариант ответа:", reply_markup=kb)
    except Exception as e:
        logger.error("ai_hint_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось сгенерировать подсказки. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "compatibility"))
async def chat_compatibility(callback: CallbackQuery, callback_data: ChatCallback, user=None, session=None) -> None:
    await callback.answer("⏳ Считаю совместимость…")
    if user is None:
        return
    match_id = callback_data.match_id
    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.profile_repository import ProfileRepository
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager

        match = await MatchRepository(session).get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return
        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        profile_repo = ProfileRepository(session)
        up = await profile_repo.get_by_user_id(user.id)
        pp = await profile_repo.get_by_user_id(partner_id)
        ai = AIService(OpenRouterClient(), CacheManager())
        result = await ai.calculate_compatibility(
            {"id": user.id, "about_me": up.about_me if up else "", "mbti_type": up.mbti_type if up else None, "relationship_goals": up.relationship_goals if up else None},
            {"id": partner_id, "about_me": pp.about_me if pp else "", "mbti_type": pp.mbti_type if pp else None, "relationship_goals": pp.relationship_goals if pp else None},
        )
        score = result.get("score", 0)
        explanation = result.get("explanation", "")
        factors = "\n".join(f"• {f}" for f in result.get("key_factors", []))
        await callback.message.answer(
            f"🔮 <b>Совместимость: {score}%</b>\n\n{explanation}" + (f"\n\n<b>Ключевые факторы:</b>\n{factors}" if factors else ""),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("compatibility_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось рассчитать совместимость. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "gift"))
async def chat_gift(callback: CallbackQuery, callback_data: ChatCallback, user=None, session=None) -> None:
    await callback.answer()
    await callback.message.answer("🎁 Функция подарков скоро будет доступна!")


@router.callback_query(AISuggestionCallback.filter())
async def ai_suggestion_send(callback: CallbackQuery, callback_data: AISuggestionCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    fsm_data = await state.get_data()
    suggestions = fsm_data.get("ai_suggestions", {})
    match_id = callback_data.match_id
    text = suggestions.get(callback_data.action, "")
    if not text:
        await callback.message.answer("Вариант не найден.")
        return
    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.message_repository import MessageRepository
        match = await MatchRepository(session).get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return
        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        await MessageRepository(session).create(match_id=match_id, sender_id=user.id, content=text, message_type="text")
        from bot.keyboards import chat_keyboard
        try:
            await callback.bot.send_message(partner_id, f"💬 <b>{user.first_name}:</b> {text}", parse_mode="HTML", reply_markup=chat_keyboard(match_id))
        except Exception:
            pass
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Отправлено: «{text}»")
        await state.set_state(ChatStates.messaging)
    except Exception as e:
        logger.error("ai_suggestion_send_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось отправить сообщение. Попробуй позже.")
