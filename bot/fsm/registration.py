from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    name = State()
    gender = State()
    looking_for = State()
    age = State()
    city = State()
    height = State()
    relationship_goals = State()
    attachment_style = State()
    interests = State()
    about_me = State()
    photos = State()
    video_profile = State()
    voice_greeting = State()
    confirm = State()
