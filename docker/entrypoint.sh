#!/bin/bash
set -e

echo "Starting cron..."
service cron start || true

echo "Starting background updater..."
python3 /app/backend/scheduler.py &

echo "Starting uvicorn..."
exec uvicorn lotto_predictor.api:app --host 0.0.0.0 --port 8000
