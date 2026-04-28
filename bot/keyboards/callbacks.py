"""All CallbackData factories for the Моя половинка bot."""
from aiogram.filters.callback_data import CallbackData


class SwipeCallback(CallbackData, prefix="swipe"):
    action: str  # like, pass, super_like, write
    user_id: int


class ChatCallback(CallbackData, prefix="chat"):
    action: str  # ai_hint, compatibility, gift
    match_id: int


class ProfileCallback(CallbackData, prefix="profile"):
    action: str  # edit, photos, ai_improve, verify, stories


class PremiumCallback(CallbackData, prefix="premium"):
    action: str  # sub_1, sub_3, sub_12, crystals_100, crystals_500, crystals_1000, crystals_5000


class VerificationCallback(CallbackData, prefix="verify"):
    level: int


class SettingsCallback(CallbackData, prefix="settings"):
    action: str  # toggle_reports, location, delete, logout


class SpeedDatingCallback(CallbackData, prefix="sd"):
    action: str  # join, match_yes, match_no
    session_id: int


class StoryCallback(CallbackData, prefix="story"):
    action: str  # view, delete
    story_id: int


class AISuggestionCallback(CallbackData, prefix="ai_sug"):
    action: str  # bold, warm, playful
    match_id: int
