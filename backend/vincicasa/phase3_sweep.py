#!/usr/bin/env python3
"""
VinciCasa Phase 3 — Signal Pattern Sweep (SYNTHETIC DATA)
==========================================================
Applies Lotto-style signal patterns to VinciCasa 5/40 data.
Uses 4300 synthetic uniform random draws (seed=42) for methodology validation.

Sweeps:
  3A. Sum × Window
  3B. Proximity × Window
  3C. Decade + freq/rit × Window

All results clearly labeled as SYNTHETIC.
"""

import random
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations

# ─── Configuration ───────────────────────────────────────────────────────────
N_NUMBERS = 40
K_DRAW = 5
N_DRAWS = 4300
SEED = 42
P_BASELINE = 10 / 780  # = 1/78
WINDOWS = [30, 50, 75, 100, 150, 200, 300]
NTFY_URL = "https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM"
REPORT_PATH = "/Users/lucafurlanut/progetti/lotto/backend/vincicasa/ANALYSIS_REPORT.md"


def generate_synthetic_data(n_draws: int, seed: int) -> list[tuple[str, list[int]]]:
    """Generate n_draws synthetic VinciCasa draws (5 from 1-40, no replacement)."""
    rng = random.Random(seed)
    base_date = datetime(2015, 1, 1)
    draws = []
    for i in range(n_draws):
        date_str = (base_date + timedelta(days=i)).strftime("%d/%m/%Y")
        nums = sorted(rng.sample(range(1, N_NUMBERS + 1), K_DRAW))
        draws.append((date_str, nums))
    return draws


def pairs_in_draw(draw: list[int]) -> set[tuple[int, int]]:
    """Return set of all C(5,2)=10 pairs in a draw."""
    return set(combinations(sorted(draw), 2))


# ─── 3A: Sum × Window Sweep ─────────────────────────────────────────────────

def sweep_sums(draws: list[tuple[str, list[int]]], label: str) -> dict:
    """Sweep sum S from 3..79, window W from WINDOWS list."""
    print(f"\n{'='*70}", flush=True)
    print(f"  3A. SUM × WINDOW SWEEP — {label}", flush=True)
    print(f"{'='*70}", flush=True)

    n = len(draws)
    # Precompute all pairs per draw
    draw_pairs = [pairs_in_draw(d[1]) for d in draws]

    # All possible pairs grouped by sum
    all_pairs_by_sum = defaultdict(list)
    for a in range(1, N_NUMBERS + 1):
        for b in range(a + 1, N_NUMBERS + 1):
            all_pairs_by_sum[a + b].append((a, b))

    results = {}  # (S, W) -> {signals, hits, ratio}

    for W in WINDOWS:
        for S in range(3, 80):
            candidate_pairs = all_pairs_by_sum[S]
            if not candidate_pairs:
                continue

            signals = 0
            hits = 0

            for i in range(W, n - 1):
                window_start = i - W
                # Count appearances and last seen for each pair in window
                for pair in candidate_pairs:
                    count = 0
                    last_seen = -1
                    for j in range(window_start, i):
                        if pair in draw_pairs[j]:
                            count += 1
                            last_seen = j
                    if count >= 1:
                        delay = i - last_seen if last_seen >= 0 else W + 1
                        if delay >= W / 3:
                            signals += 1
                            if pair in draw_pairs[i]:
                                hits += 1

            ratio = (hits / signals / P_BASELINE) if signals > 0 else 0.0
            results[(S, W)] = {
                "signals": signals,
                "hits": hits,
                "hit_rate": hits / signals if signals > 0 else 0.0,
                "ratio": ratio,
            }

        print(f"  W={W:3d} done ({n} draws)", flush=True)

    return results


def sweep_sums_optimized(draws: list[tuple[str, list[int]]], label: str) -> dict:
    """Optimized sum sweep using rolling window tracking."""
    print(f"\n{'='*70}", flush=True)
    print(f"  3A. SUM × WINDOW SWEEP — {label}", flush=True)
    print(f"{'='*70}", flush=True)

    n = len(draws)
    draw_pairs = [pairs_in_draw(d[1]) for d in draws]

    # All possible pairs grouped by sum
    all_pairs_by_sum = defaultdict(list)
    for a in range(1, N_NUMBERS + 1):
        for b in range(a + 1, N_NUMBERS + 1):
            all_pairs_by_sum[a + b].append((a, b))

    results = {}

    for W in WINDOWS:
        t0 = time.time()
        for S in range(3, 80):
            candidate_pairs = all_pairs_by_sum[S]
            if not candidate_pairs:
                continue

            signals = 0
            hits = 0

            # For each pair, track appearances in window using a list
            for pair in candidate_pairs:
                # Precompute which draws contain this pair
                pair_draws = set()
                for idx in range(n):
                    if pair in draw_pairs[idx]:
                        pair_draws.add(idx)

                for i in range(W, n - 1):
                    # Count in window [i-W, i)
                    count = 0
                    last_seen = -1
                    for j in range(i - W, i):
                        if j in pair_draws:
                            count += 1
                            last_seen = j

                    if count >= 1:
                        delay = i - last_seen
                        if delay >= W / 3:
                            signals += 1
                            if i in pair_draws:
                                hits += 1

            ratio = (hits / signals / P_BASELINE) if signals > 0 else 0.0
            results[(S, W)] = {
                "signals": signals,
                "hits": hits,
                "hit_rate": hits / signals if signals > 0 else 0.0,
                "ratio": ratio,
            }

        elapsed = time.time() - t0
        print(f"  W={W:3d} done ({elapsed:.1f}s)", flush=True)

    return results


