"""
This module contains service functions for working with database dumps,
managing logs, and interacting with S3, including creating backups, uploading
to S3, and setting lifecycle rules.
"""

import asyncio
import os
import shutil
import subprocess
from datetime import datetime
from functools import wraps
from pathlib import Path

from config import logger, settings
from services.s3.s3client import s3client


def handle_exceptions_sync(func):
    """
    Decorator to handle exceptions in synchronous functions.

    Args:
        func (function): The function to wrap.

    Returns:
        function: Wrapped function with exception handling.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                f"func:{func.__name__}, error: {e.__class__.__name__}"
            )

    return wrapper


@handle_exceptions_sync
def make_folder(today_dir: str):
    """
    Create a folder if it doesn't exist.

    Args:
        today_dir (str): The directory to create.
    """
    if not os.path.exists(today_dir):
        try:
            os.makedirs(today_dir)
        except OSError as e:
            logger.exception(f"Error creating folder {today_dir}: {e}")


@handle_exceptions_sync
def get_formatted_date(current_directory: str) -> list:
    """
    Get the formatted date and create today's directory.

    Args:
        current_directory (str): The base directory for backups.

    Returns:
        list: A list containing today's directory, formatted time, formatted
        date, and current S3 directory.
    """
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d.%m.%Y")
    formatted_time = current_date.strftime("%H:%M:%S")
    today_dir = f"{current_directory}/{formatted_date}"
    current_s3_dir = str(current_directory).split("/")[-1]
    make_folder(today_dir)
    return [today_dir, formatted_time, formatted_date, current_s3_dir]


@handle_exceptions_sync
def make_db_dump(directory: str, time: str):
    """
    Create a database dump.

    Args:
        directory (str): The directory to store the dump.
        time (str): The time to name the dump file.
    """
    command = (
        f"pg_dump postgresql://{settings.DB_USER}:{settings.DB_PASS}@"
        f"{settings.DOCKER_DATABASE}:{settings.DOCKER_DATABASE_PORT}/"
        f"{settings.DB_NAME} "
        f"> {directory}/{time}_backup.dump"
    )
    subprocess.run(command, shell=True)


@handle_exceptions_sync
def upload_dumps_to_s3(directory: str, time: str, date: str, dump_dir: str):
    """
    Upload database dumps to S3.

    Args:
        directory (str): The directory of the dump file.
        time (str): The time to name the dump file.
        date (str): The current date.
        dump_dir (str): The S3 directory for the dump.
    """
    file_path = f"{directory}/{time}_backup.dump"
    current_s3_path = f"backup_database/{dump_dir}/{date}"
    asyncio.run(s3client.upload_file_celery(file_path, current_s3_path))


@handle_exceptions_sync
def upload_db_dump_to_s3(current_directory: str):
    """
    Handle the process of creating and uploading a database dump to S3.

    Args:
        current_directory (str): The base directory for backups.
    """
    current_data = get_formatted_date(current_directory)
    make_db_dump(directory=current_data[0], time=current_data[1])
    upload_dumps_to_s3(
        directory=current_data[0],
        time=current_data[1],
        date=current_data[2],
        dump_dir=current_data[3],
    )


@handle_exceptions_sync
def delete_old_logs(directory: Path):
    """
    Delete old logs from the specified directory.

    Args:
        directory (Path): The directory containing the logs.
    """
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d.%m.%Y")
    list_dir = os.listdir(directory)
    for i in list_dir:
        if i != formatted_date:
            shutil.rmtree(f"{directory}/{i}")


@handle_exceptions_sync
def get_current_folder(dump_dir: Path, s3_dir: str) -> str:
    """
    Get the current folder path for S3.

    Args:
        dump_dir (Path): The local dump directory.
        s3_dir (str): The S3 base directory.

    Returns:
        str: The current S3 folder path.
    """
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d.%m.%Y")
    current_prefix = str(dump_dir).split("/")[-1]
    current_s3_path = f"{s3_dir}/{current_prefix}/{formatted_date}"
    return current_s3_path


@handle_exceptions_sync
def set_folder_lifecycle(dump_dir: Path, days_count: int, s3_dir: str):
    """
    Set the lifecycle rules for a folder in S3.

    Args:
        dump_dir (Path): The local dump directory.
        days_count (int): The number of days for the lifecycle rule.
        s3_dir (str): The S3 base directory.
    """
    folder = get_current_folder(dump_dir, s3_dir)
    asyncio.run(
        s3client.set_lifecycle_rules(folder_prefix=folder, days=days_count)
    )


@handle_exceptions_sync
def upload_logs_to_s3(file_dir: str):
    """
    Upload log files to S3.

    Args:
        file_dir (str): The directory containing the log files.
    """
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d.%m.%Y")
    current_s3_path = f"logs/{formatted_date}"
    asyncio.run(s3client.upload_file_celery(file_dir, current_s3_path))


@handle_exceptions_sync
def get_old_logs_folder(logs_dir: str):
    """
    Get and upload old log files to S3.

    Args:
        logs_dir (str): The directory containing the log files.
    """
    files = os.listdir(logs_dir)
    date = get_formatted_date(logs_dir)[2]
    for i in files:
        if i.endswith(".zip") and i.startswith(date):
            current_log_file = f"{str(logs_dir)}/{i}"
            upload_logs_to_s3(current_log_file)


@handle_exceptions_sync
def delete_completed_rules():
    """
    Delete completed lifecycle rules from S3.
    """
    asyncio.run(s3client.delete_completed_rule())
