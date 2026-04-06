# LOTTO ITALIANO — Sistema Predittivo a Filtri Convergenti per Ambi Secchi

## Documento di Specifica Tecnica per Sviluppo Strutturato

**Autore:** Luca (CTO SMED S.r.l.) + Claude Opus  
**Data:** Aprile 2026  
**Versione:** 1.0  
**Target:** Claude Code — sviluppo su VPS OVH/Hostinger  
**Stack previsto:** Python 3.11+, Docker, SQLite/PostgreSQL, ntfy/Telegram, cron

---

## 1. CONTESTO E OBIETTIVO

### 1.1 Cos'è questo progetto

Un sistema software che analizza le estrazioni del Lotto Italiano, applica filtri statistici e ciclometrici convergenti, e genera previsioni di ambi secchi con un punteggio di confidenza. L'obiettivo non è "battere il banco" in senso assoluto (il valore atteso del Lotto è strutturalmente negativo), ma costruire un framework disciplinato che:

1. Seleziona giocate SOLO quando più filtri indipendenti convergono sullo stesso ambo
2. Gestisce il bankroll con rigore matematico (progressione flat, stop loss, take profit)
3. Traccia ogni previsione e ogni esito per misurare il vantaggio reale nel tempo
4. Automatizza il ciclo completo: ingestione dati → analisi → previsione → notifica → verifica

### 1.2 Perché ambi secchi

L'ambo secco (2 numeri su 1 ruota) paga 250 volte la posta con probabilità 1/400.5 per estrazione. È la sorte con il miglior rapporto rischio/rendimento del Lotto:

| Sorte | Payout | Probabilità | Valore atteso per €1 | Edge del banco |
|-------|--------|-------------|----------------------|----------------|
| Estratto | 11.23x | 1/18 | €0.624 | 37.6% |
| Ambo secco | 250x | 1/400.5 | €0.624 | 37.6% |
| Terno secco | 4500x | 1/11748 | €0.383 | 61.7% |
| Quaterna | 120000x | 1/511038 | €0.235 | 76.5% |

L'ambo secco e l'estratto hanno lo stesso edge del banco (37.6%), ma l'ambo secco ha il vantaggio di un moltiplicatore alto: una singola vincita a €1 copre 250 giocate a vuoto. Questo rende le progressioni molto più sostenibili rispetto ad altre sorti.

### 1.3 Il breakeven

Per essere profittevole con 3 ambi secchi per ciclo, 10 colpi per ciclo, €1 per ambo:

- Costo ciclo: €30
- Vincita per hit: €250
- Breakeven: 30/250 = 12% hit rate per ciclo
- Probabilità casuale di almeno 1 hit: ~7.2% per ciclo
- **Vantaggio minimo necessario: 1.66x rispetto al caso**

---

## 2. FONDAMENTI TEORICI

### 2.1 La ciclometria

La ciclometria è una disciplina nata negli anni '60 per opera di Fabrizio Arrigoni (Fabarri), avvocato e studioso del Lotto. L'idea fondante è rappresentare i 90 numeri del Lotto su una circonferenza e studiare le relazioni geometriche tra i numeri estratti.

**Concetti chiave:**

- **Distanza ciclometrica**: la differenza tra due numeri, ridotta al range 0-45. Se `|a-b| > 45`, la distanza è `90 - |a-b|`. Esempio: distanza tra 5 e 80 = `|5-80| = 75`, poiché `75 > 45` → `90-75 = 15`.

- **Coppia diametrale**: due numeri la cui somma è 91 (diametralmente opposti sulla circonferenza). Esempio: 23-68, 1-46, 45-90. Ce ne sono esattamente 45.

- **Vincolo Differenziale 90**: una "quadratura" in cui la somma delle distanze ciclometriche di due coppie di numeri (presi da due ruote diverse) è esattamente 45 (metà cerchio). Questa condizione genera candidati per ambo secco calcolando il "capogioco" K1 = fuori90(a+b) e il suo diametrale K2 = diametrale(K1).

- **Isotopismo**: quando la stessa distanza ciclometrica si ripete nella stessa posizione estrattiva (es. il 1° estratto di Bari e il 1° estratto di Cagliari hanno distanza 9) tra estrazioni consecutive.

- **Quadrato ciclometrico**: una struttura a 4 numeri in cui le distanze ciclometriche formano un pattern regolare (es. due lati uguali).

- **Fuori 90**: operazione di riduzione modulo 90. Se un calcolo produce un numero > 90, si sottrae 90 ripetutamente. Se produce 0, il risultato è 90. Il range valido è sempre 1-90.

### 2.2 Analisi statistica di base

