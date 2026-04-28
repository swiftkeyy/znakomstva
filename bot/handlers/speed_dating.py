"""Speed dating handler — session join, match decisions."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards import SpeedDatingCallback

logger = structlog.get_logger(__name__)
router = Router(name="speed_dating")


@router.message(F.text == "⚡ Быстрые знакомства")
async def speed_dating_menu(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        active_sessions = await SpeedDatingRepository(session).get_active_sessions()
        if not active_sessions:
            await message.answer("⚡ <b>Быстрые знакомства</b>\n\nСейчас нет активных сессий. Загляни позже!", parse_mode="HTML")
            return
        buttons = [[InlineKeyboardButton(text=f"⚡ Сессия #{s.id}", callback_data=SpeedDatingCallback(action="join", session_id=s.id).pack())] for s in active_sessions[:5]]
        await message.answer("⚡ <b>Быстрые знакомства</b>\n\nВыбери сессию:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        logger.error("speed_dating_menu_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить сессии. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "join"))
async def speed_dating_join(callback: CallbackQuery, callback_data: SpeedDatingCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    session_id = callback_data.session_id
    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository
        success, msg = await SpeedDatingService(SpeedDatingRepository(session), UserRepository(session)).register_user(session_id, user)
        if success:
            await state.update_data(active_sd_session=session_id)
            await callback.message.answer(f"✅ {msg}\n\nОжидай начала сессии. Тебя уведомят!")
        else:
            await callback.message.answer(f"❌ {msg}")
    except Exception as e:
        logger.error("speed_dating_join_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка при регистрации. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "match_yes"))
async def speed_dating_match_yes(callback: CallbackQuery, callback_data: SpeedDatingCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("❤️")
    if user is None:
        return
    fsm_data = await state.get_data()
    pair_id = fsm_data.get("current_sd_pair_id")
    if pair_id is None:
        await callback.message.answer("Нет активной пары.")
        return
    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository
        mutual = await SpeedDatingService(SpeedDatingRepository(session), UserRepository(session)).record_decision(pair_id, user.id, wants_match=True)
        if mutual is True:
            await callback.message.answer("🎉 <b>Взаимная симпатия!</b>\nТеперь вы можете общаться.", parse_mode="HTML")
        elif mutual is False:
            await callback.message.answer("Увы, взаимности нет. Ждём следующей пары!")
        else:
            await callback.message.answer("✅ Твой выбор записан. Ждём решения партнёра…")
    except Exception as e:
        logger.error("sd_match_yes_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "match_no"))
async def speed_dating_match_no(callback: CallbackQuery, callback_data: SpeedDatingCallback, state: FSMContext, user=None, session=None) -> None:
    await callback.answer("❌")
    if user is None:
        return
    fsm_data = await state.get_data()
    pair_id = fsm_data.get("current_sd_pair_id")
    if pair_id is None:
        await callback.message.answer("Нет активной пары.")
        return
    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository
        await SpeedDatingService(SpeedDatingRepository(session), UserRepository(session)).record_decision(pair_id, user.id, wants_match=False)
        await callback.message.answer("Ждём следующей пары!")
    except Exception as e:
        logger.error("sd_match_no_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")
