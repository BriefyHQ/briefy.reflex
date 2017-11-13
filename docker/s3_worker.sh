#!/usr/bin/env bash
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-s3-worker.ini newrelic-admin run-program celery -A briefy.reflex.tasks --events --uid=33 --concurrency=${CELERY_CONCURRENCY_S3} --loglevel=INFO -Q briefy_reflex_s3 -P eventlet worker
