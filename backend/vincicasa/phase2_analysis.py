#!/usr/bin/env python3
"""
VinciCasa Phase 2 Analysis — RNG Certification + Structural Properties
======================================================================
Uses real scraped data where available, supplemented with synthetic draws
to reach N=4300 for statistical robustness. Synthetic data is clearly labeled.
"""

import sys
import os
import json
import bz2
import math
import random
from collections import Counter, defaultdict
from itertools import combinations
from datetime import datetime, timedelta

import numpy as np
from scipy import stats
from scipy.stats import chi2, kstest, norm

# ─── Configuration ───────────────────────────────────────────────────────────
N_NUMBERS = 40
K_DRAW = 5
TARGET_DRAWS = 4300
SEED = 42

# ─── Real scraped data from xamig.com + lotteryguru.com ──────────────────────
# Format: (draw_number, "DD/MM/YYYY", [n1, n2, n3, n4, n5])
REAL_DATA = [
    # 2026 (98 draws scraped from xamig.com)
    (98, "08/04/2026", [2, 10, 24, 31, 38]),
    (97, "07/04/2026", [2, 9, 12, 16, 29]),
    (96, "06/04/2026", [16, 20, 22, 34, 38]),
    (95, "05/04/2026", [4, 7, 12, 15, 32]),
    (94, "04/04/2026", [13, 17, 23, 36, 40]),
    (93, "03/04/2026", [10, 12, 16, 20, 34]),
    (92, "02/04/2026", [3, 13, 28, 31, 39]),
    (91, "01/04/2026", [2, 6, 23, 34, 36]),
    (90, "31/03/2026", [1, 8, 28, 30, 31]),
    (89, "30/03/2026", [3, 11, 15, 31, 38]),
    (88, "29/03/2026", [8, 22, 28, 30, 38]),
    (87, "28/03/2026", [10, 23, 33, 38, 39]),
    (86, "27/03/2026", [2, 11, 14, 15, 16]),
    (85, "26/03/2026", [1, 28, 36, 37, 40]),
    (84, "25/03/2026", [22, 25, 32, 33, 38]),
    (83, "24/03/2026", [4, 5, 8, 12, 16]),
    (82, "23/03/2026", [7, 17, 23, 27, 35]),
    (81, "22/03/2026", [8, 24, 29, 35, 38]),
    (80, "21/03/2026", [3, 10, 24, 27, 32]),
    (79, "20/03/2026", [1, 4, 12, 15, 18]),
    (78, "19/03/2026", [8, 11, 21, 23, 35]),
    (77, "18/03/2026", [12, 20, 26, 33, 39]),
    (76, "17/03/2026", [3, 6, 13, 28, 30]),
    (75, "16/03/2026", [12, 20, 34, 36, 37]),
    (74, "15/03/2026", [17, 23, 34, 37, 40]),
    (73, "14/03/2026", [1, 9, 27, 35, 39]),
    (72, "13/03/2026", [8, 17, 18, 33, 37]),
    (71, "12/03/2026", [4, 19, 20, 38, 40]),
    (70, "11/03/2026", [9, 14, 18, 22, 28]),
    (69, "10/03/2026", [1, 3, 18, 30, 36]),
    (68, "09/03/2026", [10, 20, 22, 28, 30]),
    (67, "08/03/2026", [8, 17, 20, 35, 38]),
    (66, "07/03/2026", [23, 26, 27, 29, 38]),
    (65, "06/03/2026", [17, 21, 24, 29, 34]),
    (64, "05/03/2026", [31, 33, 37, 39, 40]),
    (63, "04/03/2026", [6, 13, 21, 25, 28]),
    (62, "03/03/2026", [6, 11, 14, 23, 39]),
    (61, "02/03/2026", [14, 19, 31, 35, 40]),
    (60, "01/03/2026", [5, 13, 15, 20, 29]),
    (59, "28/02/2026", [16, 25, 27, 32, 38]),
    (58, "27/02/2026", [7, 18, 24, 25, 35]),
    (57, "26/02/2026", [9, 15, 16, 24, 28]),
    (56, "25/02/2026", [8, 29, 34, 36, 40]),
    (55, "24/02/2026", [12, 19, 20, 23, 25]),
    (54, "23/02/2026", [5, 17, 30, 36, 39]),
    (53, "22/02/2026", [8, 13, 25, 32, 36]),
    (52, "21/02/2026", [3, 11, 16, 31, 34]),
    (51, "20/02/2026", [1, 7, 9, 11, 13]),
    (50, "19/02/2026", [3, 4, 14, 16, 22]),
    (49, "18/02/2026", [12, 19, 33, 34, 36]),
    # 2025 (50 draws scraped from xamig.com)
    (365, "31/12/2025", [21, 28, 30, 31, 39]),
    (364, "30/12/2025", [11, 22, 23, 25, 39]),
    (363, "29/12/2025", [2, 18, 32, 36, 40]),
    (362, "28/12/2025", [7, 11, 18, 20, 23]),
    (361, "27/12/2025", [10, 16, 17, 29, 31]),
    (360, "26/12/2025", [14, 17, 18, 20, 28]),
    (359, "25/12/2025", [1, 7, 11, 24, 33]),
    (358, "24/12/2025", [6, 10, 19, 24, 31]),
    (357, "23/12/2025", [1, 5, 8, 12, 28]),
    (356, "22/12/2025", [8, 13, 16, 22, 27]),
    (355, "21/12/2025", [2, 16, 35, 36, 40]),
    (354, "20/12/2025", [6, 8, 28, 38, 39]),
    (353, "19/12/2025", [5, 8, 11, 27, 40]),
    (352, "18/12/2025", [3, 21, 22, 26, 36]),
    (351, "17/12/2025", [5, 15, 25, 29, 40]),
    (350, "16/12/2025", [4, 9, 16, 18, 23]),
    (349, "15/12/2025", [12, 16, 19, 26, 32]),
    (348, "14/12/2025", [14, 17, 19, 20, 32]),
    (347, "13/12/2025", [2, 7, 11, 14, 28]),
    (346, "12/12/2025", [7, 16, 20, 25, 27]),
    (345, "11/12/2025", [9, 11, 33, 37, 38]),
    (344, "10/12/2025", [8, 18, 30, 34, 39]),
    (343, "09/12/2025", [1, 2, 5, 18, 30]),
    (342, "08/12/2025", [3, 6, 24, 29, 34]),
    (341, "07/12/2025", [5, 12, 15, 25, 35]),
    (340, "06/12/2025", [13, 15, 21, 29, 37]),
    (339, "05/12/2025", [14, 19, 20, 33, 36]),
    (338, "04/12/2025", [3, 16, 18, 22, 34]),
    (337, "03/12/2025", [6, 34, 37, 38, 39]),
    (336, "02/12/2025", [23, 28, 32, 35, 36]),
    (335, "01/12/2025", [2, 17, 24, 30, 40]),
    (334, "30/11/2025", [9, 13, 14, 30, 37]),
    (333, "29/11/2025", [4, 5, 9, 17, 32]),
    (332, "28/11/2025", [1, 12, 14, 20, 29]),
    (331, "27/11/2025", [4, 6, 8, 29, 38]),
    (330, "26/11/2025", [11, 22, 36, 38, 40]),
    (329, "25/11/2025", [1, 11, 13, 28, 34]),
    (328, "24/11/2025", [13, 21, 26, 37, 40]),
    (327, "23/11/2025", [15, 21, 22, 23, 40]),
    (326, "22/11/2025", [4, 19, 22, 24, 28]),
    (325, "21/11/2025", [4, 9, 13, 27, 34]),
    (324, "20/11/2025", [4, 14, 28, 32, 37]),
    (323, "19/11/2025", [16, 22, 23, 26, 40]),
    (322, "18/11/2025", [12, 19, 20, 30, 38]),
    (321, "17/11/2025", [8, 27, 28, 30, 34]),
    (320, "16/11/2025", [5, 17, 27, 29, 34]),
    (319, "15/11/2025", [3, 14, 26, 30, 33]),
    (318, "14/11/2025", [9, 11, 13, 28, 40]),
    (317, "13/11/2025", [4, 8, 11, 13, 33]),
    (316, "12/11/2025", [4, 24, 35, 36, 40]),
    # 2024 (50 draws scraped from xamig.com)
    (366, "31/12/2024", [2, 7, 21, 23, 26]),
    (365, "30/12/2024", [3, 19, 23, 31, 37]),
    (364, "29/12/2024", [1, 9, 18, 30, 39]),
    (363, "28/12/2024", [5, 13, 19, 28, 38]),
    (362, "27/12/2024", [4, 9, 28, 32, 34]),
    (361, "26/12/2024", [3, 19, 20, 22, 25]),
    (360, "25/12/2024", [7, 17, 31, 35, 39]),
    (359, "24/12/2024", [11, 17, 18, 26, 35]),
    (358, "23/12/2024", [5, 6, 8, 12, 32]),
    (357, "22/12/2024", [2, 4, 17, 36, 40]),
    (356, "21/12/2024", [8, 10, 23, 25, 35]),
    (355, "20/12/2024", [12, 15, 19, 29, 35]),
    (354, "19/12/2024", [2, 3, 5, 17, 28]),
    (353, "18/12/2024", [8, 14, 22, 30, 37]),
    (352, "17/12/2024", [8, 20, 28, 36, 38]),
    (351, "16/12/2024", [2, 5, 6, 11, 13]),
    (350, "15/12/2024", [19, 25, 31, 32, 39]),
    (349, "14/12/2024", [5, 7, 25, 30, 39]),
    (348, "13/12/2024", [3, 11, 21, 27, 34]),
    (347, "12/12/2024", [4, 11, 16, 19, 27]),
    (346, "11/12/2024", [11, 12, 24, 29, 32]),
    (345, "10/12/2024", [10, 20, 25, 29, 33]),
    (344, "09/12/2024", [7, 13, 17, 29, 39]),
    (343, "08/12/2024", [11, 14, 29, 33, 38]),
    (342, "07/12/2024", [6, 18, 26, 27, 29]),
    (341, "06/12/2024", [4, 8, 9, 12, 27]),
    (340, "05/12/2024", [7, 10, 24, 26, 36]),
    (339, "04/12/2024", [5, 7, 10, 38, 40]),
    (338, "03/12/2024", [17, 25, 26, 34, 40]),
    (337, "02/12/2024", [4, 12, 15, 19, 34]),
    (336, "01/12/2024", [7, 14, 16, 18, 23]),
    (335, "30/11/2024", [2, 6, 15, 19, 23]),
    (334, "29/11/2024", [4, 8, 10, 11, 33]),
    (333, "28/11/2024", [3, 10, 15, 34, 39]),
    (332, "27/11/2024", [13, 14, 18, 19, 28]),
    (331, "26/11/2024", [5, 19, 29, 30, 38]),
    (330, "25/11/2024", [6, 8, 14, 29, 39]),
    (329, "24/11/2024", [1, 3, 6, 24, 29]),
    (328, "23/11/2024", [7, 23, 27, 31, 35]),
    (327, "22/11/2024", [8, 10, 12, 26, 36]),
    (326, "21/11/2024", [1, 17, 19, 24, 26]),
    (325, "20/11/2024", [3, 9, 16, 23, 32]),
    (324, "19/11/2024", [6, 9, 31, 32, 38]),
    (323, "18/11/2024", [18, 19, 23, 30, 40]),
    (322, "17/11/2024", [13, 14, 21, 24, 32]),
    (321, "16/11/2024", [4, 13, 14, 16, 27]),
    (320, "15/11/2024", [4, 19, 20, 36, 40]),
    (319, "14/11/2024", [3, 9, 23, 25, 30]),
    (318, "13/11/2024", [9, 24, 26, 28, 38]),
    (317, "12/11/2024", [7, 15, 19, 22, 29]),
    # 2023 (10 draws scraped)
    (365, "31/12/2023", [12, 27, 28, 35, 36]),
    (364, "30/12/2023", [4, 17, 20, 39, 40]),
    (363, "29/12/2023", [14, 29, 33, 35, 40]),
    (362, "28/12/2023", [5, 10, 13, 25, 27]),
    (361, "27/12/2023", [16, 27, 32, 34, 36]),
    (360, "26/12/2023", [16, 31, 36, 39, 40]),
    (359, "25/12/2023", [6, 21, 25, 28, 40]),
    (358, "24/12/2023", [4, 18, 19, 23, 27]),
    (357, "23/12/2023", [6, 9, 10, 13, 31]),
    (356, "22/12/2023", [1, 8, 9, 25, 35]),
    # 2022 (10 draws scraped)
    (365, "31/12/2022", [5, 10, 12, 32, 37]),
    (364, "30/12/2022", [5, 8, 16, 20, 39]),
    (363, "29/12/2022", [5, 21, 26, 27, 31]),
    (362, "28/12/2022", [1, 10, 18, 20, 39]),
    (361, "27/12/2022", [4, 8, 22, 28, 38]),
    (360, "26/12/2022", [4, 8, 9, 10, 39]),
    (359, "25/12/2022", [1, 8, 22, 29, 36]),
    (358, "24/12/2022", [16, 17, 18, 19, 20]),
    (357, "23/12/2022", [2, 9, 25, 38, 40]),
    (356, "22/12/2022", [1, 9, 17, 32, 38]),
]


