# Standard di Qualità Universali

## Il Layer Stack-Agnostico del Metodo CCLU

10 domini, 40+ regole. Ordinati per priorità: sicurezza prima di tutto.

Formato: **DEVE / NON DEVE** — Perché — Pattern — Anti-pattern.

---

## 1. SICUREZZA

### S1. Input mai fidato
**DEVE:** Ogni dato dall'esterno (HTTP, file, webhook, query string, header, cookie, WebSocket) DEVE essere validato e sanitizzato prima dell'uso.
**NON DEVE:** Mai input in query SQL, comandi shell, HTML, template, path, regex.
**Perché:** Input non validato = vettore del 90% degli attacchi.
**Anti-pattern:** "L'input arriva dal nostro frontend, quindi è sicuro." Il frontend è controllato dall'utente.

### S2. Query parametrizzate, sempre
**DEVE:** Ogni query con dati variabili usa prepared statements / parametri bind.
**NON DEVE:** Mai concatenare o interpolare stringhe per query, nemmeno con dati interni tipizzati.
**Perché:** Un `int` oggi può diventare `string` domani. Il prepared statement è difesa strutturale.

### S3. Secrets fuori dal codice
**DEVE:** Ogni credenziale in environment variables o secret manager. Mai nel codice, mai nei file committati, mai nei log.
**NON DEVE:** Mai committare file con secrets. Mai loggare token/password/chiavi, nemmeno parzialmente.

### S4. Encryption per dati sensibili at-rest
**DEVE:** Token, API key clienti, PII reversibili cifrati nel database (AES-256-GCM o equivalente).
**NON DEVE:** Mai token/chiavi in plaintext nel DB, nemmeno in JSONB, nemmeno "temporaneamente".

### S5. Auth su ogni endpoint protetto
**DEVE:** Ogni endpoint non pubblico valida autenticazione E autorizzazione (scope, ruolo, permessi).
**Pattern:** Middleware globale + whitelist esplicita per rotte pubbliche (non blacklist).

### S6. Rate limiting su endpoint pubblici
**DEVE:** Endpoint senza auth: rate limiting per IP. Endpoint autenticati: per utente/tenant.
**Pattern:** Counter in Redis/memoria con TTL. Risposta 429 con Retry-After.

---

## 2. PULIZIA DEL CODICE

### P1. Un file, una responsabilità
Controller gestisce HTTP. Service contiene logica. Repository accede ai dati. Component renderizza UI.
Mai mescolare logica di business in controller. Mai query SQL nei controller.

### P2. Naming che spiega
`calculateMonthlyRevenue()` non `calcRev()`. `isOperatorAvailable()` non `checkOp()`. Mai abbreviazioni ambigue.

### P3. File corti, coesione alta
Max 400 righe per file (ideale 200-300). Se supera, va diviso. Funzioni max 50 righe. 3+ livelli indentazione = estrarre.

### P4. Consistenza nei pattern
Un progetto, un pattern. Se è Repository, è Repository ovunque. Se è camelCase, è camelCase ovunque. Mai mescolare.

### P5. Niente codice morto
Codice commentato, funzioni non chiamate, import non usati, variabili non lette → rimossi immediatamente. Git esiste per recuperare.

---

## 3. RESILIENZA

### R1. Ogni errore gestito e loggato
Ogni operazione fallibile in try/catch. Ogni catch logga con contesto (stack, input sanitizzato, stato). Mai catch vuoti.

### R2. Timeout su ogni operazione esterna
API call: 10s. DB query: 30s. File upload: 60s. Mai chiamate senza timeout.

### R3. Retry con backoff esponenziale
Operazioni idempotenti con errori transienti: `wait = min(base × 2^attempt + jitter, max)`. Max 3-5 tentativi. Mai retry su 400/401/404.

### R4. Operazioni esterne asincrone
Webhook, email, push, sync terze parti: dispatch asincrono via job queue. Mai bloccanti nella risposta al client.

### R5. Graceful degradation
Componente non critico fallisce? Il sistema continua. Fail-open per analytics/notifiche. Fail-closed per auth/payment.

---

## 4. TESTABILITÀ

