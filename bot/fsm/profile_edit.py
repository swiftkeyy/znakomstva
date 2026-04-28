from aiogram.fsm.state import State, StatesGroup


class ProfileEditStates(StatesGroup):
    edit_about_me = State()
    edit_name = State()
    edit_age = State()
    edit_city = State()
    edit_height = State()
    edit_goals = State()
    add_photo = State()
