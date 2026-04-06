# Checklist Migration Safety

Da completare OGNI VOLTA che lo schema del database viene modificato.

## Pre-Migration

- [ ] Migration scritta e testata in locale
- [ ] Migration reversibile (rollback script presente)
- [ ] Nessun dato perso nella migrazione
- [ ] Indici necessari creati
- [ ] Vincoli di integrita preservati
- [ ] Default values per colonne NOT NULL su tabelle con dati
- [ ] Nessun lock prolungato su tabelle grandi
- [ ] Query di verifica pre/post migration preparate

## Deploy Order

- [ ] 1. Backup database completo
- [ ] 2. Eseguire migration su staging
- [ ] 3. Verificare dati su staging
- [ ] 4. Eseguire migration su produzione
- [ ] 5. Verificare dati su produzione
- [ ] 6. Monitorare errori per 30 minuti

## Post-Migration

- [ ] Dati integri (query di verifica passano)
- [ ] Nessun errore nei log
- [ ] Performance accettabile (query plan controllato)
- [ ] ORM/modelli aggiornati per riflettere nuovo schema
- [ ] Documentazione DB aggiornata nel manuale tecnico
- [ ] Migration committata nel repository