def sweep_sums_fast(draws: list[tuple[str, list[int]]], label: str) -> dict:
    """Fast sum sweep — precompute pair presence, vectorize window scan."""
    print(f"\n{'='*70}", flush=True)
    print(f"  3A. SUM × WINDOW SWEEP — {label}", flush=True)
    print(f"{'='*70}", flush=True)

    n = len(draws)
    draw_pairs = [pairs_in_draw(d[1]) for d in draws]

    # Precompute: for each pair, sorted list of draw indices where it appears
    pair_indices: dict[tuple[int, int], list[int]] = {}
    for a in range(1, N_NUMBERS + 1):
        for b in range(a + 1, N_NUMBERS + 1):
            pair_indices[(a, b)] = []
    for idx in range(n):
        for pair in draw_pairs[idx]:
            pair_indices[pair].append(idx)

    # Group pairs by sum
    pairs_by_sum = defaultdict(list)
    for a in range(1, N_NUMBERS + 1):
        for b in range(a + 1, N_NUMBERS + 1):
            pairs_by_sum[a + b].append((a, b))

    # For each pair, create a set for O(1) lookup
    pair_set: dict[tuple[int, int], set[int]] = {}
    for pair, indices in pair_indices.items():
        pair_set[pair] = set(indices)

    results = {}

    for W in WINDOWS:
        t0 = time.time()
        delay_threshold = W / 3

        for S in range(3, 80):
            candidates = pairs_by_sum.get(S, [])
            if not candidates:
                continue

            total_signals = 0
            total_hits = 0

            for pair in candidates:
                indices = pair_indices[pair]
                pset = pair_set[pair]
                if not indices:
                    continue

                for i in range(W, n - 1):
                    # Binary search for last appearance in [i-W, i)
                    # Find appearances in window
                    import bisect
                    lo = bisect.bisect_left(indices, i - W)
                    hi = bisect.bisect_left(indices, i)
                    if hi > lo:  # at least 1 appearance in window
                        last_in_window = indices[hi - 1]
                        delay = i - last_in_window
                        if delay >= delay_threshold:
                            total_signals += 1
                            if i in pset:
                                total_hits += 1

            ratio = (total_hits / total_signals / P_BASELINE) if total_signals > 0 else 0.0
            results[(S, W)] = {
                "signals": total_signals,
                "hits": total_hits,
                "hit_rate": total_hits / total_signals if total_signals > 0 else 0.0,
                "ratio": ratio,
            }

        elapsed = time.time() - t0
        print(f"  W={W:3d} done ({elapsed:.1f}s)", flush=True)

    return results


# ─── 3B: Proximity × Window Sweep ───────────────────────────────────────────

def sweep_proximity(draws: list[tuple[str, list[int]]], label: str) -> dict:
    """Sweep proximity D in [1,2,3,5,8,10,15], window W."""
    print(f"\n{'='*70}", flush=True)
    print(f"  3B. PROXIMITY × WINDOW SWEEP — {label}", flush=True)
    print(f"{'='*70}", flush=True)

    import bisect

    n = len(draws)
    draw_pairs = [pairs_in_draw(d[1]) for d in draws]

    # Precompute pair indices
    pair_indices: dict[tuple[int, int], list[int]] = defaultdict(list)
    pair_set: dict[tuple[int, int], set[int]] = defaultdict(set)
    for idx in range(n):
        for pair in draw_pairs[idx]:
            pair_indices[pair].append(idx)
            pair_set[pair].add(idx)

    # Group pairs by max distance
    DISTANCES = [1, 2, 3, 5, 8, 10, 15]
    pairs_by_max_dist: dict[int, list[tuple[int, int]]] = {}
    for D in DISTANCES:
        pairs_by_max_dist[D] = [(a, b) for a in range(1, N_NUMBERS + 1)
                                 for b in range(a + 1, N_NUMBERS + 1)
                                 if b - a <= D]

    results = {}

    for W in WINDOWS:
        t0 = time.time()
        delay_threshold = W / 3

        for D in DISTANCES:
            candidates = pairs_by_max_dist[D]
            total_signals = 0
            total_hits = 0

            for pair in candidates:
                indices = pair_indices[pair]
                pset = pair_set[pair]
                if not indices:
                    continue

                for i in range(W, n - 1):
                    lo = bisect.bisect_left(indices, i - W)
                    hi = bisect.bisect_left(indices, i)
                    if hi > lo:
                        last_in_window = indices[hi - 1]
                        delay = i - last_in_window
                        if delay >= delay_threshold:
                            total_signals += 1
                            if i in pset:
                                total_hits += 1

            ratio = (total_hits / total_signals / P_BASELINE) if total_signals > 0 else 0.0
            results[(D, W)] = {
                "signals": total_signals,
                "hits": total_hits,
                "hit_rate": total_hits / total_signals if total_signals > 0 else 0.0,
                "ratio": ratio,
            }

        elapsed = time.time() - t0
        print(f"  W={W:3d} done ({elapsed:.1f}s)", flush=True)

    return results


