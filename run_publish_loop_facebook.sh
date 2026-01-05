#!/usr/bin/env bash
set -euo pipefail

RUNS=10
SLEEP=120

for i in $(seq 1 $RUNS); do
  echo "==============================" >> logs/cron_facebook.log
  echo "[RUN $i] $(date)" >> logs/cron_facebook.log
  .venv/bin/python -m generator.cli.publish_facebook >> logs/cron_facebook.log 2>&1
  sleep $SLEEP
done
