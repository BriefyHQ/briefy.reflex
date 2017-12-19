#!/bin/sh
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-queue-worker.ini newrelic-admin run-program queue_worker
