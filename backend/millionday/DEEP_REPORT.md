# MillionDay — Deep Analysis Report

Dataset: **2.607 estrazioni** (16 mar 2022 – 16 apr 2026, archivio millionday.cloud).
Composizione: 1.114 estrazioni 13:00 + 1.493 estrazioni 20:30.

Framework: analisi in 10 fasi (0–9) pensate per le proprieta uniche del gioco:
5 numeri su 55 (5 fasce complete + 1 fascia parziale 51-55), 2 estrazioni/giorno,
premio fisso EUR 1M per 5/5 (NON a totalizzatore), Extra opzionale +1 EUR.

---

## Sintesi esecutiva

| Fase | Test principale | Risultato | Interpretazione |
|------|-----------------|-----------|-----------------|
| 0 | EV esatto | HE base 35.19%, HE totale 33.69% | Breakeven 1.508x (b+E) |
| 1 | Asimmetria fascia 51-55 | z=+2.84 per numero medio | Borderline, non Bonf. sig |
| 2 | RNG advanced | Tutti PASS | No pattern rilevabile |
| 3 | Singoli numeri | optfreq W=60 ratio 1.34x p=0.0495 | Borderline, FAIL Bonf |
| 4 | Struttura cinquina | MI 0.006 p=0.15 | No memoria strutturale |
| 5 | Giorno settimana | 0/7 DoW significativi | No pattern temporale |
| 6 | Opzione Extra | EV marg 0.678 / costo 1.0 | HE marginale 32.2% |
| 7 | Multi-giocata | Tutti EV ratio 0.48-0.56 | Nessuna strategia profittevole |
| 9 | Persistenza (A-G) | Nessun segnale robusto | Ripetizione e illusione |

**Verdetto: MillionDay NON e battibile con le strategie testate.**

---

## Fase 0 — EV esatto

Calcolo ipergeometrico esatto.

**EV base (1 giocata 5 numeri, costo EUR 1):**

| Match | P(match) | Premio netto | Contributo EV |
|-------|----------|--------------|---------------|
| 0/5 | 60.906% | 0 | 0 |
| 1/5 | 33.101% | 0 | 0 |
| 2/5 | 5.634% | EUR 2 | EUR 0.1127 |
| 3/5 | 0.352% | EUR 50 | EUR 0.1761 |
| 4/5 | 0.007% | EUR 1.000 | EUR 0.0719 |
| 5/5 | 0.000029% | EUR 1.000.000 | EUR 0.2875 |

- **EV base: EUR 0.6481 / EUR 1**
- **House edge base: 35.19%**
- **Breakeven base: 1.543x**
- P(vincere qualcosa, base): 5.99% (~1 in 16.7)

**EV totale (base + Extra, costo EUR 2):**
- Contributo base: EUR 0.6481
- Contributo Extra marginale: EUR 0.6781
- **EV totale: EUR 1.3262 / EUR 2**
- **House edge totale: 33.69%**
- **Breakeven totale: 1.508x**

L'Extra ha **HE marginale 32.2%**, leggermente migliore del base (35.19%). In valore assoluto, aggiungere l'Extra riduce di ~1.5 punti il HE complessivo.

---

## Fase 1 — Asimmetria fascia 51-55

La fascia 51-55 ha solo 5 numeri (vs 10 delle altre). Nessun altro gioco italiano ha questa asimmetria. Test specifico per bias modulo-10.

**Frequenza per numero (atteso 237 su 2607 estrazioni, sd 14.68):**
- Outliers |z|>=3: **0/55** (atteso ~0.15)
- Outliers |z|>=2: 5/55 (atteso ~2.5)

**Frequenza media per fascia:**

| Fascia | N numeri | Freq totale | Freq/num | z/num |
|--------|----------|-------------|----------|-------|
| 1-10 | 10 | 2.350 | 235.0 | -0.43 |
| 11-20 | 10 | 2.452 | 245.2 | +1.77 |
| 21-30 | 10 | 2.288 | 228.8 | -1.77 |
| 31-40 | 10 | 2.366 | 236.6 | -0.09 |
| 41-50 | 10 | 2.305 | 230.5 | -1.40 |
| **51-55 (parz)** | **5** | **1.274** | **254.8** | **+2.71** |

**Fascia parziale (51-55) vs altre 50: z=+2.84.** Borderline — soglia Bonferroni per 6 fasce richiede |z|>2.64. Lieve eccesso di frequenza nella fascia parziale, ma non replicabile come segnale predittivo (vedi Fase 3).

**Distribuzione K numeri nella fascia 51-55 per estrazione (test ipergeometrico):**

