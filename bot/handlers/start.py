"""Start handler — /start command, referral processing, main menu."""
import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.fsm import RegistrationStates
from bot.keyboards import main_menu_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, data: dict) -> None:
    user = data["user"]

    # Handle referral payload: /start ref_12345
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
            if referrer_id != user.id:
                await state.update_data(referral_from=referrer_id)
                logger.info("referral_detected", user_id=user.id, referrer_id=referrer_id)
        except ValueError:
            pass

    # If user has no profile — start registration
    if not user.is_registered:
        await state.set_state(RegistrationStates.age)
        await message.answer(
            "👋 Добро пожаловать в <b>Моя половинка</b>!\n\n"
            "Давай создадим твой профиль. Сколько тебе лет?",
            parse_mode="HTML",
        )
        logger.info("registration_started", user_id=user.id)
        return

    await state.clear()
    await message.answer(
        f"👋 С возвращением, {user.first_name}!",
        reply_markup=main_menu_keyboard(is_premium=user.is_premium),
    )
    logger.info("user_returned", user_id=user.id)
