from aiogram.fsm.state import State, StatesGroup


class VerificationStates(StatesGroup):
    level_1_waiting = State()
    level_2_waiting = State()
    level_3_waiting = State()
    processing = State()
