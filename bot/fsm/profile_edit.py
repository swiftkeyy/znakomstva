from aiogram.fsm.state import State, StatesGroup


class ProfileEditStates(StatesGroup):
    edit_about_me = State()
    edit_interests = State()
    edit_goals = State()
    edit_mbti = State()
    edit_attachment = State()
    add_photo = State()
    delete_photo = State()
    add_video = State()
    add_voice = State()
