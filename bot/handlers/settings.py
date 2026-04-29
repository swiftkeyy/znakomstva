"""Settings handler — toggle reports, location, delete profile, logout."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import SettingsCallback, main_menu_keyboard, settings_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="settings")


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    await message.answer("⚙️ <b>Настройки</b>", parse_mode="HTML", reply_markup=settings_keyboard(daily_report_enabled=user.daily_reports_enabled))


@router.callback_query(SettingsCallback.filter(F.action == "toggle_reports"))
async def settings_toggle_reports(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    try:
        from database.repositories.user_repository import UserRepository
        new_value = not user.daily_reports_enabled
        await UserRepository(session).toggle_daily_reports(user.id, new_value)
        status = "включены 🔔" if new_value else "выключены 🔕"
        await callback.message.edit_reply_markup(reply_markup=settings_keyboard(daily_report_enabled=new_value))
        await callback.message.answer(f"Ежедневные отчёты {status}.")
    except Exception as e:
        logger.error("toggle_reports_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")


@router.callback_query(SettingsCallback.filter(F.action == "location"))
async def settings_location(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
    await callback.message.answer("📍 Нажми кнопку ниже, чтобы обновить геолокацию:", reply_markup=kb)


@router.message(F.location)
async def handle_location(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    try:
        from database.repositories.profile_repository import ProfileRepository
        await ProfileRepository(session).update_location(user.id, lat=message.location.latitude, lon=message.location.longitude)
        await message.answer("✅ Геолокация обновлена!", reply_markup=main_menu_keyboard(is_premium=user.is_premium))
    except Exception as e:
        logger.error("handle_location_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось обновить геолокацию. Попробуй позже.")


@router.callback_query(SettingsCallback.filter(F.action == "support"))
async def settings_support(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    from bot.config import settings as cfg
    admin_ids = cfg.get_admin_ids()
    # Send message to all admins
    if admin_ids:
        for admin_id in admin_ids:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"📞 <b>Обращение в поддержку</b>\n\n"
                    f"От: {callback.from_user.first_name} (@{callback.from_user.username or '—'})\n"
                    f"ID: {callback.from_user.id}\n\n"
                    f"Пользователь обратился в поддержку.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
    await callback.message.answer(
        "📞 <b>Поддержка</b>\n\n"
        "Твоё обращение отправлено администраторам.\n"
        "Мы ответим тебе в ближайшее время.\n\n"
        "Если хочешь описать проблему — просто напиши следующее сообщение.",
        parse_mode="HTML",
    )
    await callback.answer()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="settings:delete_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings:delete_cancel"),
    ]])
    await callback.message.answer("⚠️ <b>Удаление профиля</b>\n\nВсе данные будут удалены безвозвратно. Продолжить?", parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "settings:delete_confirm")
async def settings_delete_confirm(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    try:
        from database.repositories.user_repository import UserRepository
        await UserRepository(session).delete_user(user.id)
        await state.clear()
        await callback.message.answer("🗑 Профиль удалён. Спасибо, что был с нами!\nИспользуй /start для новой регистрации.")
    except Exception as e:
        logger.error("delete_confirm_error", user_id=user.id, error=str(e))
        await callback.message.answer("Ошибка при удалении. Попробуй позже.")


@router.callback_query(F.data == "settings:delete_cancel")
async def settings_delete_cancel(callback: CallbackQuery) -> None:
    await callback.answer("Отменено.")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(SettingsCallback.filter(F.action == "logout"))
async def settings_logout(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer("👋 Ты вышел из аккаунта.\nИспользуй /start для входа.")


