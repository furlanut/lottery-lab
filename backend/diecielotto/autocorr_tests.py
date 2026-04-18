"""Test del meccanismo causale di vicinanza: dipendenza freq-finestra + adjacency.

L'Appendice H ha mostrato che l'edge di vicinanza W=100 viene per il ~92% dal
seed-selection (numero piu frequente in W=100) e per il ~8% dall'adjacency.
Questo script cerca di caratterizzare il PRNG che rende possibile quell'effetto.

Test H.8a — Freq-window predicts next draw:
    Per ogni (estrazione t, numero n), registra freq(n, W) e present(n, t).
    Sotto PRNG ideale: P(present|freq=k) = 20/90 per ogni k.
    Se P(present) cresce con freq → HOT-HAND numerica (momentum).

Test H.8b — Adjacency bonus:
    Controllando per freq_win(n), la freq media dei vicini (n±1..±5) aggiunge
    potere predittivo su present(n, t)? Regressione logistica.
    Se effetto neighbors > 0 dopo controllo per n → l'adjacency e reale.

Test H.8c — Window sensitivity:
    Ripete H.8a per W in {20, 50, 100, 200, 500, 1000}.
    Se il picco e a W=100, il PRNG ha memoria di ~100 estrazioni.

Test H.8d — Temporal stability:
    Split in 4 parti del dataset cronologico. Ripete H.8a su ciascuna.
    Se il pattern e stabile → e un pattern RNG genuino, non varianza.
"""

# ruff: noqa: E501, S311, N803, N806
from __future__ import annotations

import logging
from collections import Counter
from math import sqrt

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("autocorr_tests")


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
        return [{"numeri": list(r.numeri)} for r in rows]
    finally:
        s.close()


# =====================================================================
# H.8a — Freq-window → P(present at t)
# =====================================================================


