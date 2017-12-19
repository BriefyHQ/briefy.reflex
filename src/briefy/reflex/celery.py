"""Celery configuration."""
from celery import Celery


app = Celery('briefy.reflex.tasks')
app.config_from_object('briefy.reflex.tasks.config')


def main():
    """Start celery app worker."""
    app.start()


# TODO: create a command for this
# to purge all tasks from all queues
# celery -A briefy.reflex -f -Q briefy_reflex_tasks,briefy_reflex,briefy_reflex_s3 purge

if __name__ == '__main__':
    main()
