# Error Contract — Lotto Convergent

## Formato Standard

Tutte le risposte di errore dell'API seguono questo formato (ispirato a RFC 7807):

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Descrizione leggibile dall'utente",
    "details": [],
    "request_id": "req_abc123def456"
  }
}
```

### Campi

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|-------------|-------------|
| `error.code` | string | Si | Codice macchina-leggibile, UPPER_SNAKE_CASE |
| `error.message` | string | Si | Messaggio leggibile, localizzabile |
| `error.details` | array | No | Dettagli aggiuntivi (es. errori di validazione per campo) |
| `error.request_id` | string | Si | ID univoco della richiesta per tracing |

### HTTP Status Code Mapping

| Status | Quando | Esempio code |
|--------|--------|-------------|
| 400 | Input non valido | `VALIDATION_FAILED`, `INVALID_PAYLOAD` |
| 401 | Non autenticato | `AUTH_REQUIRED`, `TOKEN_EXPIRED` |
| 403 | Non autorizzato | `FORBIDDEN`, `INSUFFICIENT_SCOPE` |
| 404 | Risorsa non trovata | `NOT_FOUND`, `{RESOURCE}_NOT_FOUND` |
| 409 | Conflitto | `ALREADY_EXISTS`, `CONFLICT` |
| 422 | Semanticamente non valido | `UNPROCESSABLE`, `BUSINESS_RULE_VIOLATION` |
| 429 | Rate limit | `RATE_LIMITED` |
| 500 | Errore interno | `INTERNAL_ERROR` |
| 503 | Servizio non disponibile | `SERVICE_UNAVAILABLE` |

### Errore di Validazione (details)

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "I dati inviati non sono validi",
    "details": [
      { "field": "email", "code": "INVALID_FORMAT", "message": "Formato email non valido" },
      { "field": "password", "code": "TOO_SHORT", "message": "Minimo 8 caratteri" }
    ],
    "request_id": "req_abc123"
  }
}
```

### Regole

1. **Mai stack trace nelle risposte** — loggalo server-side, non mostrarlo al client
2. **Sempre request_id** — permette di correlare errore client con log server
3. **message sempre user-friendly** — il frontend puo mostrarlo direttamente
4. **code sempre machine-friendly** — il frontend puo fare switch/mapping
5. **Stesso formato per TUTTI gli endpoint** — inclusi auth, webhook, etc.
6. **Il frontend ha un singolo error handler** — basato su status + code