### T1. Test per la logica di business
Ogni service con logica di business ha test unitari. Copertura logica business ≥ 80%.

### T2. Test per i casi limite
Input nullo/vuoto, limite (0, max, stringa vuota), malformato, errori attesi. I bug vivono ai confini.

### T3. Test che verificano comportamento, non implementazione
Verifica cosa esce dato cosa entra. Mai test che si rompono con refactoring che non cambia il comportamento.

### T4. Build verde come precondizione
Test suite verde prima di merge/deploy. Test rosso = bloccante, non warning.

---

## 5. MANUTENIBILITÀ

### M1. CLAUDE.md come fonte di verità
Ogni progetto ha CLAUDE.md: stack, comandi, convenzioni. Aggiornato ad ogni cambio architetturale. Max 400 righe.

### M2. Lezioni apprese documentate
Ogni bug non banale → Lesson Card: contesto, problema, soluzione, regola. Le lezioni non documentate si dimenticano.

### M3. Conventional Commits dal giorno zero
`type(scope): descrizione`. Changelog auto-generato. Versioning automatico. Git blame leggibile.

### M4. Nessuna dipendenza da conoscenza orale
Tutto ciò che serve per far funzionare il progetto scritto da qualche parte: deploy, config, secrets, rollback.

### M5. Architecture Decision Records
Ogni decisione architetturale significativa documentata in ADR con: contesto, decisione, alternative, conseguenze.

### M6. Technical Debt visibile
Ogni compromesso tracciato in TECH_DEBT.md con: cosa, dove, perché, impatto, effort, deadline. Review mensile.

---

## 6. PERFORMANCE

### PF1. Query N+1 mai accettabili
Ogni lista carica dati correlati in una singola query (join, eager loading). Mai un loop con query per riga.

### PF2. Cache per dati letti spesso, scritti raramente
TTL ragionevole. Invalidazione esplicita sul write. Mai cache senza invalidazione. Mai cache senza TTL.

### PF3. Lazy loading per risorse pesanti
Immagini, componenti complessi, dati non visibili: on-demand. Mai 10k righe in una risposta. Mai bundle JS da 5MB.

---

## 7. DEVOPS

### D1. Deploy è un singolo comando
Build, push, deploy, migration, health check. Nessun step manuale. Rollback è un altro singolo comando.

### D2. Staging identico a produzione
Stesso codice, stesse immagini, stesso schema. Differenze solo: risorse, dati, secrets, domini.

### D3. Logging centralizzato e strutturato
JSON con campi dedicati. Centralizzato (non file locali). Request ID in ogni entry.

### D4. Health check su ogni servizio
Verifica: servizio up, DB raggiungibile, cache raggiungibile, dipendenze esterne.

### D5. Backup automatico con verifica
Backup giornaliero DB prod, retention 14 giorni minimo. Restore testato periodicamente.

### D6. Monitoring che notifica
Health check fallito (3x consecutivi), error rate > 5% (per 5 min), disco > 80%, SSL in scadenza.

---

## 8. ACCESSIBILITÀ

### A1. Semantic HTML
**DEVE:** Usare elementi HTML semantici (`<nav>`, `<main>`, `<article>`, `<button>`, `<label>`) invece di `<div>` con ruoli ARIA artificiali. Un `<button>` è un button, non un `<div onClick>`.
**Perché:** Gli screen reader dipendono dalla semantica. Un div cliccabile è invisibile ai non vedenti.

