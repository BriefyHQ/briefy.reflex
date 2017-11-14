"""Tasks to query data from google drive."""
from briefy.common.utils.data import Objectify
from briefy.gdrive import api
from briefy.reflex import config
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from celery import group
from googleapiclient.errors import HttpError

import os
import typing as t


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError,),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit=config.GDRIVE_RATE_LIMIT,
)
def folder_contents(folder_id: str, extract_id=False, permissions=False) -> dict:
    """Return folder contents from gdrive uri.

    :param folder_id: gdrive folder id
    :param extract_id: if true the folder_id value should be parsed to get the folder_id from url
    :param permissions: if true we will ask to return folder permissions
    :return: dict with folder contents payload
    """
    if extract_id:
        folder_id = api.get_folder_id_from_url(folder_id)
    return api.contents(folder_id, permissions=permissions)


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError,),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit=config.GDRIVE_RATE_LIMIT,
)
def download_file(destiny: t.Tuple[str, str], image_payload: dict) -> t.Tuple[str, str]:
    """Download file from a gdrive api and save in the file system.

    :param destiny: tuple composed of (directory, file_name)
    :param image_payload: google drive file id
    :return: destiny file path of downloaded file
    """
    directory, file_name = destiny
    image = Objectify(image_payload)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = f'{directory}/{file_name}'
    with open(file_path, 'wb') as data:
        data.write(api.get_file(image.id))

    return directory, file_name


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError,),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit=config.GDRIVE_RATE_LIMIT,
)
def move(origin: str, destiny: str, extract_ids=False) -> dict:
    """Return folder contents from gdrive uri.

    :param origin: origin item gdrive ID
    :param destiny: destiny folder ID
    :param extract_ids: if true the folder_id value should be parsed to get the folder_id from url
    :return: True if success and False if failure
    """
    if extract_ids:
        origin = api.get_folder_id_from_url(origin)
        destiny = api.get_folder_id_from_url(destiny)
    return api.move(origin, destiny)


def move_all_files(origin_folder: str, destiny_folder: str):
    """Move all files from one folder to another.

    :param origin_folder: origin folder id
    :param destiny_folder: destiny folder id
    :return: moved files
    """
    files_to_move = api.list(origin_folder)
    task_list = [move.s(file.get('id'), destiny_folder) for file in files_to_move]
    task_group = group(task_list)
    return task_group()


def run(orders):
    """List assets from all folders."""
    tasks = []
    for item in orders:
        delivery = item.get('delivery')
        task = folder_contents.s(
            api.get_folder_id_from_url(delivery.get('gdrive'))
        )
        tasks.append(task)

    task_group = group(tasks)()
    return task_group.join()
