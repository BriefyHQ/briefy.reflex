"""briefy.reflex config."""
from briefy.common.config import _queue_suffix
from prettyconf import config

# Reflex
REFLEX_QUEUE = config('REFLEX_QUEUE', default='reflex-{0}'.format(_queue_suffix))

# NewRelic
NEW_RELIC_LICENSE_KEY = config('NEW_RELIC_LICENSE_KEY', default='')

# CELERY
TASKS_BROKER = config('TASKS_BROKER', default='redis://localhost:6379/1')
TASKS_RESULT_DB = config('TASKS_RESULT_DB', default='redis://localhost:6379/2')

# leica
LEICA_BASE = config('LEICA_BASE', default='http://briefy-leica.briefy-leica')

# alexandria
ALEXANDRIA_BASE = config('ALEXANDRIA_BASE', default='http://briefy-alexandria.briefy-alexandria')
ALEXANDRIA_LEICA_ROOT = '48f47fdc-922b-4aae-8388-0fb23a123fcc'
ALEXANDRIA_CITYPACKAGES_ROOT = '27f0cdff-14da-42c4-880a-51c3d6f0b841'

# tmp folder
TMP_PATH = config('TMP_PATH', default='/tmp/assets')

# aws assets base
AWS_ASSETS_SOURCE = config('AWS_ASSETS_SOURCE', default='source/assets')

# celery
CELERY_CONCURRENCY_DEFAULT = config('CELERY_CONCURRENCY_DEFAULT', default=2)
CELERY_CONCURRENCY_GDRIVE = config('CELERY_CONCURRENCY_GDRIVE', default=2)
CELERY_CONCURRENCY_S3 = config('CELERY_CONCURRENCY_S3', default=2)
CELERY_LOG_LEVEL = config('CELERY_LOG_LEVEL', default='INFO')
CELERY_DEFAULT_QUEUE = config('CELERY_DEFAULT_QUEUE', default='briefy_reflex')
CELERY_DEFAULT_QUEUE_DRIVE = config('CELERY_DEFAULT_QUEUE_DRIVE', default='briefy_reflex_gdrive')
CELERY_DEFAULT_QUEUE_S3 = config('CELERY_DEFAULT_QUEUE_S3', default='briefy_reflex_s3')
TASK_MAX_RETRY = config('TASK_MAX_RETRY', cast=int, default='10')
GDRIVE_RATE_LIMIT = config('GDRIVE_RATE_LIMIT', default='10/s')

# kinesis
GDRIVE_DELIVERY_STREAM = config('GDRIVE_DELIVERY_STREAM', default='gdrive_delivery_contents')
