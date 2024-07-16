"""
Module providing services for managing tweets and related operations.

Includes:
- TweetsService: Service class for creating, deleting, liking, and fetching
tweets.

Uses SQLAlchemy for database interactions, FastAPI for web framework,
and Redis for caching tweet data.
"""

import json

from fastapi import Depends
from sqlalchemy import and_, delete, desc, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from services.database.db_connect import get_async_session
from services.database.models import Like, Media, Tweet, User
from services.s3.s3client import s3client
from services.redis.redis_service import redis
from services.response_schema import ExceptionSchema, ResponseSchema
from services.tweets_service.schemas import (
    AllTweetsSchema,
    ReadyAllData,
    ResponseTweetsSchema,
    TweetSchema,
)
from services.utils import handle_exceptions


class TweetsService:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    @handle_exceptions
    async def create_tweet(
        self, tweet_data: TweetSchema, user: User
    ) -> ResponseTweetsSchema | ExceptionSchema:
        """
        Create a new tweet and associate it with the specified user.

        Parameters:
            tweet_data (TweetSchema): The data for the tweet to be created.
            user (User): The user who is creating the tweet.

        Returns:
            ResponseTweetsSchema | ExceptionSchema:
            A response containing the result of the operation,
            including the ID of the created tweet, or an exception schema
            if an error occurred.

        Raises:
            ExceptionSchema: If there is an error during the creation process.
        """
        tweet = Tweet.from_schema(tweet_data)
        tweet.user_id = user.id
        self.session.add(tweet)
        await self.session.flush()
        tweet_id = tweet.id
        if tweet.tweet_media_ids:
            picture_data = [
                {"tweet_id": tweet_id, "picture_id": pic_id}
                for pic_id in tweet.tweet_media_ids
            ]
            await self.session.execute(insert(Media).values(picture_data))
        await self.session.commit()
        await redis.delete(settings.REDIS_TWEETS_CACHE)
        return ResponseTweetsSchema.parse_obj(
            {"result": True, "tweet_id": tweet_id}
        )

    @handle_exceptions
    async def delete_tweet(
        self, tweet_id: int, user: User
    ) -> ResponseSchema | ExceptionSchema:
        """
        Delete a tweet with the specified ID owned by the given user.

        Parameters:
            tweet_id (int): The ID of the tweet to be deleted.
            user (User): The user who owns the tweet.

        Returns:
            ResponseSchema | ExceptionSchema: A response containing the
            result of the operation,
            or an exception schema if an error occurred.

        Raises:
            ExceptionSchema:
            If the specified tweet does not exist or if the user
            is not the owner of the tweet.
        """
        query = await self.session.execute(
            select(Tweet)
            .options(selectinload(Tweet.attachments))
            .where(and_(Tweet.user_id == user.id, Tweet.id == tweet_id))
        )
        tweet_data = query.scalar()
        if tweet_data:
            if len(tweet_data.attachments) > 0:
                await s3client.delete_file(tweet_data.attachments)
            await self.session.delete(tweet_data)
            await self.session.commit()
            await redis.delete(settings.REDIS_TWEETS_CACHE)
            return ResponseSchema.parse_obj({"result": True})
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "Data error",
                    "error_message": f"This user doesn't have a tweet "
                    f"wits id: {tweet_id}",
                }
            )

    @handle_exceptions
    async def add_like(
        self, tweet_id: int, user: User
    ) -> ResponseSchema | ExceptionSchema:
        """
        Add a like to the specified tweet by the given user.

        Parameters:
            tweet_id (int): The ID of the tweet to like.
            user (User): The user who is liking the tweet.

        Returns:
            ResponseSchema | ExceptionSchema:
            A response containing the result of the operation,
            or an exception schema if an error occurred.

        Raises:
            ExceptionSchema: If the specified tweet does not exist.
        """
        tweet_data = await self.session.execute(
            select(Tweet).where(Tweet.id == tweet_id)
        )
        data = tweet_data.scalar()
        if data is not None:
            like = Like(user_id=user.id, tweet_id=data.id)
            data.likes_count += 1 if data.likes_count is not None else 1
            self.session.add(like)
            await self.session.commit()
            await redis.delete(settings.REDIS_TWEETS_CACHE)
            return ResponseSchema.parse_obj({"result": True})
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "Tweet error",
                    "error_message": f"Tweet wits id: {tweet_id} not found",
                }
            )

    @handle_exceptions
    async def delete_like(
        self, tweet_id: int, user: User
    ) -> ResponseSchema | ExceptionSchema:
        """
        Delete a like made by the specified user on the given tweet.

        Parameters:
            tweet_id (int): The ID of the tweet from which to delete the like.
            user (User): The user who is removing the like.

        Returns:
            ResponseSchema | ExceptionSchema: A response containing the
            result of the operation, or an exception schema
            if an error occurred.

        Raises:
            ExceptionSchema: If the specified tweet or like does not exist.
        """
        delete_tweet = await self.session.execute(
            delete(Like).where(
                and_(Like.tweet_id == tweet_id, Like.user_id == user.id)
            )
        )

        rowcount = delete_tweet.rowcount
        if rowcount != 0:
            tweet = await self.session.execute(
                select(Tweet).where(Tweet.id == tweet_id)
            )
            tweet_data = tweet.scalar()
            tweet_data.likes_count -= 1
            await self.session.commit()
            await redis.delete(settings.REDIS_TWEETS_CACHE)
            return ResponseSchema.parse_obj({"result": True})
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "Like error",
                    "error_message": f"This user has not liked this tweet",
                }
            )

    @handle_exceptions
    async def get_tweets(self) -> ReadyAllData | ExceptionSchema:
        """
        Fetches all tweets with additional information
        (author, likes, attachments).

        Parameters:
            None.

        Returns:
            ReadyAllData | ExceptionSchema:
            An `ReadyAllData` object containing the result of the
            operation and a list of tweets, or an `ExceptionSchema`
            object if an error occurred.

        Raises:
            ExceptionSchema: If no tweets are found.
        """
        # if limit == 0:
        cache_data = await redis.get(settings.REDIS_TWEETS_CACHE)
        if not cache_data:
            query = await self.session.execute(
                select(Tweet)
                .options(
                    selectinload(Tweet.author),
                    selectinload(Tweet.likes),
                    selectinload(Tweet.attachments),
                )
                .order_by(desc(Tweet.id))
            )
            tweets = query.scalars()
            if tweets:
                tweets_data = list()
                for tweet in tweets:
                    tweet_schema = AllTweetsSchema(
                        id=tweet.id,
                        content=tweet.content,
                        attachments=[
                            picture.link for picture in tweet.attachments
                        ],
                        author=tweet.author,
                        likes=tweet.likes,
                    )
                    tweets_data.append(tweet_schema)
                result = ReadyAllData.parse_obj(
                    {"result": True, "tweets": tweets_data}
                )
                tweets_data_json = json.dumps(result.dict())
                await redis.set(
                    settings.REDIS_TWEETS_CACHE, tweets_data_json, ttl=180
                )
                return result
            else:
                return ExceptionSchema.parse_obj(
                    {
                        "result": False,
                        "error_type": "Tweet error",
                        "error_message": f"No tweets in the database",
                    }
                )
        else:
            tweets_data = json.loads(cache_data)
            return tweets_data