def test_a(data: list[dict], W: int = 100) -> dict:
    """Per ogni (t>=W, n in 1..90), registra (freq_n_W, present_n_t).
    Poi stima P(present | freq=k) e confronta con baseline 20/90.
    """
    log.info("=" * 70)
    log.info(f"TEST H.8a — Freq-window predicts next draw (W={W})")
    log.info("=" * 70)

    # Sliding window freq: aggiornare in modo incrementale
    bins: dict[int, list[int]] = {}  # freq -> [hits, total]
    n_samples = 0

    # Precompute per ogni slot l'indicator "e nell'estrazione?"
    # usiamo un dict {t: set(drawn)} per lookup rapido
    drawn_sets = [set(e["numeri"]) for e in data]

    # Sliding window: conto frequenza di ciascun numero nelle W estrazioni precedenti
    win_freq = Counter()
    for i in range(W):
        for n in data[i]["numeri"]:
            win_freq[n] += 1

    for t in range(W, len(data)):
        # Al tempo t, la finestra e [t-W, t-1], gia aggiornata
        drawn_t = drawn_sets[t]
        for n in range(1, 91):
            f = win_freq.get(n, 0)
            present = 1 if n in drawn_t else 0
            if f not in bins:
                bins[f] = [0, 0]
            bins[f][0] += present
            bins[f][1] += 1
            n_samples += 1

        # Slide window: rimuovi estrazione t-W, aggiungi t
        for n in data[t - W]["numeri"]:
            win_freq[n] -= 1
            if win_freq[n] == 0:
                del win_freq[n]
        for n in data[t]["numeri"]:
            win_freq[n] += 1

    baseline = 20 / 90  # 0.2222

    log.info(f"Samples: {n_samples:,} (= ({len(data)}-{W}) * 90)")
    log.info(f"Baseline P(present): {baseline:.4f}")
    log.info("")
    log.info(f"{'freq':>6} {'n':>10} {'P(pres)':>10} {'diff%':>8} {'z':>8}")
    log.info("-" * 50)

    # Raggruppa bins per intervalli di freq per pulizia
    # Mostra freq da 0 a max in step
    max(bins.keys())
    min(bins.keys())

    for f in sorted(bins):
        hits, tot = bins[f]
        if tot < 100:  # skip freqs with poche osservazioni
            continue
        p = hits / tot
        diff_pct = (p - baseline) / baseline * 100
        # SE binomiale
        se = sqrt(baseline * (1 - baseline) / tot)
        z = (p - baseline) / se
        log.info(f"{f:>6} {tot:>10,} {p:>10.4f} {diff_pct:>+7.2f}% {z:>+8.2f}")

    # Aggregate: freq high (>= mean+1.5sd) vs low (<= mean-1.5sd)
    # Con W=100 e p=20/90, freq attesa = W * 20/90 = 22.22, SD ~ sqrt(W*p*(1-p)) ~ 4.15
    expected_mean = W * 20 / 90
    expected_sd = sqrt(W * 20 / 90 * 70 / 90)
    hi_threshold = expected_mean + 1.5 * expected_sd
    lo_threshold = expected_mean - 1.5 * expected_sd

    hi_hits, hi_tot = 0, 0
    lo_hits, lo_tot = 0, 0
    for f, (hits, tot) in bins.items():
        if f >= hi_threshold:
            hi_hits += hits
            hi_tot += tot
        elif f <= lo_threshold:
            lo_hits += hits
            lo_tot += tot

    p_hi = hi_hits / hi_tot if hi_tot else 0
    p_lo = lo_hits / lo_tot if lo_tot else 0

    log.info("")
    log.info(f"Aggregati (W={W}, expected freq_mean={expected_mean:.1f}, SD={expected_sd:.2f}):")
    log.info(f"  HIGH freq (>= {hi_threshold:.1f}): n={hi_tot:,}  P(present)={p_hi:.4f}  diff={((p_hi-baseline)/baseline)*100:+.2f}%")
    log.info(f"  LOW  freq (<= {lo_threshold:.1f}): n={lo_tot:,}  P(present)={p_lo:.4f}  diff={((p_lo-baseline)/baseline)*100:+.2f}%")

    # Test z sulla differenza HI vs LO
    if hi_tot > 0 and lo_tot > 0:
        p_pool = (hi_hits + lo_hits) / (hi_tot + lo_tot)
        se_diff = sqrt(p_pool * (1 - p_pool) * (1 / hi_tot + 1 / lo_tot))
        z_diff = (p_hi - p_lo) / se_diff if se_diff > 0 else 0
        log.info(f"  HI - LO: {(p_hi-p_lo)*100:+.3f} pp  z={z_diff:+.2f}")
    else:
        z_diff = 0

    verdict = ""
    if z_diff > 3.0:
        verdict = f"HOT-HAND POSITIVO (z={z_diff:+.2f}): numeri caldi → piu probabili."
    elif z_diff < -3.0:
        verdict = f"ANTI-PERSISTENZA (z={z_diff:+.2f}): numeri caldi → meno probabili."
    else:
        verdict = f"NESSUN EFFETTO FREQ (z={z_diff:+.2f}): il PRNG e uniforme rispetto alla freq W={W}."
    log.info(f"\nVerdetto: {verdict}")

    return {
        "W": W,
        "n_samples": n_samples,
        "baseline": baseline,
        "p_hi": p_hi,
        "p_lo": p_lo,
        "hi_tot": hi_tot,
        "lo_tot": lo_tot,
        "z_diff": z_diff,
        "verdict": verdict,
    }


# =====================================================================
# H.8b — Adjacency bonus (controlling for freq_n)
# =====================================================================


