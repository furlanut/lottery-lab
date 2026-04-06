#!/usr/bin/env bash
# deploy.sh — Deploy automatico Lotto Convergent
# Uso: ./deploy.sh staging|prod

set -euo pipefail

ENV="${1:-}"
if [[ "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    echo "Uso: ./deploy.sh staging|prod"
    exit 1
fi

echo "=== Deploy $ENV ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"

# 1. Lint
echo "--- Lint ---"
ruff check backend/ || { echo "ERRORE: lint fallito"; exit 1; }

# 2. Test
echo "--- Test ---"
python -m pytest backend/tests/ -q || { echo "ERRORE: test falliti"; exit 1; }

# 3. Build
echo "--- Build ---"
COMPOSE_FILE="docker/docker-compose.${ENV}.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "ERRORE: $COMPOSE_FILE non trovato"
    exit 1
fi
docker compose -f "$COMPOSE_FILE" build || { echo "ERRORE: build fallito"; exit 1; }

# 4. Deploy
echo "--- Deploy ---"
docker compose -f "$COMPOSE_FILE" up -d || { echo "ERRORE: deploy fallito"; exit 1; }

# 5. Health check (attendi 10 secondi)
echo "--- Health check ---"
sleep 10
HEALTH_URL="http://localhost:8000/api/v1/health"
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "Health check: OK"
else
    echo "ATTENZIONE: health check fallito, verificare i log"
fi

# 6. Notifica
echo "=== Deploy $ENV completato ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
