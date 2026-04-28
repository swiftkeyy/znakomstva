from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import VerificationCallback


def verification_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭕ Уровень 1 — Жест круга", callback_data=VerificationCallback(level=1).pack())],
        [InlineKeyboardButton(text="🎥 Уровень 2 — Видео-селфи", callback_data=VerificationCallback(level=2).pack())],
        [InlineKeyboardButton(text="🤖 Уровень 3 — AI распознавание", callback_data=VerificationCallback(level=3).pack())],
    ])
