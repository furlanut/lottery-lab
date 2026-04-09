from __future__ import annotations

"""Scraper estrazioni VinciCasa — Lottery Lab.

Scarica le estrazioni storiche da tuttosuperenalotto.it.
Struttura HTML target:
    <table>
      <tr><td><a href="...">08/04/2026</a></td>
          <td>02 - 10 - 24 - 31 - 38</td></tr>
    </table>

Fonte alternativa: xamig.com (tabella con concorso esplicito).
"""

import logging
import re
import time
from datetime import date, datetime

import httpx

from vincicasa.config import vc_settings

logger = logging.getLogger(__name__)

# ---- Costanti ----

# URL base dell'archivio annuale (tutti i concorsi di un anno in una pagina)
_ARCHIVIO_URL = "https://www.tuttosuperenalotto.it/vincicasa-archivio-estrazioni-1.asp?a={anno}"

# Pattern per riga della tabella: data (dd/mm/yyyy) e cinquina (NN - NN - NN - NN - NN)
_RE_RIGA = re.compile(
    r"<td[^>]*>\s*<a[^>]*>\s*(\d{2}/\d{2}/\d{4})\s*</a>\s*</td>"
    r"\s*<td[^>]*>\s*"
    r"(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})"
    r"\s*</td>",
    re.IGNORECASE,
)

# Headers HTTP realistici
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

# Anno di inizio VinciCasa
ANNO_INIZIO = 2014


# ---- Eccezioni ----


class VCScraperError(Exception):
    """Errore generico dello scraper VinciCasa."""


class VCScraperHTTPError(VCScraperError):
    """Errore HTTP durante lo scraping."""

    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP {status_code} per {url}")


class VCScraperParseError(VCScraperError):
    """Errore nel parsing dell'HTML."""


# ---- Funzioni principali ----


def scarica_estrazioni_anno(
    anno: int,
    max_tentativi: int | None = None,
    delay_secondi: float | None = None,
) -> list[dict]:
    """Scarica tutte le estrazioni VinciCasa di un anno.

    La pagina archivio di tuttosuperenalotto.it elenca tutti i concorsi
    di un anno in una sola tabella HTML, senza paginazione.

    Args:
        anno: anno da scaricare (>= 2014).
        max_tentativi: numero massimo di tentativi HTTP (default da config).
        delay_secondi: secondi di attesa tra tentativi (default da config).

    Returns:
        Lista di dict con:
            - 'data': date
            - 'n1'...'n5': int (i 5 numeri estratti)

    Raises:
        VCScraperError: se lo scraping fallisce dopo tutti i tentativi.
        ValueError: se l'anno e fuori range.
    """
    if anno < ANNO_INIZIO:
        raise ValueError(f"VinciCasa inizia nel {ANNO_INIZIO}, anno richiesto: {anno}")

    url = _ARCHIVIO_URL.format(anno=anno)
    tentativi = max_tentativi or vc_settings.scraper_retry
    delay = delay_secondi or vc_settings.scraper_delay

    html = _fetch_con_retry(url, tentativi=tentativi, delay=delay)
    return _parse_pagina_archivio(html, anno)


def scarica_archivio_completo(
    anno_inizio: int = ANNO_INIZIO,
    anno_fine: int | None = None,
    delay_tra_anni: float = 3.0,
) -> list[dict]:
    """Scarica tutto l'archivio VinciCasa, anno per anno.

    Args:
        anno_inizio: primo anno da scaricare (default: 2014).
        anno_fine: ultimo anno (default: anno corrente).
        delay_tra_anni: secondi di pausa tra una richiesta annuale e l'altra.

    Returns:
        Lista completa di dict (come scarica_estrazioni_anno),
        ordinata dalla piu vecchia alla piu recente.

    Raises:
        VCScraperError: se lo scraping di un anno fallisce.
    """
    if anno_fine is None:
        anno_fine = date.today().year

    tutte: list[dict] = []

    for anno in range(anno_inizio, anno_fine + 1):
        logger.info("Scaricamento estrazioni VinciCasa anno %d...", anno)
        estrazioni = scarica_estrazioni_anno(anno)
        tutte.extend(estrazioni)
        logger.info("Anno %d: %d estrazioni scaricate", anno, len(estrazioni))

        # Rate limiting: rispettiamo il server
        if anno < anno_fine:
            time.sleep(delay_tra_anni)

    # Ordina per data crescente
    tutte.sort(key=lambda e: e["data"])

    logger.info(
        "Archivio completo: %d estrazioni (%d-%d)",
        len(tutte),
        anno_inizio,
        anno_fine,
    )
    return tutte


