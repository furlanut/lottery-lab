#!/bin/bash
set -e

# Start cron daemon in background
echo "Starting cron daemon..."
service cron start 2>/dev/null || cron 2>/dev/null || true

# Fallback: start a background Python scheduler if cron fails
python3 -c "
import subprocess, time, threading

def run_update():
    while True:
        try:
            subprocess.run(['python', 'backend/auto_update.py'], cwd='/app', timeout=120,
                         capture_output=True, text=True)
        except Exception:
            pass
        time.sleep(600)  # every 10 minutes

t = threading.Thread(target=run_update, daemon=True)
t.start()
print('Background updater started (every 10 min)')
" &

# Start uvicorn (foreground)
echo "Starting uvicorn..."
exec uvicorn lotto_predictor.api:app --host 0.0.0.0 --port 8000
