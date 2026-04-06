# Lesson Cards — Universali

Lezioni valide per qualsiasi stack, linguaggio e infrastruttura. Ogni lezione nasce da un errore reale incontrato in produzione.

---

## Architettura e Pattern

### 1. Tenant resolution — fallback obbligatorio per route admin/dashboard

**Contesto:** Architettura multi-tenant dove un middleware risolve il tenant automaticamente, ma salta le rotte di gestione (dashboard, admin).
**Problema:** I controller dashboard non hanno il tenant risolto dal middleware. Se controllano solo l'attributo del middleware, restituiscono "Tenant not found".
**Soluzione:** Implementare un fallback che risolve il tenant dall'ID organizzazione presente nel token auth.
**Regola:** Ogni controller che serve rotte di gestione (non utente finale) DEVE avere un fallback per la risoluzione del contesto.

### 2. Route pubbliche — registrare in TUTTI i middleware di sicurezza

**Contesto:** Endpoint che riceve chiamate esterne senza autenticazione (webhook, callback, health check).
**Problema:** L'endpoint viene aggiunto alla whitelist del middleware auth, ma non a quella degli altri middleware (tenant resolver, metering). Un middleware a valle crasha.
**Soluzione:** Ogni endpoint pubblico va whitelistato in TUTTI i middleware della catena.
**Regola:** Quando aggiungi un endpoint pubblico, scorri TUTTI i middleware e verifica.

### 3. Effetti collaterali — orchestrare nel controller, non nel service

**Contesto:** Un'operazione (es. AI che suggerisce escalation) deve triggerare un effetto collaterale (es. creazione record in coda).
**Problema:** Il service che genera il dato non crea l'effetto collaterale. Il record non appare nella coda.
**Soluzione:** Il Controller orchestra: riceve il risultato dal service A, e chiama il service B per l'effetto collaterale.
**Regola:** I service producono dati e decisioni. I controller collegano i service e orchestrano i flussi.

### 4. Operazioni esterne — dispatch asincrono nel flusso di risposta

**Contesto:** Notifiche esterne (webhook, email, push) durante una richiesta HTTP.
**Problema:** Il client aspetta 20+ secondi perché il webhook destinatario è lento o in retry.
**Soluzione:** Inserire un job nella coda asincrona e ritornare subito al client.
**Regola:** Nessuna chiamata esterna sincrona nel flusso request-response, tranne l'operazione primaria.

### 5. Matrix endpoint — combinare dati nel backend