Il Lotto Italiano estrae 5 numeri (senza reimmissione) da un'urna di 90 per ciascuna delle 11 ruote. Le estrazioni sono indipendenti tra ruote e tra concorsi.

**Proprietà matematiche verificate sul dataset:**

- I 90 numeri sono equidistribuiti (frequenza attesa: N_estrazioni × 5/90 per numero per ruota)
- Le 45 distanze ciclometriche sono equidistribuite (ratio osservato/atteso: 0.89-1.06, compatibile con rumore statistico)
- Le 9 decine sono equidistribuite
- La probabilità che almeno 2 numeri su 5 condividano la stessa decina è ~71.5% (paradosso del compleanno applicato a 5 palline in 9 categorie)
- Le coppie diametrali (distanza 45) appaiono con frequenza compatibile al caso (ratio 0.97)

### 2.3 La tesi della convergenza

Nessun singolo filtro ciclometrico o statistico produce un vantaggio misurabile rispetto al caso (tutti i ratio testati sono nel range 0.95-1.11x). Tuttavia, l'ipotesi di lavoro è che la **convergenza di più filtri indipendenti** possa amplificare un segnale debole. Se ogni filtro ha un lieve bias (1.05-1.10x), la combinazione di 3-4 filtri potrebbe produrre un vantaggio composto di 1.5-3x.

**Evidenza dal backtesting iniziale (339 estrazioni, out-of-sample):**

| Score (filtri convergenti) | Segnali | Hit | Hit rate | Baseline | Ratio |
|---------------------------|---------|-----|----------|----------|-------|
| 3 (tre filtri) | 9228 | 216 | 2.34% | 2.22% | 1.05x |
| 4 (quattro filtri) | 72 | 5 | 6.94% | 2.22% | 3.12x |

Il dato a score 4 (3.12x) è il più promettente ma su un campione molto piccolo (72 segnali, 5 hit). Serve validazione su dataset completo.

---

## 3. SCOPERTE DALL'ANALISI PRELIMINARE

### 3.1 Dataset utilizzato

339 estrazioni dal 10/10/2015 al 30/12/2025, 10 ruote (esclusa Nazionale), scraped da archivioestrazionilotto.it. Il sito mostra solo ~30-38 estrazioni per anno sulla pagina principale — il dataset è quindi parziale (~20% del totale per quel periodo).

### 3.2 Risultati dei metodi singoli

| Metodo | Segnali | Hit | Hit% | Baseline% | Ratio | Verdetto |
|--------|---------|-----|------|-----------|-------|----------|
| Ponfig (distanza 9 inter-ruota) | 335 | 77 | 23.0% | 23.7% | 0.97x | ❌ Non funziona |
| Intra-decina | 2858 | 383 | 13.4% | 12.6% | 1.06x | ⚠️ Marginale |
| Diametrali (somma 91) | 16950 | 6764 | 39.9% | 40.2% | 0.99x | ❌ Random |
| Vincolo Diff. 90 | 500 | 168 | 33.6% | 30.3% | 1.11x | ⚠️ Interessante |

### 3.3 Distanze ciclometriche

La distribuzione delle distanze è quasi perfettamente uniforme:
- Distanza più frequente: 17 (ratio 1.058)
- Distanza meno frequente: 37 (ratio 0.894)
- Nessuna distanza devia più di ±10% dall'atteso

Questo conferma che le estrazioni sono indistinguibili da un generatore casuale uniforme, almeno per quanto riguarda le distanze intra-estrazione.

### 3.4 Correlazioni inter-ruota

La distanza 9 (chiave del metodo Ponfig) tra ruote consecutive nella stessa posizione:
- Range ratio: 0.80 (Cagliari-Firenze) → 1.35 (Torino-Venezia)
- Nessuna coppia di ruote mostra una deviazione statisticamente significativa
- La coppia Torino-Venezia a 1.35x è interessante ma su campione piccolo

### 3.5 Ambi più frequenti

I top ambi per ruota hanno frequenza 5-6 su 339 estrazioni. L'atteso per un ambo casuale è ~339×10/(C(90,2)) ≈ 0.85 uscite. Frequenza 5-6 è ~6-7x l'atteso, ma è compatibile con la distribuzione di Poisson (con 4005 ambi possibili, ci si aspetta che i top abbiano frequenze 5-7).

### 3.6 Il dato chiave: score 4 a 3.12x

Quando 4 filtri convergono (vincolo90 + isotopismo + coerenza decina + ritardo critico), l'hit rate osservato è 3.12x il baseline. Su 72 segnali e 5 hit, l'intervallo di confidenza al 95% (binomiale) è circa [1.1x, 7.3x]. Il centro dell'intervallo è ben sopra il breakeven di 1.66x, ma il limite inferiore no. Serve più campione.