### A2. Navigazione da tastiera
**DEVE:** Ogni elemento interattivo raggiungibile e attivabile da tastiera (Tab, Enter, Space, Escape). Focus visibile e in ordine logico.
**NON DEVE:** Mai `outline: none` senza alternativa. Mai trap del focus (l'utente non riesce a uscire da un modale).

### A3. Contrasto sufficiente
**DEVE:** Testo normale: rapporto contrasto ≥ 4.5:1. Testo grande (18px+ o 14px+ bold): ≥ 3:1. Elementi UI interattivi: ≥ 3:1.
**Anti-pattern:** Grigio chiaro su bianco. Placeholder come unica label.

### A4. Informazioni non solo via colore
**DEVE:** Ogni informazione comunicata via colore deve avere anche un indicatore alternativo (icona, testo, pattern).
**Perché:** ~8% degli uomini è daltonico. Un semaforo rosso/verde senza label è inutile per loro.

### A5. Form accessibili
**DEVE:** Ogni input ha un `<label>` associato (con `for`/`id`). Errori di validazione collegati all'input via `aria-describedby`. Gruppi di radio/checkbox in `<fieldset>` con `<legend>`.

---

## 9. OBSERVABILITY

### O1. Request ID / Correlation ID
**DEVE:** Ogni richiesta in ingresso riceve un ID univoco (UUID o equivalente), propagato in tutti i log, risposte di errore, e chiamate a servizi downstream. Permette di tracciare il percorso completo di una richiesta.
**Pattern:** Middleware al primo ingresso genera l'ID. L'ID va nell'header `X-Request-ID`. Ogni riga di log include l'ID.

### O2. Metriche applicative
**DEVE:** Esporre metriche per: latency (P50, P95, P99 per endpoint), error rate (per endpoint e globale), throughput (richieste/secondo), saturazione risorse (DB connections, memory, CPU).
**Pattern:** Contatore/istogramma nel codice → esportati a Prometheus (o equivalente) → dashboard Grafana (o equivalente).

### O3. Alerting con soglie
**DEVE:** Configurare alert per: error rate > soglia per N minuti, latency P95 > soglia, health check fallito 3x, risorse > 80%.
**NON DEVE:** Mai alert su singoli errori (rumore). Sempre su trend o soglie persistenti.
**Pattern:** Alert → canale notifica (Telegram, Slack, email) con contesto sufficiente per diagnosticare senza aprire i log.

### O4. Livelli di log corretti
**DEVE:** DEBUG per eventi attesi ad alto volume. INFO per eventi significativi (deploy, startup, shutdown). WARNING per anomalie non bloccanti. ERROR per bug ed errori inattesi. FATAL per crash.
**Anti-pattern:** Tutto a ERROR → log illeggibili. Token scaduto = DEBUG, non ERROR.

---

## 10. DATA & PRIVACY

### DP1. Privacy by Design
**DEVE:** Ogni campo che contiene dati personali (PII) deve essere identificato nello schema DB con annotazione/commento. La decisione "perché raccogliamo questo dato" deve essere documentata.
**Perché:** GDPR richiede data mapping. Senza sapere dove sono i PII, non puoi garantire compliance.

### DP2. Data Retention
**DEVE:** Ogni tipo di dato deve avere una retention policy definita: quanto tempo lo conservi, quando lo elimini, come lo elimini.
**Pattern:** Tabella retention policy nella documentazione. Job periodico che pulisce i dati scaduti.

### DP3. Data Minimization
**DEVE:** Raccogliere solo i dati necessari per la funzionalità. Se un campo non serve, non chiederlo.
**NON DEVE:** Mai "lo raccogliamo perché potrebbe servire in futuro".

### DP4. Right to Deletion
**DEVE:** Implementare una procedura (anche manuale inizialmente) per cancellare tutti i dati di un utente su richiesta. Includere: DB, backup, log, cache, servizi terzi.
**Perché:** GDPR Art. 17. Non è opzionale se tratti dati di residenti EU.

### DP5. Audit Trail per dati sensibili
**DEVE:** Ogni accesso a dati sensibili (PII, dati sanitari, finanziari) deve essere loggato: chi, quando, cosa, perché.
**Pattern:** Tabella `audit_log` append-only con: user_id, action, resource, timestamp, ip.

---

## Come Usare Questo Documento

### Nel CLAUDE.md

```markdown
## Standard di Qualità
Le regole sono in `docs/QUALITY_STANDARDS.md`.
Seguile SEMPRE. Priorità: Sicurezza > Pulizia > Resilienza > Test.
```

### Durante la review

Per ogni file modificato: S (sicurezza?) → P (pulizia?) → R (resilienza?) → T (test?) → M (manutenibilità?) → PF (performance?) → D (devops?) → A (accessibilità?) → O (observability?) → DP (data/privacy?)

### Per nuovi membri del team

Questo documento è il primo da leggere dopo il CLAUDE.md. Contiene le regole del gioco.