# ─── 3C: Decade + freq/rit Sweep ────────────────────────────────────────────

def sweep_decade(draws: list[tuple[str, list[int]]], label: str) -> dict:
    """Sweep same-decade pairs × window."""
    print(f"\n{'='*70}", flush=True)
    print(f"  3C. DECADE × WINDOW SWEEP — {label}", flush=True)
    print(f"{'='*70}", flush=True)

    import bisect

    n = len(draws)
    draw_pairs = [pairs_in_draw(d[1]) for d in draws]

    # Precompute pair indices
    pair_indices: dict[tuple[int, int], list[int]] = defaultdict(list)
    pair_set: dict[tuple[int, int], set[int]] = defaultdict(set)
    for idx in range(n):
        for pair in draw_pairs[idx]:
            pair_indices[pair].append(idx)
            pair_set[pair].add(idx)

    # Same-decade pairs: decades 1-10, 11-20, 21-30, 31-40
    def decade(num: int) -> int:
        return (num - 1) // 10

    same_decade_pairs = [(a, b) for a in range(1, N_NUMBERS + 1)
                          for b in range(a + 1, N_NUMBERS + 1)
                          if decade(a) == decade(b)]
    print(f"  Same-decade pairs: {len(same_decade_pairs)}", flush=True)

    results = {}

    for W in WINDOWS:
        t0 = time.time()
        delay_threshold = W / 3

        total_signals = 0
        total_hits = 0

        for pair in same_decade_pairs:
            indices = pair_indices[pair]
            pset = pair_set[pair]
            if not indices:
                continue

            for i in range(W, n - 1):
                lo = bisect.bisect_left(indices, i - W)
                hi = bisect.bisect_left(indices, i)
                if hi > lo:
                    last_in_window = indices[hi - 1]
                    delay = i - last_in_window
                    if delay >= delay_threshold:
                        total_signals += 1
                        if i in pset:
                            total_hits += 1

        ratio = (total_hits / total_signals / P_BASELINE) if total_signals > 0 else 0.0
        results[W] = {
            "signals": total_signals,
            "hits": total_hits,
            "hit_rate": total_hits / total_signals if total_signals > 0 else 0.0,
            "ratio": ratio,
        }

        elapsed = time.time() - t0
        print(f"  W={W:3d}: signals={total_signals}, hits={total_hits}, ratio={ratio:.4f} ({elapsed:.1f}s)", flush=True)

    return results


# ─── Cross-validation ────────────────────────────────────────────────────────

def cross_validate_config(draws, config_fn, n_folds=5):
    """5-fold CV for a given configuration function.
    config_fn(draws, label) -> signals, hits for a single sweep."""
    import bisect

    n = len(draws)
    fold_size = n // n_folds
    fold_ratios = []

    for fold in range(n_folds):
        # Validation fold
        val_start = fold * fold_size
        val_end = val_start + fold_size
        # Use remaining as train (but we actually test on val only)
        # For CV we just split the data into folds and run the sweep on each
        val_draws = draws[val_start:val_end]

        draw_pairs = [pairs_in_draw(d[1]) for d in val_draws]
        n_val = len(val_draws)

        pair_indices_val: dict[tuple[int, int], list[int]] = defaultdict(list)
        pair_set_val: dict[tuple[int, int], set[int]] = defaultdict(set)
        for idx in range(n_val):
            for pair in draw_pairs[idx]:
                pair_indices_val[pair].append(idx)
                pair_set_val[pair].add(idx)

        # Run config_fn on val data
        signals, hits = config_fn(val_draws, n_val, draw_pairs,
                                   pair_indices_val, pair_set_val)

        ratio = (hits / signals / P_BASELINE) if signals > 0 else 0.0
        fold_ratios.append(ratio)

    return fold_ratios


