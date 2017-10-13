"""Ms. Laure Queues."""
from briefy.common.db import datetime_utcnow
from briefy.common.queue import Queue as BaseQueue
from briefy.common.queue import IQueue
from briefy.common.utils.schema import Dictionary
from briefy.common.validators import EventName
from briefy.reflex.config import REFLEX_QUEUE
from zope.interface import implementer

import colander
import logging


logger = logging.getLogger('ms.laure')


def null_validator(*args, **kw):
    """Validate any thing."""
    return None


class Schema(colander.MappingSchema):
    """Payload for the assigment queue."""

    id = colander.SchemaNode(colander.String(), validator=colander.uuid)
    """message id"""

    created_at = colander.SchemaNode(
        colander.DateTime(), validator=null_validator, missing=datetime_utcnow()
    )
    """Event creation time"""

    actor = colander.SchemaNode(colander.String(), validator=null_validator, missing=None)
    """Actor of this message"""

    data = colander.SchemaNode(Dictionary())
    """Payload -- for interpolation -- to be used on the email."""

    guid = colander.SchemaNode(colander.String(), validator=colander.uuid)
    """GUID for the event."""

    event_name = colander.SchemaNode(colander.String(), validator=EventName)
    """Event name."""


@implementer(IQueue)
class Queue(BaseQueue):
    """A Queue to handle messages received from briefy.choreographer."""

    name = REFLEX_QUEUE
    """Queue name."""

    _schema = Schema
    """Validation schema."""

    @property
    def payload(self) -> dict:
        """Return an example payload for this queue.

        :returns: Dictionary representing the payload for this queue
        """
        return {
            'event_name': '',

        }
