"""Tasks to query data from google drive."""
from briefy.common.utils.data import Objectify
from briefy.gdrive import api
from briefy.reflex import config
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from celery import group
from googleapiclient.errors import HttpError
from ssl import SSLError

import csv
import os
import typing as t


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError, SSLError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit=config.GDRIVE_RATE_LIMIT,
)
def folder_contents(folder_id: str, extract_id=False, permissions=False, subfolders=True) -> dict:
    """Return folder contents from gdrive uri.

    :param folder_id: gdrive folder id
    :param extract_id: if true the folder_id value should be parsed to get the folder_id from url
    :param permissions: if true we will ask to return folder permissions
    :param subfolders: return subfolders
    :return: dict with folder contents payload
    """
    if extract_id:
        folder_id = api.get_folder_id_from_url(folder_id)
    return api.contents(folder_id, subfolders=subfolders, permissions=permissions)


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError, SSLError, OSError),
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
    autoretry_for=(HttpError, SSLError, OSError),
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


@app.task(
    base=ReflexTask,
    autoretry_for=(HttpError, SSLError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit='80/s',
)
def check_order_permission(order: dict, accounts: list) -> tuple:
    """Check if we have permission and which user."""
    slug = order.get('briefy_id')
    link = order.get('delivery_link')
    folder_id = api.get_folder_id_from_url(link)
    response = None
    while not response and accounts:
        for user in accounts:
            api.pool.impersonate(user)

            try:
                response = api.list(folder_id)
            except HttpError as error:
                if error.resp.status == 404:
                    response = 'NOT_FOUND'
                    break
            else:
                if response:
                    response = user
                    break
                else:
                    response = 'NO_PERMISSION'

            accounts.remove(user)

    return slug, response, link


@app.task(
    base=ReflexTask,
    autoretry_for=(SSLError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
    rate_limit='80/s',
)
def add_permission(slug: str, folder_id: str, user: str='', body: dict=None) -> tuple:
    """Add permission to a folder in gdrive.

    :param slug: order slug
    :param folder_id: gdrive folder ID
    :param user: if we need to impersonate another to add permission
    :param body: gdrvive permissions.create body arguments
    :return: true is permission is added or false if not
    """
    if not body:
        body = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': 'management@briefy.co'
        }

    if user:
        api.pool.impersonate(user)

    try:
        response = api.session.permissions.create(
            fileId=folder_id,
            sendNotificationEmail=False,
            body=body
        )
    except HttpError as error:
        response = {'id': str(error)}

    return slug, str(response)


def check_folders(file_name: str='orders-inventory-zero-images.csv',):
    """Check if we can list the folders with one the existing users.

    And if we can read the folder, create a new read permission to management@briefy.co.

    :param file_name: csv file with the orders we could not find any image.
    :return: None
    """
    with open('users.csv', 'r') as users_file:
        accounts = [
            item.get('email') for item in csv.DictReader(users_file)
        ]

    with open(file_name, 'r') as orders_file:
        orders = list(csv.DictReader(orders_file))
        task_list = [check_order_permission.s(item, accounts.copy()) for item in orders]

    task_group = group(task_list)
    result = task_group().join()

    add_permission_list = []
    for slug, email, link in result:
        if email not in ('NOT_FOUND', 'NO_PERMISSION'):
            folder_id = api.get_folder_id_from_url(link)
            add_permission_list.append(add_permission.s(slug, folder_id, email))

    add_permission_group = group(add_permission_list)
    permission_result = add_permission_group().join()
    permission_result_map = {slug: result for slug, result in permission_result}

    with open('folder_permissions.csv', 'w') as output:
        fieldnames = ['briefy_id', 'email', 'add_permission', 'link']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for slug, email, link in result:
            writer.writerow(
                dict(
                    briefy_id=slug,
                    email=email,
                    link=link,
                    add_permission=permission_result_map.get(slug, False)
                )
            )
