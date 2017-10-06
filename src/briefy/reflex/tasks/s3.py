"""Communication with amazon S3 service."""
from briefy.common.config import ENV
from briefy.reflex import config
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask

import boto3
import typing as t


@app.task(base=ReflexTask)
def upload_file(destiny: t.Tuple[str, str]) -> str:
    """Upload file to S3 bucket.

    :param destiny: tuple composed of (directory, file_name)
    :return: return the file_path
    """
    directory, file_name = destiny
    source_path = f'{config.AWS_ASSETS_SOURCE}/{file_name}'
    if ENV == 'production':
        bucket = f'images-live-briefy'
    else:
        bucket = f'images-stg-briefy'
    file_path = f'{directory}/{file_name}'

    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(file_path, bucket, source_path)
    logger.info(f'File name "{file_path}" uploaded to bucket "{bucket}"')
    return source_path
