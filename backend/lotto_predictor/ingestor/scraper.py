from __future__ import annotations

"""Scraper estrazioni Lotto Italiano — Lotto Convergent.

Scarica le estrazioni piu recenti da archivioestrazionilotto.it.
Parsing HTML basato su regex (struttura tabellare molto regolare).

Struttura HTML target:
    <tr><td class="sin"><a href="/ruota-bari.html">Bari</a></td>
    <td><a href="/numero-80.html">80</a></td>
    <td><a href="/numero-54.html">54</a></td>
    ...
    </tr>
"""

import logging
import re
import time
from datetime import date, datetime

import httpx

from lotto_predictor.config import settings
from lotto_predictor.ingestor.validator import (
    ValidationError,
    valida_numeri,
    valida_ruota,
)

logger = logging.getLogger(__name__)

# ---- Costanti ----

# Le 10 ruote che ci interessano (escludendo Nazionale)
RUOTE_SCRAPING = [
    "BARI",
    "CAGLIARI",
    "FIRENZE",
    "GENOVA",
    "MILANO",
    "NAPOLI",
    "PALERMO",
    "ROMA",
    "TORINO",
    "VENEZIA",
]

# Mappa nomi ruote dal sito (capitalizzati) ai nostri nomi (maiuscolo)
_RUOTA_MAP = {r.capitalize(): r for r in RUOTE_SCRAPING}
_RUOTA_MAP["Nazionale"] = "NAZIONALE"

# Pattern regex per estrarre concorso e data dalla homepage
# Es: "Estrazione n&ordm; 56 di marted&igrave;" + value="07/04/2026"
_RE_CONCORSO = re.compile(
    r"Estrazione\s+n(?:&ordm;|°|º)\s*(\d+)",
    re.IGNORECASE,
)
_RE_DATA_INPUT = re.compile(
    r'<input[^>]+name="data_estr"[^>]+value="(\d{2}/\d{2}/\d{4})"',
    re.IGNORECASE,
)

# Pattern per una riga della tabella estrazioni
# Cattura: nome ruota e 5 numeri
_RE_RIGA_ESTRAZIONE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>\s*<a[^>]*>(\w+)</a>\s*</td>\s*"
    r"<td[^>]*>\s*<a[^>]*>(\d+)</a>\s*</td>\s*"
    r"<td[^>]*>\s*<a[^>]*>(\d+)</a>\s*</td>\s*"
    r"<td[^>]*>\s*<a[^>]*>(\d+)</a>\s*</td>\s*"
    r"<td[^>]*>\s*<a[^>]*>(\d+)</a>\s*</td>\s*"
    r"<td[^>]*>\s*<a[^>]*>(\d+)</a>\s*</td>",
    re.IGNORECASE,
)

# Headers HTTP per le richieste
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


# ---- Eccezioni ----


class ScraperError(Exception):
    """Errore generico dello scraper."""

    pass


class ScraperHTTPError(ScraperError):
    """Errore HTTP durante lo scraping."""

    def __init__(self, status_code: int, url: str):
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP {status_code} per {url}")


class ScraperParseError(ScraperError):
    """Errore nel parsing dell'HTML."""

    pass


# ---- Funzioni principali ----


def scarica_ultima_estrazione(
    base_url: str | None = None,
    max_tentativi: int | None = None,
    delay_secondi: float | None = None,
) -> dict:
    """Scarica l'ultima estrazione dalla homepage del sito.

    Effettua una GET alla homepage, che mostra sempre l'estrazione
    piu recente. Parsing con regex della tabella HTML.

    Args:
        base_url: URL base del sito (default da config).
        max_tentativi: numero massimo di tentativi (default da config).
        delay_secondi: secondi di attesa tra tentativi (default da config).

    Returns:
        Dict con:
            - 'concorso': int (numero del concorso)
            - 'data': date (data dell'estrazione)
            - 'data_str': str (data in formato dd/mm/yyyy)
            - 'ruote': dict[str, list[int]] (ruota -> [n1, n2, n3, n4, n5])

    Raises:
        ScraperError: se lo scraping fallisce dopo tutti i tentativi.
    """
    url = base_url or settings.scraper_base_url
    tentativi = max_tentativi or settings.scraper_retry
    delay = delay_secondi or settings.scraper_delay

    html = _fetch_con_retry(url, tentativi=tentativi, delay=delay)
    return _parse_pagina_estrazione(html)


