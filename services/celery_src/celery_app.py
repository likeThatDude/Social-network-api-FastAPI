"""
Module for configuring Celery tasks and schedules.

This module sets up various Celery tasks for backing up databases, managing
logs, and setting lifecycle rules for folders. It also configures the Celery
application and schedules the tasks to run at specified intervals.
"""

import datetime
from pathlib import Path

import loguru
from celery import Celery
from celery.schedules import crontab

from config import settings
from services.celery_src.celery_utils import (
    delete_completed_rules,
    delete_old_logs,
    get_old_logs_folder,
    set_folder_lifecycle,
    upload_db_dump_to_s3,
)

current_directory = Path(__file__).parent.parent.parent / settings.BACKUP_DIR
HOUR_DIR = Path(current_directory) / settings.S3_HOUR_FOLDER
DAY_DIR = Path(current_directory) / settings.S3_DAY_FOLDER
WEEK_DIR = Path(current_directory) / settings.S3_WEEK_FOLDER
LOGS_DIR = current_directory.parent / settings.LOGS_DIR
dump_s3_dir = settings.S3_DUMP_FOLDER
logs_s3_dir = settings.S3_LOGS_FOLDER

redis_url = (
    f"redis://{settings.DOCKER_REDIS}:{settings.DOCKER_REDIS_PORT}"
    f"/{settings.REDIS_CELERY}"
)

celery_app = Celery("twitter_clone_app", broker=redis_url, backend=redis_url)
celery_app.conf.result_expires = 3600
celery_app.conf.timezone = "Europe/Moscow"
celery_app.conf.broker_connection_retry_on_startup = True


@celery_app.task(name="one_hour")
def one_hour_backup_database():
    """
    Celery task to back up the database hour.

    This task uploads the database dump to the S3 hour directory.
    """
    loguru.logger.info(
        f"Startup one_hour_backup_database at" f"{datetime.datetime.now()}"
    )
    upload_db_dump_to_s3(HOUR_DIR)


@celery_app.task(name="one_day")
def one_day_backup_database():
    """
    Celery task to back up the database daily.

    This task uploads the database dump to the S3 day directory.
    """
    loguru.logger.info(
        f"Startup one_day_backup_database at" f"{datetime.datetime.now()}"
    )
    upload_db_dump_to_s3(DAY_DIR)


@celery_app.task(name="weekly_task")
def weekly_task_backup_database():
    """
    Celery task to back up the database weekly.

    This task uploads the database dump to the S3 week directory.
    """
    loguru.logger.info(
        f"Startup weekly_task_backup_database at" f"{datetime.datetime.now()}"
    )
    upload_db_dump_to_s3(WEEK_DIR)


@celery_app.task(name="delete_hour_dumps")
def delete_hour_backup():
    """
    Celery task to delete hourly database backups.

    This task deletes old logs from the hourly backup directory.
    """
    loguru.logger.info(
        f"Startup delete_hour_backup at" f"{datetime.datetime.now()}"
    )
    delete_old_logs(HOUR_DIR)


@celery_app.task(name="delete_one_day_dumps")
def delete_days_backup():
    """
    Celery task to delete daily database backups.

    This task deletes old logs from the daily backup directory.
    """
    loguru.logger.info(
        f"Startup delete_days_backup at" f"{datetime.datetime.now()}"
    )
    delete_old_logs(DAY_DIR)


@celery_app.task(name="delete_week_dumps")
def delete_week_backup():
    """
    Celery task to delete weekly database backups.

    This task deletes old logs from the weekly backup directory.
    """
    loguru.logger.info(
        f"Startup delete_week_backup at" f"{datetime.datetime.now()}"
    )
    delete_old_logs(WEEK_DIR)


@celery_app.task(name="set_lifecycle_rule_hours_dump")
def set_lifecycle_rule_hours_dump():
    """
    Celery task to set lifecycle rules for hourly backups.

    This task sets the lifecycle rules for the hourly backup directory in S3.
    """
    loguru.logger.info(
        f"Startup set_lifecycle_rule_hours_dump at"
        f"{datetime.datetime.now()}"
    )
    set_folder_lifecycle(HOUR_DIR, 3, dump_s3_dir)


