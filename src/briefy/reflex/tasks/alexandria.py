"""Tasks to query and insert data in briefy.alexandria."""
from briefy.common.utilities.interfaces import IRemoteRestEndpoint
from briefy.common.utils.data import Objectify
from briefy.reflex import config
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import leica
from briefy.reflex.tasks import gdrive
from briefy.reflex.tasks import s3
from briefy.reflex.tasks import ReflexTask
from briefy.reflex.tasks.kinesis import FOLDER_NAMES
from celery import chain
from celery import group
from celery.result import GroupResult
from requests.exceptions import ConnectionError
from slugify import slugify
from urllib3.exceptions import ProtocolError
from zope.component import getUtility


import enum
import typing as t
import uuid


class AssetsImportResult(enum.Enum):
    """Import assets from Gdrive to alexandria and S3."""

    success = 'success'
    failure = 'failure'


@app.task(
    bind=True,
    base=ReflexTask,
    autoretry_for=(ConnectionError, ProtocolError, RuntimeError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
)
def create_collections(self, order_payload: dict) -> dict:
    """Create all collections in Alexandria if the do not exists.

    :param self: reference to the task class instance
    :param order_payload: payload of order from leica
    :return: order collection payload from the library
    """
    factory = getUtility(IRemoteRestEndpoint)
    library_api = factory(config.ALEXANDRIA_BASE, 'collections', 'Collections')
    order = Objectify(order_payload)
    collections = [
        (order.customer, 'customer'),
        (order.project, 'project'),
        (order, 'order'),
    ]
    parent_id = config.ALEXANDRIA_LEICA_ROOT
    for item, type_ in collections:
        result = library_api.get(item.id)
        if not result:
            payload = {
                'slug': item.slug,
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'content_type': f'application/collection.leica-{type_}',
                'parent_id': parent_id,
                'tags': [type_]
            }
            result = library_api.post(payload)

        # this will be the new parent
        parent_id = result.get('id')

    if order.requirement_items:
        for i, item in enumerate(order.requirement_items):
            result = library_api.get(item.id)
            if not result:
                category_name = item._get('name', f'ItemName-{i}')
                payload = {
                    'slug': slugify(category_name),
                    'id': item.id,
                    'title': item.category,
                    'description': item._get('description', ''),
                    'content_type': 'application/collection.leica-order.requirement',
                    'parent_id': order.id,
                    'tags': item.tags,
                    'properties': {
                        'gdrive': {
                            'folder_id': item.folder_id,
                            'parent_folder_id': item.parent_folder_id,
                            'created_by': '9df18a79-44dc-4c2f-86aa-09bf7706ae86'
                        }
                    }
                }
                library_api.post(payload)
    return library_api.get(order.id)


@app.task(
    base=ReflexTask,
    autoretry_for=(ConnectionError, ProtocolError, RuntimeError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
)
def add_or_update_asset(image_payload: dict, collection_payload: dict) -> t.Tuple[str, str]:
    """Add one assets in Alexandria if it do not exists.

    :param image_payload: image payload from briefy.gdrive
    :param collection_payload: payload of order collection from briefy.alexandria
    :return: asset file_path
    """
    collection = Objectify(collection_payload)
    factory = getUtility(IRemoteRestEndpoint)
    library_api = factory(config.ALEXANDRIA_BASE, 'assets', 'Assets')
    image = Objectify(image_payload)
    data = library_api.query({'slug': image.id})['data']

    if image.mimeType == 'image/jpeg':
        extension = 'jpg'
    elif len(image.name) >= 3:
        extension = image.name[-3:]
    else:
        extension = 'none'

    if not data:
        tags = ['gdrive', 'image']
        tags.extend(collection.tags)
        asset_id = uuid.uuid4()
        file_name = f'{asset_id}.{extension}'
        source_path = f'{config.AWS_ASSETS_SOURCE}/{file_name}'
        payload = {
            'slug': image.id,
            'id': uuid.uuid4(),
            'title': image.name,
            'description': '',
            'content_type': image.mimeType,
            'source_path': source_path,
            'tags': tags,
            'collections': [collection.id],
            'size': image.size,
            'properties': {
                'metadata': image.imageMediaMetadata,
                'external_links': {
                    'view': image.webViewLink,
                    'download': image.webContentLink
                }
            }
        }
        data = library_api.post(payload)
    else:
        data = data[0]
        asset_id = data.get('id')
        data = library_api.get(asset_id)
        asset_collections = data.get('collections')
        if collection.id not in asset_collections:
            asset_collections.append(collection.id)
            data = library_api.put(asset_id, data)

        file_name = f'{asset_id}.{extension}'

    if not data:
        raise RuntimeError(f'Failed to add or update asset: {image_payload}')

    # in this case we should have one more directory
    if collection.content_type == 'application/collection.leica-order.requirement':
        order_id = collection.parent_id
        directory = f'{config.TMP_PATH}/{order_id}/{collection.id}'
    else:
        order_id = collection.id
        directory = f'{config.TMP_PATH}/{order_id}'

    logger.info(f'Asset added to alexandria. Path to save file: {directory}/{file_name}')
    return directory, file_name


def create_assets(collection_payload: dict, order_payload: dict) -> group:
    """Create all assets in Alexandria if the do not exists.

    :param collection_payload: payload of order collection from briefy.alexandria
    :param order_payload: payload of order from leica
    :return: list of orders returned from listing payload
    """
    factory = getUtility(IRemoteRestEndpoint)
    library_api = factory(config.ALEXANDRIA_BASE, 'collections', 'Collections')
    order = Objectify(order_payload)

    tasks = []
    if order.requirement_items:
        for item in order.requirement_items:
            folder_contents = gdrive.folder_contents.delay(item.folder_id).get()
            images = folder_contents.get('images')
            collection_payload = library_api.get(item.id)
            image_tasks = [
                chain(
                    add_or_update_asset.s(image, collection_payload),
                    s3.download_and_upload_file.s(image),
                ) for image in images
            ]

            tasks.extend(image_tasks)

    else:
        folder_contents = gdrive.folder_contents.delay(
            order.delivery.gdrive,
            extract_id=True
        ).get()
        images = folder_contents.get('images')
        sub_folders = [
            folder for folder in folder_contents.get('folders')
            if folder.get('name').lower().strip() in FOLDER_NAMES
        ]

        # make sure que get images also from sub folders
        for folder in sub_folders:
            images.extend(folder.get('images'))

        image_tasks = [
            chain(
                add_or_update_asset.s(image, collection_payload),
                s3.download_and_upload_file.s(image),
            ) for image in images
        ]
        tasks.extend(image_tasks)

    return group(tasks)


@app.task(
    base=ReflexTask,
    autoretry_for=(ConnectionError, ProtocolError, RuntimeError, OSError),
    retry_kwargs={'max_retries': config.TASK_MAX_RETRY},
    retry_backoff=True,
)
def add_order(order: dict, from_csv: bool=False) -> GroupResult:
    """Upload one order to alexandria library.

    :param order: order payload
    :param from_csv: means that the order payload is from the csv report and we need to query leica
    :return: async group result fro m celery group execution
    """
    if from_csv:
        order = leica.get_order(order.get('uid'))
    collection = create_collections(order)
    return create_assets(collection, order)()


@app.task(base=ReflexTask)
def run(order) -> tuple:
    """Upload one order to alexandria library.

    This will run synchronously.
    """
    result = add_order(order)
    assets = result.join()
    success = result.status == 'SUCCESS'
    status = AssetsImportResult.success if success else AssetsImportResult.failure
    result = {'assets': assets}
    return status, result


def main(uri: str, chunk_size=10) -> list:
    """Create assets for all orders in one project.

    :param uri: link to all orders csv file
    :param chunk_size: number of tasks per chunk of execution
    :return: list of celery async result instances, the number depends of the chunk size
    """
    orders = [
        order for order in leica.orders_from_csv(uri)
        if order.get('order_status') == 'accepted' and order.get('delivery_link')
    ]
    number_of_orders = len(orders)
    number_of_chunks = number_of_orders // chunk_size
    param_list = [(order, True) for order in orders]
    return add_order.chunks(param_list, number_of_chunks).apply_async()
