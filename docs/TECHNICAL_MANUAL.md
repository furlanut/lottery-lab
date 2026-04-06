# Manuale Tecnico — Lotto Convergent

Autore: Luca Furlanut
Versione: 0.1.0

## 1. Architettura

Il sistema e composto da 4 moduli principali:

```
INGESTOR → ANALYZER → PREDICTOR → NOTIFIER
    ↓           ↓           ↓           ↓
         ┌──────────────────────┐
         │     PostgreSQL       │
         │ estrazioni           │
         │ previsioni           │
         │ bankroll             │
         │ backtest_runs        │
         └──────────────────────┘
```

- **INGESTOR**: acquisizione dati (scraping, import CSV/TXT, validazione)
- **ANALYZER**: motore analitico (5 filtri convergenti, backtesting)
- **PREDICTOR**: generazione previsioni e money management
- **NOTIFIER**: notifiche push (ntfy) pre/post estrazione

## 2. Stack Tecnologico

| Componente | Tecnologia | Versione |
|-----------|------------|----------|
| Linguaggio backend | Python | 3.12 |
| Framework API | FastAPI | latest |
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.x |
| Migration | Alembic | latest |
| CLI | Typer | latest |
| Lint/Format | Ruff | latest |
| Test | Pytest | latest |
| Frontend | Next.js + React | 14 / 18 |
| Container | Docker + Compose | latest |
| Notifiche | ntfy | - |
| Auth | JWT (PyJWT) | - |

## 3. API

### CLI Commands

```bash
lotto ingest --year 2024              # scarica anno specifico
lotto ingest --update                 # aggiorna ultime estrazioni
lotto ingest --csv path/to/file.csv   # import da CSV
lotto backtest                        # backtest con parametri default
lotto backtest --min-score 4          # solo segnali forti
lotto predict                         # genera previsioni correnti
lotto verify                          # verifica previsioni attive
lotto status                          # bankroll, P&L, previsioni attive
lotto notify --test                   # notifica di test
lotto cycle                           # ciclo completo automatico
```

### REST Endpoints (da implementare)

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/estrazioni` | Lista estrazioni |
| GET | `/api/v1/previsioni` | Previsioni attive |
| GET | `/api/v1/backtest` | Risultati backtesting |
| GET | `/api/v1/status` | Stato bankroll e P&L |
| POST | `/api/v1/predict` | Genera nuove previsioni |

## 4. Database

### Schema

**estrazioni** — Dati storici delle estrazioni del Lotto

| Colonna | Tipo | Note |
|---------|------|------|
| id | SERIAL PK | |
| concorso | INTEGER NOT NULL | Numero concorso |
| data | DATE NOT NULL | Data estrazione |
| ruota | TEXT NOT NULL | BARI, CAGLIARI, ..., VENEZIA |
| n1-n5 | INTEGER NOT NULL | 5 numeri estratti |
| created_at | TIMESTAMP | Default CURRENT_TIMESTAMP |
| | UNIQUE(data, ruota) | |

**previsioni** — Previsioni generate dal sistema

| Colonna | Tipo | Note |
|---------|------|------|
| id | SERIAL PK | |
| data_generazione | DATE NOT NULL | Quando generata |
| data_target_inizio | DATE NOT NULL | Prima estrazione di gioco |
| ruota | TEXT NOT NULL | |
| num_a, num_b | INTEGER NOT NULL | Ambo previsto |
| score | INTEGER NOT NULL | Punteggio convergenza (0-5) |
| filtri | JSONB NOT NULL | Filtri attivati |
| max_colpi | INTEGER DEFAULT 9 | |
| posta | NUMERIC DEFAULT 1.0 | Euro |
| stato | TEXT DEFAULT 'ATTIVA' | ATTIVA/VINTA/PERSA/ANNULLATA |
| colpo_esito | INTEGER | Colpo di uscita |
| vincita | NUMERIC | Importo vinto |

**bankroll** — Registro movimenti bankroll

| Colonna | Tipo | Note |
|---------|------|------|
| id | SERIAL PK | |
| data | DATE NOT NULL | |
| tipo | TEXT NOT NULL | DEPOSITO/GIOCATA/VINCITA/PRELIEVO |
| importo | NUMERIC NOT NULL | +entrata/-uscita |
| saldo | NUMERIC NOT NULL | Saldo dopo operazione |
| previsione_id | INTEGER FK | Riferimento a previsioni |

**backtest_runs** — Log esecuzioni backtesting

| Colonna | Tipo | Note |
|---------|------|------|
| id | SERIAL PK | |
| data_run | TIMESTAMP | |
| parametri | JSONB NOT NULL | Parametri usati |
| risultati | JSONB NOT NULL | Metriche risultanti |

## 5. Autenticazione

- JWT con access token (15 min) e refresh token (7 giorni)
- Header: `Authorization: Bearer <token>`
- Refresh: `POST /api/v1/auth/refresh`
- Da implementare nella fase Foundation Sprint

## 6. Deploy

### Ambiente locale

```bash
docker compose -f docker/docker-compose.local.yml up -d
```

### Staging e Produzione

```bash
./deploy.sh staging    # Deploy su staging
./deploy.sh prod       # Deploy su produzione
./rollback.sh staging  # Rollback staging
./rollback.sh prod     # Rollback produzione
```

Hosting: VPS OVH/Hostinger con Portainer per gestione container.

## 7. Monitoring

- Health check: `GET /api/v1/health` (DB, dipendenze)
- Notifiche: ntfy push per alerting
- Logging strutturato JSON con request_id
- Metriche: hit rate rolling, P&L cumulativo, bankroll

## 8. Troubleshooting

_Da popolare durante lo sviluppo._

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| | | |

## 9. Disaster Recovery

- Backup DB: pg_dump automatico giornaliero
- Retention: 30 giorni
- Restore: `pg_restore` da ultimo backup
- RTO target: < 1 ora
- RPO target: < 24 ore

## 10. Incident Response

Riferimento completo: `runbooks/incident-response.md`

Contatti:
- Responsabile: Luca Furlanut
- Canale notifiche: ntfy
