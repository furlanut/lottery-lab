"""Verifica la teoria del 'cluster bonus combinatoriale' (Appendice I.11).

Test tre strategie:
  1. Cluster fisso random: ogni volta pesca r in [1..85], pick = [r, r+1, ..., r+5]
  2. Pick totalmente sparso: [10, 25, 40, 55, 70, 85] fisso (anti-cluster)
  3. Pick random sparso: 6 numeri casuali con pairwise distance >= 10

Se l'ipotesi "cluster bonus da convessita payoff" e vera:
  (1) ratio ~1.04-1.06x (simile vicinanza)
  (2-3) ratio ~0.94-0.98x (sotto baseline per convessita inversa)
"""

# ruff: noqa: E501, S311, N806
from __future__ import annotations

import logging
import random
from collections import Counter

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA
from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("cluster_verify")

K = 6
W = 100
COSTO = 2.0
EV_TEORICO = 1.80


def _load() -> list[dict]:
    s = get_session()
    try:
        rows = (
            s.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )
        return [{"numeri": list(r.numeri), "extra": list(r.numeri_extra)} for r in rows]
    finally:
        s.close()


def _run_backtest(data: list[dict], pick_fn) -> dict:
    """pick_fn(window_data, i, rng) -> set di 6 numeri."""
    pb = PREMI_BASE.get(K, {})
    pe = PREMI_EXTRA.get(K, {})

    giocate, totale_vinto, big_wins = 0, 0.0, 0
    match_dist: dict[int, int] = {}

    rng = random.Random(42)
    for i in range(W, len(data)):
        pick = pick_fn(data[max(0, i - W) : i], i, rng)
        drawn = set(data[i]["numeri"])
        extra = set(data[i]["extra"])
        mb = len(pick & drawn)
        me = len((pick - drawn) & extra)
        v = pb.get(mb, 0.0) + pe.get(me, 0.0)
        giocate += 1
        totale_vinto += v
        if v >= 20:
            big_wins += 1
        match_dist[mb] = match_dist.get(mb, 0) + 1

    costo_tot = giocate * COSTO
    pnl = totale_vinto - costo_tot
    ratio = (totale_vinto / giocate) / EV_TEORICO

    # Varianza del match_base osservata
    mean_match = sum(m * c for m, c in match_dist.items()) / giocate
    var_match = sum((m - mean_match) ** 2 * c for m, c in match_dist.items()) / giocate

    return {
        "giocate": giocate,
        "pnl": round(pnl, 2),
        "roi": round(pnl / costo_tot * 100, 2),
        "ratio": round(ratio, 4),
        "big_wins": big_wins,
        "match_dist": match_dist,
        "match_mean": round(mean_match, 4),
        "match_var": round(var_match, 4),
        "coda_4plus": sum(c for m, c in match_dist.items() if m >= 4),
    }


# =====================================================================
# Strategie
# =====================================================================


def pick_cluster_random_seed(window, i, rng):
    """Cluster fisso [r, r+1, ..., r+5] con r random 1-85."""
    r = rng.randint(1, 85)
    return set(range(r, r + 6))


def pick_cluster_anti(window, i, rng):
    """Sparso fisso: [10, 25, 40, 55, 70, 85]."""
    return {10, 25, 40, 55, 70, 85}


def pick_sparse_random(window, i, rng):
    """6 numeri random con pairwise distance >= 10."""
    max_tries = 100
    for _ in range(max_tries):
        candidates = sorted(rng.sample(range(1, 91), 6))
        ok = all(candidates[j + 1] - candidates[j] >= 10 for j in range(5))
        if ok:
            return set(candidates)
    # fallback
    return {8, 20, 35, 50, 65, 80}


def pick_vicinanza_classic(window, i, rng):
    """Baseline di comparazione: vicinanza come Appendice H."""
    freq = Counter()
    for e in window:
        for n in e["numeri"]:
            freq[n] += 1
    seed = freq.most_common(1)[0][0] if freq else 1
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
        if len(pick) >= K:
            break
    if len(pick) < K:
        for n, _ in freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= K:
                break
    return set(pick[:K])


