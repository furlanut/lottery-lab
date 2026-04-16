from __future__ import annotations

"""Backtest strategie specifiche per ogni K (1-10) del 10eLotto.

Per ogni K, testa multiple strategie e identifica la migliore.
Usa le estrazioni reali nel DB.
"""

import logging
from collections import Counter
from math import comb

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA
from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

COSTO = 2.0
W = 100


def _ev_analitico(k: int) -> float:
    """EV analitico per K numeri + Extra."""
    pb = PREMI_BASE.get(k, {})
    pe = PREMI_EXTRA.get(k, {})
    c90 = comb(90, 20)
    c70 = comb(70, 15)
    ev = 0.0
    for m in range(k + 1):
        ev += comb(k, m) * comb(90 - k, 20 - m) / c90 * pb.get(m, 0)
    for mb in range(k + 1):
        p_b = comb(k, mb) * comb(90 - k, 20 - mb) / c90
        rem = k - mb
        for me in range(rem + 1):
            if (70 - rem) < (15 - me):
                continue
            p_e = comb(rem, me) * comb(70 - rem, 15 - me) / c70
            ev += p_b * p_e * pe.get(me, 0)
    return ev


def _vincita(k: int, pick: set, drawn: set, extra: set) -> float:
    """Calcola vincita per K numeri giocati."""
    pb = PREMI_BASE.get(k, {})
    pe = PREMI_EXTRA.get(k, {})
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return pb.get(mb, 0.0) + pe.get(me, 0.0)


# ===================================================================
# STRATEGIE PER OGNI K
# ===================================================================


def strat_hot(k: int, estrazioni: list, idx: int) -> set:
    """Top K numeri piu frequenti nel base."""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            freq[n] += 1
    return {n for n, _ in freq.most_common(k)}


def strat_cold(k: int, estrazioni: list, idx: int) -> set:
    """K numeri meno frequenti (piu freddi) nel base."""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            freq[n] += 1
    all_nums = sorted(range(1, 91), key=lambda x: freq.get(x, 0))
    return set(all_nums[:k])


def strat_vicinanza(k: int, estrazioni: list, idx: int) -> set:
    """Numeri vicini al piu frequente (vicinanza pura, D=5)."""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
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
    pick = {seed}
    for n, _ in nearby:
        pick.add(n)
        if len(pick) >= k:
            break
    if len(pick) < k:
        for n, _ in freq.most_common():
            pick.add(n)
            if len(pick) >= k:
                break
    return set(list(pick)[:k])


def strat_freq_rit_dec(k: int, estrazioni: list, idx: int) -> set:
    """Frequenti + in ritardo + stessa decina (dal paper Lotto)."""
    freq = Counter()
    last_seen = {}
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            freq[n] += 1
            last_seen[n] = j

    candidates = []
    rit_soglia = W // 5
    for n in range(1, 91):
        f = freq.get(n, 0)
        ls = last_seen.get(n, -1)
        rit = idx - ls if ls >= 0 else W
        if f >= 3 and rit >= rit_soglia:
            dec = (n - 1) // 10
            candidates.append((n, f + rit / W * 3, dec))

    candidates.sort(key=lambda x: -x[1])
    pick = set()
    for n, _, _ in candidates:
        pick.add(n)
        if len(pick) >= k:
            break
    if len(pick) < k:
        for n, _ in freq.most_common():
            pick.add(n)
            if len(pick) >= k:
                break
    return set(list(pick)[:k])


def strat_dual_target(k: int, estrazioni: list, idx: int) -> set:
    """S4 dual-target: meta hot base + meta hot Extra."""
    base_freq = Counter()
    extra_freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            base_freq[n] += 1
        for n in estrazioni[j]["extra"]:
            extra_freq[n] += 1

    half = k // 2
    other = k - half
    hot_base = [n for n, _ in base_freq.most_common(k)][:half]
    hot_extra = [n for n, _ in extra_freq.most_common(k * 2) if n not in hot_base][:other]
    pick = set(hot_base + hot_extra)
    if len(pick) < k:
        for n, _ in base_freq.most_common():
            pick.add(n)
            if len(pick) >= k:
                break
    return set(list(pick)[:k])


