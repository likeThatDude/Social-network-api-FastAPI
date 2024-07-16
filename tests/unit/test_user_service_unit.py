from contextlib import nullcontext as not_raises
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.database.models import User
from services.response_schema import ExceptionSchema, ResponseSchema
from services.tweets_service.schemas import UserSchema
from services.users_service.schemas import (
    ResponseUserDataSchema,
    UserDataSchema,
)
from services.users_service.service import UserService

service = UserService()
session_mock = AsyncMock()
session_mock.add.return_value = None
session_mock.flush.return_value = None
session_mock.commit.return_value = None
service.session = session_mock


class TestUserServiceUnit:

    @staticmethod
    @pytest.mark.parametrize(
        "user_id, user, execute_user, response_data",
        [
            (
                1,
                User(id=22, api_key="api-key", name="Тест"),
                User(id=24, api_key="api-key", name="Тест"),
                ResponseSchema(result=True),
            ),
            (
                1,
                User(id=1, api_key="api-key", name="Тест"),
                User(id=22, api_key="api-key", name="Тест"),
                ExceptionSchema(
                    result=False,
                    error_type="User id error",
                    error_message="A user cannot subscribe to himself",
                ),
            ),
            (
                1,
                User(id=22, api_key="api-key", name="Тест"),
                None,
                ExceptionSchema(
                    result=False,
                    error_type="User id error",
                    error_message="User with id: 1 not found",
                ),
            ),
            (
                1,
                None,
                User(id=24, api_key="api-key", name="Тест"),
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="'NoneType' object has no attribute 'id'",
                ),
            ),
        ],
    )
    async def test_add_follow(user_id, user, execute_user, response_data):
        select_mock = MagicMock()
        select_mock.scalar.return_value = execute_user
        service.session.execute.side_effect = [select_mock]
        result = await service.add_follow(user_id, user)
        assert result == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "user_id, user, execute_user, delete_result, response_data",
        [
            (
                1,
                User(id=22, api_key="api-key", name="Тест"),
                User(id=24, api_key="api-key", name="Тест"),
                True,
                ResponseSchema(result=True),
            ),
            (
                1,
                User(id=22, api_key="api-key", name="Тест"),
                User(id=24, api_key="api-key", name="Тест"),
                False,
                ExceptionSchema(
                    result=False,
                    error_type="Subscribe error",
                    error_message="User with id: 22, is not subscribed to user "
                    "with id: 1",
                ),
            ),
            (
                1,
                User(id=1, api_key="api-key", name="Тест"),
                User(id=24, api_key="api-key", name="Тест"),
                True,
                ExceptionSchema(
                    result=False,
                    error_type="User id error",
                    error_message="A user cannot unsubscribe to himself",
                ),
            ),
            (
                1,
                User(id=22, api_key="api-key", name="Тест"),
                None,
                True,
                ExceptionSchema(
                    result=False,
                    error_type="User id error",
                    error_message="User with id: 1 not found",
                ),
            ),
            (
                1,
                None,
                User(id=22, api_key="api-key", name="Тест"),
                True,
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="'NoneType' object has no attribute 'id'",
                ),
            ),
        ],
    )
    async def test_unfollow_user(
        user_id, user, execute_user, delete_result, response_data
    ):
        delete_mock = MagicMock()
        delete_mock.rowcount = delete_result
        select_mock = MagicMock()
        select_mock.scalar.return_value = execute_user
        service.session.execute.side_effect = (
            [select_mock, delete_mock] if execute_user else [select_mock]
        )
        response = await service.unfollow_user(user_id, user)
        assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "user, response_data",
        [
            (
                User(
                    id=22,
                    api_key="api-key",
                    name="Тест",
                    followers=[User(id=22, name="Тестовый подписчик")],
                    following=[User(id=22, name="Тестовая подписка")],
                ),
                ResponseUserDataSchema(
                    result=True,
                    user=UserDataSchema(
                        id=22,
                        name="Тест",
                        followers=[
                            UserSchema(id=22, name="Тестовый подписчик")
                        ],
                        following=[
                            UserSchema(id=22, name="Тестовая подписка")
                        ],
                    ),
                ),
            ),
            (
                User(
                    id=1,
                    api_key="api-key",
                    name="Тест",
                    followers=[User(id=2, name="Тестовый подписчик")],
                    following=[User(id=3, name="Тестовая подписка")],
                ),
                ResponseUserDataSchema(
                    result=True,
                    user=UserDataSchema(
                        id=1,
                        name="Тест",
                        followers=[
                            UserSchema(id=2, name="Тестовый подписчик")
                        ],
                        following=[UserSchema(id=3, name="Тестовая подписка")],
                    ),
                ),
            ),
            (
                None,
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="'NoneType' object has no attribute 'id'",
                ),
            ),
        ],
    )
    async def test_get_user_data(user, response_data):
        select_mock = MagicMock()
        select_mock.scalar.return_value = user
        service.session.execute.side_effect = [select_mock]
        response = await service.get_user_data(user)
        assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "user, response_data, exep",
        [
            (
                User(
                    id=22,
                    api_key="api-key",
                    name="Тест",
                    followers=[User(id=22, name="Тестовый подписчик")],
                    following=[User(id=22, name="Тестовая подписка")],
                ),
                ResponseUserDataSchema(
                    result=True,
                    user=UserDataSchema(
                        id=22,
                        name="Тест",
                        followers=[
                            UserSchema(id=22, name="Тестовый подписчик")
                        ],
                        following=[
                            UserSchema(id=22, name="Тестовая подписка")
                        ],
                    ),
                ),
                not_raises(),
            ),
            (
                User(
                    id=1,
                    api_key="api-key",
                    name="Тест",
                    followers=[User(id=2, name="Тестовый подписчик")],
                    following=[User(id=3, name="Тестовая подписка")],
                ),
                ResponseUserDataSchema(
                    result=True,
                    user=UserDataSchema(
                        id=1,
                        name="Тест",
                        followers=[
                            UserSchema(id=2, name="Тестовый подписчик")
                        ],
                        following=[UserSchema(id=3, name="Тестовая подписка")],
                    ),
                ),
                not_raises(),
            ),
            (
                None,
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="'NoneType' object has no attribute 'id'",
                ),
                pytest.raises(AssertionError),
            ),
        ],
    )
    async def test_find_user(user, response_data, exep):
        with exep:
            select_mock = MagicMock()
            select_mock.scalar.return_value = user
            service.session.execute.side_effect = [select_mock]
            response = await service.find_user(1)
            assert response == response_data
