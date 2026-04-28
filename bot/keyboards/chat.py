from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import ChatCallback


def chat_keyboard(match_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💡 AI-подсказка", callback_data=ChatCallback(action="ai_hint", match_id=match_id).pack()),
            InlineKeyboardButton(text="🔮 Совместимость", callback_data=ChatCallback(action="compatibility", match_id=match_id).pack()),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарить", callback_data=ChatCallback(action="gift", match_id=match_id).pack()),
        ],
    ])
