#!/bin/bash
set -e

# Start cron daemon in background
echo "Starting cron daemon..."
cron

# Start uvicorn
echo "Starting uvicorn..."
exec uvicorn lotto_predictor.api:app --host 0.0.0.0 --port 8000
