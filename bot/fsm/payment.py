from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    selecting_plan = State()
    selecting_crystals = State()
    awaiting_payment = State()
