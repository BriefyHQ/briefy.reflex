"""Communication with amazon S3 service."""
from briefy.common.config import _queue_suffix
from briefy.common.utils.data import Objectify
from briefy.gdrive import api
from briefy.reflex import config
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from googleapiclient.errors import HttpError

import boto3
import os
import typing as t


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
    os.remove(file_path)
    return source_path


@app.task(base=ReflexTask)
def download_and_upload_file(
    destiny: t.Tuple[str, str],
    image_payload: dict,
    autoretry_for=(HttpError, FileNotFoundError),
    retry_kwargs={'max_retries': 5}
) -> str:
    """Download from GDrive and upload file to S3 bucket.

    :param destiny: tuple composed of (directory, file_name)
    :param image_payload: google drive file id
    :param autoretry_for: list of exceptions to retry
    :param retry_kwargs: parameters to the retry
    :return: return the file_path
    """
    directory, file_name = destiny
    image = Objectify(image_payload)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = f'{directory}/{file_name}'
    with open(file_path, 'wb') as data:
        data.write(api.get_file(image.id))

    destiny = directory, file_name
    return upload_file(destiny)
