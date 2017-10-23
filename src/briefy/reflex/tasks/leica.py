"""Tasks querying information on Leica endpoints."""
from briefy.common.utilities.interfaces import IRemoteRestEndpoint
from briefy.reflex import config
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from briefy.reflex.tasks.gdrive import folder_contents
from briefy.reflex.tasks.kinesis import put_gdrive_record
from celery import chain
from celery import group
from csv import DictReader
from io import StringIO
from zope.component import getUtility

import requests
import typing as t


@app.task(bind=True, base=ReflexTask)
def query_orders(self, project_id: str, states: list, page: int=1) -> t.Sequence[dict]:
    """Query orders from leica endpoint.

    :param self: reference to the task class instance
    :param project_id: Project ID in the Leica database
    :param states: list of states to filter orders
    :param page: page to be returned
    :return: list of orders returned from listing payload
    """
    factory = getUtility(IRemoteRestEndpoint)
    remote = factory(config.LEICA_BASE, 'orders', 'Orders')
    params = {
        'in_state': ','.join(states),
        'project_id': project_id,
        'current_type': 'order',
        '_page': page
    }
    result = remote.query(params, items_per_page=100)
    pagination = result['pagination']
    data = result['data']
    return data, pagination


@app.task(bind=True, base=ReflexTask)
def get_order(self, order_id: str) -> dict:
    """Get one order from leica endpoint.

    :param self: reference to the task class instance
    :param order_id: Order ID to get the full payload
    :return: order full payload
    """
    factory = getUtility(IRemoteRestEndpoint)
    remote = factory(config.LEICA_BASE, 'orders', 'Orders')
    return remote.get(order_id)


def get_filters():
    """Get orders filter."""
    return {
        'project_id': '6f842680-749e-4898-582d-27b240c93c34',
        'states': ['accepted', ],
    }


def orders_from_csv(csv_uri: str) -> t.Sequence[dict]:
    """Download and return all orders from a CSV report.

    :param csv_uri: URI to download the images from S3
    :return: list of orders from the csv file
    """
    response = requests.get(csv_uri)
    if response.status_code == 200:
        csv_file = StringIO(response.text)
        reader = DictReader(csv_file, delimiter='\t')
        return [item for item in reader]
    else:
        raise RuntimeError(f'Failure to download file from: {csv_uri}.')


@app.task(bind=True, base=ReflexTask)
def read_all_delivery_contents(self, csv_uri: str):
    """Read all content from the gdrive delivery folder and store in aws kinesis."""
    orders = orders_from_csv(csv_uri)
    task_list = [
        chain(
            folder_contents.s(order.get('delivery_link'), extract_id=True),
            put_gdrive_record.s(order)
        ) for order in orders if order.get('delivery_link')
    ]
    task_group = group(task_list)
    return task_group().join()


def run():
    """Execute task."""
    kwargs = get_filters()
    data, pagination = query_orders.delay(**kwargs).get()
    group_task = group([get_order.s(order.get('id')) for order in data])
    return group_task().join()
