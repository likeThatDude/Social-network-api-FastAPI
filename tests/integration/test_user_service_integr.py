from contextlib import nullcontext as not_raises

import pytest
from httpx import AsyncClient


@pytest.mark.order(3)
class TestUserService:

    @staticmethod
    @pytest.mark.parametrize(
        "user_id, header, server_response, expectation",
        [
            (1, {"api-key": "test1"}, {"result": True}, not_raises()),
            (
                1,
                {"api-key": "test0"},
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "A user cannot subscribe to himself",
                },
                not_raises(),
            ),
            (
                100,
                {"api-key": "test0"},
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "User with id: 100 not found",
                },
                not_raises(),
            ),
            (
                2,
                {"api-key": "test100"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
            (
                "str",
                {"api-key": "test1"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
            (
                4,
                {"not key": "test1"},
                {
                    "result": False,
                    "error_type": "Header error",
                    "error_message": "There is no header in the request",
                },
                not_raises(),
            ),
        ],
    )
    async def test_follow(
        ac: AsyncClient, user_id, header, server_response, expectation
    ):
        with expectation:
            response = await ac.post(
                f"/api/users/{user_id}/follow", headers=header
            )
            assert response.status_code == 200
            assert response.json() == server_response

    @staticmethod
    @pytest.mark.parametrize(
        "header, server_response, expectation",
        [
            (
                {"api-key": "test0"},
                {
                    "result": True,
                    "user": {
                        "id": 1,
                        "name": "Тест0",
                        "followers": [{"id": 2, "name": "Тест1"}],
                        "following": [],
                    },
                },
                not_raises(),
            ),
            (
                {"api-key": "test1"},
                {
                    "result": True,
                    "user": {
                        "id": 2,
                        "name": "Тест1",
                        "followers": [],
                        "following": [{"id": 1, "name": "Тест0"}],
                    },
                },
                not_raises(),
            ),
            (
                {"api-key": "test100"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
            (
                {},
                {
                    "result": False,
                    "error_type": "Header error",
                    "error_message": "There is no header in the request",
                },
                not_raises(),
            ),
        ],
    )
    async def test_user_data(
        ac: AsyncClient, header, server_response, expectation
    ):
        with expectation:
            response = await ac.get("/api/users/me", headers=header)
            assert response.status_code == 200
            assert response.json() == server_response

    @staticmethod
    @pytest.mark.parametrize(
        "user_id, header, server_response, expectation",
        [
            (
                1,
                {"api-key": "test0"},
                {
                    "result": True,
                    "user": {
                        "id": 1,
                        "name": "Тест0",
                        "followers": [{"id": 2, "name": "Тест1"}],
                        "following": [],
                    },
                },
                not_raises(),
            ),
            (
                2,
                {"api-key": "test1"},
                {
                    "result": True,
                    "user": {
                        "id": 2,
                        "name": "Тест1",
                        "followers": [],
                        "following": [{"id": 1, "name": "Тест0"}],
                    },
                },
                not_raises(),
            ),
            (
                1,
                {"api-key": "test100"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
            (
                1,
                {},
                {
                    "result": False,
                    "error_type": "Header error",
                    "error_message": "There is no header in the request",
                },
                not_raises(),
            ),
        ],
    )
    async def test_get_other_user_data(
        ac: AsyncClient, user_id, header, server_response, expectation
    ):
        with expectation:
            response = await ac.get(f"/api/users/{user_id}", headers=header)
            assert response.status_code == 200
            assert response.json() == server_response

    @staticmethod
    @pytest.mark.parametrize(
        "user_id, header, server_response, expectation",
        [
            (1, {"api-key": "test1"}, {"result": True}, not_raises()),
            (
                1,
                {"api-key": "test0"},
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "A user cannot unsubscribe to himself",
                },
                not_raises(),
            ),
            (
                100,
                {"api-key": "test0"},
                {
                    "result": False,
                    "error_type": "User id error",
                    "error_message": "User with id: 100 not found",
                },
                not_raises(),
            ),
            (
                2,
                {"api-key": "test100"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
            (
                "str",
                {"api-key": "test1"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
            (
                4,
                {"not key": "test1"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
        ],
    )
    async def test_unfollow(
        ac: AsyncClient, user_id, header, server_response, expectation
    ):
        with expectation:
            response = await ac.delete(
                f"/api/users/{user_id}/follow", headers=header
            )
            assert response.status_code == 200
            assert response.json() == server_response