def test_b(data: list[dict], W: int = 100) -> dict:
    """Raccoglie (freq_n, avg_freq_neighbors_n, present_n) per ogni (t, n).
    Poi: per ciascun valore di freq_n (fixed), analizza come P(present) varia
    con avg_freq_neighbors. Se ancora crescente → adjacency bonus reale.
    """
    log.info("=" * 70)
    log.info(f"TEST H.8b — Adjacency bonus (W={W}, controlling for freq_n)")
    log.info("=" * 70)

    # Struttura: cells[freq_n][avg_nbr_bin] = [hits, total]
    # avg_nbr_bin = round(avg_neighbor_freq)
    cells: dict[tuple[int, int], list[int]] = {}

    drawn_sets = [set(e["numeri"]) for e in data]

    # Sliding window
    win_freq = Counter()
    for i in range(W):
        for n in data[i]["numeri"]:
            win_freq[n] += 1

    for t in range(W, len(data)):
        drawn_t = drawn_sets[t]
        # Precompute avg freq dei vicini per ogni numero
        for n in range(1, 91):
            f_n = win_freq.get(n, 0)
            neighbors = [n + d for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5) if 1 <= n + d <= 90]
            sum_nbr = sum(win_freq.get(m, 0) for m in neighbors)
            avg_nbr = sum_nbr / len(neighbors)
            avg_nbr_bin = int(round(avg_nbr))
            present = 1 if n in drawn_t else 0
            key = (f_n, avg_nbr_bin)
            if key not in cells:
                cells[key] = [0, 0]
            cells[key][0] += present
            cells[key][1] += 1

        # Slide
        for n in data[t - W]["numeri"]:
            win_freq[n] -= 1
            if win_freq[n] == 0:
                del win_freq[n]
        for n in data[t]["numeri"]:
            win_freq[n] += 1

    baseline = 20 / 90

    # Analisi: per 5 valori di freq_n (low, low-mid, mid, mid-high, high),
    # come varia P(present) al variare di avg_nbr?
    expected_mean = W * 20 / 90
    freq_levels = [
        ("very_low", int(round(expected_mean - 2 * sqrt(W * 20 / 90 * 70 / 90)))),
        ("low", int(round(expected_mean - sqrt(W * 20 / 90 * 70 / 90)))),
        ("mid", int(round(expected_mean))),
        ("high", int(round(expected_mean + sqrt(W * 20 / 90 * 70 / 90)))),
        ("very_high", int(round(expected_mean + 2 * sqrt(W * 20 / 90 * 70 / 90)))),
    ]

    log.info("Per ciascun livello di freq_n (holding constant), variazione con avg_nbr:")
    log.info(f"Baseline P(present) = {baseline:.4f}")
    log.info("")

    # Raccogli: per ogni freq level, bins di avg_nbr → (hits, tot)
    for label, target_f in freq_levels:
        log.info(f"--- freq_n = {target_f} ({label}) ---")
        # bins of avg_nbr
        bin_agg: dict[int, list[int]] = {}
        for (fn, anb), (hits, tot) in cells.items():
            if fn == target_f:
                if anb not in bin_agg:
                    bin_agg[anb] = [0, 0]
                bin_agg[anb][0] += hits
                bin_agg[anb][1] += tot

        if not bin_agg:
            log.info("  (no data)")
            continue

        log.info(f"  {'avg_nbr':>8} {'n':>10} {'P(pres)':>10} {'diff%':>8}")
        for anb in sorted(bin_agg):
            hits, tot = bin_agg[anb]
            if tot < 500:  # skip low-data bins
                continue
            p = hits / tot
            log.info(f"  {anb:>8} {tot:>10,} {p:>10.4f} {((p-baseline)/baseline)*100:>+7.2f}%")

    # Test aggregato: "adjacency bonus" come correlazione parziale
    # Aggregate: freq_n ≈ mid (22±2), due livelli di avg_nbr: low vs high
    low_nbr_thresh = int(round(expected_mean - 0.5 * sqrt(W * 20 / 90 * 70 / 90)))
    hi_nbr_thresh = int(round(expected_mean + 0.5 * sqrt(W * 20 / 90 * 70 / 90)))

    cond_low_hits, cond_low_tot = 0, 0
    cond_hi_hits, cond_hi_tot = 0, 0
    # A freq_n mid (range [mid-1, mid+1]), avg_nbr low vs high
    for (fn, anb), (hits, tot) in cells.items():
        if abs(fn - int(expected_mean)) <= 1:
            if anb <= low_nbr_thresh:
                cond_low_hits += hits
                cond_low_tot += tot
            elif anb >= hi_nbr_thresh:
                cond_hi_hits += hits
                cond_hi_tot += tot

    p_cond_lo = cond_low_hits / cond_low_tot if cond_low_tot else 0
    p_cond_hi = cond_hi_hits / cond_hi_tot if cond_hi_tot else 0

    z_adj = 0
    if cond_low_tot > 0 and cond_hi_tot > 0:
        p_pool = (cond_low_hits + cond_hi_hits) / (cond_low_tot + cond_hi_tot)
        se = sqrt(p_pool * (1 - p_pool) * (1 / cond_low_tot + 1 / cond_hi_tot))
        z_adj = (p_cond_hi - p_cond_lo) / se if se > 0 else 0

    log.info("")
    log.info(f"ADJACENCY BONUS (freq_n fissa a mid ≈ {int(expected_mean)}±1):")
    log.info(f"  LOW nbr   (avg ≤ {low_nbr_thresh}): n={cond_low_tot:,}  P={p_cond_lo:.4f}")
    log.info(f"  HIGH nbr  (avg ≥ {hi_nbr_thresh}): n={cond_hi_tot:,}  P={p_cond_hi:.4f}")
    log.info(f"  Diff: {(p_cond_hi-p_cond_lo)*100:+.3f} pp  z={z_adj:+.2f}")

    verdict = ""
    if z_adj > 3.0:
        verdict = f"ADJACENCY BONUS CONFERMATO (z={z_adj:+.2f}): i vicini caldi aiutano anche controllando per freq_n."
    elif z_adj < -3.0:
        verdict = f"ANTI-ADJACENCY (z={z_adj:+.2f}): i vicini caldi penalizzano n."
    else:
        verdict = f"NESSUN BONUS (z={z_adj:+.2f}): dopo controllo per freq_n, i vicini non aggiungono."
    log.info(f"\nVerdetto: {verdict}")

    return {
        "W": W,
        "p_cond_lo_nbr": p_cond_lo,
        "p_cond_hi_nbr": p_cond_hi,
        "z_adj": z_adj,
        "cond_lo_n": cond_low_tot,
        "cond_hi_n": cond_hi_tot,
        "verdict": verdict,
    }