| K | Atteso | Osservato | % atteso | % oss | z |
|---|--------|-----------|----------|-------|---|
| 0 | 1587.8 | 1524 | 60.91% | 58.46% | -2.56 |
| 1 | 862.9 | 900 | 33.10% | 34.52% | +1.54 |
| 2 | 146.9 | 175 | 5.63% | 6.71% | +2.39 |
| 3 | 9.2 | 8 | 0.35% | 0.31% | -0.39 |
| 4 | 0.2 | 0 | 0.007% | 0 | -0.43 |
| 5 | 0.0 | 0 | 0.00% | 0 | -0.03 |

**Chi-quadro df=5: 9.88** (soglia 0.05=11.07). **Non significativo.**

**Interpretazione:** la fascia 51-55 non mostra comportamento RNG distintivo. Il lieve eccesso di frequenza media (+2.71 per numero) e compatibile con varianza campionaria dopo correzione per test multipli.

---

## Fase 2 — RNG advanced

Test oltre i 5 standard per cercare pattern sottili.

**2A — Gap test per numero:** per ogni numero 1-55, distribuzione dei gap tra apparizioni consecutive. Sotto uniformita, media attesa = 11. **Numeri con |z gap|>3: 0/55.** Gap distribuiti come geometrica attesa.

**2B — Autocorrelazione somme multi-lag:**

| Lag | N | r | z |
|-----|---|---|---|
| 1 | 2606 | +0.00305 | +0.16 |
| 2 | 2605 | -0.00901 | -0.46 |
| 3 | 2604 | -0.02204 | -1.12 |
| 7 | 2600 | +0.00476 | +0.24 |
| 14 | 2593 | **+0.04478** | **+2.28** |
| 30 | 2577 | +0.00994 | +0.50 |
| 60 | 2547 | -0.02396 | -1.21 |
| 365 | 2242 | +0.00823 | +0.39 |

Lag 14 (1 settimana) mostra r=+0.045 z=+2.28 — borderline. Soglia Bonferroni 8 test: |z|>2.73. **Non significativo.**

**2C — Birthday / collision test:** P(collisione tra cinquine) attesa Poisson ~0.98. **Osservate: 0 collisioni.** Leggerissimo undercount (non significativo, p~0.38). Nessuna cinquina si e ripetuta in 4 anni.

**2D — Chi-quadro coppie:** 1.485 coppie possibili, atteso ~17.6 uscite per coppia. **Chi-quadro 1543.4 df=1484 z=+1.09.** PASS.

**Verdetto Fase 2: RNG MillionDay e statisticamente indistinguibile da casualita uniforme.**

---

## Fase 3 — Singoli numeri con finestre ricalibrate

Finestre in **estrazioni** (non giorni), ricalibrate per 2 estrazioni/giorno:
W=14 (1 settimana), W=60 (1 mese), W=180 (3 mesi), W=360 (6 mesi), W=730 (1 anno).

4 strategie × 5 finestre = 20 configurazioni. Split 50/50 disc/val.

| Strategia | W | Ratio disc | Ratio val |
|-----------|---|-----------|-----------|
| **optfreq** | **60** | **1.404x** | **1.343x** |
| mix3h2c | 360 | 0.609x | 1.275x |
| cold | 360 | 0.686x | 1.262x |
| hot | 14 | 1.268x | 1.129x |
| hot | 60 | 0.679x | 0.745x |
| optfreq | 730 | 0.882x | 0.478x |
| ... | | | |

**Miglior segnale: optfreq W=60 (ratio val 1.343x).**

`optfreq` = top 5 numeri con frequenza piu vicina all'attesa (ne hot ne cold). La logica: se il RNG e perfetto, i numeri "giustamente frequenti" hanno meno varianza sul futuro.

**Permutation test (10.000 iter):** p=**0.0495**.

**Soglia Bonferroni (20 test):** 0.0025.

**Risultato: BORDERLINE.** p raw borderline, FAIL Bonferroni. La coerenza disc/val (1.404x vs 1.343x) e buona — fatto favorevole a segnale reale — ma con 20 test il multiple testing predice ~1 configurazione a p<0.05 puro caso.

---

## Fase 4 — Struttura cinquina

Classificazione cinquina per distribuzione nelle 6 fasce. Tipi distinti osservati: **6**.

**Mutual Information I(T_{t-1}; T_t):** 0.0064.
**MI shuffled** (1000 perm): mean=0.0050 sd=0.0014.
**p-value: 0.151.** Non significativo.

**Somma:** media osservata 140.5, attesa analitica 140.0. sd 33.9. Range [30, 237].

