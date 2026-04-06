# Protocollo di Risposta agli Incidenti

Autore: Luca Furlanut

## Severita

| Livello | Descrizione | Tempo risposta |
|---------|-------------|----------------|
| P1 — Critico | Sistema down, dati persi | < 15 minuti |
| P2 — Alto | Funzionalita principale degradata | < 1 ora |
| P3 — Medio | Funzionalita secondaria non disponibile | < 4 ore |
| P4 — Basso | Bug cosmetico, workaround disponibile | < 24 ore |

## Fase 1: DETECT (Rilevamento)

- [ ] Identificare la sorgente dell'allarme (monitoring, utente, log)
- [ ] Verificare che l'incidente sia reale (non falso positivo)
- [ ] Registrare timestamp di inizio incidente
- [ ] Classificare severita (P1-P4)

## Fase 2: TRIAGE (Valutazione)

- [ ] Determinare impatto: quanti utenti/servizi coinvolti?
- [ ] Identificare il componente coinvolto (ingestor, analyzer, predictor, notifier, DB)
- [ ] Verificare se esiste un workaround immediato
- [ ] Decidere: fix immediato o rollback?

## Fase 3: CONTAIN (Contenimento)

- [ ] Se P1/P2: attivare il workaround se disponibile
- [ ] Isolare il componente problematico
- [ ] Comunicare lo stato agli stakeholder
- [ ] Se dati a rischio: bloccare scritture

## Fase 4: FIX (Risoluzione)

- [ ] Identificare root cause
- [ ] Implementare fix
- [ ] Testare fix in staging
- [ ] Applicare fix in produzione
- [ ] Monitorare per 30 minuti

## Fase 5: VERIFY (Verifica)

- [ ] Confermare che il servizio e tornato operativo
- [ ] Verificare integrita dei dati
- [ ] Health check completo (DB, API, notifiche)
- [ ] Confermare che il monitoring non segnala anomalie

## Fase 6: POSTMORTEM (Analisi)

Da completare entro 48 ore dall'incidente:

- [ ] Timeline completa dell'incidente
- [ ] Root cause analysis (5 Whys)
- [ ] Cosa ha funzionato bene
- [ ] Cosa migliorare
- [ ] Action items con deadline e responsabile
- [ ] Lesson Card creata in `docs/lessons/`
- [ ] Aggiornamento runbook se necessario

## Template Postmortem

```
### Incidente: [TITOLO]
**Data:** YYYY-MM-DD
**Severita:** P[1-4]
**Durata:** [dalla detection alla risoluzione]
**Impatto:** [descrizione]

**Timeline:**
- HH:MM — [evento]

**Root Cause:** [analisi]

**Action Items:**
- [ ] [azione] — responsabile — deadline
```