# =====================================================================
# H.8c — Window sensitivity
# =====================================================================


def test_c(data: list[dict], W_list: list[int]) -> dict:
    """Ripete H.8a per diversi W, cerca il W con effetto massimo."""
    log.info("=" * 70)
    log.info(f"TEST H.8c — Window sensitivity (W in {W_list})")
    log.info("=" * 70)

    results = {}
    for W in W_list:
        log.info(f"\n>>> W={W}")
        r = test_a(data, W=W)
        results[W] = r

    log.info("")
    log.info("=" * 70)
    log.info("Riepilogo sensitivity:")
    log.info(f"{'W':>6} {'z_hi_vs_lo':>12} {'P(pres|hi)':>12} {'P(pres|lo)':>12} {'diff pp':>10}")
    log.info("-" * 70)
    for W in W_list:
        r = results[W]
        diff_pp = (r["p_hi"] - r["p_lo"]) * 100
        log.info(f"{W:>6} {r['z_diff']:>+11.2f} {r['p_hi']:>12.4f} {r['p_lo']:>12.4f} {diff_pp:>+9.3f}")

    # Find optimal W
    best_W = max(W_list, key=lambda w: results[w]["z_diff"])
    log.info(f"\nMiglior W (z massimo): {best_W} (z={results[best_W]['z_diff']:+.2f})")

    return {"W_results": {w: results[w]["z_diff"] for w in W_list}, "best_W": best_W}


