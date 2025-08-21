import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # Required in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = Field(..., env="DATABASE_URL")  # Required in production

    # Port configuration for Render
    PORT: int = Field(default=10000, env="PORT")

    # Admin token - required for admin endpoints (generate a secure random string)
    ADMIN_TOKEN: str = Field(
        default="", env="ADMIN_TOKEN"
    )  # Empty default for dev, MUST be set in production
    DAILY_DROP_THRESHOLD: float = -0.01

    ASSET_DEFAULT_START: str = "2018-01-01"
    SP500_TICKER: str = "^GSPC"

    # TwelveData API configuration
    TWELVEDATA_API_KEY: str = Field(default="", env="TWELVEDATA_API_KEY")
    TWELVEDATA_PLAN: str = Field(
        default="free", env="TWELVEDATA_PLAN"
    )  # free, grow, pro, etc.
    TWELVEDATA_RATE_LIMIT: int = Field(
        default=8, env="TWELVEDATA_RATE_LIMIT"
    )  # Credits per minute
    ENABLE_MARKET_DATA_CACHE: bool = Field(default=True, env="ENABLE_MARKET_DATA_CACHE")
    REFRESH_MODE: str = Field(
        default="auto", env="REFRESH_MODE"
    )  # auto, full, minimal, cached

    # Marketaux API configuration
    MARKETAUX_API_KEY: str = Field(default="", env="MARKETAUX_API_KEY")
    MARKETAUX_RATE_LIMIT: int = Field(
        default=100, env="MARKETAUX_RATE_LIMIT"
    )  # Requests per minute
    ENABLE_NEWS_CACHE: bool = Field(default=True, env="ENABLE_NEWS_CACHE")
    NEWS_REFRESH_INTERVAL: int = Field(
        default=900, env="NEWS_REFRESH_INTERVAL"
    )  # 15 minutes

    # Redis configuration
    REDIS_URL: str = Field(default="", env="REDIS_URL")  # redis://localhost:6379/0
    CACHE_TTL_SECONDS: int = Field(
        default=300, env="CACHE_TTL_SECONDS"
    )  # 5 minutes default
    CACHE_TTL_LONG_SECONDS: int = Field(
        default=3600, env="CACHE_TTL_LONG_SECONDS"
    )  # 1 hour

    # Debug mode
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Frontend URL for CORS
    FRONTEND_URL: str = Field(default="", env="FRONTEND_URL")

    # Skip startup refresh
    SKIP_STARTUP_REFRESH: bool = Field(default=False, env="SKIP_STARTUP_REFRESH")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()

# Security validation
if os.getenv("RENDER") or os.getenv("PRODUCTION"):  # Production environment
    if not settings.ADMIN_TOKEN or len(settings.ADMIN_TOKEN) < 32:
        import warnings

        warnings.warn(
            "ADMIN_TOKEN is not set or too short in production! "
            "Admin endpoints will be vulnerable. "
            "Please set a secure token of at least 32 characters.",
            RuntimeWarning,
            stacklevel=2,
        )
