# Моя половинка — утилиты бота

# FSM (Finite State Machine) хранилище реализовано через aiogram RedisStorage.
# Пример инициализации в точке входа:
#
#   from aiogram.fsm.storage.redis import RedisStorage
#   storage = RedisStorage.from_url(settings.redis_url)
#   bot = Bot(token=settings.bot_token)
#   dp = Dispatcher(storage=storage)
#
# RedisStorage автоматически сериализует состояния FSM и данные пользователей
# в Redis, обеспечивая персистентность между перезапусками бота.

from bot.utils.cache_manager import CacheManager

__all__ = ["CacheManager"]