def strat_anti_cold_for_zero(k: int, estrazioni: list, idx: int) -> set:
    """Per K=7-9: scegli numeri freddi per massimizzare P(0 match).
    Perche 0 match paga 1-2 EUR!"""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            freq[n] += 1
    all_nums = sorted(range(1, 91), key=lambda x: freq.get(x, 0))
    return set(all_nums[:k])


def strat_mix_hot_cold(k: int, estrazioni: list, idx: int) -> set:
    """Meta caldi + meta freddi."""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["numeri"]:
            freq[n] += 1
    hot_half = k // 2
    cold_half = k - hot_half
    hot = [n for n, _ in freq.most_common(hot_half)]
    all_nums = sorted(range(1, 91), key=lambda x: freq.get(x, 0))
    cold = [n for n in all_nums if n not in hot][:cold_half]
    return set(hot + cold)


def strat_hot_extra(k: int, estrazioni: list, idx: int) -> set:
    """Top K numeri piu frequenti nell'Extra."""
    freq = Counter()
    for j in range(max(0, idx - W), idx):
        for n in estrazioni[j]["extra"]:
            freq[n] += 1
    return {n for n, _ in freq.most_common(k)}


# ===================================================================
# STRATEGIE PER OGNI K (mapping)
# ===================================================================

STRATEGIES_PER_K = {
    1: [
        ("hot", strat_hot),
        ("cold", strat_cold),
        ("hot_extra", strat_hot_extra),
    ],
    2: [
        ("hot", strat_hot),
        ("cold", strat_cold),
        ("vicinanza", strat_vicinanza),
        ("hot_extra", strat_hot_extra),
    ],
    3: [
        ("hot", strat_hot),
        ("cold", strat_cold),
        ("vicinanza", strat_vicinanza),
        ("freq_rit_dec", strat_freq_rit_dec),
        ("hot_extra", strat_hot_extra),
    ],
    4: [
        ("hot", strat_hot),
        ("cold", strat_cold),
        ("vicinanza", strat_vicinanza),
        ("freq_rit_dec", strat_freq_rit_dec),
        ("dual_target", strat_dual_target),
    ],
    5: [
        ("hot", strat_hot),
        ("cold", strat_cold),
        ("vicinanza", strat_vicinanza),
        ("freq_rit_dec", strat_freq_rit_dec),
        ("dual_target", strat_dual_target),
    ],
    6: [
        ("hot", strat_hot),
        ("dual_target", strat_dual_target),
        ("vicinanza", strat_vicinanza),
        ("freq_rit_dec", strat_freq_rit_dec),
        ("cold", strat_cold),
    ],
    7: [
        ("hot", strat_hot),
        ("cold_zero", strat_anti_cold_for_zero),
        ("dual_target", strat_dual_target),
        ("mix_hot_cold", strat_mix_hot_cold),
    ],
    8: [
        ("hot", strat_hot),
        ("cold_zero", strat_anti_cold_for_zero),
        ("dual_target", strat_dual_target),
        ("mix_hot_cold", strat_mix_hot_cold),
    ],
    9: [
        ("hot", strat_hot),
        ("cold_zero", strat_anti_cold_for_zero),
        ("dual_target", strat_dual_target),
        ("mix_hot_cold", strat_mix_hot_cold),
    ],
    10: [
        ("hot", strat_hot),
        ("cold_zero", strat_anti_cold_for_zero),
        ("dual_target", strat_dual_target),
        ("mix_hot_cold", strat_mix_hot_cold),
        ("hot_extra", strat_hot_extra),
    ],
}