def pick_dual_target(window, i, rng):
    """Dual target: 3 hot base + 3 hot extra disgiunti."""
    freq = Counter()
    freq_e = Counter()
    for e in window:
        for n in e["numeri"]:
            freq[n] += 1
        for n in e["extra"]:
            freq_e[n] += 1
    hb = [n for n, _ in freq.most_common(K)][:3]
    he = [n for n, _ in freq_e.most_common(20) if n not in hb][:3]
    return set(hb + he)


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    log.info("Caricamento dataset...")
    data = _load()
    log.info(f"Dataset: {len(data):,} estrazioni\n")

    strategies = [
        ("cluster_random_seed", pick_cluster_random_seed, "Cluster fisso [r, r+1..r+5], r random"),
        ("cluster_anti",        pick_cluster_anti,       "Fisso sparso [10,25,40,55,70,85]"),
        ("sparse_random",       pick_sparse_random,      "6 random con dist ≥ 10"),
        ("vicinanza_classic",   pick_vicinanza_classic,  "Vicinanza (baseline H)"),
        ("dual_target",         pick_dual_target,        "Dual target (baseline H)"),
    ]

    results = {}
    log.info(f"{'Strategia':<24} {'Cluster?':>10} {'Ratio':>8} {'ROI':>9} {'Big':>6} {'Var(mb)':>9} {'Coda4+':>8}")
    log.info("-" * 90)
    for name, fn, desc in strategies:
        log.info(f"Running: {desc}...")
        r = _run_backtest(data, fn)
        results[name] = r
        is_cluster = "SI" if name.startswith("cluster") or name == "vicinanza_classic" else "NO"
        log.info(
            f"{name:<24} {is_cluster:>10} {r['ratio']:>7.4f}x {r['roi']:>+8.2f}% "
            f"{r['big_wins']:>6} {r['match_var']:>9.4f} {r['coda_4plus']:>8}"
        )

    # Distribuzione match per ciascuno
    log.info("")
    log.info("Distribuzione match_base per strategia:")
    match_keys = sorted({m for r in results.values() for m in r["match_dist"]})
    hdr = f"{'mb':>4} " + " ".join(f"{n:>10}" for n, _, _ in strategies)
    log.info(hdr)
    log.info("-" * len(hdr))
    for m in match_keys:
        row = f"{m:>4} " + " ".join(f"{results[n]['match_dist'].get(m, 0):>10}" for n, _, _ in strategies)
        log.info(row)

    # Verdetto teoria
    log.info("")
    log.info("=" * 70)
    log.info("VERDETTO TEORIA CONVESSITA")
    log.info("=" * 70)

    r_cluster_rand = results["cluster_random_seed"]["ratio"]
    r_cluster_anti = results["cluster_anti"]["ratio"]
    r_sparse_rand = results["sparse_random"]["ratio"]
    r_vicinanza = results["vicinanza_classic"]["ratio"]
    r_dual = results["dual_target"]["ratio"]

    log.info("")
    log.info(f"Cluster random-seed: {r_cluster_rand:.4f}x  (atteso ~1.04-1.06x se teoria vera)")
    log.info(f"Vicinanza classic:   {r_vicinanza:.4f}x  (benchmark H)")
    log.info(f"Anti-cluster fisso:  {r_cluster_anti:.4f}x  (atteso ~0.94-0.98x se teoria vera)")
    log.info(f"Sparse random:       {r_sparse_rand:.4f}x  (atteso ~0.94-0.98x)")
    log.info(f"Dual target:         {r_dual:.4f}x  (benchmark H)")

    # Se cluster random >= 1.03, la teoria convessita e' confermata
    if r_cluster_rand >= 1.03 and r_sparse_rand <= 0.98:
        verdict = (
            "TEORIA CONFERMATA: cluster pattern-free batte spread pattern-free. "
            "L'edge di vicinanza viene dalla convessita × varianza, non dal seed selection."
        )
    elif r_cluster_rand >= 1.02:
        verdict = (
            "TEORIA PARZIALMENTE CONFERMATA: cluster batte spread ma il gap e minore del previsto. "
            "Seed selection potrebbe contribuire marginalmente."
        )
    else:
        verdict = (
            "TEORIA SMENTITA: il cluster da solo non produce l'edge. "
            "Serve un altro meccanismo."
        )
    log.info(f"\n{verdict}")

    # Confronto varianze
    log.info("")
    log.info("Varianza match_base osservata (Var[X] atteso ipergeom ≈ 1.30):")
    for name, _, _ in strategies:
        log.info(f"  {name:<24} Var[mb] = {results[name]['match_var']:.4f}")


if __name__ == "__main__":
    main()
