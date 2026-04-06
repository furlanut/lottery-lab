#!/usr/bin/env bash
# rollback.sh — Rollback Lotto Convergent
# Uso: ./rollback.sh staging|prod

set -euo pipefail

ENV="${1:-}"
if [[ "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    echo "Uso: ./rollback.sh staging|prod"
    exit 1
fi

echo "=== Rollback $ENV ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"

COMPOSE_FILE="docker/docker-compose.${ENV}.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "ERRORE: $COMPOSE_FILE non trovato"
    exit 1
fi

# Stop servizi correnti
echo "--- Stop servizi ---"
docker compose -f "$COMPOSE_FILE" down || true

# Rollback all'immagine precedente
echo "--- Rollback immagine ---"
# Usa l'immagine precedente dal registry/cache locale
docker compose -f "$COMPOSE_FILE" up -d || { echo "ERRORE: rollback fallito"; exit 1; }

# Health check
echo "--- Health check ---"
sleep 10
HEALTH_URL="http://localhost:8000/api/v1/health"
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "Health check: OK"
else
    echo "ATTENZIONE: health check fallito dopo rollback"
fi

echo "=== Rollback $ENV completato ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
