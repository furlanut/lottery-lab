from __future__ import annotations

"""Generatore previsioni — Lotto Convergent.

Produce previsioni basate sull'analisi di convergenza.
Supporta sia il caricamento da CSV (uso standalone / backtest)
sia il caricamento da database (uso integrato nel servizio).
"""

import csv
import logging
from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from lotto_predictor.analyzer.convergence import calcola_convergenza
from lotto_predictor.analyzer.cyclometry import RUOTE
from lotto_predictor.config import settings
from lotto_predictor.models.database import Estrazione, Previsione

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Caricamento dati
# ---------------------------------------------------------------------------

def carica_dati_csv(filepath: str) -> list[tuple[str, dict[str, list[int]]]]:
    """Carica i dati storici da un file CSV.

    Il CSV deve avere le colonne: data, ruota, n1, n2, n3, n4, n5.
    I dati vengono raggruppati per data e restituiti nel formato
    atteso dall'analizzatore di convergenza.

    Args:
        filepath: percorso del file CSV.

    Returns:
        Lista di tuple (data, {ruota: [n1..n5]}) ordinate per data crescente.
    """
    # Raggruppa le righe per data
    by_date: dict[str, dict[str, list[int]]] = defaultdict(dict)

    with open(filepath, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            data_str = row["data"]
            ruota = row["ruota"].upper().strip()
            numeri = [
                int(row["n1"]),
                int(row["n2"]),
                int(row["n3"]),
                int(row["n4"]),
                int(row["n5"]),
            ]
            by_date[data_str][ruota] = numeri

    # Ordina per data crescente e costruisci la lista finale
    dati: list[tuple[str, dict[str, list[int]]]] = [
        (d, wheels) for d, wheels in sorted(by_date.items())
    ]
    logger.info("Caricate %d estrazioni da CSV: %s", len(dati), filepath)
    return dati


def carica_dati_db(session: Session) -> list[tuple[str, dict[str, list[int]]]]:
    """Carica i dati storici dal database.

    Legge tutte le estrazioni ordinate per data e le raggruppa
    nel formato atteso dall'analizzatore di convergenza.

    Args:
        session: sessione SQLAlchemy attiva.

    Returns:
        Lista di tuple (data, {ruota: [n1..n5]}) ordinate per data crescente.
    """
    rows = (
        session.query(Estrazione)
        .order_by(Estrazione.data, Estrazione.ruota)
        .all()
    )

    by_date: dict[str, dict[str, list[int]]] = defaultdict(dict)
    for est in rows:
        data_str = est.data.isoformat()
        by_date[data_str][est.ruota] = est.numeri

    dati: list[tuple[str, dict[str, list[int]]]] = [
        (d, wheels) for d, wheels in sorted(by_date.items())
    ]
    logger.info("Caricate %d estrazioni dal database", len(dati))
    return dati


# ---------------------------------------------------------------------------
# Generazione previsioni
# ---------------------------------------------------------------------------

def genera_previsioni(
    dati: list[tuple[str, dict[str, list[int]]]],
    min_score: int = 3,
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """Genera previsioni per tutte le ruote sull'ultima estrazione.

    Analizza l'ultima estrazione nel dataset, esegue ``calcola_convergenza``
    per ciascuna ruota, raccoglie tutti i segnali, li ordina per score
    decrescente e restituisce i migliori ``top_n`` risultati.

    Args:
        dati: dati storici nel formato (data, {ruota: [n1..n5]}).
        min_score: punteggio minimo di convergenza per includere un segnale.
        top_n: numero massimo di previsioni da restituire.

    Returns:
        Lista di dizionari con chiavi:
            - ruota (str)
            - ambo (tuple[int, int])
            - score (int)
            - filtri (list[str])
            - dettagli (list[str])
    """
    if not dati:
        logger.warning("Nessun dato disponibile per generare previsioni")
        return []

    # Indice dell'ultima estrazione
    indice_ultima = len(dati) - 1

    # Raccolta segnali da tutte le ruote
    all_signals: list[dict[str, Any]] = []

    for ruota in RUOTE:
        segnali = calcola_convergenza(
            dati,
            indice_estrazione=indice_ultima,
            ruota=ruota,
            min_score=min_score,
            soglia_ritardo=settings.filter_ritardo_soglia,
            soglia_ritardo_diametrale=settings.filter_s91_ritardo_diametrale,
        )
        for seg in segnali:
            all_signals.append({
                "ruota": seg.ruota,
                "ambo": seg.ambo,
                "score": seg.score,
                "filtri": seg.filtri,
                "dettagli": seg.dettagli,
            })

    # Ordina per score decrescente
    all_signals.sort(key=lambda s: -s["score"])

    risultati = all_signals[:top_n]
    logger.info(
        "Generate %d previsioni (min_score=%d, top_n=%d)",
        len(risultati),
        min_score,
        top_n,
    )
    return risultati


# ---------------------------------------------------------------------------
# Persistenza previsioni
# ---------------------------------------------------------------------------

def salva_previsioni(
    session: Session,
    previsioni: list[dict[str, Any]],
    data_generazione: date | None = None,
    data_target_inizio: date | None = None,
) -> list[Previsione]:
    """Salva le previsioni nel database.

    Crea un record ``Previsione`` per ogni elemento della lista e
    li inserisce nella sessione.

    Args:
        session: sessione SQLAlchemy attiva.
        previsioni: lista di dizionari generati da ``genera_previsioni``.
        data_generazione: data di generazione (default: oggi).
        data_target_inizio: prima data utile di gioco (default: oggi).

    Returns:
        Lista dei record ``Previsione`` creati.
    """
    oggi = date.today()
    data_gen = data_generazione or oggi
    data_target = data_target_inizio or oggi

    records: list[Previsione] = []
    for prev in previsioni:
        record = Previsione(
            data_generazione=data_gen,
            data_target_inizio=data_target,
            ruota=prev["ruota"],
            num_a=prev["ambo"][0],
            num_b=prev["ambo"][1],
            score=prev["score"],
            filtri={"filtri": prev["filtri"], "dettagli": prev["dettagli"]},
            max_colpi=settings.max_colpi,
            posta=settings.posta_default,
            stato="ATTIVA",
        )
        session.add(record)
        records.append(record)

    session.flush()
    logger.info("Salvate %d previsioni nel database", len(records))
    return records