---

## 4. ARCHITETTURA DEL SISTEMA

### 4.1 Componenti

```
┌─────────────────────────────────────────────────────────────┐
│                    LOTTO PREDICTOR                          │
├─────────────┬───────────────┬───────────────┬──────────────┤
│  INGESTOR   │   ANALYZER    │  PREDICTOR    │  NOTIFIER    │
│  (data in)  │  (backtest)   │  (signals)    │  (alerts)    │
├─────────────┼───────────────┼───────────────┼──────────────┤
│ • Scraper   │ • Filter eng. │ • Convergence │ • Telegram   │
│ • CSV import│ • Backtester  │ • Scoring     │ • ntfy       │
│ • Validator │ • Monte Carlo │ • Ranking     │ • Dashboard  │
│ • DB writer │ • Stats       │ • Money mgmt  │ • Logger     │
└──────┬──────┴───────┬───────┴───────┬───────┴──────┬───────┘
       │              │               │              │
       └──────────────┴───────┬───────┴──────────────┘
                              │
                     ┌────────┴────────┐
                     │    DATABASE     │
                     │  SQLite/Postgres│
                     │  • estrazioni   │
                     │  • previsioni   │
                     │  • esiti        │
                     │  • bankroll     │
                     └─────────────────┘
```

### 4.2 Moduli

**4.2.1 INGESTOR — Acquisizione dati**

Responsabilità: recuperare le estrazioni del Lotto e salvarle nel database.

Fonti dati (in ordine di preferenza):
1. Scraping di archivioestrazionilotto.it (affidabile, HTML semplice)
2. Scraping di lottologia.com (ricco ma JS-heavy)
3. Import CSV manuale (fallback)

Schema dati:
```sql
CREATE TABLE estrazioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concorso INTEGER NOT NULL,         -- numero concorso
    data DATE NOT NULL,                -- data estrazione
    ruota TEXT NOT NULL,               -- BARI, CAGLIARI, ..., VENEZIA
    n1 INTEGER NOT NULL,               -- 1° estratto
    n2 INTEGER NOT NULL,               -- 2° estratto
    n3 INTEGER NOT NULL,               -- 3° estratto
    n4 INTEGER NOT NULL,               -- 4° estratto
    n5 INTEGER NOT NULL,               -- 5° estratto
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data, ruota)
);

CREATE TABLE previsioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_generazione DATE NOT NULL,    -- quando è stata generata
    data_target_inizio DATE NOT NULL,  -- prima estrazione di gioco
    ruota TEXT NOT NULL,
    num_a INTEGER NOT NULL,            -- primo numero dell'ambo
    num_b INTEGER NOT NULL,            -- secondo numero dell'ambo
    score INTEGER NOT NULL,            -- punteggio convergenza (0-5)
    filtri TEXT NOT NULL,              -- JSON array dei filtri attivati
    max_colpi INTEGER DEFAULT 9,       -- massimo colpi di gioco
    posta REAL DEFAULT 1.0,            -- posta in euro
    stato TEXT DEFAULT 'ATTIVA',       -- ATTIVA, VINTA, PERSA, ANNULLATA
    colpo_esito INTEGER,               -- a quale colpo è uscita (null se persa)
    data_esito DATE,                   -- data dell'esito
    vincita REAL,                      -- importo vinto (null se persa)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bankroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    tipo TEXT NOT NULL,                -- DEPOSITO, GIOCATA, VINCITA, PRELIEVO
    importo REAL NOT NULL,             -- positivo=entrata, negativo=uscita
    saldo REAL NOT NULL,               -- saldo dopo operazione
    previsione_id INTEGER,             -- FK a previsioni (per GIOCATA/VINCITA)
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE backtest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_run TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parametri TEXT NOT NULL,            -- JSON con tutti i parametri
    train_start DATE,
    train_end DATE,
    test_start DATE,
    test_end DATE,
    risultati TEXT NOT NULL,            -- JSON con metriche
    note TEXT
);
```

Requisiti:
- Scraping robusto con retry e fallback tra fonti
- Validazione: ogni estrazione deve avere esattamente 5 numeri distinti nel range 1-90
- Deduplicazione: no inserimenti duplicati (UNIQUE su data+ruota)
- Storico minimo: dal 1946 (post-guerra, formato moderno con 10 ruote). Ideale: dal 2005 (aggiunta ruota Nazionale)
- Aggiornamento: automatico post-estrazione (martedì, giovedì, sabato sera)

**4.2.2 ANALYZER — Motore di analisi**

5 filtri implementati, ciascuno indipendente:

**Filtro 1: Vincolo Differenziale 90 (F_V90)**

