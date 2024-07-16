import asyncio
import shutil
import sys
import threading
from pathlib import Path
from typing import AsyncGenerator

import pytest
import requests
from fastapi.testclient import TestClient
from httpx import AsyncClient

from config import logger, settings
from main import app
from services.database.db_connect import Base, engine, session_factory
from services.database.models import User
from services.redis.redis_service import redis

URL = "https://cataas.com/cat"
OUT_PATH = Path(__file__).parent / "media_for_test"
OUT_PATH.mkdir(exist_ok=True, parents=True)
OUT_PATH = OUT_PATH.absolute()


def write_file(file, path):
    with open(path, mode="wb") as f:
        f.write(file)


def get_request(url, data_number):
    req_data = requests.get(url)
    if req_data.status_code == 200:
        write_file(req_data.content, f"{OUT_PATH}/{data_number}.png")


def get_all_cats(cats_count):
    threads = []
    for i in range(cats_count):
        thread = threading.Thread(target=get_request, args=(URL, i + 1))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


@pytest.fixture(scope="session", autouse=True)
def disable_loguru_logging():
    logger.remove()
    logger.add(lambda _: None, level="ERROR")
    yield
    logger.remove()
    logger.add(sys.stderr, level="INFO")


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_cache():
    await redis.init_cache()
    yield
    await redis.close_cache()


@pytest.fixture(scope="session", autouse=True)
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        get_all_cats(3)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        shutil.rmtree(OUT_PATH)


@pytest.fixture(scope="session", autouse=True)
async def test_db():
    async with session_factory() as session:
        user = [User(api_key=f"test{i}", name=f"Тест{i}") for i in range(5)]
        session.add_all(user)
        await session.commit()


@pytest.fixture(scope="function", autouse=True)
async def clear_cache():
    await redis.clear_cache()


client = TestClient(app)


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            app=app,
            base_url=f"http://{settings.DOCKER_DATABASE}:"
                     f"{settings.DOCKER_DATABASE_PORT}"
    ) as ac:
        yield ac
