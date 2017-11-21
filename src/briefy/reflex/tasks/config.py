"""Celery configuration."""
from briefy.common import config
from briefy.reflex.config import CELERY_DEFAULT_QUEUE
from briefy.reflex.config import CELERY_DEFAULT_QUEUE_DRIVE
from briefy.reflex.config import CELERY_DEFAULT_QUEUE_S3
from briefy.reflex.config import TASKS_BROKER
from briefy.reflex.config import TASKS_RESULT_DB


# Tell celery to use your new serializer:
accept_content = ['application/json']
# task_serializer = 'custom_json'
# result_serializer = 'custom_json'

# Broker settings.
broker_url = TASKS_BROKER

# List of modules to import when the Celery worker starts.
imports = (
    'briefy.reflex.tasks.alexandria',
    'briefy.reflex.tasks.leica',
    'briefy.reflex.tasks.gdrive',
    'briefy.reflex.tasks.kinesis',
    'briefy.reflex.tasks.s3'
)

# create missing queue by default
task_create_missing_queues = True

# defining routes
task_default_queue = CELERY_DEFAULT_QUEUE
task_routes = {
    'briefy.reflex.tasks.alexandria.*': {
        'queue': CELERY_DEFAULT_QUEUE,
        'routing_key': 'briefy.reflex.tasks.alexandria',
    },
    'briefy.reflex.tasks.leica.*': {
        'queue': CELERY_DEFAULT_QUEUE,
        'routing_key': 'briefy.reflex.tasks.leica',
    },
    'briefy.reflex.tasks.kinesis.*': {
        'queue': CELERY_DEFAULT_QUEUE,
        'routing_key': 'briefy.reflex.tasks.kinesis',
    },
    'briefy.reflex.tasks.gdrive.*': {
        'queue': CELERY_DEFAULT_QUEUE_DRIVE,
        'routing_key': 'briefy.reflex.tasks.gdrive',
    },
    'briefy.reflex.tasks.s3.*': {
        'queue': CELERY_DEFAULT_QUEUE_S3,
        'routing_key': 'briefy.reflex.tasks.s3',
    },
}

# Using the database to store task state and results.
result_backend = TASKS_RESULT_DB

# lifetime to store results in the result database (seconds)
result_expires = 86400

# if true run task local
task_always_eager = False if config.ENV != 'test' else True

# setting to make sure the task will be rescheduled in case of failure
task_acks_late = True
task_reject_on_worker_lost = True

# limiting the prefetch to one (default is 4) to balance better the tasks between workers
# worker_prefetch_multiplier = 1

# track tasks started but not finished
task_track_started = True
