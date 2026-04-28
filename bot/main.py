"""Main entry point for the Моя половинка Telegram bot."""
import asyncio
import logging
import os

import structlog
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis

from bot.config import settings
from bot.handlers import register_all_handlers
from bot.middlewares import AuthMiddleware, DbSessionMiddleware, LoggingMiddleware, RateLimitMiddleware
from bot.services.rate_limiter import RateLimiter
from bot.utils.cache_manager import CacheManager, set_redis_instance
from database.connection import close_db, init_db


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


async def run_health_server() -> None:
    """Run health check HTTP server on Railway's PORT."""
    async def health(_request):
        return web.Response(text='{"status":"ok"}', content_type="application/json")

    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "8000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger = structlog.get_logger(__name__)
    logger.info("health_server_started", port=port)

    # Keep running forever
    while True:
        await asyncio.sleep(3600)


async def run_bot() -> None:
    """Initialize and run the Telegram bot."""
    logger = structlog.get_logger(__name__)
    logger.info("bot_starting", version="1.0.0")

    await init_db()

    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    storage = RedisStorage(redis)
    rate_limiter = RateLimiter(redis, settings)
    set_redis_instance(redis)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(AuthMiddleware())
    dp.update.middleware(RateLimitMiddleware(rate_limiter))

    register_all_handlers(dp)

    scheduler = AsyncIOScheduler()
    from bot.scheduler import setup_all_jobs
    from database.connection import AsyncSessionFactory
    setup_all_jobs(scheduler, bot, AsyncSessionFactory)
    scheduler.start()

    logger.info("bot_started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await redis.aclose()
        await close_db()
        logger.info("bot_stopped")


async def main() -> None:
    configure_logging()
    # Run health server and bot concurrently
    await asyncio.gather(
        run_health_server(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
