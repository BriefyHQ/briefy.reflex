"""Tasks querying information on Leica endpoints."""
from briefy.common.utilities.interfaces import IRemoteRestEndpoint
from briefy.reflex import config
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from zope.component import getUtility

import typing as t


@app.task(bind=True, base=ReflexTask)
def get_orders(self, project_id: str, states: list, page: int=1) -> t.Sequence[dict]:
    """Get orders from leica endpoint.

    :param self: referece to the task class instance
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
    result = remote.query(params)
    pagination = result['pagination']
    data = result['data']
    return data, pagination


def get_filters():
    """Get orders filter."""
    return {
        'project_id': '6f842680-749e-4898-582d-27b240c93c34',
        'states': ['accepted', ],
    }


def run():
    """Execute task."""
    kwargs = get_filters()
    data, pagination = get_orders.delay(**kwargs).get()
    return data, pagination
