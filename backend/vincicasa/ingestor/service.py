from __future__ import annotations

"""Servizio ingestione VinciCasa — Lottery Lab.

Coordina scraper/CSV e inserimento nel database
con deduplicazione automatica (UNIQUE su concorso).
"""

import logging
from datetime import date
from pathlib import Path

from lotto_predictor.models.database import get_session
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from vincicasa.ingestor.csv_import import parse_csv_vincicasa
from vincicasa.ingestor.scraper import (
    scarica_archivio_completo,
    scarica_estrazioni_anno,
    scarica_ultime_estrazioni,
)
from vincicasa.models.database import VinciCasaEstrazione

logger = logging.getLogger(__name__)


def _calcola_concorso(data_estrazione: date, session: Session) -> int:
    """Calcola il numero di concorso per una data estrazione.

    VinciCasa ha estrazioni giornaliere dal 09/07/2014.
    Il concorso riparte da 1 ogni anno solare.

    Se il DB contiene gia estrazioni dello stesso anno, usa il max+1.
    Altrimenti conta i giorni dall'inizio dell'anno (approssimazione).

    Args:
        data_estrazione: data dell'estrazione.
        session: sessione database.

    Returns:
        Numero di concorso stimato.
    """
    anno = data_estrazione.year

    # Cerca il massimo concorso gia presente per quell'anno
    max_concorso = session.execute(
        select(func.max(VinciCasaEstrazione.concorso)).where(
            func.extract("year", VinciCasaEstrazione.data) == anno,
            VinciCasaEstrazione.data < data_estrazione,
        )
    ).scalar()

    if max_concorso is not None:
        return max_concorso + 1

    # Fallback: conta le estrazioni gia presenti nello stesso anno + 1
    count = session.execute(
        select(func.count(VinciCasaEstrazione.id)).where(
            func.extract("year", VinciCasaEstrazione.data) == anno,
            VinciCasaEstrazione.data < data_estrazione,
        )
    ).scalar()

    return (count or 0) + 1


def inserisci_estrazioni(
    session: Session,
    records: list[dict],
    calcola_concorso: bool = False,
) -> dict:
    """Inserisce estrazioni VinciCasa nel database con deduplicazione.

    Usa INSERT ... ON CONFLICT DO NOTHING sul vincolo uq_vc_concorso
    per evitare duplicati.

    Args:
        session: sessione database.
        records: lista di dizionari con chiavi data, n1..n5,
                 e opzionalmente concorso.
        calcola_concorso: se True, calcola il concorso automaticamente
                          quando non presente nel record.

    Returns:
        Dizionario con statistiche: inseriti, duplicati, errori.
    """
    inseriti = 0
    duplicati = 0
    errori = 0

    for record in records:
        try:
            # Se il record non ha il concorso, calcolalo
            concorso = record.get("concorso")
            if concorso is None or concorso == 0:
                concorso = (
                    _calcola_concorso(record["data"], session)
                    if calcola_concorso
                    else 0
                )

            stmt = (
                pg_insert(VinciCasaEstrazione)
                .values(
                    concorso=concorso,
                    data=record["data"],
                    n1=record["n1"],
                    n2=record["n2"],
                    n3=record["n3"],
                    n4=record["n4"],
                    n5=record["n5"],
                )
                .on_conflict_do_nothing(constraint="uq_vc_data")
            )
            result = session.execute(stmt)

            if result.rowcount > 0:
                inseriti += 1
            else:
                duplicati += 1
        except Exception as e:
            errori += 1
            logger.error("Errore inserimento VinciCasa: %s — %s", record, e)

    session.commit()

    stats = {"inseriti": inseriti, "duplicati": duplicati, "errori": errori}
    logger.info(
        "VinciCasa — inserimento completato: %d inseriti, %d duplicati, %d errori",
        inseriti,
        duplicati,
        errori,
    )
    return stats


def importa_da_scraper(
    anno: int | None = None,
    session: Session | None = None,
) -> dict:
    """Importa estrazioni VinciCasa via scraper web.

    Se anno e specificato, scarica solo quell'anno.
    Se anno e None, scarica l'anno corrente (aggiornamento incrementale).

    Args:
        anno: anno da scaricare (None = anno corrente).
        session: sessione database (ne crea una nuova se None).

    Returns:
        Statistiche di importazione.
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        if anno is not None:
            records = scarica_estrazioni_anno(anno)
        else:
            records = scarica_ultime_estrazioni(n=30)

        stats = inserisci_estrazioni(session, records)
        stats["records_scaricati"] = len(records)
        return stats
    finally:
        if own_session:
            session.close()


def importa_archivio_completo_web(
    anno_inizio: int = 2014,
    anno_fine: int | None = None,
    session: Session | None = None,
) -> dict:
    """Importa l'intero archivio VinciCasa via scraper, anno per anno.

    Args:
        anno_inizio: primo anno da scaricare.
        anno_fine: ultimo anno (default: anno corrente).
        session: sessione database (ne crea una nuova se None).

    Returns:
        Statistiche aggregate di importazione.
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        records = scarica_archivio_completo(
            anno_inizio=anno_inizio,
            anno_fine=anno_fine,
        )
        stats = inserisci_estrazioni(session, records)
        stats["records_scaricati"] = len(records)
        return stats
    finally:
        if own_session:
            session.close()


def importa_csv(
    filepath: str | Path,
    session: Session | None = None,
) -> dict:
    """Importa estrazioni VinciCasa da un file CSV.

    Args:
        filepath: percorso del file CSV.
        session: sessione database (ne crea una nuova se None).

    Returns:
        Statistiche di importazione.
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        records = parse_csv_vincicasa(Path(filepath))
        stats = inserisci_estrazioni(session, records)
        stats["file"] = str(filepath)
        stats["records_parsati"] = len(records)
        return stats
    finally:
        if own_session:
            session.close()


def conta_estrazioni(session: Session | None = None) -> int:
    """Conta il numero totale di estrazioni VinciCasa nel database."""
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        result = session.execute(select(func.count(VinciCasaEstrazione.id))).scalar()
        return result or 0
    finally:
        if own_session:
            session.close()


def ultima_estrazione(
    session: Session | None = None,
) -> VinciCasaEstrazione | None:
    """Ritorna l'ultima estrazione VinciCasa nel database.

    Returns:
        L'estrazione piu recente o None se il DB e vuoto.
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        result = session.execute(
            select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data.desc()).limit(1)
        ).scalar_one_or_none()
        return result
    finally:
        if own_session:
            session.close()