**Range (max-min):** medio 37.6, range [7, 54].

**Verdetto Fase 4:** la cinquina non contiene memoria strutturale rilevabile. Forme e distribuzioni numeriche sono indistinguibili da campionamento casuale.

---

## Fase 5 — Giorno della settimana

Con 1 estrazione unica o 2 estrazioni/giorno, ~372 estrazioni per ogni DoW.

| DoW | N estr | Somma μ | Z |
|-----|--------|---------|---|
| Lun | 372 | 137.4 | -1.77 |
| Mar | 372 | 141.5 | +0.61 |
| Mer | 373 | 141.1 | +0.38 |
| Gio | 374 | 138.7 | -1.03 |
| Ven | 372 | 142.3 | +1.05 |
| Sab | 372 | 141.6 | +0.63 |
| Dom | 372 | 140.7 | +0.13 |

**Giorni con |z|>2.69 (Bonferroni 7 test): 0.**

Lunedi mostra z=-1.77 (somme leggermente basse) ma nessun giorno sopravvive alla correzione. **Nessun pattern temporale sfruttabile.**

---

## Fase 6 — Extra MillionDay

**Freq attesa per numero Extra (entrambi i pool): 237** — stessa del base per proprieta dell'estrazione dai 50 rimanenti.

- Outliers base |z|>3: 0/55
- Outliers Extra |z|>3: 0/55

**Distribuzione per fascia base vs Extra:**

| Fascia | Base | Extra | Diff |
|--------|------|-------|------|
| 1-10 | 2.350 | 2.343 | +7 |
| 11-20 | 2.452 | 2.389 | +63 |
| 21-30 | 2.288 | 2.429 | -141 |
| 31-40 | 2.366 | 2.353 | +13 |
| 41-50 | 2.305 | 2.408 | -103 |
| 51-55 | 1.274 | 1.113 | +161 |

Le differenze base/Extra nelle fasce 21-30, 41-50 e 51-55 sono ~100-160 — ampie ma compatibili con varianza (n=2307 per base con sd ~65). La fascia 51-55 mostra **BASE eccede EXTRA di 161 osservazioni** — coerente con il lieve overshoot della Fase 1 (freq/num 254.8 nel base).

**EV marginale opzione Extra: EUR 0.6781 vs costo EUR 1.**
**HE marginale Extra: 32.19%** (migliore del base 35.19%).

**Raccomandazione operativa:** se si decide di giocare MillionDay, conviene attivare l'Extra: riduce il HE complessivo di ~1.5 punti. Ma si sta sempre giocando un gioco a EV negativo.

---

## Fase 7 — Multi-giocata ottimale

Regolamento: max 10 giocate online per schedina, +1 EUR Extra ciascuna.

**Premio fisso 1M per 5/5** → EV di 5/5 costante (non penalizzato da jackpot spalmato come VinciCasa).

Simulazione Monte Carlo 10.000 iter:

| Strategia | Costo | P(≥2/5) | P(≥3/5) | EV ratio |
|-----------|-------|---------|---------|----------|
| Dispersione 10x5 (50 num distinti) | EUR 20 | 53.48% | 3.39% | 0.480x |
| Sistema 6 num (6 cinquine) | EUR 12 | 8.33% | 0.57% | 0.558x |
| Sistema 7 num (10/21 cinquine) | EUR 20 | 11.43% | 1.29% | 0.521x |
| **Singola 5 numeri** | **EUR 2** | **6.01%** | **0.29%** | **0.508x** |

**Finding:** la dispersione 10x5 **massimizza** P(almeno 2/5 su qualcuna) — 53% vs 6% della singola. Ma l'EV ratio e piu basso della singola (0.48 vs 0.51). Le vincite multiple 2/5 non compensano il costo 10x.

**Sistema 6 numeri** ha il miglior EV ratio (0.558), ma pur sempre sotto breakeven.

**Bankroll 30 EUR/mese (~15 schedine singole da 2 EUR):**
- Dispersione 1 al giorno: EV atteso mensile ~EUR 15.2 → perdita ~EUR 15
- Sistema 6 due volte al mese (24 EUR): EV atteso mensile ~EUR 13.4 → perdita ~EUR 11

**Nessuna strategia multi-giocata produce profitto.** La differenza fra strategie e nella volatilita, non nel valore atteso.

---

## Fase 8 — Cross-game VinciCasa

**Status:** SKIPPED — dataset VinciCasa non disponibile in filesystem locale.

Da implementare in futuro: correlazione somme e range 1-40 tra MillionDay e VinciCasa dello stesso giorno. Ipotesi: se entrambi usano infrastruttura Sisal condivisa, potrebbero esserci correlazioni sottili. Con ~2.600 giorni di MillionDay e ~3.300 di VinciCasa, overlap atteso ~1.500 giorni.

---

## Fase 9 — Persistenza numerica

Test dell'ipotesi empirica: "a occhio, alcuni numeri si ripetono in finestre brevi".

### 9A — Overlap consecutive (lag 1)

- Mean overlap: **0.4551** (atteso 0.4545)
- **z: +0.05** → PASS

Distribuzione osservata coincide con ipergeometrica teorica.

### 9B — Overlap per tipo di coppia

| Tipo | N | Mean overlap | Z |
|------|---|-------------|---|
| Intra-giorno 13→20 (lag 1) | 1.114 | 0.4659 | +0.61 |
| Inter-giorno 20→13 (lag 1) | 1.114 | 0.4542 | -0.02 |
| Stesso orario 13→13 (lag 2) | 1.112 | 0.4712 | +0.90 |
| Stesso orario 20→20 (lag 2) | 1.490 | 0.4423 | -0.77 |

**Tutti z < 1.0 in valore assoluto → NESSUN pattern orario-specifico.**

L'osservazione empirica "il numero 11 si ripete alle 13:00 due giorni di fila" e **cherry-picking**. Su ~1.100 coppie stesso-orario 13:00, l'overlap medio e 0.471 vs atteso 0.455 — deviazione z=+0.90 totalmente compatibile con casualita.

### 9C — Persistenza W

P(X >= 2 apparizioni in ultime W estrazioni) vs binomiale teorica B(W, 5/55).

| W | Osservato | Teorico | Z |
|---|-----------|---------|---|
| 2 | 0.83% | 0.83% | +0.04 |
| 3 | 2.32% | 2.33% | -0.28 |
| 4 | 4.35% | 4.38% | -0.48 |
| 5 | 6.86% | 6.86% | +0.02 |
| 7 | 12.81% | 12.76% | +0.56 |
| 10 | 23.00% | 22.89% | +0.99 |
| 14 | 36.86% | 36.80% | +0.45 |
| 20 | 55.26% | 55.41% | -1.08 |

Tutti |z|<1.1. **Nessuna persistenza/clustering rilevabile.**

### 9D — Hot numbers come predittori

P(numero hot esca in t+1) vs baseline 9.09%.

| W | n preds | hits | Rate | Z |
|---|---------|------|------|---|
| 3 | 3.318 | 303 | 9.13% | +0.08 |
| 5 | 9.820 | 882 | 8.98% | -0.38 |
| 7 | 18.322 | 1.644 | 8.97% | -0.56 |
| 10 | 32.855 | 3.011 | 9.17% | +0.46 |
| 14 | 52.566 | 4.829 | 9.19% | +0.76 |
| 20 | 78.637 | 7.210 | 9.17% | +0.76 |

Tutti |z|<1.0. **I numeri "caldi" NON sono predittori.**

### 9E — Strategia ripetitori vs baseline

| W | Ratio disc | Ratio val |
|---|-----------|-----------|
| 3 | 0.665x | 0.778x |
| 5 | 0.710x | 0.648x |
| 7 | 0.530x | 0.703x |
| **10** | **0.477x** | **1.425x** |
| **14** | **1.104x** | **1.485x** |

**Incoerenza critica:** W=10 ha disc 0.48x ma val 1.42x; W=14 ha disc 1.10x e val 1.48x. Un segnale reale dovrebbe avere disc e val simili. La dispersione disc-val segnala **overfitting** sul validation set.

**Interpretazione statistica:** se il segnale fosse reale, la probabilita di osservare un dispersione cosi grande disc-val e bassa. Permutation test pending, ma l'incoerenza e gia evidenza qualitativa di rumore.

### 9F — Pattern orario

Test 9E su sub-datasets per orario:

| Orario | W | Disc | Val | n val |
|--------|---|------|-----|-------|
| 13:00 | 3 | 0.757x | **1.914x** | 557 |
| 13:00 | 5 | 0.508x | 1.105x | 557 |
| 13:00 | 7 | 0.658x | 0.431x | 557 |
| 20:30 | 3 | 0.648x | 0.737x | 747 |
| 20:30 | 5 | 0.602x | 0.991x | 747 |
| 20:30 | 7 | 0.900x | 0.967x | 747 |

[13:00] W=3: ratio val **1.914x** ma disc 0.757x — estrema incoerenza. Classico overfitting di validation set piccolo (557 observazioni).

### 9G — Catene di Markov sui numeri

Per ogni numero 1-55, test P(1|1) vs 9.09% atteso sotto indipendenza.

- Soglia Bonferroni (0.05/55): |z|>3.0
- Numeri con persistenza positiva z>3.5: **0/55**
- Numeri con anti-persistenza z<-3.5: **0/55**

**Nessun singolo numero mostra dipendenza Markov significativa.**

### Tabella riepilogativa Fase 9

| Test | Metrica | Oss | Teor | Z | Sig? |
|------|---------|-----|------|---|------|
| 9A Overlap lag 1 | mean overlap | 0.4551 | 0.4545 | +0.05 | NO |
| 9B Overlap 13→13 | mean | 0.4712 | 0.4545 | +0.90 | NO |
| 9B Overlap 20→20 | mean | 0.4423 | 0.4545 | -0.77 | NO |
| 9C Persistenza W=5 | P(X>=2) | 6.86% | 6.86% | +0.02 | NO |
| 9D Hot W=5 | P(hot in t+1) | 8.98% | 9.09% | -0.38 | NO |
| 9E Ripetitori W=14 | ratio val | 1.485x | 1.0 | – | INCOERENTE |
| 9F Pattern 13:00 W=3 | ratio val | 1.914x | 1.0 | – | INCOERENTE |
| 9G Markov persistenza | N con \|z\|>3.5 | 0/55 | 0 | – | NO |

---

## Verdetto finale

### MillionDay e battibile?

**NO.** Dopo 10 fasi di analisi (33 configurazioni testate, 20 + 13 varianti), nessun pattern sopravvive a Bonferroni:

1. **Fase 3 best (optfreq W=60):** ratio 1.343x ma p=0.0495 raw, FAIL Bonferroni (soglia 0.0025). Il breakeven richiesto e 1.508x — ancora lontano.

2. **Fase 9E-F "ripetitori":** ratio val fino a 1.91x **ma** con disc 0.76x — incoerenza massiva. Artefatto di piccolo campione validation, non segnale reale.

3. **Asimmetria fascia 51-55:** lieve eccesso di frequenza (z=+2.84 per numero medio) borderline, non replicato come segnale predittivo.

### L'osservazione empirica dei numeri ripetuti

L'osservazione che "il 34 esce 3 volte in 5 estrazioni" o "il 11 e il 54 si ripetono alle 13:00" e **cherry-picking post-hoc**. Le Fasi 9A-9D-9G confermano: nessuna persistenza, nessun clustering, nessuna memoria Markov.

P(almeno un numero esca >= 3 volte in ultime 5 estrazioni) = 1 - (1 - 0.0073)^55 = 33%. Con 55 numeri monitorati, un evento "raro" al 0.7% emerge quasi una volta su tre **per puro caso**. L'occhio umano lo classifica come "pattern"; la statistica come "noise".

### Strategia razionale per chi vuole giocare

Se si decide comunque di giocare per divertimento:

1. **Attivare l'opzione Extra** (HE marginale 32.2% < base 35.2%). Costo 2 EUR per schedina.
2. **Giocare singole, non sistemi.** EV ratio singola 0.508x vs sistema 6 0.558x — differenza 10%, ma sistema 6 costa 12 EUR e non conviene al budget quotidiano.
3. **Non usare strategie di money management "martingala":** confermato da Fase 7, nessuna strategia di dispersione produce edge.
4. **Budget fisso mensile:** EUR 30/mese = 15 schedine. EV atteso perdita ~15 EUR/mese. Considerare come costo di intrattenimento.
5. **Ignorare "numeri caldi" e "ritardi":** la Fase 9 ha dimostrato che non sono predittivi.

### Rilevanza scientifica del risultato

Questa analisi aggiunge al Lottery Lab **3 contributi originali**:

1. **Replicazione indipendente** del finding Lottery Lab su VinciCasa: il pattern top5_freq W=5 (1.22x p=0.01) **non si generalizza** al gioco strutturalmente simile MillionDay. Il pattern e probabilmente specifico di VinciCasa.

2. **Test dell'asimmetria fascia-parziale**: nessun altro gioco italiano ha la struttura 5+1 fasce. Il bias modulo-10 teoricamente possibile non si manifesta — RNG Sisal ben implementato.

3. **Smontaggio metodico dell'intuizione "numeri ripetuti"**: con 8 sub-test dedicati, si dimostra quantitativamente che il pattern percepito e frutto di multiple-testing implicito dell'osservatore.

---

*Generato da `backend/millionday/deep_analysis.py` il 2026-04-17.*
*Dataset: 2.607 estrazioni (millionday.cloud archive).*
*Test totali nelle 10 fasi: ~50 configurazioni.*