Input: estrazione corrente su tutte le ruote
Logica:
1. Per ogni coppia di ruote (w1, w2), per ogni coppia di posizioni (p1,p2) e (p3,p4):
   - Calcola d1 = cyclo_dist(w1[p1], w2[p2])
   - Calcola d2 = cyclo_dist(w1[p3], w2[p4])
   - Se d1 + d2 == 45: SEGNALE
2. Genera capogioco K1 = fuori90(w1[p1] + w2[p2])
3. Genera K2 = diametrale(K1) = fuori90(K1 + 45)
4. Ambi candidati: (K1, w1[p1]), (K1, w2[p2]), (K1, w1[p3]), (K1, w2[p4]), idem per K2
Output: lista di ambi candidati con ruote di riferimento

**Filtro 2: Isotopismo distanziale (F_ISO)**

Input: ultime 5 estrazioni sulla stessa ruota
Logica:
1. Per ogni posizione (1°-5° estratto), calcola la distanza ciclometrica tra il numero corrente e quello della stessa posizione nelle estrazioni precedenti
2. Se la stessa distanza si ripete 2+ volte consecutive: SEGNALE
3. Proietta il prossimo numero: base ± distanza_ripetuta
Output: lista di ambi candidati (base, proiezione)

**Filtro 3: Ritardo critico (F_RIT)**

Input: storico completo della ruota, coppia di numeri candidata
Logica:
1. Calcola il ritardo corrente della coppia (ambo) sulla ruota specifica
2. Se ritardo >= 150 estrazioni (37% del ritardo medio teorico di 400): SEGNALE
3. Peso proporzionale: più alto il ritardo, più alto il contributo allo score
Output: flag booleano + valore ritardo
Nota: il ritardo medio di un ambo su 1 ruota è ~400 estrazioni. Un ritardo di 150+ indica che la coppia è nella "zona calda" secondo la legge dei grandi numeri (pur essendo ogni estrazione indipendente, il ritardo si distribuisce geometricamente e i ritardi estremi sono rari).

**Filtro 4: Coerenza di decina (F_DEC)**

Input: coppia candidata (a, b)
Logica:
1. Se a e b appartengono alla stessa decina (1-10, 11-20, ..., 81-90): SEGNALE
2. Altrimenti, se la distanza ciclometrica è <= 10: SEGNALE debole (score 0.5)
Output: score 0/0.5/1
Razionale: il 71.5% delle estrazioni contiene almeno un ambo intra-decina. Le coppie intra-decina hanno una probabilità strutturalmente più alta di co-occorrere.

**Filtro 5: Somma 91 — diametrali caldi (F_S91)**

Input: estrazione corrente, storico
Logica:
1. Per ogni numero estratto n, calcola il suo diametrale d = fuori90(n + 45)
2. Se d ha un ritardo >= 15 estrazioni sulla stessa ruota: SEGNALE
3. Candidato: ambo (n, d)
Output: lista di ambi candidati
Razionale: la somma 91 è il valore medio atteso per una coppia di numeri (45.5 × 2). Le coppie diametrali sono un pilastro della ciclometria di Fabarri.

**4.2.3 PREDICTOR — Motore di previsione**

Logica del punteggio di convergenza:
```python
score = 0
filters_active = []

if F_V90 attivato per la coppia:
    score += 1
    filters_active.append('vincolo90')

if F_ISO attivato per la coppia:
    score += 1
    filters_active.append('isotopismo')

if F_RIT attivato per la coppia:
    score += 1
    filters_active.append(f'ritardo({valore})')

if F_DEC score > 0:
    score += round(F_DEC score)  # 0 o 1
    filters_active.append('decade')

if F_S91 attivato per la coppia:
    score += 1
    filters_active.append('somma91')

# Score finale: 0-5
```

Regole di output:
- Score >= 4: **GIOCA** — segnale forte, massima priorità
- Score == 3: **ATTENZIONE** — segnale moderato, gioca solo se bankroll lo consente
- Score <= 2: **NON GIOCARE** — rumore, nessun edge atteso
- Max 3-4 ambi per ciclo di gioco (evita diluizione)
- Preferenza per ruote con più segnali convergenti

**4.2.4 NOTIFIER — Notifiche**

- Pre-estrazione (18:00 nei giorni di estrazione: mar, gio, sab): invia previsioni attive
- Post-estrazione (21:30): verifica esiti, aggiorna stato, notifica vincite
- Report settimanale: P&L, hit rate rolling, confronto con baseline
- Canali: ntfy (push notification) + Telegram bot (opzionale)

