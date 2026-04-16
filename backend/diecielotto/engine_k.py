from __future__ import annotations

"""10eLotto engine generico per K=1-10 numeri + Extra.

Motore OTTIMALE per ogni K, basato sui risultati del backtest su 17.082 giocate:
  K=1:  hot_extra      (1.011x) — numero piu frequente nell'Extra
  K=2:  hot_extra      (1.028x) — 2 numeri piu frequenti nell'Extra
  K=3:  freq_rit_dec   (1.040x) — frequenti + in ritardo + stessa decina
  K=4:  dual_target    (1.070x) — 2 hot base + 2 hot Extra
  K=5:  dual_target    (1.024x) — 2 hot base + 3 hot Extra
  K=6:  vicinanza      (1.080x) — numeri vicini al seed piu frequente
  K=7:  dual_target    (1.185x) — 3 hot base + 4 hot Extra
  K=8:  dual_target    (1.445x) — 4 hot base + 4 hot Extra  *** BREAKEVEN ***
  K=9:  dual_target    (1.079x) — 4 hot base + 5 hot Extra
  K=10: dual_target    (0.934x) — 5 hot base + 5 hot Extra
"""

from collections import Counter
from math import comb

from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA

COSTO = 2.0
W = 100

# Mapping K -> (strategy_name, strategy_function_name)
STRATEGY_NAMES = {
    1: "hot_extra",
    2: "hot_extra",
    3: "freq_rit_dec",
    4: "dual_target",
    5: "dual_target",
    6: "vicinanza",
    7: "dual_target",
    8: "dual_target",
    9: "dual_target",
    10: "dual_target",
}


def calcola_he(k: int) -> float:
    """Calcola house edge per K numeri + Extra."""
    premi_b = PREMI_BASE.get(k, {})
    premi_e = PREMI_EXTRA.get(k, {})
    c90_20 = comb(90, 20)
    c70_15 = comb(70, 15)

    ev_base = sum(
        comb(k, m) * comb(90 - k, 20 - m) / c90_20 * premi_b.get(m, 0) for m in range(k + 1)
    )
    ev_extra = 0.0
    for m_base in range(k + 1):
        p_base = comb(k, m_base) * comb(90 - k, 20 - m_base) / c90_20
        remaining = k - m_base
        for m_extra in range(remaining + 1):
            if (70 - remaining) < (15 - m_extra):
                continue
            p_extra = comb(remaining, m_extra) * comb(70 - remaining, 15 - m_extra) / c70_15
            ev_extra += p_base * p_extra * premi_e.get(m_extra, 0)

    ev_tot = ev_base + ev_extra
    return (1 - ev_tot / COSTO) * 100


def _hot_extra(k: int, window: list) -> list[int]:
    """Top K numeri piu frequenti nell'Extra. Ottimale per K=1,2."""
    freq = Counter()
    for e in window:
        for n in e.numeri_extra:
            freq[n] += 1
    return sorted([n for n, _ in freq.most_common(k)])


def _freq_rit_dec(k: int, window: list, idx: int) -> list[int]:
    """Frequenti + in ritardo + decina. Ottimale per K=3."""
    freq = Counter()
    last_seen: dict[int, int] = {}
    for j, e in enumerate(window):
        for n in e.numeri:
            freq[n] += 1
            last_seen[n] = idx - len(window) + j

    rit_soglia = len(window) // 5
    candidates = []
    for n in range(1, 91):
        f = freq.get(n, 0)
        ls = last_seen.get(n, -1)
        rit = idx - ls if ls >= 0 else len(window)
        if f >= 3 and rit >= rit_soglia:
            candidates.append((n, f + rit / len(window) * 3))

    candidates.sort(key=lambda x: -x[1])
    pick = [n for n, _ in candidates[:k]]

    if len(pick) < k:
        for n, _ in freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= k:
                break
    return sorted(pick[:k])


def _dual_target(k: int, window: list) -> list[int]:
    """Meta hot base + meta hot Extra. Ottimale per K=4,5,7,8,9,10."""
    base_freq = Counter()
    extra_freq = Counter()
    for e in window:
        for n in e.numeri:
            base_freq[n] += 1
        for n in e.numeri_extra:
            extra_freq[n] += 1

    half = k // 2
    other = k - half
    hot_base = [n for n, _ in base_freq.most_common(k)][:half]
    hot_extra = [n for n, _ in extra_freq.most_common(k * 2) if n not in hot_base][:other]
    pick = hot_base + hot_extra

    if len(pick) < k:
        for n, _ in base_freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= k:
                break
    return sorted(pick[:k])


def _vicinanza(k: int, window: list) -> list[int]:
    """Numeri vicini al seed piu frequente (D=5). Ottimale per K=6."""
    freq = Counter()
    for e in window:
        for n in e.numeri:
            freq[n] += 1

    seed = freq.most_common(1)[0][0]
    nearby = sorted(
        [
            (n, freq.get(n, 0))
            for n in range(1, 91)
            if abs(n - seed) <= 5 and n != seed and freq.get(n, 0) > 0
        ],
        key=lambda x: -x[1],
    )
    pick = [seed]
    for n, _ in nearby:
        pick.append(n)
        if len(pick) >= k:
            break

    if len(pick) < k:
        for n, _ in freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= k:
                break
    return sorted(pick[:k])


def genera_previsione_k(k: int, estrazioni_ordinate: list) -> list[int]:
    """Genera previsione per K numeri usando il motore OTTIMALE.

    Args:
        k: quanti numeri giocare (1-10)
        estrazioni_ordinate: lista di oggetti con .numeri e .numeri_extra

    Returns:
        lista di K numeri ordinati
    """
    window = estrazioni_ordinate[-W:] if len(estrazioni_ordinate) >= W else estrazioni_ordinate

    strategy = STRATEGY_NAMES.get(k, "dual_target")

    if strategy == "hot_extra":
        return _hot_extra(k, window)
    if strategy == "freq_rit_dec":
        return _freq_rit_dec(k, window, len(estrazioni_ordinate))
    if strategy == "vicinanza":
        return _vicinanza(k, window)
    # default: dual_target
    return _dual_target(k, window)


def verifica_previsione_k(
    k: int,
    previsione: list[int],
    numeri_estratti: list[int],
    numeri_extra: list[int],
) -> dict:
    """Verifica previsione K numeri contro estrazione reale."""
    premi_b = PREMI_BASE.get(k, {})
    premi_e = PREMI_EXTRA.get(k, {})

    pick = set(previsione)
    drawn = set(numeri_estratti)
    extra = set(numeri_extra)

    mb = len(pick & drawn)
    remaining = pick - drawn
    me = len(remaining & extra)

    vb = premi_b.get(mb, 0.0)
    ve = premi_e.get(me, 0.0)
    vincita = vb + ve

    return {
        "match_base": mb,
        "match_extra": me,
        "vincita_base": vb,
        "vincita_extra": ve,
        "vincita_totale": vincita,
        "pnl": vincita - COSTO,
        "numeri_azzeccati": sorted(pick & drawn),
        "numeri_azzeccati_extra": sorted(remaining & extra),
    }
