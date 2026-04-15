"""Background scheduler — runs auto_update every 5 minutes."""

import subprocess
import time

print("Scheduler started: auto_update every 60s", flush=True)

while True:
    try:
        subprocess.run(
            ["python3", "backend/auto_update.py"],
            cwd="/app",
            timeout=120,
        )
    except Exception as e:
        print(f"Scheduler error: {e}", flush=True)
    time.sleep(60)