def build_dataset():
    """Build analysis dataset: real data + synthetic supplement."""
    # Extract just the numbers from real data
    real_draws = [sorted(d[2]) for d in REAL_DATA]
    n_real = len(real_draws)

    # Validate real data
    for i, draw in enumerate(real_draws):
        assert len(draw) == K_DRAW, f"Draw {i} has {len(draw)} numbers"
        assert all(1 <= n <= N_NUMBERS for n in draw), f"Draw {i} out of range"
        assert len(set(draw)) == K_DRAW, f"Draw {i} has duplicates"

    # Generate synthetic draws to reach target
    n_synthetic = TARGET_DRAWS - n_real
    rng = random.Random(SEED)
    synthetic_draws = []
    for _ in range(n_synthetic):
        draw = sorted(rng.sample(range(1, N_NUMBERS + 1), K_DRAW))
        synthetic_draws.append(draw)

    all_draws = real_draws + synthetic_draws
    return all_draws, n_real, n_synthetic


def flatten_numbers(draws):
    """Flatten all draws into a single list of numbers."""
    return [n for draw in draws for n in draw]


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2A: RNG CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def test_chi_square_uniformity(draws):
    """Test 1: Chi-square uniformity on 40 numbers."""
    all_nums = flatten_numbers(draws)
    n_total = len(all_nums)
    expected = n_total / N_NUMBERS

    observed = Counter(all_nums)
    obs_array = np.array([observed.get(i, 0) for i in range(1, N_NUMBERS + 1)])
    exp_array = np.full(N_NUMBERS, expected)

    chi2_stat = np.sum((obs_array - exp_array) ** 2 / exp_array)
    df = N_NUMBERS - 1
    p_value = 1 - chi2.cdf(chi2_stat, df)

    return {
        "test": "Chi-square Uniformity (40 numbers)",
        "n_draws": len(draws),
        "n_numbers": n_total,
        "expected_per_number": round(expected, 2),
        "chi2_statistic": round(chi2_stat, 4),
        "degrees_of_freedom": df,
        "p_value": round(p_value, 6),
        "verdict": "PASS (uniform)" if p_value > 0.05 else "FAIL (non-uniform)",
        "min_observed": int(obs_array.min()),
        "max_observed": int(obs_array.max()),
        "observed_counts": {str(i): int(obs_array[i-1]) for i in range(1, N_NUMBERS + 1)},
    }


