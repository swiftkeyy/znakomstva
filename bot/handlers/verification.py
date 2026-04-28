"""Verification handler — sends to moderator queue instead of AI."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.fsm import VerificationStates
from bot.keyboards import VerificationCallback, verification_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="verification")


@router.callback_query(VerificationCallback.filter(F.level == 1))
async def verify_level_1_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_1_waiting)
    await state.update_data(verif_level=1)
    await callback.message.answer(
        "⭕ <b>Верификация уровня 1</b>\n\n"
        "Сделай фото, на котором ты показываешь жест круга пальцами.\n"
        "Лицо должно быть хорошо видно.\n\n"
        "Фото проверит модератор вручную.",
        parse_mode="HTML",
    )


@router.callback_query(VerificationCallback.filter(F.level == 2))
async def verify_level_2_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_2_waiting)
    await state.update_data(verif_level=2)
    await callback.message.answer(
        "🎥 <b>Верификация уровня 2</b>\n\n"
        "Отправь короткое видео-селфи (до 30 сек).\n"
        "Видео проверит модератор вручную.",
        parse_mode="HTML",
    )


@router.callback_query(VerificationCallback.filter(F.level == 3))
async def verify_level_3_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_3_waiting)
    await state.update_data(verif_level=3)
    await callback.message.answer(
        "🤖 <b>Верификация уровня 3</b>\n\n"
        "Отправь чёткое фото своего лица.\n"
        "Фото проверит модератор вручную.",
        parse_mode="HTML",
    )


async def _submit_to_queue(message: Message, state: FSMContext, user, session, file_id: str, media_type: str) -> None:
    fsm_data = await state.get_data()
    level = fsm_data.get("verif_level", 1)
    await state.clear()

    try:
        from database.repositories.admin_repository import AdminRepository
        item = await AdminRepository(session).add_to_queue(user.id, level, file_id, media_type)
        await session.commit()

        # Notify all moderators and superadmins
        from bot.config import settings
        from database.repositories.admin_repository import AdminRepository as AR
        from sqlalchemy import select
        from database.models.admin import AdminRole

        result = await session.execute(select(AdminRole).where(AdminRole.role.in_(["superadmin", "moderator"])))
        mods = result.scalars().all()
        for mod in mods:
            try:
                await message.bot.send_message(
                    mod.telegram_id,
                    f"🔔 Новая верификация в очереди!\nИспользуй /admin → Верификации",
                )
            except Exception:
                pass
        # Also notify superadmins from config
        for admin_id in settings.get_admin_ids():
            try:
                await message.bot.send_message(admin_id, f"🔔 Новая верификация в очереди! /admin → Верификации")
            except Exception:
                pass

        await message.answer(
            "⏳ <b>Заявка на верификацию отправлена!</b>\n\n"
            "Модератор проверит её в ближайшее время и уведомит тебя о результате.",
            parse_mode="HTML",
            reply_markup=verification_keyboard(),
        )
    except Exception as e:
        logger.error("submit_verification_error", user_id=user.id, error=str(e))
        await message.answer("Ошибка при отправке заявки. Попробуй позже.")


@router.message(VerificationStates.level_1_waiting, F.photo)
async def verify_level_1_photo(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await _submit_to_queue(message, state, user, session, message.photo[-1].file_id, "photo")


@router.message(VerificationStates.level_2_waiting, F.video)
async def verify_level_2_video(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await _submit_to_queue(message, state, user, session, message.video.file_id, "video")


@router.message(VerificationStates.level_3_waiting, F.photo)
async def verify_level_3_photo(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await _submit_to_queue(message, state, user, session, message.photo[-1].file_id, "photo")

