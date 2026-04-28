from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import SettingsCallback


def settings_keyboard(daily_report_enabled: bool = True) -> InlineKeyboardMarkup:
    report_text = "🔔 Отчёты: ВКЛ" if daily_report_enabled else "🔕 Отчёты: ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=report_text, callback_data=SettingsCallback(action="toggle_reports").pack())],
        [InlineKeyboardButton(text="📍 Обновить геолокацию", callback_data=SettingsCallback(action="location").pack())],
        [InlineKeyboardButton(text="🗑 Удалить профиль", callback_data=SettingsCallback(action="delete").pack())],
        [InlineKeyboardButton(text="🚪 Выйти", callback_data=SettingsCallback(action="logout").pack())],
    ])
