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
    """Forward a text message to the matched partner."""
            fsm_data = await state.get_data()
    match_id = fsm_data.get("active_match_id")

    if match_id is None:
        await message.answer("Нет активного чата. Найди совпадение через поиск.")
        return

    try:
        from database.repositories.match_repository import MatchRepository
        match_repo = MatchRepository(session)
        match = await match_repo.get_by_id(match_id)

        if match is None:
            await message.answer("Чат не найден.")
            return

        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id

        from database.repositories.message_repository import MessageRepository
        msg_repo = MessageRepository(session)
        await msg_repo.create(
            match_id=match_id,
            sender_id=user.id,
            content=message.text or "",
            message_type="text",
        )

        from bot.keyboards import chat_keyboard
        try:
            await message.bot.send_message(
                partner_id,
                f"💬 <b>{user.first_name}:</b> {message.text}",
                parse_mode="HTML",
                reply_markup=chat_keyboard(match_id),
            )
        except Exception:
            pass

        logger.info("message_forwarded", user_id=user.id, partner_id=partner_id, match_id=match_id)
    except Exception as e:
        logger.error("forward_message_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось отправить сообщение. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "ai_hint"))
async def chat_ai_hint(callback: CallbackQuery, callback_data: ChatCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("⏳ Генерирую подсказки…")
            match_id = callback_data.match_id

    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.profile_repository import ProfileRepository
        from database.repositories.message_repository import MessageRepository
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager

        match_repo = MatchRepository(session)
        match = await match_repo.get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return

        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        profile_repo = ProfileRepository(session)
        user_profile = await profile_repo.get_by_user_id(user.id)
        partner_profile = await profile_repo.get_by_user_id(partner_id)

        msg_repo = MessageRepository(session)
        history = await msg_repo.get_recent(match_id, limit=10)
        history_dicts = [{"sender_id": m.sender_id, "content": m.content} for m in history]

        openrouter = OpenRouterClient()
        cache = CacheManager()
        ai = AIService(openrouter, cache)

        user_dict = {"id": user.id, "about_me": user_profile.about_me if user_profile else ""}
        partner_dict = {"id": partner_id, "about_me": partner_profile.about_me if partner_profile else ""}

        bold, warm, playful = await ai.generate_chat_suggestions(history_dicts, user_dict, partner_dict)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"😏 {bold[:30]}…" if len(bold) > 30 else f"😏 {bold}",
                callback_data=AISuggestionCallback(action="bold", match_id=match_id).pack(),
            )],
            [InlineKeyboardButton(
                text=f"❤️ {warm[:30]}…" if len(warm) > 30 else f"❤️ {warm}",
                callback_data=AISuggestionCallback(action="warm", match_id=match_id).pack(),
            )],
            [InlineKeyboardButton(
                text=f"😄 {playful[:30]}…" if len(playful) > 30 else f"😄 {playful}",
                callback_data=AISuggestionCallback(action="playful", match_id=match_id).pack(),
            )],
        ])

        await state.set_state(ChatStates.ai_suggestion_pending)
        await state.update_data(
            ai_suggestions={"bold": bold, "warm": warm, "playful": playful},
            active_match_id=match_id,
        )
        await callback.message.answer("💡 Выбери вариант ответа:", reply_markup=kb)
        logger.info("ai_hints_shown", user_id=user.id, match_id=match_id)
    except Exception as e:
        logger.error("ai_hint_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось сгенерировать подсказки. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "compatibility"))
async def chat_compatibility(callback: CallbackQuery, callback_data: ChatCallback, user=None, session=None) -> None:
    await callback.answer("⏳ Считаю совместимость…")
            match_id = callback_data.match_id

    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.profile_repository import ProfileRepository
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager

        match_repo = MatchRepository(session)
        match = await match_repo.get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return

        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        profile_repo = ProfileRepository(session)
        user_profile = await profile_repo.get_by_user_id(user.id)
        partner_profile = await profile_repo.get_by_user_id(partner_id)

        openrouter = OpenRouterClient()
        cache = CacheManager()
        ai = AIService(openrouter, cache)

        user_dict = {
            "id": user.id,
            "about_me": user_profile.about_me if user_profile else "",
            "mbti_type": user_profile.mbti_type if user_profile else None,
            "relationship_goals": user_profile.relationship_goals if user_profile else None,
        }
        partner_dict = {
            "id": partner_id,
            "about_me": partner_profile.about_me if partner_profile else "",
            "mbti_type": partner_profile.mbti_type if partner_profile else None,
            "relationship_goals": partner_profile.relationship_goals if partner_profile else None,
        }

        result = await ai.calculate_compatibility(user_dict, partner_dict)
        score = result.get("score", 0)
        explanation = result.get("explanation", "")
        factors = result.get("key_factors", [])
        factors_str = "\n".join(f"• {f}" for f in factors) if factors else ""

        await callback.message.answer(
            f"🔮 <b>Совместимость: {score}%</b>\n\n"
            f"{explanation}"
            + (f"\n\n<b>Ключевые факторы:</b>\n{factors_str}" if factors_str else ""),
            parse_mode="HTML",
        )
        logger.info("compatibility_shown", user_id=user.id, match_id=match_id, score=score)
    except Exception as e:
        logger.error("compatibility_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось рассчитать совместимость. Попробуй позже.")


@router.callback_query(ChatCallback.filter(F.action == "gift"))
async def chat_gift(callback: CallbackQuery, callback_data: ChatCallback, user=None, session=None) -> None:
    await callback.answer()
    await callback.message.answer(
        "🎁 Функция подарков скоро будет доступна!\n"
        "Следи за обновлениями."
    )


@router.callback_query(AISuggestionCallback.filter())
async def ai_suggestion_send(
    callback: CallbackQuery,
    callback_data: AISuggestionCallback,
    state: FSMContext,
    data: dict,
) -> None:
    await callback.answer()
            fsm_data = await state.get_data()
    suggestions = fsm_data.get("ai_suggestions", {})
    match_id = callback_data.match_id
    action = callback_data.action  # bold, warm, playful

    text = suggestions.get(action, "")
    if not text:
        await callback.message.answer("Вариант не найден.")
        return

    try:
        from database.repositories.match_repository import MatchRepository
        from database.repositories.message_repository import MessageRepository

        match_repo = MatchRepository(session)
        match = await match_repo.get_by_id(match_id)
        if match is None:
            await callback.message.answer("Чат не найден.")
            return

        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id

        msg_repo = MessageRepository(session)
        await msg_repo.create(
            match_id=match_id,
            sender_id=user.id,
            content=text,
            message_type="text",
        )

        from bot.keyboards import chat_keyboard
        try:
            await callback.bot.send_message(
                partner_id,
                f"💬 <b>{user.first_name}:</b> {text}",
                parse_mode="HTML",
                reply_markup=chat_keyboard(match_id),
            )
        except Exception:
            pass

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Отправлено: «{text}»")
        await state.set_state(ChatStates.messaging)
        logger.info("ai_suggestion_sent", user_id=user.id, action=action, match_id=match_id)
    except Exception as e:
        logger.error("ai_suggestion_send_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось отправить сообщение. Попробуй позже.")



