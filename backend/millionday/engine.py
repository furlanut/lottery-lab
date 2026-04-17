"""Engine MillionDay — Predizione con strategia optfreq W=60 + Extra.

Strategia selezionata dopo deep analysis (10 fasi, ~50 configurazioni testate):
  - optfreq W=60: top 5 numeri con frequenza piu vicina all'attesa
    (ne troppo caldi ne troppo freddi) nelle ultime 60 estrazioni (~1 mese).
  - Ratio validation: 1.343x (discovery coerente 1.404x).
  - Permutation test p=0.0495 (borderline, FAIL Bonferroni 20 test).
  - Opzione Extra: HE marginale 32.2% (migliore del base 35.2%).

Costo giocata: EUR 2 (1 base + 1 Extra). Breakeven 1.508x.

IMPORTANTE: il sistema NON e profittevole (ratio 1.343 < breakeven 1.508).
E semplicemente la strategia meno-peggio fra quelle testate su 2.607 estrazioni.
Per dettagli vedi backend/millionday/DEEP_REPORT.md.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from lotto_predictor.models.database import get_session
from sqlalchemy import select
from sqlalchemy.orm import Session

from millionday.models.database import MillionDayEstrazione

logger = logging.getLogger(__name__)

# Finestra predittiva ottimale (60 estrazioni ~= 1 mese con 2 estr/giorno)
N_WINDOW = 60

# Payout netti (tassazione 8% gia applicata, da regolamento ADM 2026)
PREMI_BASE = {0: 0.0, 1: 0.0, 2: 2.0, 3: 50.0, 4: 1000.0, 5: 1_000_000.0}
PREMI_EXTRA = {0: 0.0, 1: 0.0, 2: 4.0, 3: 100.0, 4: 1000.0, 5: 100_000.0}

COSTO_BASE = 1.0
COSTO_EXTRA = 1.0
COSTO_TOTALE = 2.0

# Caratteristiche del segnale (backtest su 2.607 estrazioni, split 50/50)
SCORE_BACKTEST = 1.343  # ratio validation
HE_TOTALE = 33.69  # % house edge con Extra


@dataclass
class PrevisioneMD:
    """Previsione MillionDay del turno (per estrazione 13:00 o 20:30)."""

    numeri: list[int]
    frequenze: dict[int, int]
    expected: float  # frequenza attesa per numero su W estrazioni
    data_generazione: date
    finestra: int
    dettagli: str = ""


def carica_ultime_estrazioni(
    n: int = N_WINDOW,
    session: Optional[Session] = None,
) -> list[MillionDayEstrazione]:
    """Carica le ultime N estrazioni dal DB, ordine cronologico desc."""
    own = session is None
    if own:
        session = get_session()
    try:
        rows = (
            session.execute(
                select(MillionDayEstrazione)
                .order_by(MillionDayEstrazione.data.desc(), MillionDayEstrazione.ora.desc())
                .limit(n)
            )
            .scalars()
            .all()
        )
        return list(rows)
    finally:
        if own:
            session.close()


def calcola_frequenze(estrazioni: list[MillionDayEstrazione]) -> Counter:
    """Calcola la frequenza di ciascun numero nelle estrazioni date (solo base)."""
    freq = Counter()
    for e in estrazioni:
        for n in e.numeri:
            freq[n] += 1
    return freq


def _pick_optfreq(freq: Counter, window_size: int) -> list[int]:
    """Top 5 numeri con frequenza piu vicina al valore atteso.

    Sotto uniformita, attesa = window_size * 5/55.
    Selezione: sort per |freq - expected|, poi per numero (tie-break).
    """
    expected = window_size * 5 / 55
    return sorted(
        range(1, 56),
        key=lambda x: (abs(freq.get(x, 0) - expected), x),
    )[:5]


def genera_previsione(session: Optional[Session] = None) -> PrevisioneMD:
    """Genera la previsione MillionDay del prossimo turno.

    Strategia optfreq W=60: top 5 numeri con frequenza piu vicina all'attesa.

    Returns:
        PrevisioneMD con i 5 numeri selezionati.
    """
    estrazioni = carica_ultime_estrazioni(N_WINDOW, session)

    if len(estrazioni) < 10:
        logger.warning("Troppe poche estrazioni MillionDay nel DB (%d)", len(estrazioni))
        return PrevisioneMD(
            numeri=[],
            frequenze={},
            expected=0.0,
            data_generazione=date.today(),
            finestra=N_WINDOW,
            dettagli="Dati insufficienti",
        )

    window_size = len(estrazioni)
    freq = calcola_frequenze(estrazioni)
    expected = window_size * 5 / 55
    numeri = _pick_optfreq(freq, window_size)

    # Dettagli: per ciascun numero giocato, quanto e vicino all'attesa
    freq_str = ", ".join(f"{n}({freq.get(n, 0)}x vs {expected:.1f})" for n in numeri)
    dettaglio = f"optfreq W={window_size}: {freq_str}"

    logger.info("MillionDay previsione optfreq W=%d: %s", window_size, numeri)

    return PrevisioneMD(
        numeri=numeri,
        frequenze=dict(freq),
        expected=expected,
        data_generazione=date.today(),
        finestra=window_size,
        dettagli=dettaglio,
    )


def formatta_previsione(prev: PrevisioneMD) -> str:
    """Formatta la previsione per output testo."""
    lines = []
    lines.append("MILLIONDAY — Previsione del turno")
    lines.append(f"Data: {prev.data_generazione}")
    lines.append(f"Metodo: optfreq W={prev.finestra} (miglior sistema da deep analysis)")
    lines.append(f"Score backtest: {SCORE_BACKTEST:.3f}x (breakeven 1.508x — sotto)")
    lines.append("")
    lines.append(f"  Cinquina: {' '.join(f'{n:>2}' for n in prev.numeri)}")
    lines.append(f"  {prev.dettagli}")
    lines.append("")
    lines.append(f"  Costo: EUR {COSTO_TOTALE:.2f} (1 base + 1 Extra)")
    lines.append(f"  House edge: {HE_TOTALE:.2f}%")
    lines.append("  P(vincere base): 5.99% (~1 in 17)")
    lines.append("  Premi base (netti): 2/5=EUR 2 | 3/5=EUR 50 | 4/5=EUR 1.000 | 5/5=EUR 1M")
    lines.append("  Premi Extra: 2/5=EUR 4 | 3/5=EUR 100 | 4/5=EUR 1.000 | 5/5=EUR 100k")
    return "\n".join(lines)


def verifica_previsione(
    previsione: list[int],
    numeri_base: list[int],
    numeri_extra: list[int],
) -> dict:
    """Verifica una previsione contro l'estrazione reale.

    Args:
        previsione: 5 numeri giocati
        numeri_base: 5 numeri estratti nella base
        numeri_extra: 5 numeri estratti nell'Extra (dai 50 rimanenti)

    Returns:
        dict con match_base, match_extra, vincita_base, vincita_extra, totale
    """
    pick = set(previsione)
    base = set(numeri_base)
    extra = set(numeri_extra)

    match_base = len(pick & base)
    rimanenti = pick - base
    match_extra = len(rimanenti & extra)

    vincita_base = PREMI_BASE.get(match_base, 0.0)
    vincita_extra = PREMI_EXTRA.get(match_extra, 0.0)
    totale = vincita_base + vincita_extra

    return {
        "match_base": match_base,
        "match_extra": match_extra,
        "vincita_base": vincita_base,
        "vincita_extra": vincita_extra,
        "vincita": totale,
        "costo": COSTO_TOTALE,
        "pnl": totale - COSTO_TOTALE,
        "categoria": f"{match_base}/5" + (f" + {match_extra}/5E" if match_extra > 0 else ""),
    }


def genera_previsione_retroattiva(
    estrazioni_precedenti: list[MillionDayEstrazione],
) -> list[int]:
    """Genera una previsione retroattiva usando solo le estrazioni precedenti.

    Utile per paper trading storico: "cosa avrebbe predetto il sistema alla data X?"

    Args:
        estrazioni_precedenti: lista cronologica di estrazioni disponibili prima del turno.

    Returns:
        Lista di 5 numeri predetti. Vuota se dati insufficienti.
    """
    if len(estrazioni_precedenti) < 10:
        return []

    # Usa le ultime N_WINDOW estrazioni precedenti
    window = estrazioni_precedenti[-N_WINDOW:]
    freq = calcola_frequenze(window)
    return _pick_optfreq(freq, len(window))


# Data e ora "ore italiane" — MillionDay estrae alle 13:00 e 20:30
ORARI_ESTRAZIONE = [time(13, 0), time(20, 30)]


def prossima_estrazione() -> tuple[date, time]:
    """Calcola data e ora della prossima estrazione MillionDay."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Europe/Rome"))
    current = now.time()
    today = now.date()

    for ora in ORARI_ESTRAZIONE:
        if current < ora:
            return today, ora
    # Dopo l'ultimo turno di oggi: prima estrazione domani
    from datetime import timedelta

    return today + timedelta(days=1), ORARI_ESTRAZIONE[0]
