"""briefy.reflex base events."""
from briefy.common.event import BaseEvent
from briefy.common.event import IDataEvent
from briefy.reflex import logger
from zope.interface import implementer


class IReflexEvent(IDataEvent):
    """Inferface for Reflex events."""


class ReflexEvent(BaseEvent):
    """A briefy.reflex event."""

    logger = logger
    """Event logger."""


@implementer(IReflexEvent)
class ImportAssetsSuccess(ReflexEvent):
    """Import assets from gdrive to s3 and add data in briefy.alexandria success."""

    event_name = 'reflex.import.assets.success'
    """Event name."""


@implementer(IReflexEvent)
class ImportAssetsFailure(ReflexEvent):
    """Import assets from gdrive to s3 and add data in briefy.alexandria failure."""

    event_name = 'reflex.import.assets.success'
    """Event name."""