@celery_app.task(name="set_lifecycle_rule_days_dump")
def set_lifecycle_rule_days_dump():
    """
    Celery task to set lifecycle rules for daily backups.

    This task sets the lifecycle rules for the daily backup directory in S3.
    """
    loguru.logger.info(
        f"Startup set_lifecycle_rule_days_dump at" f"{datetime.datetime.now()}"
    )
    set_folder_lifecycle(DAY_DIR, 5, dump_s3_dir)


@celery_app.task(name="set_lifecycle_rule_week_dump")
def set_lifecycle_rule_week_dump():
    """
    Celery task to set lifecycle rules for weekly backups.

    This task sets the lifecycle rules for the weekly backup directory in S3.
    """
    loguru.logger.info(
        f"Startup set_lifecycle_rule_week_dump at" f"{datetime.datetime.now()}"
    )
    set_folder_lifecycle(WEEK_DIR, 14, dump_s3_dir)


@celery_app.task(name="upload_logs_to_s3")
def upload_logs():
    """
    Celery task to upload logs to S3.

    This task uploads logs from the local logs directory to the S3 logs
    directory.
    """
    loguru.logger.info(f"Startup upload_logs at" f"{datetime.datetime.now()}")
    get_old_logs_folder(LOGS_DIR)


@celery_app.task(name="set_logs_lifecycle_rule")
def set_logs_lifecycle_rule():
    """
    Celery task to set lifecycle rules for logs.

    This task sets the lifecycle rules for the logs directory in S3.
    """
    loguru.logger.info(
        f"Startup set_logs_lifecycle_rule at" f"{datetime.datetime.now()}"
    )
    set_folder_lifecycle(LOGS_DIR, 4, logs_s3_dir)


@celery_app.task(name="delete_completed_rules")
def delete_rules():
    """
    Celery task to delete completed lifecycle rules.

    This task deletes rules that are no longer needed from the lifecycle
    configuration.
    """
    loguru.logger.info(f"Startup delete_rules at" f"{datetime.datetime.now()}")
    delete_completed_rules()


celery_app.conf.beat_schedule = {
    "backup_every_hour": {
        "task": "one_hour",
        "schedule": crontab(hour="*", minute="58"),
        "options": {"expires": 3600},
    },
    "delete_old_hour_dump": {
        "task": "delete_hour_dumps",
        "schedule": crontab(hour="00", minute="01"),
        "options": {"expires": 3600},
    },
    "set_lifecycle_hour_dump_folder": {
        "task": "set_lifecycle_rule_hours_dump",
        "schedule": crontab(hour="23", minute="59"),
        "options": {"expires": 3600},
    },
    "backup_every_day": {
        "task": "one_day",
        "schedule": crontab(hour="23", minute="58"),
        "options": {"expires": 86400},
    },
    "delete_old_day_dump": {
        "task": "delete_one_day_dumps",
        "schedule": crontab(hour="00", minute="01"),
        "options": {"expires": 86400},
    },
    "set_lifecycle_day_dump_folder": {
        "task": "set_lifecycle_rule_days_dump",
        "schedule": crontab(hour="23", minute="59"),
        "options": {"expires": 86400},
    },
    "backup_every_week": {
        "task": "weekly_task",
        "schedule": crontab(hour="23", minute="58", day_of_week="sunday"),
        "options": {"expires": 604800},
    },
    "delete_week_dump": {
        "task": "delete_week_dumps",
        "schedule": crontab(hour="00", minute="01", day_of_week="monday"),
        "options": {"expires": 604800},
    },
    "set_lifecycle_week_dump_folder": {
        "task": "set_lifecycle_rule_week_dump",
        "schedule": crontab(hour="23", minute="59", day_of_week="sunday"),
        "options": {"expires": 604800},
    },
    "upload_logs": {
        "task": "upload_logs_to_s3",
        "schedule": crontab(hour="23", minute="58"),
        "options": {"expires": 86400},
    },
    "logs_lifecycle": {
        "task": "set_logs_lifecycle_rule",
        "schedule": crontab(hour="23", minute="59"),
        "options": {"expires": 86400},
    },
    "delete_rules_task": {
        "task": "delete_completed_rules",
        "schedule": crontab(hour="00", minute="30"),
        "options": {"expires": 3600},
    },
}
