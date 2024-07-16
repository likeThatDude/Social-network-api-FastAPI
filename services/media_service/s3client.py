"""
Provides an interface for asynchronous interaction with an AWS S3 bucket
using aiobotocore.

This module allows you to upload, delete files, set lifecycle rules, and
manage S3 objects
While handling exceptions gracefully.

Dependencies:
    - aiobotocore: Asynchronous client library for AWS services.
    - aiohttp: Asynchronous HTTP client-server framework.
    - fastapi: Web framework for creating APIs using Python.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Union

from aiobotocore.session import get_session
from aiohttp import ClientError
from fastapi import File, UploadFile

from config import logger, settings
from services.utils import handle_exceptions


class S3Client:
    """
    Provides asynchronous methods to interact with an AWS S3 bucket,
    including file uploads, deletions,
    lifecycle rule management, and Celery-based file uploads.

    Attributes:
        config (dict): Configuration dictionary containing AWS access
        credentials and endpoint URL.
        bucket_name (str): Name of the AWS S3 bucket.
        session: aiobotocore session instance.
    """

    def __init__(self):
        """
        Initializes the S3Client instance with AWS credentials and endpoint
        URL from the settings module.
        """
        self.config = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "endpoint_url": settings.S3_URL,
        }
        self.bucket_name = settings.S3_BUCKET_NAME
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        """
        Asynchronous context manager to create an S3 client session.
        Yields:
            client: aiobotocore S3 client session.
        """
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    @handle_exceptions
    async def upload_file(
        self, upload_file: Union[UploadFile, File], object_name: str
    ):
        """
        Uploads a file to the AWS S3 bucket.

        Args:
            upload_file (Union[UploadFile, File]): The file to upload.
            object_name (str): The name of the object in the S3 bucket.

        Returns:
            str: URL of the uploaded file in the S3 bucket.
        """
        file_data = await upload_file.read()
        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                ContentType="content_type",
            )
        return f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/{object_name}"

    @handle_exceptions
    async def delete_file(self, pictures: list):
        """
        Deletes files from the AWS S3 bucket.

        Args:
            pictures (list): List of objects (pictures) to delete.
        """
        async with self.get_client() as client:
            for picture in pictures:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=f"{settings.S3_TWEETS_MEDIA_FOLDER}"
                    f"{picture.link.split('/')[-1]}",
                )

    @handle_exceptions
    async def send_rules(self, rules: dict):
        """
        Sets lifecycle rules for the AWS S3 bucket.

        Args:
            rules (dict): Dictionary containing lifecycle rules.
        """
        async with self.get_client() as client:
            await client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=rules,
            )

    @handle_exceptions
    async def get_lifecycle_rules(self):
        """
        Retrieves current lifecycle rules applied to the AWS S3 bucket.

        Returns:
            dict: Response containing lifecycle rules.
        """
        async with self.get_client() as client:
            response = await client.get_bucket_lifecycle_configuration(
                Bucket=self.bucket_name
            )
        return response

    @handle_exceptions
    async def set_lifecycle_rules(self, folder_prefix: str, days: int):
        """
        Sets new lifecycle rules for objects in the AWS S3 bucket.

        Args:
            folder_prefix (str): Prefix of the folder to apply rules to.
            days (int): Number of days before objects expire.
        """
        response = await self.get_lifecycle_rules()
        random_id = str(uuid.uuid4())
        if "Rules" in response:
            old_rule = response["Rules"]
            new_rules = [
                *old_rule,
                {
                    "ID": f"{random_id}",
                    "Status": "Enabled",
                    "Filter": {"Prefix": folder_prefix},
                    "Expiration": {"Days": days},
                },
            ]
            lifecycle_configuration = {"Rules": new_rules}
        else:
            lifecycle_configuration = {
                "Rules": [
                    {
                        "ID": f"{random_id}",
                        "Status": "Enabled",
                        "Filter": {"Prefix": folder_prefix},
                        "Expiration": {"Days": days},
                    },
                ],
            }

        await self.send_rules(rules=lifecycle_configuration)

    @handle_exceptions
    async def upload_file_celery(self, file_path: str, s3_path: str):
        """
        Uploads a file to the AWS S3 bucket using Celery for asynchronous
        processing.

        Args:
            file_path (str): Local path of the file to upload.
            s3_path (str): Path in S3 where the file will be stored.
        """
        object_name = f'{s3_path}/{file_path.split("/")[-1]}'
        try:
            async with self.get_client() as client:
                with open(file_path, "rb") as file:
                    await client.put_object(
                        Bucket=self.bucket_name,
                        Key=object_name,
                        Body=file,
                        ContentType="content_type",
                    )
        except ClientError as e:
            logger.error(f"Error uploading file: {e}")

    @handle_exceptions
    async def delete_completed_rule(self):
        """
        Deletes completed lifecycle rules from the AWS S3 bucket.
        If no active rules are found, attempts to delete the entire lifecycle
        configuration.

        Raises:
            ClientError: If there are issues accessing or deleting
            lifecycle rules.
        """
        try:
            data = await self.get_lifecycle_rules()
            correct_rules = list()
            rules_data = data["Rules"]
            for rule in rules_data:
                date_str = rule["Filter"]["Prefix"].split("/")[-1]
                date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
                next_day = date_obj + timedelta(
                    days=rule["Expiration"]["Days"] + 1
                )
                current_date = datetime.now().date()
                if next_day > current_date:
                    correct_rules.append(rule)
            if len(correct_rules) > 0:
                lifecycle_configuration = {"Rules": correct_rules}
                await self.send_rules(lifecycle_configuration)
            else:
                async with self.get_client() as client:
                    await client.delete_bucket_lifecycle(
                        Bucket=self.bucket_name
                    )
        except (TypeError, ClientError):
            logger.error("No rules found in S3")


s3client = S3Client()
