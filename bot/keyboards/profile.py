from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import ProfileCallback


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=ProfileCallback(action="edit").pack())],
        [InlineKeyboardButton(text="📸 Фото", callback_data=ProfileCallback(action="photos").pack())],
        [InlineKeyboardButton(text="🤖 Улучшить через AI", callback_data=ProfileCallback(action="ai_improve").pack())],
        [InlineKeyboardButton(text="✅ Верификация", callback_data=ProfileCallback(action="verify").pack())],
        [InlineKeyboardButton(text="📖 Мои истории", callback_data=ProfileCallback(action="stories").pack())],
    ])
