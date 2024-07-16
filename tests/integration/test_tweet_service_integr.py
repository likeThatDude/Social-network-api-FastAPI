from contextlib import nullcontext as not_raises

import pytest
from httpx import AsyncClient

from config import settings


@pytest.mark.order(2)
class TestTweetService:
    @staticmethod
    @pytest.mark.parametrize(
        "data, header, tweet_id, expectation",
        [
            (
                {"tweet_data": "Твит без медиа", "tweet_media_ids": []},
                {"api-key": "test0"},
                1,
                not_raises(),
            ),
            (
                {
                    "tweet_data": "Твит с тремя картинками",
                    "tweet_media_ids": [1, 2, 3],
                },
                {"api-key": "test0"},
                2,
                not_raises(),
            ),
            (
                {"tweet_data": "Попытка 2", "tweet_media_ids": []},
                {"api-key": "not valid key"},
                3,
                not_raises(),
            ),
            (
                {
                    "tweet_data": "Твит с одной картинкой",
                    "tweet_media_ids": [1],
                },
                {"api-key": "test0"},
                4,
                pytest.raises(AssertionError),
            ),
            (
                {"tweet_media_ids": []},
                {"api-key": "test0"},
                5,
                pytest.raises(AssertionError),
            ),
            (
                {"tweet_data": 1, "tweet_media_ids": []},
                {"api-key": "test0"},
                6,
                pytest.raises(AssertionError),
            ),
            (
                {"tweet_data": "Попытка 5", "tweet_media_ids": "string"},
                {"api-key": "test0"},
                7,
                pytest.raises(AssertionError),
            ),
        ],
    )
    async def test_create_tweets(
        ac: AsyncClient, data, header, expectation, tweet_id
    ):
        with expectation:
            response = await ac.post("/api/tweets", json=data, headers=header)
            if header["api-key"] == "test0":
                assert response.status_code == 200
                assert response.json() == {
                    "result": True,
                    "tweet_id": tweet_id,
                }
            if header["api-key"] == "not valid key":
                assert response.status_code == 200
                assert response.json() == {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                }

    @staticmethod
    @pytest.mark.parametrize(
        "header, expectation",
        [
            ({"api-key": "test0"}, not_raises()),
            ({"api-key": "not valid key"}, not_raises()),
            ({"invalid header": "test0"}, not_raises()),
        ],
    )
    async def test_get(ac: AsyncClient, header, expectation):
        with expectation:
            response = await ac.get("/api/tweets", headers=header)
            assert response.status_code == 200
            if "api-key" in header and header["api-key"] == "test0":
                assert response.json()["result"] is True
                assert len(response.json()["tweets"][0]["attachments"]) == 1
                assert (
                    type(response.json()["tweets"][0]["attachments"][0]) == str
                )
                assert response.json()["tweets"][0]["attachments"][
                    0
                ].startswith(settings.S3_URL)
                assert len(response.json()["tweets"][1]["attachments"]) == 3
                assert (
                    type(response.json()["tweets"][1]["attachments"][0]) == str
                )
                assert response.json()["tweets"][1]["attachments"][
                    0
                ].startswith(settings.S3_URL)
                assert (
                    type(response.json()["tweets"][1]["attachments"][1]) == str
                )
                assert response.json()["tweets"][1]["attachments"][
                    1
                ].startswith(settings.S3_URL)
                assert (
                    type(response.json()["tweets"][1]["attachments"][2]) == str
                )
                assert response.json()["tweets"][1]["attachments"][
                    2
                ].startswith(settings.S3_URL)
            if "api-key" in header and header["api-key"] == "not valid key":
                assert response.json() == {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                }
            if (
                "invalid header" in header
                and header["invalid header"] == "test0"
            ):
                assert response.json() == {
                    "result": False,
                    "error_type": "Header error",
                    "error_message": "There is no header in the request",
                }

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_id, header, server_response, expectation",
        [
            *[
                (1, {"api-key": f"test{i}"}, {"result": True}, not_raises())
                for i in range(5)
            ],
            (
                1,
                {"api-key": "test0"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
            (2, {"api-key": "test1"}, {"result": True}, not_raises()),
            (
                4,
                {"api-key": "test1"},
                {
                    "result": False,
                    "error_type": "Tweet error",
                    "error_message": "Tweet wits id: 4 not found",
                },
                not_raises(),
            ),
            (
                3,
                {"api-key": "not register user"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
        ],
    )
    async def test_add_like(
        ac: AsyncClient, tweet_id, header, server_response, expectation
    ):
        with expectation:
            response = await ac.post(
                f"/api/tweets/{tweet_id}/likes", headers=header
            )
            assert response.status_code == 200
            assert response.json() == server_response

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_id, header, server_response, expectation",
        [
            *[
                (1, {"api-key": f"test{i}"}, {"result": True}, not_raises())
                for i in range(5)
            ],
            (
                1,
                {"api-key": "test0"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
            (2, {"api-key": "test1"}, {"result": True}, not_raises()),
            (
                "str",
                {"api-key": "test1"},
                {"result": True},
                pytest.raises(AssertionError),
            ),
            (
                4,
                {"api-key": "test1"},
                {
                    "result": False,
                    "error_type": "Like error",
                    "error_message": "This user has not liked this tweet",
                },
                not_raises(),
            ),
            (
                3,
                {"api-key": "not register user"},
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": "You account not in database",
                },
                not_raises(),
            ),
        ],
    )
    async def test_delete_like(
        ac: AsyncClient, tweet_id, header, server_response, expectation
    ):
        with expectation:
            response = await ac.delete(
                f"/api/tweets/{tweet_id}/likes", headers=header
            )
            assert response.status_code == 200
            assert response.json() == server_response

    @staticmethod
    @pytest.mark.order(4)
    @pytest.mark.parametrize(
        "header, tweet_id, expectation",
        [
            ({"api-key": "test0"}, 1, not_raises()),
            ({"api-key": "test0"}, 2, not_raises()),
            ({"api-key": "test0"}, 3, not_raises()),
        ],
    )
    async def test_del_tweet(ac: AsyncClient, header, tweet_id, expectation):
        response = await ac.delete(f"/api/tweets/{tweet_id}", headers=header)
        assert response.status_code == 200
        assert response.json() == {"result": True}