Formato notifica pre-estrazione:
```
🎯 LOTTO PREDICTOR — Previsioni 06/04/2026

SCORE 4 ⭐⭐⭐⭐
  54-58 GENOVA (V90+ISO+DEC+RIT)
  52-53 NAPOLI (V90+ISO+DEC+RIT)

SCORE 3 ⭐⭐⭐
  34-36 BARI (V90+DEC+RIT)

Ciclo: 3 ambi × €1 × 9 colpi = €27
Bankroll: €473 | P&L: -€27
```

Formato notifica post-estrazione:
```
📊 ESITO Estrazione 06/04/2026

BARI:  15 42 67 33 88
GENOVA: 54 21 58 76 03  ← 54-58 CENTRATO! 🎉

✅ VINCITA: €250 (ambo 54-58 GENOVA, score 4, colpo 1)
Bankroll: €723 | P&L: +€223
```

### 4.3 Money management

**Strategia: flat betting con controllo del rischio**

Parametri:
- Posta per ambo: €1 (configurabile)
- Max ambi per ciclo: 3
- Max colpi per ciclo: 9
- Bankroll iniziale consigliato: €600
- Stop loss: -€750 (125% del bankroll)
- Take profit: rivalutazione dopo ogni vincita
- NO progressione Martingala (rischio rovina)

Logica:
```python
def decide_play(bankroll, score, current_cycle_cost):
    if bankroll < 100:  # safety margin
        return False, "Bankroll troppo basso"
    if score < 3:
        return False, "Score insufficiente"
    if score == 3 and bankroll < 300:
        return False, "Score 3 richiede bankroll >= €300"
    if score >= 4:
        return True, "Segnale forte"
    return True, "Segnale moderato"
```

---

## 5. FORMULE E ALGORITMI

### 5.1 Funzioni ciclometriche

```python
def cyclo_dist(a: int, b: int) -> int:
    """Distanza ciclometrica tra due numeri (0-45)."""
    d = abs(a - b)
    return d if d <= 45 else 90 - d

def diametrale(n: int) -> int:
    """Numero diametralmente opposto (somma 91)."""
    r = (n + 45) % 90
    return r if r != 0 else 90

def fuori90(n: int) -> int:
    """Riduzione al range 1-90."""
    while n > 90: n -= 90
    while n <= 0: n += 90
    return n

def decade(n: int) -> int:
    """Decina di appartenenza (0=1-10, 1=11-20, ..., 8=81-90)."""
    return (n - 1) // 10

def cadenza(n: int) -> int:
    """Ultima cifra (0 per multipli di 10)."""
    return n % 10

def figura(n: int) -> int:
    """Radice digitale (somma iterata delle cifre)."""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n
```

### 5.2 Calcolo probabilistico

```python
from math import comb

# Ambi possibili nei 90 numeri
TOTAL_AMBI = comb(90, 2)  # = 4005

# Ambi in un'estrazione (5 numeri -> 10 ambi)
AMBI_PER_DRAW = comb(5, 2)  # = 10

# Probabilità di un ambo secco specifico su 1 ruota, 1 estrazione
P_AMBO = comb(88, 3) / comb(90, 5)  # = 109736/43949268 ≈ 1/400.5

# Probabilità di NON uscita in N estrazioni
def p_no_hit(n_draws, n_ambi=1, n_ruote=1):
    p_single = 1 - P_AMBO
    return p_single ** (n_draws * n_ambi * n_ruote)

# Probabilità di almeno 1 hit
def p_at_least_one(n_draws, n_ambi=1, n_ruote=1):
    return 1 - p_no_hit(n_draws, n_ambi, n_ruote)

# Ritardo medio teorico
RITARDO_MEDIO = 1 / P_AMBO  # ≈ 400.5 estrazioni

# Valore atteso per €1 su ambo secco
EV = 250 * P_AMBO  # ≈ 0.624 → perdita attesa 37.6%
```

### 5.3 Calcolo del breakeven

```python
def breakeven_advantage(posta, n_ambi, n_colpi, payout=250):
    """Calcola il vantaggio minimo necessario per breakeven."""
    costo_ciclo = posta * n_ambi * n_colpi
    vincita = posta * payout
    
    # Hit rate minimo per ciclo
    min_hit_rate_cycle = costo_ciclo / vincita
    
    # Hit rate casuale per ciclo
    random_hit_rate = 1 - (1 - P_AMBO) ** (n_colpi * n_ambi)
    
    # Vantaggio necessario
    advantage = min_hit_rate_cycle / random_hit_rate
    
    return {
        'costo_ciclo': costo_ciclo,
        'vincita': vincita,
        'min_hit_rate': min_hit_rate_cycle,
        'random_hit_rate': random_hit_rate,
        'advantage_needed': advantage
    }
```

