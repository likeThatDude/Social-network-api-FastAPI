"""
Module for defining user data schemas using Pydantic.

This module provides Pydantic models to structure and validate the data related
to users, including their ID, name, and their followers and following lists.
"""

from pydantic import BaseModel, ConfigDict

from services.response_schema import ResponseSchema
from services.tweets_service.schemas import UserSchema


class UserDataSchema(BaseModel):
    """
    Schema representing user data.

    Attributes:
        id (int): The unique identifier of the user.
        name (str): The name of the user.
        followers (list[UserSchema] | None): A list of users following this
        user, or None if there are no followers.
        following (list[UserSchema] | None): A list of users this user is
        following, or None if not following anyone.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    name: str
    followers: list[UserSchema] | None
    following: list[UserSchema] | None


class ResponseUserDataSchema(ResponseSchema):
    """
    Schema representing the response containing user data.

    Attributes:
        result (bool): The result status of the response.
        user (UserDataSchema): The user data contained in the response.
    """

    result: bool
    user: UserDataSchema
