from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.callbacks import PremiumCallback


def premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Premium 1 мес. — 299₽", callback_data=PremiumCallback(action="sub_1").pack())],
        [InlineKeyboardButton(text="💎 Premium 3 мес. — 699₽", callback_data=PremiumCallback(action="sub_3").pack())],
        [InlineKeyboardButton(text="💎 Premium 12 мес. — 1999₽", callback_data=PremiumCallback(action="sub_12").pack())],
        [InlineKeyboardButton(text="💠 100 кристаллов — 99₽", callback_data=PremiumCallback(action="crystals_100").pack())],
        [InlineKeyboardButton(text="💠 500 кристаллов — 399₽", callback_data=PremiumCallback(action="crystals_500").pack())],
        [InlineKeyboardButton(text="💠 1000 кристаллов — 699₽", callback_data=PremiumCallback(action="crystals_1000").pack())],
        [InlineKeyboardButton(text="💠 5000 кристаллов — 2999₽", callback_data=PremiumCallback(action="crystals_5000").pack())],
    ])
