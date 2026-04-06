# Manuale Utente — Lotto Convergent

Autore: Luca Furlanut
Versione: 0.1.0

## 1. Introduzione

Lotto Convergent e un sistema di analisi predittiva per il Lotto Italiano. Analizza le estrazioni storiche usando 5 filtri ciclometrici e statistici indipendenti. Quando piu filtri convergono sullo stesso ambo, il sistema genera un segnale con un punteggio di confidenza (score 0-5).

**Filosofia**: nessun singolo metodo batte il caso. Ma la convergenza di piu segnali indipendenti puo produrre un vantaggio sfruttabile. Il sistema gioca SOLO quando i filtri convergono, e la maggior parte dei turni la raccomandazione e: non giocare.

## 2. Primi Passi

### Requisiti

- Python 3.12+
- PostgreSQL 16
- Docker (opzionale, per deploy)

### Setup

```bash
# Clona il repository
git clone <repo-url>
cd lotto-convergent

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate

# Installa dipendenze
pip install -e ".[dev]"

# Configura database
cp .env.example .env
# Modifica .env con le credenziali PostgreSQL

# Import dati storici
lotto ingest --csv doc/files/lotto_archive.csv

# Primo backtest
lotto backtest
```

## 3. Funzionalita

### Ingestione Dati

Il sistema acquisisce le estrazioni del Lotto da diverse fonti:
- Scraping automatico da archivi online
- Import CSV/TXT da file locali
- Aggiornamento automatico post-estrazione

### I 5 Filtri Convergenti

1. **Vincolo Differenziale 90 (F_V90)**: cerca quadrature ciclometriche tra coppie di ruote dove la somma delle distanze ciclometriche e 45
2. **Isotopismo Distanziale (F_ISO)**: cerca distanze ciclometriche ripetute nella stessa posizione tra estrazioni consecutive
3. **Ritardo Critico (F_RIT)**: identifica coppie nella "zona calda" (ritardo >= 150 estrazioni)
4. **Coerenza Decina (F_DEC)**: favorisce ambi nella stessa decina (es. 31-38)
5. **Somma 91 — Diametrali Caldi (F_S91)**: cerca numeri il cui diametrale ha ritardo alto

### Punteggio di Convergenza

| Score | Significato | Azione |
|-------|------------|--------|
| 0-2 | Rumore | NON giocare |
| 3 | Segnale moderato | Giocare se bankroll lo consente |
| 4-5 | Segnale forte | Giocare con priorita massima |

### Notifiche

- **Pre-estrazione** (18:00 mar/gio/sab): previsioni attive con score e filtri
- **Post-estrazione** (21:30): esiti, vincite, aggiornamento bankroll
- **Report settimanale**: P&L, hit rate, confronto con baseline

### Money Management

- Posta costante: €1 per ambo (NO Martingala)
- Max 3 ambi per ciclo, 9 colpi per ciclo
- Bankroll consigliato: €600
- Stop loss: -€750
- Il sistema decide automaticamente se giocare o no in base a score e bankroll

## 4. FAQ

**D: Il sistema garantisce vincite?**
R: No. Il Lotto ha un valore atteso strutturalmente negativo (-37.6%). Il sistema cerca di sfruttare la convergenza dei filtri, ma non elimina il rischio.

**D: Cosa significa "score 4"?**
R: Significa che 4 filtri indipendenti convergono sullo stesso ambo. Nei test preliminari, questo ha mostrato un ratio di 3.12x rispetto al caso.

**D: Quanto serve come bankroll minimo?**
R: €600 consigliati. Il sistema smette di giocare sotto €100 di bankroll.

**D: Quante volte a settimana si gioca?**
R: Dipende dai segnali. La maggior parte delle settimane: 0-2 giocate. Il sistema NON forza giocate.

## 5. Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| Nessun segnale generato | Normale: la maggior parte dei turni non ha segnali forti |
| Errore connessione DB | Verificare che PostgreSQL sia avviato e .env sia configurato |
| Scraper non funziona | Il sito potrebbe aver cambiato struttura. Usare import CSV |
| Notifiche non arrivano | Verificare NTFY_TOPIC in .env |

## 6. Contatti

- **Autore:** Luca Furlanut
- **Segnalazione bug:** aprire una issue nel repository

## 7. Novita Versione

### v0.1.0 (Aprile 2026)
- Inizializzazione progetto
- Documentazione base
- Archivio dati storici (1874-2026)
