"""
Module for managing user-related services.

This module provides a service class that handles user operations
such as following/unfollowing users and retrieving user data. It uses
SQLAlchemy for database interactions and Redis for caching.
"""

import json

from fastapi import Depends
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from services.database.db_connect import get_async_session
from services.database.models import Subscription, User
from services.redis.redis_service import redis
from services.response_schema import ExceptionSchema, ResponseSchema
from services.users_service.schemas import (
    ResponseUserDataSchema,
    UserDataSchema,
)
from services.utils import handle_exceptions


class UserService:
    """
    Service class for user operations.

    This class includes methods to add or remove followers, as well as
    methods to retrieve user data. Each method handles exceptions using
    the handle_exceptions decorator.
    """

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        """
        Initializes the UserService with a database session.

        Args:
            session (AsyncSession): The asynchronous database session.
        """
        self.session = session

    @handle_exceptions
    async def add_follow(
        self, user_id: int, user: User
    ) -> ResponseSchema | ExceptionSchema:
        """
        Adds a follow relationship between the
        current user and the specified user.

        Args:
            user_id (int): The ID of the user to follow.
            user (User): The current user.

        Returns:
            ResponseSchema | ExceptionSchema:
            The result of the operation or error information.
        """
        if user_id == user.id:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "A user cannot subscribe to himself",
                }
            )
        query = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        data = query.scalar()
        if data:
            subscription = Subscription(
                subscriber_id=user.id, subscribed_to_id=user_id
            )
            self.session.add(subscription)
            await self.session.commit()
            await redis.delete(f"{settings.REDIS_USER_CACHE}:{user_id=}")
            return ResponseSchema.parse_obj({"result": True})
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": f"User with id: {user_id} not found",
                }
            )

    @handle_exceptions
    async def unfollow_user(
        self, user_id: int, user: User
    ) -> ResponseSchema | ExceptionSchema:
        """
        Unsubscribes the current user from the specified user.

        Args:
            user_id (int): The ID of the user to unfollow.
            user (User): The current user.red

        Returns:
            ResponseSchema | ExceptionSchema:
            The result of the operation or error information.
        """
        if user_id == user.id:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "A user cannot unsubscribe to himself",
                }
            )
        query = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        data = query.scalar()
        if data:
            stmt = await self.session.execute(
                delete(Subscription).where(
                    and_(
                        Subscription.subscriber_id == user.id,
                        Subscription.subscribed_to_id == user_id,
                    )
                )
            )
            rowcount = stmt.rowcount
            if rowcount == 1:
                await self.session.commit()
                await redis.delete(f"{settings.REDIS_USER_CACHE}:{user_id=}")
                return ResponseSchema.parse_obj({"result": True})
            else:
                return ExceptionSchema.parse_obj(
                    {
                        "result": False,
                        "error_type": "Subscribe error",
                        "error_message": f"User with id: {user.id}, "
                        f"is not subscribed "
                        f"to user with id: {user_id}",
                    }
                )
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": f"User with id: {user_id} not found",
                }
            )

    @handle_exceptions
    async def get_user_data(self, user: User):
        """
        Retrieves the data of a specific user,
        including their followers and users they are following.

        Args:
            user (User): The user whose data is to be retrieved.

        Returns:
            ResponseUserDataSchema:
            The user's data wrapped in a response schema.
        """
        user_cache_data = await redis.get(
            f"{settings.REDIS_USER_CACHE}:{user.id=}"
        )
        if not user_cache_data:
            query = await self.session.execute(
                select(User)
                .options(
                    selectinload(User.followers), selectinload(User.following)
                )
                .where(User.id == user.id)
            )
            data = query.scalar()
            user_data = UserDataSchema.model_validate(data)
            service_response = ResponseUserDataSchema.parse_obj(
                {"result": True, "user": user_data}
            )
            json_response = json.dumps(service_response.dict())
            await redis.set(
                f"{settings.REDIS_USER_CACHE}:{user.id=}",
                json_response,
                ttl=120,
            )
            return service_response
        else:
            cache_response = json.loads(user_cache_data)
            return cache_response

    @handle_exceptions
    async def find_user(self, user_id: int):
        """
        Asynchronously finds a user by their ID in the database.

        Args:
            user_id (int): The ID of the user to find.

        Returns:
            ResponseUserDataSchema:
            An object containing the result of the user search.
            If the user is found, it returns the user data in the specified
            schema.
            If the user is not found, it returns a response indicating failure.
        """
        user_cache_data = await redis.get(
            f"{settings.REDIS_USER_CACHE}:{user_id=}"
        )
        if not user_cache_data:
            query = await self.session.execute(
                select(User)
                .options(
                    selectinload(User.followers), selectinload(User.following)
                )
                .where(User.id == user_id)
            )
            data = query.scalar()
            user_data = UserDataSchema.model_validate(data)
            service_response = ResponseUserDataSchema.parse_obj(
                {"result": True, "user": user_data}
            )
            json_response = json.dumps(service_response.dict())
            await redis.set(
                f"{settings.REDIS_USER_CACHE}:{user_id=}",
                json_response,
                ttl=120,
            )
            return service_response
        else:
            cache_response = json.loads(user_cache_data)
            return cache_response
