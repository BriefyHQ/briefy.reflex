#!/bin/sh
python3.6 -m http.server 8000 &
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-tasks-worker.ini newrelic-admin run-program celery -A briefy.reflex.tasks --events --uid=33 --concurrency=${CELERY_CONCURRENCY_DEFAULT} --loglevel=INFO -Q briefy_reflex -P eventlet worker
