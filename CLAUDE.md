# Lotto Convergent

Sistema predittivo per ambi secchi del Lotto Italiano con filtri convergenti.

## Stack

- **Backend:** Python 3.12 + FastAPI
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis (futuro, non ancora implementato)
- **Frontend:** React 18 / Next.js 14 (fase 4)
- **Infra:** Docker + Docker Compose, VPS OVH/Hostinger

## Comandi frequenti

```bash
# Build backend
pip install -e ".[dev]"

# Lint backend
ruff check . && ruff format --check .

# Test backend
pytest -v

# Build frontend
cd frontend && npm run build

# Deploy
./deploy.sh staging       # Deploy su staging
./deploy.sh prod          # Deploy su produzione

# Rollback
./rollback.sh staging     # Rollback staging
./rollback.sh prod        # Rollback produzione

# Logs e status
docker compose logs -f
docker compose ps
```

## Regole Obbligatorie — Commit e Deploy

### Conventional Commits — OBBLIGATORIO

Formato: `type(scope): descrizione breve`

| Tipo | Bump | Quando |
|------|------|--------|
| `feat` | MINOR | Nuova funzionalita |
| `fix` | PATCH | Correzione bug |
| `refactor` | PATCH | Ristrutturazione senza cambiare comportamento |
| `perf` | PATCH | Miglioramento performance |
| `docs` | nessuno | Solo documentazione |
| `chore` | nessuno | Manutenzione |
| `test` | nessuno | Solo test |

Scope: `ingestor`, `analyzer`, `predictor`, `notifier`, `db`, `ui`, `infra`, `docs`

### Procedura deploy

`deploy.sh` gestisce tutto. `rollback.sh` annulla tutto.
**NON fare mai deploy manuali o push separati dal flusso automatizzato.**

## Regola — Gestione Piano di Lavoro

PRIMA di aggiornare o cancellare un piano esistente: verifica che TUTTE le fasi precedenti siano completate. Se anche una sola non e completata, mostra lo stato e chiedi conferma.

## Struttura directory

```
lotto-convergent/
├── backend/
│   ├── lotto_predictor/
│   │   ├── __init__.py
│   │   ├── cli.py                    # Entry point CLI (typer)
│   │   ├── config.py                 # Configurazione centralizzata
│   │   ├── models/
│   │   │   ├── database.py           # SQLAlchemy + PostgreSQL
│   │   │   └── schemas.py            # Pydantic schemas
│   │   ├── ingestor/
│   │   │   ├── scraper.py            # Scraping archivio estrazioni
│   │   │   ├── csv_import.py         # Import CSV/TXT
│   │   │   └── validator.py          # Validazione dati
│   │   ├── analyzer/
│   │   │   ├── cyclometry.py         # Funzioni ciclometriche
│   │   │   ├── filters/
│   │   │   │   ├── base.py           # Abstract base filter
│   │   │   │   ├── vincolo90.py      # Vincolo Differenziale 90
│   │   │   │   ├── isotopismo.py     # Isotopismo distanziale
│   │   │   │   ├── ritardo.py        # Ritardo critico
│   │   │   │   ├── decade.py         # Coerenza decina
│   │   │   │   └── somma91.py        # Diametrali caldi
│   │   │   ├── convergence.py        # Scoring engine
│   │   │   └── backtester.py         # Framework backtesting
│   │   ├── predictor/
│   │   │   ├── generator.py          # Generatore previsioni
│   │   │   └── money_mgmt.py         # Money management
│   │   ├── notifier/
│   │   │   ├── ntfy.py               # Push via ntfy.sh
│   │   │   └── formatter.py          # Formattazione messaggi
│   │   └── utils/
│   │       └── stats.py              # Utility statistiche
│   └── tests/
├── frontend/                          # Next.js (fase 4)
├── docker/
│   ├── docker-compose.local.yml
│   ├── docker-compose.staging.yml
│   └── docker-compose.prod.yml
├── scripts/
│   └── bump-versions.sh
├── docs/
│   ├── QUALITY_STANDARDS.md
│   ├── ERROR_CONTRACT.md
│   ├── TECH_DEBT.md
│   ├── TECHNICAL_MANUAL.md
│   ├── USER_MANUAL.md
│   ├── adr/
│   ├── lessons/
│   └── checklists/
├── runbooks/
│   ├── incident-response.md
│   └── rollback.md
├── archivio_dati/                     # Dati storici (1874-2026)
├── doc/files/                         # Spec e prototipi
├── version.json
├── CHANGELOG.md
├── deploy.sh
└── rollback.sh
```