---

## 6. BACKTESTING — RISULTATI E METODOLOGIA

### 6.1 Metodologia

- Split temporale 70/30: train (estrazioni 1-237, 2015-2023) / test (238-339, 2023-2025)
- Nessun parametro ottimizzato sul test set (zero look-ahead bias)
- Baseline: probabilità teorica esatta (non simulata)
- Hit verificato: entrambi i numeri dell'ambo presenti nella stessa estrazione sulla ruota target

### 6.2 Risultati per metodo singolo (test set)

Tutti i metodi singoli producono ratio nel range 0.97-1.11x. Nessuno è individualmente significativo.

### 6.3 Risultati filtri convergenti (test set)

- Score 3: 2.34% vs 2.22% baseline = 1.05x (NON significativo, troppi segnali)
- Score 4: 6.94% vs 2.22% baseline = 3.12x (PROMETTENTE, campione piccolo)

### 6.4 Limiti del backtesting attuale

1. **Campione ridotto**: 339 estrazioni sono ~20% del disponibile 2015-2025. I 72 segnali a score 4 sono insufficienti per significatività statistica robusta (p-value stimato ~0.08, serve < 0.05).
2. **Bias di selezione sui filtri**: i 5 filtri sono stati scelti basandosi su conoscenza pregressa (ciclometria classica), non su discovery data-driven. Questo riduce il rischio di overfitting ma potrebbe anche limitare il potenziale.
3. **Ritardi calcolati solo sul dataset disponibile**: con 339 estrazioni, un "ritardo 338" significa semplicemente "mai visto nel dataset", non necessariamente un ritardo reale alto.

---

## 7. OBIETTIVI DI SVILUPPO

### 7.1 Fase 1 — Infrastruttura (priorità alta)

- [ ] Setup progetto Python con struttura modulare (package `lotto_predictor`)
- [ ] Database SQLite con schema delle 4 tabelle
- [ ] Scraper robusto per archivioestrazionilotto.it (con retry, rate limiting, parsing HTML)
- [ ] Comando CLI: `lotto ingest --year 2024` (ingestione per anno)
- [ ] Comando CLI: `lotto ingest --update` (aggiorna ultime estrazioni)
- [ ] Validazione dati: no duplicati, range 1-90, 5 numeri distinti per ruota
- [ ] Import CSV per caricamento bulk di archivi storici esterni

### 7.2 Fase 2 — Motore analitico (priorità alta)

- [ ] Implementazione dei 5 filtri come classi indipendenti con interfaccia comune
- [ ] Motore di convergenza (scoring 0-5)
- [ ] Backtester con split temporale configurabile
- [ ] Report statistico: hit rate per score, ratio vs baseline, intervalli di confidenza
- [ ] Comando CLI: `lotto backtest --train-end 2023-12-31 --min-score 3`
- [ ] Export risultati in JSON per analisi esterna

### 7.3 Fase 3 — Previsioni e notifiche (priorità media)

- [ ] Generatore previsioni: `lotto predict` → top ambi per score
- [ ] Integrazione ntfy: notifica push pre/post estrazione
- [ ] Verifica automatica esiti post-estrazione
- [ ] Tracking bankroll con log completo
- [ ] Cron job per ciclo automatico (scrape → predict → notify → verify)
- [ ] Comando CLI: `lotto status` → bankroll, previsioni attive, P&L

### 7.4 Fase 4 — Ottimizzazione e ricerca (priorità bassa)

- [ ] Aggiungere nuovi filtri: frequenza delle cadenze, figure, pattern temporali
- [ ] Machine learning leggero: random forest su features ciclometriche per scoring
- [ ] Monte Carlo con 10M simulazioni per validazione statistica
- [ ] Dashboard web (React/HTML statico con grafici Chart.js)
- [ ] A/B testing: confronto score >= 3 vs score >= 4 su live data
- [ ] Analisi di correlazione tra ruote (ci sono ruote che "anticipano" altre?)

### 7.5 Fase 5 — Deploy (priorità media)

- [ ] Dockerfile per containerizzazione
- [ ] docker-compose.yml con volume per DB persistente
- [ ] Deploy su VPS OVH con Portainer
- [ ] Health check e alerting se il sistema non gira
- [ ] Backup automatico DB

---

## 8. STRUTTURA DEL PROGETTO