def scarica_ultime_estrazioni(
    n: int = 10,
) -> list[dict]:
    """Scarica le ultime N estrazioni VinciCasa.

    Scarica l'anno corrente e, se necessario, l'anno precedente
    per ottenere almeno N risultati.

    Args:
        n: numero di estrazioni desiderate.

    Returns:
        Lista di dict (come scarica_estrazioni_anno), dalla piu recente
        alla piu vecchia, troncata a N elementi.
    """
    anno_corrente = date.today().year
    estrazioni = scarica_estrazioni_anno(anno_corrente)

    # Se l'anno corrente non ha abbastanza estrazioni, aggiungi l'anno precedente
    if len(estrazioni) < n and anno_corrente > ANNO_INIZIO:
        logger.info(
            "Anno %d ha solo %d estrazioni, scarico anche %d",
            anno_corrente,
            len(estrazioni),
            anno_corrente - 1,
        )
        time.sleep(vc_settings.scraper_delay)
        precedenti = scarica_estrazioni_anno(anno_corrente - 1)
        estrazioni = precedenti + estrazioni

    # Ordina per data decrescente e tronca a N
    estrazioni.sort(key=lambda e: e["data"], reverse=True)
    return estrazioni[:n]


# ---- Funzioni interne ----


def _fetch_con_retry(
    url: str,
    tentativi: int = 3,
    delay: float = 2.0,
) -> str:
    """Effettua una GET HTTP con retry e backoff esponenziale.

    Args:
        url: URL da scaricare.
        tentativi: numero massimo di tentativi.
        delay: secondi di attesa iniziale (raddoppia ad ogni retry).

    Returns:
        Contenuto HTML della pagina.

    Raises:
        VCScraperHTTPError: se tutti i tentativi falliscono con errore HTTP.
        VCScraperError: per errori di connessione/timeout.
    """
    last_error: Exception | None = None
    current_delay = delay

    for attempt in range(1, tentativi + 1):
        try:
            logger.info("Tentativo %d/%d: GET %s", attempt, tentativi, url)

            with httpx.Client(
                headers=_HEADERS,
                follow_redirects=True,
                timeout=httpx.Timeout(30.0),
            ) as client:
                response = client.get(url)

            response.raise_for_status()

            logger.info("Risposta OK (%d bytes)", len(response.text))
            return response.text

        except httpx.HTTPStatusError as e:
            last_error = VCScraperHTTPError(e.response.status_code, url)
            logger.warning(
                "Tentativo %d: HTTP %d per %s",
                attempt,
                e.response.status_code,
                url,
            )
        except httpx.TimeoutException as e:
            last_error = VCScraperError(f"Timeout per {url}: {e}")
            logger.warning("Tentativo %d: timeout per %s", attempt, url)
        except httpx.ConnectError as e:
            last_error = VCScraperError(f"Connessione fallita per {url}: {e}")
            logger.warning("Tentativo %d: connessione fallita per %s", attempt, url)

        # Attesa con backoff esponenziale (non dopo l'ultimo tentativo)
        if attempt < tentativi:
            logger.info(
                "Attesa %.1f secondi prima del prossimo tentativo...",
                current_delay,
            )
            time.sleep(current_delay)
            current_delay *= 2

    raise last_error or VCScraperError(f"Scraping fallito dopo {tentativi} tentativi")


def _parse_pagina_archivio(html: str, anno: int) -> list[dict]:
    """Parsa l'HTML dell'archivio annuale VinciCasa.

    Estrae data e 5 numeri da ogni riga della tabella.
    Il numero di concorso viene calcolato dall'ordine cronologico
    (la fonte non lo espone direttamente).

    Args:
        html: contenuto HTML della pagina.
        anno: anno di riferimento (per logging).

    Returns:
        Lista di dict con data e numeri, ordinata per data crescente.

    Raises:
        VCScraperParseError: se il parsing fallisce.
    """
    matches = _RE_RIGA.findall(html)
    if not matches:
        raise VCScraperParseError(f"Nessuna estrazione trovata nell'HTML per l'anno {anno}")

    estrazioni: list[dict] = []

    for match in matches:
        data_str = match[0]
        numeri_raw = match[1:6]

        # Parsing data
        try:
            data_estrazione = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError as e:
            logger.warning("Data non valida '%s', riga ignorata: %s", data_str, e)
            continue

        # Parsing numeri
        numeri = [int(n) for n in numeri_raw]

        # Validazione range 1-40
        if not all(1 <= n <= 40 for n in numeri):
            logger.warning(
                "Numeri fuori range per %s: %s, riga ignorata",
                data_str,
                numeri,
            )
            continue

        # Validazione unicita numeri
        if len(set(numeri)) != 5:
            logger.warning(
                "Numeri duplicati per %s: %s, riga ignorata",
                data_str,
                numeri,
            )
            continue

        estrazioni.append(
            {
                "data": data_estrazione,
                "n1": numeri[0],
                "n2": numeri[1],
                "n3": numeri[2],
                "n4": numeri[3],
                "n5": numeri[4],
            }
        )

    # Ordina per data crescente
    estrazioni.sort(key=lambda e: e["data"])

    logger.info(
        "Anno %d: %d estrazioni parsate dall'HTML",
        anno,
        len(estrazioni),
    )
    return estrazioni
