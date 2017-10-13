"""Define briefy.reflex base task class."""
from briefy.reflex import logger
from briefy.reflex.celery import app


class ReflexTask(app.Task):
    """Base class to be used by all tasks in ms.laure.tasks module."""

    def on_failure(self, exc, task_id: str, args, kwargs, einfo):
        """Execute callback in case of failure.

        :param exc: failure exception
        :param task_id: id of the task
        :param args: list of additional arguments
        :param kwargs: dict of additional arguments
        :param einfo: additional info
        :return:
        """
        logger.debug(f'{task_id!r} failed: {exc!r}')

    def on_success(self, retval, task_id, args, kwargs):
        """Execute callback in case of success.

        :param retval: result of the task execution
        :param task_id: id of the task
        :param args: list of additional arguments
        :param kwargs: dict of additional arguments
        :return:
        """
        logger.debug(f'{task_id!r} success: {retval!r}')