def make_sum_config(S, W):
    """Return a config function for sum S, window W."""
    import bisect

    pairs_for_sum = [(a, b) for a in range(1, N_NUMBERS + 1)
                      for b in range(a + 1, N_NUMBERS + 1) if a + b == S]

    def config_fn(val_draws, n_val, draw_pairs, pair_indices_val, pair_set_val):
        delay_threshold = W / 3
        total_signals = 0
        total_hits = 0
        for pair in pairs_for_sum:
            indices = pair_indices_val.get(pair, [])
            pset = pair_set_val.get(pair, set())
            if not indices:
                continue
            for i in range(min(W, n_val), n_val - 1):
                lo = bisect.bisect_left(indices, i - W)
                hi = bisect.bisect_left(indices, i)
                if hi > lo:
                    last = indices[hi - 1]
                    delay = i - last
                    if delay >= delay_threshold:
                        total_signals += 1
                        if i in pset:
                            total_hits += 1
        return total_signals, total_hits

    return config_fn


def make_prox_config(D, W):
    """Return a config function for proximity D, window W."""
    import bisect

    pairs_for_d = [(a, b) for a in range(1, N_NUMBERS + 1)
                    for b in range(a + 1, N_NUMBERS + 1) if b - a <= D]

    def config_fn(val_draws, n_val, draw_pairs, pair_indices_val, pair_set_val):
        delay_threshold = W / 3
        total_signals = 0
        total_hits = 0
        for pair in pairs_for_d:
            indices = pair_indices_val.get(pair, [])
            pset = pair_set_val.get(pair, set())
            if not indices:
                continue
            for i in range(min(W, n_val), n_val - 1):
                lo = bisect.bisect_left(indices, i - W)
                hi = bisect.bisect_left(indices, i)
                if hi > lo:
                    last = indices[hi - 1]
                    delay = i - last
                    if delay >= delay_threshold:
                        total_signals += 1
                        if i in pset:
                            total_hits += 1
        return total_signals, total_hits

    return config_fn


def make_decade_config(W):
    """Return a config function for same-decade pairs, window W."""
    import bisect

    def dec(num):
        return (num - 1) // 10

    same_dec_pairs = [(a, b) for a in range(1, N_NUMBERS + 1)
                       for b in range(a + 1, N_NUMBERS + 1) if dec(a) == dec(b)]

    def config_fn(val_draws, n_val, draw_pairs, pair_indices_val, pair_set_val):
        delay_threshold = W / 3
        total_signals = 0
        total_hits = 0
        for pair in same_dec_pairs:
            indices = pair_indices_val.get(pair, [])
            pset = pair_set_val.get(pair, set())
            if not indices:
                continue
            for i in range(min(W, n_val), n_val - 1):
                lo = bisect.bisect_left(indices, i - W)
                hi = bisect.bisect_left(indices, i)
                if hi > lo:
                    last = indices[hi - 1]
                    delay = i - last
                    if delay >= delay_threshold:
                        total_signals += 1
                        if i in pset:
                            total_hits += 1
        return total_signals, total_hits

    return config_fn


# ─── Formatting ──────────────────────────────────────────────────────────────

def print_heatmap_sums(results, title):
    """Print textual heatmap for sums (step 5) × windows."""
    print(f"\n  Heatmap: {title}", flush=True)
    print(f"  {'Sum':>5s}", end="", flush=True)
    for W in WINDOWS:
        print(f" | W={W:>3d}", end="", flush=True)
    print(flush=True)
    print(f"  {'─'*5}", end="", flush=True)
    for _ in WINDOWS:
        print(f"-+------", end="", flush=True)
    print(flush=True)

    for S in range(5, 80, 5):
        print(f"  {S:>5d}", end="", flush=True)
        for W in WINDOWS:
            key = (S, W)
            if key in results and results[key]["signals"] >= 10:
                r = results[key]["ratio"]
                marker = "**" if r >= 1.3 else "* " if r >= 1.1 else "  "
                print(f" | {r:4.2f}{marker}", end="", flush=True)
            else:
                print(f" |   -  ", end="", flush=True)
        print(flush=True)


def print_heatmap_prox(results, title):
    """Print textual heatmap for proximity × windows."""
    DISTANCES = [1, 2, 3, 5, 8, 10, 15]
    print(f"\n  Heatmap: {title}", flush=True)
    print(f"  {'D':>5s}", end="", flush=True)
    for W in WINDOWS:
        print(f" | W={W:>3d}", end="", flush=True)
    print(flush=True)
    print(f"  {'─'*5}", end="", flush=True)
    for _ in WINDOWS:
        print(f"-+------", end="", flush=True)
    print(flush=True)

    for D in DISTANCES:
        print(f"  {D:>5d}", end="", flush=True)
        for W in WINDOWS:
            key = (D, W)
            if key in results and results[key]["signals"] >= 10:
                r = results[key]["ratio"]
                marker = "**" if r >= 1.3 else "* " if r >= 1.1 else "  "
                print(f" | {r:4.2f}{marker}", end="", flush=True)
            else:
                print(f" |   -  ", end="", flush=True)
        print(flush=True)


