"""Verification handler — levels 1-3 photo/video verification."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.fsm import VerificationStates
from bot.keyboards import VerificationCallback, verification_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="verification")

_BADGE_INFO = {
    1: "⭕ Уровень 1 — Жест круга подтверждён",
    2: "🎥 Уровень 2 — Видео-верификация пройдена",
    3: "🤖 Уровень 3 — AI-распознавание пройдено",
}


@router.callback_query(VerificationCallback.filter(F.level == 1))
async def verify_level_1_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_1_waiting)
    await callback.message.answer("⭕ <b>Верификация уровня 1</b>\n\nСделай фото с жестом круга пальцами.", parse_mode="HTML")


@router.callback_query(VerificationCallback.filter(F.level == 2))
async def verify_level_2_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_2_waiting)
    await callback.message.answer("🎥 <b>Верификация уровня 2</b>\n\nОтправь короткое видео-селфи (до 30 сек).", parse_mode="HTML")


@router.callback_query(VerificationCallback.filter(F.level == 3))
async def verify_level_3_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_3_waiting)
    await callback.message.answer("🤖 <b>Верификация уровня 3</b>\n\nОтправь чёткое фото лица для AI-распознавания.", parse_mode="HTML")


@router.message(VerificationStates.level_1_waiting, F.photo)
async def verify_level_1_photo(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Проверяю фото…")
    try:
        file = await message.bot.get_file(message.photo[-1].file_id)
        image_bytes = (await message.bot.download_file(file.file_path)).read()
        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.groq_client import GroqClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository
        ver_service = VerificationService(VerificationRepository(session), AIService(GroqClient(), CacheManager()))
        passed, msg = await ver_service.verify_level_1(user.id, image_bytes)
        await state.clear()
        prefix = "✅" if passed else "❌"
        await message.answer(f"{prefix} {msg}" + (f"\n\n🏅 {_BADGE_INFO[1]}" if passed else "\n\nПопробуй ещё раз."), reply_markup=verification_keyboard())
    except Exception as e:
        logger.error("verify_level_1_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")


@router.message(VerificationStates.level_2_waiting, F.video)
async def verify_level_2_video(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Проверяю видео…")
    try:
        file = await message.bot.get_file(message.video.file_id)
        video_bytes = (await message.bot.download_file(file.file_path)).read()
        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.groq_client import GroqClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository
        ver_service = VerificationService(VerificationRepository(session), AIService(GroqClient(), CacheManager()))
        passed, msg = await ver_service.verify_level_2(user.id, video_bytes)
        await state.clear()
        prefix = "✅" if passed else "❌"
        await message.answer(f"{prefix} {msg}" + (f"\n\n🏅 {_BADGE_INFO[2]}" if passed else "\n\nПопробуй ещё раз."), reply_markup=verification_keyboard())
    except Exception as e:
        logger.error("verify_level_2_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")


@router.message(VerificationStates.level_3_waiting, F.photo)
async def verify_level_3_photo(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Сравниваю лица через AI…")
    try:
        file = await message.bot.get_file(message.photo[-1].file_id)
        verification_bytes = (await message.bot.download_file(file.file_path)).read()
        from database.repositories.profile_repository import ProfileRepository
        profile = await ProfileRepository(session).get_by_user_id(user.id)
        profile_bytes = b""
        if profile and profile.photos:
            try:
                pf = await message.bot.get_file(profile.photos[0].file_id)
                profile_bytes = (await message.bot.download_file(pf.file_path)).read()
            except Exception:
                pass
        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.groq_client import GroqClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository
        ver_service = VerificationService(VerificationRepository(session), AIService(GroqClient(), CacheManager()))
        passed, msg = await ver_service.verify_level_3(user.id, verification_bytes, profile_bytes)
        await state.clear()
        prefix = "✅" if passed else "❌"
        await message.answer(f"{prefix} {msg}" + (f"\n\n🏅 {_BADGE_INFO[3]}" if passed else "\n\nПопробуй ещё раз."), reply_markup=verification_keyboard())
    except Exception as e:
        logger.error("verify_level_3_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")


