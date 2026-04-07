# Lotto Convergent -- Paper di Ricerca Completo

## Abstract

Un sistema predittivo per ambi secchi del Lotto Italiano basato su filtri convergenti e stato sviluppato e testato su 6.886 estrazioni storiche (1946-2026). Dopo 18+ analisi statistiche, test su geometria sacra, cabala, e ottimizzazione delle finestre temporali, il miglior segnale trovato (freq+rit+dec con finestra 150 estrazioni) mostra un edge medio del 22.5% rispetto al caso, validato su 5 periodi temporali indipendenti. Il breakeven richiede un edge del 60%, rendendo il sistema non profittevole in media. Tuttavia, l'analisi per ruota e ciclica rivela che il segnale e ciclico: durante le fasi attive (20% del tempo), supera il breakeven con ratio 1.5-2.0x. La sfida aperta e prevedere il timing di attivazione. Il paper documenta l'intero percorso di ricerca con trasparenza metodologica.

**Parole chiave:** Lotto Italiano, ciclometria, filtri convergenti, backtesting, ambo secco, money management, analisi statistica, gambler's fallacy

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

I risultati del Capitolo 10 hanno ridefinito le prospettive: il segnale freq+rit+dec e ciclico, e durante le fasi attive (20% del tempo) supera il breakeven. Il problema centrale si sposta dalla ricerca dell'edge alla **predizione del timing**.

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

*Documento generato dal sistema Lotto Convergent -- Aprile 2026*
*Dati: archivio estrazioni Lotto Italiano 2007-2026 (6886 estrazioni)*
