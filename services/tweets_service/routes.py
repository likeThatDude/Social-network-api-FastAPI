"""
Defines API endpoints for managing tweets using FastAPI's APIRouter.

This module provides endpoints for creating, retrieving, deleting tweets, and
managing tweet likes.
"""

from typing import Union

from fastapi import APIRouter, Depends

from services.response_schema import ExceptionSchema, ResponseSchema
from services.tweets_service.schemas import (
    ReadyAllData,
    ResponseTweetsSchema,
    TweetSchema,
)
from services.tweets_service.service import TweetsService
from services.utils import check_user

tweets_router = APIRouter(prefix="/api/tweets", tags=["Tweets service"])


@tweets_router.post(
    "", response_model=Union[ResponseTweetsSchema, ExceptionSchema]
)
async def post_tweets(
    tweets_data: TweetSchema,
    user=Depends(check_user),
    service: TweetsService = Depends(),
):
    """
    Creates a new tweet based on provided data.

    Args:
        tweets_data (TweetSchema): Data representing the new tweet.
        user: Authenticated user information.
        service (TweetsService): Instance of the tweet service.

    Returns:
        Union[ResponseTweetsSchema, ExceptionSchema]:
        - ResponseTweetsSchema: Data representing the newly created tweet.
        - ExceptionSchema: Error response if user authentication fails.
    """
    return (
        await service.create_tweet(tweets_data, user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@tweets_router.get("", response_model=ReadyAllData | ExceptionSchema)
async def get_user_tweets(
    user=Depends(check_user), service: TweetsService = Depends()
):
    """
    Retrieves all tweets.

    Args:
        user: Authenticated user information.
        service (TweetsService): Instance of the tweet service.

    Returns:
        Union[ReadyAllData, ExceptionSchema]:
        - ReadyAllData: Data representing all tweets.
        - ExceptionSchema: Error response if user authentication fails.
    """
    return (
        await service.get_tweets()
        if not isinstance(user, ExceptionSchema)
        else user
    )


@tweets_router.delete(
    "/{tweet_id}", response_model=Union[ResponseSchema, ExceptionSchema]
)
async def delete_tweet(
    tweet_id: int, user=Depends(check_user), service: TweetsService = Depends()
):
    """
    Deletes a tweet by its ID.

    Args:
        tweet_id (int): ID of the tweet to delete.
        user: Authenticated user information.
        service (TweetsService): Instance of the tweet service.

    Returns:
        Union[ResponseSchema, ExceptionSchema]:
        - ResponseSchema: Success response after deleting the tweet.
        - ExceptionSchema: Error response if user authentication fails.
    """
    return (
        await service.delete_tweet(tweet_id, user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@tweets_router.post(
    "/{tweet_id}/likes", response_model=Union[ResponseSchema, ExceptionSchema]
)
async def add_like(
    tweet_id: int, user=Depends(check_user), service: TweetsService = Depends()
):
    """
    Adds a like to a tweet by its ID.

    Args:
        tweet_id (int): ID of the tweet to like.
        user: Authenticated user information.
        service (TweetsService): Instance of the tweet service.

    Returns:
        Union[ResponseSchema, ExceptionSchema]:
        - ResponseSchema: Success response after adding a like to the tweet.
        - ExceptionSchema: Error response if user authentication fails.
    """
    return (
        await service.add_like(tweet_id, user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@tweets_router.delete(
    "/{tweet_id}/likes", response_model=Union[ResponseSchema, ExceptionSchema]
)
async def delete_like(
    tweet_id: int, user=Depends(check_user), service: TweetsService = Depends()
):
    """
    Deletes a like from a tweet by its ID.

    Args:
        tweet_id (int): ID of the tweet to unlike.
        user: Authenticated user information.
        service (TweetsService): Instance of the tweet service.

    Returns:
        Union[ResponseSchema, ExceptionSchema]:
        - ResponseSchema: Success response after deleting the like from the tweet.
        - ExceptionSchema: Error response if user authentication fails.
    """
    return (
        await service.delete_like(tweet_id, user)
        if not isinstance(user, ExceptionSchema)
        else user
    )
