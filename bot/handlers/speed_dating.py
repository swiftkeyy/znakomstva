"""Speed dating handler — session join, match decisions."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards import SpeedDatingCallback

logger = structlog.get_logger(__name__)
router = Router(name="speed_dating")


@router.message(F.text == "⚡ Быстрые знакомства")
async def speed_dating_menu(message: Message, data: dict) -> None:
    user = data["user"]
    session = data["session"]

    try:
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        sd_repo = SpeedDatingRepository(session)
        active_sessions = await sd_repo.get_active_sessions()

        if not active_sessions:
            await message.answer(
                "⚡ <b>Быстрые знакомства</b>\n\n"
                "Сейчас нет активных сессий. Загляни позже!",
                parse_mode="HTML",
            )
            return

        buttons = []
        for s in active_sessions[:5]:
            buttons.append([
                InlineKeyboardButton(
                    text=f"⚡ Сессия #{s.id}",
                    callback_data=SpeedDatingCallback(action="join", session_id=s.id).pack(),
                )
            ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚡ <b>Быстрые знакомства</b>\n\nВыбери сессию:",
            parse_mode="HTML",
            reply_markup=kb,
        )
        logger.info("speed_dating_menu_shown", user_id=user.id)
    except Exception as e:
        logger.error("speed_dating_menu_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить сессии. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "join"))
async def speed_dating_join(
    callback: CallbackQuery,
    callback_data: SpeedDatingCallback,
    state: FSMContext,
    data: dict,
) -> None:
    await callback.answer()
    user = data["user"]
    session = data["session"]
    session_id = callback_data.session_id

    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository

        sd_service = SpeedDatingService(
            SpeedDatingRepository(session),
            UserRepository(session),
        )
        success, msg = await sd_service.register_user(session_id, user)

        if success:
            await state.update_data(active_sd_session=session_id)
            await callback.message.answer(
                f"✅ {msg}\n\nОжидай начала сессии. Тебя уведомят!",
            )
        else:
            await callback.message.answer(f"❌ {msg}")

        logger.info("speed_dating_join", user_id=user.id, session_id=session_id, success=success)
    except Exception as e:
        logger.error("speed_dating_join_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка при регистрации. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "match_yes"))
async def speed_dating_match_yes(
    callback: CallbackQuery,
    callback_data: SpeedDatingCallback,
    state: FSMContext,
    data: dict,
) -> None:
    await callback.answer("❤️")
    user = data["user"]
    session = data["session"]
    fsm_data = await state.get_data()
    pair_id = fsm_data.get("current_sd_pair_id")

    if pair_id is None:
        await callback.message.answer("Нет активной пары.")
        return

    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository

        sd_service = SpeedDatingService(
            SpeedDatingRepository(session),
            UserRepository(session),
        )
        mutual = await sd_service.record_decision(pair_id, user.id, wants_match=True)

        if mutual is True:
            await callback.message.answer(
                "🎉 <b>Взаимная симпатия!</b>\nТеперь вы можете общаться.",
                parse_mode="HTML",
            )
        elif mutual is False:
            await callback.message.answer("Увы, взаимности нет. Ждём следующей пары!")
        else:
            await callback.message.answer("✅ Твой выбор записан. Ждём решения партнёра…")

        logger.info("sd_match_yes", user_id=user.id, pair_id=pair_id, mutual=mutual)
    except Exception as e:
        logger.error("sd_match_yes_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")


@router.callback_query(SpeedDatingCallback.filter(F.action == "match_no"))
async def speed_dating_match_no(
    callback: CallbackQuery,
    callback_data: SpeedDatingCallback,
    state: FSMContext,
    data: dict,
) -> None:
    await callback.answer("❌")
    user = data["user"]
    session = data["session"]
    fsm_data = await state.get_data()
    pair_id = fsm_data.get("current_sd_pair_id")

    if pair_id is None:
        await callback.message.answer("Нет активной пары.")
        return

    try:
        from bot.services.speed_dating_service import SpeedDatingService
        from database.repositories.speed_dating_repository import SpeedDatingRepository
        from database.repositories.user_repository import UserRepository

        sd_service = SpeedDatingService(
            SpeedDatingRepository(session),
            UserRepository(session),
        )
        await sd_service.record_decision(pair_id, user.id, wants_match=False)
        await callback.message.answer("Ждём следующей пары!")
        logger.info("sd_match_no", user_id=user.id, pair_id=pair_id)
    except Exception as e:
        logger.error("sd_match_no_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")