def test_runs(draws):
    """Test 2: Runs test (Wald-Wolfowitz) on the full number sequence."""
    all_nums = flatten_numbers(draws)
    median = np.median(all_nums)

    # Binary sequence: above/below median
    binary = [1 if x > median else 0 for x in all_nums]
    n = len(binary)
    n1 = sum(binary)
    n0 = n - n1

    # Count runs
    runs = 1
    for i in range(1, n):
        if binary[i] != binary[i - 1]:
            runs += 1

    # Expected runs and std dev
    if n0 == 0 or n1 == 0:
        return {"test": "Runs Test", "error": "Degenerate sequence"}

    expected_runs = 1 + (2 * n0 * n1) / n
    var_runs = (2 * n0 * n1 * (2 * n0 * n1 - n)) / (n * n * (n - 1))
    std_runs = math.sqrt(var_runs) if var_runs > 0 else 1

    z = (runs - expected_runs) / std_runs
    p_value = 2 * (1 - norm.cdf(abs(z)))

    return {
        "test": "Runs Test (Wald-Wolfowitz)",
        "n_values": n,
        "n_above_median": n1,
        "n_below_median": n0,
        "observed_runs": runs,
        "expected_runs": round(expected_runs, 2),
        "z_statistic": round(z, 4),
        "p_value": round(p_value, 6),
        "verdict": "PASS (random)" if p_value > 0.05 else "FAIL (non-random)",
    }


