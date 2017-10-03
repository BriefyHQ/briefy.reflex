"""Celery configuration."""
from celery import Celery


app = Celery('briefy.reflex.tasks')
app.config_from_object('briefy.reflex.tasks.config')


def main():
    """Start celery app worker."""
    app.start()


if __name__ == '__main__':
    main()
