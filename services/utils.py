"""
Module providing utility functions and decorators for handling API operations
and exceptions.
"""

from functools import wraps
from io import BytesIO

from fastapi import Depends, Header, UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import logger
from services.database.db_connect import get_async_session
from services.database.models import User
from services.response_schema import ExceptionSchema


def handle_exceptions(func):
    """
    Decorator to handle exceptions within async functions and return an
    ExceptionSchema on failure.

    Args:
        func: The async function to decorate.

    Returns:
        A wrapped async function that catches exceptions and logs them,
        returning an ExceptionSchema.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            logger.exception(
                f"func:{func.__name__}, " f"error: {e.__class__.__name__}"
            )
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                }
            )

    return wrapper


async def check_user(
    api_key: str = Header(None),
    session: AsyncSession = Depends(get_async_session),
) -> User | ExceptionSchema:
    """
    Validate the API key and retrieve user data asynchronously.

    Args:
        api_key (str): The API key provided in the request header.
        session (AsyncSession): The asynchronous session object for database
        operations.

    Returns:
        Union[User, ExceptionSchema]: Returns a User object if the API key is
        valid and user data is found, otherwise returns an ExceptionSchema
        with details of the error.
    """
    if api_key:
        user = await session.execute(
            select(User).filter(User.api_key == api_key)
        )
        user_data = user.scalar()
        if user_data is not None:
            return user_data
        else:
            return ExceptionSchema.parse_obj(
                {
                    "result": False,
                    "error_type": "Not authorize",
                    "error_message": f"You account not in database",
                }
            )
    else:
        return ExceptionSchema.parse_obj(
            {
                "result": False,
                "error_type": "Header error",
                "error_message": "There is no header in the request",
            }
        )


async def compress_image(
    image: UploadFile,
    quality=75,
) -> UploadFile:
    """
    Compresses an image file asynchronously.

    Args:
        image (UploadFile): The image file received as an UploadFile.
        quality (int, optional): The JPEG quality level for compression
        (default is 75).

    Returns:
        UploadFile: Returns a compressed image file as an UploadFile object.
    """
    original_size = image.size / (1024 * 1024)
    logger.debug(f"Original file size: {original_size:.2f} MB")
    contents = await image.read()
    original_image = Image.open(BytesIO(contents))
    original_image = original_image.convert("RGB")

    original_width, original_height = original_image.size
    logger.debug(f"Original resolution: {original_width}x{original_height}")

    if original_width > 1920 or original_height > 1080:
        ratio = min(1920 / original_width, 1080 / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        original_image = original_image.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )
    buffer = BytesIO()
    original_image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    compressed_image = UploadFile(filename=image.filename, file=buffer)

    new_width, new_height = original_image.size
    logger.debug(f"New resolution: {new_width}x{new_height}")
    new_size_mb = len(buffer.getvalue()) / (1024 * 1024)
    logger.debug(f"New file size: {new_size_mb:.2f} MB")

    return compressed_image
