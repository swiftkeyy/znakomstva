from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard(is_premium: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="❤️ Поиск"), KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="💎 Бусты и кристаллы"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⚙️ Настройки")],
    ]
    if is_premium:
        buttons[1].insert(0, KeyboardButton(text="🔥 Кто меня лайкнул"))

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, persistent=True)
