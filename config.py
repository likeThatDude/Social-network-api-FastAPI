from datetime import datetime
from pathlib import Path
from loguru import logger

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent
ALLOWED_EXTENSIONS_FOR_FILE = [
    "jpeg",
    "png",
    "ico",
    "gif",
    "tiff",
    "webp",
    "eps",
    "svg",
    "psd",
    "indd",
    "cdr",
    "ai",
    "raw",
    "jpg",
    "heic"
]


class Settings(BaseSettings):
    # Tests
    MODE: str

    # Backup dir in app
    BACKUP_DIR: str

    # Logs dir in app
    LOGS_DIR: str

    # Database settings
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # S3 settings
    S3_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_TWEETS_MEDIA_FOLDER: str
    S3_LOGS_FOLDER: str
    S3_DUMP_FOLDER: str
    S3_HOUR_FOLDER: str
    S3_DAY_FOLDER: str
    S3_WEEK_FOLDER: str

    # Sentry settings
    SENTRY_DSN: str

    # Redis settings
    REDIS_TWEETS_CACHE: str
    REDIS_USER_CACHE: str

    # Docker container names
    DOCKER_CLIENT: str
    DOCKER_CLIENT_PORT: str
    DOCKER_SERVER: str
    DOCKER_SERVER_PORT: str
    DOCKER_DATABASE: str
    DOCKER_DATABASE_PORT: str
    DOCKER_REDIS: str
    DOCKER_REDIS_PORT: str
    REDIS_DB_CACHE: int
    REDIS_CELERY: int
    DOCKER_CELERY: str
    DOCKER_FLOWER: str
    DOCKER_FLOWER_PORT: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

current_date = datetime.now().strftime("%Y-%m-%d")
log_path = f"logs/{current_date}-logfile.log"

logger.add(
    log_path,
    format="{time:YYYY-MM-DD at HH:mm:ss}| {file}:{function}:"
           "{line} | {level} | {message}",
    level="INFO",
    enqueue=True,
    rotation="10 mb",
    compression="zip",
    serialize=False,
    retention="1 day",
)
