"""
This module sets up the asynchronous SQLAlchemy database engine, session
factory, and base model for an application.

It provides:
1. An asynchronous engine for connecting to the PostgreSQL database.
2. A session factory for managing database sessions.
3. A base model class for defining database models.
4. A function for obtaining asynchronous sessions.

Configuration details are loaded from the `settings` module.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy.pool import NullPool

from config import settings

engine = create_async_engine(
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@"
    f"{settings.DOCKER_DATABASE}:{settings.DOCKER_DATABASE_PORT}/"
    f"{settings.DB_NAME}",
    echo=False,
    poolclass=NullPool if settings.MODE != "PROD" else None,
)

session_factory = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@as_declarative()
class Base:
    """
    Base class for all database models.

    The `__tablename__` attribute is automatically generated based on the
    class name.
    """

    @classmethod
    @declared_attr
    def __tablename__(cls):
        """
        Generate the table name for the model class.

        Returns:
            str: The table name in lowercase, pluralized form.
        """
        return f"{cls.__name__.lower()}s"


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous session for database operations.

    Yields:
        AsyncGenerator[AsyncSession, None]: An asynchronous session for use
        within a context manager.
    """
    async with session_factory() as session:
        yield session