def top_n(results, n=10, min_signals=30):
    """Return top N results sorted by ratio, with minimum signals."""
    filtered = [(k, v) for k, v in results.items() if v["signals"] >= min_signals]
    filtered.sort(key=lambda x: x[1]["ratio"], reverse=True)
    return filtered[:n]


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    t_start = time.time()
    print("=" * 70, flush=True)
    print("  VinciCasa Phase 3 — Signal Pattern Sweep (SYNTHETIC DATA)", flush=True)
    print("=" * 70, flush=True)
    print(f"  N_DRAWS = {N_DRAWS}, SEED = {SEED}", flush=True)
    print(f"  P_BASELINE = {P_BASELINE:.6f} (1/{1/P_BASELINE:.1f})", flush=True)
    print(f"  Windows: {WINDOWS}", flush=True)

    # Generate synthetic data
    print("\n  Generating synthetic data...", flush=True)
    draws = generate_synthetic_data(N_DRAWS, SEED)
    print(f"  Generated {len(draws)} synthetic draws", flush=True)

    # Split: discovery (first half) / validation (second half)
    mid = N_DRAWS // 2
    disc_draws = draws[:mid]
    val_draws = draws[mid:]
    print(f"  Discovery: draws 0-{mid-1} ({len(disc_draws)})", flush=True)
    print(f"  Validation: draws {mid}-{N_DRAWS-1} ({len(val_draws)})", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 3A: Sum × Window
    # ═══════════════════════════════════════════════════════════════════════
    disc_sums = sweep_sums_fast(disc_draws, "DISCOVERY")
    val_sums = sweep_sums_fast(val_draws, "VALIDATION")

    print_heatmap_sums(disc_sums, "Discovery — Sum × Window ratios")

    # Top 10 discovery with validation
    top10_sums = top_n(disc_sums, n=10, min_signals=20)
    print(f"\n  Top 10 Sum configurations (Discovery → Validation):", flush=True)
    print(f"  {'Config':>12s} | {'Signals':>8s} | {'Hits':>5s} | {'D-Ratio':>8s} | {'V-Ratio':>8s} | {'V-Signals':>10s}", flush=True)
    print(f"  {'─'*12}-+{'─'*9}-+{'─'*6}-+{'─'*9}-+{'─'*9}-+{'─'*11}", flush=True)
    for (S, W), v in top10_sums:
        vk = val_sums.get((S, W), {"ratio": 0, "signals": 0})
        print(f"  S={S:2d},W={W:3d} | {v['signals']:8d} | {v['hits']:5d} | {v['ratio']:8.4f} | {vk['ratio']:8.4f} | {vk['signals']:10d}", flush=True)

    # 5-fold CV on top 5
    top5_sums = top10_sums[:5]
    print(f"\n  5-Fold CV on top 5 Sum configurations:", flush=True)
    print(f"  {'Config':>12s} | {'CV Mean':>8s} | {'CV Min':>8s} | {'CV Max':>8s} | {'Folds':>30s}", flush=True)
    print(f"  {'─'*12}-+{'─'*9}-+{'─'*9}-+{'─'*9}-+{'─'*31}", flush=True)
    cv_sums_results = []
    for (S, W), v in top5_sums:
        config_fn = make_sum_config(S, W)
        fold_ratios = cross_validate_config(draws, config_fn, n_folds=5)
        mean_r = sum(fold_ratios) / len(fold_ratios)
        min_r = min(fold_ratios)
        max_r = max(fold_ratios)
        folds_str = " ".join(f"{r:.3f}" for r in fold_ratios)
        print(f"  S={S:2d},W={W:3d} | {mean_r:8.4f} | {min_r:8.4f} | {max_r:8.4f} | {folds_str}", flush=True)
        cv_sums_results.append(((S, W), v, mean_r, min_r))

    # ═══════════════════════════════════════════════════════════════════════
    # 3B: Proximity × Window
    # ═══════════════════════════════════════════════════════════════════════
    disc_prox = sweep_proximity(disc_draws, "DISCOVERY")
    val_prox = sweep_proximity(val_draws, "VALIDATION")

    print_heatmap_prox(disc_prox, "Discovery — Proximity × Window ratios")

    top10_prox = top_n(disc_prox, n=10, min_signals=20)
    print(f"\n  Top 10 Proximity configurations (Discovery → Validation):", flush=True)
    print(f"  {'Config':>12s} | {'Signals':>8s} | {'Hits':>5s} | {'D-Ratio':>8s} | {'V-Ratio':>8s} | {'V-Signals':>10s}", flush=True)
    print(f"  {'─'*12}-+{'─'*9}-+{'─'*6}-+{'─'*9}-+{'─'*9}-+{'─'*11}", flush=True)
    for (D, W), v in top10_prox:
        vk = val_prox.get((D, W), {"ratio": 0, "signals": 0})
        print(f"  D={D:2d},W={W:3d} | {v['signals']:8d} | {v['hits']:5d} | {v['ratio']:8.4f} | {vk['ratio']:8.4f} | {vk['signals']:10d}", flush=True)

    top5_prox = top10_prox[:5]
    print(f"\n  5-Fold CV on top 5 Proximity configurations:", flush=True)
    print(f"  {'Config':>12s} | {'CV Mean':>8s} | {'CV Min':>8s} | {'CV Max':>8s} | {'Folds':>30s}", flush=True)
    print(f"  {'─'*12}-+{'─'*9}-+{'─'*9}-+{'─'*9}-+{'─'*31}", flush=True)
    cv_prox_results = []
    for (D, W), v in top5_prox:
        config_fn = make_prox_config(D, W)
        fold_ratios = cross_validate_config(draws, config_fn, n_folds=5)
        mean_r = sum(fold_ratios) / len(fold_ratios)
        min_r = min(fold_ratios)
        max_r = max(fold_ratios)
        folds_str = " ".join(f"{r:.3f}" for r in fold_ratios)
        print(f"  D={D:2d},W={W:3d} | {mean_r:8.4f} | {min_r:8.4f} | {max_r:8.4f} | {folds_str}", flush=True)
        cv_prox_results.append(((D, W), v, mean_r, min_r))

    # ═══════════════════════════════════════════════════════════════════════
    # 3C: Decade × Window
    # ═══════════════════════════════════════════════════════════════════════
    disc_dec = sweep_decade(disc_draws, "DISCOVERY")
    val_dec = sweep_decade(val_draws, "VALIDATION")

    print(f"\n  Decade × Window results (Discovery → Validation):", flush=True)
    print(f"  {'W':>5s} | {'Signals':>8s} | {'Hits':>5s} | {'D-Ratio':>8s} | {'V-Ratio':>8s} | {'V-Signals':>10s}", flush=True)
    print(f"  {'─'*5}-+{'─'*9}-+{'─'*6}-+{'─'*9}-+{'─'*9}-+{'─'*11}", flush=True)
    for W in WINDOWS:
        d = disc_dec[W]
        v = val_dec[W]
        print(f"  {W:5d} | {d['signals']:8d} | {d['hits']:5d} | {d['ratio']:8.4f} | {v['ratio']:8.4f} | {v['signals']:10d}", flush=True)

    # CV on top 5 decade configs
    decade_sorted = sorted(disc_dec.items(), key=lambda x: x[1]["ratio"], reverse=True)
    top5_dec = decade_sorted[:5]
    print(f"\n  5-Fold CV on top 5 Decade configurations:", flush=True)
    print(f"  {'Config':>8s} | {'CV Mean':>8s} | {'CV Min':>8s} | {'CV Max':>8s} | {'Folds':>30s}", flush=True)
    print(f"  {'─'*8}-+{'─'*9}-+{'─'*9}-+{'─'*9}-+{'─'*31}", flush=True)
    cv_dec_results = []
    for W, v in top5_dec:
        config_fn = make_decade_config(W)
        fold_ratios = cross_validate_config(draws, config_fn, n_folds=5)
        mean_r = sum(fold_ratios) / len(fold_ratios)
        min_r = min(fold_ratios)
        max_r = max(fold_ratios)
        folds_str = " ".join(f"{r:.3f}" for r in fold_ratios)
        print(f"  W={W:5d} | {mean_r:8.4f} | {min_r:8.4f} | {max_r:8.4f} | {folds_str}", flush=True)
        cv_dec_results.append((W, v, mean_r, min_r))

    # ═══════════════════════════════════════════════════════════════════════
    # COMPARISON TABLE
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}", flush=True)
    print(f"  COMPARISON TABLE — Best configurations across all methods", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"  {'Method':<20s} | {'Best Params':<15s} | {'Discovery':>10s} | {'Validation':>10s} | {'CV Mean':>8s} | {'CV Min':>8s}", flush=True)
    print(f"  {'─'*20}-+{'─'*16}-+{'─'*11}-+{'─'*11}-+{'─'*9}-+{'─'*9}", flush=True)

    comparison_rows = []

    # Best sum
    if cv_sums_results:
        best = cv_sums_results[0]
        (S, W), v, cv_mean, cv_min = best
        vk = val_sums.get((S, W), {"ratio": 0})
        row = ("Sum", f"S={S},W={W}", v["ratio"], vk["ratio"], cv_mean, cv_min)
        comparison_rows.append(row)
        print(f"  {'Sum':<20s} | {'S='+str(S)+',W='+str(W):<15s} | {v['ratio']:10.4f} | {vk['ratio']:10.4f} | {cv_mean:8.4f} | {cv_min:8.4f}", flush=True)

    # Best proximity
    if cv_prox_results:
        best = cv_prox_results[0]
        (D, W), v, cv_mean, cv_min = best
        vk = val_prox.get((D, W), {"ratio": 0})
        row = ("Proximity", f"D={D},W={W}", v["ratio"], vk["ratio"], cv_mean, cv_min)
        comparison_rows.append(row)
        print(f"  {'Proximity':<20s} | {'D='+str(D)+',W='+str(W):<15s} | {v['ratio']:10.4f} | {vk['ratio']:10.4f} | {cv_mean:8.4f} | {cv_min:8.4f}", flush=True)

    # Best decade
    if cv_dec_results:
        best = cv_dec_results[0]
        W_best, v, cv_mean, cv_min = best
        vk = val_dec[W_best]
        row = ("Decade", f"W={W_best}", v["ratio"], vk["ratio"], cv_mean, cv_min)
        comparison_rows.append(row)
        print(f"  {'Decade':<20s} | {'W='+str(W_best):<15s} | {v['ratio']:10.4f} | {vk['ratio']:10.4f} | {cv_mean:8.4f} | {cv_min:8.4f}", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    # KEY QUESTION
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}", flush=True)
    print(f"  KEY QUESTION: With P(pair)=1/78 (5x Lotto), do filters", flush=True)
    print(f"  produce higher ratio on VinciCasa vs Lotto?", flush=True)
    print(f"{'='*70}", flush=True)

    best_ratio = max(r[2] for r in comparison_rows) if comparison_rows else 0
    print(f"  Best discovery ratio across all methods: {max(r[3] for r in comparison_rows) if comparison_rows else 0:.4f}", flush=True)
    print(f"  Best validation ratio: {max(r[4] for r in comparison_rows) if comparison_rows else 0:.4f}", flush=True)
    print(f"  Best CV mean ratio: {max(r[5] for r in comparison_rows) if comparison_rows else 0:.4f}", flush=True)
    print(flush=True)

    if best_ratio <= 1.05:
        verdict = "NO EDGE — Synthetic uniform data shows no filter advantage (as expected)."
    elif best_ratio <= 1.2:
        verdict = "WEAK — Marginal advantage, likely noise on synthetic data."
    else:
        verdict = "SUSPICIOUS — High ratio on synthetic data suggests overfitting or bug."

    print(f"  Verdict: {verdict}", flush=True)
    print(f"  Note: These results are from SYNTHETIC uniform random data.", flush=True)
    print(f"  True signal can only emerge from REAL VinciCasa data.", flush=True)

    elapsed_total = time.time() - t_start
    print(f"\n  Total elapsed: {elapsed_total:.1f}s", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    # Write report
    # ═══════════════════════════════════════════════════════════════════════
    report = generate_report(disc_sums, val_sums, disc_prox, val_prox,
                              disc_dec, val_dec, cv_sums_results,
                              cv_prox_results, cv_dec_results,
                              comparison_rows, verdict, elapsed_total)
    append_report(report)

    # ═══════════════════════════════════════════════════════════════════════
    # ntfy notification
    # ═══════════════════════════════════════════════════════════════════════
    send_ntfy(comparison_rows, verdict, elapsed_total)

    print("\n  Done.", flush=True)


def generate_report(disc_sums, val_sums, disc_prox, val_prox,
                     disc_dec, val_dec, cv_sums, cv_prox, cv_dec,
                     comparison, verdict, elapsed):
    """Generate markdown report sections 4-6."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""

---

## 4. Signal Pattern Sweep — Sum x Window (Phase 3A, SYNTHETIC)

**Generated:** {now}
**Dataset:** {N_DRAWS} SYNTHETIC uniform random draws (seed={SEED})
**Method:** Discovery on first half ({N_DRAWS//2} draws), validation on second half
**Baseline:** P(pair) = 10/780 = 1/78

### 4.1 Heatmap — Sum × Window Discovery Ratios (step 5)

| Sum |"""

    for W in WINDOWS:
        report += f" W={W} |"
    report += "\n|-----|"
    for _ in WINDOWS:
        report += "------|"
    report += "\n"

    for S in range(5, 80, 5):
        report += f"| {S} |"
        for W in WINDOWS:
            key = (S, W)
            if key in disc_sums and disc_sums[key]["signals"] >= 10:
                r = disc_sums[key]["ratio"]
                marker = " **" if r >= 1.3 else " *" if r >= 1.1 else ""
                report += f" {r:.2f}{marker} |"
            else:
                report += " - |"
        report += "\n"

    # Top 10 discovery
    top10_s = top_n(disc_sums, n=10, min_signals=20)
    report += """
### 4.2 Top 10 Sum Configurations

| Config | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
"""
    for (S, W), v in top10_s:
        vk = val_sums.get((S, W), {"ratio": 0})
        report += f"| S={S}, W={W} | {v['signals']} | {v['hits']} | {v['ratio']:.4f} | {vk['ratio']:.4f} |\n"

    # CV results
    if cv_sums:
        report += """
### 4.3 5-Fold CV — Top 5 Sum Configurations

| Config | CV Mean | CV Min | CV Max |
|--------|---------|--------|--------|
"""
        for (S, W), v, mean_r, min_r in cv_sums:
            max_r = v["ratio"]  # approximate
            report += f"| S={S}, W={W} | {mean_r:.4f} | {min_r:.4f} | - |\n"

    # Section 5: Proximity
    DISTANCES = [1, 2, 3, 5, 8, 10, 15]
    report += f"""

---

## 5. Signal Pattern Sweep — Proximity x Window (Phase 3B, SYNTHETIC)

### 5.1 Heatmap — Proximity × Window Discovery Ratios

| D |"""

    for W in WINDOWS:
        report += f" W={W} |"
    report += "\n|---|"
    for _ in WINDOWS:
        report += "------|"
    report += "\n"

    for D in DISTANCES:
        report += f"| {D} |"
        for W in WINDOWS:
            key = (D, W)
            if key in disc_prox and disc_prox[key]["signals"] >= 10:
                r = disc_prox[key]["ratio"]
                marker = " **" if r >= 1.3 else " *" if r >= 1.1 else ""
                report += f" {r:.2f}{marker} |"
            else:
                report += " - |"
        report += "\n"

    top10_p = top_n(disc_prox, n=10, min_signals=20)
    report += """
### 5.2 Top 10 Proximity Configurations

| Config | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
"""
    for (D, W), v in top10_p:
        vk = val_prox.get((D, W), {"ratio": 0})
        report += f"| D={D}, W={W} | {v['signals']} | {v['hits']} | {v['ratio']:.4f} | {vk['ratio']:.4f} |\n"

    if cv_prox:
        report += """
### 5.3 5-Fold CV — Top 5 Proximity Configurations

| Config | CV Mean | CV Min |
|--------|---------|--------|
"""
        for (D, W), v, mean_r, min_r in cv_prox:
            report += f"| D={D}, W={W} | {mean_r:.4f} | {min_r:.4f} |\n"

    # Section 6: Decade
    report += f"""

---

## 6. Decade Filter Sweep (Phase 3C, SYNTHETIC)

4 decades: 1-10, 11-20, 21-30, 31-40.
Same-decade pairs with freq+rit filter.

### 6.1 Decade × Window Results

| Window | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
"""
    for W in WINDOWS:
        d = disc_dec[W]
        v = val_dec[W]
        report += f"| {W} | {d['signals']} | {d['hits']} | {d['ratio']:.4f} | {v['ratio']:.4f} |\n"

    if cv_dec:
        report += """
### 6.2 5-Fold CV — Top 5 Decade Configurations

| Config | CV Mean | CV Min |
|--------|---------|--------|
"""
        for W, v, mean_r, min_r in cv_dec:
            report += f"| W={W} | {mean_r:.4f} | {min_r:.4f} |\n"

    # Comparison
    report += f"""

---

## Phase 3 Summary — Comparison Table (SYNTHETIC)

| Method | Best Params | Discovery | Validation | CV Mean | CV Min |
|--------|-------------|-----------|------------|---------|--------|
"""
    for method, params, disc, val, cv_mean, cv_min in comparison:
        report += f"| {method} | {params} | {disc:.4f} | {val:.4f} | {cv_mean:.4f} | {cv_min:.4f} |\n"

    report += f"""
**Key Question:** With P(pair)=1/78 (5x Lotto), do filters produce higher ratio?

**Verdict:** {verdict}

> These results use SYNTHETIC uniform random data (seed=42).
> No genuine signal is expected. True patterns can only emerge from REAL VinciCasa data.
> Re-run Phase 3 after full real data ingestion.

*Phase 3 completed in {elapsed:.1f}s*
"""
    return report


def append_report(report_text):
    """Append to ANALYSIS_REPORT.md."""
    print("\n  Appending report to ANALYSIS_REPORT.md...", flush=True)
    try:
        with open(REPORT_PATH, "a") as f:
            f.write(report_text)
        print("  Report appended successfully.", flush=True)
    except Exception as e:
        print(f"  ERROR writing report: {e}", flush=True)


def send_ntfy(comparison, verdict, elapsed):
    """Send summary notification via ntfy."""
    print("\n  Sending ntfy notification...", flush=True)

    lines = ["VinciCasa Phase 3 — SYNTHETIC Signal Sweep"]
    lines.append(f"Elapsed: {elapsed:.0f}s")
    lines.append("")
    for method, params, disc, val, cv_mean, cv_min in comparison:
        lines.append(f"{method} ({params}): D={disc:.3f} V={val:.3f} CV={cv_mean:.3f}")
    lines.append("")
    lines.append(verdict)

    body = "\n".join(lines)

    try:
        req = urllib.request.Request(
            NTFY_URL,
            data=body.encode("utf-8"),
            headers={
                "Title": "VinciCasa Phase 3 Complete",
                "Priority": "default",
                "Tags": "chart_with_upwards_trend",
            },
        )
        resp = urllib.request.urlopen(req)
        print(f"  ntfy response: {resp.status}", flush=True)
    except Exception as e:
        print(f"  ntfy error: {e}", flush=True)


if __name__ == "__main__":
    main()
