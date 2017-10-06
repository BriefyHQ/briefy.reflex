#!/bin/sh
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-tasks-worker.ini newrelic-admin run-program tasks_worker
