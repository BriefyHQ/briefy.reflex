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
from celery import chain
from celery import group
from slugify import slugify
from zope.component import getUtility

import typing as t
import uuid


@app.task(bind=True, base=ReflexTask)
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
                'slug': slugify(item.title),
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
        for item in order.requirement_items:
            result = library_api.get(item.id)
            if not result:
                payload = {
                    'slug': item.folder_name,
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


@app.task(base=ReflexTask)
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
        data = library_api.get(data.get('id'))
        if collection.id not in data.get('collections'):
            data.get('collections').append(collection.id)
            data = library_api.put(data)

        asset_id = data.get('id')
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
            folder_contents = gdrive.folder_contents(item.folder_id)
            images = folder_contents.get('images')
            collection_payload = library_api.get(item.id)
            image_tasks = [
                chain(
                    add_or_update_asset.s(image, collection_payload),
                    gdrive.download_file.s(image),
                    s3.upload_file.s()
                ) for image in images
            ]

            tasks.extend(image_tasks)

    else:
        folder_contents = gdrive.folder_contents(order.delivery.gdrive)
        images = folder_contents.get('images')
        image_tasks = [
            chain(
                add_or_update_asset.s(image, collection_payload),
                gdrive.download_file.s(image),
                s3.upload_file.s()
            ) for image in images
        ]
        tasks.extend(image_tasks)

    return group(tasks)


def run(order):
    """Execute task."""
    collection = create_collections(order)
    return create_assets(collection, order)()


def main():
    """Main function."""
    orders = leica.run()
    task_results = []
    for order in orders:
        task_results.append(run(order))

    results = []
    for task in task_results:
        results.extend(task.join())

    return results
