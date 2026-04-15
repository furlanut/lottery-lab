from __future__ import annotations

"""Scraper 10eLotto ogni 5 minuti.

Scarica estrazioni dal JSON endpoint di 10elotto5.it.
L'endpoint restituisce le ultime ~15 estrazioni live.
Per accumulare dati storici, eseguire il polling ogni 5 minuti.

Ogni estrazione contiene: 20 numeri, Numero Oro (1° estratto),
Doppio Oro (2° estratto), e 15 numeri Extra.
"""

import logging
import time as time_module
from datetime import date, time

import httpx

logger = logging.getLogger(__name__)

# Endpoint JSON scoperto su 10elotto5.it (WordPress theme)
LIVE_ENDPOINT = (
    "https://www.10elotto5.it/wp-content/themes/"
    "twentysixteen-child/10elotto5/estrazioni10elotto5.php"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class ScraperError(Exception):
    """Errore durante lo scraping."""


def scarica_ultime_estrazioni(retry: int = 3, delay: float = 2.0) -> list[dict]:
    """Scarica le ultime estrazioni live dal JSON endpoint.

    L'endpoint restituisce ~15 estrazioni recenti con tutti i dati:
    20 numeri, Numero Oro, Doppio Oro, 15 Extra.

    Returns:
        Lista di dict con chiavi: concorso, data, ora, numeri (list[int] len 20),
        numero_oro (int), doppio_oro (int), numeri_extra (list[int] len 15)
    """
    for attempt in range(retry):
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(LIVE_ENDPOINT, headers=HEADERS)
                resp.raise_for_status()
                data = resp.json()

            estrazioni_raw = data.get("estrazioni", [])
            if not estrazioni_raw:
                logger.warning("Nessuna estrazione nell'endpoint")
                return []

            return [_parse_estrazione(e) for e in estrazioni_raw]

        except Exception as e:
            logger.warning("Tentativo %d/%d fallito: %s", attempt + 1, retry, e)
            if attempt < retry - 1:
                time_module.sleep(delay)

    msg = "Impossibile scaricare estrazioni dopo tutti i tentativi"
    raise ScraperError(msg)


def _parse_estrazione(raw: dict) -> dict:
    """Converte un record JSON in formato standard.

    Input JSON keys: nestr, data, ora, c1-c20, Oro, dOro, e1-e15
    """
    # Numeri principali (c1-c20)
    numeri = [int(raw[f"c{i}"]) for i in range(1, 21)]

    # Extra (e1-e15)
    numeri_extra = []
    for i in range(1, 16):
        val = raw.get(f"e{i}")
        if val is not None and str(val).strip():
            numeri_extra.append(int(val))

    # Data e ora
    data_str = raw["data"]
    ora_str = raw["ora"]

    # Parse data (formato YYYY-MM-DD)
    data_parsed = date.fromisoformat(data_str)

    # Parse ora (formato HH:MM:SS)
    parts = ora_str.split(":")
    ora_parsed = time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

    return {
        "concorso": int(raw.get("nestr", 0)),
        "data": data_parsed,
        "ora": ora_parsed,
        "numeri": sorted(numeri),
        "numero_oro": int(raw["Oro"]),
        "doppio_oro": int(raw["dOro"]),
        "numeri_extra": sorted(numeri_extra) if numeri_extra else [],
    }


def scarica_e_accumula(
    intervallo_secondi: int = 300,
    max_cicli: int = 288,
) -> list[dict]:
    """Polling continuo dell'endpoint per accumulare estrazioni.

    Scarica ogni 5 minuti (default) e accumula, deduplicando per data+ora.

    Args:
        intervallo_secondi: secondi tra un polling e l'altro (default 300 = 5 min)
        max_cicli: numero massimo di cicli (default 288 = 1 giorno)

    Returns:
        Lista deduplicata di tutte le estrazioni accumulate
    """
    tutte: dict[str, dict] = {}  # key = "data_ora"

    for ciclo in range(max_cicli):
        try:
            batch = scarica_ultime_estrazioni()
            nuove = 0
            for e in batch:
                key = f"{e['data']}_{e['ora']}"
                if key not in tutte:
                    tutte[key] = e
                    nuove += 1

            logger.info(
                "Ciclo %d/%d: %d nuove estrazioni (totale: %d)",
                ciclo + 1,
                max_cicli,
                nuove,
                len(tutte),
            )

        except ScraperError as err:
            logger.error("Errore ciclo %d: %s", ciclo + 1, err)

        if ciclo < max_cicli - 1:
            time_module.sleep(intervallo_secondi)

    return list(tutte.values())
