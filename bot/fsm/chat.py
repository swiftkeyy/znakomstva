from aiogram.fsm.state import State, StatesGroup


class ChatStates(StatesGroup):
    messaging = State()
    ai_suggestion_pending = State()
    gift_selection = State()
