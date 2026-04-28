from aiogram.fsm.state import State, StatesGroup


class SwipeStates(StatesGroup):
    viewing = State()
    deep_search_active = State()