```
lotto-predictor/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example                    # NTFY_TOPIC, TELEGRAM_TOKEN, etc.
│
├── lotto_predictor/
│   ├── __init__.py
│   ├── cli.py                      # Entry point CLI (click/typer)
│   ├── config.py                   # Configurazione centralizzata
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLAlchemy/raw SQLite setup
│   │   └── schemas.py              # Dataclass per Estrazione, Previsione, etc.
│   │
│   ├── ingestor/
│   │   ├── __init__.py
│   │   ├── scraper.py              # Scraping archivioestrazionilotto.it
│   │   ├── csv_import.py           # Import da CSV
│   │   └── validator.py            # Validazione dati
│   │
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── cyclometry.py           # Funzioni ciclometriche base
│   │   ├── filters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Abstract base filter
│   │   │   ├── vincolo90.py        # Filtro vincolo differenziale
│   │   │   ├── isotopismo.py       # Filtro isotopismo distanziale
│   │   │   ├── ritardo.py          # Filtro ritardo critico
│   │   │   ├── decade.py           # Filtro coerenza decina
│   │   │   └── somma91.py          # Filtro diametrali caldi
│   │   ├── convergence.py          # Scoring engine
│   │   └── backtester.py           # Backtesting framework
│   │
│   ├── predictor/
│   │   ├── __init__.py
│   │   ├── generator.py            # Generatore previsioni
│   │   └── money_mgmt.py           # Money management / bankroll
│   │
│   ├── notifier/
│   │   ├── __init__.py
│   │   ├── ntfy.py                 # Push via ntfy.sh
│   │   ├── telegram.py             # Bot Telegram (opzionale)
│   │   └── formatter.py            # Formattazione messaggi
│   │
│   └── utils/
│       ├── __init__.py
│       └── stats.py                # Utility statistiche
│
├── data/
│   ├── lotto.db                    # Database SQLite
│   └── imports/                    # CSV per import manuale
│
├── tests/
│   ├── test_cyclometry.py
│   ├── test_filters.py
│   ├── test_convergence.py
│   └── test_backtester.py
│
└── scripts/
    ├── setup_db.py                 # Inizializzazione DB
    ├── initial_import.py           # Import storico completo
    └── cron_cycle.py               # Script per cron job
```

---

## 9. CONFIGURAZIONE

```python
# config.py — valori di default, sovrascrivibili da .env

# Database
DB_PATH = "data/lotto.db"

# Scraper
SCRAPER_BASE_URL = "https://www.archivioestrazionilotto.it"
SCRAPER_RETRY = 3
SCRAPER_DELAY = 2  # secondi tra richieste

# Filtri
FILTER_RITARDO_SOGLIA = 150       # estrazioni minime per segnale ritardo
FILTER_ISO_LOOKBACK = 5           # estrazioni indietro per isotopismo
FILTER_ISO_MIN_REPEAT = 2         # ripetizioni minime della distanza
FILTER_S91_RITARDO_DIAMETRALE = 15  # ritardo minimo del diametrale
FILTER_V90_RUOTE = [               # coppie di ruote per vincolo 90
    ('BARI','CAGLIARI'), ('BARI','MILANO'), ('CAGLIARI','FIRENZE'),
    ('FIRENZE','GENOVA'), ('GENOVA','MILANO'), ('MILANO','NAPOLI'),
    ('NAPOLI','PALERMO'), ('PALERMO','ROMA'), ('ROMA','TORINO'),
    ('TORINO','VENEZIA'), ('BARI','NAPOLI'), ('FIRENZE','ROMA'),
]

# Scoring
MIN_SCORE_PLAY = 3                # score minimo per giocare
MIN_SCORE_STRONG = 4              # score per segnale forte

# Money management
POSTA_DEFAULT = 1.0               # euro per ambo
MAX_AMBI_PER_CICLO = 3
MAX_COLPI = 9
PAYOUT_AMBO = 250
BANKROLL_INIZIALE = 600
STOP_LOSS = -750
BANKROLL_MIN_PLAY = 100           # sotto questo, stop

# Notifiche
NTFY_TOPIC = ""                   # da .env
NTFY_SERVER = "https://ntfy.sh"
TELEGRAM_TOKEN = ""               # da .env
TELEGRAM_CHAT_ID = ""             # da .env

# Scheduling
GIORNI_ESTRAZIONE = [1, 3, 5]     # martedì=1, giovedì=3, sabato=5
ORA_PREVISIONE = "18:00"
ORA_VERIFICA = "21:30"

# Backtesting
BACKTEST_TRAIN_RATIO = 0.7
```

---

## 10. COMANDI CLI

