"""Celery configuration."""
from briefy.common import config
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
    'briefy.reflex.tasks.s3'
)

# Using the database to store task state and results.
result_backend = TASKS_RESULT_DB

# lifetime to store results in the result database (seconds)
result_expires = 2592000

# if true run task local
task_always_eager = False if config.ENV != 'test' else True
