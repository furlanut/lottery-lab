"""Motore di convergenza V3 — Lotto Convergent.

Basato sui risultati della validazione con fold scorrevole (metodo corretto).
Ogni segnale usa la SUA finestra ottimale, non una finestra unica.

Classifica segnali (fold scorrevole, ~400 finestre):
  1. freq_rit_fib  W=75:  media 1.159x, 30% sopra breakeven
  2. somma72       W=100: media 1.081x, 25% sopra breakeven
  3. freq_rit_dec  W=125: media 1.024x, 13% sopra breakeven
  4. hot_cold      W=100: media 1.020x, 19% sopra breakeven
  5. freq_rit_fig  W=200: media 1.032x, 12% sopra breakeven
  6. fib_dist      W=50:  media 1.016x,  8% sopra breakeven

Combo testata: dec AND somma72 W=125: media 1.205x, 22% sopra breakeven
  (ma mediana 0.0 — segnali rari e forti)

Specializzazione ruota: ROMA 21-30 W=150: media 1.110x, 20% sopra breakeven
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist

logger = logging.getLogger(__name__)

FIB_DISTS = {1, 2, 3, 5, 8, 13, 21, 34}


@dataclass
class SegnaleV3:
    """Segnale generato dal motore V3."""

    ambo: tuple[int, int]
    ruota: str
    score: float = 0.0
    metodo: str = ""
    frequenza: int = 0
    ritardo: int = 0
    dettagli: str = ""


def _analizza_finestra(dati, idx, ruota, finestra):
    """Calcola features nella finestra per una ruota."""
    pf: Counter = Counter()
    pl: dict = {}
    nf: Counter = Counter()

    for back in range(1, finestra + 1):
        bi = idx - back
        if bi < 0:
            break
        _, bw = dati[bi]
        if ruota not in bw:
            continue
        for n in bw[ruota]:
            nf[n] += 1
        for a, b in combinations(sorted(bw[ruota]), 2):
            pf[(a, b)] += 1
            if (a, b) not in pl:
                pl[(a, b)] = back

    avg_nf = sum(nf.values()) / 90 if nf else 1.0
    return pf, pl, nf, avg_nf


def _figura(n: int) -> int:
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


# ====================================================================
# SEGNALE 1: freq_rit_fib — IL MIGLIORE (W=75, media 1.159x, 30% >1.6)
# Coppia uscita >=2 volte, in ritardo, distanza ciclometrica Fibonacci
# ====================================================================


def segnale_freq_rit_fib(dati, idx, ruota, finestra=75, max_risultati=10):
    """Segnale #1: frequenza + ritardo + distanza Fibonacci.

    Validato fold scorrevole: media 1.159x, 30% finestre sopra breakeven.
    """
    if idx < finestra:
        return []

    pf, pl, _, _ = _analizza_finestra(dati, idx, ruota, finestra)
    soglia_rit = finestra // 3
    risultati = []

    for pair, freq in pf.items():
        if freq < 2:
            continue
        a, b = pair
        last = pl.get(pair, finestra)
        if last < soglia_rit:
            continue
        if cyclo_dist(a, b) not in FIB_DISTS:
            continue

        score = freq + (last / soglia_rit)
        risultati.append(
            SegnaleV3(
                ambo=pair,
                ruota=ruota,
                score=score,
                metodo="freq_rit_fib",
                frequenza=freq,
                ritardo=last,
                dettagli=f"freq={freq},rit={last},dist={cyclo_dist(a, b)}",
            )
        )

    risultati.sort(key=lambda x: -x.score)
    return risultati[:max_risultati]


# ====================================================================
# SEGNALE 2: somma72 — SECONDO (W=100, media 1.081x, 25% >1.6)
# Coppia la cui somma e' 72, frequente e in ritardo
# ====================================================================


def segnale_somma72(dati, idx, ruota, finestra=100, max_risultati=10):
    """Segnale #2: somma 72 + frequenza + ritardo.

    Validato fold scorrevole: media 1.081x, 25% finestre sopra breakeven.
    """
    if idx < finestra:
        return []

    pf, pl, _, _ = _analizza_finestra(dati, idx, ruota, finestra)
    soglia_rit = finestra // 3
    risultati = []

    for pair, freq in pf.items():
        if freq < 1:
            continue
        a, b = pair
        if a + b != 72:
            continue
        last = pl.get(pair, finestra)
        if last < soglia_rit:
            continue

        score = freq + (last / soglia_rit)
        risultati.append(
            SegnaleV3(
                ambo=pair,
                ruota=ruota,
                score=score,
                metodo="somma72",
                frequenza=freq,
                ritardo=last,
                dettagli=f"freq={freq},rit={last},somma=72",
            )
        )

    risultati.sort(key=lambda x: -x.score)
    return risultati[:max_risultati]


# ====================================================================
# SEGNALE 3: freq_rit_dec — (W=125, media 1.024x)
# Coppia stessa decina, frequente e in ritardo
# ====================================================================


def segnale_freq_rit_dec(dati, idx, ruota, finestra=125, max_risultati=10):
    """Segnale #3: frequenza + ritardo + stessa decina.

    Validato fold scorrevole: media 1.024x, 13% finestre sopra breakeven.
    """
    if idx < finestra:
        return []

    pf, pl, _, _ = _analizza_finestra(dati, idx, ruota, finestra)
    soglia_rit = finestra // 3
    risultati = []

    for pair, freq in pf.items():
        if freq < 1:
            continue
        a, b = pair
        if (a - 1) // 10 != (b - 1) // 10:
            continue
        last = pl.get(pair, finestra)
        if last < soglia_rit:
            continue

        score = freq + (last / soglia_rit)
        risultati.append(
            SegnaleV3(
                ambo=pair,
                ruota=ruota,
                score=score,
                metodo="freq_rit_dec",
                frequenza=freq,
                ritardo=last,
                dettagli=f"freq={freq},rit={last},dec={(a - 1) // 10}",
            )
        )

    risultati.sort(key=lambda x: -x.score)
    return risultati[:max_risultati]


# ====================================================================
# SEGNALE 4: hot_cold — (W=100, media 1.020x)
# Un numero caldo + un numero freddo nella finestra
# ====================================================================


def segnale_hot_cold(dati, idx, ruota, finestra=100, max_risultati=10):
    """Segnale #4: un numero caldo + un numero freddo.

    Validato fold scorrevole: media 1.020x, 19% finestre sopra breakeven.
    """
    if idx < finestra:
        return []

    pf, pl, nf, avg_nf = _analizza_finestra(dati, idx, ruota, finestra)
    risultati = []

    for pair, freq in pf.items():
        a, b = pair
        hot_a = nf.get(a, 0) > avg_nf * 1.5
        hot_b = nf.get(b, 0) > avg_nf * 1.5
        cold_a = nf.get(a, 0) < avg_nf * 0.5
        cold_b = nf.get(b, 0) < avg_nf * 0.5

        if not ((hot_a and cold_b) or (hot_b and cold_a)):
            continue

        score = freq + abs(nf.get(a, 0) - nf.get(b, 0)) / avg_nf
        risultati.append(
            SegnaleV3(
                ambo=pair,
                ruota=ruota,
                score=score,
                metodo="hot_cold",
                frequenza=freq,
                ritardo=pl.get(pair, finestra),
                dettagli=f"freq_a={nf.get(a, 0)},freq_b={nf.get(b, 0)},avg={avg_nf:.0f}",
            )
        )

    risultati.sort(key=lambda x: -x.score)
    return risultati[:max_risultati]


# ====================================================================
# SEGNALE COMBO: dec AND somma72 — (W=125, media 1.205x, raro ma forte)
# ====================================================================


def segnale_combo_dec_somma72(dati, idx, ruota, finestra=125, max_risultati=10):
    """Segnale combo: stessa decina AND somma 72.

    Raro (mediana 0 segnali) ma quando appare e' forte (media 1.205x).
    """
    if idx < finestra:
        return []

    pf, pl, _, _ = _analizza_finestra(dati, idx, ruota, finestra)
    soglia_rit = finestra // 3
    risultati = []

    for pair, freq in pf.items():
        if freq < 1:
            continue
        a, b = pair
        is_dec = (a - 1) // 10 == (b - 1) // 10
        is_s72 = a + b == 72
        if not (is_dec and is_s72):
            continue
        last = pl.get(pair, finestra)
        if last < soglia_rit:
            continue

        score = freq * 2 + (last / soglia_rit)  # bonus per doppia convergenza
        risultati.append(
            SegnaleV3(
                ambo=pair,
                ruota=ruota,
                score=score,
                metodo="combo_dec_s72",
                frequenza=freq,
                ritardo=last,
                dettagli=f"freq={freq},rit={last},dec+somma72",
            )
        )

    risultati.sort(key=lambda x: -x.score)
    return risultati[:max_risultati]


# ====================================================================
# GENERATORE PRINCIPALE V3
# ====================================================================


def genera_segnali_v3(
    dati,
    top_n: int = 20,
    ruote: list[str] | None = None,
) -> list[dict]:
    """Genera previsioni V3 con tutti i segnali validati.

    Ogni segnale usa la propria finestra ottimale.
    I risultati sono ordinati per score e metodo.

    Args:
        dati: dati storici (data, {ruota: [n1..n5]})
        top_n: massimo risultati totali
        ruote: lista ruote da analizzare (default: tutte)

    Returns:
        Lista di dizionari ordinata per score decrescente
    """
    if not dati:
        return []

    idx = len(dati) - 1
    target_ruote = ruote or list(RUOTE)
    tutti: list[dict] = []

    for ruota in target_ruote:
        # Segnale 1: freq_rit_fib (W=75) — il migliore
        for s in segnale_freq_rit_fib(dati, idx, ruota):
            tutti.append(_to_dict(s, rank=1))

        # Segnale 2: somma72 (W=100)
        for s in segnale_somma72(dati, idx, ruota):
            tutti.append(_to_dict(s, rank=2))

        # Segnale 3: freq_rit_dec (W=125)
        for s in segnale_freq_rit_dec(dati, idx, ruota):
            tutti.append(_to_dict(s, rank=3))

        # Segnale 4: hot_cold (W=100)
        for s in segnale_hot_cold(dati, idx, ruota):
            tutti.append(_to_dict(s, rank=4))

        # Segnale combo: dec AND somma72 (W=125) — raro
        for s in segnale_combo_dec_somma72(dati, idx, ruota):
            tutti.append(_to_dict(s, rank=0))  # rank 0 = combo speciale

    # Ordina: combo prima, poi per rank del metodo, poi per score
    tutti.sort(key=lambda x: (x["rank"], -x["score"]))

    logger.info("V3: generati %d segnali (top %d)", len(tutti), top_n)
    return tutti[:top_n]


def _to_dict(s: SegnaleV3, rank: int) -> dict:
    return {
        "ruota": s.ruota,
        "ambo": s.ambo,
        "score": s.score,
        "metodo": s.metodo,
        "frequenza": s.frequenza,
        "ritardo": s.ritardo,
        "dettagli": s.dettagli,
        "filtri": [s.metodo],
        "rank": rank,
    }