## Convenzioni

| Aspetto | Convenzione |
|---------|-------------|
| Naming variabili (Python) | snake_case |
| Naming variabili (JS/TS) | camelCase |
| Naming file (Python) | snake_case.py |
| Naming file (frontend) | PascalCase.tsx (componenti), kebab-case.ts (utility) |
| Naming DB | snake_case |
| API response format | snake_case |
| API versioning | /api/v1/ prefix |
| Auth pattern | JWT (access + refresh token) |
| Error format | Come da `docs/ERROR_CONTRACT.md` |

## Standard di Qualita

Le regole universali sono in `docs/QUALITY_STANDARDS.md` (10 domini, 40+ regole).
Seguile SEMPRE. Priorita: **Sicurezza > Pulizia > Resilienza > Test.**

## Lezioni Apprese

| Area | File | Strato |
|------|------|--------|
| Universali | `docs/lessons/universal.md` | Qualita (2) |
| Python/FastAPI | `docs/lessons/python-fastapi.md` | Stack (3) |

**Regola:** Bug non banale -> Lesson Card nel file appropriato. NON in questo file.

## Documentazione Operativa

| Documento | Scopo |
|-----------|-------|
| `docs/ERROR_CONTRACT.md` | Formato errori API standard |
| `docs/TECH_DEBT.md` | Registro debito tecnico |
| `docs/TECHNICAL_MANUAL.md` | Manuale tecnico (dev/IT) |
| `docs/USER_MANUAL.md` | Manuale utente |
| `docs/adr/` | Architecture Decision Records |
| `runbooks/incident-response.md` | Protocollo incidenti |
| `runbooks/rollback.md` | Procedura rollback |
| `docs/RESEARCH_PAPER.md` | Paper di ricerca completo |

## Regola — Aggiornamento Paper di Ricerca (OBBLIGATORIO)

Ogni volta che viene eseguita una nuova analisi statistica, test, backtest,
o ricerca sui dati del Lotto, il paper `docs/RESEARCH_PAPER.md` DEVE essere
aggiornato con:
1. **Motivazione**: perche si e deciso di fare questo test
2. **Metodo**: come e stato condotto (dataset, split, metriche)
3. **Risultati**: numeri esatti (segnali, hit, ratio, p-value)
4. **Conclusione**: cosa significa il risultato per il progetto

Il paper e il documento vivente che traccia l'intero percorso di ricerca.
Senza aggiornamento, le scoperte vengono perse e i test ripetuti inutilmente.

---

## Routine Post-Implementazione (OBBLIGATORIA)

**Dopo OGNI feature, eseguire SEMPRE:**

### 1. Build e Lint
```bash
ruff check . && ruff format --check .
cd frontend && npm run build
```

### 2. Check Correttezza
- Nessun import mancante
- Nessun errore di tipizzazione
- Query DB sicure (parametri bind)
- Nessun debug output rimasto

### 3. Check Coerenza
- Tipi frontend <-> backend matchano
- Route registrate, servizi nel DI
- Formato errori conforme all'Error Contract

### 4. Check Consistenza
- Niente rotto, cache invalidata, backward compat

### 5. Se schema DB toccato -> `docs/checklists/migration-safety.md`

### 6. Se frontend toccato -> a11y check (keyboard, semantic HTML, contrast)

### 7. Se endpoint nuovi/modificati -> documentazione aggiornata

### 8. Se funzionalita cambiate -> aggiorna manuali tecnico/utente

### 9. Deploy Staging
```bash
./deploy.sh staging
```

**NON saltare MAI la routine.**
