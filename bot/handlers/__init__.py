"""Handler registration for the Моя половинка bot."""
from aiogram import Dispatcher

from .start import router as start_router
from .profile import router as profile_router
from .swipe import router as swipe_router
from .chat import router as chat_router
from .premium import router as premium_router
from .verification import router as verification_router
from .speed_dating import router as speed_dating_router
from .stories import router as stories_router
from .settings import router as settings_router
from .stats import router as stats_router
from .payments import router as payments_router

__all__ = [
    "register_all_handlers",
    "start_router",
    "profile_router",
    "swipe_router",
    "chat_router",
    "premium_router",
    "verification_router",
    "speed_dating_router",
    "stories_router",
    "settings_router",
    "stats_router",
    "payments_router",
]


def register_all_handlers(dp: Dispatcher) -> None:
    """Include all routers into the dispatcher."""
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(swipe_router)
    dp.include_router(chat_router)
    dp.include_router(premium_router)
    dp.include_router(verification_router)
    dp.include_router(speed_dating_router)
    dp.include_router(stories_router)
    dp.include_router(settings_router)
    dp.include_router(stats_router)
    dp.include_router(payments_router)
