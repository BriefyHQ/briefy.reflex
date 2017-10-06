#!/usr/bin/python
"""Wrapper to execute ms.laure tasks worker."""
from briefy.common.config import ENV
from briefy.reflex.celery import app


def main():
    """Start celery worker."""
    argv = [
        'worker',
        '--concurrency=20',
        '--events',
        '--loglevel=INFO',
    ]
    if ENV in ('production', 'staging'):
        argv.append('--uid=33')
    app.worker_main(argv)


if __name__ == '__main__':
    main()
