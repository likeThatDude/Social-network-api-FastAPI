"""
Provides asynchronous methods for handling media upload operations,
including file extension validation, file processing, uploading to S3,
and database integration.

Dependencies:
    - Depends: Dependency injection for obtaining an asynchronous database
    session.
    - UploadFile: FastAPI's component for uploading files.
    - AsyncSession: Asynchronous session for interacting with the database.
    - ALLOWED_EXTENSIONS_FOR_FILE: List of allowed file extensions.
    - logger: Configured logger instance for logging actions and errors.
    - settings: Configuration settings for accessing S3 storage and other
    parameters.
    - s3client: Instance of S3Client for interacting with AWS S3.
    - compress_image: Asynchronous function for compressing images.
    - handle_exceptions: Decorator for handling exceptions gracefully.

Classes:
    - MediaService:
        Service class for handling media upload operations asynchronously.

Methods:
    - _get_file_extension(file_name: str) -> str:
        Returns the file extension from its name.

    - async _write_file(file: UploadFile) ->
    DataBaseLoadSchema | ExceptionSchema:
        Asynchronously writes the uploaded file to the server.

    - async _load_into_the_database(file_url: DataBaseLoadSchema) ->
    MediaResponseSchema | ExceptionSchema:
        Asynchronously loads file data into the database.

    - async upload_picture(file: UploadFile) ->
    MediaResponseSchema | ExceptionSchema:
        Asynchronously processes and uploads an image to the server and
        database.
"""

import datetime
import uuid
from pathlib import Path

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config import ALLOWED_EXTENSIONS_FOR_FILE, logger, settings
from services.database.db_connect import get_async_session
from services.database.models import Picture
from services.s3.s3client import s3client
from services.media_service.schemas import (
    DataBaseLoadSchema,
    MediaResponseSchema,
)
from services.response_schema import ExceptionSchema
from services.utils import compress_image, handle_exceptions


class MediaService:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    @staticmethod
    @logger.catch
    def _get_file_extension(file_name: str) -> str:
        """
        Returns the file extension from its name.

        Args:
            file_name (str): The name of the file.

        Returns:
            str: The file extension in lowercase, without the dot.
        """
        logger.debug(
            f"Start _get_file_extension function with file name: {file_name}"
        )
        return Path(file_name).suffix[1:].lower()

    @staticmethod
    @logger.catch
    async def _write_file(
        file: UploadFile,
    ) -> DataBaseLoadSchema | ExceptionSchema:
        """
        Asynchronously writes the uploaded file to the server.

        Args:
            file (UploadFile): The uploaded file.

        Returns:
            Union[DataBaseLoadSchema, ExceptionSchema]:
            An object containing data about the uploaded file
            if successful, otherwise an object containing error information.

        Note:
            The file is uploaded to an S3 storage.
        """
        try:
            logger.debug(f"Write file: {file.filename}")
            link = await s3client.upload_file(file, file.filename)
            logger.debug(f"Entry completed: {file.filename}")
            return DataBaseLoadSchema.parse_obj({"link": link})
        except Exception as e:
            return ExceptionSchema(
                result=False, error_type=type(e).__name__, error_message=str(e)
            )

    @logger.catch()
    async def _load_into_the_database(
        self, file_url: DataBaseLoadSchema
    ) -> MediaResponseSchema | ExceptionSchema:
        """
        Asynchronously loads file data into the database.

        Args:
            file_url (DataBaseLoadSchema): Data about the uploaded file.

        Returns:
            MediaResponseSchema:
            An object with the result of the upload to the database.
        """
        try:
            link = Picture.from_schema(file_url)
            logger.debug(f"Sending a link: {link=} to the database")
            self.session.add(link)
            await self.session.flush()
            picture_id = link.id
            await self.session.commit()
            logger.info(f"Sending complete, id into database: {picture_id}")
            return MediaResponseSchema(result=True, media_id=picture_id)
        except Exception as e:
            return ExceptionSchema(
                result=False, error_type=type(e).__name__, error_message=str(e)
            )

    @handle_exceptions
    @logger.catch
    async def upload_picture(
        self, file: UploadFile
    ) -> MediaResponseSchema | ExceptionSchema:
        """
        Asynchronously processes and uploads an image
        to the server and database.

        Args:
            file (UploadFile): The uploaded image.

        Returns:
            MediaResponseSchema | ExceptionSchema:
            The upload result or error information.
        """

        try:
            logger.debug(
                f"Start upload_picture function with file: {file.filename}"
            )
            file_extension = self._get_file_extension(file.filename)
            logger.debug(
                f"Termination of the _get_file_extension "
                f"function with the result: {file_extension}"
            )
            if file_extension not in ALLOWED_EXTENSIONS_FOR_FILE:
                logger.info(f"Invalid file extension: {file_extension}")
                return ExceptionSchema(
                    result=False,
                    error_type="Authorization failed",
                    error_message="Authentication failed: "
                    "invalid credentials. Status code: 415",
                )
            else:
                file.filename = (
                    f"{settings.S3_TWEETS_MEDIA_FOLDER}{str(uuid.uuid4())}-"
                    f"{datetime.datetime.now().date()}.{file_extension}"
                )
                file_compress = await compress_image(file)
                file_url = await self._write_file(file_compress)
                if isinstance(file_url, DataBaseLoadSchema):
                    return await self._load_into_the_database(file_url)
                else:
                    return file_url
        except Exception as e:
            return ExceptionSchema(
                result=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )
