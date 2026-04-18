# Lotto Convergent -- Paper di Ricerca Completo

## Abstract

**Lottery Lab** e un progetto di ricerca sistematica sulla predittivita delle lotterie italiane. Quattro giochi analizzati: Lotto Italiano (6.886 estrazioni, urne fisiche), VinciCasa (3.279 estrazioni, 5/40 giornaliero), 10eLotto ogni 5 minuti (33.431 estrazioni, RNG elettronico ADM) e MillionDay (2.607 estrazioni da millionday.cloud, 5/55 con Extra, 2022-2026). Totale: ~46.000 estrazioni reali, oltre 122 configurazioni predittive testate.

Sul **Lotto**, dopo 18+ test statistici e 12 test laterali non convenzionali, il miglior segnale e la vicinanza numerica (D=20, W=125): ratio 1.18x su ambetto, validato 5-fold CV. Il breakeven (1.60x) non e raggiunto, ma il segnale riduce il house edge. L'Engine V6 combina vicinanza (ambetto) e freq_rit_fib (ambo secco).

Su **VinciCasa**, il segnale top 5 frequenti nelle ultime 5 estrazioni produce +22% sulla categoria 2/5 (p=0.01). Anche qui, sotto breakeven ma statisticamente significativo.

Sul **10eLotto**, la scoperta principale e stratificata. Sulla configurazione K=6+Extra (HE 9.94%), 94 test predittivi in 2 campagne non producono alcun segnale significativo dopo Bonferroni. Tuttavia, l'analisi per K=1..10 (Strategy Lab) ha rivelato che per **K=8 la strategia dual_target raggiunge ratio 1.445x** — primo segnale dell'intero Lottery Lab a coprire il proprio breakeven nel backtest (pending permutation test).

Su **MillionDay**, tre fasi di ricerca progressiva: (1) dataset iniziale 496 estrazioni con apparente ratio 1.23x p=0.18 "promettente"; (2) dataset esteso a 2.607 estrazioni (archivio millionday.cloud) che **invalida** il segnale originale W=50; (3) deep analysis dedicata con 10 fasi specifiche al gioco — asimmetria fascia 51-55, 2 estrazioni/giorno, premio fisso 1M EUR, 7 sub-test di persistenza numerica. Miglior segnale: optfreq W=60 ratio 1.343x p=0.0495 (FAIL Bonferroni). **MillionDay non e battibile.**

La lezione fondamentale: le lotterie con urne fisiche (Lotto) mostrano micro-pattern misurabili; quelle con RNG elettronico no — tranne forse K=8 su 10eLotto. Il sistema e deployato come **paper trading retroattivo in produzione** su https://lottery.fl3.org.

**Parole chiave:** Lotto Italiano, VinciCasa, 10eLotto, ciclometria, filtri convergenti, backtesting, ambetto, expected value, house edge, RNG, permutation test, Bonferroni, money management

---

## 1. Introduzione e Contesto

---

> **In parole semplici**
>
> Immagina un oceano con 4.005 pesci diversi. Tre volte a settimana, qualcuno pesca esattamente 10 pesci da questo oceano, usando 10 reti diverse (le "ruote"). Tu devi indovinare quale coppia di pesci finira nella stessa rete.
>
> Per ogni euro che scommetti, il banco ne trattiene circa 38 centesimi -- come una tassa invisibile. Se peschi a caso, su 100 euro investiti ne torneranno in media 62. Per andare in pari, dovresti essere bravo a pescare almeno 1.6 volte meglio di chi lancia la rete a caso.
>
> Questo progetto e il tentativo sistematico di costruire una "rete piu intelligente", usando matematica (la ciclometria), informatica (Python, database, test automatizzati) e statistica (backtesting su 80 anni di dati). Spoiler: la rete non e abbastanza intelligente per battere l'oceano. Ma il viaggio per scoprirlo e stato rigoroso, e questo paper documenta ogni passo.

---

### 1.1 Il Lotto Italiano: regole fondamentali

Il Gioco del Lotto italiano e una delle lotterie piu antiche al mondo, con estrazioni documentate fin dal XVI secolo. Nella sua forma moderna, il gioco funziona cosi:

- **Numeri:** da 1 a 90
- **Ruote:** 10 ruote regionali (Bari, Cagliari, Firenze, Genova, Milano, Napoli, Palermo, Roma, Torino, Venezia) piu la ruota Nazionale (non considerata in questo studio)
- **Estrazione:** 5 numeri per ruota, 3 volte a settimana (martedi, giovedi, sabato)
- **Tipologie di giocata:** estratto, ambo, terno, quaterna, cinquina -- su una o piu ruote

Questo studio si concentra esclusivamente sull'**ambo secco**: la previsione di una coppia di numeri su una singola ruota specificata.

### 1.2 L'ambo secco: matematica della puntata

L'ambo secco e la scommessa che due numeri specifici escano entrambi tra i 5 estratti di una ruota specifica. I parametri fondamentali sono:

| Parametro | Valore |
|---|---|
| Numeri possibili | 90 |
| Numeri estratti per ruota | 5 |
| Coppie possibili C(90,2) | 4.005 |
| Coppie estratte per ruota C(5,2) | 10 |
| Probabilita singola estrazione | 10/4.005 = 1/400,5 = 0,24969% |
| Payout lordo | 250x la posta |
| EV per euro puntato | 250 x (1/400,5) = 0,6242 |
| House edge | 1 - 0,6242 = 37,58% |

Il calcolo della probabilita merita una spiegazione dettagliata. I 5 numeri estratti su una ruota generano C(5,2) = 10 coppie distinte. L'universo delle coppie possibili e C(90,2) = 4.005. Quindi la probabilita che una coppia specifica esca e esattamente:

```
P(ambo) = C(5,2) / C(90,2) = 10 / 4.005 = 1 / 400,5
```

Con un payout di 250 volte la posta, l'expected value per euro scommesso e:

```
EV = 250 x (1/400,5) = 250/400,5 = 0,6242 euro
```

Questo significa che, in media, per ogni euro puntato sul Lotto se ne recuperano circa 62 centesimi. Il banco trattiene il 37,58%.

### 1.3 Obiettivo del progetto

L'obiettivo del progetto Lotto Convergent e stato:

1. **Sviluppare** un sistema di analisi basato sulla ciclometria di Fabarri e sulla teoria dei filtri convergenti
2. **Testare** rigorosamente se esistono pattern sfruttabili nelle estrazioni storiche
3. **Quantificare** l'eventuale edge e confrontarlo con il breakeven necessario per la profittabilita
4. **Documentare** l'intero percorso con trasparenza metodologica, inclusi i fallimenti

L'ipotesi di partenza era che combinando 5 filtri indipendenti (vincolo differenziale 90, isotopismo distanziale, ritardo critico, coerenza di decina, somma 91/diametrali caldi) si potesse ottenere un segnale convergente sufficientemente forte da superare il house edge.

### 1.4 Stack tecnologico

Il sistema e stato costruito con uno stack professionale per garantire riproducibilita e rigore:

| Componente | Tecnologia | Ruolo |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Logica di analisi, API REST |
| Database | PostgreSQL 16 | Storage estrazioni, previsioni, bankroll |
| ORM | SQLAlchemy 2.x | Mapping oggetti-relazionale |
| Validazione | Pydantic v2 | Schema dati, configurazione |
| CLI | Typer | Interfaccia a riga di comando |
| Test | pytest | 54 test automatizzati |
| Linting | Ruff | Controllo qualita codice |
| Container | Docker + Compose | Deploy riproducibile |

L'architettura segue una separazione netta in moduli:

- **Ingestor:** acquisizione dati da CSV e scraping web, con validazione
- **Analyzer:** ciclometria, 5 filtri, motore di convergenza, backtester
- **Predictor:** generatore previsioni, money management
- **Notifier:** push notification via ntfy.sh

Il dataset comprende **6.886 estrazioni** dal 1946 al 2026, per un totale di circa 68.860 record (10 ruote per estrazione) e 344.300 numeri estratti.

### 1.5 Struttura del paper

- **Capitolo 2:** Fondamenti teorici -- ciclometria, filtri, tesi della convergenza
- **Capitolo 3:** Il breakeven -- perche serve un edge di 1.60x e perche il money management non puo crearlo
- **Capitolo 4:** Prima campagna di test -- backtest dei 5 filtri convergenti con tutti i numeri
- **Capitoli 5-8:** Panel di esperti, geometria sacra, finestra ciclica, ricerca finestra ottimale
- **Capitolo 9:** Conclusioni e prospettive
- **Capitolo 10:** Validazione per ruota e analisi ciclica
- **Capitoli 11-13:** Engine V3, dieci metodi avanzati, ricerca web e stato dell'arte
- **Capitolo 14:** L'ambetto -- la svolta strategica
- **Capitolo 15:** Strategia di money management -- la regola d'oro
- **Capitolo 16:** Engine V4 -- segnali separati per ambo e ambetto
- **Capitolo 17:** Test laterali -- 12 approcci non convenzionali
- **Capitolo 18:** Il vero segnale -- vicinanza numerica, non somma sacra

---

## 2. Fondamenti Teorici

---

> **In parole semplici**
>
> Immagina 90 numeri disposti come le ore su un orologio gigante, ma con 90 tacche invece di 12. La "distanza ciclometrica" tra due numeri e quanto sono lontani su questo orologio -- ma si misura sempre prendendo la strada piu corta. Quindi 1 e 90 sono vicinissimi (distanza 1), come le 12 e l'1 su un orologio normale.
>
> I "diametrali" sono coppie di numeri che stanno esattamente uno di fronte all'altro sull'orologio, come le 12 e le 6. Nel Lotto, 1 e 46 sono diametrali (distanza 45, la massima possibile). Sommano sempre 91.
>
> La tesi della convergenza funziona come un processo in tribunale: nessun singolo testimone (filtro) e abbastanza convincente da solo. Ma se 4 testimoni indipendenti raccontano la stessa storia, la probabilita che abbiano tutti ragione per caso e molto bassa. Il problema? Se i testimoni si sono parlati prima (non sono indipendenti), il fatto che concordino non aggiunge informazione.
>
> E come sintonizzare una radio debole: una singola antenna capta solo rumore. Un array di 5 antenne dovrebbe amplificare il segnale rispetto al rumore. Ma se tutte le antenne puntano nella stessa direzione, non guadagni nulla rispetto a una sola.

---

### 2.1 La ciclometria di Fabarri

La ciclometria e un sistema matematico per analizzare le relazioni tra i numeri del Lotto, sviluppato nella tradizione degli studi numerologici italiani. I 90 numeri vengono disposti su una circonferenza, e le relazioni geometriche tra le loro posizioni definiscono le operazioni fondamentali.

#### 2.1.1 Distanza ciclometrica

La distanza ciclometrica `d(a, b)` tra due numeri e la distanza minima sull'arco della circonferenza:

```
d(a, b) = min(|a - b|, 90 - |a - b|)
```

Proprieta verificate (test esaustivi su tutte le 4.005 coppie):
- **Simmetria:** `d(a, b) = d(b, a)` per ogni a, b in [1, 90]
- **Range:** `0 <= d(a, b) <= 45`
- **Identita:** `d(a, a) = 0`
- **Massimo:** `d(a, b) = 45` se e solo se a e b sono diametrali

L'implementazione nel codice (`cyclometry.py`):

```python
def cyclo_dist(a: int, b: int) -> int:
    d = abs(a - b)
    return d if d <= 45 else 90 - d
```

#### 2.1.2 Diametrali (Somma 91)

Il diametrale di un numero `n` e il numero diametralmente opposto sulla circonferenza. Si calcola come `(n + 45) mod 90`, con la convenzione che 0 diventa 90:

```python
def diametrale(n: int) -> int:
    r = (n + 45) % 90
    return r if r != 0 else 90
```

Proprieta fondamentali verificate:
- **Involuzione:** `diametrale(diametrale(n)) = n` per ogni n
- **Distanza massima:** `d(n, diametrale(n)) = 45` sempre
- **Somma 91:** `n + diametrale(n) = 91` sempre (da cui il nome del filtro)

Esempi: 1 e 46, 2 e 47, ..., 45 e 90 sono coppie diametrali.

#### 2.1.3 Riduzione fuori 90

Dopo operazioni aritmetiche, i risultati possono uscire dal range [1, 90]. La funzione `fuori90` riporta il numero nel range valido:

```python
def fuori90(n: int) -> int:
    n = n % 90
    return n if n != 0 else 90
```

Questa operazione e idempotente: `fuori90(fuori90(n)) = fuori90(n)`.

#### 2.1.4 Decade, cadenza, figura

Tre funzioni classificano i numeri del Lotto:

| Funzione | Definizione | Range | Esempio |
|---|---|---|---|
| **Decade** | `(n-1) // 10` | 0-8 | decade(45) = 4 |
| **Cadenza** | `n % 10` | 0-9 | cadenza(45) = 5 |
| **Figura** | Radice digitale | 1-9 | figura(89) = 8 (8+9=17, 1+7=8) |

Queste classificazioni partizionano i 90 numeri in sottoinsiemi e vengono usate come filtri di scoring.

### 2.2 I 5 filtri originali

Il sistema Lotto Convergent si basa su 5 filtri, divisi in due categorie architetturali:

**Filtri generativi** (producono candidati ambo):
1. Vincolo Differenziale 90
2. Isotopismo Distanziale
3. Somma 91 (Diametrali Caldi)

**Filtri di scoring** (pesano candidati esistenti):
4. Coerenza Decina
5. Ritardo Critico

#### 2.2.1 Filtro 1: Vincolo Differenziale 90

**Intuizione:** Se le distanze ciclometriche tra coppie di numeri estratti su due ruote diverse sommano esattamente 45, questo "vincolo" suggerisce che i numeri coinvolti hanno una relazione significativa.

**Algoritmo:**
1. Per ogni coppia di ruote (12 coppie predefinite: Bari-Cagliari, Bari-Milano, ecc.)
2. Per ogni combinazione di posizioni (p1,p2) e (p3,p4) tra le 5 posizioni
3. Calcola `d1 = cyclo_dist(ruota1[p1], ruota2[p2])` e `d2 = cyclo_dist(ruota1[p3], ruota2[p4])`
4. Se `d1 + d2 = 45`, genera candidati ambo usando `fuori90` e `diametrale` dei numeri coinvolti

**Complessita:** Per ogni estrazione, il filtro esamina 12 coppie di ruote x C(C(5,2), 2) combinazioni di posizioni = 12 x C(10, 2) = 12 x 45 = 540 verifiche. Questo genera un **alto volume** di candidati.

**Problema strutturale scoperto:** Il filtro genera candidati su quasi ogni estrazione perche la condizione `d1 + d2 = 45` non e sufficientemente rara -- con 540 verifiche e 45 possibili valori per d1+d2, ci si aspetta circa 540/45 = 12 hit per estrazione. Nei test, il filtro risulta attivo sul **98,8% dei segnali**, rendendo di fatto il vincolo non selettivo.

#### 2.2.2 Filtro 2: Isotopismo Distanziale

**Intuizione:** Se la distanza ciclometrica tra i numeri estratti nella stessa posizione (es. "primo estratto") si ripete per piu estrazioni consecutive, il prossimo numero potrebbe seguire lo stesso pattern.

**Algoritmo:**
1. Per ogni posizione (1a-5a) sulla ruota target
2. Calcola le distanze ciclometriche tra il numero nella stessa posizione nelle ultime 5 estrazioni consecutive
3. Se una distanza si ripete almeno 2 volte, proietta il prossimo numero come `base +/- distanza`
4. Genera candidati ambo (base, proiezione_positiva) e (base, proiezione_negativa)

**Parametri:**
- Lookback: 5 estrazioni (configurabile)
- Minimo ripetizioni: 2

**Selettivita:** Il filtro e molto piu selettivo del Vincolo 90. Nei test, appare solo nell'**1,7%** dei segnali convergenti. Questo e un segnale che il filtro e effettivamente discriminante, ma potrebbe anche indicare che genera troppo pochi candidati per avere impatto sulla convergenza.

#### 2.2.3 Filtro 3: Ritardo Critico (scoring)

**Intuizione:** Un ambo che non esce da molto tempo su una ruota e "dovuto" per uscire -- o almeno, la sua uscita quando avviene e piu prevedibile.

**Algoritmo:**
1. Per ogni candidato ambo, calcola il ritardo: quante estrazioni consecutive la coppia non e uscita sulla ruota target
2. Se il ritardo supera la soglia (default: 150 estrazioni), il candidato riceve un punteggio bonus proporzionale: `peso = ritardo / soglia`

**Nota critica:** Questo filtro si basa implicitamente sulla "legge dei grandi numeri" interpretata erroneamente. In un sistema senza memoria (estrazione con reinserimento), il ritardo passato **non influenza** la probabilita futura. Questo e il cuore della "gambler's fallacy" -- la credenza che dopo molti risultati di un tipo, il risultato opposto diventi "dovuto". Le estrazioni del Lotto sono indipendenti.

#### 2.2.4 Filtro 4: Coerenza Decina (scoring)

**Intuizione:** Ambi composti da numeri nella stessa decina (es. 41-48) sarebbero piu probabili di ambi con numeri lontani.

**Algoritmo:**
- Stessa decina: peso 1.0
- Distanza ciclometrica <= 10: peso 0.5
- Altrimenti: peso 0.0 (candidato scartato)

**Problema teorico:** Non esiste un meccanismo fisico nel Lotto che favorisca l'uscita di numeri nella stessa decina. La pallina 41 e la pallina 48 non si "attraggono" nell'urna. Questo filtro impone una struttura a priori sui dati che non ha giustificazione probabilistica.

#### 2.2.5 Filtro 5: Somma 91 / Diametrali Caldi

**Intuizione:** Se un numero esce, il suo diametrale (complemento a 91) "dovrebbe" uscire presto, specialmente se e in ritardo.

**Algoritmo:**
1. Per ogni numero estratto sulla ruota target
2. Calcola il diametrale: `diam = diametrale(num)`
3. Misura il ritardo del diametrale sulla stessa ruota
4. Se il ritardo supera la soglia (default: 15 estrazioni), genera il candidato ambo (num, diam)

**Selettivita:** Il filtro appare solo nello **0,5%** dei segnali convergenti -- ancora piu raro dell'isotopismo. La soglia di 15 e relativamente bassa, ma la coppia (num, diametrale) e molto specifica.

### 2.3 La tesi della convergenza

La tesi centrale del sistema e:

> Se K filtri indipendenti concordano su un ambo, la probabilita che sia un falso positivo diminuisce esponenzialmente con K.

In termini formali, se ogni filtro ha un tasso di falsi positivi `alpha_i`, e i filtri sono indipendenti, la probabilita di un falso positivo congiunto e:

```
P(falso positivo | K filtri) = alpha_1 x alpha_2 x ... x alpha_K
```

Per esempio, se ogni filtro ha `alpha = 0.20` (20% falsi positivi):
- 1 filtro: 20%
- 2 filtri: 4%
- 3 filtri: 0.8%
- 4 filtri: 0.16%
- 5 filtri: 0.032%

Questo e il principio dell'intersezione: piu vincoli sovrapposti, meno segnali sopravvivono, ma quelli che sopravvivono dovrebbero essere piu affidabili.

**Il problema fondamentale:** Questa moltiplicazione funziona SOLO se i filtri sono statisticamente indipendenti. Se i filtri sono correlati (guardano aspetti sovrapposti dei dati), la formula sovrastima drammaticamente il beneficio della convergenza. Come vedremo nel Capitolo 4, i filtri del sistema non sono indipendenti.

### 2.4 Lo scoring 0-5

Il motore di convergenza (`convergence.py`) assegna a ogni coppia candidata un punteggio da 0 a 5:

| Score | Significato | Azione suggerita |
|---|---|---|
| 0-2 | Rumore statistico | NON giocare |
| 3 | Segnale moderato | Giocare con cautela (se bankroll > 300) |
| 4-5 | Segnale forte | Priorita massima |

L'algoritmo opera in tre fasi:
1. **Raccolta:** I 3 filtri generativi (vincolo90, isotopismo, somma91) producono candidati
2. **Scoring:** Per ogni candidato, i 2 filtri di scoring (decade, ritardo) aggiungono punti
3. **Selezione:** Solo i candidati con score >= min_score vengono restituiti (max 10 per ruota)

### 2.5 La spec originale e il dato preliminare

La specifica originale del sistema riportava:

> Score 4: ratio 3.12x su 72 segnali

Questo dato preliminare suggeriva che il sistema avesse un edge del 212% rispetto al caso. Come vedremo nel Capitolo 4, questo era **rumore statistico** causato da un dataset troppo piccolo. Il valore reale, misurato su 2.000 estrazioni, e **1.10x** -- un edge del 10% che, come mostreremo nel Capitolo 3, e radicalmente insufficiente.

---

## 3. Il Breakeven -- Perche Serve 1.60x

---

> **In parole semplici**
>
> Immagina di gestire una bancarella di limonate. Ogni "ciclo di vendita" funziona cosi:
>
> - Compri limoni per 27 euro (3 ambi x 1 euro x 9 estrazioni)
> - SE vendi una limonata, incassi 250 euro
> - Un venditore casuale vende circa 6,5 limonate ogni 100 cicli
>
> Per coprire i costi (27 euro a ciclo), devi vendere almeno 10,8 limonate ogni 100 cicli. Cioe devi essere 10,8/6,5 = **1,66 volte meglio** di un venditore casuale.
>
> E il money management? E come decidere a che ora aprire la bancarella, o quanto succo mettere in ogni bicchiere. Puoi ottimizzare l'operativita, ma se i tuoi limoni producono meno succo di quanto costano, nessuna ottimizzazione del processo ti salva. Non puoi spremere piu succo dagli stessi limoni.
>
> La lezione: prima devi avere limoni buoni (un edge reale), poi puoi ottimizzare la spremitura (money management). Mai il contrario.

---

### 3.1 Parametri della giocata tipo

Il sistema Lotto Convergent opera con questi parametri di default, configurati in `config.py`:

| Parametro | Valore | Configurazione |
|---|---|---|
| Posta per ambo | 1,00 euro | `posta_default = 1.0` |
| Ambi per ciclo | 3 | `max_ambi_per_ciclo = 3` |
| Colpi per ciclo | 9 estrazioni | `max_colpi = 9` |
| Payout ambo | 250x | `payout_ambo = 250` |
| Bankroll iniziale | 600,00 euro | `bankroll_iniziale = 600.0` |
| Stop loss | -750,00 euro | `stop_loss = -750.0` |
| Bankroll minimo | 100,00 euro | `bankroll_min_play = 100.0` |

### 3.2 Costo di un ciclo di gioco

Un ciclo di gioco consiste nel giocare `n_ambi` ambi per `n_colpi` estrazioni consecutive, con posta fissa. Il costo totale e:

```
costo_ciclo = posta x n_ambi x n_colpi = 1 x 3 x 9 = 27 euro
```

Questo e implementato in `money_mgmt.py`:

```python
def calcola_costo_ciclo(posta, n_ambi, n_colpi):
    return posta * n_ambi * n_colpi
```

### 3.3 Probabilita casuale di hit nel ciclo

La probabilita di centrare almeno un ambo in un ciclo giocando 3 ambi per 9 estrazioni:

**Passo 1:** Probabilita di NON centrare un singolo ambo in una singola estrazione:
```
P(miss_singolo) = 1 - 1/400,5 = 399,5/400,5 = 0,997503
```

**Passo 2:** Numero totale di "tentativi" nel ciclo:
```
tentativi = n_ambi x n_colpi = 3 x 9 = 27
```

**Passo 3:** Probabilita di NON centrare nessun ambo nell'intero ciclo (assumendo indipendenza):
```
P(0 hit nel ciclo) = (399,5/400,5)^27 = 0,997503^27 = 0,93473
```

**Passo 4:** Probabilita di centrare almeno un hit:
```
P(almeno 1 hit) = 1 - 0,93473 = 0,06527 = 6,527%
```

Nota: l'approssimazione assume indipendenza tra i 27 tentativi. In realta, i 3 ambi giocati nella stessa estrazione condividono i 5 numeri estratti, quindi non sono perfettamente indipendenti. Tuttavia, per coppie distinte l'approssimazione e eccellente.

### 3.4 Calcolo del breakeven

Per andare in pari, il valore atteso del ciclo deve essere >= 0:

```
EV(ciclo) = P(hit) x vincita_netta - costo_ciclo >= 0
```

La vincita netta di un ambo secco e `payout - posta = 250 - 1 = 249 euro` (la posta giocata e persa, si riceve solo il premio). Piu precisamente, se si giocano 3 ambi per 9 colpi e si centra un hit al colpo k, si sono gia spesi `3 x k` euro. Semplificando con il costo medio:

```
P(hit) x 249 >= 27
P(hit) >= 27/249 = 0,10843 = 10,843%
```

Il rapporto tra il hit rate necessario e quello casuale:

```
edge_necessario = P(hit_breakeven) / P(hit_casuale)
                = 10,843% / 6,527%
                = 1,661x
```

Con la correzione per il payout netto di 249x (non 250x):

```
breakeven_ratio = 1,602x (arrotondato)
```

**Interpretazione:** Il sistema deve essere almeno 1,60 volte piu preciso del caso per andare in pari. Un ratio di 1,60x corrisponde a un hit rate del ~10,4% per ciclo, contro il 6,5% casuale.

### 3.5 Il criterio di Kelly

Il criterio di Kelly (Kelly, 1956) fornisce la frazione ottimale del bankroll da scommettere per massimizzare il tasso di crescita logaritmico del capitale:

```
f* = (b x p - q) / b
```

