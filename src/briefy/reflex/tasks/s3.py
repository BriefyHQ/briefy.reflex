"""Communication with amazon S3 service."""
from briefy.common.config import _queue_suffix
from briefy.common.utils.data import Objectify
from briefy.gdrive import api
from briefy.reflex import config
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from googleapiclient.errors import HttpError
from http.client import IncompleteRead
from ssl import SSLError

import boto3
import botocore
import os
import typing as t


# TODO: crete a function to count assets
# aws s3api list-objects --bucket images-dev-briefy --prefix "source/assets/"
# --output json --query "[length(Contents[])]"


@app.task(base=ReflexTask)
def file_exists(destiny: t.Tuple[str, str]) -> bool:
    """Check if file exists in S3 bucket.

    :param destiny: tuple composed of (directory, file_name)
    :return: return True if file exists esle False
    """
    directory, file_name = destiny
    bucket = f'images-{_queue_suffix}-briefy'
    file_path = os.path.join(directory, file_name)
    s3 = boto3.resource('s3')
    result = True

    try:
        s3.Object(bucket, file_path).load()
    except botocore.exceptions.ClientError as exc:
        if exc.response['Error']['Code'] == '404':
            result = False
        else:
            raise exc

    return result


@app.task(base=ReflexTask)
def upload_file(destiny: t.Tuple[str, str]) -> str:
    """Upload file to S3 bucket.

    :param destiny: tuple composed of (directory, file_name)
    :return: return the file_path
    """
    directory, file_name = destiny
    source_path = f'{config.AWS_ASSETS_SOURCE}/{file_name}'
    bucket = f'images-{_queue_suffix}-briefy'
    file_path = os.path.join(directory, file_name)
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(file_path, bucket, source_path)
    logger.info(f'File name "{file_path}" uploaded to bucket "{bucket}"')
    return source_path


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError, FileNotFoundError, SSLError, IncompleteRead, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit=config.GDRIVE_RATE_LIMIT,
)
def download_and_upload_file(destiny: t.Tuple[str, str], image_payload: dict) -> str:
    """Download from GDrive and upload file to S3 bucket.

    :param destiny: tuple composed of (directory, file_name)
    :param image_payload: google drive file id
    :return: return the file_path
    """
    directory, file_name = destiny
    image = Objectify(image_payload)
    if not file_exists(destiny):
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = f'{directory}/{file_name}'
        with open(file_path, 'wb') as data:
            data.write(api.get_file(image.id))

        result = upload_file(destiny)
        os.remove(file_path)
    else:
        result = f'{config.AWS_ASSETS_SOURCE}/{file_name}'
    return result
