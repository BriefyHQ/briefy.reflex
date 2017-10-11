"""Tasks to query data from google drive."""
from briefy.common.utils.data import Objectify
from briefy.gdrive import api
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from celery import group

import os
import typing as t


@app.task(bind=True, base=ReflexTask)
def folder_contents(self, folder_id: str, extract_id=False) -> dict:
    """Return folder contents from gdrive uri.

    :param self: task class instance
    :param folder_id: gdrive folder id
    :param extract_id: if true the folder_id value should be parsed to get the folder_id from url
    :return: dict with folder contents payload
    """
    if extract_id:
        folder_id = api.get_folder_id_from_url(folder_id)
    return api.contents(folder_id)


@app.task(base=ReflexTask)
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