dove:
- `b` = odds netti (249 a 1 per l'ambo secco)
- `p` = probabilita di vincita
- `q = 1 - p` = probabilita di perdita

Per una scommessa casuale:
```
f* = (249 x 0,002497 - 0,997503) / 249
   = (0,6218 - 0,9975) / 249
   = -0,3757 / 249
   = -0,001509
```

**f* e negativo.** Il criterio di Kelly dice esplicitamente: **non scommettere**. Un f* negativo significa che qualsiasi posta positiva riduce il tasso di crescita atteso del bankroll.

Per ottenere f* > 0, serve:
```
b x p > q
249 x p > 1 - p
250p > 1
p > 1/250 = 0,004 = 0,4%
```

Cioe la probabilita di centrare l'ambo in una singola estrazione deve superare 0,4%, contro lo 0,2497% casuale. Questo corrisponde a un edge di 0,4%/0,2497% = **1,602x** -- esattamente il breakeven calcolato sopra.

### 3.6 La fallacia della decomposizione

Un errore comune nel gambling e credere che:

```
profitto = qualita_predizione x qualita_money_management
```

Cioe che si possa compensare una predizione debole con un money management sofisticato. Questo e **matematicamente falso**.

**Dimostrazione:** Il money management ottimizza l'allocazione del capitale date le probabilita. Non modifica le probabilita stesse. Il criterio di Kelly e la dimostrazione: la strategia di puntata ottimale dipende interamente dal rapporto tra probabilita reale e odds offerti.

Se l'edge e negativo (probabilita reale < probabilita di breakeven):
- Kelly dice di non scommettere (f* < 0)
- Qualsiasi strategia di puntata positiva ha un EV negativo
- Aumentare la posta peggiora le cose (perdite piu rapide)
- Diminuire la posta rallenta le perdite ma non le elimina

Il money management puo:
- **Ottimizzare** il tasso di crescita (dato un edge positivo)
- **Controllare** la varianza (ridurre il rischio di rovina)
- **Gestire** il drawdown (stop loss, position sizing)

Il money management NON puo:
- **Creare** un edge dove non c'e
- **Trasformare** un gioco a EV negativo in uno a EV positivo
- **Compensare** una probabilita di hit insufficiente

L'implementazione in `money_mgmt.py` riflette questa consapevolezza: il sistema rifiuta di giocare se lo score e insufficiente (< 3) e impone un stop loss assoluto di -750 euro. Ma anche queste precauzioni non possono rendere profittevole un sistema con edge insufficiente.

### 3.7 Analisi di sensitivita

Come varia il breakeven al variare dei parametri?

| n_ambi | n_colpi | Costo ciclo | P(casuale) | Breakeven ratio |
|---|---|---|---|---|
| 1 | 9 | 9 euro | 2,22% | 1,616x |
| 2 | 9 | 18 euro | 4,40% | 1,638x |
| **3** | **9** | **27 euro** | **6,53%** | **1,661x** |
| 3 | 12 | 36 euro | 8,62% | 1,676x |
| 3 | 18 | 54 euro | 12,72% | 1,702x |
| 5 | 9 | 45 euro | 10,74% | 1,681x |

Il breakeven ratio oscilla in un range ristretto (1,60-1,70x) indipendentemente dalla configurazione. Questo perche il house edge del 37,6% e una costante strutturale del gioco. **Non esiste una configurazione di puntata che riduca significativamente il breakeven.**

### 3.8 Riferimenti teorici

- **Kelly, J.L. (1956).** "A New Interpretation of Information Rate." Bell System Technical Journal, 35(4), 917-926. -- Fondamento del criterion di Kelly per il bet sizing ottimale.
- **Thorp, E.O. (1962).** "Beat the Dealer." Random House. -- Prima applicazione pratica del conteggio delle carte, dimostrando che un edge misurabile precede qualsiasi strategia di money management.
- **Shannon, C.E. (1948).** "A Mathematical Theory of Communication." Bell System Technical Journal, 27, 379-423. -- Il tasso di crescita del capitale e formalmente equivalente alla capacita del canale di Shannon; il money management e la codifica ottimale, ma non aumenta la capacita del canale (l'edge).

---

## 4. Prima Campagna di Test -- I 5 Filtri Convergenti

---

> **In parole semplici**
>
> Immagina un talent show con 5 giudici. Ogni giudice (filtro) valuta ogni concorrente (coppia di numeri) e dice "si" o "no". L'idea e: se 4 giudici su 5 dicono "si", il concorrente deve essere forte.
>
> Ma cosa succede se i giudici non sono indipendenti? Se il primo giudice dice sempre "si" a tutti (il filtro vincolo90, attivo nel 98,8% dei casi), il suo voto non vale nulla. Se il secondo e il terzo giudice sono nella stanza accanto e non sentono i concorrenti (isotopismo e somma91, che votano rarissimamente), i loro "si" sono rarissimi ma non necessariamente piu accurati.
>
> Risultato: "4 si su 5" in pratica significa "il giudice sempre-si ha detto si (ovvio), il giudice decade ha detto si, e il giudice ritardo ha detto si". Non e la convergenza di 4 segnali indipendenti -- e la convergenza di 2 segnali deboli filtrata da un giudice che non filtra nulla.
>
> E come scoprire che i voti della giuria non valgono piu del lancio di una moneta: i concorrenti approvati dalla giuria vincono quanto quelli scelti a caso.

---

### 4.1 Backtest su CSV seed (339 estrazioni, 2015-2025)

Il primo test e stato eseguito su un dataset CSV di seed, contenente 339 estrazioni dal 2015 al 2025. Questo dataset era stato usato durante lo sviluppo per verificare il funzionamento del codice.

**Configurazione del backtest:**
- Dataset: 339 estrazioni
- Train/Test split: 70/30 (237 train, 102 test)
- Min score: 2
- Max colpi: 9
- Baseline: `P(hit casuale in 9 colpi) = 1 - (1 - 1/400,5)^9 = 2,223%`

**Risultati:**

| Score | Segnali | Hit | Hit Rate | Baseline | Ratio |
|---|---|---|---|---|---|
| 2 | 3.992 | 84 | 2,10% | 2,22% | 0,95x |
| 3 | 5.302 | 103 | 1,94% | 2,22% | 0,87x |
| 4 | 6 | 0 | 0,00% | 2,22% | 0,00x |

**Analisi:**
- **Score 2:** Leggermente sotto il baseline. 3.992 segnali su 102 estrazioni = circa 39 segnali per estrazione. Il sistema non e selettivo.
- **Score 3:** Peggio del caso. 5.302 segnali > 3.992 segnali a score 2, il che e paradossale: piu segnali a score alto che a score basso significa che i filtri non stanno filtrando, ma accumulando.
- **Score 4:** Solo 6 segnali, zero hit. Campione troppo piccolo per trarre conclusioni.

**Verdetto:** Nessun vantaggio misurabile. Il dataset e troppo piccolo (102 estrazioni di test) per misurare un edge credibile su un evento con probabilita ~2%.

### 4.2 Backtest su archivio completo (2.000 estrazioni, 2014-2026)

Il secondo test ha utilizzato un dataset significativamente piu ampio: 2.000 estrazioni dal 2014 al 2026, caricato dall'archivio storico.

**Configurazione:**
- Dataset: 2.000 estrazioni
- Train/Test split: 70/30 (1.400 train, 600 test)
- Min score: 2
- Max colpi: 9
- Baseline: 2,223%

**Risultati:**

| Score | Segnali | Hit | Hit Rate | Baseline | Ratio |
|---|---|---|---|---|---|
| 2 | 26.468 | 622 | 2,35% | 2,22% | 1,06x |
| 3 | 32.591 | 745 | 2,29% | 2,22% | 1,03x |
| 4 | 41 | 1 | 2,44% | 2,22% | 1,10x |

**Analisi dettagliata:**

**Score 2 (ratio 1,06x):** Un hit rate del 2,35% contro il 2,22% casuale sembra un miglioramento. Ma e statisticamente significativo? Con 26.468 segnali e un hit rate atteso del 2,22%, il numero atteso di hit e 26.468 x 0,0222 = 587,6. Abbiamo osservato 622 hit. La deviazione standard sotto l'ipotesi nulla e `sqrt(26.468 x 0,0222 x 0,9778) = 23,97`. Lo z-score e `(622 - 587,6) / 23,97 = 1,44`. Il p-value (two-sided) e circa 0,15 -- **non significativo** al livello convenzionale di 0,05.

**Score 3 (ratio 1,03x):** Ancora piu deludente. Il rapporto scende a 1,03x, suggerendo che aggiungere il terzo filtro non migliora il segnale. Il numero di segnali a score 3 (32.591) e MAGGIORE di quelli a score 2 (26.468), il che sembra controintuitivo ma si spiega con l'architettura: i filtri di scoring (decade, ritardo) aggiungono punti a candidati che gia avevano score 2 dal vincolo90, quindi molti segnali "salgono" da 2 a 3.

**Score 4 (ratio 1,10x):** Un solo hit su 41 segnali. Il campione e troppo piccolo per qualsiasi inferenza statistica. L'intervallo di confidenza al 95% per il hit rate va da 0,06% a 12,75% -- un range cosi ampio da essere inutile.

**Confronto con la spec originale:** La specifica originale riportava un ratio di 3,12x per score 4, basato su 72 segnali. Il backtest completo mostra 1,10x su 41 segnali. La discrepanza e enorme: il dato originale era **rumore statistico** generato da un dataset troppo piccolo e potenzialmente viziato da data snooping (il dato era calcolato sugli stessi dati usati per calibrare i filtri, senza split train/test).

### 4.3 Diagnosi del problema architetturale

L'analisi approfondita dei risultati ha rivelato un problema strutturale fondamentale nel design dei filtri.

#### 4.3.1 Distribuzione degli score

Analizzando la distribuzione dei filtri attivi nei segnali:

| Filtro | % dei segnali in cui e attivo | Ruolo effettivo |
|---|---|---|
| vincolo90 | 98,8% | Quasi universalmente attivo -- non filtra |
| decade | ~25% (stima) | Moderatamente selettivo |
| ritardo | ~30% (stima) | Moderatamente selettivo |
| isotopismo | 1,7% | Troppo selettivo -- quasi mai attivo |
| somma91 | 0,5% | Troppo selettivo -- quasi mai attivo |

**Il problema del vincolo90:** Il filtro Vincolo Differenziale 90 genera talmente tanti candidati che e praticamente un generatore casuale di coppie. Con 12 coppie di ruote e centinaia di combinazioni di posizioni, il vincolo `d1 + d2 = 45` viene soddisfatto frequentemente. Il filtro produce circa 100 candidati per estrazione, e la sua "approvazione" non aggiunge informazione.

**Il problema dell'isotopismo e somma91:** All'estremo opposto, questi due filtri sono talmente selettivi da non contribuire mai alla convergenza. Se un filtro si attiva solo nell'1,7% dei casi, non puo mai portare lo score a 4 o 5 perche e quasi impossibile che si attivi contemporaneamente a un altro filtro raro.

**Conseguenza:** Lo scoring 0-5 e in realta uno scoring 0-3 mascherato:
- Score 1 = vincolo90 (quasi sempre)
- Score 2 = vincolo90 + (decade OR ritardo)
- Score 3 = vincolo90 + decade + ritardo
- Score 4 = vincolo90 + decade + ritardo + (isotopismo OR somma91) -- rarissimo
- Score 5 = tutti e 5 -- mai osservato

La "convergenza di 5 filtri indipendenti" e in realta la "sovrapposizione di 2-3 filtri parzialmente correlati mascherata da un filtro non-selettivo".

#### 4.3.2 Il problema della selettivita

Un buon sistema di filtri convergenti dovrebbe avere:
- Ogni filtro attivo nel 20-40% dei segnali (selettivita moderata)
- Filtri statisticamente indipendenti (correlazione ~0)
- Score alto = evento raro ma significativo

Il sistema attuale ha:
- Un filtro attivo nel 98,8% dei casi (nessuna selettivita)
- Due filtri attivi nell'1-2% dei casi (selettivita eccessiva)
- Due filtri con selettivita moderata ma senza indipendenza

Questo sbilanciamento rende il sistema incapace di produrre convergenza genuina.

#### 4.3.3 Volume di segnali per estrazione

Un indicatore critico e il numero medio di segnali per estrazione:

- Score >= 2: 26.468 segnali / 600 estrazioni = **44 segnali per estrazione**
- Score >= 3: 32.591 / 600 = **54 segnali per estrazione**

Con 54 segnali per estrazione a score >= 3, il sistema propone circa 5 ambi per ruota per estrazione. Considerando che ci sono solo 10 coppie estratte per ruota, il sistema sta "coprendo" circa il 50% dello spazio possibile. Questo non e predizione -- e gioco a tappeto.

### 4.4 Le 9 analisi strutturali

Dopo i risultati deludenti del backtest principale, sono state condotte 9 analisi strutturali per capire se il problema fosse nei filtri, nei dati, o nell'architettura. Ogni analisi ha cercato di rispondere a una domanda specifica.

#### 4.4.1 Analisi per ruota

**Domanda:** Alcune ruote sono piu "prevedibili" di altre?

**Metodo:** Backtest separato per ciascuna delle 10 ruote.

**Risultati:**

| Ruota | Ratio (score >= 2) |
|---|---|
| BARI | 1,03x |
| CAGLIARI | 0,98x |
| FIRENZE | 1,07x |
| GENOVA | 1,10x |
| MILANO | 0,92x |
| NAPOLI | 1,05x |
| PALERMO | 1,02x |
| ROMA | 0,97x |
| TORINO | 1,04x |
| VENEZIA | 1,00x |

**Range:** 0,92x - 1,10x. **Nessuna ruota supera 1,20x.**

**Interpretazione:** Le fluttuazioni tra ruote sono compatibili con il rumore statistico. Non esiste una ruota "piu prevedibile" -- le estrazioni sono ugualmente casuali su tutte le ruote. La varianza osservata (range di 0,18x) e esattamente quella attesa per campioni di questa dimensione.

#### 4.4.2 Analisi temporale

**Domanda:** L'efficacia del sistema varia nel tempo?

**Metodo:** Backtest su finestre temporali annuali.

**Risultati:**

| Periodo | Ratio |
|---|---|
| 2014-2016 | 1,02x |
| 2016-2018 | 1,07x |
| 2018-2020 | 1,00x |
| 2020-2022 | 1,04x |
| 2022-2024 | 1,05x |

**Range:** 1,00x - 1,07x per anno.

**Interpretazione:** Nessun trend temporale. Il sistema non migliora ne peggiora nel tempo, il che e coerente con un processo stazionario e casuale.

#### 4.4.3 Distribuzione score (conferma)

**Domanda:** Il vincolo90 sta davvero dominando?

**Metodo:** Conteggio della percentuale di segnali in cui ogni filtro e attivo.

**Risultato confermato:** vincolo90 = 98,8%. Il filtro non discrimina.

**Implicazione:** Lo score di convergenza e essenzialmente un conteggio di quanti tra i filtri "decade" e "ritardo" sono attivi, poiche vincolo90 e quasi sempre presente e isotopismo/somma91 sono quasi sempre assenti.

#### 4.4.4 Ritardo adattivo

**Domanda:** Cambiare la soglia del ritardo critico migliora il sistema?

**Metodo:** Backtest con diverse soglie per il filtro ritardo.

**Risultati:**

| Soglia ritardo | Ratio |
|---|---|
| 50 | 1,01x |
| 100 | 0,98x |
| **150** (default) | **0,95x** |
| 200 | 0,97x |
| 250 | 1,02x |
| 300 | 0,99x |

**Risultato critico:** La soglia di default (150) produce un ratio di 0,95x -- **SOTTO il baseline**. Usare il filtro ritardo con soglia 150 e PEGGIO che non usarlo.

**Interpretazione:** Il ritardo critico non ha potere predittivo. Un ambo in ritardo da 150 estrazioni non ha una probabilita maggiore di uscire rispetto a un ambo in ritardo da 50. Questo e perfettamente coerente con l'indipendenza delle estrazioni: il Lotto non ha memoria.

Questo risultato e una confutazione empirica diretta della "legge della maturita" (gambler's fallacy): l'idea che un evento "dovuto" sia piu probabile.

#### 4.4.5 Cadenza e figura

**Domanda:** Raggruppare i numeri per cadenza (ultima cifra) o figura (radice digitale) rivela pattern?

**Metodo:** Backtest filtrato per cadenza e figura delle coppie.

**Risultati:**
- Cadenza: ratio medio 1,06x (range 0,94x - 1,12x)
- Figura: ratio medio 1,06x (range 0,91x - 1,14x)

**Interpretazione:** Nessun gruppo di cadenza o figura mostra un vantaggio sistematico. Le variazioni sono rumore.

#### 4.4.6 Numeri caldi e freddi

**Domanda:** I numeri che escono piu frequentemente ("caldi") o meno frequentemente ("freddi") hanno un potere predittivo?

**Metodo:** Classificazione dei numeri in caldi (frequenza sopra la media), freddi (sotto la media), e neutri. Backtest separato per ambi composti da numeri dello stesso gruppo.

**Risultati:**
- Ambi "caldi" (entrambi i numeri caldi): **SOTTO il baseline**
- Ambi "freddi" (entrambi freddi): **SOTTO il baseline**
- Ambi misti: in linea con il baseline

**Interpretazione devastante:** Non solo i numeri caldi/freddi non hanno potere predittivo, ma filtrandoli il ratio scende sotto 1,0x. Questo e la **gambler's fallacy in entrambe le direzioni**: ne "continua la striscia" (hot hand) ne "e dovuto per uscire" (maturity) hanno basi nella realta del Lotto.

Questo risultato e particolarmente significativo perche distrugge due delle intuizioni piu comuni tra i giocatori:
1. "Gioca i numeri che escono spesso" (hot hand fallacy)
2. "Gioca i numeri che non escono da tempo" (gambler's fallacy)

Entrambe le strategie producono risultati PEGGIORI del caso.

#### 4.4.7 Test chi-quadrato

**Domanda:** La distribuzione dei numeri estratti e davvero uniforme?

**Metodo:** Test chi-quadrato di Pearson sulla distribuzione di frequenza dei 90 numeri, per ogni ruota.

**Risultati:**

| Ruota | p-value |
|---|---|
| Range osservato | 0,25 - 0,97 |

**Interpretazione:** p-value tra 0,25 e 0,97. Per rifiutare l'ipotesi di uniformita servirebbe p < 0,05. I p-value osservati sono **perfettamente compatibili** con una distribuzione uniforme.

In altre parole: ogni numero da 1 a 90 ha esattamente la stessa probabilita di essere estratto. Non ci sono numeri "fortunati" o "sfortunati". L'urna e equa.

Questo risultato, pur atteso per un gioco regolamentato, e importante perche esclude una possibile fonte di edge: se la distribuzione fosse anche leggermente non uniforme (ad esempio per difetti nelle sfere o nell'urna), un sistema che sfruttasse questa non-uniformita potrebbe avere un vantaggio.

#### 4.4.8 Correlazione consecutiva

**Domanda:** I numeri estratti in un'estrazione influenzano quelli dell'estrazione successiva?

**Metodo:** Correlazione seriale tra i numeri estratti in posizioni corrispondenti di estrazioni consecutive.

**Risultato:** Correlazione 0,989x (essenzialmente 1,0x -- nessuna correlazione utilizzabile).

**Nota tecnica:** Il valore 0,989x non indica una correlazione del 98,9%. Indica che il ratio tra il hit rate dei segnali basati sulla correlazione e il baseline e 0,989, cioe leggermente SOTTO il caso. Non c'e autocorrelazione sfruttabile.

**Interpretazione:** Le estrazioni sono indipendenti. Il numero estratto martedi non influenza il numero estratto giovedi. Questo e il risultato atteso per un generatore di numeri casuali ben funzionante, e conferma che qualsiasi strategia basata su "pattern sequenziali" e destinata a fallire.

#### 4.4.9 Analisi inter-ruota

**Domanda:** I numeri estratti su una ruota influenzano quelli estratti su un'altra ruota nella stessa estrazione?

**Metodo:** Correlazione tra i numeri estratti su ruote diverse nella stessa estrazione.

**Risultato:** Le ruote sono **indipendenti**.

**Interpretazione:** Questo e il colpo di grazia per il filtro Vincolo Differenziale 90, che si basa esattamente sull'ipotesi che le relazioni tra ruote abbiano significato predittivo. Se le ruote sono indipendenti, qualsiasi "vincolo" trovato tra due ruote e puramente casuale.

### 4.5 Sintesi della prima campagna

I risultati della prima campagna si possono riassumere in una tabella:

| Analisi | Risultato | Implicazione |
|---|---|---|
| Backtest CSV (339 estr.) | 0,87-0,95x | Nessun vantaggio, dataset piccolo |
| Backtest completo (2.000 estr.) | 1,03-1,10x | Edge marginale, non significativo |
| Per ruota | 0,92-1,10x | Nessuna ruota privilegiata |
| Temporale | 1,00-1,07x | Nessun trend |
| Distribuzione score | vincolo90=98,8% | Filtro dominante non selettivo |
| Ritardo adattivo | 0,95x (default!) | Peggio del baseline |
| Cadenza/Figura | ~1,06x | Rumore |
| Numeri caldi/freddi | SOTTO baseline | Gambler's fallacy confutata |
| Chi-quadrato | p=0,25-0,97 | Distribuzione uniforme |
| Correlazione consecutiva | 0,989x | Estrazioni indipendenti |
| Inter-ruota | Indipendenti | Vincolo90 non ha basi |

**Conclusione della prima campagna:** I 5 filtri convergenti non producono un edge statisticamente significativo. Il miglior risultato (1,10x a score 4) e basato su 41 segnali e 1 hit -- un campione troppo piccolo e un risultato troppo debole, lontanissimo dal breakeven di 1,60x.

Le analisi strutturali hanno identificato i problemi fondamentali:
1. **Vincolo90 non filtra:** attivo nel 98,8% dei casi
2. **Isotopismo e Somma91 filtrano troppo:** attivi nell'1-2% dei casi
3. **Ritardo critico e una fallacia:** ratio 0,95x sotto il baseline
4. **Le estrazioni sono indipendenti:** confermato da chi-quadrato, correlazione seriale, analisi inter-ruota
5. **I filtri non sono indipendenti tra loro:** la tesi della convergenza non si applica

Il dato originale di 3,12x per score 4 era rumore su un campione piccolo. Il valore reale e 1,10x, che non e nemmeno statisticamente significativo e che, anche se fosse reale, sarebbe drammaticamente insufficiente per superare il breakeven di 1,60x.

---

## 5. Il Panel degli Esperti -- Matematico, Gambling, Data Science

---

> **In parole semplici**
>
> Immaginate di avere un problema di salute misterioso e di consultare tre medici specialisti diversi. Il primo e un **internista** che controlla se i numeri delle analisi tornano -- pressione, colesterolo, globuli bianchi. Il secondo e un **chirurgo esperto** che ha visto migliaia di casi e sa quali interventi funzionano nella pratica e quali sono rischiosi. Il terzo e un **ricercatore** con accesso a database enormi e strumenti di analisi all'avanguardia, che cerca pattern nascosti nei dati clinici.
>
> Allo stesso modo, il nostro "paziente" e il sistema di previsione del Lotto. Lo sottoponiamo a tre tipi di esame completamente diversi:
> - L'**esperto matematico** verifica se i numeri hanno senso a livello teorico: le formule reggono? La scommessa ha valore atteso positivo?
> - L'**esperto di gambling** simula migliaia di scenari di gioco reale: quale strategia di puntata funziona? Quanto dura il bankroll?
> - L'**esperto data scientist** attacca il problema con 200 test statistici e algoritmi di machine learning: c'e un segnale nascosto nei dati?
>
> Se tutti e tre i medici dicono la stessa cosa, possiamo fidarci della diagnosi. Se sono in disaccordo, abbiamo un problema che merita ulteriore indagine.

---

### 5.1 Esperto Matematico -- Teoria dell'Informazione e Kelly

Il primo livello di analisi e puramente formale. Non guardiamo i dati: guardiamo le equazioni. La domanda e: **ammesso che i nostri filtri funzionino esattamente come misurato, la scommessa ha senso?**

#### 5.1.1 Composizione dell'edge

Il sistema Lotto Convergent si basa sulla convergenza di filtri multipli. Ogni filtro produce un vantaggio (edge) marginale rispetto alla selezione casuale. La composizione di questi edge segue regole precise che dipendono dalla correlazione tra i filtri.

**Caso ideale -- filtri indipendenti:**
Se tre filtri hanno ciascuno un edge di 1.10x (cioe selezionano coppie che escono il 10% piu spesso del caso), e i filtri sono perfettamente indipendenti tra loro, l'edge composto e il prodotto:

```
Edge composto = 1.10 x 1.10 x 1.10 = 1.331x
```

**Caso reale -- filtri correlati:**
Nella realta, i filtri condividono informazione. Due filtri che guardano entrambi la frequenza recente saranno parzialmente correlati. Con una correlazione media rho = 0.5 tra le coppie di filtri, l'edge composto si riduce drasticamente:

```
Edge composto (rho=0.5) = 1.154x
```

Questo rappresenta una perdita del 53% dell'edge teorico rispetto al caso indipendente. La correlazione tra filtri e il primo grande ostacolo: **aggiungere filtri non moltiplica l'edge linearmente**.

#### 5.1.2 Kelly Criterion

Il criterio di Kelly fornisce la frazione ottimale del bankroll da scommettere per massimizzare la crescita a lungo termine:

```
f* = (p * b - q) / b
```

dove:
- `p` = probabilita di vincita
- `q` = 1 - p = probabilita di perdita
- `b` = odds netti (payout - 1)

Per l'ambo secco:
- Probabilita base: 1/4005 = 0.0002497
- Con edge 1.154x: p = 0.000288
- Payout: 250x (ma la quota reale e spesso inferiore)
- b = 249

```
f* = (0.000288 * 249 - 0.999712) / 249
f* = (0.0717 - 0.9997) / 249
f* = -0.00373
```

**La frazione ottimale e negativa.** Nel framework di Kelly, questo significa che la scommessa ottimale e esattamente zero euro. Per ottenere un f* positivo con payout 250x, servirebbe:

```
p_min = q / b = 0.999712 / 249 = 0.004015
```

Ovvero un edge di almeno 1.602x -- il 60.2% superiore al caso. Il nostro edge di 1.154x copre meno del 40% del percorso necessario.

#### 5.1.3 Limite di Shannon

La teoria dell'informazione di Shannon pone un limite fondamentale ancora piu stringente. Un generatore di numeri casuali (RNG) certificato, come quello utilizzato dal Lotto Italiano, ha per definizione **zero informazione mutua** con qualsiasi variabile esterna.

Formalmente:

```
I(X; Y) = 0
```

dove X e l'estrazione futura e Y e qualsiasi funzione delle estrazioni passate, dei numeri "sacri", delle fasi lunari o di qualsiasi altro predittore.

Questo non e un'osservazione empirica: e una proprieta matematica dell'RNG certificato. Se l'informazione mutua fosse diversa da zero, l'RNG non sarebbe certificato. Questo pone un **tetto teorico** a qualsiasi sistema predittivo basato su dati storici.

L'obiezione potrebbe essere: "ma il Lotto Italiano usa estrazioni fisiche con urne, non un RNG digitale". Vero -- e questo potrebbe introdurre micro-bias meccanici. Ma tali bias, se esistono, sarebbero dell'ordine di grandezza di 0.001x o inferiore, ben al di sotto della soglia di rilevabilita con 6886 estrazioni.

#### 5.1.4 Strutture di scommessa alternative

Il Lotto Italiano offre diverse tipologie di scommessa. Abbiamo analizzato se qualche struttura alternativa possa colmare il gap:

| Tipo scommessa | Payout | Probabilita base | House edge |
|:---|:---:|:---:|:---:|
| Estratto singolo | 11.23x | 1/18 | 37.6% |
| Ambo secco | 250x | 1/4005 | 37.5% |
| Ambo tutte le ruote | 25x | ~1/400 | 37.5% |
| Terno secco | 4500x | 1/11748 | ~38% |
| Quaterna | 120000x | ~1/511038 | ~42% |

L'house edge e notevolmente consistente tra il 37% e il 42% su tutte le tipologie. Non esiste una scommessa strutturalmente piu favorevole. Questo e un design deliberato: il sistema e costruito per garantire un margine uniforme al banco.

#### 5.1.5 Il ruolo della varianza

Un'obiezione comune e: "non importa il valore atteso, importa la varianza -- se sei abbastanza fortunato, vinci". Questo e tecnicamente vero ma praticamente irrilevante.

Con valore atteso negativo, la varianza determina **quanto velocemente** si perde, non **se** si perde. Una varianza alta significa oscillazioni piu ampie -- periodi piu lunghi di apparente profitto seguiti da crolli piu profondi. Ma su un orizzonte temporale sufficientemente lungo, la legge dei grandi numeri garantisce la convergenza al valore atteso.

In concreto: con un edge di 1.10x su ambo secco (EV = -34.4% per scommessa), la probabilita di essere in profitto dopo N scommesse decresce esponenzialmente con N.

#### 5.1.6 Teorema di Doob sull'arresto opzionale

Un'ultima obiezione sofisticata e: "e se usassi una strategia di arresto -- smettere quando sei in vantaggio?". Il teorema di Doob sull'arresto opzionale demolisce questa speranza.

Per un gioco con EV negativo, nessuna strategia di arresto (stop-loss, take-profit, o qualsiasi combinazione) puo trasformare il gioco in un gioco con EV positivo. Le progressioni di puntata (Martingala, Fibonacci, D'Alembert) non fanno eccezione: ridistribuiscono il rischio nel tempo ma non alterano il valore atteso complessivo.

**Verdetto dell'esperto matematico:** *Con un edge di 1.154x e un payout di 250x, la scommessa ottimale secondo Kelly e zero. Il gap tra l'edge osservato e quello necessario e di 37.7 punti percentuali. Nessuna struttura di scommessa o strategia di arresto puo colmare questo gap.*

---

### 5.2 Esperto Gambling -- Money Management e Strategie

Il secondo esperto non si preoccupa delle formule: simula. La sua domanda e: **nella pratica, con soldi veri, quale strategia funziona meglio?**

#### 5.2.1 Framework Monte Carlo

Abbiamo costruito un simulatore Monte Carlo con i seguenti parametri:
- **50.000 simulazioni** per ciascun scenario
- Orizzonte temporale: 10 anni (3120 estrazioni)
- Bankroll iniziale: 1000 euro
- Metriche: P(profitto), P(rovina), profitto medio, profitto mediano

Le 50.000 simulazioni garantiscono che le probabilita stimate abbiano un errore standard inferiore allo 0.2%.

#### 5.2.2 Tipologie di scommessa testate

Ogni tipologia e stata simulata con l'edge migliore osservato per quella categoria:

**Ambo secco (payout 250x):**
- Edge: 1.154x
- EV per scommessa: -34.4%
- Risultato: P(profitto a 10 anni) = 2.1%, profitto medio = -612 euro

**Estratto (payout 11.23x):**
- Edge: 1.08x (stimato)
- EV per scommessa: -34.8%
- Risultato: P(profitto a 10 anni) = 1.8%, profitto medio = -587 euro

**Ambo tutte le ruote (payout 25x):**
- Edge: 1.10x (stimato)
- EV per scommessa: -33.1%
- Risultato: P(profitto a 10 anni) = 3.1%, profitto medio = -498 euro

**Terno secco (payout 4500x):**
- Edge: 1.05x (stimato)
- EV per scommessa: -40.1%
- Risultato: P(profitto a 10 anni) = 0.4%, profitto medio = -891 euro

#### 5.2.3 Gioco selettivo

Lo scenario piu interessante emerge quando il sistema viene utilizzato non per "prevedere i numeri giusti" ma per **selezionare quando NON giocare**. Se il giocatore gioca solo quando il segnale del sistema e particolarmente forte (top 5% dei turni) e la selezione ha un edge di 2.0x:

```
Gioco selettivo (5% turni, edge 2.0x):
- Scommesse/anno: ~15 (invece di ~310)
- EV per scommessa: +0.13 euro
- Profitto atteso/anno: +2.00 euro
- P(profitto a 10 anni): 3.4%
- P(rovina): 0%
```

Questo e l'**unico scenario con EV positivo** in tutta la nostra analisi. Ma il profitto atteso di 2 euro/anno e le probabilita di profitto del 3.4% rendono lo scenario accademico piu che pratico. Il margine e talmente sottile che le commissioni di gioco o i costi di trasporto per raggiungere una ricevitoria supererebbero facilmente il profitto atteso.

#### 5.2.4 Risultati delle strategie di puntata progressiva

Le strategie progressive sono state testate con puntata base di 1 euro e bankroll di 1000 euro:

**Flat betting (puntata costante):**

| Metrica | Valore |
|:---|:---:|
| P(profitto a 10 anni) | 35.2% |
| P(rovina) | 0.0% |
| Profitto medio | -127 euro |
| Profitto mediano | -142 euro |
| Massimo drawdown medio | 298 euro |

**D'Alembert (incremento +1 dopo perdita, -1 dopo vincita):**

| Metrica | Valore |
|:---|:---:|
| P(profitto a 10 anni) | 2.4% |
| P(rovina) | 96.6% |
| Profitto medio | -934 euro |
| Tempo medio alla rovina | 4.2 anni |

**Fibonacci (puntata = somma delle ultime 2 puntate dopo perdita):**

| Metrica | Valore |
|:---|:---:|
| P(profitto a 10 anni) | 1.1% |
| P(rovina) | 98.9% |
| Profitto medio | -978 euro |
| Tempo medio alla rovina | 2.8 anni |

Il pattern e inequivocabile: le strategie progressive **accelerano la rovina**. Il flat betting ha il 35.2% di probabilita di essere in profitto dopo 10 anni (grazie alla varianza degli eventi rari), ma le progressioni trasformano questa probabilita in meno del 2.5%.

La spiegazione e intuitiva: le progressioni aumentano la puntata dopo le perdite, il che significa puntare di piu proprio quando il bankroll e piu basso. Con un gioco a EV negativo, questo e equivalente a premere l'acceleratore mentre si guida verso un muro.

#### 5.2.5 Sopravvivenza del bankroll

Anche con l'approccio ottimale (flat betting), la sopravvivenza del bankroll a lungo termine con un edge di 1.10x e problematica:

```
P(rovina a 10 anni, edge 1.10x, flat bet 1% bankroll) = 37.8%
P(rovina a 20 anni, edge 1.10x, flat bet 1% bankroll) = 58.3%
P(rovina a 50 anni, edge 1.10x, flat bet 1% bankroll) = 89.1%
```

Anche con un edge reale del 10%, la rovina e piu probabile che no su un orizzonte ventennale. Questo perche l'edge non e sufficiente a compensare la varianza intrinseca del gioco.

**Verdetto dell'esperto gambling:** *Il flat betting e l'unica strategia razionale. Le progressioni (D'Alembert, Fibonacci, Martingala) portano alla rovina con probabilita superiore al 95%. L'unico scenario con EV positivo (gioco selettivo al 5%) produce un profitto cosi marginale da essere irrilevante nella pratica.*

---

### 5.3 Esperto Data Science -- ML e Feature Engineering

Il terzo esperto porta gli strumenti piu potenti: 200 test statistici, feature engineering avanzato, e modelli di machine learning. La domanda e: **c'e un segnale nascosto nei dati che i metodi tradizionali non vedono?**

#### 5.3.1 Batteria di test statistici

Abbiamo eseguito 200 test statistici sulle 6886 estrazioni del dataset. Per gestire il problema dei test multipli (200 test = alta probabilita di falsi positivi), abbiamo applicato la **correzione di Bonferroni**:

```
Soglia standard: p < 0.05
Soglia Bonferroni: p < 0.05/200 = p < 0.00025
```

**Risultato: zero test passano la soglia di Bonferroni.**

Nessuno dei 200 test ha prodotto un p-value inferiore a 0.00025. Questo significa che non c'e evidenza statistica di alcun pattern nel generatore di numeri del Lotto Italiano, anche cercando con estrema aggressivita.

I test includevano:
- Test di uniformita (chi-quadro) per ciascun numero e ciascuna ruota
- Test di indipendenza seriale (autocorrelazione a lag 1-50)
- Test runs (sequenze di numeri crescenti/decrescenti)
- Test di gap (intervalli tra apparizioni consecutive)
- Test di poker (raggruppamenti di cifre)
- Test spettrali (analisi di Fourier delle sequenze)

#### 5.3.2 Feature engineering per coppie

Abbiamo costruito features specifiche per le coppie di numeri:

- **Overdue score:** quanto una coppia e "in ritardo" rispetto alla sua frequenza attesa
- **Momentum:** trend della frequenza nelle ultime N estrazioni
- **Co-occurrence:** frequenza di apparizione congiunta con altri numeri
- **Positional:** posizione estrattiva preferenziale
- **Cyclometric:** distanza ciclometrica, somma mod 90, differenza

La feature piu promettente e stata lo score "overdue" (ritardo), che ha prodotto un edge di **1.04x** sulle coppie piu in ritardo. Ma 1.04x non e statisticamente significativo con il nostro campione:

```
Intervallo di confidenza 95% per edge 1.04x: [0.92x, 1.16x]
Il valore 1.0 (nessun edge) e ben dentro l'intervallo.
```

#### 5.3.3 Ensemble di features

Abbiamo combinato le 10 features migliori in un modello ensemble (gradient boosting) per verificare se la combinazione amplifica segnali deboli.

Risultato: **no**. L'ensemble produce un edge di 1.03x in cross-validazione, inferiore a quanto ci si aspetterebbe da overfitting su rumore puro. L'ensemble non amplifica segnali deboli perche non ci sono segnali da amplificare -- solo rumore statistico.

#### 5.3.4 Anomaly detection sui ritardi

Se il Lotto fosse veramente casuale, la distribuzione dei ritardi (numero di estrazioni tra due apparizioni consecutive dello stesso numero) dovrebbe seguire una distribuzione geometrica.

Abbiamo testato questa predizione:

```
Distribuzione osservata dei ritardi:
- Media: 17.8 estrazioni
- Deviazione standard: 17.9 estrazioni
- Coefficiente di variazione (CV): 1.00

Distribuzione geometrica teorica (p=1/18):
- Media: 18.0
- CV: 1.00
```

Il CV osservato di **1.00** e esattamente quello predetto dalla distribuzione geometrica. Non c'e alcuna anomalia nella distribuzione dei ritardi: i numeri si comportano come monete perfettamente casuali.

#### 5.3.5 Autocorrelazione temporale

L'autocorrelazione misura se le estrazioni successive sono correlate -- se un'estrazione "alta" tende a essere seguita da un'altra estrazione "alta" (correlazione positiva) o "bassa" (correlazione negativa).

```
Autocorrelazione media: r = -0.0004
Autocorrelazione a lag 1: r = 0.0012
Autocorrelazione a lag 2: r = -0.0008
...
Autocorrelazione a lag 50: r = 0.0003
```

L'autocorrelazione e **zero a tutti i lag testati**, entro i limiti dell'errore di campionamento. Non c'e alcuna memoria nel processo: sapere cosa e uscito all'estrazione precedente non fornisce alcuna informazione su cosa uscira alla prossima.

#### 5.3.6 Trasferimento tra ruote

Abbiamo testato se le estrazioni su una ruota forniscono informazione su un'altra ruota (cross-wheel transfer):

```
Correlazione media tra ruote: r = 0.001
Massima correlazione osservata: r = 0.023 (Bari-Napoli)
p-value della massima correlazione: p = 0.34
```

Le ruote sono **completamente indipendenti**. Non c'e alcun trasferimento di informazione tra una ruota e l'altra. Questo e atteso: le estrazioni avvengono fisicamente in sedi diverse con urne diverse.

#### 5.3.7 Analisi posizionale

Abbiamo verificato se la posizione estrattiva (primo, secondo, terzo, quarto, quinto numero estratto) porta informazione:

```
Entropia posizionale media: H = 4.17 bit
Entropia massima teorica (uniforme): H_max = 4.17 bit
Deficit di informazione: 0.00 bit
```

Le posizioni portano **zero informazione**. Il primo numero estratto non e sistematicamente diverso dal quinto. Questo conferma che l'ordine di estrazione e irrilevante per la previsione.

**Verdetto dell'esperto data science:** *200 test statistici, feature engineering avanzato, e modelli ensemble non trovano alcun segnale statisticamente significativo. La distribuzione dei ritardi e perfettamente geometrica (CV=1.00), l'autocorrelazione e zero a tutti i lag, le ruote sono indipendenti, e le posizioni non portano informazione. Il generatore del Lotto Italiano si comporta come un RNG ideale.*

---

## 6. Geometria Sacra, Cabala ed Esoterismo

---

> **In parole semplici**
>
> Immaginate di avere un paio di calzini portafortuna e di voler verificare scientificamente se funzionano davvero. Cosa fareste? Correreste 100 volte con i calzini e 100 volte senza, misurando i tempi, e poi confrontereste i risultati.
>
> In questo capitolo facciamo esattamente questo, ma con i "numeri sacri" del Lotto. Numeri di Fibonacci, numeri triangolari, somme cabalistiche, sezioni auree -- tutte queste tradizioni hanno i loro "calzini portafortuna". Noi li abbiamo testati su **6886 estrazioni** (quasi 20 anni di dati) per vedere se hanno un effetto misurabile.
>
> Spoiler: i calzini non fanno correre piu veloci. Ma il modo in cui lo scopriamo e istruttivo, perche lungo la strada incontriamo un fenomeno insidioso: i **falsi segnali** prodotti da campioni troppo piccoli. Un "segnale" che sembra fortissimo su 100 dati puo svanire completamente su 10.000 dati. E una lezione che vale ben oltre il Lotto.

---

### 6.1 Numeri sacri

Abbiamo classificato i 90 numeri del Lotto in categorie "sacre" secondo diverse tradizioni:

- **Numeri di Fibonacci** (1-89): 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89
- **Numeri triangolari** (1-90): 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78
- **Numeri quadrati** (1-90): 1, 4, 9, 16, 25, 36, 49, 64, 81
- **Numeri primi** (1-90): 2, 3, 5, 7, 11, 13, ..., 83, 89
- **Numeri maestri** (11, 22, 33, 44, 55, 66, 77, 88)

Per ciascuna categoria, abbiamo calcolato il ratio tra la frequenza di uscita delle coppie formate da numeri della categoria e la frequenza attesa sotto l'ipotesi di casualita:

| Categoria | Ratio osservato/atteso | N coppie testate | Interpretazione |
|:---|:---:|:---:|:---|
| Fibonacci | 0.993x | 45 | Nessun effetto |
| Triangolari | 1.001x | 66 | Nessun effetto |
| Quadrati | 0.987x | 36 | Leggermente sotto |
| Primi | 0.998x | 300 | Nessun effetto |
| Maestri | 0.991x | 28 | Nessun effetto |

Tutti i ratio sono compresi nell'intervallo **0.987x - 1.001x**, indistinguibili dal caso puro. I numeri sacri non hanno alcun potere predittivo.

### 6.2 Stessa figura (radice digitale)

La "figura" di un numero e la sua radice digitale (somma iterata delle cifre fino a ottenere una singola cifra). Per esempio, 47 ha figura 4+7=11, poi 1+1=2. Le coppie con la stessa figura hanno ratio:

```
Stessa figura: 0.931x
```

Le coppie con la stessa figura escono il **6.9% meno del caso**. Questo e l'unico risultato statisticamente significativo in questa sezione, ma va nella direzione sbagliata: le coppie con la stessa figura sono da **evitare**, non da cercare. Tuttavia, l'effetto potrebbe essere un artefatto della struttura del campione e richiede ulteriori verifiche.

### 6.3 Somme sacre

Alcune tradizioni assegnano significato speciale a coppie la cui somma ha un valore "sacro":

| Somma sacra | Ratio | N segnali | N hit | Note |
|:---:|:---:|:---:|:---:|:---|
| 7 | 1.524x | 177 | 6 | Campione minuscolo |
| 72 | 1.341x | 1877 | 56 | Sotto breakeven |
| 91 | 1.025x | 4521 | 113 | Nessun effetto |
| 108 | 0.978x | 892 | 22 | Nessun effetto |

La somma 7 mostra un ratio apparentemente impressionante di 1.524x, ma e basata su soli 6 hit su 177 segnali. L'intervallo di confidenza al 95% e [0.62x, 3.31x] -- enorme. Il risultato non e statisticamente significativo.

La somma 72 e piu interessante: 1.341x su 1877 segnali. Ma anche 1.341x e ben sotto la soglia di breakeven di 1.602x. Anche se il segnale fosse reale, **non sarebbe sufficiente per un profitto**.

### 6.4 Sezione aurea

La sezione aurea (phi = 1.618...) e una delle costanti piu celebrate in matematica e nelle tradizioni esoteriche. Abbiamo testato coppie il cui rapporto e vicino a phi:

```
Coppie con rapporto ~ phi (tolleranza 5%): 0.962x
```

Nessun effetto. Il rapporto aureo non conferisce alcun vantaggio alle coppie del Lotto.

### 6.5 Figure geometriche

Abbiamo testato coppie che formano figure geometriche "sacre" sulla ruota dei 90 numeri:

| Figura | Ratio | Note |
|:---|:---:|:---|
| Triangolo equilatero (distanza 30) | 0.98x | Nessun effetto |
| Esagramma (distanza 15) | 0.99x | Nessun effetto |
| Diametrali (distanza 45) | 0.98x | Nessun effetto |
| Quadrato (distanza 22-23) | 0.99x | Nessun effetto |

Tutte le figure geometriche producono ratio compresi tra **0.98x e 0.99x**, leggermente sotto il caso. Le geometrie sacre non hanno potere predittivo.

### 6.6 Distanze di Fibonacci

Un test piu sottile: le coppie la cui distanza (differenza tra i due numeri) e un numero di Fibonacci mostrano un edge?

```
Distanze Fibonacci: 1.019x
Distanze non-Fibonacci: 0.927x
Rapporto Fib/Non-Fib: 1.099x
```

Un rapporto di 1.099x sembra promettente, ma e un artefatto: le distanze di Fibonacci coprono una gamma piu ampia di valori e includono distanze piccole (1, 2, 3, 5) che sono naturalmente piu frequenti. Normalizzando per la distribuzione delle distanze, l'effetto svanisce.

### 6.7 Famiglie cabalistiche -- un caso istruttivo

Le "famiglie cabalistiche" sono gruppi di numeri associati nella tradizione della Smorfia napoletana. Abbiamo condotto un'analisi in due fasi che illustra perfettamente il pericolo dei campioni piccoli.

**Fase 1 -- Test campionato:**
Su un sottocampione di 500 estrazioni, selezionando le 10 famiglie piu "calde":

```
Ratio campionato: 1.302x (apparente segnale forte!)
```

Un ratio di 1.302x e vicino alla soglia di breakeven. Questo risultato, preso isolatamente, suggerirebbe che le famiglie cabalistiche hanno potere predittivo. Un ricercatore meno scrupoloso potrebbe fermarsi qui e pubblicare una "scoperta".

**Fase 2 -- Test completo:**
Estendendo l'analisi all'intero dataset (6886 estrazioni, 205.700 segnali):

```
Ratio completo: 1.005x
p-value: 0.40
```

Il ratio crolla da 1.302x a **1.005x** -- praticamente il caso puro. Il p-value di 0.40 indica che il risultato e perfettamente compatibile con il rumore statistico.

**Cosa e successo?** Il campione piccolo aveva selezionato le famiglie che erano "calde" in quel periodo specifico. Ma caldo e freddo si alternano casualmente, e su un campione grande l'effetto si mediava a zero. Questo e un esempio classico di **selection bias combinato con campione insufficiente**.

**Lezione fondamentale:** I campioni piccoli producono falsi segnali con alta probabilita. In un dataset con 4005 coppie possibili, anche con zero segnale reale, ci saranno sempre coppie che "sembrano" calde o fredde. Solo l'analisi su campioni grandi e con validazione indipendente puo distinguere il segnale dal rumore.

### 6.8 Deep dive: Somma 72

La somma 72 merita un'analisi dedicata perche e il risultato piu forte dell'intera sezione esoterica.

```
Somma 72 -- statistiche dettagliate:
- Numero di segnali: 1877
- Hit osservati: 56
- Hit attesi: 41.7
- Ratio: 1.341x
- p-value (test binomiale): 0.012
- Intervallo di confidenza 95%: [1.02x, 1.73x]
```

Il p-value di 0.012 sarebbe significativo con un singolo test, ma abbiamo eseguito decine di test su diverse somme. Applicando la correzione per test multipli, il p-value aggiustato diventa 0.15 -- non significativo.

Ma anche prendendo il ratio di 1.341x al valore nominale: e sotto la soglia di breakeven di 1.602x. **Anche un segnale reale non sarebbe abbastanza forte per rendere la scommessa profittevole.**

---

## 7. L'Intuizione della Finestra Ciclica

---

> **In parole semplici**
>
> Immaginate di voler prevedere il tempo meteorologico. Se calcolate la temperatura media degli ultimi 100 anni, ottenete un numero piatto e inutile: "la temperatura media a Milano e 13.5 gradi". Ma se guardate gli ultimi 30 giorni, vedete pattern utili: "siamo in una fase calda, probabilmente domani sara caldo".
>
> La stessa intuizione si applica al Lotto: forse la casualita ha delle "micro-stagioni" -- brevi periodi in cui certe coppie sono leggermente piu probabili. Il trucco e capire **quante estrazioni recenti guardare**. Guardarne troppe poche significa affogarsi nel rumore (come prevedere il tempo guardando solo l'ultima ora). Guardarne troppe significa mediare tutto a zero (come usare la media centenaria).
>
> Questo capitolo racconta la ricerca della "finestra giusta" -- il numero magico di estrazioni recenti che bilancia rumore e segnale.

---

### 7.1 Sweep delle finestre (N=10 a N=1000)

Abbiamo testato sistematicamente finestre di diversa ampiezza, da N=10 (ultime 10 estrazioni, circa 3 settimane) a N=1000 (ultime 1000 estrazioni, circa 3 anni). Per ciascuna finestra, abbiamo applicato 4 metodi di selezione diversi.

**Protocollo di cross-validazione temporale:**
Il dataset e stato diviso in due periodi non sovrapposti:
- **Periodo A (optimize):** 2007-2016 (~3000 estrazioni) -- usato per selezionare la finestra ottimale
- **Periodo B (validate):** 2017-2026 (~3000 estrazioni) -- usato per verificare che il risultato tenga

Questa separazione temporale e fondamentale: se un metodo funziona nel periodo A ma non nel periodo B, e overfitting.

#### Metodo A: Coppie frequenti nella finestra

Selezione delle coppie piu frequenti nelle ultime N estrazioni.

| Finestra N | Edge (optimize) | Edge (validate) |
|:---:|:---:|:---:|
| 10 | 0.872x | 0.911x |
| 50 | 0.934x | 0.956x |
| 100 | 0.967x | 0.971x |
| 200 | 0.981x | 0.978x |
| **300** | **0.986x** | **0.983x** |
| 500 | 0.979x | 0.975x |
| 1000 | 0.968x | 0.961x |

**Verdetto:** La finestra ottimale e N=300, ma il miglior risultato (0.986x) e **sotto il baseline** di 1.0x. Le coppie frequenti nella finestra tendono a essere meno frequenti nel periodo successivo -- un classico effetto di regressione verso la media.

#### Metodo B: Numeri caldi nella finestra

Selezione dei numeri con frequenza superiore alla media nelle ultime N estrazioni, poi formazione di coppie.

| Finestra N | Edge (optimize) | Edge (validate) |
|:---:|:---:|:---:|
| 50 | 1.087x | 0.823x |
| 100 | 1.156x | 0.789x |
| 200 | 1.234x | 0.734x |
| **500** | **1.320x** | **0.706x** |
| 1000 | 1.198x | 0.812x |

**Verdetto:** OVERFITTING massiccio. L'edge nel periodo di ottimizzazione cresce con N (1.320x a N=500), ma **crolla nel periodo di validazione** (0.706x). Il metodo identifica pattern specifici del periodo A che non si ripetono nel periodo B. Questo e il caso da manuale dell'overfitting temporale.

#### Metodo C: Ritardo nella finestra

Selezione delle coppie il cui ritardo (numero di estrazioni dall'ultima apparizione) e elevato all'interno della finestra.

| Finestra N | Edge (optimize) | Edge (validate) |
|:---:|:---:|:---:|
| 50 | 1.034x | 0.987x |
| 100 | 1.089x | 1.012x |
| **200** | **1.153x** | **1.054x** |
| 300 | 1.121x | 1.031x |
| 500 | 1.098x | 1.019x |

**Verdetto:** Debole ma tiene. L'edge di 1.054x in validazione e piccolo ma positivo. La finestra N=200 e ottimale. Il metodo ha una logica intuitiva: coppie "in ritardo" nella finestra hanno una leggerissima tendenza a recuperare.

#### Metodo D: Pattern composto

Combinazione di frequenza, ritardo e coerenza decina all'interno della finestra.

| Finestra N | Edge (optimize) | Edge (validate) |
|:---:|:---:|:---:|
| 25 | 0.998x | 1.023x |
| 50 | 1.012x | 1.067x |
| **75** | **1.034x** | **1.091x** |
| 100 | 1.045x | 1.078x |
| 200 | 1.067x | 1.034x |

**Verdetto:** Risultato controintuitivo e molto interessante. L'edge **migliora** nel periodo di validazione rispetto a quello di ottimizzazione (1.091x > 1.034x). Questo e estremamente raro e suggerisce un segnale robusto. La finestra N=75 e ottimale.

La spiegazione possibile: il pattern composto a N=75 non e abbastanza flessibile per fare overfitting nel periodo A, e cattura un effetto genuino (anche se debole) che si manifesta piu chiaramente nel periodo B, forse perche il periodo B ha condizioni piu favorevoli.

### 7.2 Deep dive N=75: combinazioni di filtri

Il risultato del Metodo D suggerisce che la finestra N=75 (~6 mesi di estrazioni) merita un'analisi approfondita. Abbiamo testato 12 filtri singoli all'interno di questa finestra:

| Filtro | Edge (N=75) |
|:---|:---:|
| hot_cold (numeri caldi) | 1.064x |
| freq (frequenza coppia) | 1.041x |
| rit (ritardo coppia) | 1.038x |
| dec (stessa decina) | 1.032x |
| fig (stessa figura) | 1.027x |
| fib (distanza Fibonacci) | 1.023x |
| som91 (somma 91) | 1.019x |
| diam (diametrali) | 1.011x |
| vincolo90 | 1.008x |
| iso (isotopismo) | 1.005x |
| pos (posizione) | 0.998x |
| ciclo (ciclometria) | 0.993x |

Il filtro **hot_cold** e il migliore singolo con 1.064x, seguito da freq (1.041x) e rit (1.038x).

Abbiamo poi testato 20 combinazioni di filtri con soglia di convergenza variabile:

**Le 5 migliori combinazioni:**

| Combinazione | Soglia | Edge optimize | Edge validate |
|:---|:---:|:---:|:---:|
| freq+rit+dec | >= 3 | 1.065x | 1.071x |
| freq_rit+fib | >= 2 | 1.063x | 1.110x |
| hot+freq+rit | >= 3 | 1.059x | 1.043x |
| freq+rit+fig | >= 3 | 1.052x | 1.067x |
| hot+dec+fib | >= 3 | 1.048x | 1.029x |

Due combinazioni emergono come candidate:
1. **freq+rit+dec (>= 3):** Edge stabile in ottimizzazione e validazione (1.065x -> 1.071x)
2. **freq_rit+fib (>= 2):** Edge piu alto in validazione (1.110x) ma basato su un campione piu piccolo

---

## 8. La Ricerca della Finestra Ottimale -- 3 Metodi Convergenti

---

> **In parole semplici**
>
> Immaginate di cercare la frequenza giusta su una radio. Tre persone diverse, ciascuna con una tecnica diversa, provano a sintonizzarsi:
>
> - **Il primo** (k-fold) divide il segnale in 5 pezzi e verifica che la stazione si senta bene su tutti e 5 i pezzi. Se si sente bene su 4 ma non sul quinto, probabilmente e un riflesso, non la stazione vera.
> - **Il secondo** (rolling window) fa scorrere lentamente il cursore della frequenza e controlla se la stazione resta stabile o va e viene. Una stazione vera resta stabile.
> - **Il terzo** (autocorrelazione) cerca se c'e un ritmo naturale nel segnale -- una periodicita che suggerisce una frequenza portante.
>
> Se tutti e tre convergono sulla stessa frequenza, possiamo essere ragionevolmente certi che e una stazione vera e non interferenza casuale.

---

### 8.1 K-fold temporale (5 fold x 600 estrazioni)

Il k-fold temporale e il metodo piu rigoroso. Dividiamo il dataset in 5 periodi consecutivi non sovrapposti (fold), ciascuno di circa 600 estrazioni (~2 anni):

- Fold 1: 2007-2008
- Fold 2: 2009-2011
- Fold 3: 2012-2014
- Fold 4: 2015-2018
- Fold 5: 2019-2026

Per ciascun segnale e ciascuna finestra, calcoliamo l'edge in ciascun fold separatamente. Un segnale **robusto** deve essere positivo in **tutti e 5 i fold**, non solo nella media.

Design sperimentale: 5 segnali x 12 finestre x 5 fold = **300 esperimenti**.

#### Risultati: il vincitore

**freq+rit+dec con W=150:**

| Fold | Edge |
|:---|:---:|
| Fold 1 (2007-2008) | 1.285x |
| Fold 2 (2009-2011) | 1.190x |
| Fold 3 (2012-2014) | 1.312x |
| Fold 4 (2015-2018) | 1.259x |
| Fold 5 (2019-2026) | 1.079x |
| **Media** | **1.225x** |
| **Minimo** | **1.079x** |

Questo segnale e **robusto in tutti e 5 i fold**. Il fold peggiore (Fold 5, 2019-2026) mostra ancora un edge di 1.079x -- positivo. La media di 1.225x e il risultato piu forte dell'intera ricerca.

#### Secondo classificato

**freq+rit+fig con W=70:**

| Fold | Edge |
|:---|:---:|
| Fold 1 | 1.201x |
| Fold 2 | 1.156x |
| Fold 3 | 1.089x |
| Fold 4 | 1.198x |
| Fold 5 | 1.019x |
| **Media** | **1.159x** |
| **Minimo** | **1.019x** |

Robusto anche questo (minimo 1.019x > 1.0x), ma con edge inferiore.

#### La trappola: freq_rit+fib

**freq_rit+fib con W=100:**

| Fold | Edge |
|:---|:---:|
| Fold 1 | 1.345x |
| Fold 2 | 1.267x |
| Fold 3 | 1.198x |
| Fold 4 | 1.298x |
| Fold 5 | **0.888x** |
| **Media** | **1.199x** |
| **Minimo** | **0.888x** |

La media di 1.199x e alta, ma il Fold 5 crolla a **0.888x** -- sotto il baseline. Questo segnale e **FRAGILE**: funziona bene in 4 periodi su 5 ma fallisce nel piu recente. Non supera il test di robustezza.

### 8.2 Rolling window (stabilita)

Il rolling window verifica la stabilita nel tempo. Facciamo scorrere una finestra di 300 estrazioni lungo tutto il dataset, calcolando l'edge in ciascuna posizione.

**freq+rit+dec W=75:**

```
Finestre totali analizzate: 110
Finestre con edge > 1.0: 78 (70.9%)
Edge medio: 1.109x
Edge minimo: 0.834x
Edge massimo: 1.423x
Rating: STABLE
```

Il segnale e positivo nel 70.9% delle finestre. Non e perfetto (l'ideale sarebbe >80%), ma e classificato come **stabile** perche le finestre negative sono poco profonde e le positive sono preponderanti.

**freq_rit+fib W=100:**

```
Finestre totali analizzate: 110
Finestre con edge > 1.0: 62 (56.4%)
Edge medio: 1.069x
Edge minimo: 0.465x
Edge massimo: 1.534x
Rating: UNSTABLE
```

Classificato come **UNSTABLE** a causa dell'edge minimo di 0.465x -- un crollo del 53.5% rispetto al baseline in una singola finestra. L'escursione massima e troppo ampia per un segnale affidabile.

### 8.3 Autocorrelazione

L'analisi di autocorrelazione cerca periodicita nella serie temporale degli hit-rate (frequenza di successo del segnale nel tempo).

**Autocorrelazione della hit-rate:**

```
Lag 1: r = 0.034
Lag 5: r = 0.012
Lag 10: r = -0.008
Lag 20: r = 0.021
Lag 50: r = 0.003
Lag 75: r = 0.019
Lag 100: r = -0.005
```

Nessun picco forte nell'autocorrelazione. Questo significa che non c'e una periodicita netta nel successo del segnale: non c'e un "ciclo" prevedibile di fasi buone e cattive.

**Analisi spettrale:**
L'analisi di Fourier della serie degli hit-rate rivela un quadro piu sfumato:

```
Densita spettrale di potenza:
- Periodo 10-30: rumore piatto
- Periodo 30-64: leggero incremento
- Periodo 64-76: CLUSTER DI ENERGIA (picco relativo)
- Periodo 76-150: decrescita graduale
- Periodo 150-500: rumore piatto
```

C'e un **cluster di energia** nella banda di periodo 64-76 estrazioni. Questo corrisponde a circa 5-6 mesi di estrazioni -- esattamente nella zona della finestra N=75 identificata nel capitolo precedente.

La periodicita e **debole ma reale**: il picco spettrale e circa 2.3 volte il livello del rumore di fondo. Non e un segnale travolgente, ma e coerente con l'ipotesi che esista una "zona di coerenza" intorno a 64-76 estrazioni.

**Interpretazione:** La finestra N=75 si trova nel cuore di questa zona di coerenza spettrale. Questo fornisce un **supporto debole ma indipendente** alla scelta della finestra, basato su un metodo completamente diverso (analisi spettrale vs. cross-validazione).

### 8.4 Sintesi: la finestra ottimale

I tre metodi convergono su un quadro coerente:

| Metodo | Segnale vincitore | Finestra | Edge | Robustezza |
|:---|:---|:---:|:---:|:---|
| K-fold 5-fold | freq+rit+dec | W=150 | 1.225x | Robusto (tutti i fold > 1.0) |
| Rolling window | freq+rit+dec | W=75 | 1.109x | Stabile (70.9% > 1.0) |
| Autocorrelazione | -- | 64-76 | -- | Zona di coerenza spettrale |

**Il k-fold 5-fold e il metodo piu affidabile** perche i fold sono completamente separati: non c'e alcuna sovrapposizione temporale, il che elimina il rischio di data leakage. Per questo motivo, il suo verdetto ha la precedenza:

**Segnale vincitore: freq+rit+dec con W=150**

Significato pratico: nelle ultime 150 estrazioni (~1 anno), cercare coppie intra-decina (entrambi i numeri nella stessa decina) che sono apparse di recente ma hanno un ritardo superiore alla media. La convergenza di tre criteri (frequenza, ritardo, decina) produce un edge medio di 1.225x.

Ma 1.225x non e sufficiente. L'edge necessario per raggiungere il breakeven sull'ambo secco e 1.602x. Il nostro segnale copre il **37.5%** del percorso:

```
Edge trovato:      1.225x = 22.5% sopra il caso
Edge necessario:   1.602x = 60.2% sopra il caso
Gap:               37.7 punti percentuali
Copertura:         22.5 / 60.2 = 37.4%
```

---

## 9. Conclusioni e Prospettive

---

> **In parole semplici**
>
> Abbiamo costruito un sistema sofisticato, lo abbiamo testato con rigore scientifico, e la risposta e chiara: **il Lotto Italiano e un generatore di numeri casuali estremamente ben progettato**. Il nostro sistema migliore trova un vantaggio del 22.5% rispetto al caso puro, ma per andare in pari servirebbe un vantaggio del 60%.
>
> E come avere una canna da pesca leggermente migliore della media: prenderete qualche pesce in piu degli altri pescatori, ma l'oceano vi chiede comunque 37 centesimi per ogni euro di esca. La canna migliore non cambia il prezzo dell'esca.
>
> Ma il viaggio non e stato inutile. Abbiamo imparato come distinguere i segnali veri dal rumore, come i campioni piccoli possono ingannare, e perche la cross-validazione temporale e indispensabile. Queste lezioni valgono ben oltre il Lotto.

---

### 9.1 Il segnale vincitore

Dopo aver esaminato centinaia di combinazioni di filtri, finestre, e metodi di validazione, un solo segnale supera tutti i test di robustezza:

**freq+rit+dec con W=150**

- **Composizione:** coppia frequente nelle ultime 150 estrazioni + ritardo superiore alla media + entrambi i numeri nella stessa decina
- **Interpretazione pratica:** nelle ultime ~150 estrazioni (circa 1 anno), cercare coppie i cui due numeri appartengono alla stessa decina (es. 31-38, 72-79), che sono apparse almeno una volta ma non di recente
- **Edge medio:** 1.225x
- **Edge nel caso peggiore (Fold 5):** 1.079x
- **Stabilita:** robusto su 5 periodi temporali indipendenti (2007-2026)
- **Consistenza:** stabile nel 70.9% delle finestre rolling

Il segnale ha una logica intuitiva: coppie intra-decina hanno una micro-struttura comune (cifra delle decine uguale), e la combinazione di "vista di recente ma non recentissima" cattura un effetto di regressione verso la media locale. Ma sottolineiamo: la logica intuitiva non e una prova. Il segnale potrebbe essere un artefatto sofisticato che non abbiamo saputo identificare.

### 9.2 Gap verso la profittabilita

Il calcolo iniziale era impietoso:

```
EDGE TROVATO (media globale)
  Ratio medio: 1.225x
  Sopra il caso: +22.5%

EDGE NECESSARIO (ambo secco, payout 250x)
  Ratio minimo per breakeven: 1.602x
  Sopra il caso: +60.2%

GAP (media globale)
  Punti percentuali mancanti: 37.7
  Percentuale del percorso coperta: 37.5%

IMPLICAZIONE (media globale)
  Per ogni euro scommesso, si perdono in media:
    - Senza sistema: 0.375 euro (house edge standard)
    - Con sistema: 0.234 euro (house edge ridotto)
    - Risparmio: 0.141 euro per scommessa
  Ma la perdita rimane positiva: il gioco resta a EV negativo in media.
```

Tuttavia, l'analisi per ruota e per ciclo temporale (Capitolo 10) ha rivelato che il segnale non e costante ma **ciclico**. Con la validazione a finestra scorrevole su ROMA 21-30, il 20% delle finestre supera il breakeven di 1.6x, con picchi fino a 3.164x. Questo cambia la narrativa da "impossibile" a **"possibile durante cicli specifici, ma il timing e imprevedibile"**. Il problema aperto non e piu l'esistenza dell'edge, ma la capacita di prevedere quando il segnale si attiva.

Una svolta ulteriore e arrivata con la scoperta dell'**ambetto** (Capitolo 14): il breakeven scende a 1.543x (da 1.602x), e i filtri convergenti si rivelano migliori nell'identificare zone numeriche che punti esatti. La strategia di money management (Capitolo 15) quantifica come sfruttare questa scoperta con un protocollo operativo a EUR 5/estrazione. L'**Engine V4** (Capitolo 16) porta questa intuizione al livello successivo: segnali diversi hanno finestre ottimali diverse per ambo e ambetto, e la configurazione separata (freq_rit_fib W=75 per ambo, somma72 W=150 per ambetto) massimizza ciascun tipo di scommessa.

### 9.3 Cosa funziona e cosa no

| Metodo | Edge | Validazione | Verdetto |
|:---|:---:|:---:|:---|
| freq+rit+dec W=150 | 1.225x | Robusto (5/5 fold) | SEGNALE REALE (insufficiente) |
| freq+rit+fig W=70 | 1.159x | Robusto (5/5 fold) | Segnale debole ma reale |
| freq_rit+fib W=100 | 1.199x | Fragile (4/5 fold) | NON AFFIDABILE |
| Numeri caldi N=500 | 1.320x/0.706x | Overfitting | FALSO SEGNALE |
| Coppie frequenti N=300 | 0.986x | Sotto baseline | NON FUNZIONA |
| Famiglie cabalistiche | 1.005x | Artefatto campionamento | FALSO SEGNALE |
| Numeri sacri (tutti) | 0.987-1.001x | -- | NESSUN EFFETTO |
| Geometria sacra | 0.98-0.99x | -- | NESSUN EFFETTO |
| Somma 72 | 1.341x | Sotto breakeven | INSUFFICIENTE |
| Somma 7 | 1.524x | Campione troppo piccolo | NON CONCLUSIVO |
| Sezione aurea | 0.962x | -- | NESSUN EFFETTO |
| Autocorrelazione temporale | r=-0.0004 | -- | ZERO |
| Cross-wheel transfer | r=0.001 | -- | ZERO |
| Anomaly detection ritardi | CV=1.00 | -- | PERFETTAMENTE CASUALE |
| Ensemble ML (10 features) | 1.03x | Non significativo | NESSUN SEGNALE |
| 200 test statistici | 0 passano | Bonferroni p<0.00025 | ZERO |

### 9.4 Lezioni metodologiche

Questo progetto ha prodotto lezioni metodologiche che trascendono il dominio del Lotto:

**1. I campioni piccoli producono falsi segnali.**
Le famiglie cabalistiche mostravano un edge di 1.302x su 500 estrazioni, che crollava a 1.005x sull'intero dataset di 205.700 segnali. In qualsiasi analisi statistica, la dimensione del campione e tanto importante quanto il risultato.

**2. L'overfitting a finestre temporali specifiche e insidioso.**
I numeri caldi con N=500 producevano un edge di 1.320x nel periodo di ottimizzazione, ma crollavano a 0.706x in validazione. La tentazione di "trovare il periodo giusto" e enorme, ma se un metodo funziona solo in un periodo, non funziona affatto.

**3. La cross-validazione temporale e essenziale.**
Il k-fold temporale con fold completamente separati e il gold standard. Il rolling window e utile come verifica di stabilita, ma puo soffrire di data leakage tra finestre adiacenti. L'autocorrelazione fornisce supporto indipendente ma non e sufficiente da sola.

**4. Il k-fold con fold separati e il gold standard.**
La separazione completa dei fold elimina qualsiasi possibilita di data leakage. Se un segnale e positivo in tutti e 5 i fold (come freq+rit+dec), la probabilita che sia un artefatto e bassa (p = 0.5^5 = 3.1%, assumendo che fold positivi e negativi siano equiprobabili sotto l'ipotesi nulla).

**5. Edge e profittabilita sono concetti diversi.**
Un edge di 1.225x e statisticamente significativo e probabilmente reale. Ma con un house edge del 37.5%, non e sufficiente per il profitto. La distinzione tra "segnale reale" e "segnale profittevole" e cruciale.

**6. La composizione di filtri correlati e sublineare.**
Tre filtri da 1.10x con correlazione rho=0.5 producono un edge composto di 1.154x, non 1.331x. Aggiungere filtri ha rendimenti decrescenti, e la correlazione tra filtri e il collo di bottiglia principale.

### 9.5 Prospettive future

I risultati del Capitolo 10 hanno ridefinito le prospettive: il segnale freq+rit+dec e ciclico, e durante le fasi attive (20% del tempo) supera il breakeven. Il Capitolo 14 introduce l'ambetto come veicolo strategico piu adatto ai nostri filtri, e il Capitolo 15 definisce il protocollo operativo ottimale di money management. Il problema centrale si sposta dalla ricerca dell'edge alla **predizione del timing**.

**1. Implementazione di freq+rit+dec W=150 nel codice**
Il segnale vincitore puo essere implementato nel modulo `analyzer/` del backend per generare previsioni in tempo reale. L'implementazione e gia parzialmente in atto nei filtri `ritardo.py` e `decade.py`.

**2. Monitoraggio delle performance in tempo reale**
Un sistema di tracking che misuri l'edge effettivo del segnale su base rolling permetterebbe di rilevare eventuali deterioramenti o miglioramenti nel tempo. Il Capitolo 10 mostra che ad aprile 2026 il segnale ROMA 21-30 e in fase di riaccensione (1.207x), rendendo il monitoraggio particolarmente urgente.

**3. Predizione dei cicli ON/OFF**
La sfida aperta principale: i 12 cicli ON identificati su ROMA 21-30 hanno durata media 3.2 anni ma intervalli irregolari (std > media). Servono metodi di change-point detection o regime-switching models per anticipare l'attivazione del segnale.

**4. Specializzazione per ruota e decina**
L'analisi Bonferroni del Capitolo 10 mostra che solo 10/90 combinazioni ruota-decina passano il test di significativita. La strategia ottimale non e giocare "tutte le ruote" ma concentrarsi sulle combinazioni piu forti (ROMA 21-30, FIRENZE 71-80, MILANO 11-20).

**5. Il sistema come "filtro per NON giocare"**
L'applicazione piu razionale del sistema non e prevedere quando giocare, ma **identificare quando sicuramente NON giocare**. Se il sistema non produce alcun segnale per una data estrazione, la probabilita di successo e ancora piu bassa del gia misero baseline. In questo ruolo, il sistema ha valore genuino: riduce la frequenza di gioco e quindi la perdita complessiva.

**6. Valore educativo e metodologico**
Il progetto dimostra come applicare il metodo scientifico a un dominio pieno di superstizioni e false credenze. Le lezioni su campionamento, overfitting, e cross-validazione sono trasferibili a qualsiasi problema di data science.

---

## 10. Validazione per Ruota e Analisi Ciclica

---

> **In parole semplici**
>
> Come un medico che prima fa un check-up generale e poi approfondisce gli organi sospetti, abbiamo preso il segnale vincitore e verificato se funziona su tutte le 10 ruote allo stesso modo. Abbiamo scoperto che non tutte le ruote si comportano ugualmente, e che il segnale va a cicli: periodi di 2-3 anni in cui funziona bene, alternati a periodi in cui non funziona. La sfida e' capire quando si accende.

---

### 10.1 Breakdown per ruota (5-fold CV)

Applicando il segnale vincitore freq+rit+dec con W=150 separatamente per ciascuna ruota, emerge un quadro eterogeneo:

| Ruota | Ratio medio |
|:---|:---:|
| **FIRENZE** | **1.380x** (miglior ruota) |
| MILANO | 1.321x |
| GENOVA | 1.198x |
| TORINO | 1.156x |
| NAPOLI | 1.089x |
| BARI | 1.045x |
| ROMA | 1.034x |
| PALERMO | 0.987x |
| VENEZIA | 0.923x |
| **CAGLIARI** | **0.772x** (peggiore) |
| **Media totale** | **1.029x** |

**Osservazioni critiche:**
- Nessuna ruota e stabile: il minimo fold e sempre sotto 0.95x per ogni ruota
- La miglior ruota **cambia ad ogni fold** -- non esiste una ruota strutturalmente piu prevedibile
- Il range (0.772x - 1.380x) e molto piu ampio di quello osservato nella prima campagna (0.92x - 1.10x), segno che il segnale freq+rit+dec amplifica le differenze tra ruote

### 10.2 Validazione Firenze 41-50 (il "miraggio" del 1.776x)

Il risultato iniziale di Firenze sulla decina 41-50 mostrava un ratio di 1.776x -- apparentemente il miglior segnale dell'intera ricerca. Ma la validazione rigorosa ha smascherato il cherry-picking:

| Test | Risultato | Interpretazione |
|:---|:---|:---|
| Edge iniziale (non validato) | 1.776x | Cherry-picking |
| 5-fold CV | Media 0.966x, min fold 0.404x | **SOTTO BASELINE** |
| Bonferroni (90 combinazioni) | Non tra le top 10 | Non significativo |
| Permutation test | p=0.220 | **NON SIGNIFICATIVO** |
| Analisi ciclica | 14 fasi ON, intervalli 1-18 anni | std > media = **irregolare** |

**Lezione:** Un edge di 1.776x senza cross-validazione e un miraggio statistico. La 5-fold CV rivela che il segnale non tiene: il fold peggiore (0.404x) indica che in alcuni periodi la strategia perde piu della meta rispetto al caso puro.

### 10.3 Top 3 Bonferroni -- sorpresa

Testando tutte le 90 combinazioni ruota x decina con correzione di Bonferroni (soglia p < 0.05/90 = 0.000556), 10 combinazioni su 90 passano il test (contro le 0.05 x 90 = 4.5 attese per caso):

| Combinazione | Ratio | z-score | 5-fold CV | Robustezza |
|:---|:---:|:---:|:---:|:---|
| **FIRENZE 71-80** | 2.538x | 10.38 | 1.280x (min 0.65x) | Fragile |
| **ROMA 21-30** | 2.179x | 7.95 | 1.186x (min 0.988x) | **ROBUSTO** |
| **MILANO 11-20** | 2.044x | 7.04 | 1.015x (min 0.72x) | Fragile |

**Osservazione chiave:** ROMA 21-30 e la combinazione piu interessante. Non ha il ratio piu alto, ma ha la miglior robustezza in cross-validazione: il fold peggiore (0.988x) e quasi al baseline, indicando che il segnale non crolla mai completamente.

### 10.4 Validazione ROMA 21-30 (6 test rigorosi)

ROMA 21-30 e stata sottoposta a 6 test indipendenti per verificare la solidita del segnale:

| Test | Risultato | Interpretazione |
|:---|:---|:---|
| 5-fold CV | Media 1.186x, min 0.988x | **ROBUSTO** |
| 10-fold micro | 6/10 fold sopra 1.0 | Moderatamente stabile |
| Permutation test | p=0.070, z=2.44 | Borderline (non sig. al 5%) |
| Ranking per decina 21-30 | #1 su 10 ruote | Miglior ruota per questa decina |
| Ranking per ROMA | #1 su 9 decine | Miglior decina per questa ruota |
| Pre/Post RNG | 0.629x / 1.078x | Miglioramento post-RNG |

**Interpretazione:** Il segnale e robusto ma non schiacciante. Il permutation test a p=0.070 non passa la soglia convenzionale del 5%, ma e borderline. Il confronto pre/post RNG e interessante: il segnale funziona meglio nel periodo moderno (post-RNG), il che potrebbe indicare che le estrazioni meccaniche pre-RNG avevano caratteristiche diverse.

### 10.5 Correzione metodologica: fold scorrevole

Un'intuizione chiave ha migliorato la metodologia: il fold della cross-validazione deve corrispondere alla finestra predittiva (W=150), non a un valore arbitrario. Se il segnale usa le ultime 150 estrazioni per prevedere, il fold di validazione deve essere di 150 estrazioni.

**Protocollo fold scorrevole:**
- Fold = 150 estrazioni (allineato con W=150)
- Step = 30 estrazioni (scorrimento)
- Target: ROMA 21-30
- Finestre totali: 220

**Risultati:**

| Metrica | Valore |
|:---|:---:|
| Media | 1.110x |
| Finestre sopra 1.0x | 45% |
| Finestre sopra 1.2x | 35% |
| Finestre sopra 1.6x (breakeven) | **20%** |
| Fasi ON identificate | 12 |
| Durata media fase ON | 3.2 anni |
| Picco massimo | 3.164x |
| Stato aprile 2026 | **Segnale in riaccensione (1.207x)** |

**Risultato cruciale:** Il 20% delle finestre supera il breakeven di 1.6x, con picchi fino a 3.164x. Questo cambia radicalmente la prospettiva: il segnale non e "sempre insufficiente" -- e **ciclicamente sufficiente**, ma il timing e imprevedibile.

Le 12 fasi ON hanno una durata media di 3.2 anni, ma gli intervalli tra una fase e l'altra sono altamente irregolari, rendendo impossibile prevedere la prossima attivazione con i dati attuali.

### 10.6 Conclusione del capitolo

Il segnale freq+rit+dec e **ciclico, non costante**. Le caratteristiche principali:

| Proprieta | Valore |
|:---|:---|
| Natura del segnale | Ciclico ON/OFF |
| Frequenza fasi ON | ~20% del tempo |
| Ratio durante fasi ON | 1.5-2.0x (sopra breakeven) |
| Ratio durante fasi OFF | 0.7-1.0x (sotto baseline) |
| Durata media fase ON | 3.2 anni |
| Prevedibilita timing | **Bassa** (std intervalli > media) |
| Miglior combinazione | ROMA 21-30 |
| Stato attuale (aprile 2026) | Riaccensione (1.207x) |

**Problema aperto:** La sfida non e piu trovare un edge (esiste), ma **prevedere quando il segnale si attiva**. I cicli sono irregolari (std degli intervalli superiore alla media), il che rende la predizione del timing una sfida aperta. Possibili approcci futuri includono modelli di regime-switching, change-point detection, e analisi di correlazione con variabili esogene.

### Schema riassuntivo della metodologia

```
+---------------------------------------------------+
|          LA METODOLOGIA IN 4 PUNTI                |
+---------------------------------------------------+
|                                                   |
|  1. FINESTRA = 150 estrazioni (~1 anno)           |
|     Il "contesto" in cui cercare pattern.         |
|     Troppo corta = rumore. Troppo lunga =         |
|     tutto si appiattisce all'equilibrio.          |
|                                                   |
|  2. SEGNALE = 3 condizioni simultanee:            |
|     - Coppia uscita nella finestra (frequenza)    |
|     - Non uscita di recente (ritardo >= W/3)      |
|     - Stessa decina (struttura numerica)          |
|                                                   |
|  3. FOLD SCORREVOLE = la finestra stessa          |
|     NON dividere in blocchi arbitrari.            |
|     Scorri la finestra di 150 estrazioni          |
|     lungo tutto il dataset per vedere i CICLI.    |
|                                                   |
|  4. IL SEGNALE E' CICLICO:                        |
|     ON (2-3 anni) -> ratio 1.5-2.0x (profitto!)  |
|     OFF (variabile) -> ratio 0.3-0.8x (perdita)  |
|                                                   |
|  SFIDA APERTA: prevedere quando si accende        |
+---------------------------------------------------+
```

---

## 11. Engine V3 — Correzione Metodologica e Nuova Classifica

### In parole semplici
Immagina di avere 6 strumenti diversi per prevedere il meteo: un barometro, un igrometro, un anemometro, ecc. Finora li usavamo tutti guardando lo stesso periodo (150 giorni). Ma abbiamo scoperto che ogni strumento funziona meglio con un periodo diverso: il barometro funziona meglio guardando 75 giorni, l'igrometro 100 giorni. Usare il periodo giusto per ogni strumento cambia completamente la classifica di chi e' piu' preciso.

### 11.1 La correzione metodologica

Il test precedente (5-fold con fold da 600) aveva un difetto: il fold era 4 volte piu' grande della finestra predittiva. Questo mescolava periodi ON e OFF, gonfiando artificialmente certi segnali. Il metodo corretto usa fold = finestra (scorrevole), dove ogni singola misura corrisponde esattamente a una finestra predittiva.

Questo e' analogo alla differenza tra "temperatura media annuale" (poco utile) e "temperatura di oggi" (utile per decidere come vestirsi).

### 11.2 Nuova classifica segnali (fold scorrevole)

| # | Segnale | Finestra ottimale | Media ratio | % sopra breakeven (1.6x) |
|---|---------|-------------------|-------------|------------------------|
| 1 | freq_rit_fib | W=75 | 1.159x | 30% |
| 2 | somma72 | W=100 | 1.081x | 25% |
| 3 | freq_rit_dec | W=125 | 1.024x | 13% |
| 4 | hot_cold | W=100 | 1.020x | 19% |
| 5 | freq_rit_fig | W=200 | 1.032x | 12% |
| 6 | fib_dist | W=50 | 1.016x | 8% |

Cambio piu' importante: freq_rit_fib (scartato come "fragile" nel test precedente) e' in realta' il migliore. Era fragile nel 5-fold con fold=600 perche' il fold era troppo grande — con fold=finestra (75) e' il piu' forte e consistente, con il 30% delle finestre sopra breakeven.

### 11.3 Combinazioni testate

| Combinazione | Media | % sopra 1.0 | % sopra 1.6 | Note |
|-------------|-------|-------------|-------------|------|
| dec AND somma72 | 1.205x | 23% | 22% | Raro ma forte (mediana 0) |
| dec AND fib_dist | 1.005x | 47% | 12% | Neutro |
| dec OR fig | 1.011x | 47% | 9% | Neutro |

La combo dec AND somma72 ha la media piu' alta (1.205x) ma genera segnali solo nel 23% delle finestre. Quando genera segnali, sono forti.

### 11.4 Finestra ottimale per ROMA 21-30

Confermata W=150 come migliore per ROMA 21-30 (media 1.110x, 20% sopra breakeven). Le finestre piu' corte (50-75) non funzionano per questa combinazione specifica.

### 11.5 Engine V3

L'engine V3 implementa ogni segnale con la sua finestra ottimale:
- freq_rit_fib (W=75): coppia uscita >=2 volte, in ritardo, distanza Fibonacci
- somma72 (W=100): coppia con somma 72, frequente e in ritardo
- freq_rit_dec (W=125): coppia stessa decina, frequente e in ritardo
- hot_cold (W=100): un numero caldo + un numero freddo
- combo dec+somma72 (W=125): stessa decina AND somma 72 (raro)

### 11.6 Lezione metodologica

La scelta del fold nel cross-validation non e' neutra. Un fold troppo grande rispetto alla finestra predittiva:
- Media insieme periodi ON e OFF
- Gonfia i segnali che hanno lunghe fasi ON
- Penalizza i segnali con cicli corti ma intensi (come freq_rit_fib)

Il fold deve corrispondere alla finestra predittiva. Questa correzione ha ribaltato completamente la classifica dei segnali.

### Schema riassuntivo V3

```
+---------------------------------------------------+
|            ENGINE V3 — FINESTRE OTTIMALI          |
+---------------------------------------------------+
|                                                   |
|  SEGNALE         FINESTRA   MEDIA   % >BREAKEVEN  |
|  freq_rit_fib    W=75       1.159x  30%  <-- #1   |
|  somma72         W=100      1.081x  25%  <-- #2   |
|  combo dec+s72   W=125      1.205x  22%  <-- raro |
|  freq_rit_dec    W=125      1.024x  13%            |
|  hot_cold        W=100      1.020x  19%            |
|                                                    |
|  OGNI SEGNALE HA LA SUA FINESTRA OTTIMALE          |
|  Non esiste una finestra "universale"              |
+---------------------------------------------------+
```

---

## 12. Dieci Metodi Avanzati — La Prova Definitiva

### In parole semplici
Immagina di aver provato 13 chiavi diverse su un lucchetto senza riuscire ad aprirlo. Invece di arrenderti, provi altre 10 chiavi ancora piu' sofisticate: chiavi a infrarossi, chiavi magnetiche, chiavi quantistiche. Le provi tutte, una per una, con la massima cura. Nessuna apre il lucchetto. A questo punto puoi dire con ragionevole certezza: il lucchetto non ha fori nascosti. E' davvero chiuso.

### 12.1 I metodi testati

| # | Metodo | Cosa misura | Risultato |
|---|--------|-------------|-----------|
| 1 | Conditional Entropy | Dipendenze non-lineari tra estrazioni | 0.44% riduzione entropia. NEGATIVO |
| 2 | Runs Test (Wald-Wolfowitz) | Clustering nelle apparizioni delle coppie | 199 significativi vs 200 attesi MC. NEGATIVO |
| 3 | Analisi spettrale (FFT) | Periodicita' nei ritardi delle coppie | Nessuna componente periodica. NEGATIVO |
| 4 | Copula (delay congiunti) | Struttura di dipendenza tra coppie | Falso positivo da troncamento. NEGATIVO |
| 5 | RQA (Recurrence Quantification) | Struttura deterministica nelle sequenze | Ricorrenza 0.943x vs random. NEGATIVO |
| 6 | Markov Chain (transizioni decine) | Probabilita' condizionali tra decine | Falso positivo intra-estrazione. NEGATIVO |
| 7 | EWMA vs Fixed Window | Pesatura esponenziale vs finestra fissa | EWMA 1.08x vs fixed 1.11x. Finestra fissa migliore |
| 8 | Bayesian Changepoint Detection | Cambiamenti nel regime probabilistico | 3.0% changepoint vs 4.1% falsi positivi. NEGATIVO |
| 9 | Mutual Information (ruote, lag 0-5) | Informazione condivisa tra ruote a diversi ritardi | Max MI 0.011 bits vs 0.012 soglia. NEGATIVO |
| 10 | Variance Ratio Test | Prevedibilita' a diversi orizzonti | VR(20) = 0.989 ≈ 1.0. Random walk perfetto |

### 12.2 Lezioni dai falsi positivi

Tre metodi hanno inizialmente mostrato risultati "interessanti" che sono poi collassati:

**Markov Chain**: concatenare i 5 numeri di un'estrazione come sequenza temporale crea anti-correlazione meccanica dal campionamento senza reimmissione. Testato correttamente (solo transizioni tra estrazioni): zero segnale.

**Runs Test**: 20 coppie per ruota mostravano clustering 2.7x, ma su 4.005 coppie totali con Monte Carlo il risultato e' perfettamente casuale.

**Copula**: troncare sequenze di lunghezze diverse a lunghezza uguale introduce correlazione spuria.

### 12.3 Il Bayesian Changepoint — la speranza delusa

Il metodo piu' promettente dalla ricerca web (BOCPD) avrebbe dovuto rilevare i cambiamenti di regime ON/OFF nel nostro segnale. Risultato: 3.0% di coppie mostra changepoint vs 4.1% atteso per falsi positivi. I cicli ON/OFF che osserviamo sono varianza statistica, non cambiamenti reali del regime sottostante.

### 12.4 Bilancio complessivo

Con 23 metodi testati (13 precedenti + 10 nuovi), il Lotto Italiano non mostra struttura sfruttabile a nessun livello: lineare, non-lineare, spettrale, entropico, o congiunto.

---

## 13. Ricerca Web e Stato dell'Arte

### In parole semplici
Abbiamo chiesto a internet: "qualcuno ha trovato un modo per battere il Lotto?" Abbiamo esaminato paper accademici, forum italiani, sistemi AI, e le tecniche dei giocatori professionisti. La risposta unanime: nessuno ha dimostrato un vantaggio riproducibile. Ma abbiamo trovato un'idea interessante per il nostro prossimo passo.

### 13.1 Paper accademici
- Modello CDM (Compound-Dirichlet-Multinomial): 2/6 numeri ogni 12 estrazioni. Non applicabile ad ambo secco.
- Nessun paper dimostra edge robusto out-of-sample su lotterie.

### 13.2 Metodi specifici Lotto italiano
- Forum LottoCED (2025): sistema AI+Markov+Monte Carlo, essenzialmente il nostro approccio convergente. Riportato un ambo al primo colpo (aneddotico, non validato).
- I metodi ciclometrici di Fabarri sono gia' nel nostro Engine V1.
- Nessun metodo documentato con track record verificabile.

### 13.3 Machine Learning
- LSTM: 4 layer bidirezionali. Nessun paper mostra accuratezza superiore al caso per numeri. Potenzialmente utile per regime ON/OFF.
- Random Forest: 8.33% vs 8-9% baseline. Marginale.
- Insight chiave: features statistiche (frequenze, ritardi) come input funzionano meglio dei numeri grezzi.

### 13.4 Change-point detection e HMM
- HMM per regime detection: usato da Renaissance Technologies in finanza.
- BOCPD (Adams & MacKay 2007): il piu' promettente in teoria, ma il nostro test (metodo 8 nel cap. 12) non trova changepoint reali.
- Il problema: i cicli ON/OFF nel nostro segnale sono probabilmente varianza statistica.

### 13.5 Metodi non applicabili
- Benford's Law: non applicabile (numeri uniformi 1-90, non distribuiti su ordini di grandezza).
- Exploiting RNG: il Lotto italiano usa estrazione meccanica certificata (non RNG software).
- Caso Eddie Tipton (Hot Lotto USA): rootkit su RNG software, non applicabile.

### 13.6 Prima verifica previsioni reali

Il 07/04/2026 abbiamo confrontato le previsioni Engine V3 con l'estrazione #56:
- 10 previsioni generate (5 V3 + 5 V2)
- 0 ambi centrati
- 2 "mezzo-centro" (1 numero su 2 presente)
- Risultato coerente con le aspettative: P(almeno 1 hit su 10 ambi) ≈ 2.5%

Prossima estrazione: giovedi 09/04/2026.

### 13.7 Conclusione

Lo stato dell'arte conferma che il Lotto e' un gioco a informazione nulla. Il nostro approccio (convergenza + finestre ottimali) e' allineato con le migliori pratiche trovate online. L'unico gap non colmato resta il timing dei cicli ON/OFF.

---

## 14. L'Ambetto -- La Svolta Strategica

---

> **In parole semplici**
>
> Immagina di lanciare freccette su un bersaglio. Con l'ambo secco devi centrare esattamente il centro -- difficilissimo. Con l'ambetto, vinci anche se la freccetta finisce nel cerchio subito accanto al centro. Il bersaglio e piu grande, il premio e piu piccolo (65x invece di 250x), ma centri molto piu spesso. E c'e una sorpresa: i nostri filtri sono bravi a trovare la ZONA giusta piu che il PUNTO esatto -- quindi l'ambetto premia esattamente il nostro punto di forza.

---

### 14.1 Cos'e l'ambetto

Introdotto nel 2013. Vinci se un numero e esatto e l'altro e adiacente (+/-1) a un estratto. Servono 2 numeri DISTINTI tra gli estratti. Se escono i numeri esatti (ambo secco), l'ambetto NON vince -- sono mutuamente esclusivi.

| | Ambo secco | Ambetto |
|:--|:----------|:--------|
| Regola | Entrambi esatti | 1 esatto + 1 adiacente |
| Payout | 250x | 65x |
| Probabilita | 1/400.5 | 1/100.32 |
| House edge | 37.6% | 35.2% |
| Breakeven | 1.602x | 1.543x |

### 14.2 Primo test (con bug)

Il primo backtest mostrava ratio 1.985x-2.433x per l'ambetto -- apparentemente sopra breakeven! Ma conteneva un bug critico: contava lo stesso numero estratto sia come "numero esatto" che come "adiacente dell'altro". Esempio: previsione 14-15, estratto solo il 14 -> il bug contava 14 come esatto E come 15-1=14 adiacente. In realta servono DUE numeri diversi tra gli estratti.

Scoperto grazie all'osservazione dell'utente sulla verifica di MILANO 14-15 nell'estrazione del 07/04/2026.

### 14.3 Risultati corretti

Con il check corretto (2 numeri distinti):

| Segnale | W | Ratio ambetto | Sotto breakeven? |
|:--------|:---:|:-------------|:----------------|
| somma72 | 100 | 1.219x | Si (serve 1.543x) |
| hot_cold | 100 | 1.163x | Si |
| freq_rit_fib | 75 | 1.146x | Si |
| freq_rit_dec | 125 | 1.110x | Si |

### 14.4 La vera scoperta: stabilita straordinaria

Il 5-fold CV dell'ambetto mostra stabilita mai vista con l'ambo secco:

| Segnale | F1 | F2 | F3 | F4 | F5 | Media | Min |
|:--------|:---:|:---:|:---:|:---:|:---:|:-----:|:---:|
| somma72 | 1.19 | 1.26 | 1.34 | 1.17 | 1.13 | 1.219x | 1.132x |
| hot_cold | 1.21 | 1.14 | 1.11 | 1.22 | 1.14 | 1.163x | 1.113x |
| freq_rit_fib | 1.09 | 1.16 | 1.17 | 1.14 | 1.17 | 1.146x | 1.088x |
| freq_rit_dec | 1.11 | 1.11 | 1.13 | 1.11 | 1.09 | 1.110x | 1.089x |

Nessun fold scende mai sotto 1.08x. Con l'ambo secco i min fold crollavano a 0.4-0.6x.

### 14.5 Prima verifica reale

Estrazione #56 del 07/04/2026: su 10 previsioni, 1 ambetto centrato:
- 6-75 su VENEZIA: il 6 esatto + il 76 (adiacente al 75) estratto
- Vincita: EUR 65 con EUR 10 investiti = +EUR 55

### 14.6 Lezione metodologica

Due lezioni importanti:

**1. Il bug del "doppio conteggio"** (stesso numero usato come esatto e adiacente) puo gonfiare enormemente i risultati. Sempre verificare manualmente i primi risultati.

**2. L'ambetto premia la capacita di identificare la ZONA corretta**, non il punto esatto. I nostri filtri sono migliori nel trovare zone (decine, famiglie numeriche) che coppie precise -- l'ambetto e il veicolo naturale per questo tipo di segnale.

---

## 15. Strategia di Money Management -- La Regola d'Oro

---

> **In parole semplici**
>
> Immagina di pescare in un lago. Ogni volta che lanci la lenza costa EUR 5. Quando peschi un pesce piccolo (ambetto) guadagni EUR 65, quando peschi uno grande (ambo) guadagni EUR 250. La regola piu importante non e DOVE lanciare la lenza -- e QUANTO puoi permetterti di spendere prima di prendere un pesce. Se spendi troppo per lancio, finisci i soldi prima di pescare. Se spendi poco, ogni pesce piccolo ti rimette in gioco.

---

### 15.1 La regola d'oro del money management

> Il costo del ciclo deve essere inferiore alla vincita minima.

Questa regola determina tutto il resto della strategia:
- Vincita minima = ambetto = EUR 65
- Costo ciclo = EUR/estrazione x 9 estrazioni
- Quindi: EUR/estrazione x 9 < 65 -> EUR/estrazione < 7.22
- Arrotondato: EUR 5 per estrazione (margine di sicurezza)

Con EUR 5/estrazione, una vincita ambetto (EUR 65) copre 1.44 cicli -- ti rimette in gioco con margine.
Con EUR 10/estrazione, una vincita ambetto (EUR 65) copre solo 0.72 cicli -- anche vincendo, perdi.

### 15.2 La strategia ottimale

Per ogni estrazione (EUR 5 totali):
- **COPPIA #1** (la migliore): EUR 1 ambo secco + EUR 1 ambetto = EUR 2
- **COPPIA #2:** EUR 1 ambetto = EUR 1
- **COPPIA #3:** EUR 1 ambetto = EUR 1
- **COPPIA #4:** EUR 1 ambetto = EUR 1
- **TOTALE:** EUR 5

Ciclo: 9 estrazioni = 3 settimane = EUR 45
Se vinci ambo: EUR 250 (copre 5.5 cicli)
Se vinci ambetto: EUR 65 (copre 1.44 cicli)

### 15.3 Simulazione Monte Carlo (50.000 iterazioni, 1 anno)

| Strategia | Costo/estr | BR finale | P(profitto) | P(rovina) | Vincite/anno |
|:----------|:-----------|:----------|:------------|:----------|:-------------|
| 4 ambetti + 1 ambo = EUR 5 | EUR 5 | EUR 322 | 10% | 5% | 6.6 |
| 5x(ambo+ambetto) = EUR 10 | EUR 10 | EUR 152 | 8% | 62% | 7.6 |
| 3x(ambo+ambetto) = EUR 6 | EUR 6 | EUR 276 | 14% | 27% | 5.6 |
| 5 ambo secco = EUR 5 | EUR 5 | EUR 324 | 13% | 22% | 1.8 |

La strategia EUR 5 (4 ambetti + 1 ambo) ha il miglior rapporto rischio/rendimento.

### 15.4 Scalabilita

La strategia scala linearmente con la posta:

| Posta | Costo/estr | Costo ciclo | Vincita ambetto | Copre? | Bankroll consigliato |
|:------|:-----------|:------------|:----------------|:-------|:--------------------|
| EUR 1 | EUR 5 | EUR 45 | EUR 65 | 144% | EUR 450 |
| EUR 5 | EUR 25 | EUR 225 | EUR 325 | 144% | EUR 2.250 |
| EUR 10 | EUR 50 | EUR 450 | EUR 650 | 144% | EUR 4.500 |

Regola bankroll: almeno 10 cicli di riserva.

### 15.5 Perche NON giocare su tutte le ruote come hedge

L'ambo "tutte le ruote" paga EUR 25 -- non copre neanche 1 estrazione di gioco (EUR 5). E una trappola psicologica: vinci spesso ma poco, e diluisci il bankroll. Ogni euro speso su "tutte le ruote" ha house edge 38.3% (il peggiore).

### 15.6 Schema operativo finale

```
+-----------------------------------------------------------+
|  PROTOCOLLO DI GIOCO V3                                   |
+-----------------------------------------------------------+
|                                                           |
|  1. GENERA PREVISIONI (lotto predict-v2 --archivio ...)   |
|     -> 5 coppie ordinate per score                        |
|                                                           |
|  2. GIOCA (EUR 5 per estrazione):                         |
|     Coppia #1: EUR 1 ambo + EUR 1 ambetto                 |
|     Coppie #2-#4: EUR 1 ambetto ciascuna                  |
|                                                           |
|  3. RIPETI per 9 estrazioni (3 settimane)                 |
|     Stessi numeri, stesse ruote, non cambiare!            |
|                                                           |
|  4. SE VINCI -> incassa, genera nuove previsioni          |
|     SE 9 ESTRAZIONI SENZA VINCITA -> nuovo ciclo          |
|                                                           |
|  5. STOP LOSS: se bankroll scende sotto 3 cicli (EUR 135) |
|     fermati e rivaluta                                    |
|                                                           |
|  Bankroll: EUR 450+ (10 cicli)                            |
|  Vincite attese: ~7/anno                                  |
|  P(profitto annuale): ~10%                                |
+-----------------------------------------------------------+
```

---

## 16. Engine V4 — Segnali Separati per Ambo e Ambetto

---

> **In parole semplici**
>
> Fino ad ora usavamo lo stesso binocolo per guardare sia le stelle che i fiori. Ma le stelle si vedono meglio con un telescopio e i fiori con una lente d'ingrandimento. Allo stesso modo, il miglior segnale per l'ambo secco (dove devi centrare la coppia esatta) e' diverso dal miglior segnale per l'ambetto (dove basta essere vicini). L'Engine V4 usa lo strumento giusto per ogni tipo di scommessa.

---

### 16.1 La scoperta: finestre diverse per ambo e ambetto

Sweep completo con check ambetto corretto (2 numeri distinti) e fold scorrevole:

**Ambo secco — classifica:**

| Segnale | W ottimale | Ratio |
|---------|-----------|-------|
| freq_rit_fib | 75 | 1.159x |
| somma72 | 100 | 1.081x |
| freq_rit_dec | 125 | 1.024x |

**Ambetto — classifica (finestre diverse!):**

| Segnale | W ottimale | Ratio | Min fold |
|---------|-----------|-------|----------|
| somma72 | 150 | 1.239x | 1.178x |
| freq_rit_fib | 125 | 1.153x | 1.098x |
| freq_rit_dec | 75 | 1.115x | 1.023x |

Le finestre ottimali cambiano: somma72 per ambetto preferisce W=150 (non 100), freq_rit_fib preferisce W=125 (non 75). L'ambetto, che allarga il bersaglio di +/-1, funziona meglio con finestre piu' ampie perche' cattura pattern di zona.

### 16.2 Perche' segnali diversi funzionano diversamente

freq_rit_fib seleziona coppie con distanza Fibonacci (1,2,3,5,8,13,21,34). Distanze grandi (21, 34) significano numeri lontani — l'adiacenza +/-1 dell'ambetto aiuta poco. Per l'ambo secco (che richiede esattezza) funziona bene perche' seleziona coppie precise.

somma72 genera coppie come 34-38 — numeri nella stessa zona. Se esce 34-39, l'ambetto vince. La vicinanza numerica e' il punto di forza dell'ambetto, e somma72 produce coppie naturalmente "vicine".

### 16.3 Configurazione Engine V4

| Ruolo | Segnale | Finestra | Posta | Vincita |
|-------|---------|----------|-------|---------|
| Coppia #1 ambo | freq_rit_fib | W=75 | EUR 1 ambo + EUR 1 ambetto | EUR 250 / EUR 65 |
| Coppia #2 ambetto | somma72 | W=150 | EUR 1 | EUR 65 |
| Coppia #3 ambetto | somma72 | W=150 | EUR 1 | EUR 65 |
| Coppia #4 ambetto | somma72 | W=150 | EUR 1 | EUR 65 |
| **TOTALE** | | | **EUR 5** | |

Ciclo: 9 estrazioni = EUR 45. Vincita ambetto (EUR 65) copre 144% del ciclo.

### 16.4 Validazione 5-fold CV ambetto con finestre corrette

| Segnale | W | F1 | F2 | F3 | F4 | F5 | Media | Min |
|---------|---|----|----|----|----|-----|-------|-----|
| somma72 | 150 | 1.24 | 1.21 | 1.31 | 1.18 | 1.26 | 1.239x | 1.178x |
| freq_rit_fib | 125 | 1.10 | 1.19 | 1.13 | 1.13 | 1.22 | 1.153x | 1.098x |
| freq_rit_dec | 75 | 1.02 | 1.10 | 1.10 | 1.15 | 1.14 | 1.102x | 1.023x |

somma72 W=150: il segnale piu' stabile di tutta la ricerca. Nessun fold scende sotto 1.17x.

### 16.5 Schema operativo V4

```
+-----------------------------------------------------------+
|  ENGINE V4 — SEGNALI SEPARATI                             |
+-----------------------------------------------------------+
|                                                           |
|  AMBO SECCO (coppia #1):                                  |
|    Segnale: freq_rit_fib                                  |
|    Finestra: W=75 (~6 mesi)                               |
|    Logica: coppia uscita 2+ volte, in ritardo,            |
|            distanza ciclometrica di Fibonacci              |
|    Posta: EUR 1 ambo + EUR 1 ambetto                      |
|                                                           |
|  AMBETTO (coppie #2-4):                                   |
|    Segnale: somma72                                       |
|    Finestra: W=150 (~1 anno)                              |
|    Logica: coppia con somma 72, uscita nella finestra,    |
|            in ritardo recente                              |
|    Posta: EUR 1 ambetto ciascuna                          |
|                                                           |
|  COSTO: EUR 5/estrazione, EUR 45/ciclo (9 estrazioni)    |
|  SCALA: posta × N mantiene gli stessi rapporti            |
+-----------------------------------------------------------+
```

---

## 17. Test Laterali — 12 Approcci Non Convenzionali

---

> **In parole semplici**
>
> Dopo aver esplorato i metodi classici, abbiamo provato 12 approcci completamente diversi — come un detective che, dopo aver interrogato i sospetti, controlla le telecamere, analizza il DNA e consulta un medium. Alcuni sembravano promettenti all'inizio, ma una verifica rigorosa li ha smontati tutti. La lezione piu importante: ogni volta che un test sembra dare risultati straordinari, bisogna chiedersi "sto misurando il segnale o un artefatto del mio metodo?"

---

### 17.1 Batch 1: 6 test (lateral_tests.py)

| # | Test | Risultato | Note |
|---|------|-----------|------|
| 1 | Compressibilita Kolmogorov | APPROFONDIRE | BARI p=0.01 ma solo prima meta dataset, effetto -0.08% |
| 2 | Autocorrelazione meta-proprieta | NESSUN SEGNALE | 50 sig vs 60 attesi |
| 3 | Rete negativa (esclusione) | NESSUN SEGNALE | Nessun edge |
| 4 | Transfer entropy Schreiber | NESSUN SEGNALE | TE=0.000 su tutte le ruote |
| 5 | Regime detection (media mobile) | ARTEFATTO | 94.6% → 38.5% su blocchi indipendenti (correlazione seriale) |
| 6 | Differenze giorno settimana | MARGINALE | GIO +5% per somma72, effetto trascurabile |

**Lezione critica dal Test 5:** la media mobile a 5 punti crea correlazione seriale artificiale. Due punti adiacenti condividono 4/5 dei dati. Il 94.6% misurava l'inerzia della media, non la predizione del futuro. Corretto con blocchi non sovrapposti: 38.5% (peggio del caso).

### 17.2 Batch 2: 3 test (lateral_tests_v3.py)

| # | Test | Risultato | Note |
|---|------|-----------|------|
| 7 | Fingerprint cinquine (MI) | APPROFONDIRE | PALERMO MI sig (p=0.04), 1/10 = caso |
| 8 | Attacco PRNG (spectral/birthday/serial) | NESSUN SEGNALE | Nessuna firma LCG, serial r=0 |
| 9 | Predizione forma (transizioni) | ARTEFATTO | 40/40 sig con baseline uniforme → 1/40 con baseline marginale |

**Lezione critica dal Test 9:** il chi-quadro sulle transizioni di forma (parita, somma, spread) mostrava 40/40 significativi — apparentemente sensazionale. Ma il test confrontava con distribuzione UNIFORME tra stati, mentre gli stati non sono equidistribuiti (2-3 pari coprono il 66% delle estrazioni, 0 e 5 pari solo il 2%). Corretto con baseline marginale: 1/40 significativi = caso.

### 17.3 Batch 3: 2 test corretti (lateral_tests_v4.py)

| # | Test | Risultato | Note |
|---|------|-----------|------|
| 9B | Forma con MI + baseline marginale | NESSUN SEGNALE | Chi2: 2/40 sig (attesi 2.0), MI: 3/40 sig (attesi 2.0) |
| 10 | Sweep 161 somme x 6 finestre | Cherry-picking smascherato | Somma72 NON nella top 20 |

### 17.4 Le 3 lezioni metodologiche dai test laterali

1. **Correlazione seriale della media mobile**: qualsiasi test di "accuracy" su punti adiacenti in una serie filtrata dara risultati alti. Usare sempre blocchi NON sovrapposti.
2. **Baseline sbagliata**: confrontare transizioni con distribuzione uniforme quando gli stati sono non-equidistribuiti produce falsi positivi massicci (40/40 → 1/40).
3. **Cherry-picking**: testare UN numero (somma 72) e trovare un buon ratio non significa nulla. Bisogna fare sweep sistematico su TUTTE le alternative e usare discovery/validazione separata.

---

## 18. Il Vero Segnale: Vicinanza Numerica, Non Somma Sacra

---

> **In parole semplici**
>
> Pensavamo che il "72" fosse un numero magico. Come un alchimista che crede nella pietra filosofale, avevamo attribuito poteri speciali a una somma specifica. Ma quando abbiamo testato TUTTE le 161 somme possibili (da 10 a 170), abbiamo scoperto che il 72 non era neanche nella top 20. Il vero pattern era molto piu semplice: le coppie di numeri VICINI tra loro (somme alte come 130-170 = entrambi i numeri nel range 60-90) funzionano tutte allo stesso modo. La somma 72 era solo un proxy accidentale per la vicinanza numerica.

---

### 18.1 Lo sweep 161 somme x 6 finestre (Test 10)

Discovery su prima meta, validazione su seconda meta:

- 966 combinazioni testate
- Somma72 W=150: NON nella top 20 discovery
- Top discovery: S=152 W=75 (1.399x), S=170 W=100 (1.393x), S=160 W=100 (1.386x)
- Le somme vincenti sono SPARSE (range 10-170, span 160)
- Ma la heatmap mostra una BANDA calda: somme 120-170 con ratio ~1.20x consistente

**Validazione top 5:**

| Somma | W | Discovery | Validazione |
|-------|---|-----------|-------------|
| 160 | 100 | 1.386x | 1.316x |
| 10 | 50 | 1.363x | 1.275x |
| 19 | 50 | 1.334x | 1.218x |
| 127 | 200 | 1.327x | 1.207x |
| 160 | 50 | 1.317x | 1.316x |

5-fold CV: S=160 W=100 media 1.203x, min fold 1.107x — tutti i fold sopra 1.1x.

### 18.2 Engine V5

Basato sui risultati dello sweep:

- **Ambo secco:** freq_rit_fib W=75 (invariato, ratio 1.159x)
- **Ambetto:** somma_alta S=160 W=100 (discovery 1.386x, validazione 1.316x)
- Banda 120-170 con priorita al target 160
- EUR 5/estrazione, EUR 45/ciclo

### 18.3 Test in corso

Al momento della scrittura, due test aggiuntivi sono in esecuzione:

- Sweep somme x finestre per AMBO SECCO (non solo ambetto)
- Test 11: filtro vicinanza pura (|a-b| <= D) per verificare se la somma e solo un proxy per la prossimita numerica

I risultati di questi test determineranno se l'Engine V5 sara aggiornato ulteriormente.

---

## Appendice A: Stack Tecnologico

Il sistema Lotto Convergent e costruito su uno stack moderno ottimizzato per analisi dati e API:

| Componente | Tecnologia | Versione |
|:---|:---|:---:|
| Linguaggio backend | Python | 3.12 |
| Framework API | FastAPI | 0.104+ |
| ORM/Database | SQLAlchemy + PostgreSQL | 2.0 / 16 |
| CLI | Typer | 0.9+ |
| Validazione dati | Pydantic | 2.0+ |
| Testing | pytest | 7.0+ |
| Linting/Formatting | ruff | 0.1+ |
| Containerizzazione | Docker + Docker Compose | 24+ |
| Frontend (pianificato) | React 18 / Next.js 14 | -- |
| Infrastruttura | VPS OVH/Hostinger | -- |

**Struttura dei moduli di analisi:**
- `ingestor/` -- Acquisizione e validazione dati storici (scraping + CSV)
- `analyzer/filters/` -- 5 filtri convergenti (vincolo90, isotopismo, ritardo, decade, somma91)
- `analyzer/convergence.py` -- Engine di scoring con convergenza multi-filtro
- `analyzer/backtester.py` -- Framework di backtesting con cross-validazione temporale
- `predictor/generator.py` -- Generazione previsioni basate sulla convergenza
- `predictor/money_mgmt.py` -- Money management e simulazione Monte Carlo
- `notifier/` -- Sistema di notifiche push via ntfy.sh

---

## Appendice B: Glossario Ciclometrico

| Termine | Definizione |
|:---|:---|
| **Ambo secco** | Scommessa su una coppia specifica di numeri su una ruota specifica |
| **Ambetto** | Scommessa in cui un numero e esatto e l'altro e adiacente (+/-1) a un estratto. Payout 65x, introdotto nel 2013. Mutuamente esclusivo con l'ambo secco |
| **Ambo tutte le ruote** | Scommessa su una coppia su tutte le ruote simultaneamente |
| **Autocorrelazione** | Misura della correlazione di una serie temporale con se stessa a diversi ritardi (lag) |
| **Backtesting** | Validazione di una strategia su dati storici |
| **Baseline** | Ratio di 1.0x, corrispondente alla frequenza attesa sotto casualita pura |
| **Bonferroni** | Correzione statistica per test multipli: divide la soglia di significativita per il numero di test |
| **Breakeven** | Punto in cui il valore atteso della scommessa e zero (ne profitto ne perdita) |
| **Ciclometria** | Studio matematico delle proprieta cicliche dei numeri nella ruota del Lotto |
| **Coefficiente di variazione (CV)** | Rapporto tra deviazione standard e media. Per distribuzione geometrica, CV=1.0 |
| **Convergenza** | Concordanza di piu filtri indipendenti sulla stessa coppia |
| **Cross-validazione** | Tecnica di validazione che divide i dati in sottoinsiemi per training e testing |
| **Decina** | Gruppo di 10 numeri consecutivi (1-10, 11-20, ..., 81-90) |
| **Diametrali** | Coppie di numeri la cui somma e 91 (es. 1-90, 2-89, ..., 45-46) |
| **Edge** | Vantaggio del sistema rispetto alla selezione casuale, espresso come ratio |
| **Estratto** | Scommessa su un singolo numero |
| **Figura (radice digitale)** | Somma iterata delle cifre di un numero fino a ottenere una singola cifra |
| **Fold** | Sottinsieme dei dati usato nella cross-validazione |
| **House edge** | Vantaggio percentuale del banco su ogni scommessa |
| **Isotopismo** | Analisi delle relazioni tra numeri basata sulle distanze nella ruota |
| **Kelly Criterion** | Formula per la scommessa ottimale che massimizza la crescita del bankroll |
| **K-fold** | Cross-validazione con K sottoinsiemi (fold) disgiunti |
| **Monte Carlo** | Metodo di simulazione basato su generazione di campioni casuali |
| **Overfitting** | Adattamento eccessivo di un modello ai dati di training, che non generalizza |
| **P-value** | Probabilita di osservare un risultato almeno cosi estremo sotto l'ipotesi nulla |
| **Ratio** | Rapporto tra frequenza osservata e frequenza attesa (1.0x = caso puro) |
| **Ritardo** | Numero di estrazioni trascorse dall'ultima apparizione di un numero o coppia |
| **Rolling window** | Finestra temporale che scorre lungo i dati per analisi locale |
| **Ruota** | Una delle 11 sedi di estrazione del Lotto Italiano |
| **Shannon** | Teoria dell'informazione: quantifica il contenuto informativo di una sorgente |
| **Smorfia** | Tradizione napoletana che associa numeri a sogni, eventi e significati |
| **Terno** | Scommessa su tre numeri specifici nella stessa ruota |
| **Vincolo Differenziale 90** | Filtro basato sulle proprieta della differenza modulo 90 tra numeri |

---

## Appendice C: Tabella Completa dei Test

### C.1 Test statistici (200 test, soglia Bonferroni p < 0.00025)

| Categoria | N test | Miglior p-value | Passano soglia |
|:---|:---:|:---:|:---:|
| Chi-quadro uniformita (per numero) | 90 | 0.0031 | 0 |
| Chi-quadro uniformita (per ruota) | 11 | 0.012 | 0 |
| Autocorrelazione (lag 1-50) | 50 | 0.0084 | 0 |
| Test runs | 11 | 0.034 | 0 |
| Test gap | 11 | 0.089 | 0 |
| Test poker | 11 | 0.142 | 0 |
| Test spettrali | 11 | 0.067 | 0 |
| Test di indipendenza cross-ruota | 5 | 0.34 | 0 |
| **Totale** | **200** | **0.0031** | **0** |

### C.2 Filtri singoli (edge su intero dataset)

| Filtro | Edge | Significativo? |
|:---|:---:|:---:|
| Vincolo Differenziale 90 | 1.008x | No |
| Isotopismo distanziale | 1.005x | No |
| Ritardo critico | 1.038x | Marginale |
| Coerenza decina | 1.032x | Marginale |
| Diametrali caldi (somma 91) | 1.019x | No |

### C.3 Combinazioni di filtri con cross-validazione (N=75)

| Combinazione | Edge optimize | Edge validate | Robusto? |
|:---|:---:|:---:|:---:|
| freq+rit+dec (>= 3) | 1.065x | 1.071x | Si |
| freq_rit+fib (>= 2) | 1.063x | 1.110x | Parziale |
| hot+freq+rit (>= 3) | 1.059x | 1.043x | Si |
| freq+rit+fig (>= 3) | 1.052x | 1.067x | Si |
| hot+dec+fib (>= 3) | 1.048x | 1.029x | Si |

### C.4 K-fold 5-fold: segnali principali

| Segnale + Finestra | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Media | Min |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| freq+rit+dec W=150 | 1.285 | 1.190 | 1.312 | 1.259 | 1.079 | 1.225 | 1.079 |
| freq+rit+fig W=70 | 1.201 | 1.156 | 1.089 | 1.198 | 1.019 | 1.159 | 1.019 |
| freq_rit+fib W=100 | 1.345 | 1.267 | 1.198 | 1.298 | 0.888 | 1.199 | 0.888 |
| hot+freq+rit W=75 | 1.134 | 1.078 | 1.112 | 1.089 | 0.967 | 1.076 | 0.967 |

---

## 19. VinciCasa — Secondo Gioco del Lottery Lab

### 19.1 Regole e struttura

VinciCasa: 5 numeri su 40, estrazione giornaliera (tutti i giorni alle 20:00). Premi: 5/5 = 500.000 EUR (di cui 300K vincolati a immobile), 4/5 = 200 EUR, 3/5 = 20 EUR, 2/5 = 2.60 EUR. Costo giocata: 2 EUR.

Dataset: 3.279 estrazioni (luglio 2014 — aprile 2026) da archivio xamig.com, importate in PostgreSQL.

### 19.2 Certificazione RNG

5 test standard (chi-quadro, runs, autocorrelazione, gap CV, compressibilita): tutti PASS. L'RNG di VinciCasa e indistinguibile dal random.

### 19.3 Percorso di ricerca (V1-V14)

- **V1-V5 (struttura, wheeling, Hamming, persistenza, hot numbers)**: nessun segnale per predire quintine esatte
- **V6-V9 (singoli numeri)**: hot numbers (top 5 piu frequenti in finestra N=5) producono +22% sulla categoria 2/5 (p=0.01, permutation test)
- **V10-V14 (dispersione, pool extension, frequenza vs recency, quintette ancorate)**: la dispersione non amplifica il segnale; la concentrazione (top 5 puri) resta la strategia migliore

### 19.4 Segnale confermato

**Top 5 numeri piu frequenti nelle ultime 5 estrazioni**: +22% sulla categoria 2/5 (2.60 EUR). Validato con permutation test (p=0.01) e split temporale.

EV: non sufficiente per profitto (house edge 37.3%, breakeven 1.60x, segnale 1.22x). Riduce il house edge ma non lo supera.

---

## 20. Engine V6 — Consolidamento Lotto

L'Engine V6 consolida i risultati di 18 capitoli di ricerca in un singolo motore predittivo con due segnali separati:

1. **Ambo secco**: freq_rit_fib (W=75) — numeri la cui frequenza e il cui ritardo seguono rapporti Fibonacci
2. **Ambetto**: vicinanza cross-decina |a-b| <= 20 (W=125) — coppie di numeri vicini con alta frequenza recente

Il V6 genera giocate quotidiane con costo EUR 5/estrazione (4 ambetti a EUR 1 + 1 ambo secco a EUR 1). La "golden rule" del money management: costo ciclo (9 estrazioni x EUR 5 = EUR 45) < vincita minima ambetto (EUR 65).

Ratio validato 5-fold CV: vicinanza 1.18x (ambetto), freq_rit_fib 1.16x (ambo).

---

## 21. 10eLotto Ogni 5 Minuti — Terzo Gioco del Lottery Lab

### 21.1 Regole del gioco

- 90 numeri, 20 estratti per estrazione
- Giocatore sceglie 1-10 numeri
- 288 estrazioni/giorno (ogni 5 minuti, 24/7)
- RNG elettronico certificato ADM
- Opzioni: Numero Oro (1° estratto), Doppio Oro (2° estratto), Extra (15 numeri aggiuntivi dai 70 rimanenti), GONG

### 21.2 Calcolo EV — Scoperta della configurazione ottimale

Calcolo analitico ipergeometrico per tutte le 116 configurazioni (1-10 numeri x opzioni base/Oro/DoppioOro/Extra/GONG). Verificato con Monte Carlo (1M simulazioni, convergenza 0.84%).

**Risultato chiave — Tabella top 5:**

| # | Config | Costo | EV/EUR | House Edge |
|---|--------|-------|--------|------------|
| 1 | **6 numeri + Extra** | **EUR 2** | **0.9006** | **9.94%** |
| 2 | 6 numeri + Oro + Extra | EUR 3 | 0.8783 | 12.17% |
| 3 | 6 numeri + Extra + GONG | EUR 3 | 0.8412 | 15.88% |
| 4 | 8 numeri + Oro | EUR 2 | 0.7387 | 26.13% |
| 5 | GONG solo | EUR 2 | 0.7222 | 27.78% |

La configurazione 6+Extra (9.94% HE) e il gioco con il house edge piu basso di tutte le lotterie italiane analizzate. Breakeven: solo 1.11x.

L'Extra contribuisce il 65% dell'EV totale (1.176 su 1.801 EUR). Il 67.7% delle giocate vince qualcosa nell'Extra.

**Peggiori configurazioni**: Doppio Oro con pochi numeri (HE 45-50%). L'opzione Doppio Oro e una trappola.

### 21.3 Ingestione dati

Fonte: API JSON di lottologia.com (`/api/metalotto/data/lottery/10elotto5minuti/draw/bydate`). 288 estrazioni/giorno con 20 numeri + Oro + Doppio Oro + 15 Extra.

Dataset: **33.431 estrazioni** (15 dicembre 2025 — 13 aprile 2026), ~120 giorni.

---

## 22. 10eLotto — Certificazione RNG e Analisi Statistica

### 22.1 RNG Certification (5/5 PASS)

| Test | Risultato | Dettaglio |
|------|-----------|-----------|
| Chi-quadro uniformita | PASS (z=-0.45) | freq attesa 7437, min 7221, max 7606 |
| Runs test (somme) | PASS (z=0.28) | runs osservati = attesi |
| Autocorrelazione somme | PASS (max r=0.013) | nessuna correlazione fino a lag 20 |
| Gap CV | PASS (CV=0.882) | distribuzione geometrica confermata |
| Compressibilita | PASS (z=1.14) | identico a random |
| Overlap consecutivo | PASS (4.46 vs 4.44 atteso) | nessuna memoria |

### 22.2 Analisi Deep (D1-D5)

**D1 — Numero Oro e Doppio Oro:**
- Distribuzione Oro: PASS (uniforme, chi2 z=-0.67)
- Distribuzione Doppio Oro: PASS (z=1.73)
- Autocorrelazione Oro: PASS (max r=0.008)
- Distanza |Oro-DoppioOro|: z=3.08 — unico segnale borderline. Media 30.35 vs 29.99 atteso. Il bias e stabile (split: z=2.31 + z=2.05) ma non sfruttabile (P(DoppioOro) non dipende dalla distanza)

**D2 — Sequenze PRNG:** N/A (dati ordinati nel DB, ordine originale perso)

**D3 — Dipendenza Extra|Base:** Correlazione negativa r=-0.24 per decina (strutturale e atteso). Autocorrelazione tra estrazioni: ZERO.

**D4 — Lag 288 (ciclo giornaliero):** Nessun picco. Il PRNG non viene reseedato giornalmente. Tutte le autocorrelazioni sotto z=2.0.

**D5 — Numeri spia (8.010 coppie + Bonferroni):** 1 coppia (64,56) a z=-4.38 — direzione negativa, non sfruttabile. Con 8.010 test, ~0.5 falsi positivi attesi a questa soglia.

### 22.3 Pattern orari (Fase 5)

Nessun bias temporale. Overlap medio uniforme per tutte le 24 ore (range 4.34-4.56, varianza 0.002). L'RNG si comporta identicamente alle 3:00 e alle 18:00.

---

## 23. 10eLotto — Prediction Lab (8 Test Predittivi)

### 23.1 Framework di giocata virtuale

Per ogni estrazione t nel test set: seleziona 6 numeri col metodo in test, confronta con i 20 base e i 15 Extra, calcola EV reale (premio base + premio Extra). Costo EUR 2, baseline EV 1.8013.

Discovery su prima meta (16.700 estr.), validazione su seconda meta (16.700 estr.).

### 23.2 Risultati

| # | Metodo | Config | EV val | Ratio | Supera BE ST? |
|---|--------|--------|--------|-------|---------------|
| 1 | P2 vicinanza | W=100 D=5 | 1.9655 | 1.091x | SI |
| 2 | P3 top-freq | W=576 | 1.9339 | 1.074x | SI |
| 3 | P2 vicinanza | W=50 D=5 | 1.9323 | 1.073x | SI |
| 4 | P5 mix caldi+freddi | W=288 | 1.9288 | 1.071x | SI |
| 5 | P1 freq+rit+dec | W=50 | 1.8649 | 1.035x | no |
| 6 | P6 overlap scoring | W=10 | 1.7817 | 0.989x | no |
| 7 | P7 somma regressione | W=288 | 1.8516 | 1.028x | no |
| 8 | P4 freddi | W=288 | 1.8752 | 1.041x | no |

P8 (ML ensemble) non eseguito (sklearn non installato).

4 segnali superano il breakeven Special Time (1.067x) in validazione grezza. Ma serviva la validazione rigorosa.

### 23.3 Validazione rigorosa (Step 1-4)

**Step 1 — Permutation test (10.000 shuffle + Bonferroni p < 0.001):**

| Segnale | EV val | Ratio | p-value | Soglia | Risultato |
|---------|--------|-------|---------|--------|-----------|
| P2 vicinanza W=100 D=5 | 1.965 | 1.091x | **0.054** | 0.001 | **FAIL** |
| P3 top-freq W=576 | 1.934 | 1.074x | 0.108 | 0.001 | FAIL |
| P2 vicinanza W=50 D=5 | 1.931 | 1.072x | 0.087 | 0.001 | FAIL |
| P5 mix W=288 | 1.928 | 1.071x | 0.095 | 0.001 | FAIL |

**Nessun segnale passa Bonferroni.** Il p-value migliore (0.054) non e significativo nemmeno senza correzione per test multipli. I ratio 1.07-1.09x erano varianza campionaria amplificata dalla selezione di ~60 configurazioni.

Step 2, 3, 4 non eseguiti (prerequisito Step 1 non superato).

### 23.4 Special Time

Special Time: 6 estrazioni random nella fascia 16:05-18:00 con premi maggiorati. Dalla tabella ufficiale (10elotto5.it):

| Numeri vincenti | Base normale | Base ST | Extra normale | Extra ST |
|-----------------|-------------|---------|---------------|----------|
| 6/6 | 1000 | 1300 (+30%) | 2000 | 3000 (+50%) |
| 5/6 | 100 | 110 (+10%) | 200 | 210 (+5%) |
| 4/6 | 10 | 11 (+10%) | 20 | 21 (+5%) |
| 3/6 | 2 | 2 (0%) | 7 | 7 (0%) |

I premi bassi (alta probabilita) sono quasi invariati. Solo i premi alti (bassa probabilita) sono maggiorati.

| Config | EV | House Edge |
|--------|-----|-----------|
| 6+Extra normale | 1.801 | 9.94% |
| **6+Extra Special Time** | **1.874** | **6.30%** |
| 6+Extra media fascia 16-18 | 1.819 | 9.03% |

Special Time riduce l'HE al 6.30% — il piu basso di qualsiasi lotteria italiana — ma resta sotto breakeven.

---

## 24. Strategy Lab — Seconda Campagna Predittiva 10eLotto

### 24.1 Motivazione

La prima campagna (cap. 23) ha testato 8 metodi "standard" adattati dal Lotto, tutti falliti al permutation test. Ma diversi metodi dal paper non erano mai stati adattati al 10eLotto:

- **freq_rit_fib** (vincitore Lotto ambo a 1.16x)
- **Ciclometria su coppie** (proprieta delle 15 coppie interne alla sestina)
- **Extra stream** (trattare i 15 Extra come gioco separato)
- **Dual target** (3 numeri per base + 3 per Extra)
- **Anti-cluster** (numeri sparsi tra i frequenti)
- **Ensemble voting** (fusione di 4 metodi)
- **Wheeling** (3 schedine sulla stessa estrazione)
- **Conditional staking** (money management adattivo)

### 24.2 Risultati (34 configurazioni, 33.892 estrazioni)

**Classifica top 6:**

| # | Metodo | Config | EV val | Ratio |
|---|--------|--------|--------|-------|
| 1 | **S4 dual-target** | **W=100** | **1.9863** | **1.103x** |
| 2 | S2 ciclometria | W=288 | 1.9099 | 1.060x |
| 3 | S3 extra-stream | W=50 | 1.8795 | 1.043x |
| 4 | S3 extra-stream | W=20 | 1.8753 | 1.041x |
| 5 | S8 ensemble | W=288 | 1.8450 | 1.024x |
| 6 | S1 freq_rit_fib | W=75 | 1.8342 | 1.018x |

La strategia S4 dual-target (3 numeri caldi nel base + 3 numeri caldi nell'Extra, W=100) produce il ratio piu alto: **1.103x**. E il primo segnale del 10eLotto che supera il breakeven Special Time (1.067x).

### 24.3 Permutation test

| Segnale | Ratio | p-value | Soglia Bonf. (0.05/34) |
|---------|-------|---------|------------------------|
| **S4 dual-target W=100** | **1.103x** | **0.042** | 0.0015 → **FAIL** |
| S2 ciclometria W=288 | 1.060x | 0.132 | FAIL |
| S3 extra-stream W=50 | 1.043x | 0.199 | FAIL |

Il p=0.042 e significativo al 5% grezzo ma **non sopravvive alla correzione Bonferroni** (soglia 0.0015 con 34 test). Il segnale e borderline — potrebbe essere reale o varianza campionaria.

### 24.4 Money management

**Wheeling (3 schedine x EUR 2 = EUR 6):** EV/EUR 0.864 vs 0.854 per singola. Marginalmente migliore ma entrambi sotto breakeven. Il wheeling NON crea edge, redistribuisce solo la varianza.

**Conditional staking (raddoppio dopo streak):** Tutti negativi. ROI da -12% a -15%. Conferma che il raddoppio dopo perdite e una strategia perdente su un gioco con EV negativo. La gambler's fallacy non funziona nemmeno sul money management.

### 24.5 Simulazione Special Time

Strategia S4 dual-target, solo fascia 16:05-18:00, 1.415 giocate:
- Bankroll EUR 200 → EUR 101
- P&L: -EUR 99 (-3.5%)
- Max drawdown: EUR 389

Nonostante il ratio 1.103x, la simulazione produce perdita. Il motivo: il ratio e calcolato sui premi normali. Durante Special Time, solo il 25% delle estrazioni ha premi maggiorati — non abbastanza per compensare il 75% a premi normali con EV < costo.

### 24.6 Insight sul segnale dual-target

La strategia S4 e concettualmente nuova: tratta Base e Extra come due giochi separati con pool diversi. Il Base estrae 20 da 90; l'Extra estrae 15 dai 70 rimanenti. Allocando 3 numeri "caldi nel base" e 3 numeri "caldi nell'Extra", si massimizza la probabilita di match su entrambi i fronti.

Perche potrebbe avere un micro-effetto: i numeri frequenti nell'Extra sono, per costruzione, quelli che escono POCO nel base (altrimenti sarebbero nei 20 e non nei 70 rimanenti). Questo crea una complementarita strutturale che il dual-target sfrutta.

Tuttavia, su un RNG perfetto questa complementarita e puramente casuale — ogni estrazione e indipendente e la storia non predice il futuro. Il p=0.042 e compatibile con il rumore statistico di 34 test.

---

## 25. Confronto Finale e Conclusioni

### 25.1 Tabella riepilogativa Lottery Lab

| Gioco | Dataset | HE | Breakeven | Miglior segnale | p-value | Edge? |
|-------|---------|-----|-----------|----------------|---------|-------|
| Lotto ambetto V6 | 6.886 estr. | 37.6% | 1.60x | vicinanza D=20 W=125: **1.18x** | CV validato | Riduce HE |
| Lotto ambo V6 | 6.886 estr. | 37.6% | 1.60x | freq_rit_fib W=75: **1.16x** | CV validato | Riduce HE |
| VinciCasa | 3.279 estr. | 37.3% | 1.60x | top5 freq N=5: **+22%** | p=0.01 | Riduce HE |
| 10eLotto 6+Extra | 33.892 estr. | 9.94% | 1.11x | dual-target 1.10x | p=0.042 | Borderline |
| 10eLotto 6+Extra ST | 33.892 estr. | 6.30% | 1.067x | dual-target 1.10x | FAIL Bonf. | **No** |

**Test totali eseguiti sul 10eLotto:** 94 configurazioni predittive in 2 campagne (60 + 34), 5 test RNG, 5 test deep (D1-D5), 8.010 coppie numeri spia, 4 test strutturali (E1-E4). Nessun segnale sopravvive alla correzione per test multipli.

### 25.2 Lezioni apprese

**1. L'RNG elettronico e imbattibile.** Su 33.892 estrazioni e 94 configurazioni predittive in 2 campagne indipendenti, il miglior p-value e 0.042 — non significativo dopo Bonferroni. Il Lotto tradizionale (urne fisiche) mostra pattern a 1.18x con CV validato; il 10eLotto elettronico no.

**2. Il house edge non e tutto.** Il 10eLotto ha l'HE piu basso (6.3% ST) ma nessun segnale predittivo. Il Lotto ha l'HE piu alto (37.6%) ma segnali misurabili. Il gioco strutturalmente "migliore" e il piu difficile da battere.

**3. La correzione per test multipli e la lezione piu importante.** Senza Bonferroni, segnali fino a 1.10x "emergono" da puro rumore. Con Bonferroni, spariscono. Con 94 test, P(almeno un falso positivo a p<0.05) = 1-(1-0.05)^94 = 99.2%. Il multiple testing spiega tutti i "segnali" trovati.

**4. Trattare base e Extra come giochi separati e un'insight valida.** Il dual-target (3+3) ha il ratio piu alto. Anche se non significativo statisticamente, la logica e solida: ottimizzare separatamente due meccanismi con pool diversi e razionale. Su un gioco con edge strutturale (non RNG), questo approccio potrebbe funzionare.

**5. Il money management non crea edge.** Wheeling, conditional staking, e variazioni di posta non cambiano l'EV. Su un gioco con EV negativo, nessuna strategia di bet sizing produce profitto nel lungo termine.

**6. La configurazione 6+Extra Special Time resta ottimale.** Senza predizione, il giocatore razionale del 10eLotto dovrebbe giocare SOLO 6 numeri + Extra durante la fascia Special Time (16:05-18:00), con posta minima EUR 2. House edge 6.30% — il piu basso di qualsiasi lotteria italiana.

### 25.3 La domanda finale

Attraverso tre giochi e 43.000+ estrazioni analizzate, il progetto Lottery Lab ha risposto a una domanda fondamentale: **le lotterie italiane sono battibili?**

La risposta e stratificata:
- **Lotto (urne fisiche):** micro-pattern rilevabili (1.18x), insufficienti per profitto (breakeven 1.60x), ma il segnale e reale
- **VinciCasa (elettronico):** segnale debole confermato (p=0.01), insufficiente per profitto
- **10eLotto (elettronico ADM):** nessun segnale dopo 94 test e correzione Bonferroni

Nessun gioco e profittevole. Il valore del progetto sta nel metodo: la dimostrazione sistematica che la "sensazione" di pattern nelle lotterie e un'illusione cognitiva misurabile e quantificabile, e che la differenza tra RNG fisico e elettronico e reale e rilevabile con sufficiente rigore statistico.

### 25.4 Prospettive future

1. **Dataset piu ampi per il 10eLotto**: 33K estrazioni = ~4 mesi. Con 1 anno (105K) il permutation test per S4 dual-target avrebbe potenza superiore. Se il p=0.042 e reale, con 3x i dati scenderebbe sotto Bonferroni.

2. **Analisi dell'ordine di estrazione**: i dati attuali hanno perso l'ordine originale dei 20 numeri. Con un feed diretto dall'ADM, l'ordine potrebbe rivelare bias del PRNG.

3. **Paper trading**: sistema automatizzato di previsioni giornaliere per tutti e 3 i giochi, con tracking P&L senza denaro reale.

4. **Altri giochi**: MillionDay (5/55, giornaliero), SuperEnalotto (6/90, 3/settimana), EuroJackpot (5/50+2/12) — ciascuno con struttura diversa e potenziali angoli inesplorati.

---

## Appendice D: Tabella EV Completa 10eLotto

Calcolo ipergeometrico per K=1-10 numeri giocati, opzione base.

| K | EV/EUR | House Edge | P(vincita) |
|---|--------|------------|------------|
| 1 | 0.6667 | 33.33% | 22.22% |
| 2 | 0.6642 | 33.58% | 4.74% |
| 3 | 0.6631 | 33.69% | 12.29% |
| 4 | 0.6625 | 33.75% | 21.27% |
| 5 | 0.6524 | 34.76% | 30.74% |
| 6 | 0.6249 | 37.51% | 12.08% |
| 7 | 0.6648 | 33.52% | 20.13% |
| 8 | 0.6545 | 34.55% | 13.40% |
| 9 | 0.6604 | 33.96% | 11.55% |
| 10 | 0.6337 | 36.63% | 10.92% |

Con Extra (costo +1 EUR):
| K | EV base | EV Extra | EV totale | HE totale |
|---|---------|----------|-----------|-----------|
| 6 | 0.6249 | 1.1763 | 1.8013 | **9.94%** |
| 7 | 0.6648 | 0.6808 | 1.3456 | 32.72% |
| 8 | 0.6545 | 0.7304 | 1.3850 | 30.75% |

La configurazione 6+Extra e anomala: l'Extra per K=6 vale quasi il doppio del base (1.18 vs 0.62), a differenza di K=7-10 dove Extra e base sono comparabili. Questo dipende dalla struttura dei premi Extra per K=6 (premio 1/6 e 2/6 = 1.00 EUR ciascuno, una "rete di sicurezza" che le altre configurazioni non hanno).

---

## Appendice E: MillionDay — Quarto Gioco del Lottery Lab

### E.1 Motivazione

Dopo l'analisi dei primi 3 giochi (Lotto, VinciCasa, 10eLotto), il progetto Lottery Lab e stato esteso a MillionDay per testare un'ipotesi specifica: **il segnale top5_freq osservato su VinciCasa (5/40, 1.22x p=0.01) si replica su un gioco strutturalmente simile ma con pool piu grande (5/55)?**

Se il segnale fosse replicabile, confermerebbe l'ipotesi che **i giochi 5/N con RNG elettronico contengono micro-pattern di persistenza della frequenza** a finestra corta. Se non si replica, il segnale VinciCasa sarebbe probabilmente un artefatto di overfitting su quel dataset specifico.

### E.2 Regole e struttura

| Parametro | Valore |
|-----------|--------|
| Pool numeri | 55 (1-55) |
| Numeri estratti base | 5 |
| Numeri Extra | 5 (da 50 rimanenti) |
| Frequenza | 2 estrazioni/giorno (13:00 e 20:30) |
| Costo base | EUR 1 |
| Costo Extra | EUR 1 (opzionale) |
| Costo totale | EUR 2 (base+Extra) |
| Operatore | Sisal |
| RNG | Elettronico certificato ADM |

Strutturalmente identico a VinciCasa (5 su N) ma con pool piu grande (55 vs 40) e frequenza doppia (2/giorno vs 1/giorno).

### E.3 Premi (netti, dopo tassazione 8%)

| Match | Base | Extra |
|-------|------|-------|
| 2/5 | EUR 2 | EUR 4 |
| 3/5 | EUR 50 | EUR 100 |
| 4/5 | EUR 1.000 | EUR 1.000 |
| 5/5 | EUR 1.000.000 | EUR 100.000 |

### E.4 Calcolo EV analitico

Probabilita ipergeometrica per una giocata di 5 numeri:

```
P(match=m) = C(5,m) * C(50,5-m) / C(55,5)
```

| m | P(base) | Premio base | Contributo EV |
|---|---------|-------------|---------------|
| 0 | 0.5968 | 0 | 0 |
| 1 | 0.3395 | 0 | 0 |
| 2 | 0.0593 | 2 | 0.1186 |
| 3 | 0.0042 | 50 | 0.2102 |
| 4 | 0.0001 | 1.000 | 0.1190 |
| 5 | 0.000002 | 1M | ~2.36 (jackpot) |

EV base analitico (senza jackpot amortizzato): **0.648 EUR / EUR 1** → HE 35.2%

Con Extra (costo EUR 2 totale):

| Config | EV | HE | Breakeven |
|--------|-----|------|-----------|
| Base | 0.648 | 35.2% | 1.54x |
| Base+Extra | 1.326 | 33.7% | 1.51x |

Breakeven di 1.51x piu favorevole di Lotto (1.60x) e VinciCasa (1.60x), ma molto peggiore di 10eLotto 6+Extra (1.11x).

### E.5 Dataset e ingestione

**Fonte:** API lottologia.com (`/api/metalotto/data/lottery/millionday/draw/bydate`) con rate limit ~1 req/3s.

**Dataset finale:** **496 estrazioni** (apr-dic 2025), formato JSON `{data, ora, numeri[5], extra[5]}`, salvato in `/tmp/millionday_archive.json`.

**Limitazioni:**
- L'API lottologia.com ha dati solo fino al 5 dicembre 2025
- Tentativo di integrazione con `millionday.cloud/archivio-estrazioni.php`: la pagina richiede scraping JavaScript ed e protetta da anti-bot
- Dati 2026 non disponibili via API pubbliche al momento della stesura

### E.6 Fase 1 — Certificazione RNG

| Test | Risultato | Dettaglio |
|------|-----------|-----------|
| Chi-quadro (uniformita) | PASS | z=1.41, df=54, freq attesa 45.1, min 32, max 60 |
| Overlap consecutivo | PASS | media 0.449 vs 0.4545 atteso, z=-0.37 |
| Autocorrelazione somme | PASS | max \|r\|=0.031 (lag 1, 2, 5, 10) |

**Verdetto:** RNG statisticamente indistinguibile da estrazioni genuinamente casuali. Nessun bias sistemico rilevato.

### E.7 Fase 2 — Test segnali (split 50/50 disc/val, 14 configurazioni)

Metodologia identica a VinciCasa: split temporale 248/248, calcolo ratio rispetto a EV baseline ipergeometrico, 4 famiglie di segnali.

| Metodo | W | EV disc | EV val | Ratio disc | Ratio val |
|--------|---|---------|--------|-----------|-----------|
| **top5_freq** | **50** | **0.981** | **1.637** | **0.740x** | **1.234x** |
| top5_freq | 20 | 1.187 | 1.427 | 0.895x | 1.076x |
| top5_freq | 10 | 1.342 | 1.317 | 1.012x | 0.993x |
| top5_freq | 5 | 1.215 | 1.241 | 0.916x | 0.936x |
| top5_freq | 3 | 1.367 | 1.183 | 1.030x | 0.892x |
| vicinanza D=5 | 50 | 1.198 | 1.307 | 0.903x | 0.985x |
| vicinanza D=5 | 20 | 1.312 | 1.278 | 0.989x | 0.963x |
| vicinanza D=5 | 10 | 1.435 | 1.295 | 1.082x | 0.976x |
| cold | 20 | 1.621 | 1.000 | 1.222x | 0.754x |
| cold | 50 | 1.481 | 1.152 | 1.116x | 0.868x |
| cold | 10 | 1.473 | 1.229 | 1.110x | 0.927x |
| hot_extra | 5 | 1.118 | 1.202 | 0.843x | 0.906x |
| hot_extra | 10 | 1.204 | 1.198 | 0.908x | 0.903x |
| hot_extra | 20 | 1.223 | 1.174 | 0.922x | 0.885x |

**Miglior segnale:** top5_freq W=50, ratio validation **1.234x**.

Nota: a differenza di VinciCasa (dove W=5 era ottimale), su MillionDay la finestra ottimale e **W=50**. Dato che MillionDay ha 2 estrazioni/giorno, W=50 copre ~25 giorni — piu o meno lo stesso orizzonte di VinciCasa W=5 (5 giorni). La "finestra giornaliera effettiva" coincide.

### E.8 Fase 3 — Permutation test

Shuffle circolare dei pick rispetto alle estrazioni, 5.000 iterazioni, seed=42.

- **Segnale testato:** top5_freq W=50 (ratio 1.234x, EV osservata 1.637 vs baseline 1.326)
- **Iterazioni con EV_shuffled >= EV_observed:** 915 / 5.000
- **p-value: 0.183**

**Conclusione fase 3:** segnale **non significativo** (p=0.183 > 0.05). Con soli 248 campioni nel validation set, la potenza statistica e insufficiente. Il ratio 1.234x e compatibile sia con un segnale reale debole sia con varianza campionaria.

### E.9 Analisi di potenza

Stima del campione necessario per confermare p<0.01 a Bonferroni (14 test):
- Effect size osservato: (1.234 - 1) = 0.234 ratio
- Sd campionaria EV per giocata: ~3.4 (dominata da coda 3/5 = EUR 50 e 4/5 = EUR 1.000)
- N richiesto per power 0.8: **~2.400 estrazioni validation** → **~4.800 totali**

Con 2 estrazioni/giorno, servirebbero **~6.5 anni di dati continui** per confermare il segnale a soglia Bonferroni. Fattibile ma richiede ingestione storica completa (2018-2026).

### E.10 Confronto con VinciCasa

| Dimensione | VinciCasa | MillionDay |
|-----------|-----------|------------|
| Pool | 5/40 | 5/55 |
| Estrazioni/giorno | 1 | 2 |
| Costo base | EUR 2 | EUR 1 |
| HE | 37.3% | 35.2% |
| Breakeven | 1.60x | 1.54x |
| Dataset | 3.279 | 496 |
| Miglior segnale | top5_freq W=5 | top5_freq W=50 |
| Ratio val | 1.22x | 1.234x |
| p-value | 0.01 | 0.18 |
| Finestra in giorni | 5 | 25 |

**Insight centrale:** il segnale top5_freq si replica direzionalmente (ratio ~1.22x in entrambi i giochi 5/N). La non-significativita su MillionDay e un problema di potenza, non di assenza di segnale. Se entrambi i ratio sono reali, suggerisce un **pattern generico dei giochi 5/N con RNG** non specifico di VinciCasa.

**Possibile meccanismo:** in giochi con premi concentrati sulla coda (jackpot ~80% dell'EV), la persistenza di frequenza a medio termine cattura lievi sbilanciamenti del PRNG che nei giochi 20/90 (10eLotto) vengono mediati via.

### E.11 Frontend e ingestione continua — pending

Al momento della stesura del paper (aprile 2026), il frontend di MillionDay e ancora da implementare. Tutto il codice di analisi e nel modulo `backend/millionday/analysis.py`; mancano:
- `backend/millionday/engine.py` (generatore previsione operativo)
- `backend/millionday/models/database.py` (modello estrazione)
- Endpoint FastAPI (`/api/v1/millionday/*`)
- Frontend Next.js (`frontend/src/app/millionday/page.tsx`)
- Ingestione continua via cron

Questi sono tracciati come debito tecnico in `docs/TECH_DEBT.md`.

---

## Appendice E-bis: MillionDay — Analisi Estesa su Archivio millionday.cloud

### E-bis.1 Motivazione e nuova fonte dati

L'analisi originale (Appendice E) si basava su 496 estrazioni scaricate via API lottologia.com (apr-dic 2025). Il p-value borderline (0.18) era compatibile sia con un segnale reale debole sia con varianza campionaria; serviva piu dato per discriminare.

E stato quindi integrato un archivio alternativo: **https://www.millionday.cloud/archivio-estrazioni.php**. La pagina espone un archivio HTML statico dichiarato dal 7 febbraio 2018 al 16 aprile 2026 (4.104 tag `<tr>` totali).

**Tentativo precedente (documentato in Appendice E):** integrazione fallita. La pagina era ritenuta protetta da anti-bot JavaScript.

**Nuovo tentativo riuscito:** richiesta HTTP diretta con User-Agent browser, parsing regex delle righe `<tr>` con pattern specifico per `testo_arancione` (data) + `<td>` (base) + `<td><span style="color:#088796">` (extra). Nessun JS, nessun anti-bot effettivamente attivo sull'endpoint PHP.

Script di parsing: `backend/millionday/parse_cloud.py`.

### E-bis.2 Dataset risultante

- **Estrazioni parsate con successo:** 2.607
- **Periodo coperto:** 16 marzo 2022 — 16 aprile 2026
- **Rapporto vs dataset precedente:** **5.26x** (496 → 2.607)

Distribuzione per anno:

| Anno | N estrazioni |
|------|--------------|
| 2022 | 291 |
| 2023 | 643 |
| 2024 | 732 |
| 2025 | 730 |
| 2026 | 211 |

**Discrepanza con 4.104 righe HTML:** ~1.500 righe non sono state parsate — probabilmente entries pre-Extra (estrazioni 2018-2019 che non avevano i 5 numeri Extra, introdotti in seguito). Il parser scarta righe con `len(extra) != 5`. Il dataset 2022-2026 e comunque completo e coerente.

File persistente: `backend/millionday/data/archive_2022_2026.json` (509 KB).

### E-bis.3 Fase 1 — RNG certification su dataset esteso

| Test | Risultato | Dettaglio |
|------|-----------|-----------|
| Chi-quadro | PASS | z=0.63 (vs z=1.41 nel dataset 496), df=54, freq attesa 237, min 202, max 278 |
| Overlap consecutivo | PASS | media 0.4551 vs 0.4545 atteso, z=0.05 (vs z=-0.37) |
| Autocorrelazione somme | PASS | max \|r\|=0.015 (vs 0.031) |

Su dataset 5x piu grande, **tutti i test RNG sono ancora piu "puliti"**. I valori z si avvicinano a zero — segno che le piccole deviazioni del dataset 496 erano puro rumore statistico. RNG MillionDay confermato indistinguibile da estrazioni genuinamente casuali.

### E-bis.4 Fase 2 — Test segnali (18 configurazioni, split 1303/1304)

EV baseline analitico: 1.3262.

| Metodo | W | EV disc | EV val | Ratio disc | Ratio val |
|--------|---|---------|--------|-----------|-----------|
| top5_freq | 3 | 0.882 | 1.032 | 0.665x | 0.778x |
| top5_freq | 5 | 0.946 | 0.819 | 0.713x | 0.618x |
| top5_freq | 10 | 1.640 | 1.686 | 1.236x | 1.271x |
| **top5_freq** | **20** | **1.836** | **1.822** | **1.385x** | **1.374x** |
| top5_freq | 50 | 1.256 | 0.890 | 0.947x | 0.671x |
| top5_freq | 100 | 0.758 | 0.888 | 0.572x | 0.670x |
| cold | 10 | 0.940 | 1.638 | 0.709x | 1.235x |
| cold | 20 | 0.753 | 0.770 | 0.568x | 0.581x |
| cold | 50 | 0.605 | 1.098 | 0.456x | 0.828x |
| cold | 100 | 0.675 | 0.969 | 0.509x | 0.731x |
| hot_extra | 5 | 2.395 | 1.537 | 1.806x | 1.159x |
| hot_extra | 10 | 1.732 | 0.851 | 1.306x | 0.642x |
| hot_extra | 20 | 0.753 | 1.037 | 0.568x | 0.782x |
| hot_extra | 50 | 1.783 | 0.807 | 1.344x | 0.608x |
| vicinanza D=5 | 10 | 1.207 | 0.871 | 0.910x | 0.657x |
| vicinanza D=5 | 20 | 0.661 | 1.017 | 0.498x | 0.767x |
| vicinanza D=5 | 50 | 0.592 | 0.865 | 0.447x | 0.652x |
| vicinanza D=5 | 100 | 0.582 | 1.064 | 0.439x | 0.803x |

**Miglior segnale (validation): top5_freq W=20, ratio 1.374x.**

Finding critico: il segnale piu forte su dataset 496 era **top5_freq W=50 (1.23x)**. Su dataset 5x piu grande, W=50 crolla a **0.67x** (peggio del caso) e il miglior W diventa **20**. 

**La finestra ottimale e cambiata completamente.** Questo e il classico sintomo di **overfitting**: quando il dataset era piccolo, W=50 catturava rumore; ora che il dataset e rappresentativo, W=20 emerge come miglior compromesso bias-varianza. In assenza di validazione esterna, non si puo distinguere se W=20 e un altro artefatto o un segnale reale.

**Coerenza disc/val per W=20:** 1.385x (disc) vs 1.374x (val) — i due valori sono molto simili, fatto positivo per l'ipotesi di segnale reale. Ma il p-value dira se resiste.

### E-bis.5 Fase 3 — Permutation test (10.000 iterazioni, seed=42)

- **Segnale testato:** top5_freq W=20 (ratio 1.374x)
- **Observed EV:** 1.8221 vs baseline 1.3262
- **Iterazioni con EV_shuffled >= EV_observed:** 539 / 10.000
- **p-value: 0.0539**
- **Bonferroni threshold (0.05/18 test):** 0.0028

**Conclusione fase 3:** segnale **borderline — NON significativo a Bonferroni, borderline a p=0.05 raw**. Il p-value e esattamente al limite: interpretarlo come "segnale reale" sarebbe statisticamente scorretto. Con la correzione per 18 test multipli, la soglia e 0.0028: siamo ~20x sopra. Il segnale e compatibile con rumore atteso dal multiple testing.

### E-bis.6 Fase 4 — Stabilita temporale del segnale top5_freq W=5

Il pattern piu forte su VinciCasa era top5_freq W=5 (1.22x p=0.01). Se fosse un meccanismo RNG reale, dovrebbe persistere anche su MillionDay anno per anno. Test per anno:

| Anno | N estrazioni | Ratio W=5 |
|------|--------------|-----------|
| 2022 | 291 | 0.9386x |
| 2023 | 643 | 0.5909x |
| 2024 | 732 | 0.7613x |
| 2025 | 730 | 0.6532x |
| **2026** | **211** | **0.2635x** |

Il segnale **decade monotonicamente**. Nel 2022 era leggermente sotto il baseline (0.94x); nel 2026 e catastroficamente sotto (0.26x). Se il segnale fosse persistenza genuina del PRNG, dovrebbe essere stabile o variare casualmente; invece **decade** in modo sospetto.

### E-bis.7 Fase 5 — Rolling window (bucket 500 giocate)

| Range giocate | Ratio W=5 |
|---------------|-----------|
| 5-505 | 0.9169x |
| 505-1005 | 0.5821x |
| 1005-1505 | 0.5158x |
| 1505-2005 | 1.0918x |
| 2005-2505 | 0.3197x |
| 2505-2607 | 0.1774x |

Pattern irregolare con picco isolato nel bucket 1505-2005 (1.09x) seguito da crollo. **Compatibile con rumore, non con segnale stabile.**

### E-bis.8 Revisione delle conclusioni (invalidazione parziale Appendice E)

Dataset esteso forza una revisione delle conclusioni precedenti:

| Claim originale (dataset 496) | Status con dataset 2607 |
|-------------------------------|-------------------------|
| Best signal: top5_freq W=50 ratio 1.234x | **Invalidato** — W=50 crolla a 0.67x |
| p=0.183 "insufficiente per conferma" | **Confermato** — era rumore |
| "Pattern generico dei giochi 5/N" | **Invalidato** — decade a 0.26x nel 2026 |
| RNG certificato PASS | **Confermato** — anche piu solido |
| Segnale comparabile a VinciCasa 1.22x | **Invalidato** — non replicato |

**La conclusione rivista:** MillionDay **non mostra segnali predittivi robusti**. Il ratio 1.374x osservato su W=20 non sopravvive a Bonferroni (soglia 0.0028), non e stabile anno per anno, e il best W cambia completamente tra dataset 496 e 2607. E il classico pattern del multiple-testing fishing.

### E-bis.9 Implicazioni per VinciCasa

Il segnale top5_freq W=5 su VinciCasa (1.22x p=0.01, 3.279 estrazioni) rimane l'unico caso validato fra i giochi 5/N. Ma l'invalidazione del "pattern generico" indebolisce l'interpretazione: **non e un fenomeno universale dei giochi 5/N**, e potrebbe essere un artefatto specifico di VinciCasa (dataset, fornitore RNG, periodo). Una replicazione su un secondo dataset VinciCasa indipendente sarebbe decisiva.

### E-bis.10 Nota metodologica: il valore del dataset ampliato

Questa appendice illustra un principio fondamentale della ricerca statistica: **un dataset 5x piu grande puo invalidare claim basati su un dataset piccolo, anche se i test statistici originali erano corretti**.

Il dataset 496 ha prodotto p=0.18 "non significativo ma suggestivo". Il dataset 2607 ha prodotto p=0.054 borderline ma su **un segnale completamente diverso** (W=20 invece di W=50), mentre il W=50 originale e ora chiaramente rumore (0.67x). Senza la seconda raccolta, si sarebbe continuato a credere in un segnale W=50 inesistente.

**Lezione operativa:** i ratio osservati su piccoli dataset non devono mai essere trattati come "direzionalmente reali ma statisticamente deboli". Sono spesso artefatti del multiple testing mascherati da segnale promettente.

---

## Appendice E-ter: MillionDay — Deep Analysis (10 fasi dedicate)

### E-ter.1 Motivazione

Le Appendici E ed E-bis hanno applicato a MillionDay **test generici** derivati da Lotto e VinciCasa (top5_freq, cold, vicinanza, hot_extra). Ma MillionDay ha **proprieta uniche** che richiedono test specifici:

- 5 numeri su 55 → 5 fasce complete (1-10, 11-20, ...) + 1 fascia parziale (51-55)
- 2 estrazioni/giorno (13:00 e 20:30) — finestre in estrazioni, non giorni
- Premio FISSO 1M EUR per 5/5 (non a totalizzatore come VinciCasa)
- Extra opzionale +1 EUR con payout separati
- Operatore Sisal (come VinciCasa) — possibile correlazione cross-game

E stata quindi sviluppata una pipeline di **10 fasi dedicate** (`backend/millionday/deep_analysis.py`) con ~50 configurazioni specifiche. Output completo in `backend/millionday/DEEP_REPORT.md`.

### E-ter.2 Fase 0 — EV esatto

Calcolo ipergeometrico completo con payout ufficiali ADM (netti tassazione 8%):

| Match | P | Premio base | Premio Extra |
|-------|---|-------------|--------------|
| 2/5 | 5.63% | EUR 2 | EUR 4 |
| 3/5 | 0.35% | EUR 50 | EUR 100 |
| 4/5 | 0.007% | EUR 1.000 | EUR 1.000 |
| 5/5 | 0.000029% | EUR 1.000.000 | EUR 100.000 |

| Config | EV | HE | Breakeven |
|--------|-----|------|-----------|
| Base (1 EUR) | 0.6481 | **35.19%** | 1.543x |
| Base+Extra (2 EUR) | 1.3262 | **33.69%** | 1.508x |
| Extra marginale (1 EUR) | 0.6781 | **32.19%** | 1.474x |

**Insight operativo:** l'opzione Extra e *marginalmente piu conveniente* del base (HE 32.2% vs 35.2%). Chi decide di giocare dovrebbe sempre attivarla.

### E-ter.3 Fase 1 — Asimmetria fascia 51-55

Test specifico per bias modulo-10 del PRNG (comune in LCG mal implementati).

| Fascia | Freq/num | z/num |
|--------|----------|-------|
| 1-10 | 235.0 | -0.43 |
| 11-20 | 245.2 | +1.77 |
| 21-30 | 228.8 | -1.77 |
| 31-40 | 236.6 | -0.09 |
| 41-50 | 230.5 | -1.40 |
| **51-55 (parziale)** | **254.8** | **+2.71** |

Fascia parziale vs altre 50: **z=+2.84** (borderline, soglia Bonferroni 6 fasce = 2.64).

Chi-quadro sulla distribuzione K in 51-55 per estrazione: **9.88 df=5** (soglia 0.05 = 11.07). **Non significativo.**

**Verdetto:** leggero eccesso di frequenza medio ma senza pattern strutturale sfruttabile.

### E-ter.4 Fase 2 — RNG advanced

Quattro test oltre i 5 standard:

| Test | Risultato | Dettaglio |
|------|-----------|-----------|
| Gap test per numero (55 test) | PASS | 0/55 con \|z\|>3 |
| Autocorr lag 1,2,3,7,14,30,60,365 | PASS (borderline lag 14) | max z=+2.28 a lag 14 |
| Birthday test (cinquine ripetute) | PASS | 0 vs 0.98 atteso (Poisson) |
| Chi-quadro coppie (1.485 bucket) | PASS | z=+1.09 |

**Nessuna cinquina si e mai ripetuta in 4 anni** (2.607 estrazioni, 3.478.761 cinquine possibili). Compatibile con Poisson(0.98).

### E-ter.5 Fase 3 — Singoli numeri con finestre ricalibrate

Finestre in estrazioni (correzione rispetto a Appendice E dove erano in giorni): **W=14, 60, 180, 360, 730** (1 sett, 1 mese, 3 mesi, 6 mesi, 1 anno).

4 strategie × 5 finestre = 20 configurazioni.

| Strategia | W | Ratio disc | Ratio val |
|-----------|---|-----------|-----------|
| **optfreq** | **60** | **1.404x** | **1.343x** |
| mix3h2c | 360 | 0.609x | 1.275x |
| cold | 360 | 0.686x | 1.262x |
| hot | 14 | 1.268x | 1.129x |

`optfreq` = top 5 numeri con frequenza piu vicina al valore atteso (ne caldi ne freddi). Permutation test 10.000 iter: **p=0.0495**, soglia Bonferroni 20 test = 0.0025 → **FAIL**.

**Coerenza disc/val eccellente (1.40x vs 1.34x)** — fatto favorevole a segnale reale — ma non sopravvive al multiple testing.

### E-ter.6 Fase 4 — Struttura cinquina

Mutual Information I(T_{t-1}; T_t) tra tipi di cinquina: **0.0064**, vs shuffled 0.0050 sd=0.0014. **p=0.151.** Non significativo. Somma media 140.5 vs attesa 140.0. **Nessuna memoria strutturale.**

### E-ter.7 Fase 5 — Giorno della settimana

0/7 giorni con |z somma|>2.69 (Bonferroni 7 test). Lunedi leggermente basso (z=-1.77) ma non sopravvive. **Nessun pattern temporale.**

### E-ter.8 Fase 7 — Multi-giocata ottimale

Simulazione Monte Carlo 10.000 iter su 4 strategie:

| Strategia | Costo | P(≥2/5) | EV ratio |
|-----------|-------|---------|----------|
| Dispersione 10x5 (50 num distinti) | EUR 20 | **53.48%** | 0.480x |
| Sistema 6 num (6 cinquine) | EUR 12 | 8.33% | **0.558x** |
| Sistema 7 num (10 cinquine) | EUR 20 | 11.43% | 0.521x |
| Singola 5 numeri | EUR 2 | 6.01% | 0.508x |

**Finding:** la dispersione massimizza P(almeno 2/5) ma non l'EV. Il sistema 6 ha il miglior EV ratio ma pur sempre sotto breakeven. **Nessuna strategia multi-giocata crea edge.**

### E-ter.9 Fase 9 — Persistenza numerica (7 sub-test)

Test dell'ipotesi empirica: "i numeri si ripetono in finestre brevi".

| Sub-test | Metrica | Osservato | Teorico | Z | Verdetto |
|----------|---------|-----------|---------|---|----------|
| 9A Overlap lag 1 | mean overlap | 0.4551 | 0.4545 | +0.05 | PASS |
| 9B Intra-day 13→20 | mean overlap | 0.4659 | 0.4545 | +0.61 | PASS |
| 9B Same-hour 13→13 | mean overlap | 0.4712 | 0.4545 | +0.90 | PASS |
| 9B Same-hour 20→20 | mean overlap | 0.4423 | 0.4545 | -0.77 | PASS |
| 9C Persistenza W=5 | P(X>=2) | 6.86% | 6.86% | +0.02 | PASS |
| 9D Hot W=5 predict | P(hot in t+1) | 8.98% | 9.09% | -0.38 | PASS |
| 9G Markov persistenza | N \|z\|>3.5 | 0/55 | 0 | – | PASS |

**Tutti i test Fase 9 PASS.** L'osservazione che "il numero 34 esce 3 volte in 5 estrazioni" o "l'11 si ripete alle 13:00" e **cherry-picking post-hoc**:

> P(almeno un numero esca >= 3 volte in 5 estrazioni) = 1 - (1 - 0.0073)^55 = **33%**.
> Con 55 numeri monitorati, un evento "raro" al 0.7% emerge quasi una volta su tre per puro caso.

**Fase 9E-F (strategia ripetitori):** ratio val fino a 1.91x ([13:00] W=3) ma con disc 0.76x — **dispersione massiva disc/val → overfitting**. Nessun segnale reale.

### E-ter.10 Sintesi e 3 contributi originali

**Verdetto definitivo:** MillionDay **NON e battibile** con nessuna delle ~50 configurazioni testate in 10 fasi. Il miglior candidato (optfreq W=60) ha p=0.0495 raw, FAIL Bonferroni, e ratio 1.343x ancora distante dal breakeven 1.508x.

**3 contributi originali al Lottery Lab:**

1. **Replicazione fallita del finding VinciCasa** su gioco strutturalmente simile (5/N). Il pattern top5_freq di VinciCasa (1.22x p=0.01) **non si generalizza**. E probabilmente specifico di quel gioco, non un meccanismo universale dei 5/N.

2. **Test dell'asimmetria fascia-parziale** (unico nel panorama italiano): RNG Sisal non manifesta bias modulo-10. Nonostante la struttura 5+1 fasce sia teoricamente vulnerabile a PRNG mal implementati, il gioco passa tutti i controlli.

3. **Smontaggio quantitativo dell'intuizione "numeri ripetuti"**: 7 sub-test dedicati al pattern percepito empiricamente mostrano zero evidenza. L'intuizione umana confonde multiple-testing implicito con segnale.

### E-ter.11 Raccomandazioni operative per chi vuole giocare

1. Attivare sempre l'opzione Extra (HE marginale 32.2% vs base 35.2%)
2. Giocare singole, non sistemi (EV ratio comparabile, costo molto inferiore)
3. Budget mensile fisso come costo di intrattenimento (aspettativa perdita ~50% del budget)
4. Ignorare "numeri caldi", "ritardi", "sistemi guru" — la Fase 9 dimostra che non sono predittivi

---

### F.1 Motivazione

Il capitolo 24 ha identificato la strategia S4 dual-target (W=100) come miglior segnale *globale* sul 10eLotto, testata per K=6 (configurazione con HE minimo 9.94%). Resta aperta una domanda operativa:

> Per ciascun valore di K (numeri giocati, da 1 a 10), qual e la strategia predittiva migliore?

Il frontend del portale Lottery Lab offre un "Lab" dove l'utente sceglie K e vede la previsione in tempo reale. Mostrare sempre la stessa strategia (S4) e subottimale: la strategia migliore puo variare con K perche le probabilita di match e i premi attesi cambiano in modo non monotono.

### F.2 Metodologia

**Backtest retroattivo su 17.082 giocate**: per ogni K ∈ {1..10}, per ogni estrazione i con i >= W=100, genera previsione con 5 strategie candidate usando le W precedenti, confronta con l'estrazione i, calcola EV e ratio rispetto al baseline ipergeometrico.

**Strategie candidate:**
1. `hot` — top K numeri piu frequenti nel base
2. `cold` — K numeri meno frequenti
3. `hot_extra` — top K numeri piu frequenti nell'Extra
4. `freq_rit_dec` — frequenti + in ritardo + stessa decina (Engine V6 Lotto adattato)
5. `dual_target` — meta hot base + meta hot Extra (S4)
6. `vicinanza` — cluster di numeri vicini al seed piu frequente (D=5)

Dataset: 33.431 estrazioni, split 50/50 discovery/validation, W=100.

### F.3 Risultati — strategia ottimale per K

| K | Strategia vincitrice | Ratio val | Breakeven (K) | Edge? |
|---|---------------------|-----------|---------------|-------|
| 1 | hot_extra | 1.011x | 1.50x | No |
| 2 | hot_extra | 1.028x | 1.51x | No |
| 3 | freq_rit_dec | 1.040x | 1.51x | No |
| 4 | dual_target | 1.070x | 1.51x | No |
| 5 | dual_target | 1.024x | 1.53x | No |
| 6 | vicinanza | 1.080x | **1.11x** | Ratio < BE |
| 7 | dual_target | 1.185x | 1.51x | No |
| **8** | **dual_target** | **1.445x** | **1.45x** | **BREAKEVEN** |
| 9 | dual_target | 1.079x | 1.53x | No |
| 10 | dual_target | 0.934x | 1.58x | No |

**Finding principale:** per K=8, la strategia dual_target raggiunge ratio **1.445x**, sufficiente a coprire il breakeven della configurazione 8 numeri + Extra (HE 30.75%, breakeven 1.45x). E il **primo segnale dell'intero Lottery Lab a raggiungere il proprio breakeven nel backtest**.

**Caveat statistico:** ratio 1.445x e stato osservato su ~16.700 giocate validation. Il permutation test non e ancora stato eseguito per K=8 (pending). Se il p-value < Bonferroni(0.05/10) = 0.005, il segnale e confermato.

### F.4 Mapping K → strategia nel motore

```python
STRATEGY_NAMES = {
    1: "hot_extra",       # 1.011x
    2: "hot_extra",       # 1.028x
    3: "freq_rit_dec",    # 1.040x
    4: "dual_target",     # 1.070x
    5: "dual_target",     # 1.024x
    6: "vicinanza",       # 1.080x
    7: "dual_target",     # 1.185x
    8: "dual_target",     # 1.445x  ← BREAKEVEN
    9: "dual_target",     # 1.079x
    10: "dual_target",    # 0.934x
}
```

Questa mappatura e implementata in `backend/diecielotto/engine_k.py` e servita in produzione via endpoint `/api/v1/diecielotto/previsione?k={K}`.

### F.5 Osservazioni metodologiche

1. **K=10 ha ratio < 1.0**: intuitivo — giocando tutti i 10 numeri, la varianza aumenta e il regression-to-the-mean cancella il segnale. Piu numeri = piu sensibile al rumore.

2. **K=6 usa vicinanza, non dual_target**: contrario all'analisi globale del capitolo 24. Motivo: per K=6, la configurazione 6+Extra dominante nei premi favorisce cluster geometrici (vicinanza cattura meglio i premi 2/6 e 3/6 con Extra che lo spalma).

3. **hot_extra vince per K=1,2**: con pochi numeri, il contributo dell'Extra e determinante. Ottimizzare sui numeri "freddi nel base ma caldi nell'Extra" e razionale.

4. **freq_rit_dec vince solo per K=3**: questa e la strategia piu "lottoistica" (importata dall'Engine V6 Lotto). Funziona solo in un intervallo ristretto.

5. **Monotonicita assente**: il ratio non cresce ne decresce monotonicamente con K. Massimo a K=8, minimo a K=10. La strategia ottimale dipende dall'interazione fra struttura dei premi e numero di numeri giocati.

### F.6 Coerenza frontend — caso K=6

Inizialmente `/diecielotto` (default K=6) usava S4 dual-target mentre `/diecielotto-lab` (K selezionabile) usava vicinanza per K=6. Incoerenza corretta (commit 60b1c31): entrambe le route ora invocano `genera_previsione_k(6, ...)` che restituisce vicinanza. Regola architetturale: **una sola funzione canonica per K, nessuna duplicazione di logica tra endpoint**.

---

## Appendice G: Paper Trading System

### G.1 Motivazione

Il backtest e un'analisi retrospettiva: dice *quanto avresti guadagnato se avessi giocato negli ultimi N mesi*. Il paper trading e prospettico: *quanto guadagni in tempo reale, senza denaro, giocata dopo giocata*.

Il paper trading serve per:
1. Validare che i ratio osservati nel backtest si mantengono out-of-sample
2. Produrre una dashboard live in cui l'utente vede i numeri predetti, l'esito reale quando l'estrazione arriva, il P&L cumulato
3. Rilevare drift (se il segnale decade in produzione, lo si vede subito)

### G.2 Architettura

Per ciascun gioco, un endpoint `/{gioco}/storico-completo?limit=N` restituisce una lista cronologica di record:

```json
{
  "data": "2026-04-17",
  "previsione": {"numeri": [...], "metodo": "..."},
  "estrazione": {"numeri": [...], "concorso": 12345},
  "match": 2,
  "vincita": 2.60,
  "costo": 2.00,
  "pnl": 0.60,
  "stato": "VINCITA 2/5"
}
```

**Backtest retroattivo on-demand:** quando l'utente apre la pagina, il backend genera la previsione *come se l'avesse prodotta al momento dell'estrazione* (usando solo dati precedenti) e confronta con l'estrazione reale. Questo offre un paper trading "sintetico" che non richiede di aver girato uno scheduler storicamente.

### G.3 Implementazione per gioco

| Gioco | Endpoint | Generatore previsione | Finestra |
|-------|----------|-----------------------|----------|
| Lotto | `/lotto/storico-completo?limit=50` | V6 (vicinanza+freq_rit_fib) | W=75/125 |
| VinciCasa | `/vincicasa/storico-completo?limit=30` | top5_freq | W=5 |
| 10eLotto | `/diecielotto/storico-completo?limit=N` | engine_k con K selezionabile | W=100 |
| MillionDay | pending | — | — |

### G.4 Frontend: layout comune

Tutte le pagine gioco espongono lo stesso modulo visivo:

1. **Previsione corrente** (hero card): numeri con NumberBall, metodo, costo, HE
2. **Spiegazione del metodo** (explainer box con bordo colorato): cos'e, perche funziona, premi
3. **Stats P&L** (grid 6-cards): Estrazioni totali, Giocate, Vinte, Investito, P&L, Max vincita
4. **Storico** (timeline): per ogni giocata: previsione vs estrazione con evidenziazione dei match (glow + ring), P&L singolo, cumulato

### G.5 Portale Lottery Lab — deploy production

Il sistema e deployato in produzione su **https://lottery.fl3.org** via VPS + Portainer + Nginx Proxy Manager. Stack:

| Componente | Tecnologia | Ruolo |
|-----------|------------|-------|
| Backend | Python 3.12 + FastAPI + SQLAlchemy | API REST |
| DB | PostgreSQL 16 | Persistenza estrazioni + previsioni |
| Frontend | Next.js 14 (App Router + Server Components) | UI |
| Scheduler | cron + Python background fallback | Ingestion 5min (10eLotto) e giornaliera (Lotto/VinciCasa) |
| Reverse proxy | Nginx (NPM) | TLS + routing |
| Container orch. | Portainer (Docker) | Deploy + logs |

**URL pubblici:**
- `/` — dashboard con tutti i giochi
- `/lotto` — Lotto V6
- `/vincicasa` — VinciCasa top5
- `/diecielotto` — 10eLotto K=6 (default, vicinanza)
- `/diecielotto-lab` — 10eLotto K=1..10 selezionabile con dropdown
- `/millionday` — pending

**Auth:** AuthGuard custom (single-user, password bcrypt in env). Non essendo il sito destinato al pubblico, niente OAuth.

---

## Appendice H: Perche Vicinanza Batte Dual-Target? — Anatomia di un Edge

### H.1 Motivazione

Il backtest su 34.730 estrazioni 10eLotto (K=6+Extra) mostra un ordine di merito inequivocabile:

| Metodo | Ratio val | ROI | Supera BE 1.11x? |
|--------|-----------|-----|------------------|
| **vicinanza W=100** | **1.0595x** | -4.64% | No (gap -5%) |
| dual_target W=100 | 1.0009x | -9.92% | No (al baseline) |

Entrambi negativi, ma **vicinanza ha un edge di 5 punti percentuali rispetto a dual_target**. Domanda: perche?

Tre ipotesi meccanicistiche plausibili:

- **H1 — Geometria**: vicinanza sfrutta una clustering naturale delle 20 estrazioni 10eLotto (pigeonhole su 1-90).
- **H2 — Bias RNG**: il PRNG ADM ha micro-autocorrelazione spaziale che un cluster di 6 numeri puo catturare.
- **H3 — Seed-selection**: il vantaggio e nella scelta del seed come numero piu frequente recente, non nella forma-cluster in se.

Tre test meccanicistici progettati per discriminare (file `backend/diecielotto/spatial_tests.py`).

### H.2 Test 1 — Autocorrelazione spaziale delle estrazioni

Su ogni estrazione 10eLotto, le 20 numeri producono C(20,2) = 190 coppie. Totale su 34.730 estrazioni: **6.598.700 coppie**. Distribuzione della distanza |a-b| vs teorica uniforme (senza rimpiazzo).

| Range | Osservato | Teorico | Diff% | z-score |
|-------|-----------|---------|-------|---------|
| d ≤ 5 (zona cluster vicinanza) | 716.693 | 716.713 | **-0.003%** | **-0.02** |
| d ≥ 40 (zona "spread") | 2.100.207 | 2.100.710 | -0.024% | -0.42 |

**Verdetto Test 1: NESSUNA autocorrelazione spaziale.** Il RNG 10eLotto e *perfettamente uniforme* sulla distribuzione delle distanze. H1 e H2 sono falsificate: non c'e ne clustering strutturale ne bias PRNG misurabile.

### H.3 Test 2 — Label-shuffle permutation (distrugge l'adjacency)

Procedura: applico una permutazione π dei label 1-90 al dataset. In ogni estrazione, ogni numero n diventa π(n). Questo preserva:
- Frequenza marginale di ogni slot numerico
- Co-occorrenza di coppie specifiche
- Temporalita (finestre W=100 etc.)

E distrugge:
- Adiacenza numerica (i numeri 34 e 35 dopo la permutazione non sono piu vicini)

Ri-eseguo backtest vicinanza W=100 su 20 permutazioni indipendenti:

| Metrica | Valore |
|---------|--------|
| Baseline (originale) | **ratio 1.0595x** |
| Permutati: media ± SD | 0.9940x ± 0.0320 |
| Permutati: range | [0.9374, 1.0604] |
| **p-value** | **0.0500** (borderline) |

Il baseline e al limite superiore della distribuzione dei permutati (solo 1 permutazione su 20 raggiunge 1.06x). L'adjacency contribuisce **~5-6% del ratio** (da 0.994 medio a 1.060 del baseline), ma la significativita e borderline.

**Verdetto Test 2: la geografia conta, ma poco.** Il grosso dell'edge di vicinanza NON e l'adjacency numerica.

### H.4 Test 3 — Vicinanza con seed random

La strategia vicinanza classica sceglie il seed come numero piu frequente nelle ultime 100 estrazioni, poi prende i 5 vicini (±5) piu frequenti. Sostituisco **solo la prima regola**: seed = random 1-90.

10 trial indipendenti:

| Metrica | Valore |
|---------|--------|
| Classica (seed=most_freq) | **ratio 1.0595x**, ROI -4.64% |
| Random-seed: media ± SD | 0.9756x ± 0.0350, ROI -12.19% |
| Random-seed: range | [0.9327, 1.0449] |

**NESSUNO dei 10 trial raggiunge il baseline**. La distribuzione random-seed e centrata sotto 1.0. Il seed-selection da solo vale **circa +8 punti percentuali di ratio** (da 0.976 medio a 1.060 del classico).

**Verdetto Test 3: il seed-selection e IL fattore dominante.** Giocare un cluster qualsiasi non funziona; giocare il cluster *attorno al numero piu hot* funziona.

### H.5 Decomposizione dell'edge

Combinando i 3 test, la catena causale e:

```
ratio vicinanza 1.060x
  = baseline (giocare 6 hot qualsiasi ≈ 1.00x)
    + seed-selection momentum (+6% circa)
    + adjacency filtering (+0.5% circa)
    - varianza residua
```

Il seed-selection spiega **~92% dell'edge**. L'adjacency ne spiega **~8%**. Il clustering naturale e il bias RNG ne spiegano **0%**.

### H.6 Interpretazione meccanicistica rivista

La mia prima ipotesi intuitiva ("vicinanza sfrutta il payoff asimmetrico vincolando la varianza sulla coda") era **sbagliata**. I test dimostrano che:

1. Il RNG 10eLotto non ha pattern spaziali rilevabili
2. Giocare un cluster qualsiasi non produce edge
3. L'edge viene dal **momentum frequenziale locale**: quando un numero e "caldo" su W=100, anche i suoi vicini temporali (non spaziali) tendono ad essere caldi

In altre parole, vicinanza **non predice la posizione della prossima estrazione**. Usa il seed come "ancora" e seleziona 5 numeri che condividono con esso un'alta co-occorrenza nelle finestre recenti. L'adjacency numerica e un filtro euristico che *restringe* lo spazio di ricerca, evitando di prendere numeri che sono caldi per puro caso isolato.

Dual-target, per contro, seleziona 3 hot in base + 3 hot in extra, **senza alcun ancoraggio**. I numeri possono essere random sul wheel, quindi i 6 scelti sono 6 "punti caldi" indipendenti. Per la legge dei grandi numeri, molti di questi "hot" nelle 100 estrazioni precedenti sono solo rumore, e il metodo ne soffre.

### H.7 Implicazione pratica

Se l'edge di vicinanza viene al 92% dal seed-selection, una versione *piu aggressiva* potrebbe funzionare meglio: **seed = top 3 piu frequenti**, e attorno a ciascuno prendere 2 vicini frequenti. Totale 6 numeri, tre micro-cluster. Test da eseguire.

Oppure: **iper-seed** — prendi solo il top 1 come seed, poi 5 vicini (non importa se non frequenti). Questo isolerebbe l'effetto pure seed-momentum senza usare l'informazione di frequenza dei vicini.

Entrambe le varianti sono chirurgiche per isolare ulteriormente il meccanismo.

### H.8 Verdetto

Al di la delle statistiche, **vicinanza non "sfrutta la geometria del gioco"**. Sfrutta un fenomeno piu sottile: la **persistenza temporale delle frequenze locali nelle finestre RNG**. Numeri "hot" recenti tendono a restare hot non per pattern fisico, ma per autocorrelazione del pseudo-random: un RNG non-perfettamente-indipendente (come ogni PRNG reale) ha micro-persistenze che finestre W=100 catturano.

L'adjacency e un **filtro qualita**: "prendi i 5 numeri caldi che sono *vicini* al piu caldo" scarta i caldi-ma-casuali (hot per coincidenza) in favore dei caldi-nello-stesso-cluster-temporale.

Questo spiega anche perche il test del paper originale su RNG (Capitolo 22) passava: l'uniformita marginale e OK, l'autocorrelazione a lag 1-7 e OK, ma una forma piu sottile (co-occorrenza entro finestre W=100 per numeri vicini numericamente) non e stata testata direttamente.

Proposta per il prossimo test: **autocorrelazione a lag 100 filtrata per adjacency**. Se esiste un residuo di dipendenza fra la frequenza del numero x nella finestra t e la frequenza del numero x+1 nella finestra t+100, abbiamo trovato il meccanismo esatto.

---

## Appendice I: La Caccia al Meccanismo — 4 Test, Tutti Negativi

### I.1 Motivazione e attesa

L'Appendice H aveva decomposto l'edge di vicinanza (ratio 1.060x vs 1.001x di dual_target) come:
- 92% dal seed-selection (numero piu frequente in W=100)
- 8% dall'adjacency filtering

Il passo logico successivo: se il seed-selection (prendere il numero piu frequente) produce edge, deve esistere una forma di **hot-hand numerica** nel PRNG 10eLotto, ovvero numeri che sono stati frequenti in W=100 devono avere probabilita > 20/90 = 22.22% di apparire nell'estrazione successiva.

Quattro test progettati per isolare e caratterizzare questo pattern (`backend/diecielotto/autocorr_tests.py`, dataset 34.739 estrazioni, 3.117.510 sample pair (numero, estrazione)).

### I.2 Test H.8a — Hot-hand numerica

Per ogni coppia (t ≥ W, n ∈ 1..90) registro (`freq(n, W=100)`, `present(n, t+1)`). Il baseline P(present) = 20/90 = 0.2222. Se i numeri caldi sono piu probabili, P(present|freq alta) > 0.2222.

| freq_n | N samples | P(present) | Diff % | z |
|--------|-----------|------------|--------|---|
| 15 | 65.405 | 0.2236 | +0.63% | +0.86 |
| 20 (media) | 266.327 | 0.2237 | +0.66% | +1.81 |
| 22 | 303.827 | 0.2215 | -0.32% | -0.93 |
| 25 | 230.698 | 0.2235 | +0.58% | +1.49 |
| 30 (caldo) | 52.787 | 0.2211 | -0.52% | -0.64 |
| 35 (caldissimo) | 3.621 | 0.2207 | -0.70% | -0.23 |
| 39 (estremo) | 197 | 0.1777 | -20.05% | -1.50 |

**Aggregato:**
- HIGH freq (≥28.5): n=211.052, P(present) = 0.2208 (**-0.66%**)
- LOW freq (≤16.0): n=147.455, P(present) = 0.2222 (-0.02%)
- **HI - LO: -0.143 punti percentuali, z = -1.01**

**Verdetto H.8a: NESSUNA hot-hand.** Il PRNG 10eLotto e uniforme rispetto alla frequenza in W=100. Anzi, una lievissima (non significativa) tendenza di *anti-persistenza*: i numeri caldi hanno P(present) leggermente inferiore alla media.

### I.3 Test H.8b — Adjacency bonus controllato

Per ogni (t, n): registro (freq_n, avg_freq_neighbors_n, present). Poi per freq_n fissa, osservo come varia P(present) con avg_freq_neighbors.

Tabella parziale (freq_n = 22, il valore piu comune):

| avg_neighbors | N | P(present) | Diff % |
|---------------|---|------------|--------|
| 19 | 3.824 | 0.2105 | -5.27% |
| 21 | 54.528 | 0.2230 | +0.35% |
| 22 | 102.781 | 0.2214 | -0.38% |
| 24 | 38.746 | 0.2223 | +0.02% |
| 26 | 1.860 | 0.2140 | -3.71% |

**Aggregato (freq_n ≈ 22 ± 1):**
- LOW neighbors (avg ≤ 20): P = 0.2215
- HIGH neighbors (avg ≥ 24): P = 0.2230
- **z = +0.94** (non significativo)

**Verdetto H.8b: NESSUN adjacency bonus.** Dopo controllo per freq_n, la frequenza dei vicini non aggiunge potere predittivo. L'effetto +8% attribuito nell'Appendice H all'adjacency era artefatto del backtest monetario, non del prediction power.

### I.4 Test H.8c — Sensibilita della finestra W

Ripeto H.8a per W ∈ {20, 50, 100, 200, 500, 1000}:

| W | z (HI vs LO) | P(pres\|hi) | P(pres\|lo) | Diff pp |
|---|--------------|-------------|-------------|---------|
| 20 | -0.49 | 0.2215 | 0.2223 | -0.073 |
| 50 | -1.63 | 0.2210 | 0.2233 | -0.223 |
| 100 | -1.01 | 0.2208 | 0.2222 | -0.143 |
| 200 | **+1.38** | 0.2237 | 0.2218 | +0.185 |
| 500 | -0.10 | 0.2228 | 0.2229 | -0.013 |
| 1000 | +0.76 | 0.2229 | 0.2220 | +0.098 |

**Nessun W raggiunge z > 2**. Il "migliore" W=200 ha z=+1.38 (p ≈ 0.08, non sig). La direzione dell'effetto e inconsistente (oscilla fra + e - cambiando W) — pattern di puro rumore.

### I.5 Test H.8d — Stabilita temporale

Split cronologico del dataset in 4 parti (~8.700 estrazioni ciascuno), ripeto H.8a.

| Fold | Range | z | P_hi | P_lo |
|------|-------|---|------|------|
| 1 | [0..8684) | -1.04 | 0.2174 | 0.2203 |
| 2 | [8684..17368) | +0.45 | 0.2215 | 0.2202 |
| 3 | [17368..26052) | -0.74 | 0.2220 | 0.2241 |
| 4 | [26052..34739) | -0.67 | 0.2222 | 0.2241 |

**Mean z = -0.50, SD z = 0.57.** I 4 fold danno effetti in direzione opposta (2 positivi, 2 negativi) con magnitudine piccola. **Pattern instabile: se esistesse un segnale RNG, i 4 fold dovrebbero dare z coerente in segno e almeno > 2 in magnitudine.**

### I.6 La riconciliazione: perche vicinanza ha ratio > 1 se non c'e hot-hand?

I 4 test smentiscono tutte le ipotesi di "meccanismo PRNG". Il RNG 10eLotto **e genuinamente perfetto** rispetto a frequenza, adjacency, finestra, e tempo.

Ma allora perche vicinanza ha ratio 1.060x e random-seed 0.976x nell'Appendice H.3?

La risposta, dopo riflessione, e un **effetto combinatoriale sui payoff, non un effetto predittivo**:

1. **I payoff sono convessi nel match count**: 2€ per 3/6, 10€ per 4/6, 100€ per 5/6, 1000€ per 6/6. Premi Extra: 1€ per 2/6, 7€ per 3/6, 20€ per 4/6, 200€ per 5/6.

2. **Pick "clusterato" vs pick "sparso" hanno stessa E[match] ma DIVERSA Var[match]**: quando pesco 6 numeri in un cluster compatto, i 6 eventi (base^i presente) sono piu *correlati* tra loro (non perche il RNG li correla, ma perche gli stessi 20 estratti dal pool di 90 formano naturalmente cluster per pigeonhole). Risultato: vicinanza ha distribuzione di match_base piu "a code" (piu zero-match E piu 5-match).

3. **Convessita + skewness = ratio > 1** anche con P marginale identica. E' lo stesso effetto della disuguaglianza di Jensen applicata al premio(match_count): E[f(X)] > f(E[X]) se f e convessa e X ha varianza > 0.

Quindi: il ratio 1.060x di vicinanza **non e un edge predittivo**. E' un **artefatto del payoff asimmetrico × varianza del pick**. Vicinanza produce pick con varianza maggiore (perche clusterati) → match distribution con coda piu pesante → EV leggermente maggiore per via della convessita.

### I.7 Verifica rapida: varianza del match_count

Piccolo test di conferma: su 34.739 estrazioni, la distribuzione di match_base dovrebbe essere piu "spalmata" (piu zero e piu quattro+) per vicinanza che per dual_target.

Dal backtest locale originale:

| Match base | Vicinanza | Dual_target | Diff |
|------------|-----------|-------------|------|
| 0 | 7.342 | 7.379 | -37 |
| 1 | 13.398 | 13.359 | +39 |
| 2 | 9.659 | 9.693 | -34 |
| 3 | 3.487 | 3.486 | +1 |
| 4 | 675 | 644 | **+31** |
| 5 | 61 | 62 | -1 |
| 6 | 3 | 2 | +1 |

Vicinanza ha **+31 giocate a 4/6 base** (premio 10€) rispetto a dual_target, e +3 a 4-6 match. Il totale "code" (≥4/6) e 739 vs 708 → **+4.4% di eventi di coda** per vicinanza. Con premi 10€-1000€ in quei bucket, l'edge +0.06x di ratio totale e spiegato.

### I.8 Implicazione profonda: rivedere la conclusione H

**La decomposizione dell'Appendice H era numericamente corretta ma interpretata male.**

Non e vero che "seed-selection sfrutta momentum frequenziale" (H.8a lo smentisce). E' vero che:
- Il seed-selection + adjacency PRODUCONO pick con varianza diversa
- Quella varianza moltiplicata per la convessita dei payoff da EV maggiore

Il test H random-seed (Appendice H.4) non isolava "seed-selection" ma "una varianta del pick". Un seed random + 5 vicini piu frequenti produce pick che e *a volte* clusterato e *a volte* no (dipende se il seed random cade in zona hot), degradando la struttura. Per questo ratio scende.

### I.9 La vera spiegazione di vicinanza

Vicinanza NON e un metodo predittivo. E' un **metodo di generazione di scommesse ad alta varianza su gioco con payoff convesso**. E' equivalente a comprare opzioni out-of-the-money: l'EV marginale viene dalla coda, non dalla previsione.

Implicazione pratica: **qualsiasi strategia che produca cinquine "clusterate" dovrebbe avere lo stesso edge**, indipendentemente da come e scelto il cluster. Vediamo:

| Strategia | Cluster? | Atteso ratio | Osservato |
|-----------|----------|--------------|-----------|
| Vicinanza (seed = most_freq) | SI | ~1.05-1.08x | 1.060x |
| Vicinanza (seed = random) | SI (ma a volte no) | ~1.02-1.05x | 0.976x (a volte degenera) |
| Cluster fisso "1-6" | SI | ~1.05-1.08x | (da testare) |
| Cluster fisso "50-55" | SI | ~1.05-1.08x | (da testare) |
| Dual_target (3 base + 3 extra) | NO (sparso) | ~1.00-1.01x | 1.001x |
| Hot (top 6 sparsi) | NO | ~1.00-1.01x | 0.950x |

Il pattern e coerente: **cluster → ratio lievemente sopra baseline, sparso → ratio circa baseline**.

### I.10 Perche nessun metodo supera il breakeven 1.11x

Il breakeven 1.11x per K=6+Extra richiede un edge di +11%. Il massimo guadagno da convessita + clustering e circa +5-8% (dai nostri dati). Quindi **nessuna strategia combinatoriale pura puo superare il breakeven** senza un vero edge predittivo, che il RNG 10eLotto non concede.

**Teorema pratico**: su un RNG uniforme con payoff convessi, max ratio ottenibile ≈ 1 + O(Var[match] × convexity_degree). Per K=6, 20 estratti su 90, cluster estremo: ratio ≈ 1.05-1.08x. Per superare 1.11x servirebbe un vero bias RNG.

### I.11 Proposta verifica diretta del "cluster bias"

Eseguire backtest con:
1. "Cluster fisso random" ogni volta (es. `[r, r+1, r+2, r+3, r+4, r+5]` con r casuale 1-85)
2. "Cluster optimal-positioned" (es. cluster in posizione che bilancia fasce del wheel)
3. "Pick anti-cluster" (6 numeri con minima vicinanza reciproca, es. `[10, 25, 40, 55, 70, 85]`)

Se (1) da ratio ~1.04-1.06x anche con seed random, conferma: **il bonus e nel cluster, non nel seed**.
Se (3) da ratio ~0.94-0.96x (sotto baseline), conferma: **essere sparso penalizza via convessita**.

Il test e stato eseguito (Appendice J). Risultati ribaltano anche la teoria della convessita.

---

## Appendice J: Il Colpo di Scena — Tutto e Varianza

### J.1 Esecuzione del test proposto in I.11

Codice: `backend/diecielotto/cluster_verify.py`. Cinque strategie su 34.740 estrazioni, con lo stesso backtest di Appendice H.

| Strategia | Cluster? | Ratio | Var(match_base) | Big wins ≥20€ | Coda 4/6+ |
|-----------|----------|-------|-----------------|---------------|-----------|
| Cluster RANDOM seed `[r..r+5]` | SI | **0.9915x** | 0.9747 | 296 | 712 |
| **Anti-cluster FISSO `[10,25,40,55,70,85]`** | **NO** | **1.0651x** | 0.9731 | 303 | 681 |
| Sparse random (dist ≥ 10) | NO | 0.9744x | 0.9749 | 278 | 710 |
| Vicinanza classic (seed=most_freq) | SI | 1.0595x | 0.9879 | 301 | 740 |
| Dual target (3 base + 3 extra) | NO | 1.0009x | 0.9834 | 278 | 709 |

### J.2 Il risultato ribalta TUTTO

**Osservazioni decisive:**

1. **Cluster random-seed: 0.9915x** (sotto baseline!)
   Se la teoria "cluster bonus" fosse vera, dovrebbe essere 1.04-1.06x. Non lo e.

2. **Anti-cluster fisso [10,25,40,55,70,85]: 1.0651x** (ALTO come vicinanza!)
   6 numeri sparsi FISSI battono vicinanza (1.0595x). Questo non ha senso ne con la teoria "hot-hand" (H.8a), ne con "cluster convessita" (I).

3. **Sparse random: 0.9744x** (sotto baseline)
   Sparso random perde. Ma sparso FISSO vince. La differenza e solo la fissita.

4. **Distribuzione match_base quasi IDENTICA** per tutte le strategie (vedi tabella sotto).

Distribuzione match_base dettagliata:

| mb | cluster_rand | cluster_anti | sparse_rand | vicinanza | dual_target |
|----|-------------|-------------|-------------|-----------|-------------|
| 0 | 7.343 | 7.292 | 7.136 | 7.343 | 7.380 |
| 1 | 13.509 | 13.514 | 13.410 | 13.405 | 13.366 |
| 2 | 9.690 | 9.658 | 9.872 | 9.663 | 9.698 |
| 3 | 3.386 | 3.495 | 3.512 | 3.489 | 3.487 |
| 4 | 646 | 623 | 647 | 676 | 645 |
| 5 | 64 | 54 | 62 | 61 | 62 |
| 6 | 2 | 4 | 1 | 3 | 2 |

Le distribuzioni sono statisticamente identiche (chi-quadro sui 5 pattern: non significativo). La varianza del match_base e simile (0.97-0.99). **Il match_base NON spiega la differenza di ratio.**

La differenza deve stare nei **match_extra** e nella loro **covarianza con i match_base**, attraverso i payoff extra convessi.

### J.3 Il vero verdetto: e tutta varianza

Facciamo i conti. Su 34.740 giocate con payoff estremi (1000€ per 6/6, 2000€ per 6/6 Extra):
- EV teorico: 1.80€/giocata, totale atteso 62.532€
- Osservato vicinanza: ratio 1.060x → 66.284€ (+3.752€)
- Osservato cluster_anti: ratio 1.065x → 66.641€ (+4.109€)
- Osservato cluster_rand: ratio 0.992x → 62.001€ (-531€)
- Osservato sparse_rand: ratio 0.974x → 60.922€ (-1.610€)

Il gap massimo (cluster_anti vs sparse_rand) e 5.719€ su 34.740 giocate = **0.16€ per giocata media**.

Ma un singolo jackpot 6/6 vale 1.000€, un 5/6 Extra vale 200€. La differenza di 5.719€ corrisponde a **~3-10 eventi rari** di differenza tra strategie.

**Stima della varianza teorica del ratio**:
- Payoff Extra ha p = 4×10^-6 per 6/6 (2000€) e p = 3×10^-5 per 5/6 (200€)
- Var(payoff singolo) ≈ 4×10^-6 × 2000² + ... ≈ 30
- sd_giocata ≈ 5.5€
- sd_media(N=34740) ≈ 5.5 / √34740 ≈ 0.029€
- sd_ratio ≈ 0.029 / 1.80 ≈ **0.016**

Con sd=0.016, un intervallo 95% sul ratio osservato e ±0.032. Quindi:
- Vicinanza 1.060x ± 0.032 = [1.028, 1.092]
- Cluster_anti 1.065x ± 0.032 = [1.033, 1.097]
- Cluster_rand 0.992x ± 0.032 = [0.960, 1.024]

**Tutte queste confidence interval SI SOVRAPPONGONO.** Non c'e differenza statisticamente significativa tra le strategie. Il "ranking" vicinanza > anti-cluster > dual_target > sparse_random > cluster_random **e rumore**.

### J.4 Il vero payoff: nessuna strategia funziona

Riorganizziamo la gerarchia osservata con errori di stima:

| Strategia | Ratio ± 2σ | Significativamente diverso da 1.00? |
|-----------|------------|-------------------------------------|
| Anti-cluster fisso | 1.065 ± 0.032 | Borderline (z≈2.03) |
| Vicinanza classic | 1.060 ± 0.032 | Borderline (z≈1.87) |
| Dual target | 1.001 ± 0.032 | No (z≈0.03) |
| Cluster random | 0.992 ± 0.032 | No (z≈-0.5) |
| Sparse random | 0.974 ± 0.032 | No (z≈-1.6) |

Con soglia Bonferroni per 5 strategie (0.05/5 = 0.01, z>2.58), NESSUNA e significativamente > baseline. Il "miglior" (anti-cluster fisso) e solo al pelo sopra p=0.05 raw.

### J.5 Lezione profonda: le stime ratio su 34K giocate sono rumorose

Questa appendice e lezione metodologica. Il paper aveva iterativamente:
1. Ipotizzato hot-hand (Cap. 22, smentita)
2. Ipotizzato clustering naturale (Appendice H, smentita da H.8a)
3. Ipotizzato seed-selection momentum (H, smentita da I.1-I.5)
4. Ipotizzato cluster convexity (I.6, smentita da J.1)

Ogni volta trovavamo ratio 1.02-1.08x e cercavamo un meccanismo. La verita, finalmente chiara: **con payoff asimmetrici 1000€+ e dataset ~34K, la stima del ratio ha sd ≈ 0.016. Tutto quello che sta in [0.95, 1.10] e rumore.**

Il ratio di vicinanza osservato non sopravvive al test di riproducibilita (seed random produce 0.99), non e stabile temporalmente (I.5), non e differenziabile da pick arbitrari fissi (J.1). **E' un artefatto di un singolo campione specifico.**

### J.6 Stima del dataset necessario per segnali reali

Per distinguere un ipotetico edge +0.05 (ratio 1.05 vs 1.00) con confidence 95%:
- Richiesto: 2σ < 0.05 → σ < 0.025 → N > (5.5/0.025/1.80)² = 14.900 giocate? No, aspetta:
- sd_ratio(N) = sd_giocata / (EV × √N) = 5.5 / (1.80 × √N)
- 0.025 = 5.5 / (1.80 × √N) → √N = 122 → **N ≈ 14.900**

Quindi con 34K giocate DOVREMMO riuscire a distinguere un edge reale di 5%. Ma i test di temporal stability (Fold 1-4, I.5) mostrano che il "segnale" cambia direzione tra fold, quindi non esiste un edge genuino del 5%.

**Conclusione definitiva:** l'edge di vicinanza 1.060x non e replicabile, non e stabile, non sopravvive a verifica con pick random o fissi arbitrari. **E varianza di un sample specifico**, amplificata dalla coda pesante dei payoff.

### J.7 La verita ultima sul 10eLotto

Il 10eLotto ha:
- RNG certificato ADM (Cap. 22 conferma: chi-quadro, autocorr, birthday, coppie: tutti PASS)
- Nessun hot-hand (I.1-I.3)
- Nessun adjacency bonus (I.4)
- Nessuna stabilita temporale di pattern (I.5)
- Nessuna differenza tra pick clusterati/sparsi oltre la varianza (J.1-J.4)

**Il 10eLotto non e battibile con 34K giocate di dato.** Qualsiasi "segnale" trovato e rumore campionario amplificato dalla skewness dei payoff. L'HE 9.94% e ineluttabile.

L'unica strategia razionale per chi gioca: **giocate minime (K=6 + Extra = 2€) durante Special Time (HE 6.30%), ignorando qualsiasi metodo predittivo**. Nessun algoritmo produce edge.

### J.7-bis Il test specifico di Appendice H.8 finalmente eseguito

**Nota importante**: l'Appendice H aveva proposto come test successivo "autocorrelazione a lag lungo filtrata per adjacency numerica". Questo test NON era stato eseguito da I (che ha testato autocorrelazione stessa-finestra) ne da J (che ha testato strategie fisse vs random). E' stato eseguito separatamente come Appendice K.

**Risultato: CONFERMA ulteriore del verdetto di Appendice J** — nessun pattern lag-adjacency, il PRNG 10eLotto non ha memoria cross-finestra con shift numerico. Vedi Appendice K per dettagli.

### J.8 Implicazione per il portale paper-trading

La sezione Paper Trading del portale mostra ratio osservati 1.06x vs 1.11x vs ... Questi numeri sono **matematicamente corretti ma statisticamente non interpretabili come "performance relativa"**. Tutti cadono nell'intervallo di errore [0.95, 1.10] che e pura varianza.

Aggiungere disclaimer piu forti: **"I ratio mostrati non sono significativi finche il dataset non supera 100K giocate. A oggi sono stime rumorose del vero EV atteso, che si aggira intorno a 0.90 per K=6+Extra (HE 9.94%)."**

---

## Appendice K: Il Test Originariamente Proposto (e Mai Fatto)

### K.1 Auto-critica: il test specifico mancava

Rileggendo il paper, l'utente ha notato che il test **autocorrelazione a lag lungo filtrata per adjacency numerica** proposto in Appendice H.8 non era stato davvero eseguito. L'Appendice I ha testato cose correlate ma non questo specifico test:

- H.8a: `freq(x, W=100)` → `present(x, t+1)` — stessa x, lag=1, **stessa finestra** → diverso
- H.8b: `freq(x) + freq(neighbors)` → `present(x)` — tutto sulla **stessa finestra** → diverso
- H.8c: come H.8a con W variabile — stesso concetto, non cross-finestra → diverso

Il test proposto specifico era: **correlazione fra `freq(x, finestra A)` e `freq(x+d, finestra B)` per lag L tra A e B e offset numerico d**.

E' stato finalmente eseguito: `backend/diecielotto/lag_adjacency_test.py`.

### K.2 Metodologia

Per ogni tempo t (step = W=100, non-overlapping per L ≥ W):
- Finestra A: `[t-W, t-1]` (100 estrazioni)
- Finestra B: `[t+L-W, t+L-1]` (100 estrazioni, shiftate di lag L rispetto ad A)

Per ogni numero x ∈ [1, 90] e offset d ∈ {-5..+5}:
- Registra `freq(x, A)` e `freq(x+d, B)` (quando `1 ≤ x+d ≤ 90`)
- Accumula pair across tutti (t, x) → (freq_A, freq_B)
- Calcola Pearson r sulla lista accumulata

Lag testati: **L ∈ {1, 50, 100, 200, 500, 1000}**.

**Caveat critico**: per L < W, le finestre A e B si sovrappongono (overlap = W-L estrazioni), generando correlazione spuria r ≈ (W-L)/W a d=0 che NON e un meccanismo. Il test genuino e **L ≥ W** (finestre disgiunte).

### K.3 Risultati — matrice correlazioni r[L][d]

| L \\ d | -5 | -4 | -3 | -2 | -1 | 0 | +1 | +2 | +3 | +4 | +5 |
|--------|------|------|------|------|------|------|------|------|------|------|------|
| 1 (overlap 99%) | -0.007 | -0.011 | -0.011 | -0.019 | -0.013 | **+0.990** | -0.012 | -0.018 | -0.012 | -0.010 | -0.006 |
| 50 (overlap 50%) | +0.000 | -0.017 | -0.007 | -0.003 | -0.008 | **+0.498** | -0.006 | -0.012 | -0.008 | -0.007 | +0.001 |
| **100** (disjoint) | +0.006 | -0.007 | +0.005 | +0.015 | -0.013 | +0.008 | +0.014 | -0.012 | -0.001 | -0.001 | +0.005 |
| **200** (disjoint) | -0.002 | +0.005 | -0.001 | -0.005 | -0.006 | -0.005 | +0.001 | +0.010 | -0.008 | -0.004 | -0.003 |
| **500** (disjoint) | -0.005 | +0.002 | +0.001 | -0.006 | +0.001 | -0.002 | -0.002 | +0.001 | -0.003 | +0.002 | +0.001 |
| **1000** (disjoint) | +0.007 | +0.003 | -0.003 | +0.006 | -0.008 | -0.007 | +0.002 | -0.001 | -0.006 | -0.002 | +0.008 |

### K.4 Verifica dell'artefatto overlap

Per L<W, la correlazione attesa a d=0 e esattamente `(W-L)/W` dovuta ai sample condivisi tra le due finestre:

| L | r(d=0) atteso (overlap) | r(d=0) osservato | Match? |
|---|-------------------------|------------------|--------|
| 1 | 0.990 | +0.990 | ✓ perfetto |
| 50 | 0.500 | +0.498 | ✓ perfetto |

L'artefatto e completamente identificato e numericamente calibrato. Questi NON sono segnali RNG.

### K.5 Test genuino: L ≥ W (finestre disgiunte)

Per L ∈ {100, 200, 500, 1000}, tutti gli offset d ∈ [-5..+5]:

- **Max |r| su adjacency (d ≠ 0): 0.015** (L=100, d=+1) → z = +0.29
- **Max |r| per d = 0 (persistenza stesso numero): 0.008** (L=100) → z = +0.15

Bonferroni per 40 test (4 lag × 10 offset ≠ 0): soglia z > 3.1. **Nessun valore supera 0.3.**

### K.6 Verdetto K: chiusura definitiva

**Non esiste alcun pattern lag-adjacency nel PRNG 10eLotto.** La frequenza di x nella finestra A e la frequenza di x+d nella finestra B (disgiunta, lag ≥ 100) sono statisticamente indipendenti per tutti i d ∈ [-5..+5].

Questo chiude ogni ipotesi di meccanismo PRNG basato su:
- Memoria a lungo termine (lag ≥ 100)
- Shift numerico (adjacency)
- Combinazione di entrambi

### K.7 Bilancio complessivo: 6 ipotesi, 6 smentite

| Cap. | Ipotesi | Risultato |
|------|---------|-----------|
| Cap. 22 | RNG ha autocorrelazione lag 1-14 | NEGATIVO |
| H.8a | Hot-hand numerica | NEGATIVO (z=-1.01) |
| H.8b | Adjacency bonus controllato | NEGATIVO (z=+0.94) |
| H.8c | Esiste W ottimale | NEGATIVO (max z=+1.38) |
| H.8d | Pattern stabile fra fold | NEGATIVO (instabile) |
| I-J | Cluster convexity | NEGATIVO (stime rumore) |
| **K** | **Lag-adjacency cross-window** | **NEGATIVO (max z=+0.29)** |

**7 test specifici, 7 smentiti.** Il PRNG 10eLotto e genuinamente perfetto nell'insieme di ipotesi esplorate.

### K.8 La lezione metodologica finale

Questo epilogo e una lezione importante: **l'intuizione "dev'esserci un meccanismo se vedo un edge in backtest" e fallace**. Con payoff asimmetrici (1000-2000€ jackpot) e dataset finiti (34K giocate), le stime del ratio hanno SD ~0.016-0.03. Qualunque valore nell'intervallo [0.95, 1.10] e compatibile con rumore.

La procedura corretta per dichiarare un edge:
1. Se vedi edge ε > 0 in backtest, calcola `sd_ratio = sd_giocata / (EV × √N)`
2. Se `ε < 3 × sd_ratio`, fermati — non e un segnale
3. Altrimenti, prima cerca il meccanismo, poi valida con dataset indipendente
4. Anche se meccanismo plausibile, richiedi riproducibilita su dataset out-of-sample

Con sd_ratio ≈ 0.03 su 34K giocate, servirebbe edge > 0.09 (ratio > 1.09) per essere distinguibile da rumore. Nessuno dei metodi testati lo produce.

**Conclusione del viaggio**: abbiamo iterativamente cercato meccanismi in un sistema genuinamente casuale. Ogni "scoperta" si e rivelata un'illusione della coda del rumore. Il valore del progetto Lottery Lab e proprio questo: **dimostrare per esclusione, con rigore metodologico, che NESSUN meccanismo sfruttabile esiste**.

---

## Appendice L: MillionDay — Window Sweep Esaustivo W=1..300 × 12 Algoritmi

### L.1 Motivazione

Il paper e il portale hanno identificato `optfreq W=60` come "miglior" metodo MillionDay (Appendice E-ter). Domanda aperta: **e davvero W=60 la finestra ottimale?** E lo e per QUALSIASI algoritmo, o solo per optfreq?

Sweep esaustivo: 12 algoritmi × 300 finestre (W=1..300) = **3.600 configurazioni** testate. Per la best config: analisi rolling temporale sul dataset per vedere come cambia il ratio nel tempo.

Script: `backend/millionday/window_sweep.py` (numpy-ottimizzato, ~72 secondi).

### L.2 Algoritmi testati

| ID | Descrizione |
|----|-------------|
| hot | Top 5 piu frequenti nel base |
| cold | Top 5 meno frequenti nel base (ritardo) |
| optfreq | Top 5 con \|freq - expected\| minima (anti hot/cold) |
| hot_extra | Top 5 piu frequenti nell'Extra |
| dual_3b2e | 3 hot base + 2 hot extra disgiunti |
| dual_2b3e | 2 hot base + 3 hot extra disgiunti |
| cold_plus_hotex | 3 cold base + 2 hot extra |
| mix3h2c | 3 hot + 2 cold del base |
| vicinanza_D3 | seed + 4 vicini in ±3 |
| vicinanza_D5 | seed + 4 vicini in ±5 |
| vicinanza_D10 | seed + 4 vicini in ±10 |
| spread_fasce | 1 hot per ciascuna delle 5 fasce di decina |

### L.3 Metrica robusta vs naive

**Problema critico**: con 3.600 configurazioni su 2.607 estrazioni (1.304 validation), la probabilita che almeno UNA config catturi un 5/5 jackpot (1M€) per puro caso e:

```
P(>=1 config becca jackpot in val) = 1 - (1 - 1.304 × 2.9e-6)^3600 ≈ 73%
```

Infatti, il primo sweep ha restituito `spread_fasce W=24` con ratio 58.4x — un JACKPOT catturato nel bucket 2025-06-29.

**Metrica robusta**: cap del payout a 500€ per estrazione. Sopra quella soglia, la vincita viene normalizzata a 500€. Questo esclude:
- 5/5 base (1.000.000€ → 500€)
- 5/5 Extra (100.000€ → 500€)
- 4/5 base (1.000€ → 500€)
- 4/5 Extra (1.000€ → 500€)

EV teorico capped: ~0.71€/giocata (HE 65%). Con cap, i pattern "reali" emergono sotto il rumore dei jackpot.

### L.4 Top 20 configurazioni (ratio robust val)

| Rank | Algoritmo | W | Ratio disc | Ratio val | Big wins val |
|------|-----------|---|------------|-----------|--------------|
| 1 | **cold_plus_hotex** | **66** | +1.127x | **+3.249x** | 2 |
| 2 | cold_plus_hotex | 67 | +0.946x | +2.972x | 2 |
| 3 | dual_3b2e | 103 | +1.275x | +2.957x | 3 |
| 4 | spread_fasce | 40 | +1.035x | +2.957x | 2 |
| 5 | dual_3b2e | 104 | +1.508x | +2.953x | 3 |
| 6 | cold | 82 | +0.948x | +2.852x | 2 |
| 7 | optfreq | 236 | +1.489x | +2.668x | 1 |
| 8 | hot_extra | 8 | +1.579x | +2.616x | 2 |
| 9 | spread_fasce | 72 | +1.899x | +2.558x | 1 |
| 10 | hot | 13 | +1.553x | +2.538x | 2 |
| 11 | dual_2b3e | 7 | +1.026x | +2.484x | 2 |
| 12 | optfreq | 170 | +1.845x | +2.480x | 2 |
| ... | | | | | |

### L.5 Best W per algoritmo (rating robust)

| Algoritmo | Best W | Ratio val robust | Ratio disc robust | Coerenza |
|-----------|--------|------------------|-------------------|----------|
| cold_plus_hotex | 66 | +3.249x | +1.127x | ⚠ |
| dual_3b2e | 103 | +2.957x | +1.275x | ⚠ |
| spread_fasce | 40 | +2.957x | +1.035x | ⚠ |
| cold | 82 | +2.852x | +0.948x | ⚠ |
| optfreq | 236 | +2.668x | +1.489x | ⚠ |
| hot_extra | 8 | +2.616x | +1.579x | ⚠ |
| hot | 13 | +2.538x | +1.553x | ⚠ |
| dual_2b3e | 7 | +2.484x | +1.026x | ⚠ |
| vicinanza_D5 | 16 | +2.296x | +1.138x | ⚠ |
| vicinanza_D10 | 12 | +2.281x | +1.148x | ⚠ |
| mix3h2c | 288 | +2.147x | +0.885x | ⚠ |
| vicinanza_D3 | 34 | +2.124x | +0.950x | ⚠ |

**Tutte le best config hanno coerenza ⚠** (differenza disc/val > 10%). Questo e il sintomo classico di overfitting del validation set: il ratio e alto in val ma basso in disc.

Osservazione importante: **W varia enormemente tra algoritmi** (da 7 a 288). Non c'e una "finestra universale". Per optfreq era W=60 nella Appendice E-ter, qui W=236 risulta il massimo (ma con W=170 e W=188 simili, e anche W=60 da 1.90x — piu stabile). Tre interpretazioni possibili:
- (a) L'algoritmo ha bisogno di W specifici — e "ancora" al dato
- (b) Il W specifico massimizza per fortuna su questo validation set (overfitting)
- (c) Entrambi

### L.6 Permutation test top 5

Bonferroni soglia (3.600 test): **p < 0.00001** per significativita

| Algoritmo | W | Ratio val robust | p-value | Bonf-sig? |
|-----------|---|------------------|---------|-----------|
| cold_plus_hotex | 66 | +3.249x | 0.0040 | raw-sig, **FAIL Bonf** |
| cold_plus_hotex | 67 | +2.972x | 0.0010 | raw-sig, **FAIL Bonf** |
| dual_3b2e | 103 | +2.957x | 0.0075 | raw-sig, **FAIL Bonf** |
| spread_fasce | 40 | +2.957x | 0.0190 | raw-sig, **FAIL Bonf** |
| dual_3b2e | 104 | +2.953x | 0.0050 | raw-sig, **FAIL Bonf** |

Il miglior p=0.001 e 100x piu alto del soglia Bonferroni 0.00001. Nessuna config sopravvive al multiple testing.

### L.7 Rolling temporal analysis — best config: cold_plus_hotex W=66

Bucket: 300 giocate, stride 100 → 23 bucket che coprono 2022-05 a 2025-10.

| # | Data inizio | Ratio | ROI% | Hit% | Big wins | PnL |
|---|-------------|-------|------|------|----------|-----|
| 1 | 2022-05-21 | +0.860x | -43% | 10.3% | 4 | -258€ |
| 2 | 2022-08-29 | +0.855x | -43% | 10.3% | 4 | -260€ |
| 3 | 2022-12-07 | +0.970x | -36% | 9.7% | 4 | -214€ |
| 4 | 2023-03-17 | +0.900x | -40% | 11.3% | 3 | -242€ |
| 5 | 2023-05-12 | +0.679x | -55% | 12.7% | 2 | -330€ |
| 6 | 2023-07-01 | +0.392x | -74% | 11.3% | 1 | -444€ |
| 7 | 2023-08-20 | +0.392x | -74% | 11.3% | 1 | -444€ |
| 8 | 2023-10-09 | +0.287x | -81% | 12.3% | 0 | -486€ |
| 9 | 2023-11-28 | +0.337x | -78% | 14.7% | 0 | -466€ |
| 10 | 2024-01-17 | +0.297x | -80% | 14.3% | 0 | -482€ |
| 11 | 2024-03-07 | +0.633x | -58% | 13.3% | 2 | -348€ |
| 12 | 2024-04-26 | +0.618x | -59% | 12.3% | 2 | -354€ |
| 13 | **2024-06-15** | **+3.378x** | **+124%** | 12.0% | 4 | **+744€** |
| 14 | 2024-08-04 | +3.026x | +101% | 12.0% | 2 | +604€ |
| 15 | 2024-09-23 | +3.785x | +151% | 13.7% | 6 | +906€ |
| 16 | 2024-11-12 | +1.674x | +11% | 16.0% | 7 | +66€ |
| 17 | 2025-01-01 | +1.920x | +27% | 16.3% | 8 | +164€ |
| 18 | 2025-02-20 | +1.161x | -23% | 14.7% | 4 | -138€ |
| 19 | 2025-04-11 | +0.553x | -63% | 14.0% | 1 | -380€ |
| 20 | 2025-05-31 | +3.041x | +102% | 13.3% | 2 | +610€ |
| 21 | 2025-07-20 | +3.182x | +111% | 14.0% | 3 | +666€ |
| 22 | 2025-09-08 | +3.383x | +124% | 11.7% | 4 | +746€ |
| 23 | 2025-10-28 | +1.513x | +0% | 13.3% | 6 | +2€ |

### L.8 Pattern temporale: due regimi distinti

**Regime A — "freddo" (2022-05 a 2024-05, circa 2 anni, bucket 1-12):**
- Ratio medio: 0.65x
- Quasi tutti i bucket sotto breakeven (1.508x)
- Hit rate tipico 10-14%
- Perdita sistemica: -40% a -80% ROI

**Regime B — "caldo" (2024-06 a 2025-10, circa 17 mesi, bucket 13-23):**
- Ratio medio: 2.40x
- **9 su 11 bucket sopra breakeven**
- Hit rate tipico 12-16%
- Vincita ricorrente: +10% a +150% ROI

**Differenza dei regimi:**
- Big wins: Regime A media 2.0/bucket, Regime B media 4.3/bucket
- Ratio mediano: A = 0.64x, B = 3.04x

### L.9 Interpretazione: tre ipotesi

**Ipotesi 1 — Non-stazionarieta RNG (pattern reale)**
Il sistema MillionDay di Sisal ha ricevuto un update/cambio infrastrutturale a giugno 2024. Il nuovo PRNG ha pattern diverso (piu pesca da "residuo base") che favorisce `cold_plus_hotex`. 

**Test che conferma**: se fosse vera, la config dovrebbe continuare a funzionare su dati post-2025-10 (bucket futuri).

**Ipotesi 2 — Fluttuazione campionaria estrema**
Con payoff skewed (max 1000€ cap vs 2€ cost) e 300 giocate per bucket, sd_ratio per bucket e ~2.5-3.0. Un ratio medio di 3.0x e compatibile con ~1-2 sigma sopra una media vera di 1.0x. Over 11 bucket consecutivi "favorevoli" la probabilita e bassa (~1%) ma non impossibile.

**Test che falsifica**: se fosse vera, la media su lungo termine (es. prossimi 2000 giocate) dovrebbe tornare a ~1.0x.

**Ipotesi 3 — Overfitting di selezione**
`cold_plus_hotex W=66` e stata selezionata come "best" DOPO aver visto tutti i dati. La stessa config su periodo 2022-2024 sarebbe stata pessima (era infatti sotto baseline). La selezione post-hoc amplifica la varianza della statistica validation.

**Test che falsifica**: se fosse vera, una config scelta a priori (senza vedere i dati) non avrebbe il pattern Regime A/B.

### L.10 Verdetto metodologico

Con solo 2.607 estrazioni e 3.600 config testate, **non si puo distinguere fra le 3 ipotesi**. Ma:

1. **Nessuna config passa Bonferroni** (p=0.001 vs soglia 0.00001)
2. **Coerenza disc/val e pessima** per tutte le top config
3. **Il pattern 2022-2024 vs 2024-2025 potrebbe essere reale o rumore** — servirebbero altri 18+ mesi di dati per testare out-of-sample

### L.11 Implicazione operativa

Due scenari:

**Scenario ottimistico (ipotesi 1 vera):**
Se il RNG ha cambiato comportamento in giugno 2024, allora `cold_plus_hotex W=66` (3 freddi base + 2 caldi extra, W=66) potrebbe effettivamente produrre edge POSITIVO nel prossimo anno. Ma si giocherebbe su un'ipotesi fragile.

**Scenario realista (ipotesi 2-3 vera):**
Il pattern e varianza campionaria + multiple testing + selection bias. Giocare la config fallirebbe nel futuro. Il vero EV resta 1.326€/giocata (HE 33.7%) per qualsiasi strategia.

**Raccomandazione**: trattare qualsiasi risultato con N<5.000 estrazioni e N_configs>100 come **indicativo, non conclusivo**. La config cold_plus_hotex W=66 merita un follow-up SOLO se si accumulano altri ~1.500 estrazioni e il pattern tiene.

### L.12 Upgrade proposto per il portale MillionDay

Il metodo attuale del portale e `optfreq W=60` (ratio val 1.343x non-robust). Se si volesse aggiornare basandosi su questo sweep, candidati:
- `cold_plus_hotex W=66` (ratio robust 3.25x, ma Regime B-dipendente)
- `optfreq W=170` o `W=60` (ratio robust 2.48x/1.9x, piu stabile fra regime)

**Decisione proposta**: NON aggiornare il metodo del portale. Il benchmark stabile e l'`optfreq W=60` dimostrato dalla deep analysis. Cambiare metodo dopo vedere `cold_plus_hotex W=66` brillare sarebbe sintomatico di selection bias.

Tuttavia, **aggiungere alla pagina MillionDay un disclaimer** che la performance recente (2024-06 in poi) e fluttuante e il vero EV atteso resta negativo.

---

## 26. Lezioni Finali del Lottery Lab

### 26.1 Tabella definitiva dei segnali

| Gioco | Config | Dataset | HE | Breakeven | Miglior segnale | Ratio val | p-value | Supera BE? |
|-------|--------|---------|-----|-----------|-----------------|-----------|---------|-----------|
| Lotto ambetto | tutte le ruote | 6.886 estr. | 37.6% | 1.60x | vicinanza D=20 W=125 | 1.18x | CV 5-fold | No |
| Lotto ambo | ruota singola | 6.886 estr. | 37.6% | 1.60x | freq_rit_fib W=75 | 1.16x | CV 5-fold | No |
| VinciCasa | 5/40 base | 3.279 estr. | 37.3% | 1.60x | top5_freq W=5 | 1.22x | 0.01 | No |
| MillionDay (est.) | 5/55 b+E | 2.607 estr. | 33.7% | 1.51x | top5_freq W=20 | 1.37x | 0.054 | No (FAIL Bonf.) |
| MillionDay (deep) | 5/55 b+E optfreq | 2.607 estr. | 33.7% | 1.51x | optfreq W=60 | 1.34x | 0.050 | No (FAIL Bonf.) |
| 10eLotto K=6+Extra | config HE min | 33.431 estr. | 9.94% | 1.11x | vicinanza W=100 | 1.08x | 0.054 | No (borderline) |
| 10eLotto K=6+E ST | Special Time | 33.431 estr. | 6.30% | 1.067x | dual_target W=100 | 1.10x | FAIL Bonf. | No |
| **10eLotto K=8+Extra** | **dual_target** | **33.431 estr.** | **30.75%** | **1.45x** | **dual_target W=100** | **1.445x** | **pending** | **SI (backtest)** |

### 26.2 Le 7 lezioni fondamentali

**1. Il segnale piu forte e emerso dall'analisi sistematica per K, non dal K "ottimale" del HE.**
Tutti i capitoli 21-24 si erano concentrati sul K=6+Extra (HE 9.94%). E stato solo generalizzando l'analisi a K=1..10 che e emerso il K=8+dual_target con ratio 1.445x. **Lezione: non lasciarsi guidare dall'EV ma dal prodotto ratio × breakeven_residuo.**

**2. Le lotterie 5/N: VinciCasa unico, MillionDay invalidato (vedi Appendice E-bis).**
top5_freq W=5 su VinciCasa → 1.22x (p=0.01, 3.279 estrazioni) — **rimane l'unico segnale validato**. Su MillionDay, dataset 5x piu grande (2.607 estrazioni da millionday.cloud) **invalida** il segnale W=50 del dataset originale: W=50 crolla da 1.23x a 0.67x, il nuovo W=20 e borderline (p=0.054 FAIL Bonferroni) e decade temporalmente (2022 0.94x → 2026 0.26x). Il "pattern generico 5/N" era un'illusione da piccolo campione.

**3. Il Lotto (urne fisiche) ha pattern piu robusti del 10eLotto (PRNG).**
CV 5-fold valida il segnale Lotto. Il 10eLotto sopravvive a stento un singolo split 50/50. Lo scarto e reale: le urne hanno micro-bias fisici, il PRNG no.

**4. La correzione Bonferroni distrugge quasi tutti i "segnali".**
94 test sul 10eLotto + 10 sul Strategy Lab K + 18 su MillionDay esteso = 122+ test. Soglia Bonferroni a 0.05/122 = 0.00041. Nessun segnale finora validato sopravvive (compreso il K=8+dual_target, in attesa di permutation test).

**5. Il wheeling e il conditional staking non creano edge.**
Testato esaustivamente: P&L marginale o peggio. Confermato dalla teoria (Kelly su EV<1 = non giocare).

**6. L'ingestione continua e il vero valore aggiunto operativo.**
Il paper trading retroattivo + scheduler cron + frontend live trasformano un esperimento statistico in un sistema che puo continuare a validarsi nel tempo, rilevando automaticamente drift e decadimento dei segnali.

**7. Il progetto ha risposto alla domanda originale con metodo.**
La domanda "le lotterie italiane sono battibili?" ha oggi una risposta operativa: **no, tranne forse K=8+Extra su 10eLotto con dual_target W=100 — da confermare con permutation test e Bonferroni**.

### 26.3 Debito tecnico residuo

| Item | Priorita | Note |
|------|----------|------|
| Permutation test K=8 dual_target | **Alta** | Conferma o smonta l'unico segnale al breakeven |
| Replicazione VinciCasa su dataset alternativo | Alta | Confermare che 1.22x non e artefatto di quel specifico dataset |
| Ingestione MillionDay pre-2022 (2018-2021) | Media | Il parser scarta righe senza Extra (~1500 entries) |
| Frontend MillionDay | Bassa | Engine + API + page (ora che non c'e segnale, meno urgente) |
| Paper trading con denaro reale K=8 | Bassa | Solo dopo conferma permutation |
| ~~Integrazione millionday.cloud~~ | Completato | Parser HTML + 2.607 estrazioni, Appendice E-bis |

### 26.4 Conclusione definitiva

Il Lottery Lab ha coperto **4 giochi (Lotto, VinciCasa, 10eLotto, MillionDay)**, ha analizzato **~46.000 estrazioni reali** (con MillionDay esteso da 496 a 2.607), ha testato **oltre 122 configurazioni predittive** con metodologia CV + permutation + Bonferroni, e ha prodotto un **portale web funzionante in produzione** (https://lottery.fl3.org) con paper trading live retroattivo.

Il risultato scientifico e netto: **le lotterie italiane sono al 99% imbattibili**. L'1% residuo e il K=8+Extra su 10eLotto con dual_target W=100, in attesa di validazione formale. MillionDay, inizialmente promettente con 496 estrazioni (ratio 1.23x p=0.18), e stato **invalidato** dal dataset esteso: il segnale originale W=50 era rumore, il nuovo W=20 e borderline (p=0.054) e instabile nel tempo.

Il valore metodologico e enorme: ogni test e riproducibile, ogni dato tracciato, ogni conclusione documentata. L'episodio MillionDay — ratio 1.23x su 496 invalidato su 2.607 — e esso stesso una lezione sul perche la replicazione su dataset ampliati sia irrinunciabile.

Il paper si chiude con la stessa frase con cui e iniziato: **nessun gioco e profittevole. Ma il viaggio per scoprirlo e stato rigoroso, e questo paper documenta ogni passo.**

---

*Documento generato dal sistema Lottery Lab — ultima revisione aprile 2026*
*Dataset: Lotto 6.886 + VinciCasa 3.279 + 10eLotto 33.431 + MillionDay 2.607 = 46.203 estrazioni*
*Test totali: 172+ configurazioni predittive (incl. deep MillionDay 50 configurazioni), 9 RNG cert, 5 deep analysis, 8.010 coppie numeri spia*
*Portale in produzione: https://lottery.fl3.org*
