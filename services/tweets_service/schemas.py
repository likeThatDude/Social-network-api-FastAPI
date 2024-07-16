"""
Module containing Pydantic schemas for representing data structures in the
application.

This module defines several Pydantic BaseModel classes for structured data
validation and serialization, including schemas for tweets, responses, users,
pictures, and aggregated tweet data.
"""

from pydantic import BaseModel, ConfigDict

from services.response_schema import ResponseSchema


class TweetSchema(BaseModel):
    """
    Schema representing data for creating a new tweet.

    Attributes:
        tweet_data (str): The content of the tweet.
        tweet_media_ids (list[int], optional): List of media IDs associated
        with the tweet.
    """

    tweet_data: str
    tweet_media_ids: list[int] | None = None


class ResponseTweetsSchema(ResponseSchema):
    """
    Schema representing the response for a tweet.

    Attributes:
        tweet_id (int): The ID of the tweet.
    """

    tweet_id: int


class UserSchema(BaseModel):
    """
    Base schema representing user information.

    Attributes:
        id (int): The user's ID.
        name (str): The user's name.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class UserLikeSchema(UserSchema):
    """
    Schema representing user information for likes.

    Inherits:
        UserSchema

    Attributes:
        id (int): The user's ID.
    """

    id: int


class PictureSchema(BaseModel):
    """
    Schema representing a picture link.

    Attributes:
        link (str): The URL link of the picture.
    """

    link: str


class AllTweetsSchema(BaseModel):
    """
    Schema representing all details of a tweet.

    Attributes:
        id (int): The ID of the tweet.
        content (str): The content of the tweet.
        attachments (list[str], optional): List of attachment URLs associated
          with the tweet.
        author (UserSchema): The author of the tweet.
        likes (list[UserSchema], optional): List of users who liked the tweet.
    """

    id: int
    content: str
    attachments: list[str] | None
    author: UserSchema
    likes: list[UserSchema] | None


class ReadyAllData(BaseModel):
    """
    Schema representing all tweets data.

    Attributes:
        result (bool): Result of the operation.
        tweets (list[AllTweetsSchema]): List of all tweets.
    """

    result: bool
    tweets: list[AllTweetsSchema]