**Contesto:** Il frontend mostra una matrice (es. entità × proprietà da un'altra tabella).
**Problema:** Il frontend fa N+1 chiamate (una per la lista, poi N per i dettagli).
**Soluzione:** Endpoint dedicato che restituisce la matrice pre-calcolata.
**Regola:** Se il frontend deve combinare dati da 2+ endpoint per una vista, creare un endpoint aggregato.

### 6. Record base + override — mostrare entrambi

**Contesto:** Tabella base (es. profili) con tabella override (es. versioni custom).
**Problema:** Se cerchi solo nella tabella override, gli item senza override non appaiono.
**Soluzione:** Query UNION ALL: record con override attivo + record base senza override (con NOT EXISTS).
**Regola:** Ogni coppia base-override deve usare UNION ALL per la vista completa.

---

## Deploy e Infrastruttura

### 7. Env vars — preservare ad ogni redeploy

**Contesto:** Sistema di deploy che ricrea i container (qualsiasi orchestrator).
**Problema:** Il redeploy sovrascrive le env vars con quelle passate nel body. Se omesse, vengono azzerate.
**Soluzione:** Leggere le env vars correnti PRIMA del redeploy e ri-inviarle.
**Regola:** Se dopo un deploy le env vars sono vuote, STOP. Ripristinare manualmente prima di procedere.

### 8. DNS e service discovery — naming univoco su reti condivise

**Contesto:** Più ambienti (staging, prod) sulla stessa rete.
**Problema:** Il nome generico (es. "backend") risolve a TUTTI i container con quel nome, in round-robin. 33% delle richieste vanno al servizio sbagliato.
**Soluzione:** Usare nomi univoci (es. `progetto-backend-staging`) per le comunicazioni inter-servizio.
**Regola:** Su reti condivise, mai nomi generici. Sempre nomi globalmente univoci.

### 9. Database volume — credenziali persistenti

**Contesto:** Cambio password del database nel file di configurazione.
**Problema:** Il database inizializza le credenziali al PRIMO avvio. Cambiare la config non aggiorna il volume esistente.
**Soluzione:** Se il DB è vuoto, ricrea il volume. Se ha dati, cambia la password via shell interattiva.
**Regola:** Le credenziali DB vivono nel volume, non nella config. Per cambiarle, agire nel DB.

### 10. Proxy applicativo — strippare header di encoding

**Contesto:** Un proxy server-side che forwarda risposte dal backend al client.
**Problema:** Il proxy decomprime automaticamente la risposta (gzip/deflate), ma forwarda l'header `Content-Encoding` originale. Il client tenta una seconda decompressione → errore.
**Soluzione:** Rimuovere `content-encoding` e `content-length` dai response header prima del forward.
**Regola:** In qualsiasi proxy applicativo, sempre strippare gli header di encoding.

### 11. Health check IPv6 — usare IP esplicito

**Contesto:** Health check in container basati su distribuzioni minimali.
**Problema:** `localhost` può risolvere a IPv6. Se il servizio ascolta solo su IPv4, il check fallisce → container marcato unhealthy → restart loop.
**Soluzione:** Usare `127.0.0.1` invece di `localhost` nei health check.
**Regola:** In TUTTI i health check, usare l'IP esplicito.

### 12. Rete esterna — dichiarare, non connettere manualmente

**Contesto:** Reverse proxy che deve raggiungere i container applicativi su reti Docker.
**Problema:** La connessione manuale si perde quando la rete viene ricreata (al redeploy).
**Soluzione:** Dichiarare la rete come esterna nel compose. I container si connettono automaticamente.
**Regola:** Mai connessioni di rete manuali. Sempre dichiarative nel compose.

---

## Frontend e UI

### 13. Token scaduti con polling attivi — handler globale obbligatorio

**Contesto:** Dashboard con polling periodici (analytics, notifiche, code live) e token auth con scadenza.
**Problema:** Alla scadenza del token, i polling continuano con token invalido → flood di 401 nei log.
**Soluzione:** Handler globale nel client HTTP: al primo 401, flag di deduplicazione, revoca token, redirect a login.
**Regola:** Se hai polling, DEVI avere un 401 handler globale che li ferma.

### 14. Polling — backoff esponenziale obbligatorio

**Contesto:** Client che fa polling periodico a un endpoint.
**Problema:** Intervallo fisso senza gestione errori = flood infinito di richieste fallite se il backend è down.
**Soluzione:** Backoff esponenziale su errore, counter di fallimenti, stop dopo N errori, stop quando componente non visibile, timer dinamico (non intervallo fisso).
**Regola:** Ogni polling DEVE avere: backoff, cap, e stop condition.

### 15. Dati client — il backend è la source of truth

**Contesto:** Persistenza di stato tra navigazioni di pagina.
**Problema:** Salvare dati nel client storage (localStorage, AsyncStorage) → diventano stale.
**Soluzione:** Usare il client storage solo per identificativi (session ID, token). Ricaricare i dati dal backend ad ogni inizializzazione.
**Regola:** Il client storage è per chiavi di riferimento, non per dati.

### 16. Feature flags — default a "abilitato" nel frontend

**Contesto:** Feature gating con sistema di feature flags.
**Problema:** Se i flag non sono caricati (rete fallita, backend down), ritornare `false` nasconde feature funzionanti.
**Soluzione:** `isEnabled()` ritorna `true` se il flag non esiste. Kill switch = `false` esplicito nel backend.
**Regola:** Il frontend non deve mai nascondere feature per un errore di rete.

### 17. Security headers — solo gli appropriati per ambiente

**Contesto:** Header come HSTS che forzano HTTPS.
**Problema:** Se attivi in sviluppo, il browser forza HTTPS su localhost → tutto si rompe.
**Soluzione:** Condizionare gli header di sicurezza sull'ambiente.
**Regola:** Security headers ambiente-dipendenti vanno condizionati su `APP_ENV` o equivalente.

---

## Testing e Qualità

### 18. Fix completi — verificare tutto il visibile all'utente

**Contesto:** Fix di un dato tecnico (es. versione nel DB).
**Problema:** Il dato tecnico è corretto, ma la pagina che lo mostra ha sezioni vuote, contenuti non compilati, UI incompleta.
**Soluzione:** Checklist mentale: dato corretto? UI aggiornata? Testi compilati? Esperienza end-to-end completa?
**Regola:** Un fix è completo solo quando l'utente finale vede tutto correttamente.

### 19. Livelli di log — eventi attesi ≠ errori

**Contesto:** Token scaduti, richieste rate-limitate, utenti non trovati.
**Problema:** Loggati come ERROR riempiono i log senza informazioni azionabili.
**Soluzione:** Usare il livello appropriato: evento atteso → DEBUG, anomalia non bloccante → WARNING, bug → ERROR.
**Regola:** Se un evento riempie i log senza fornire azioni possibili, il livello è troppo alto.

### 20. SQL — zero interpolazione, sempre

**Contesto:** Query con parametri, anche tipizzati o interni.
**Problema:** Un parametro tipizzato `int` oggi può diventare `string` in un refactoring. L'interpolazione è un rischio strutturale.
**Soluzione:** Prepared statements / parametri bind. Sempre. Nessuna eccezione.
**Regola:** Zero interpolazione in SQL. La difesa è strutturale, non disciplinare.

---

## Operazioni e Recovery

### 21. Rollback — testare PRIMA che serva

**Contesto:** Script di rollback scritto ma mai eseguito.
**Problema:** Quando serve (incidente in produzione), scopri che non funziona: dipendenza mancante, path sbagliato, migration down() che perde dati.
**Soluzione:** Testare il rollback periodicamente (almeno ogni release significativa) con dry-run in staging.
**Regola:** Un rollback mai testato è un rollback che non esiste.

### 22. Migration — backward compatibility obbligatoria

**Contesto:** Migration che rinomina/rimuove colonne deployata prima del codice aggiornato.
**Problema:** Il codice in produzione ancora usa il nome vecchio. 500 su tutti gli endpoint che toccano quella tabella.
**Soluzione:** Schema addittivo (ADD) prima del codice. Schema sottrattivo (DROP) dopo il codice. Schema modificativo (RENAME) in due step.
**Regola:** Mai rimuovere/rinominare colonne nello stesso deploy che aggiorna il codice. Sempre in due step.

### 23. Dependency audit — settimanale, non "quando mi ricordo"

**Contesto:** Dipendenza con CVE critica nota da 3 mesi, non aggiornata.
**Problema:** L'aggiornamento è diventato complesso (breaking change accumulate) o impossibile (dipendenza abbandonata).
**Soluzione:** Audit automatico settimanale. Patch subito. Minor mensili. Major trimestrali pianificati.
**Regola:** Più aspetti ad aggiornare, più costa. Il costo dell'aggiornamento cresce esponenzialmente col tempo.

### 24. Error contract — un formato, tutti gli endpoint

**Contesto:** Frontend che gestisce errori da 15 endpoint diversi, ognuno con formato diverso.
**Problema:** L'error handler è un mostro di if/else. Un nuovo endpoint con formato leggermente diverso rompe la UI.
**Soluzione:** Un singolo Error Contract definito al giorno zero. Tutti gli endpoint, inclusi auth e webhook, lo rispettano. Il frontend ha un singolo handler.
**Regola:** Definire il formato errori prima del primo endpoint. È un contratto, non un suggerimento.

### 25. Accessibility — non è un nice-to-have

**Contesto:** Applicazione web usata da centinaia di utenti, zero test di accessibilità.
**Problema:** Utente non vedente non riesce ad usare il prodotto. Utente con mobilità ridotta non riesce a navigare da tastiera. In EU, può essere un requisito legale (European Accessibility Act 2025).
**Soluzione:** Semantic HTML, keyboard navigation, contrast ratio, label sui form, informazioni non solo via colore. Check in post-implementation per ogni componente frontend.
**Regola:** Se ha un frontend, ha requisiti di accessibilità. WCAG 2.1 AA come baseline minima.

### 26. Observability — metriche prima dei log

**Contesto:** Bug in produzione. Vai a cercare nei log. Trovi migliaia di righe, nessuna utile.
**Problema:** I log ti dicono cosa è successo dopo che hai identificato il problema. Non ti dicono che c'è un problema.
**Soluzione:** Metriche applicative (latency, error rate, throughput) con alerting su soglie. I log sono per il dettaglio, le metriche per la detection. Request ID per collegare i due.
**Regola:** Se non hai metriche, non sai che c'è un problema finché un utente non te lo dice. E l'utente ti dirà "non funziona" senza dettagli.

### 27. Technical debt — visibile o mortale

**Contesto:** "Lo sistemo dopo" detto 15 volte in 3 mesi.
**Problema:** Dopo 3 mesi: 15 hack, nessuno ricorda perché, il refactoring costa 3 settimane invece di 3 ore.
**Soluzione:** Ogni compromesso in TECH_DEBT.md con: cosa, dove, perché, impatto, effort, deadline. Review mensile. Deadline scaduta = priorità nel prossimo sprint.
**Regola:** Il debito tecnico invisibile è il debito tecnico che uccide il progetto.
