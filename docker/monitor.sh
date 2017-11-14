#!/bin/sh
/docker_entrypoint.sh && NEW_RELIC_CONFIG_FILE=/app/newrelic-monitor.ini newrelic-admin run-program flower -A briefy.reflex --conf=/app/src/briefy/reflex/flower.py