def scarica_estrazione_per_data(
    data: date,
    base_url: str | None = None,
    max_tentativi: int | None = None,
    delay_secondi: float | None = None,
) -> dict:
    """Scarica l'estrazione di una data specifica.

    Usa il form POST del sito per caricare l'estrazione di una data.

    Args:
        data: data dell'estrazione da cercare.
        base_url: URL base del sito (default da config).
        max_tentativi: numero massimo di tentativi (default da config).
        delay_secondi: secondi di attesa tra tentativi (default da config).

    Returns:
        Dict con concorso, data, data_str, ruote (come scarica_ultima_estrazione).

    Raises:
        ScraperError: se lo scraping fallisce.
    """
    url = base_url or settings.scraper_base_url
    tentativi = max_tentativi or settings.scraper_retry
    delay = delay_secondi or settings.scraper_delay

    data_str = data.strftime("%d/%m/%Y")
    form_url = f"{url.rstrip('/')}/estrazione.php"

    html = _fetch_con_retry(
        form_url,
        tentativi=tentativi,
        delay=delay,
        method="POST",
        data={"data_estr": data_str},
    )
    return _parse_pagina_estrazione(html)


# ---- Funzioni interne ----


def _fetch_con_retry(
    url: str,
    tentativi: int = 3,
    delay: float = 2.0,
    method: str = "GET",
    data: dict | None = None,
) -> str:
    """Effettua una richiesta HTTP con retry e backoff esponenziale.

    Args:
        url: URL da scaricare.
        tentativi: numero massimo di tentativi.
        delay: secondi di attesa iniziale tra tentativi (raddoppia ad ogni retry).
        method: metodo HTTP (GET o POST).
        data: dati per richieste POST.

    Returns:
        Contenuto HTML della pagina.

    Raises:
        ScraperHTTPError: se tutti i tentativi falliscono con errore HTTP.
        ScraperError: per errori di connessione.
    """
    last_error: Exception | None = None
    current_delay = delay

    for attempt in range(1, tentativi + 1):
        try:
            logger.info(
                "Tentativo %d/%d: %s %s",
                attempt,
                tentativi,
                method,
                url,
            )

            with httpx.Client(
                headers=_HEADERS,
                follow_redirects=True,
                timeout=httpx.Timeout(30.0),
            ) as client:
                response = client.post(url, data=data) if method == "POST" else client.get(url)

            response.raise_for_status()

            logger.info(
                "Risposta OK (%d bytes)",
                len(response.text),
            )
            return response.text

        except httpx.HTTPStatusError as e:
            last_error = ScraperHTTPError(e.response.status_code, url)
            logger.warning(
                "Tentativo %d: HTTP %d per %s",
                attempt,
                e.response.status_code,
                url,
            )
        except httpx.TimeoutException as e:
            last_error = ScraperError(f"Timeout per {url}: {e}")
            logger.warning("Tentativo %d: timeout per %s", attempt, url)
        except httpx.ConnectError as e:
            last_error = ScraperError(f"Connessione fallita per {url}: {e}")
            logger.warning("Tentativo %d: connessione fallita per %s", attempt, url)

        # Attesa con backoff esponenziale (non dopo l'ultimo tentativo)
        if attempt < tentativi:
            logger.info("Attesa %.1f secondi prima del prossimo tentativo...", current_delay)
            time.sleep(current_delay)
            current_delay *= 2

    raise last_error or ScraperError(f"Scraping fallito dopo {tentativi} tentativi")


