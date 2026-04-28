from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# OpenRouter free model constants
OPENROUTER_MODEL_TEXT = "meta-llama/llama-3.2-3b-instruct:free"
OPENROUTER_MODEL_VISION = "meta-llama/llama-3.2-11b-vision-instruct:free"
OPENROUTER_MODEL_REASONING = "meta-llama/llama-3.2-3b-instruct:free"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Bot
    bot_token: str
    bot_username: str = Field(default="")  # Bot username for referral links
    admin_user_ids: List[int] = Field(default_factory=list)

    # Database
    database_url: str
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_pool_size: int = Field(default=10)

    # OpenRouter AI
    openrouter_api_key: str = Field(default="")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_text_model: str = Field(default=OPENROUTER_MODEL_TEXT)
    openrouter_vision_model: str = Field(default=OPENROUTER_MODEL_VISION)
    openrouter_reasoning_model: str = Field(default=OPENROUTER_MODEL_REASONING)
    openrouter_timeout: int = Field(default=60)

    # Payments
    telegram_payment_token: str = Field(default="")
    yukassa_shop_id: str = Field(default="")
    yukassa_secret_key: str = Field(default="")

    # Monitoring
    sentry_dsn: str = Field(default="")
    log_level: str = Field(default="INFO")

    # Features
    enable_speed_dating: bool = Field(default=True)
    enable_deep_search: bool = Field(default=True)
    max_photo_count: int = Field(default=15)
    max_video_duration: int = Field(default=30)
    max_voice_duration: int = Field(default=90)

    # Rate limits
    rate_limit_swipes_free: int = Field(default=100)
    rate_limit_swipes_premium: int = Field(default=500)
    rate_limit_messages_free: int = Field(default=50)
    rate_limit_messages_premium: int = Field(default=250)
    rate_limit_ai_suggestions_free: int = Field(default=10)

    # Crystal costs
    superswipe_cost: int = Field(default=10)
    boost_cost_24h: int = Field(default=50)
    boost_cost_72h: int = Field(default=100)
    referral_crystals_registration: int = Field(default=100)
    referral_crystals_premium: int = Field(default=500)


settings = Settings()
