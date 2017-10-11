"""Reflex worker."""
from briefy.common.queue import IQueue
from briefy.common.queue.message import SQSMessage
from briefy.common.utils.data import Objectify
from briefy.common.worker.queue import QueueWorker
from briefy.reflex import events
from briefy.reflex import logger
from briefy.reflex.config import NEW_RELIC_LICENSE_KEY
from briefy.reflex.tasks import alexandria
from zope.component import getUtility

import enum
import newrelic.agent


# This could be a namedtuple, but they don't work with the current version of 'Objectify'
NA = lambda action, success, message: dict(action=action, success=success, message=message)  # noQA


class ResponseWrapper:
    """Wrap payload in object with neeed attributes."""

    def __init__(self, obj, payload):
        """Initialize attributes."""
        self.data = payload
        self.created_at = obj.created_at
        self.id = obj.id

    def to_dict(self, *args, **kwargs):
        """Unwrap wrapped data."""
        data = self.data
        return data._dct if isinstance(data, Objectify) else data


class Worker(QueueWorker):
    """Ms.laure queue worker."""

    name = ''
    """Worker name."""

    input_queue = None
    """Queue to read event messages from."""

    run_interval = 1
    """Interval to fetch new messages from the queue."""

    _events_queue = None
    """Events queue."""

    dispatch_map = None
    """Dict with configuration to choose the dispatcher."""

    def __init__(self, *args, name: str, dispatch_map: dict, **kwargs):
        """Added new parameter to the worker init class."""
        self.name = name
        self.dispatch_map = dispatch_map
        super().__init__(*args, **kwargs)

    @newrelic.agent.background_task(name='process_message', group='Task')
    def process_message(self, message: SQSMessage) -> bool:
        """Process a message retrieved from the input_queue.

        :param message: A message from the queue
        :returns: Status from the process
        """
        body = message.body
        assignment = Objectify(body.get('data', {}))
        event = body.get('event_name', '')
        message_id = body.get('id', '')
        assignment.sqs_message_id = message_id
        dispatch = Objectify(self.dispatch_map.get(event, {}))
        if not dispatch:
            logger.info('Unknown event type - message {0} ignored'.format(body['id']))
            return True

        logger.info('Processing event {event}'.format(event=event))
        try:
            status, payload = dispatch.action(assignment)
        except Exception as error:
            msg = 'Unknown exception raised on \'{0}\' assignment {1}. \n' \
                  'Error: {2} \n Payload: {3}'
            logger.error(
                msg.format(
                    dispatch.name,
                    assignment.id,
                    error,
                    assignment.dct
                )
            )
            raise  # Let newrelic deal with it.
        response = ResponseWrapper(assignment, payload)
        notification_action = dispatch.notification_actions[status]
        event = notification_action.action(response)
        message = notification_action.message
        logger.info(message.format(event=event))
        event()
        if not notification_action.success:  # processing failed
            # Return False if the message is to be retried
            return not dispatch.on_failure_retry
        return True


def run_worker(queue_name: str, worker_name: str, dispatch_map: dict):
    """Execute worker using queue name.

    :param queue_name: name of the queue utility.
    :param worker_name: name of the worker.
    :param dispatch_map: dict with configuration to be dispatched for each event name.
    :return:
    """
    queue = getUtility(IQueue, queue_name)
    worker = Worker(
        logger_=logger,
        input_queue=queue,
        name=worker_name,
        dispatch_map=dispatch_map
    )
    if NEW_RELIC_LICENSE_KEY:
        newrelic.agent.register_application(timeout=10.0)
    try:
        worker()
    except Exception as exc:
        name = Worker.name
        logger.exception(f'{name} exiting due to an exception.', exc_info=exc)


class ImportAssetsResult(enum.Enum):
    """Import assets from Gdrive to alexandria and S3."""

    success = 'success'
    failure = 'failure'


NOTIFICATION_ACTIONS = {
    ImportAssetsResult.success: NA(
        events.ImportAssetsSuccess,
        True,
        'Task for {event} was processed successfully'
    ),
    ImportAssetsResult.failure: NA(
        events.ImportAssetsFailure,
        True,
        'Task for {event} was processed with failure'
    ),
}


MESSAGE_DISPATCH = {
    'order.workflow.accept': dict(
        name='alexandria.run',
        action=alexandria.run,
        notification_actions=NOTIFICATION_ACTIONS,
        on_failure_retry=True
    )
}


def main():
    """Initialize and execute the Worker."""
    run_worker('reflex.queue', 'reflex.worker', MESSAGE_DISPATCH)
