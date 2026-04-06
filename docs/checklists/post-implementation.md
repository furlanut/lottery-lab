# Checklist Post-Implementazione

Da eseguire DOPO OGNI feature. Non saltare MAI nessuno step.

## 1. Build e Lint
- [ ] `ruff check .` passa senza errori
- [ ] `ruff format --check .` passa senza errori
- [ ] `cd frontend && npm run build` compila senza errori (se frontend toccato)

## 2. Check Correttezza
- [ ] Nessun import mancante
- [ ] Nessun errore di tipizzazione
- [ ] Query DB sicure (parametri bind, no SQL injection)
- [ ] Nessun debug output rimasto (print, console.log, breakpoint)
- [ ] Nessun secret hardcoded

## 3. Check Coerenza
- [ ] Tipi frontend <-> backend matchano
- [ ] Route registrate correttamente
- [ ] Servizi registrati nel dependency injection
- [ ] Formato errori conforme all'Error Contract

## 4. Check Consistenza
- [ ] Niente rotto nelle funzionalita esistenti
- [ ] Cache invalidata dove necessario
- [ ] Backward compatibility mantenuta

## 5. Migration Safety (se schema DB toccato)
- [ ] Completare `docs/checklists/migration-safety.md`

## 6. Accessibility (se frontend toccato)
- [ ] Navigazione da tastiera funziona
- [ ] HTML semantico (heading, landmark, label)
- [ ] Contrasto colori >= 4.5:1
- [ ] Focus visibile su elementi interattivi

## 7. API Docs (se endpoint nuovi/modificati)
- [ ] Endpoint documentato
- [ ] Esempi request/response aggiornati
- [ ] Codici errore documentati

## 8. Documentazione (se funzionalita cambiate)
- [ ] Manuale tecnico aggiornato (`docs/TECHNICAL_MANUAL.md`)
- [ ] Manuale utente aggiornato (`docs/USER_MANUAL.md`)

## 9. Deploy Staging
- [ ] `./deploy.sh staging` eseguito con successo
- [ ] Health check OK
- [ ] Notifica inviata
