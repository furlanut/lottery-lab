from __future__ import annotations

"""10eLotto engine generico per K=1-10 numeri + Extra.

Strategia per ogni K: top K numeri piu frequenti nelle ultime W=100 estrazioni.
"""

from collections import Counter
from math import comb

from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA

COSTO = 2.0
W = 100


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


def genera_previsione_k(
    k: int,
    estrazioni_ordinate: list,
) -> list[int]:
    """Genera previsione per K numeri.

    K=6: usa S4 dual-target (3 hot base + 3 hot Extra) — stesso motore di /diecielotto
    Altri K: top K numeri piu frequenti nelle ultime W estrazioni

    Args:
        k: quanti numeri giocare (1-10)
        estrazioni_ordinate: lista di oggetti con .numeri e .numeri_extra property

    Returns:
        lista di K numeri ordinati
    """
    window = estrazioni_ordinate[-W:] if len(estrazioni_ordinate) >= W else estrazioni_ordinate

    if k == 6:
        # S4 dual-target: 3 hot base + 3 hot Extra (coerente con /diecielotto)
        base_freq = Counter()
        extra_freq = Counter()
        for e in window:
            for n in e.numeri:
                base_freq[n] += 1
            for n in e.numeri_extra:
                extra_freq[n] += 1

        hot_base = [n for n, _ in base_freq.most_common(6)]
        hot_extra = [n for n, _ in extra_freq.most_common(20) if n not in hot_base][:3]
        pick = hot_base[:3] + hot_extra[:3]
        if len(pick) < 6:
            for n, _ in base_freq.most_common():
                if n not in pick:
                    pick.append(n)
                if len(pick) >= 6:
                    break
        return sorted(pick[:6])

    # Per tutti gli altri K: top K frequenti nel base
    freq = Counter()
    for e in window:
        for n in e.numeri:
            freq[n] += 1

    return sorted([n for n, _ in freq.most_common(k)])


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
