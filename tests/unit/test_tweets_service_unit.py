from contextlib import nullcontext as not_raises
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.database.models import Picture, Tweet, User
from services.redis.redis_service import redis
from services.response_schema import ExceptionSchema, ResponseSchema
from services.tweets_service.schemas import (
    AllTweetsSchema,
    ReadyAllData,
    ResponseTweetsSchema,
    UserSchema,
)
from services.tweets_service.service import TweetsService
from services.utils import check_user

service = TweetsService()
session_mock = AsyncMock()
session_mock.add.return_value = None
session_mock.flush.return_value = None
session_mock.commit.return_value = None
session_mock.execute.return_value = None
session_mock.delete.return_value = None
service.session = session_mock


class TestTweetsServiceUnit:

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_data, user, response_data, expectation",
        [
            (
                {"tweet_data": "тесовая строка", "tweet_media_ids": [1, 2]},
                User(id=1, api_key="api-key", name="Тест"),
                ResponseTweetsSchema(result=True, tweet_id=1),
                not_raises(),
            ),
            (
                {
                    "tweet_data_fail": "тесовая строка",
                    "tweet_media_ids": [1, 2],
                },
                User(id=1, api_key="api-key", name="Тест"),
                ResponseTweetsSchema(result=True, tweet_id=1),
                pytest.raises(KeyError),
            ),
            (
                {"tweet_data": "тесовая строка"},
                User(id=1, api_key="api-key", name="Тест"),
                ResponseTweetsSchema(result=True, tweet_id=1),
                pytest.raises(KeyError),
            ),
            (
                {"tweet_data": 123, "tweet_media_ids": [1, 2]},
                User(id=1, api_key="api-key", name="Тест"),
                ResponseTweetsSchema(result=True, tweet_id=1),
                not_raises(),
            ),
            (
                {"tweet_data": "тесовая строка", "tweet_media_ids": [1, 2]},
                "fail data",
                ResponseTweetsSchema(result=True, tweet_id=1),
                pytest.raises(AttributeError),
            ),
        ],
    )
    async def test_create_tweet(
        mocker, tweet_data, user, response_data, expectation
    ):
        with expectation:
            mocker.patch(
                "services.database.models.Tweet.from_schema",
                return_value=Tweet(
                    id=1,
                    content=tweet_data["tweet_data"],
                    tweet_media_ids=tweet_data["tweet_media_ids"],
                    user_id=user.id,
                    likes_count=10,
                ),
            )

            response = await service.create_tweet(tweet_data, user)
            assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_id, user, tweet_data, response_data, expectation",
        [
            (
                1,
                User(id=1, api_key="api-key", name="Тест"),
                Tweet(
                    id=1,
                    content="тест контент",
                    tweet_media_ids=[1, 2, 3],
                    user_id=1,
                    likes_count=10,
                ),
                ResponseSchema(result=True),
                not_raises(),
            ),
            (
                1,
                User(id=1, api_key="api-key", name="Тест"),
                None,
                ExceptionSchema(
                    result=False,
                    error_type="Data error",
                    error_message="This user doesn't have a tweet wits id: 1",
                ),
                not_raises(),
            ),
        ],
    )
    async def test_delete_tweet(
        mocker, tweet_id, user, tweet_data, response_data, expectation
    ):
        with expectation:
            session_mock.execute.return_value = MagicMock(
                scalar=MagicMock(return_value=tweet_data)
            )
            mocker.patch(
                "services.media_service.s3client.S3Client.delete_file",
                return_value=None,
            )
            response = await service.delete_tweet(tweet_id, user)
            assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_id, user, tweet_data, response_data, expectation",
        [
            (
                1,
                User(id=23, api_key="api-key", name="Тест"),
                Tweet(
                    id=31,
                    content="тест контент",
                    tweet_media_ids=[1, 2, 3],
                    user_id=1,
                    likes_count=10,
                ),
                ResponseSchema(result=True),
                not_raises(),
            ),
            (
                22,
                User(id=22, api_key="api-key", name="Тест"),
                None,
                ExceptionSchema(
                    result=False,
                    error_type="Tweet error",
                    error_message="Tweet wits id: 22 not found",
                ),
                not_raises(),
            ),
        ],
    )
    async def test_add_like(
        tweet_id, user, tweet_data, response_data, expectation
    ):
        with expectation:
            session_mock.execute.return_value = MagicMock(
                scalar=MagicMock(return_value=tweet_data)
            )
            response = await service.add_like(tweet_id, user)
            assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_id, user, like_data, tweet_data, response_data, expectation",
        [
            (
                1,
                User(id=23, api_key="api-key", name="Тест"),
                True,
                Tweet(
                    id=31,
                    content="тест контент",
                    tweet_media_ids=[1, 2, 3],
                    user_id=1,
                    likes_count=10,
                ),
                ResponseSchema(result=True),
                not_raises(),
            ),
            (
                1,
                User(id=23, api_key="api-key", name="Тест"),
                False,
                Tweet(
                    id=31,
                    content="тест контент",
                    tweet_media_ids=[1, 2, 3],
                    user_id=1,
                    likes_count=10,
                ),
                ExceptionSchema(
                    result=False,
                    error_type="Like error",
                    error_message="This user has not liked this tweet",
                ),
                not_raises(),
            ),
        ],
    )
    async def test_delete_like(
        tweet_id, user, like_data, tweet_data, response_data, expectation
    ):
        with expectation:
            delete_mock = MagicMock()
            delete_mock.rowcount = 1 if like_data else 0
            select_mock = MagicMock()
            select_mock.scalar.return_value = tweet_data
            service.session.execute.side_effect = (
                [delete_mock, select_mock] if like_data else [delete_mock]
            )
            response = await service.delete_like(tweet_id, user)
            assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "tweet_data, response_data, expectation",
        [
            (
                [
                    Tweet(
                        id=31,
                        content="тест контент",
                        tweet_media_ids=[1, 2, 3],
                        user_id=1,
                        attachments=[
                            Picture(
                                id=1,
                                link="http://example.com/test.png",
                            )
                        ],
                        author=User(id=22, api_key="api-key", name="Тест"),
                        likes_count=10,
                    )
                    for i in range(2)
                ],
                ReadyAllData(
                    result=True,
                    tweets=[
                        AllTweetsSchema(
                            id=31,
                            content="тест контент",
                            attachments=["http://example.com/test.png"],
                            author=UserSchema(id=22, name="Тест"),
                            likes=[],
                        ),
                        AllTweetsSchema(
                            id=31,
                            content="тест контент",
                            attachments=["http://example.com/test.png"],
                            author=UserSchema(id=22, name="Тест"),
                            likes=[],
                        ),
                    ],
                ),
                not_raises(),
            ),
            (
                None,
                ExceptionSchema(
                    result=False,
                    error_type="Tweet error",
                    error_message="No tweets in the database",
                ),
                not_raises(),
            ),
        ],
    )
    async def test_get_tweets(tweet_data, response_data, expectation):
        with expectation:
            await redis.delete("get_tweets")
            select_mock = MagicMock()
            select_mock.scalars.return_value = tweet_data
            service.session.execute.side_effect = [select_mock]
            response = await service.get_tweets()
            assert response == response_data

    @staticmethod
    @pytest.mark.parametrize(
        "key, user, response_data, expectation",
        [
            (
                "api-key",
                User(id=22, api_key="api-key", name="Тест"),
                User(),
                not_raises(),
            ),
            (
                "api-key",
                None,
                ExceptionSchema(
                    result=False,
                    error_type="Not authorize",
                    error_message="You account not in database",
                ),
                not_raises(),
            ),
        ],
    )
    async def test_check_user(key, user, response_data, expectation):
        with expectation:
            select_mock = MagicMock()
            select_mock.scalar.return_value = user
            service.session.execute.side_effect = [select_mock]
            response = await check_user(key, session_mock)
            if user:
                assert isinstance(response, User)
            else:
                assert response == response_data