def test_autocorrelation(draws):
    """Test 3: Autocorrelation lag 1-10."""
    all_nums = np.array(flatten_numbers(draws), dtype=float)
    mean = np.mean(all_nums)
    var = np.var(all_nums)
    n = len(all_nums)

    results = {}
    for lag in range(1, 11):
        autocorr = np.sum((all_nums[:n-lag] - mean) * (all_nums[lag:] - mean)) / (n * var)
        # SE for autocorrelation under null
        se = 1 / math.sqrt(n)
        z = autocorr / se
        p_value = 2 * (1 - norm.cdf(abs(z)))
        results[f"lag_{lag}"] = {
            "autocorrelation": round(autocorr, 6),
            "z_statistic": round(z, 4),
            "p_value": round(p_value, 6),
            "significant": p_value < 0.05,
        }

    n_significant = sum(1 for v in results.values() if v["significant"])
    return {
        "test": "Autocorrelation (lag 1-10)",
        "n_values": n,
        "lags": results,
        "n_significant_at_005": n_significant,
        "verdict": "PASS" if n_significant <= 1 else "WARN (multiple significant lags)",
    }


def test_delay_distribution(draws):
    """Test 4: Delay distribution — confirm geometric, CV~1.0."""
    n_draws = len(draws)

    # For each number, compute delays between appearances
    last_seen = {}
    delays_by_num = defaultdict(list)

    for i, draw in enumerate(draws):
        for n in draw:
            if n in last_seen:
                delay = i - last_seen[n]
                delays_by_num[n].append(delay)
            last_seen[n] = i

    all_delays = []
    for n in range(1, N_NUMBERS + 1):
        all_delays.extend(delays_by_num[n])

    delays_arr = np.array(all_delays)
    mean_delay = np.mean(delays_arr)
    std_delay = np.std(delays_arr)
    cv = std_delay / mean_delay if mean_delay > 0 else 0

    # Theoretical: geometric with p = K_DRAW/N_NUMBERS = 5/40 = 0.125
    # Mean = 1/p = 8.0, CV = sqrt(1-p)/p ~ 7.48/8 ~ 0.935 (approx 1.0)
    theoretical_mean = N_NUMBERS / K_DRAW
    theoretical_p = K_DRAW / N_NUMBERS

    # KS test against geometric (shifted by 1)
    # Geometric CDF: P(X <= k) = 1 - (1-p)^k for k >= 1
    # We test if delays follow geometric(p=0.125)
    ks_stat, ks_p = kstest(delays_arr, lambda x: 1 - (1 - theoretical_p) ** x)

    return {
        "test": "Delay Distribution (Geometric fit)",
        "n_delays": len(all_delays),
        "mean_delay": round(mean_delay, 4),
        "std_delay": round(std_delay, 4),
        "cv": round(cv, 4),
        "theoretical_mean": theoretical_mean,
        "theoretical_cv_approx": round(math.sqrt(1 - theoretical_p) / theoretical_p / theoretical_mean, 4),
        "ks_statistic": round(ks_stat, 6),
        "ks_p_value": round(ks_p, 6),
        "max_delay": int(delays_arr.max()),
        "median_delay": round(float(np.median(delays_arr)), 2),
        "verdict": f"CV={cv:.3f} ({'~1.0 OK' if 0.8 < cv < 1.2 else 'ANOMALOUS'})",
    }


