"""Profile handler — show profile, edit, AI improve, registration FSM."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PhotoSize

from bot.fsm import ProfileEditStates, RegistrationStates
from bot.keyboards import ProfileCallback, main_menu_keyboard, profile_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="profile")


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from database.repositories.profile_repository import ProfileRepository
        profile = await ProfileRepository(session).get_by_user_id(user.id)
        if profile is None:
            await message.answer("Профиль не найден. Используй /start для регистрации.")
            return
        text = (
            f"👤 <b>{user.first_name}</b>, {profile.age} лет\n"
            f"📍 {profile.city or '—'}\n"
            f"📏 {profile.height or '—'} см\n"
            f"🎯 {profile.relationship_goals or '—'}\n"
            f"🧠 MBTI: {profile.mbti_type or '—'}\n"
            f"💬 {profile.about_me or '—'}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=profile_keyboard())
    except Exception as e:
        logger.error("show_profile_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить профиль. Попробуй позже.")


@router.callback_query(ProfileCallback.filter(F.action == "edit"))
async def profile_edit(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(ProfileEditStates.edit_about_me)
    await callback.message.answer("✏️ Введи новый текст «О себе»:")


@router.callback_query(ProfileCallback.filter(F.action == "photos"))
async def profile_photos(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.set_state(ProfileEditStates.add_photo)
    await callback.message.answer("📸 Отправь фото для добавления в профиль:")


@router.callback_query(ProfileCallback.filter(F.action == "ai_improve"))
async def profile_ai_improve(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("⏳ Улучшаю профиль через AI…")
    if user is None:
        return
    try:
        from database.repositories.profile_repository import ProfileRepository
        from bot.services.ai_service import AIService
        from bot.openrouter_client import OpenRouterClient
        from bot.utils.cache_manager import CacheManager

        profile = await ProfileRepository(session).get_by_user_id(user.id)
        if profile is None:
            await callback.message.answer("Профиль не найден.")
            return

        ai = AIService(OpenRouterClient(), CacheManager())
        result = await ai.improve_profile({
            "about_me": profile.about_me,
            "age": profile.age,
            "city": profile.city,
            "relationship_goals": profile.relationship_goals,
            "mbti_type": profile.mbti_type,
        })

        improved_text = result.get("about_me", "")
        tags_str = ", ".join(result.get("suggested_tags", [])) or "—"

        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Применить", callback_data="ai_improve:confirm"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="ai_improve:reject"),
        ]])
        await callback.message.answer(
            f"🤖 <b>AI-улучшение профиля</b>\n\n<b>О себе:</b>\n{improved_text}\n\n<b>Теги:</b> {tags_str}",
            parse_mode="HTML", reply_markup=kb,
        )
    except Exception as e:
        logger.error("ai_improve_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось улучшить профиль. Попробуй позже.")


@router.callback_query(F.data == "ai_improve:confirm")
async def ai_improve_confirm(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("✅ Профиль обновлён!")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data == "ai_improve:reject")
async def ai_improve_reject(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("❌ Изменения отклонены.")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(ProfileCallback.filter(F.action == "verify"))
async def profile_verify(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    from bot.keyboards import verification_keyboard
    await callback.message.answer(
        "✅ <b>Верификация профиля</b>\n\nВыбери уровень:",
        parse_mode="HTML", reply_markup=verification_keyboard(),
    )


@router.callback_query(ProfileCallback.filter(F.action == "stories"))
async def profile_stories(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    await callback.message.answer("📖 Переходим к историям…")


# ── Registration FSM ──────────────────────────────────────────────────────────

@router.message(RegistrationStates.age)
async def reg_age(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text.strip())
        if not (16 <= age <= 100):
            raise ValueError
        await state.update_data(age=age)
        await state.set_state(RegistrationStates.city)
        await message.answer("📍 В каком городе ты живёшь?")
    except ValueError:
        await message.answer("Введи корректный возраст (16–100):")


@router.message(RegistrationStates.city)
async def reg_city(message: Message, state: FSMContext) -> None:
    city = message.text.strip()
    if len(city) < 2:
        await message.answer("Введи название города:")
        return
    await state.update_data(city=city)
    await state.set_state(RegistrationStates.height)
    await message.answer("📏 Твой рост в сантиметрах (или пропусти — отправь «-»):")


@router.message(RegistrationStates.height)
async def reg_height(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    height = None
    if text != "-":
        try:
            height = int(text)
            if not (100 <= height <= 250):
                raise ValueError
        except ValueError:
            await message.answer("Введи рост от 100 до 250 см, или «-» для пропуска:")
            return
    await state.update_data(height=height)
    await state.set_state(RegistrationStates.relationship_goals)
    await message.answer("🎯 Что ты ищешь?\n\nВарианты: серьёзные отношения, дружба, флирт, не знаю")


@router.message(RegistrationStates.relationship_goals)
async def reg_goals(message: Message, state: FSMContext) -> None:
    await state.update_data(relationship_goals=message.text.strip())
    await state.set_state(RegistrationStates.attachment_style)
    await message.answer(
        "💞 Стиль привязанности?\n\n"
        "Варианты: надёжный, тревожный, избегающий, дезорганизованный, «-» если не знаешь"
    )


@router.message(RegistrationStates.attachment_style)
async def reg_attachment(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    await state.update_data(attachment_style=None if text == "-" else text)
    await state.set_state(RegistrationStates.interests)
    await message.answer("🎨 Перечисли свои интересы через запятую:")


@router.message(RegistrationStates.interests)
async def reg_interests(message: Message, state: FSMContext) -> None:
    interests = [i.strip() for i in message.text.split(",") if i.strip()]
    await state.update_data(interests=interests)
    await state.set_state(RegistrationStates.about_me)
    await message.answer("💬 Расскажи о себе в нескольких словах:")


@router.message(RegistrationStates.about_me)
async def reg_about_me(message: Message, state: FSMContext) -> None:
    await state.update_data(about_me=message.text.strip())
    await state.set_state(RegistrationStates.photos)
    await message.answer("📸 Отправь своё главное фото (или «-» для пропуска):")


@router.message(RegistrationStates.photos, F.photo)
async def reg_photos(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(RegistrationStates.video_profile)
    await message.answer("🎥 Отправь короткое видео-знакомство (до 30 сек) или «-» для пропуска:")


@router.message(RegistrationStates.photos, F.text == "-")
async def reg_photos_skip(message: Message, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.video_profile)
    await message.answer("🎥 Отправь короткое видео-знакомство (до 30 сек) или «-» для пропуска:")


@router.message(RegistrationStates.video_profile, F.video)
async def reg_video(message: Message, state: FSMContext) -> None:
    await state.update_data(video_file_id=message.video.file_id)
    await state.set_state(RegistrationStates.voice_greeting)
    await message.answer("🎙 Запиши голосовое приветствие или «-» для пропуска:")


@router.message(RegistrationStates.video_profile, F.text == "-")
async def reg_video_skip(message: Message, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.voice_greeting)
    await message.answer("🎙 Запиши голосовое приветствие или «-» для пропуска:")


@router.message(RegistrationStates.voice_greeting, F.voice)
async def reg_voice(message: Message, state: FSMContext) -> None:
    await state.update_data(voice_file_id=message.voice.file_id)
    await state.set_state(RegistrationStates.confirm)
    await _show_registration_summary(message, state)


@router.message(RegistrationStates.voice_greeting, F.text == "-")
async def reg_voice_skip(message: Message, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.confirm)
    await _show_registration_summary(message, state)


async def _show_registration_summary(message: Message, state: FSMContext) -> None:
    d = await state.get_data()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="reg:confirm"),
        InlineKeyboardButton(text="🔄 Начать заново", callback_data="reg:restart"),
    ]])
    await message.answer(
        f"📋 <b>Твой профиль:</b>\n\n"
        f"Возраст: {d.get('age')}\n"
        f"Город: {d.get('city')}\n"
        f"Рост: {d.get('height') or '—'}\n"
        f"Цели: {d.get('relationship_goals')}\n"
        f"MBTI: {d.get('mbti_type') or '—'}\n"
        f"О себе: {d.get('about_me')}",
        parse_mode="HTML", reply_markup=kb,
    )


@router.callback_query(F.data == "reg:confirm", RegistrationStates.confirm)
async def reg_confirm(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    d = await state.get_data()
    try:
        from database.repositories.profile_repository import ProfileRepository
        from database.repositories.user_repository import UserRepository
        from bot.utils.timezone_helper import detect_timezone_from_city

        profile_repo = ProfileRepository(session)
        user_repo = UserRepository(session)
        city = d.get("city")
        timezone = detect_timezone_from_city(city)
        await user_repo.update_timezone(user.id, timezone)
        await profile_repo.create_or_update(
            user_id=user.id,
            age=d.get("age"),
            city=city,
            height=d.get("height"),
            relationship_goals=d.get("relationship_goals"),
            mbti_type=d.get("mbti_type"),
            attachment_style=d.get("attachment_style"),
            interests=d.get("interests", []),
            about_me=d.get("about_me"),
        )
        await user_repo.mark_registered(user.id)

        referral_from = d.get("referral_from")
        if referral_from:
            from bot.services.referral_service import ReferralService
            from database.repositories.referral_repository import ReferralRepository
            await ReferralService(ReferralRepository(session), user_repo).process_referral(referral_from, user.id)

        await state.clear()
        await callback.message.answer(
            "🎉 Профиль создан! Добро пожаловать в <b>Моя половинка</b>!",
            parse_mode="HTML", reply_markup=main_menu_keyboard(is_premium=False),
        )
        logger.info("registration_completed", user_id=user.id)
    except Exception as e:
        logger.error("reg_confirm_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка при сохранении профиля. Попробуй позже.")


@router.callback_query(F.data == "reg:restart", RegistrationStates.confirm)
async def reg_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(RegistrationStates.age)
    await callback.message.answer("🔄 Начинаем заново. Сколько тебе лет?")


@router.message(ProfileEditStates.edit_about_me)
async def edit_about_me(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from database.repositories.profile_repository import ProfileRepository
        await ProfileRepository(session).create_or_update(user_id=user.id, about_me=message.text.strip())
        await state.clear()
        await message.answer("✅ Текст «О себе» обновлён!", reply_markup=main_menu_keyboard(user.is_premium))
    except Exception as e:
        logger.error("edit_about_me_error", user_id=user.id, error=str(e))
        await message.answer("Ошибка при обновлении. Попробуй позже.")


@router.message(ProfileEditStates.add_photo, F.photo)
async def edit_add_photo(message: Message, state: FSMContext, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from database.repositories.profile_repository import ProfileRepository
        profile = await ProfileRepository(session).get_by_user_id(user.id)
        if profile:
            await ProfileRepository(session).add_photo(profile.id, message.photo[-1].file_id, 0)
        await state.clear()
        await message.answer("✅ Фото добавлено!", reply_markup=main_menu_keyboard(user.is_premium))
    except Exception as e:
        logger.error("add_photo_error", user_id=user.id, error=str(e))
        await message.answer("Ошибка при добавлении фото. Попробуй позже.")
