from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import ProfileCallback


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать анкету", callback_data=ProfileCallback(action="edit_full").pack())],
        [InlineKeyboardButton(text="📸 Фото", callback_data=ProfileCallback(action="photos").pack())],
        [InlineKeyboardButton(text="🤖 Улучшить через AI", callback_data=ProfileCallback(action="ai_improve").pack())],
        [InlineKeyboardButton(text="✅ Верификация", callback_data=ProfileCallback(action="verify").pack())],
        [InlineKeyboardButton(text="📖 Мои истории", callback_data=ProfileCallback(action="stories").pack())],
    ])


def edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Имя", callback_data=ProfileCallback(action="edit_name").pack())],
        [InlineKeyboardButton(text="🎂 Возраст", callback_data=ProfileCallback(action="edit_age").pack())],
        [InlineKeyboardButton(text="📍 Город", callback_data=ProfileCallback(action="edit_city").pack())],
        [InlineKeyboardButton(text="📏 Рост", callback_data=ProfileCallback(action="edit_height").pack())],
        [InlineKeyboardButton(text="🎯 Цели", callback_data=ProfileCallback(action="edit_goals").pack())],
        [InlineKeyboardButton(text="💬 О себе", callback_data=ProfileCallback(action="edit_about").pack())],
        [InlineKeyboardButton(text="⚧ Пол", callback_data=ProfileCallback(action="edit_gender").pack())],
        [InlineKeyboardButton(text="🔍 Кого ищу", callback_data=ProfileCallback(action="edit_looking").pack())],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=ProfileCallback(action="back").pack())],
    ])