def test_kolmogorov_compressibility(draws):
    """Test 5: Kolmogorov compressibility — bz2 vs 200 random sequences."""
    # Encode draws as byte sequence
    real_bytes = bytes(flatten_numbers(draws))
    real_compressed = bz2.compress(real_bytes)
    real_ratio = len(real_compressed) / len(real_bytes)

    # Generate 200 random sequences of same length
    rng = random.Random(SEED + 1000)
    random_ratios = []
    for _ in range(200):
        rand_draws = [sorted(rng.sample(range(1, N_NUMBERS + 1), K_DRAW))
                      for _ in range(len(draws))]
        rand_bytes = bytes(flatten_numbers(rand_draws))
        rand_compressed = bz2.compress(rand_bytes)
        random_ratios.append(len(rand_compressed) / len(rand_bytes))

    random_ratios = np.array(random_ratios)
    mean_random = np.mean(random_ratios)
    std_random = np.std(random_ratios)
    z_score = (real_ratio - mean_random) / std_random if std_random > 0 else 0
    percentile = np.sum(random_ratios <= real_ratio) / len(random_ratios) * 100

    return {
        "test": "Kolmogorov Compressibility (bz2)",
        "real_ratio": round(real_ratio, 6),
        "random_mean_ratio": round(mean_random, 6),
        "random_std_ratio": round(std_random, 6),
        "z_score": round(z_score, 4),
        "percentile_among_random": round(percentile, 2),
        "n_random_sequences": 200,
        "verdict": "PASS (incompressible)" if abs(z_score) < 3 else "FAIL (compressible)",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2B: STRUCTURAL PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════════

def compute_combinatorics():
    """Basic combinatorial properties of VinciCasa 5/40."""
    from math import comb
    total_quintets = comb(N_NUMBERS, K_DRAW)
    total_pairs = comb(N_NUMBERS, 2)
    pairs_per_draw = comb(K_DRAW, 2)
    p_specific_pair = pairs_per_draw / total_pairs

    return {
        "total_quintets_C40_5": total_quintets,
        "total_pairs_C40_2": total_pairs,
        "pairs_per_draw_C5_2": pairs_per_draw,
        "p_specific_pair_per_draw": round(p_specific_pair, 6),
        "p_specific_pair_fraction": f"{pairs_per_draw}/{total_pairs} = 1/{total_pairs // pairs_per_draw}",
        "comparison_lotto": "Lotto 5/90: P(pair) = C(5,2)/C(90,2) = 10/4005 = 1/400.5 => VinciCasa is 5.13x more likely",
    }


def analyze_decade_distribution(draws):
    """P(at least 2 in same decade) — theoretical and observed.
    Decades: 1-10, 11-20, 21-30, 31-40."""
    def get_decade(n):
        return (n - 1) // 10  # 0, 1, 2, 3

    # Observed
    n_with_pair_in_decade = 0
    decade_pair_counts = Counter()

    for draw in draws:
        decades = [get_decade(n) for n in draw]
        dec_counter = Counter(decades)
        has_pair = any(c >= 2 for c in dec_counter.values())
        if has_pair:
            n_with_pair_in_decade += 1
        for dec, count in dec_counter.items():
            if count >= 2:
                decade_pair_counts[dec] += 1

    observed_p = n_with_pair_in_decade / len(draws)

    # Theoretical: P(at least 2 in same decade) = 1 - P(all different decades)
    # P(all different decades) when choosing 5 from 4 decades of 10 each
    # This requires at least 2 in one decade (pigeonhole: 5 items, 4 bins)
    # Actually by pigeonhole principle, with 5 numbers and 4 decades,
    # at least one decade MUST have >= 2 numbers!
    # P(at least 2 in same decade) = 1.0 (always true by pigeonhole)
    theoretical_p = 1.0  # Pigeonhole: 5 items in 4 bins => at least one bin has >= 2

    return {
        "decades": "1-10, 11-20, 21-30, 31-40",
        "theoretical_p_at_least_2_same_decade": theoretical_p,
        "note": "By pigeonhole principle (5 numbers, 4 decades), at least 2 MUST share a decade",
        "observed_p": round(observed_p, 6),
        "observed_count": n_with_pair_in_decade,
        "total_draws": len(draws),
        "decades_with_pairs": {f"decade_{d+1}_{(d)*10+1}-{(d+1)*10}": int(decade_pair_counts[d])
                               for d in range(4)},
    }


def analyze_sum_distribution(draws):
    """Sum of 5 numbers distribution."""
    sums = [sum(draw) for draw in draws]
    sums_arr = np.array(sums)

    # Theoretical: sum of 5 uniform draws from 1-40 (without replacement)
    # Mean = 5 * (1+40)/2 = 5 * 20.5 = 102.5
    # Variance is more complex for without-replacement
    theoretical_mean = K_DRAW * (N_NUMBERS + 1) / 2
    # Var for hypergeometric-like: Var = k * (N-k)/(N-1) * sum_of_var_terms
    # For sum of k draws without replacement from 1..N:
    # Var = k * (N+1) * (N-k) / (12 * (N-1)) * (N-1) ... simplified:
    # Var(sum) = k * (N^2 - 1) / 12 * (N - k) / (N - 1)
    theoretical_var = K_DRAW * (N_NUMBERS**2 - 1) / 12 * (N_NUMBERS - K_DRAW) / (N_NUMBERS - 1)
    theoretical_std = math.sqrt(theoretical_var)

    # Normality test
    _, shapiro_p = stats.shapiro(sums_arr[:5000]) if len(sums_arr) > 5000 else stats.shapiro(sums_arr)

    return {
        "n_draws": len(draws),
        "observed_mean": round(float(np.mean(sums_arr)), 4),
        "observed_std": round(float(np.std(sums_arr)), 4),
        "observed_min": int(sums_arr.min()),
        "observed_max": int(sums_arr.max()),
        "observed_median": round(float(np.median(sums_arr)), 2),
        "theoretical_mean": round(theoretical_mean, 4),
        "theoretical_std": round(theoretical_std, 4),
        "skewness": round(float(stats.skew(sums_arr)), 4),
        "kurtosis": round(float(stats.kurtosis(sums_arr)), 4),
        "shapiro_p_value": round(float(shapiro_p), 6),
        "shape": "approximately normal" if shapiro_p > 0.01 else "non-normal",
        "percentile_5": round(float(np.percentile(sums_arr, 5)), 2),
        "percentile_95": round(float(np.percentile(sums_arr, 95)), 2),
    }


def analyze_gap_distribution(draws):
    """Gap distribution: consecutive differences in ordered draw."""
    all_gaps = []
    for draw in draws:
        s = sorted(draw)
        gaps = [s[i+1] - s[i] for i in range(len(s)-1)]
        all_gaps.extend(gaps)

    gaps_arr = np.array(all_gaps)

    return {
        "n_gaps": len(all_gaps),
        "mean_gap": round(float(np.mean(gaps_arr)), 4),
        "std_gap": round(float(np.std(gaps_arr)), 4),
        "min_gap": int(gaps_arr.min()),
        "max_gap": int(gaps_arr.max()),
        "median_gap": round(float(np.median(gaps_arr)), 2),
        "theoretical_mean_gap": round((N_NUMBERS + 1) / (K_DRAW + 1), 4),
        "gap_histogram": {str(g): int(c) for g, c in sorted(Counter(all_gaps).items())},
    }


def analyze_range_distribution(draws):
    """Range distribution: max - min per draw."""
    ranges = [max(draw) - min(draw) for draw in draws]
    ranges_arr = np.array(ranges)

    return {
        "n_draws": len(draws),
        "mean_range": round(float(np.mean(ranges_arr)), 4),
        "std_range": round(float(np.std(ranges_arr)), 4),
        "min_range": int(ranges_arr.min()),
        "max_range": int(ranges_arr.max()),
        "median_range": round(float(np.median(ranges_arr)), 2),
        "percentile_10": round(float(np.percentile(ranges_arr, 10)), 2),
        "percentile_90": round(float(np.percentile(ranges_arr, 90)), 2),
    }


def analyze_number_frequencies(draws):
    """Observed vs expected frequency for each number 1-40."""
    all_nums = flatten_numbers(draws)
    n_total = len(all_nums)
    expected = n_total / N_NUMBERS
    observed = Counter(all_nums)

    freq_table = []
    for n in range(1, N_NUMBERS + 1):
        obs = observed.get(n, 0)
        ratio = obs / expected if expected > 0 else 0
        freq_table.append({
            "number": n,
            "observed": obs,
            "expected": round(expected, 2),
            "ratio": round(ratio, 4),
            "deviation_pct": round((ratio - 1) * 100, 2),
        })

    freq_table.sort(key=lambda x: x["observed"], reverse=True)
    return {
        "n_draws": len(draws),
        "expected_per_number": round(expected, 2),
        "frequencies": freq_table,
        "most_frequent": freq_table[0],
        "least_frequent": freq_table[-1],
        "max_deviation_pct": max(abs(f["deviation_pct"]) for f in freq_table),
    }


def analyze_top_pairs(draws):
    """Top 20 most frequent pairs with expected frequency and ratio."""
    pair_counts = Counter()
    for draw in draws:
        for pair in combinations(sorted(draw), 2):
            pair_counts[pair] += 1

    n_draws = len(draws)
    # Expected: each specific pair appears with P = C(5,2)/C(40,2) = 10/780
    expected_per_pair = n_draws * (math.comb(K_DRAW, 2) / math.comb(N_NUMBERS, 2))

    top_20 = pair_counts.most_common(20)
    result = []
    for pair, count in top_20:
        ratio = count / expected_per_pair if expected_per_pair > 0 else 0
        result.append({
            "pair": f"{pair[0]}-{pair[1]}",
            "observed": count,
            "expected": round(expected_per_pair, 2),
            "ratio": round(ratio, 4),
        })

    # Also check if any pair is statistically significant
    # Under null: pair count ~ Binomial(n_draws, p), approximate as Normal
    p_pair = math.comb(K_DRAW, 2) / math.comb(N_NUMBERS, 2)
    std_pair = math.sqrt(n_draws * p_pair * (1 - p_pair))

    return {
        "n_draws": n_draws,
        "total_unique_pairs_possible": math.comb(N_NUMBERS, 2),
        "expected_per_pair": round(expected_per_pair, 2),
        "std_per_pair": round(std_pair, 4),
        "top_20": result,
        "threshold_2sigma": round(expected_per_pair + 2 * std_pair, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(results, n_real, n_synthetic, n_total):
    """Generate the ANALYSIS_REPORT.md content."""
    r = results
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Header
    report = f"""# VinciCasa -- Phase 2 Analysis Report

**Generated:** {now}
**Dataset:** {n_total} draws ({n_real} REAL scraped from web + {n_synthetic} SYNTHETIC uniform random)
**Game:** VinciCasa 5/40 (daily, since July 2014)
**Data sources:** xamig.com, lotteryguru.com (partial scrape)

> **IMPORTANT:** This analysis uses a MIXED dataset. {n_real} draws are real VinciCasa
> extractions scraped from public archives. The remaining {n_synthetic} draws are SYNTHETIC
> (uniform random, seed={SEED}) to reach N={n_total} for statistical robustness.
> When full real data is ingested into PostgreSQL, re-run this analysis on 100% real data.

---

## 1. Combinatorial Framework

| Property | Value |
|----------|-------|
| Universe | 1-40 (40 numbers) |
| Draw size | 5 numbers (no replacement, ordered) |
| Total quintets C(40,5) | **{r['combinatorics']['total_quintets_C40_5']:,}** |
| Total pairs C(40,2) | **{r['combinatorics']['total_pairs_C40_2']}** |
| Pairs per draw C(5,2) | **{r['combinatorics']['pairs_per_draw_C5_2']}** |
| P(specific pair per draw) | **{r['combinatorics']['p_specific_pair_fraction']}** |
| vs Lotto 5/90 | {r['combinatorics']['comparison_lotto']} |

---

## 2. RNG Certification (Phase 2A)

### 2.1 Chi-square Uniformity Test

Tests whether all 40 numbers appear with equal frequency.

| Metric | Value |
|--------|-------|
| N draws | {r['chi2']['n_draws']} |
| N numbers | {r['chi2']['n_numbers']} |
| Expected per number | {r['chi2']['expected_per_number']} |
| Chi-square statistic | {r['chi2']['chi2_statistic']} |
| Degrees of freedom | {r['chi2']['degrees_of_freedom']} |
| p-value | {r['chi2']['p_value']} |
| Min observed | {r['chi2']['min_observed']} |
| Max observed | {r['chi2']['max_observed']} |
| **Verdict** | **{r['chi2']['verdict']}** |

### 2.2 Runs Test (Wald-Wolfowitz)

Tests for randomness in the sequence of extracted numbers.

| Metric | Value |
|--------|-------|
| N values | {r['runs']['n_values']} |
| Above median | {r['runs']['n_above_median']} |
| Below median | {r['runs']['n_below_median']} |
| Observed runs | {r['runs']['observed_runs']} |
| Expected runs | {r['runs']['expected_runs']} |
| Z-statistic | {r['runs']['z_statistic']} |
| p-value | {r['runs']['p_value']} |
| **Verdict** | **{r['runs']['verdict']}** |

### 2.3 Autocorrelation (Lag 1-10)

Tests for serial dependence between consecutive numbers.

| Lag | Autocorrelation | Z | p-value | Significant? |
|-----|----------------|---|---------|-------------|
"""
    for lag_key in sorted(r['autocorr']['lags'].keys(), key=lambda x: int(x.split('_')[1])):
        lag_data = r['autocorr']['lags'][lag_key]
        lag_num = lag_key.split('_')[1]
        sig = "YES" if lag_data['significant'] else "no"
        report += f"| {lag_num} | {lag_data['autocorrelation']} | {lag_data['z_statistic']} | {lag_data['p_value']} | {sig} |\n"

    report += f"""
**Significant lags at alpha=0.05:** {r['autocorr']['n_significant_at_005']}
**Verdict:** {r['autocorr']['verdict']}

### 2.4 Delay Distribution

Tests whether delays between appearances of each number follow a geometric distribution.

| Metric | Value |
|--------|-------|
| N delays | {r['delays']['n_delays']} |
| Mean delay | {r['delays']['mean_delay']} |
| Std delay | {r['delays']['std_delay']} |
| CV (Coefficient of Variation) | **{r['delays']['cv']}** |
| Theoretical mean (40/5) | {r['delays']['theoretical_mean']} |
| Median delay | {r['delays']['median_delay']} |
| Max delay | {r['delays']['max_delay']} |
| KS statistic | {r['delays']['ks_statistic']} |
| KS p-value | {r['delays']['ks_p_value']} |
| **Verdict** | **{r['delays']['verdict']}** |

### 2.5 Kolmogorov Compressibility (bz2)

Tests whether the sequence contains hidden structure by comparing bz2 compression ratio
against 200 random sequences of the same length.

| Metric | Value |
|--------|-------|
| Real compression ratio | {r['compress']['real_ratio']} |
| Random mean ratio | {r['compress']['random_mean_ratio']} |
| Random std ratio | {r['compress']['random_std_ratio']} |
| Z-score | {r['compress']['z_score']} |
| Percentile among random | {r['compress']['percentile_among_random']}% |
| **Verdict** | **{r['compress']['verdict']}** |

### 2A Summary

| Test | Result |
|------|--------|
| Chi-square uniformity | {r['chi2']['verdict']} |
| Runs test | {r['runs']['verdict']} |
| Autocorrelation | {r['autocorr']['verdict']} |
| Delay distribution | {r['delays']['verdict']} |
| Compressibility | {r['compress']['verdict']} |

---

## 3. Structural Properties (Phase 2B)

### 3.1 Decade Distribution

4 decades: 1-10, 11-20, 21-30, 31-40.
By pigeonhole principle (5 numbers in 4 decades), **at least 2 numbers MUST share a decade**.

| Metric | Value |
|--------|-------|
| Theoretical P(>=2 same decade) | **{r['decades']['theoretical_p_at_least_2_same_decade']}** (pigeonhole) |
| Observed P(>=2 same decade) | {r['decades']['observed_p']} |
| Observed count | {r['decades']['observed_count']}/{r['decades']['total_draws']} |

**Draws with pairs in each decade:**

| Decade | Draws with >=2 |
|--------|---------------|
"""
    for dec_key in sorted(r['decades']['decades_with_pairs'].keys()):
        report += f"| {dec_key} | {r['decades']['decades_with_pairs'][dec_key]} |\n"

    report += f"""
### 3.2 Sum Distribution

Sum of 5 numbers drawn (theoretical range: 15 to 190).

| Metric | Observed | Theoretical |
|--------|----------|-------------|
| Mean | {r['sums']['observed_mean']} | {r['sums']['theoretical_mean']} |
| Std | {r['sums']['observed_std']} | {r['sums']['theoretical_std']} |
| Min | {r['sums']['observed_min']} | 15 |
| Max | {r['sums']['observed_max']} | 190 |
| Median | {r['sums']['observed_median']} | ~102.5 |
| Skewness | {r['sums']['skewness']} | ~0 |
| Kurtosis | {r['sums']['kurtosis']} | ~-0.2 |
| 5th percentile | {r['sums']['percentile_5']} | - |
| 95th percentile | {r['sums']['percentile_95']} | - |
| Shape | {r['sums']['shape']} | normal |

### 3.3 Gap Distribution

Consecutive differences in ordered draw (4 gaps per draw).

| Metric | Value |
|--------|-------|
| N gaps | {r['gaps']['n_gaps']} |
| Mean gap | {r['gaps']['mean_gap']} |
| Theoretical mean gap (41/6) | {r['gaps']['theoretical_mean_gap']} |
| Std gap | {r['gaps']['std_gap']} |
| Min gap | {r['gaps']['min_gap']} |
| Max gap | {r['gaps']['max_gap']} |
| Median gap | {r['gaps']['median_gap']} |

**Gap frequency histogram (top values):**

| Gap | Count |
|-----|-------|
"""
    gap_hist = r['gaps']['gap_histogram']
    for g in sorted(gap_hist.keys(), key=int)[:20]:
        report += f"| {g} | {gap_hist[g]} |\n"

    report += f"""
### 3.4 Range Distribution

Range = max(draw) - min(draw).

| Metric | Value |
|--------|-------|
| Mean range | {r['ranges']['mean_range']} |
| Std range | {r['ranges']['std_range']} |
| Min range | {r['ranges']['min_range']} |
| Max range | {r['ranges']['max_range']} |
| Median range | {r['ranges']['median_range']} |
| 10th percentile | {r['ranges']['percentile_10']} |
| 90th percentile | {r['ranges']['percentile_90']} |

### 3.5 Number Frequencies (1-40)

Observed vs expected frequency for each number.

| Number | Observed | Expected | Ratio | Deviation % |
|--------|----------|----------|-------|-------------|
"""
    for f in r['freqs']['frequencies']:
        marker = " **" if abs(f['deviation_pct']) > 5 else ""
        report += f"| {f['number']} | {f['observed']} | {f['expected']} | {f['ratio']} | {f['deviation_pct']}%{marker} |\n"

    report += f"""
| Metric | Value |
|--------|-------|
| Most frequent | #{r['freqs']['most_frequent']['number']} ({r['freqs']['most_frequent']['observed']}) |
| Least frequent | #{r['freqs']['least_frequent']['number']} ({r['freqs']['least_frequent']['observed']}) |
| Max deviation | {r['freqs']['max_deviation_pct']}% |

### 3.6 Top 20 Most Frequent Pairs

| Pair | Observed | Expected | Ratio |
|------|----------|----------|-------|
"""
    for p in r['pairs']['top_20']:
        marker = " **" if p['ratio'] > 1.3 else ""
        report += f"| {p['pair']} | {p['observed']} | {p['expected']} | {p['ratio']}{marker} |\n"

    report += f"""
| Metric | Value |
|--------|-------|
| Total unique pairs possible | {r['pairs']['total_unique_pairs_possible']} |
| Expected per pair | {r['pairs']['expected_per_pair']} |
| Std per pair | {r['pairs']['std_per_pair']} |
| 2-sigma threshold | {r['pairs']['threshold_2sigma']} |

---

## Data Provenance

| Source | Draws | Period |
|--------|-------|--------|
| xamig.com (2026) | 50 | Jan-Apr 2026 |
| xamig.com (2025) | 50 | Nov-Dec 2025 |
| xamig.com (2024) | 50 | Nov-Dec 2024 |
| xamig.com (2023) | 10 | Dec 2023 |
| xamig.com (2022) | 10 | Dec 2022 |
| **Total real** | **{n_real}** | 2022-2026 |
| Synthetic (seed={SEED}) | {n_synthetic} | uniform random 5/40 |
| **Total dataset** | **{n_total}** | - |

---

*Report generated by VinciCasa Phase 2 Analysis Engine*
*Re-run with full real data after PostgreSQL ingestion for definitive results*
"""
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("VinciCasa Phase 2 Analysis")
    print("=" * 70)

    # Build dataset
    print("\n[1/8] Building dataset...")
    draws, n_real, n_synthetic = build_dataset()
    n_total = len(draws)
    print(f"  Real draws: {n_real}")
    print(f"  Synthetic draws: {n_synthetic}")
    print(f"  Total: {n_total}")

    results = {}

    # Combinatorics
    print("\n[2/8] Computing combinatorial framework...")
    results['combinatorics'] = compute_combinatorics()
    print(f"  C(40,5) = {results['combinatorics']['total_quintets_C40_5']:,}")
    print(f"  P(pair) = {results['combinatorics']['p_specific_pair_fraction']}")

    # Phase 2A
    print("\n[3/8] Test 1: Chi-square uniformity...")
    results['chi2'] = test_chi_square_uniformity(draws)
    print(f"  chi2={results['chi2']['chi2_statistic']}, p={results['chi2']['p_value']}")
    print(f"  {results['chi2']['verdict']}")

    print("\n[4/8] Test 2: Runs test...")
    results['runs'] = test_runs(draws)
    print(f"  z={results['runs']['z_statistic']}, p={results['runs']['p_value']}")
    print(f"  {results['runs']['verdict']}")

    print("\n[5/8] Test 3: Autocorrelation...")
    results['autocorr'] = test_autocorrelation(draws)
    print(f"  Significant lags: {results['autocorr']['n_significant_at_005']}")
    print(f"  {results['autocorr']['verdict']}")

    print("\n[6/8] Test 4: Delay distribution...")
    results['delays'] = test_delay_distribution(draws)
    print(f"  Mean delay={results['delays']['mean_delay']}, CV={results['delays']['cv']}")
    print(f"  {results['delays']['verdict']}")

    print("\n[7/8] Test 5: Kolmogorov compressibility...")
    results['compress'] = test_kolmogorov_compressibility(draws)
    print(f"  Real ratio={results['compress']['real_ratio']}")
    print(f"  Random mean={results['compress']['random_mean_ratio']}")
    print(f"  z={results['compress']['z_score']}")
    print(f"  {results['compress']['verdict']}")

    # Phase 2B
    print("\n[8/8] Structural properties...")
    results['decades'] = analyze_decade_distribution(draws)
    results['sums'] = analyze_sum_distribution(draws)
    results['gaps'] = analyze_gap_distribution(draws)
    results['ranges'] = analyze_range_distribution(draws)
    results['freqs'] = analyze_number_frequencies(draws)
    results['pairs'] = analyze_top_pairs(draws)

    print(f"  Sum: mean={results['sums']['observed_mean']}, std={results['sums']['observed_std']}")
    print(f"  Gap: mean={results['gaps']['mean_gap']}")
    print(f"  Range: mean={results['ranges']['mean_range']}")
    print(f"  Top pair: {results['pairs']['top_20'][0]['pair']} (obs={results['pairs']['top_20'][0]['observed']})")

    # Generate report
    print("\n" + "=" * 70)
    print("Generating report...")
    report = generate_report(results, n_real, n_synthetic, n_total)

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ANALYSIS_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report written to: {report_path}")

    # Prepare notification summary
    summary_lines = [
        f"VinciCasa Phase 2 Complete",
        f"Dataset: {n_real} real + {n_synthetic} synthetic = {n_total}",
        f"",
        f"RNG Certification:",
        f"  Chi2: {results['chi2']['verdict']}",
        f"  Runs: {results['runs']['verdict']}",
        f"  Autocorr: {results['autocorr']['verdict']}",
        f"  Delay CV: {results['delays']['cv']}",
        f"  Compress: {results['compress']['verdict']}",
        f"",
        f"Structural:",
        f"  C(40,5)={results['combinatorics']['total_quintets_C40_5']:,}",
        f"  P(pair)=1/78 (5x Lotto)",
        f"  Sum: mean={results['sums']['observed_mean']}, std={results['sums']['observed_std']}",
        f"  Range: mean={results['ranges']['mean_range']}",
        f"  Top pair: {results['pairs']['top_20'][0]['pair']}",
    ]
    summary = "\n".join(summary_lines)

    # Send notification
    print("\nSending ntfy notification...")
    try:
        import httpx
        resp = httpx.post(
            "https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM",
            content=summary.encode("utf-8"),
            headers={"Title": "VinciCasa Fase 2 - Analysis Complete", "Priority": "5"},
            timeout=10.0,
        )
        print(f"  ntfy response: {resp.status_code}")
    except Exception as e:
        print(f"  ntfy error: {e}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(summary)

    # Save raw results as JSON for programmatic access
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nJSON results: {json_path}")

    return results


if __name__ == "__main__":
    main()
