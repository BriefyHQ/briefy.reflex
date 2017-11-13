#!/usr/bin/env bash
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-tasks-worker.ini newrelic-admin run-program celery -A briefy.reflex.tasks --events --uid=33 --concurrency=${CELERY_CONCURRENCY_GDRIVE} --loglevel=INFO -Q briefy_reflex_gdrive -P eventlet worker
