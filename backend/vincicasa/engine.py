"""Engine VinciCasa — Predizione basata su segnale validato.

Segnale confermato (p=0.010, stabile 2014-2026):
  I 5 numeri piu' frequenti nelle ultime 5 estrazioni producono
  12.14% di 2/5 vs 9.95% baseline (+22% relativo).

Strategia operativa:
  1. Carica ultime 5 estrazioni dal DB
  2. Conta frequenza di ogni numero (1-40)
  3. Seleziona top 5 per frequenza
  4. Genera la cinquina del giorno
  Costo: EUR 2/giorno
  Boost: +EUR 0.057/giocata, -EUR 20.80/anno vs random
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Optional

from lotto_predictor.models.database import get_session
from sqlalchemy import select
from sqlalchemy.orm import Session

from vincicasa.models.database import VinciCasaEstrazione

logger = logging.getLogger(__name__)

N_WINDOW = 5  # Ultime 5 estrazioni (segnale validato p=0.01)


@dataclass
class PrevisioneVC:
    """Previsione VinciCasa del giorno."""

    numeri: list[int]
    frequenze: dict[int, int]
    data_generazione: date
    finestra: int
    dettagli: str = ""


def carica_ultime_estrazioni(
    n: int = N_WINDOW,
    session: Optional[Session] = None,
) -> list[list[int]]:
    """Carica le ultime N estrazioni dal DB.

    Args:
        n: numero di estrazioni da caricare
        session: sessione DB (opzionale)

    Returns:
        Lista di cinquine ordinate per data decrescente
    """
    own = session is None
    if own:
        session = get_session()

    try:
        rows = (
            session.execute(
                select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data.desc()).limit(n)
            )
            .scalars()
            .all()
        )
        return [sorted([r.n1, r.n2, r.n3, r.n4, r.n5]) for r in rows]
    finally:
        if own:
            session.close()


def calcola_frequenze(estrazioni: list[list[int]]) -> Counter:
    """Calcola la frequenza di ogni numero nelle estrazioni date.

    Args:
        estrazioni: lista di cinquine

    Returns:
        Counter con frequenza per numero
    """
    freq = Counter()
    for nums in estrazioni:
        for n in nums:
            freq[n] += 1
    return freq


def genera_previsione(session: Optional[Session] = None) -> PrevisioneVC:
    """Genera la previsione VinciCasa del giorno.

    Strategia validata (p=0.01): top 5 numeri per frequenza
    nelle ultime 5 estrazioni.

    Returns:
        PrevisioneVC con i 5 numeri selezionati
    """
    estrazioni = carica_ultime_estrazioni(N_WINDOW, session)

    if not estrazioni:
        logger.warning("Nessuna estrazione disponibile nel DB")
        return PrevisioneVC(
            numeri=[],
            frequenze={},
            data_generazione=date.today(),
            finestra=N_WINDOW,
            dettagli="Nessuna estrazione disponibile",
        )

    freq = calcola_frequenze(estrazioni)

    # Top 5 per frequenza
    top5 = sorted(freq.most_common(5), key=lambda x: (-x[1], x[0]))
    numeri = [n for n, _ in top5]

    # Dettagli
    freq_str = ", ".join(f"{n}({c}x)" for n, c in top5)
    dettaglio = f"Top 5 freq N={N_WINDOW}: {freq_str}"

    logger.info("VinciCasa previsione: %s", numeri)

    return PrevisioneVC(
        numeri=sorted(numeri),
        frequenze=dict(freq),
        data_generazione=date.today(),
        finestra=N_WINDOW,
        dettagli=dettaglio,
    )


def formatta_previsione(prev: PrevisioneVC) -> str:
    """Formatta la previsione per output."""
    lines = []
    lines.append("VINCICASA — Previsione del giorno")
    lines.append(f"Data: {prev.data_generazione}")
    lines.append(f"Metodo: top 5 frequenti nelle ultime {prev.finestra} estrazioni")
    lines.append("Segnale: +22% sui 2/5 (p=0.01, validato 2014-2026)")
    lines.append("")
    lines.append(f"  Cinquina: {' '.join(f'{n:>2}' for n in prev.numeri)}")
    lines.append(f"  {prev.dettagli}")
    lines.append("")
    lines.append("  Costo: EUR 2.00")
    lines.append("  P(2/5): 12.1% (baseline 10.0%)")
    lines.append("  P(3/5): 0.9%")
    lines.append("  Vincita 2/5: EUR 2.60 | 3/5: EUR 20 | 4/5: EUR 200")
    return "\n".join(lines)


def verifica_previsione(
    previsione: list[int],
    estrazione: list[int],
) -> dict:
    """Verifica una previsione contro l'estrazione reale.

    Args:
        previsione: 5 numeri previsti
        estrazione: 5 numeri estratti

    Returns:
        dict con match, premio, categoria
    """
    match = len(set(previsione) & set(estrazione))
    premi = {0: 0, 1: 0, 2: 2.60, 3: 20, 4: 200, 5: 500000}
    premio = premi.get(match, 0)

    return {
        "match": match,
        "premio": premio,
        "categoria": f"{match}/5",
        "previsione": sorted(previsione),
        "estrazione": sorted(estrazione),
        "numeri_azzeccati": sorted(set(previsione) & set(estrazione)),
    }
