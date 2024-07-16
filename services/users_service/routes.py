"""
Module for managing users in a FastAPI application.

This module provides routes for operations such as following a user,
unfollowing a user, getting current user data, and retrieving data for a
specific user.
All operations are protected by user verification using the check_user
dependency.
"""

from fastapi import APIRouter, Depends

from services.response_schema import ExceptionSchema, ResponseSchema
from services.users_service.service import UserService
from services.utils import check_user

user_router = APIRouter(prefix="/api/users", tags=["Users Service"])


@user_router.post(
    "/{user_id}/follow", response_model=ResponseSchema | ExceptionSchema
)
async def follow_user(
    user_id: int, user=Depends(check_user), service: UserService = Depends()
):
    """
    Follow a user.

    Args:
        user_id (int): ID of the user to follow.
        user: The current user, verified by the check_user dependency.
        service (UserService): The user service dependency.

    Returns:
        ResponseSchema or ExceptionSchema: The response schema or exception
        schema based on the operation result.
    """
    return (
        await service.add_follow(user_id=user_id, user=user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@user_router.delete(
    "/{user_id}/follow", response_model=ResponseSchema | ExceptionSchema
)
async def unfollow_user(
    user_id: int, user=Depends(check_user), service: UserService = Depends()
):
    """
    Unfollow a user.

    Args:
        user_id (int): ID of the user to unfollow.
        user: The current user, verified by the check_user dependency.
        service (UserService): The user service dependency.

    Returns:
        ResponseSchema or ExceptionSchema: The response schema or exception
        schema based on the operation result.
    """
    return (
        await service.unfollow_user(user_id=user_id, user=user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@user_router.get("/me")
async def get_user_data(
    user=Depends(check_user), service: UserService = Depends()
):
    """
    Get current user data.

    Args:
        user: The current user, verified by the check_user dependency.
        service (UserService): The user service dependency.

    Returns:
        ResponseSchema or ExceptionSchema: The response schema or exception
        schema based on the operation result.
    """
    return (
        await service.get_user_data(user=user)
        if not isinstance(user, ExceptionSchema)
        else user
    )


@user_router.get("/{user_id}")
async def get_user_data(
    user_id: int, user=Depends(check_user), service: UserService = Depends()
):
    """
    Get data for a specific user.

    Args:
        user_id (int): ID of the user to retrieve data for.
        user: The current user, verified by the check_user dependency.
        service (UserService): The user service dependency.

    Returns:
        ResponseSchema or ExceptionSchema: The response schema or exception
        schema based on the operation result.
    """
    return (
        await service.find_user(user_id=user_id)
        if not isinstance(user, ExceptionSchema)
        else user
    )
