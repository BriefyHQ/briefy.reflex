"""briefy.reflex config."""
from prettyconf import config  # noQA

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
