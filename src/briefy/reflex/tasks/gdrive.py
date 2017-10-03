"""Tasks to query data from google drive."""
from briefy.gdrive import api
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask
from celery import group


@app.task(bind=True, base=ReflexTask)
def folder_contents(self, folder_id: str) -> dict:
    """Return folder contents from gdrive uri.

    :param self: task class instance
    :param folder_id: gdrive folder id
    :return: dict with folder contents payload
    """
    return api.contents(folder_id)


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
