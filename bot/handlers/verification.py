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
async def verify_level_1_start(callback: CallbackQuery, state: FSMContext, data: dict) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_1_waiting)
    await callback.message.answer(
        "⭕ <b>Верификация уровня 1</b>\n\n"
        "Сделай фото, на котором ты показываешь жест круга пальцами.\n"
        "Лицо должно быть хорошо видно.",
        parse_mode="HTML",
    )


@router.callback_query(VerificationCallback.filter(F.level == 2))
async def verify_level_2_start(callback: CallbackQuery, state: FSMContext, data: dict) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_2_waiting)
    await callback.message.answer(
        "🎥 <b>Верификация уровня 2</b>\n\n"
        "Отправь короткое видео-селфи (до 30 сек).\n"
        "Максимальный размер файла: 50 МБ.",
        parse_mode="HTML",
    )


@router.callback_query(VerificationCallback.filter(F.level == 3))
async def verify_level_3_start(callback: CallbackQuery, state: FSMContext, data: dict) -> None:
    await callback.answer()
    await state.set_state(VerificationStates.level_3_waiting)
    await callback.message.answer(
        "🤖 <b>Верификация уровня 3</b>\n\n"
        "Отправь чёткое фото своего лица для AI-распознавания.\n"
        "Оно будет сравнено с фото в профиле.",
        parse_mode="HTML",
    )


@router.message(VerificationStates.level_1_waiting, F.photo)
async def verify_level_1_photo(message: Message, state: FSMContext, data: dict) -> None:
    user = data["user"]
    session = data["session"]
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Проверяю фото…")

    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository

        openrouter = OpenRouterClient()
        cache = CacheManager()
        ai = AIService(openrouter, cache)
        ver_service = VerificationService(VerificationRepository(session), ai)

        passed, msg = await ver_service.verify_level_1(user.id, image_bytes)
        await state.clear()

        if passed:
            await message.answer(
                f"✅ {msg}\n\n🏅 Значок: {_BADGE_INFO[1]}",
                reply_markup=verification_keyboard(),
            )
        else:
            await message.answer(
                f"❌ {msg}\n\nПопробуй ещё раз.",
                reply_markup=verification_keyboard(),
            )
        logger.info("level1_verification_done", user_id=user.id, passed=passed)
    except Exception as e:
        logger.error("verify_level_1_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")


@router.message(VerificationStates.level_2_waiting, F.video)
async def verify_level_2_video(message: Message, state: FSMContext, data: dict) -> None:
    user = data["user"]
    session = data["session"]
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Проверяю видео…")

    try:
        file = await message.bot.get_file(message.video.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        video_bytes = file_bytes.read()

        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository

        openrouter = OpenRouterClient()
        cache = CacheManager()
        ai = AIService(openrouter, cache)
        ver_service = VerificationService(VerificationRepository(session), ai)

        passed, msg = await ver_service.verify_level_2(user.id, video_bytes)
        await state.clear()

        if passed:
            await message.answer(
                f"✅ {msg}\n\n🏅 Значок: {_BADGE_INFO[2]}",
                reply_markup=verification_keyboard(),
            )
        else:
            await message.answer(f"❌ {msg}\n\nПопробуй ещё раз.", reply_markup=verification_keyboard())
        logger.info("level2_verification_done", user_id=user.id, passed=passed)
    except Exception as e:
        logger.error("verify_level_2_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")


@router.message(VerificationStates.level_3_waiting, F.photo)
async def verify_level_3_photo(message: Message, state: FSMContext, data: dict) -> None:
    user = data["user"]
    session = data["session"]
    await state.set_state(VerificationStates.processing)
    await message.answer("⏳ Сравниваю лица через AI…")

    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        verification_bytes = file_bytes.read()

        # Get profile photo for comparison
        from database.repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(session)
        profile = await profile_repo.get_by_user_id(user.id)

        profile_bytes = b""
        if profile and profile.photos:
            try:
                pf = await message.bot.get_file(profile.photos[0])
                pb = await message.bot.download_file(pf.file_path)
                profile_bytes = pb.read()
            except Exception:
                pass

        from bot.services.verification_service import VerificationService
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager
        from database.repositories.verification_repository import VerificationRepository

        openrouter = OpenRouterClient()
        cache = CacheManager()
        ai = AIService(openrouter, cache)
        ver_service = VerificationService(VerificationRepository(session), ai)

        passed, msg = await ver_service.verify_level_3(user.id, verification_bytes, profile_bytes)
        await state.clear()

        if passed:
            await message.answer(
                f"✅ {msg}\n\n🏅 Значок: {_BADGE_INFO[3]}",
                reply_markup=verification_keyboard(),
            )
        else:
            await message.answer(f"❌ {msg}\n\nПопробуй ещё раз.", reply_markup=verification_keyboard())
        logger.info("level3_verification_done", user_id=user.id, passed=passed)
    except Exception as e:
        logger.error("verify_level_3_error", user_id=user.id, error=str(e))
        await state.clear()
        await message.answer("Ошибка при проверке. Попробуй позже.")
