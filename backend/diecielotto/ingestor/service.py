from __future__ import annotations

"""Servizio ingestione 10eLotto — Lottery Lab.

Coordina scraper e inserimento nel database
con deduplicazione automatica (UNIQUE su data+ora).
"""

import logging
from datetime import date
from typing import Optional

from lotto_predictor.models.database import get_session
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from diecielotto.models.database import DiecieLottoEstrazione

logger = logging.getLogger(__name__)


def inserisci_estrazioni(session: Session, records: list[dict]) -> dict:
    """Inserisce estrazioni 10eLotto nel database con deduplicazione.

    Usa INSERT ... ON CONFLICT DO NOTHING sul vincolo uq_del_data_ora.
    """
    inseriti = 0
    duplicati = 0
    errori = 0

    for record in records:
        try:
            numeri = record["numeri"]  # list of 20 sorted
            extras = record.get("numeri_extra", [])

            values: dict = {
                "concorso": record.get("concorso", 0),
                "data": record["data"],
                "ora": record["ora"],
                "numero_oro": record["numero_oro"],
                "doppio_oro": record["doppio_oro"],
            }

            # Add n1..n20
            for i, n in enumerate(numeri[:20], 1):
                values[f"n{i}"] = n

            # Add extra_1..extra_15
            for i in range(1, 16):
                values[f"extra_{i}"] = extras[i - 1] if i <= len(extras) else None

            stmt = (
                pg_insert(DiecieLottoEstrazione)
                .values(**values)
                .on_conflict_do_nothing(constraint="uq_del_data_ora")
            )
            result = session.execute(stmt)

            if result.rowcount > 0:
                inseriti += 1
            else:
                duplicati += 1
        except Exception as e:
            errori += 1
            logger.error("Errore inserimento 10eLotto: %s — %s", record, e)

    session.commit()

    stats = {"inseriti": inseriti, "duplicati": duplicati, "errori": errori}
    logger.info(
        "10eLotto — inserimento: %d inseriti, %d duplicati, %d errori",
        inseriti,
        duplicati,
        errori,
    )
    return stats


def importa_da_scraper(
    data: Optional[date] = None,
    session: Optional[Session] = None,
) -> dict:
    """Importa estrazioni 10eLotto via scraper web."""
    from diecielotto.ingestor.scraper import scarica_estrazioni_giorno

    own = session is None
    if own:
        session = get_session()

    try:
        target = data or date.today()
        records = scarica_estrazioni_giorno(target)
        stats = inserisci_estrazioni(session, records)
        stats["records_scaricati"] = len(records)
        stats["data"] = str(target)
        return stats
    finally:
        if own:
            session.close()


def conta_estrazioni(session: Optional[Session] = None) -> int:
    """Conta il numero totale di estrazioni 10eLotto nel database."""
    own = session is None
    if own:
        session = get_session()
    try:
        return session.execute(select(func.count(DiecieLottoEstrazione.id))).scalar() or 0
    finally:
        if own:
            session.close()


def ultima_estrazione(
    session: Optional[Session] = None,
) -> Optional[DiecieLottoEstrazione]:
    """Ritorna l'ultima estrazione 10eLotto nel database."""
    own = session is None
    if own:
        session = get_session()
    try:
        return session.execute(
            select(DiecieLottoEstrazione)
            .order_by(
                DiecieLottoEstrazione.data.desc(),
                DiecieLottoEstrazione.ora.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()
    finally:
        if own:
            session.close()
