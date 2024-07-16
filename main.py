import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.tweets_service.routes import tweets_router
from services.media_service.routes import media_router
from services.users_service.routes import user_router
from services.database.users_init import check_users
from config import logger, settings
import sentry_sdk
from services.redis.redis_service import redis

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
)


@asynccontextmanager
async def startup_event(app: FastAPI):
    await redis.init_cache()
    logger.info(f"Start application at {datetime.datetime.now()}")
    await check_users()
    yield
    await redis.close_cache()
    logger.info(f"Stop application at {datetime.datetime.now()}")
    logger.remove()


app = FastAPI(title="Twitter clone, SkillBox", lifespan=startup_event)

origins = ["http://gorbatenkoiv.ru/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=[
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization",
    ],
)

app.include_router(tweets_router)
app.include_router(media_router)
app.include_router(user_router)
