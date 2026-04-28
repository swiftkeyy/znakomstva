from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import SwipeCallback


def swipe_keyboard(candidate_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайк", callback_data=SwipeCallback(action="like", user_id=candidate_user_id).pack()),
            InlineKeyboardButton(text="❌ Пропустить", callback_data=SwipeCallback(action="pass", user_id=candidate_user_id).pack()),
        ],
        [
            InlineKeyboardButton(text="💬 Написать сразу", callback_data=SwipeCallback(action="write", user_id=candidate_user_id).pack()),
            InlineKeyboardButton(text="⭐ SuperSwipe", callback_data=SwipeCallback(action="super_like", user_id=candidate_user_id).pack()),
        ],
    ])