```bash
# Ingestione dati
lotto ingest --year 2024                    # scarica anno specifico
lotto ingest --year 2015 --year-end 2025    # range di anni
lotto ingest --update                       # aggiorna ultime estrazioni
lotto ingest --csv data/imports/archive.csv # import da CSV

# Backtesting
lotto backtest                              # backtest con parametri default
lotto backtest --train-end 2023-12-31       # split specifico
lotto backtest --min-score 4                # solo segnali forti
lotto backtest --export results.json        # export risultati

# Previsioni
lotto predict                               # genera previsioni correnti
lotto predict --min-score 4                 # solo score >= 4
lotto predict --dry-run                     # senza salvare in DB

# Verifica
lotto verify                                # verifica previsioni attive vs ultime estrazioni
lotto verify --date 2026-04-03              # verifica data specifica

# Status
lotto status                                # bankroll, previsioni attive, P&L
lotto status --history 30                   # ultimi 30 giorni

# Notifiche
lotto notify --test                         # invia notifica di test
lotto notify --predict                      # invia previsioni correnti
lotto notify --verify                       # invia esiti

# Ciclo completo (per cron)
lotto cycle                                 # ingest → predict → notify
lotto cycle --verify                        # verify → notify esiti
```

---

## 11. NOTE PER LO SVILUPPATORE

### 11.1 Principi guida

1. **Misurabilità**: ogni decisione deve essere tracciabile e verificabile. Ogni previsione va salvata PRIMA dell'estrazione.
2. **Onestà**: il sistema deve mostrare sia le vincite che le perdite. Il P&L cumulativo è la metrica ultima.
3. **Disciplina**: il sistema NON deve mai giocare senza segnale. "Non giocare" è l'output più frequente e più importante.
4. **Modularità**: ogni filtro deve essere testabile e disattivabile indipendentemente.
5. **Parsimonia**: iniziare con SQLite, migrare a PostgreSQL solo se necessario.

### 11.2 Anti-pattern da evitare

- MAI ottimizzare parametri sul test set
- MAI cambiare le regole dopo aver visto il risultato
- MAI usare progressione Martingala (rischio rovina esponenziale)
- MAI giocare più di quanto il bankroll consenta
- MAI considerare il sistema "infallibile" — il Lotto è un gioco d'azzardo

### 11.3 Testing

- Unit test per tutte le funzioni ciclometriche (valori noti)
- Test di regressione: il backtester deve produrre risultati identici con gli stessi dati
- Test di integrazione: ciclo completo ingest → predict → verify su dati sintetici
- Proprietà note da verificare: cyclo_dist(a,b) == cyclo_dist(b,a), diametrale(diametrale(n)) == n, fuori90 sempre in range 1-90

### 11.4 Dataset CSV di partenza

Il file `lotto_archive.csv` allegato contiene 339 estrazioni (2015-2025) con colonne: `date,wheel,n1,n2,n3,n4,n5`. Il sistema deve essere in grado di importarlo come seed iniziale e poi arricchire il DB con scraping.

---

## 12. METRICHE DI SUCCESSO

| Metrica | Target minimo | Target ottimale |
|---------|--------------|-----------------|
| Ratio vs baseline (score 4) | > 2.0x | > 3.0x |
| Hit rate per ciclo | > 12% | > 20% |
| ROI su 100 cicli | > 0% | > 30% |
| Max drawdown | < €750 | < €300 |
| Previsioni con score >= 3 per settimana | 1-5 | 2-3 |
| Turni senza gioco / turni totali | > 60% | > 75% |

---

## APPENDICE A: Glossario

| Termine | Definizione |
|---------|------------|
| Ambo secco | Giocata di esattamente 2 numeri su 1+ ruote. Paga 250x la posta. |
| Ambata | Un singolo numero giocato per estratto. Paga 11.23x. |
| Ciclo | Sequenza di N estrazioni consecutive durante le quali si gioca lo stesso ambo. |
| Colpo | Singola estrazione all'interno di un ciclo. |
| Distanza ciclometrica | |a-b| ridotto al range 0-45 tramite complemento a 90. |
| Diametrale | Numero opposto sulla circonferenza (n+45 mod 90). Somma 91. |
| Fuori 90 | Operazione di riduzione modulo 90 al range 1-90. |
| Ritardo | Numero di estrazioni consecutive in cui una coppia/numero non è uscita. |
| Score | Punteggio di convergenza 0-5. Quanti filtri indipendenti confermano un ambo. |
| Sfaldamento | Uscita di un numero/ambo che interrompe un ritardo. |
| Vincolo Differenziale 90 | Condizione in cui la somma di due distanze ciclometriche è 45 (o 90 in distanza piena). |

## APPENDICE B: File allegati

1. `lotto_archive.csv` — 339 estrazioni (2015-2025), formato CSV
2. `lotto_backtest.py` — Engine di backtesting v1.0 (analisi singoli metodi)
3. `lotto_convergent_engine.py` — Engine a filtri convergenti v2.0
4. `backtest_results.json` — Risultati del backtesting iniziale
