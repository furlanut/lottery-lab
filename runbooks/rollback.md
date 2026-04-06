# Procedura di Rollback

Autore: Luca Furlanut

## Quando fare rollback

- Health check fallito dopo deploy
- Error rate > 5% per 5 minuti
- Funzionalita critica non disponibile
- Dati corrotti dopo migration

## Procedura

### 1. Valuta la situazione
- Controlla i log: `docker compose logs -f`
- Verifica health: `curl http://localhost:8000/api/v1/health`

### 2. Esegui il rollback
```bash
./rollback.sh staging   # o prod
```

### 3. Verifica
- [ ] Health check OK
- [ ] Nessun errore nei log
- [ ] Dati integri

### 4. Post-rollback
- [ ] Notifica il team
- [ ] Apri un incident (se P1/P2)
- [ ] Investiga la root cause
- [ ] Crea Lesson Card se necessario

## Database rollback

Se la migration e stata applicata:
```bash
# Rollback ultima migration
alembic downgrade -1

# Rollback a revisione specifica
alembic downgrade <revision_id>
```

ATTENZIONE: il rollback di migration con DROP COLUMN perde dati irreversibilmente.