# =====================================================================
# H.8d — Temporal stability
# =====================================================================


def test_d(data: list[dict], W: int = 100, n_folds: int = 4) -> dict:
    """Split cronologico del dataset in n_folds parti, calcola H.8a in ciascuna."""
    log.info("=" * 70)
    log.info(f"TEST H.8d — Temporal stability ({n_folds} folds)")
    log.info("=" * 70)

    fold_size = len(data) // n_folds
    results = []
    for i in range(n_folds):
        start = i * fold_size
        end = start + fold_size if i < n_folds - 1 else len(data)
        sub = data[start:end]
        log.info(f"\n>>> Fold {i+1}/{n_folds}: estrazioni [{start}..{end}), n={len(sub)}")
        r = test_a(sub, W=W)
        r["fold"] = i + 1
        r["range"] = (start, end)
        results.append(r)

    log.info("")
    log.info("=" * 70)
    log.info(f"Stabilita del pattern W={W} tra fold:")
    log.info(f"{'Fold':>6} {'range':>20} {'z':>10} {'P_hi':>10} {'P_lo':>10}")
    log.info("-" * 70)
    zs = []
    for r in results:
        range_str = f"[{r['range'][0]}..{r['range'][1]})"
        log.info(
            f"{r['fold']:>6} {range_str:>20} {r['z_diff']:>+10.2f} {r['p_hi']:>10.4f} {r['p_lo']:>10.4f}"
        )
        zs.append(r["z_diff"])

    # Stability: coefficient of variation dei z
    mean_z = sum(zs) / len(zs)
    sd_z = sqrt(sum((z - mean_z) ** 2 for z in zs) / len(zs))
    log.info(f"\nMean z: {mean_z:+.2f}  SD z: {sd_z:.2f}")

    # All same sign?
    all_pos = all(z > 0 for z in zs)
    all_neg = all(z < 0 for z in zs)

    verdict = ""
    if all_pos and mean_z > 3:
        verdict = f"PATTERN STABILE POSITIVO (mean z={mean_z:+.2f}, tutti positivi): e un pattern RNG reale."
    elif all_neg and mean_z < -3:
        verdict = f"PATTERN STABILE NEGATIVO (mean z={mean_z:+.2f})."
    elif sd_z > 3:
        verdict = f"PATTERN INSTABILE (SD z={sd_z:.2f}): probabile varianza, non RNG."
    else:
        verdict = f"PATTERN DEBOLE (mean z={mean_z:+.2f}, SD={sd_z:.2f})."
    log.info(f"\nVerdetto: {verdict}")

    return {"folds": results, "mean_z": mean_z, "sd_z": sd_z, "verdict": verdict}


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    log.info("Caricamento dataset...")
    data = _load()
    log.info(f"Dataset: {len(data):,} estrazioni 10eLotto\n")

    results = {}

    # H.8a: core test con W=100
    results["a"] = test_a(data, W=100)
    log.info("")

    # H.8b: adjacency bonus
    results["b"] = test_b(data, W=100)
    log.info("")

    # H.8c: W sensitivity
    results["c"] = test_c(data, W_list=[20, 50, 100, 200, 500, 1000])
    log.info("")

    # H.8d: temporal stability
    results["d"] = test_d(data, W=100, n_folds=4)

    log.info("")
    log.info("=" * 70)
    log.info("SINTESI FINALE")
    log.info("=" * 70)
    log.info(f"H.8a (freq→present, W=100):    {results['a']['verdict']}")
    log.info(f"H.8b (adjacency bonus):        {results['b']['verdict']}")
    log.info(f"H.8c (W sensitivity):          best W={results['c']['best_W']}")
    log.info(f"H.8d (temporal stability):     {results['d']['verdict']}")


if __name__ == "__main__":
    main()
