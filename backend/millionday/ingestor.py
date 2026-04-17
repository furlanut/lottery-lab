"""Ingestor MillionDay — due fonti dati.

1. Retroattivo: import da backend/millionday/data/archive_2022_2026.json
   (2.607 estrazioni parsate da millionday.cloud).

2. Live: fetch periodico di millionday.cloud/archivio-estrazioni.php
   per catturare nuove estrazioni (usa lo stesso parser regex di parse_cloud.py).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, time
from pathlib import Path
from typing import Any, Optional

import httpx
from lotto_predictor.models.database import get_session
from sqlalchemy import select
from sqlalchemy.orm import Session

from millionday.models.database import MillionDayEstrazione

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_JSON = DATA_DIR / "archive_2022_2026.json"
CLOUD_URL = "https://www.millionday.cloud/archivio-estrazioni.php"

MESI_IT = {
    "Gennaio": "01", "Febbraio": "02", "Marzo": "03", "Aprile": "04",
    "Maggio": "05", "Giugno": "06", "Luglio": "07", "Agosto": "08",
    "Settembre": "09", "Ottobre": "10", "Novembre": "11", "Dicembre": "12",
}

_ROW_RE = re.compile(
    r'<tr>\s*<td><span class="testo_arancione">([^<]+)</span>\s*ore\s*(\d{2}:\d{2})</td>'
    r"(.*?)</tr>",
    re.DOTALL,
)
_NUM_BASE_RE = re.compile(r"<td>\s*(\d{1,2})\s*</td>")
_NUM_EXTRA_RE = re.compile(r'<td><span style="color:#088796">\s*(\d{1,2})\s*</span></td>')
_DATE_RE = re.compile(
    r"(?:Lun|Mar|Mer|Gio|Ven|Sab|Dom)[a-zìù]*\s+(\d{1,2})\s+(\w+)\s+(\d{4})"
)


def parse_html_archive(html: str) -> list[dict]:
    """Estrae tutte le estrazioni dall'HTML millionday.cloud."""
    estrazioni = []
    for m in _ROW_RE.finditer(html):
        data_str = m.group(1).strip()
        ora_str = m.group(2).strip()
        body = m.group(3)

        d = _DATE_RE.search(data_str)
        if not d:
            continue
        day, mese_nome, year = d.group(1), d.group(2), d.group(3)
        mese = MESI_IT.get(mese_nome)
        if not mese:
            continue
        iso_date = f"{year}-{mese}-{int(day):02d}"

        bases = [int(x) for x in _NUM_BASE_RE.findall(body)]
        extras = [int(x) for x in _NUM_EXTRA_RE.findall(body)]

        if len(bases) != 5 or len(extras) != 5:
            continue
        if not all(1 <= n <= 55 for n in bases + extras):
            continue

        estrazioni.append({"data": iso_date, "ora": ora_str, "numeri": bases, "extra": extras})
    return estrazioni


def fetch_cloud() -> list[dict]:
    """Scarica millionday.cloud e restituisce la lista delle estrazioni parsate."""
    resp = httpx.get(
        CLOUD_URL,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    resp.raise_for_status()
    return parse_html_archive(resp.text)


def _record_to_model(rec: dict) -> MillionDayEstrazione:
    """Converte un dict {data, ora, numeri, extra} in MillionDayEstrazione."""
    y, m, d = rec["data"].split("-")
    h, mi = rec["ora"].split(":")
    nums = sorted(rec["numeri"])
    extras = sorted(rec["extra"])
    return MillionDayEstrazione(
        data=date(int(y), int(m), int(d)),
        ora=time(int(h), int(mi)),
        n1=nums[0], n2=nums[1], n3=nums[2], n4=nums[3], n5=nums[4],
        e1=extras[0], e2=extras[1], e3=extras[2], e4=extras[3], e5=extras[4],
    )


def inserisci_estrazioni(
    session: Session,
    records: list[dict],
    log_every: int = 500,
) -> dict[str, int]:
    """Inserisce estrazioni nel DB con deduplicazione su (data, ora).

    Returns:
        {"inseriti": int, "duplicati": int, "errori": int}
    """
    stats = {"inseriti": 0, "duplicati": 0, "errori": 0}

    # Carica esistenti in bulk per deduplicazione rapida
    existing = set()
    for row in session.execute(
        select(MillionDayEstrazione.data, MillionDayEstrazione.ora)
    ).all():
        existing.add((row[0], row[1]))

    for i, rec in enumerate(records):
        try:
            y, m, d = rec["data"].split("-")
            h, mi = rec["ora"].split(":")
            key = (date(int(y), int(m), int(d)), time(int(h), int(mi)))
            if key in existing:
                stats["duplicati"] += 1
                continue
            session.add(_record_to_model(rec))
            existing.add(key)
            stats["inseriti"] += 1

            if log_every > 0 and stats["inseriti"] % log_every == 0:
                logger.info("  ... %d inseriti", stats["inseriti"])
                session.flush()
        except Exception as e:
            stats["errori"] += 1
            logger.warning("Errore record %d: %s", i, e)

    session.commit()
    return stats


def import_retroattivo(session: Optional[Session] = None) -> dict[str, int]:
    """Import one-shot del file archive_2022_2026.json (2.607 estrazioni)."""
    own = session is None
    if own:
        session = get_session()
    try:
        if not ARCHIVE_JSON.exists():
            raise FileNotFoundError(f"Archivio non trovato: {ARCHIVE_JSON}")
        raw: list[dict[str, Any]] = json.loads(ARCHIVE_JSON.read_text())
        logger.info("Import retroattivo: %d estrazioni dal file", len(raw))
        stats = inserisci_estrazioni(session, raw)
        logger.info(
            "Completato: inseriti=%d duplicati=%d errori=%d",
            stats["inseriti"], stats["duplicati"], stats["errori"],
        )
        return stats
    finally:
        if own:
            session.close()


def aggiorna_da_cloud(session: Optional[Session] = None) -> dict[str, int]:
    """Scarica millionday.cloud e inserisce eventuali nuove estrazioni."""
    own = session is None
    if own:
        session = get_session()
    try:
        records = fetch_cloud()
        logger.info("Scaricate %d estrazioni da millionday.cloud", len(records))
        stats = inserisci_estrazioni(session, records, log_every=0)
        if stats["inseriti"] > 0:
            logger.info("MillionDay: +%d nuove estrazioni", stats["inseriti"])
        return stats
    finally:
        if own:
            session.close()


if __name__ == "__main__":
    # CLI: python -m millionday.ingestor [retroactive|cloud]
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    mode = sys.argv[1] if len(sys.argv) > 1 else "retroactive"
    if mode == "retroactive":
        import_retroattivo()
    elif mode == "cloud":
        aggiorna_da_cloud()
    else:
        print(f"Modo sconosciuto: {mode}. Usa 'retroactive' o 'cloud'.")
        sys.exit(1)
