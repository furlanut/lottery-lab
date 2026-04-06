from __future__ import annotations

"""Servizio di ingestione dati — Lotto Convergent.

Coordina il parsing dei file e l'inserimento nel database
con deduplicazione automatica (UNIQUE su data+ruota).
"""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from lotto_predictor.ingestor.csv_import import parse_file_csv
from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.models.database import Estrazione, get_session

logger = logging.getLogger(__name__)


def inserisci_estrazioni(session: Session, records: list[dict]) -> dict:
    """Inserisce estrazioni nel database con deduplicazione.

    Usa INSERT ... ON CONFLICT DO NOTHING per evitare duplicati.

    Args:
        session: sessione database
        records: lista di dizionari da inserire

    Returns:
        Dizionario con statistiche: inseriti, duplicati, errori
    """
    inseriti = 0
    duplicati = 0
    errori = 0

    for record in records:
        try:
            stmt = (
                pg_insert(Estrazione)
                .values(
                    concorso=record["concorso"],
                    data=record["data"],
                    ruota=record["ruota"],
                    n1=record["numeri"][0],
                    n2=record["numeri"][1],
                    n3=record["numeri"][2],
                    n4=record["numeri"][3],
                    n5=record["numeri"][4],
                )
                .on_conflict_do_nothing(constraint="uq_data_ruota")
            )
            result = session.execute(stmt)

            if result.rowcount > 0:
                inseriti += 1
            else:
                duplicati += 1
        except Exception as e:
            errori += 1
            logger.error("Errore inserimento: %s — %s", record, e)

    session.commit()

    stats = {"inseriti": inseriti, "duplicati": duplicati, "errori": errori}
    logger.info(
        "Inserimento completato: %d inseriti, %d duplicati, %d errori",
        inseriti,
        duplicati,
        errori,
    )
    return stats


def importa_csv(filepath: str | Path, session: Session | None = None) -> dict:
    """Importa estrazioni da un file CSV.

    Args:
        filepath: percorso del file CSV
        session: sessione database (opzionale, ne crea una nuova se None)

    Returns:
        Statistiche di importazione
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        records = parse_file_csv(Path(filepath))
        stats = inserisci_estrazioni(session, records)
        stats["file"] = str(filepath)
        stats["records_parsati"] = len(records)
        return stats
    finally:
        if own_session:
            session.close()


def importa_txt(filepath: str | Path, session: Session | None = None) -> dict:
    """Importa estrazioni da un file TXT dell'archivio.

    Args:
        filepath: percorso del file TXT
        session: sessione database (opzionale)

    Returns:
        Statistiche di importazione
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        records = parse_file_txt(Path(filepath))
        stats = inserisci_estrazioni(session, records)
        stats["file"] = str(filepath)
        stats["records_parsati"] = len(records)
        return stats
    finally:
        if own_session:
            session.close()


def importa_archivio_completo(
    directory: str | Path,
    session: Session | None = None,
    anno_inizio: int | None = None,
    anno_fine: int | None = None,
) -> dict:
    """Importa tutto l'archivio TXT da una directory.

    Args:
        directory: percorso della directory con i file TXT
        session: sessione database (opzionale)
        anno_inizio: anno di partenza (opzionale, incluso)
        anno_fine: anno di fine (opzionale, incluso)

    Returns:
        Statistiche aggregate di importazione
    """
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        files = scan_archivio_txt(Path(directory))

        # Filtra per anno se specificato
        if anno_inizio or anno_fine:
            filtered = []
            for f in files:
                # Estrai anno dal nome file
                anno = int(f.stem.split("-")[-1])
                if anno_inizio and anno < anno_inizio:
                    continue
                if anno_fine and anno > anno_fine:
                    continue
                filtered.append(f)
            files = filtered

        totale_inseriti = 0
        totale_duplicati = 0
        totale_errori = 0
        totale_parsati = 0

        for filepath in files:
            records = parse_file_txt(filepath)
            stats = inserisci_estrazioni(session, records)
            totale_inseriti += stats["inseriti"]
            totale_duplicati += stats["duplicati"]
            totale_errori += stats["errori"]
            totale_parsati += len(records)

        risultato = {
            "file_processati": len(files),
            "records_parsati": totale_parsati,
            "inseriti": totale_inseriti,
            "duplicati": totale_duplicati,
            "errori": totale_errori,
        }

        logger.info(
            "Importazione archivio completata: %d file, %d inseriti, %d duplicati",
            len(files),
            totale_inseriti,
            totale_duplicati,
        )
        return risultato
    finally:
        if own_session:
            session.close()


def conta_estrazioni(session: Session | None = None) -> int:
    """Conta il numero totale di estrazioni nel database."""
    own_session = session is None
    if own_session:
        session = get_session()

    try:
        result = session.execute(select(Estrazione.id)).all()
        return len(result)
    finally:
        if own_session:
            session.close()
