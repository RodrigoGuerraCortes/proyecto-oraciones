#!/usr/bin/env bash
set -euo pipefail

RUNS=10
SLEEP=120

for i in $(seq 1 $RUNS); do
  echo "==============================" >> logs/cron_youtube.log
  echo "[RUN $i] $(date)" >> logs/cron_youtube.log
  .venv/bin/python -m generator.cli.publish_youtube >> logs/cron_youtube.log 2>&1
  sleep $SLEEP
done