def run_backtest(k: int, strategy_fn, estrazioni: list, start: int, end: int) -> dict:
    """Esegue backtest per una strategia su un range di estrazioni."""
    total_ev = 0.0
    n_wins = 0
    n_total = 0

    for i in range(start, end):
        pick = strategy_fn(k, estrazioni, i)
        drawn = set(estrazioni[i]["numeri"])
        extra = set(estrazioni[i]["extra"])
        v = _vincita(k, pick, drawn, extra)
        total_ev += v
        if v > 0:
            n_wins += 1
        n_total += 1

    avg_ev = total_ev / n_total if n_total > 0 else 0
    baseline = _ev_analitico(k)
    ratio = avg_ev / baseline if baseline > 0 else 0

    return {
        "avg_ev": avg_ev,
        "baseline": baseline,
        "ratio": ratio,
        "n_total": n_total,
        "n_wins": n_wins,
        "win_rate": n_wins / n_total * 100 if n_total > 0 else 0,
        "pnl": total_ev - n_total * COSTO,
        "he": (1 - avg_ev / COSTO) * 100,
    }


def main():
    print("=" * 75)
    print("10eLOTTO BACKTEST — STRATEGIE SPECIFICHE PER K=1-10")
    print("=" * 75)

    log.info("Caricamento dati...")
    session = get_session()
    rows = (
        session.execute(
            select(DiecieLottoEstrazione).order_by(
                DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
            )
        )
        .scalars()
        .all()
    )
    session.close()

    estrazioni = [{"numeri": r.numeri, "extra": r.numeri_extra} for r in rows]
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")

    if n < W + 50:
        print("Dati insufficienti per backtest")
        return

    # Split: seconda meta per validazione
    half = n // 2
    start = max(W, half)

    print(f"Backtest su estrazioni {start}-{n} ({n - start} giocate)\n")

    best_per_k = {}

    for k in range(1, 11):
        ev_baseline = _ev_analitico(k)
        he_baseline = (1 - ev_baseline / COSTO) * 100
        strategies = STRATEGIES_PER_K.get(k, [("hot", strat_hot)])

        print(f"\n{'=' * 60}")
        print(f"K={k} numeri · EV baseline={ev_baseline:.4f} · HE={he_baseline:.1f}%")
        print(f"{'=' * 60}")
        print(
            f"  {'Strategia':<18} {'EV medio':>9} {'Ratio':>8} "
            f"{'Win%':>7} {'P&L':>10} {'HE eff':>8}"
        )
        print("  " + "-" * 60)

        best_ratio = 0
        best_name = ""

        for name, fn in strategies:
            log.info("K=%d %s...", k, name)
            r = run_backtest(k, fn, estrazioni, start, n)
            marker = " ***" if r["ratio"] > best_ratio else ""
            print(
                f"  {name:<18} {r['avg_ev']:>9.4f} {r['ratio']:>7.4f}x "
                f"{r['win_rate']:>6.1f}% {r['pnl']:>+10.2f} {r['he']:>7.1f}%{marker}"
            )
            if r["ratio"] > best_ratio:
                best_ratio = r["ratio"]
                best_name = name
                best_per_k[k] = {
                    "strategy": name,
                    "ratio": r["ratio"],
                    "avg_ev": r["avg_ev"],
                    "he": r["he"],
                    "pnl": r["pnl"],
                    "n": r["n_total"],
                }

        print(f"\n  MIGLIORE K={k}: {best_name} (ratio {best_ratio:.4f}x)")

    # Riepilogo finale
    print("\n\n" + "=" * 75)
    print("RIEPILOGO — MIGLIORE STRATEGIA PER OGNI K")
    print("=" * 75)
    print(f"\n  {'K':>3}  {'Strategia':<18} {'Ratio':>8} {'EV medio':>9} {'HE eff':>8} {'P&L':>10}")
    print("  " + "-" * 60)

    for k in range(1, 11):
        if k in best_per_k:
            b = best_per_k[k]
            print(
                f"  {k:>3}  {b['strategy']:<18} {b['ratio']:>7.4f}x "
                f"{b['avg_ev']:>9.4f} {b['he']:>7.1f}% {b['pnl']:>+10.2f}"
            )


if __name__ == "__main__":
    main()
