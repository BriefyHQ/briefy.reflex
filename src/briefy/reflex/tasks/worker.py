#!/usr/bin/python
"""Wrapper to execute ms.laure tasks worker."""
from briefy.common.config import ENV
from briefy.reflex.celery import app
from briefy.reflex.config import CELERY_CONCURRENCY
from briefy.reflex.config import CELERY_LOG_LEVEL


def main():
    """Start celery worker."""
    argv = [
        'worker',
        f'--concurrency={CELERY_CONCURRENCY}',
        '--events',
        f'--loglevel={CELERY_LOG_LEVEL}',
    ]
    if ENV in ('production', 'staging', 'development'):
        argv.append('--uid=33')
    app.worker_main(argv)


if __name__ == '__main__':
    main()
