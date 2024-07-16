"""
Module defining SQLAlchemy ORM models for a social media application.

This module contains SQLAlchemy models representing various entities used in
the application, including users, tweets, pictures, likes, subscriptions,
and media attachments.

Models:
- `User`: Represents a user of the social media platform.
- `Tweet`: Represents a tweet posted by a user, with optional media attachments
and likes.
- `Picture`: Represents a picture attachment to a tweet.
- `Like`: Represents a like given by a user to a tweet.
- `Subscription`: Represents a subscription relationship between users.
- `Media`: Represents a link between tweets and pictures.

Usage:
- Each model class is derived from the `Base` class, which provides the common
attributes and mappings.
- Relationships between models are established using SQLAlchemy's
`relationship` directive.
- Class methods like `from_schema` are provided for creating instances from
external data schemas.

Dependencies:
- Requires SQLAlchemy for database interaction and schema management.

Note:
- This module assumes a PostgreSQL database backend configured in the
`db_connect` module.
- For asynchronous operations, ensure proper configuration and usage of async
session management.

"""

from datetime import datetime

from sqlalchemy import (
    ARRAY,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.db_connect import Base
from services.media_service.schemas import DataBaseLoadSchema
from services.tweets_service.schemas import TweetSchema


class User(Base):
    """
    Represents a user in the application with various
    attributes and relationships.

    Attributes:
        id (int): The unique identifier for the user
          (auto-incremented primary key).
        api_key (str): The API key associated with the user.
        name (str): The name of the user.
        tweets (list[Tweet]): Relationship mapping to tweets
          authored by the user.
        tweets_like (list[Tweet]): Relationship mapping to tweets liked
          by the user.
        following (list[User]): Relationship mapping to users followed
          by this user.
        followers (list[User]): Relationship mapping to users following
          this user.
    """

    __table_args__ = (
        Index('ix_user_api_key', 'api_key'),
    )

    id: Mapped[int] = mapped_column(
        autoincrement=True, primary_key=True, nullable=False
    )
    api_key: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        unique=True
    )
    name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False
    )
    tweets: Mapped[list["Tweet"]] = relationship(
        back_populates="author"
    )
    tweets_like: Mapped[list["Tweet"]] = relationship(
        back_populates="likes",
        secondary="likes"
    )
    following: Mapped[list["User"]] = relationship(
        back_populates="followers",
        secondary="subscriptions",
        primaryjoin="User.id == Subscription.subscriber_id",
        secondaryjoin="User.id == Subscription.subscribed_to_id",
        foreign_keys="[Subscription.subscriber_id, "
                     "Subscription.subscribed_to_id]",
    )
    followers: Mapped[list["User"]] = relationship(
        back_populates="following",
        secondary="subscriptions",
        primaryjoin="User.id == Subscription.subscribed_to_id",
        secondaryjoin="User.id == Subscription.subscriber_id",
        foreign_keys="[Subscription.subscriber_id, "
                     "Subscription.subscribed_to_id]",
    )


class Tweet(Base):
    """
    Represents a tweet in the application with various attributes
    and relationships.

    Attributes:
        id (int): The unique identifier for the tweet
          (auto-incremented primary key).
        content (str): The content of the tweet.
        tweet_media_ids (list[int]): List of media IDs associated with the
          tweet.
        attachments (list[Picture]): Relationship mapping to pictures
          attached to the tweet.
        user_id (int): The ID of the user who authored the tweet.
        likes_count (int): The count of likes received by the tweet.
        author (User): Relationship mapping to the author of the tweet.
        likes (list[User]): Relationship mapping to users who liked the tweet.
    """

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        nullable=True
    )
    tweet_media_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=True
    )
    attachments: Mapped[list["Picture"]] = relationship(
        back_populates="tweet",
        secondary="medias"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",
                   ondelete="CASCADE"),
        nullable=False
    )
    likes_count: Mapped[int] = mapped_column(
        nullable=True,
        default=0)
    author: Mapped["User"] = relationship(
        back_populates="tweets"
    )
    likes: Mapped[list["User"]] = relationship(
        back_populates="tweets_like",
        secondary="likes"
    )

    @classmethod
    def from_schema(cls, schema: TweetSchema):
        """
        Create a Tweet object from a schema object.

        Args:
            schema (TweetSchema): The schema containing tweet data.

        Returns:
            Tweet: An instance of the Tweet class.
        """
        return cls(
            content=schema.tweet_data,
            tweet_media_ids=schema.tweet_media_ids
        )


class Picture(Base):
    """
    Represents a picture attached to a tweet with its attributes
    and relationships.

    Attributes:
        id (int): The unique identifier for the picture
          (auto-incremented primary key).
        link (str): The link to the picture.
        tweet (Tweet): Relationship mapping to the tweet this picture is
          attached to.
    """

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        nullable=False
    )
    link: Mapped[str] = mapped_column(
        nullable=False
    )
    tweet: Mapped["Tweet"] = relationship(
        back_populates="attachments",
        secondary="medias"
    )

    @classmethod
    def from_schema(cls, data: DataBaseLoadSchema) -> "Picture":
        """
        Create a Picture object from schema data.

        Args:
            data (DataBaseLoadSchema): The schema data containing picture
              details.

        Returns:
            Picture: An instance of the Picture class.
        """
        return cls(
            link=data.link
        )


class Like(Base):
    """
    Represents a like relationship between a user and a tweet.

    Attributes:
        user_id (int): The ID of the user who liked the tweet.
        tweet_id (int): The ID of the tweet that was liked.
    """

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True,
    )
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True
    )

    __table_args__ = (UniqueConstraint("user_id", "tweet_id"),)


class Subscription(Base):
    """
    Represents a subscription relationship between two users.

    Attributes:
        subscriber_id (int): The ID of the user who is subscribing.
        subscribed_to_id (int): The ID of the user who is being subscribed to.
        created_at (datetime): The timestamp when the subscription was created.
    """

    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True
    )
    subscribed_to_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(
            timezone=True
        )
    )


class Media(Base):
    """
    Represents a media attachment to a tweet.

    Attributes:
        tweet_id (int): The ID of the tweet the media is attached to.
        picture_id (int): The ID of the picture being attached.
    """

    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True
    )
    picture_id: Mapped[int] = mapped_column(
        ForeignKey("pictures.id",
                   ondelete="CASCADE"
                   ),
        primary_key=True
    )
