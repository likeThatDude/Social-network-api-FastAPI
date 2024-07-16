"""
Provides API endpoints for managing media files using FastAPI's APIRouter.

This module defines routes for uploading media files and utilizes
MediaService for handling
file upload operations. It includes logging user actions and handling
exceptions gracefully.

Dependencies:
    - APIRouter: FastAPI's router for defining API endpoints.
    - Depends: Dependency injection in FastAPI for handling user
      authentication and service dependencies.
    - File, UploadFile: FastAPI's components for handling file uploads.
    - logger: Configured logger instance for logging user actions and errors.
    - MediaResponseSchema, ExceptionSchema: Response schemas for defining
      API responses.
    - MediaService: Service class for managing media files.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from config import logger
from services.media_service.schemas import MediaResponseSchema
from services.media_service.service import MediaService
from services.response_schema import ExceptionSchema
from services.utils import check_user

media_router = APIRouter(prefix="/api/medias", tags=["Media service"])


@media_router.post("", response_model=MediaResponseSchema | ExceptionSchema)
async def add_pictures(
    user=Depends(check_user),
    file: UploadFile = File(...),
    service: MediaService = Depends(),
):
    """
    Handles HTTP POST requests for uploading media files to the server.

    This endpoint logs user actions and delegates file upload operations to
    MediaService.

    Dependencies:
        - user: User authentication dependency provided by check_user.
        - file: UploadFile parameter representing the file to be uploaded.
        - service: MediaService dependency for handling file upload operations.

    Returns:
        - MediaResponseSchema or ExceptionSchema: Returns MediaResponseSchema
        if upload is successful,
          or ExceptionSchema if user authentication fails.
    """
    logger.info(
        f"The user is trying to upload an image: "
        f"User: {user.id=}, {user.name=}, {user.api_key=};"
        f"File: {file.filename};"
        f"File size: {file.size / (1024 * 1024):.2f} Mb."
    )
    return (
        await service.upload_picture(file)
        if not isinstance(user, ExceptionSchema)
        else user
    )