def _parse_pagina_estrazione(html: str) -> dict:
    """Parsa l'HTML di una pagina estrazione.

    Estrae numero concorso, data, e i 5 numeri per ciascuna delle 10 ruote.

    Args:
        html: contenuto HTML della pagina.

    Returns:
        Dict con concorso, data, data_str, ruote.

    Raises:
        ScraperParseError: se il parsing fallisce.
    """
    # Estrai numero concorso
    match_concorso = _RE_CONCORSO.search(html)
    if not match_concorso:
        raise ScraperParseError("Impossibile trovare il numero del concorso nell'HTML")
    concorso = int(match_concorso.group(1))

    # Estrai data dall'input hidden
    match_data = _RE_DATA_INPUT.search(html)
    if not match_data:
        raise ScraperParseError("Impossibile trovare la data dell'estrazione nell'HTML")
    data_str = match_data.group(1)

    try:
        data_estrazione = datetime.strptime(data_str, "%d/%m/%Y").date()
    except ValueError as e:
        raise ScraperParseError(f"Data non valida: {data_str}") from e

    # Estrai righe della tabella (ruota + 5 numeri)
    matches = _RE_RIGA_ESTRAZIONE.findall(html)
    if not matches:
        raise ScraperParseError("Nessuna riga di estrazione trovata nell'HTML")

    ruote: dict[str, list[int]] = {}
    for match in matches:
        nome_ruota_raw = match[0]
        numeri_raw = match[1:6]

        # Mappa nome ruota dal sito al nostro formato
        nome_ruota = _RUOTA_MAP.get(nome_ruota_raw)
        if nome_ruota is None:
            logger.warning("Ruota non riconosciuta: '%s', ignorata", nome_ruota_raw)
            continue

        # Ignoriamo la Nazionale
        if nome_ruota == "NAZIONALE":
            continue

        numeri = [int(n) for n in numeri_raw]

        # Validazione numeri
        try:
            valida_numeri(numeri)
            valida_ruota(nome_ruota)
        except ValidationError as e:
            raise ScraperParseError(f"Dati non validi per ruota {nome_ruota}: {e}") from e

        ruote[nome_ruota] = numeri

    # Verifica che abbiamo tutte le 10 ruote
    ruote_mancanti = set(RUOTE_SCRAPING) - set(ruote.keys())
    if ruote_mancanti:
        raise ScraperParseError(f"Ruote mancanti nell'estrazione: {sorted(ruote_mancanti)}")

    risultato = {
        "concorso": concorso,
        "data": data_estrazione,
        "data_str": data_str,
        "ruote": ruote,
    }

    logger.info(
        "Estrazione #%d del %s parsata: %d ruote",
        concorso,
        data_str,
        len(ruote),
    )
    return risultato


def scarica_ultime_n_estrazioni(
    n: int = 5,
    base_url: str | None = None,
) -> list[dict]:
    """Scarica le ultime N estrazioni navigando all'indietro.

    Utile per aggiornare il database con piu estrazioni mancanti.

    Args:
        n: numero di estrazioni da scaricare.
        base_url: URL base del sito.

    Returns:
        Lista di dict (come scarica_ultima_estrazione), dalla piu recente
        alla piu vecchia.

    Raises:
        ScraperError: se lo scraping fallisce.
    """
    # Scarica dalla homepage (ultima estrazione) e poi usa il form POST
    # per navigare indietro nel tempo
    from lotto_predictor.ingestor.schedule import giorni_estrazione_precedenti

    estrazioni: list[dict] = []

    # Prima l'ultima
    ultima = scarica_ultima_estrazione(base_url=base_url)
    estrazioni.append(ultima)

    if n <= 1:
        return estrazioni

    # Calcola le date precedenti
    date_precedenti = giorni_estrazione_precedenti(
        da_data=ultima["data"],
        n=n - 1,
    )

    for data_target in date_precedenti:
        try:
            estrazione = scarica_estrazione_per_data(data_target, base_url=base_url)
            estrazioni.append(estrazione)
            # Rate limiting: rispettiamo il server
            time.sleep(settings.scraper_delay)
        except ScraperError as e:
            logger.warning(
                "Impossibile scaricare estrazione del %s: %s",
                data_target,
                e,
            )

    return estrazioni
