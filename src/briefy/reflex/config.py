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
CELERY_CONCURRENCY = config('CELERY_CONCURRENCY', default=2)
CELERY_LOG_LEVEL = config('CELERY_LOG_LEVEL', default='INFO')

# kinesis
GDRIVE_DELIVERY_STREAM = config('GDRIVE_DELIVERY_STREAM', default='gdrive_delivery_contents')
