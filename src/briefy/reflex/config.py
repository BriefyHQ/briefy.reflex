"""briefy.reflex config."""
from prettyconf import config  # noQA

# CELERY
TASKS_BROKER = config('TASKS_BROKER', default='redis://localhost:6379/1')
TASKS_RESULT_DB = config('TASKS_RESULT_DB', default='redis://localhost:6379/2')

# leica
LEICA_BASE = config('LEICA_BASE', default='http://briefy-leica.briefy-leica')
