"""Deep Lotto Sweep — Fasi 1 + 2 + 3 per ambetto.

Obiettivo: verificare se l'edge di vicinanza W=125 (ratio 1.18x nel paper)
e un pattern REALE o artefatto del multiple testing.

Fase 1 — Diagnostica (Test A/B/C):
    A. Label-shuffle ambetto W=125 (distrugge geografia, preserva co-occ)
    B. Hot-hand per numero × ruota (bias fisici urne)
    C. Stabilita temporale 8-fold decadale (pattern stabile 1946-2026?)

Fase 2 — Window Sweep:
    8 algoritmi × 150 finestre × 10 ruote = 12.000 configurazioni
    Ricerca W e algoritmo ottimale per ciascuna ruota

Fase 3 — Pattern inter-ruota:
    Correlazione fra ruote, identifica bias comuni

Dataset: 68.898 estrazioni-ruota (~6.886 per ruota × 10 ruote × 80 anni).
Payoff ambetto: 65€ vincita, 1€ costo. Baseline atteso: 0.417€/giocata.
Breakeven: 2.40x (in termini di ratio, 1€/0.417 = 2.40x).

Nota: qui il ratio e rispetto all'EV teorico dell'ambetto (~0.417/1), quindi
ratio 1.18x = EV osservato 0.49€/giocata = ancora sotto breakeven 1€.

Usiamo ratio rispetto a baseline casuale.
"""

# ruff: noqa: E501, S311, N802, N803, N806
from __future__ import annotations

import logging
import random
from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path

import numpy as np
from sqlalchemy import select

from lotto_predictor.models.database import Estrazione, get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("deep_lotto")

# Parametri Lotto
N_POOL = 90
N_DRAWN = 5
COSTO = 1.0
PREMIO_AMBO = 250.0  # per ambo secco
PREMIO_AMBETTO = 65.0  # per ambetto (con tolleranza ±1)

# EV teorico ambetto (random 2 numeri)
# Probabilita' di vincere ambetto con pick (a, b) random:
# Servono 2 numeri estratti (x, y) con |x-a|≤1 e |y-b|≤1.
# Approssimativamente: 9 combinazioni ±1 × 10 coppie/estrazione / 4005 = ~0.022
# ~2.2% probabilita, quindi EV = 0.022 × 65 = 1.43€/giocata (approx, senza mediare)
# In realta per l'analisi ci basta il ratio rispetto al baseline empirico (calcolato da random)
# Calcoliamolo empiricamente


def load_data() -> dict[str, list[list[int]]]:
    """Carica dati Lotto raggruppati per ruota, ordine cronologico."""
    s = get_session()
    try:
        rows = (
            s.execute(select(Estrazione).order_by(Estrazione.data, Estrazione.ruota))
            .scalars()
            .all()
        )
        by_ruota: dict[str, list[list[int]]] = defaultdict(list)
        for r in rows:
            by_ruota[r.ruota].append([r.n1, r.n2, r.n3, r.n4, r.n5])
        return dict(by_ruota)
    finally:
        s.close()


def load_data_with_dates() -> dict[str, list[tuple[str, list[int]]]]:
    """Carica con date per analisi temporale."""
    s = get_session()
    try:
        rows = (
            s.execute(select(Estrazione).order_by(Estrazione.data, Estrazione.ruota))
            .scalars()
            .all()
        )
        by_ruota: dict[str, list[tuple]] = defaultdict(list)
        for r in rows:
            by_ruota[r.ruota].append((str(r.data), [r.n1, r.n2, r.n3, r.n4, r.n5]))
        return dict(by_ruota)
    finally:
        s.close()


# =====================================================================
# Algoritmi pick ambetto (coppia a, b)
# =====================================================================


def algo_hot_pair(freq: np.ndarray) -> tuple[int, int]:
    """2 numeri piu frequenti."""
    f = freq.copy().astype(np.int64)
    f[0] = -1
    idx = np.argpartition(-f, 2)[:2]
    return int(min(idx)), int(max(idx))


def algo_cold_pair(freq: np.ndarray) -> tuple[int, int]:
    """2 numeri meno frequenti."""
    f = freq.copy().astype(np.int64)
    f[0] = 10**9
    idx = np.argpartition(f, 2)[:2]
    return int(min(idx)), int(max(idx))


def algo_vicinanza_D5(freq: np.ndarray) -> tuple[int, int]:
    """2 numeri vicini (|a-b|≤5) entrambi frequenti."""
    f = freq.copy().astype(np.int64)
    f[0] = -1
    # Piu frequente come seed
    seed = int(np.argmax(f))
    # Cerca il vicino piu frequente nel range ±5
    best_n, best_f = 1, -1
    for n in range(1, 91):
        if n != seed and abs(n - seed) <= 5 and f[n] > best_f:
            best_n, best_f = n, int(f[n])
    return min(seed, best_n), max(seed, best_n)


def algo_vicinanza_D20(freq: np.ndarray) -> tuple[int, int]:
    """2 numeri vicini (|a-b|≤20) entrambi frequenti. Paper V6 baseline."""
    f = freq.copy().astype(np.int64)
    f[0] = -1
    seed = int(np.argmax(f))
    best_n, best_f = 1, -1
    for n in range(1, 91):
        if n != seed and abs(n - seed) <= 20 and f[n] > best_f:
            best_n, best_f = n, int(f[n])
    return min(seed, best_n), max(seed, best_n)


def algo_vicinanza_D40(freq: np.ndarray) -> tuple[int, int]:
    """2 vicini range ampio."""
    f = freq.copy().astype(np.int64)
    f[0] = -1
    seed = int(np.argmax(f))
    best_n, best_f = 1, -1
    for n in range(1, 91):
        if n != seed and abs(n - seed) <= 40 and f[n] > best_f:
            best_n, best_f = n, int(f[n])
    return min(seed, best_n), max(seed, best_n)


def algo_spread_decade(freq: np.ndarray) -> tuple[int, int]:
    """1 numero hot da prima meta (1-45), 1 da seconda (46-90)."""
    f = freq.copy().astype(np.int64)
    f[0] = -1
    low_f = f[1:46]
    high_f = f[46:91]
    a = int(np.argmax(low_f)) + 1
    b = int(np.argmax(high_f)) + 46
    return a, b


def algo_freq_rit_fib(window_rows: list[list[int]]) -> tuple[int, int]:
    """Paper V6: coppia con rapporto freq/ritardo vicino a Fibonacci."""
    freq = Counter()
    last_seen = {}
    W = len(window_rows)
    for idx, nums in enumerate(window_rows):
        for n in nums:
            freq[n] += 1
            last_seen[n] = idx
    # Per ogni numero: rapporto freq / (W - last_seen)
    scores = {}
    for n in range(1, 91):
        f = freq.get(n, 0)
        ls = last_seen.get(n, -W)
        rit = W - ls
        if rit <= 0:
            rit = 1
        ratio = f / rit
        # Vicino a 1/phi ≈ 0.618?
        phi_inv = 0.618
        scores[n] = -abs(ratio - phi_inv)  # più alto = più vicino a phi
    # Top 2
    top = sorted(scores.items(), key=lambda x: -x[1])[:2]
    a, b = top[0][0], top[1][0]
    return min(a, b), max(a, b)


def algo_pair_cooccur(window_rows: list[list[int]]) -> tuple[int, int]:
    """Coppia che è uscita insieme più volte nella finestra."""
    pair_freq = Counter()
    for nums in window_rows:
        nums_sorted = sorted(nums)
        for i in range(5):
            for j in range(i + 1, 5):
                pair_freq[(nums_sorted[i], nums_sorted[j])] += 1
    if not pair_freq:
        return 1, 2
    top = pair_freq.most_common(1)[0][0]
    return top


def algo_anti_persist(freq: np.ndarray) -> tuple[int, int]:
    """Opposite di hot: numeri non-caldi ma non freddissimi (sweet spot)."""
    f = freq.copy().astype(np.int64)
    f[0] = 10**9
    # Quelli vicini alla media
    total = int(f[1:91].sum())
    mean = total / 90
    diff = np.abs(f.astype(float) - mean)
    diff[0] = 1e9
    idx = np.argpartition(diff, 2)[:2]
    return int(min(idx)), int(max(idx))


ALGOS = {
    "hot_pair": algo_hot_pair,
    "cold_pair": algo_cold_pair,
    "vicinanza_D5": algo_vicinanza_D5,
    "vicinanza_D20": algo_vicinanza_D20,  # paper V6
    "vicinanza_D40": algo_vicinanza_D40,
    "spread_decade": algo_spread_decade,
    "anti_persist": algo_anti_persist,
}
# Algoritmi che richiedono window_rows invece di freq array
ALGOS_COMPLEX = {
    # freq_rit_fib e pair_cooccur rimossi dal sweep: troppo lenti.
    # Tested separatamente su W=75 nel paper V6.
}


# =====================================================================
# Vincita calcolo
# =====================================================================


def ambetto_wins(pick: tuple[int, int], drawn: list[int]) -> bool:
    """Ambetto: vince se nei 5 estratti esistono (x, y) con |x-a|≤1 AND |y-b|≤1, x≠y."""
    a, b = pick
    has_a_zone = False
    has_b_zone = False
    a_number = None
    b_number = None
    for x in drawn:
        if abs(x - a) <= 1:
            has_a_zone = True
            a_number = x
        if abs(x - b) <= 1:
            has_b_zone = True
            b_number = x
    # vince se entrambe le zone hanno almeno un numero, e NON sono lo stesso numero
    # (quando a e b sono adiacenti, una zona puo contenere un numero della zona opposta)
    if not (has_a_zone and has_b_zone):
        return False
    # se a_number == b_number, dobbiamo verificare che ci sia un altro numero in una delle zone
    if a_number == b_number:
        # conta quanti numeri cadono in zone
        hits = [x for x in drawn if abs(x - a) <= 1 or abs(x - b) <= 1]
        return len(hits) >= 2
    return True


def ambo_wins(pick: tuple[int, int], drawn: list[int]) -> bool:
    """Ambo secco: {a, b} ⊆ drawn."""
    return pick[0] in drawn and pick[1] in drawn


# =====================================================================
# Rolling freq con numpy
# =====================================================================


def indicators_matrix(rows: list[list[int]]) -> np.ndarray:
    """Crea matrice (N, 91) int8: ind[i, n] = 1 se n è in estrazione i."""
    N = len(rows)
    ind = np.zeros((N, 91), dtype=np.int32)
    for i, nums in enumerate(rows):
        for n in nums:
            ind[i, n] = 1
    return ind


def rolling_freq(ind: np.ndarray, W: int) -> np.ndarray:
    """Freq[i, n] = somma ind[i-W..i-1, n], per i >= W."""
    N = ind.shape[0]
    cs = np.cumsum(ind, axis=0)
    freq = np.zeros((N - W, 91), dtype=np.int32)
    freq[0] = cs[W - 1]
    if N - W > 1:
        freq[1:] = cs[W:N - 1] - cs[:N - W - 1]
    return freq


# =====================================================================
# Backtest single algo × W × ruota
# =====================================================================


def backtest(rows: list[list[int]], algo_name: str, W: int,
             precomputed_freq: np.ndarray | None = None) -> dict:
    """Applica algoritmo su finestra W, conta vincite ambetto, ritorna stats.

    precomputed_freq: array (N-W, 91) gia calcolato (risparmia tempo nel sweep).
    """
    N = len(rows)
    if N < W + 10:
        return {"n_plays": 0, "wins": 0, "ratio_vs_random": 0.0, "hit_rate": 0.0}

    if algo_name in ALGOS:
        if precomputed_freq is None:
            ind = indicators_matrix(rows)
            freq_arr = rolling_freq(ind, W)
        else:
            freq_arr = precomputed_freq
        wins = 0
        total = N - W
        for i in range(total):
            target = rows[i + W]
            pick = ALGOS[algo_name](freq_arr[i])
            if ambetto_wins(pick, target):
                wins += 1
    else:
        # Complex: serve window_rows (slower)
        wins = 0
        total = N - W
        algo_fn = ALGOS_COMPLEX[algo_name]
        for i in range(total):
            window = rows[i : i + W]
            target = rows[i + W]
            pick = algo_fn(window)
            if ambetto_wins(pick, target):
                wins += 1

    hit_rate = wins / total if total else 0
    ev_per_play = hit_rate * PREMIO_AMBETTO
    pnl = ev_per_play - COSTO
    return {
        "n_plays": total,
        "wins": wins,
        "hit_rate": hit_rate,
        "ev_per_play": ev_per_play,
        "pnl_total": pnl * total,
        "ratio_vs_random": 0.0,
    }


# =====================================================================
# Baseline random per comparazione
# =====================================================================


def baseline_random(rows: list[list[int]], n_sim: int = 5) -> float:
    """Hit rate media di pick completamente random."""
    N = len(rows)
    total_wins = 0
    total_plays = 0
    rng = random.Random(42)
    for _ in range(n_sim):
        for i in range(N):
            a = rng.randint(1, 90)
            b = rng.randint(1, 90)
            while b == a:
                b = rng.randint(1, 90)
            if ambetto_wins((min(a, b), max(a, b)), rows[i]):
                total_wins += 1
            total_plays += 1
    return total_wins / total_plays


# =====================================================================
# FASE 1 — TEST A: Label-shuffle ambetto W=125
# =====================================================================


def test_A_label_shuffle(rows: list[list[int]], n_permutations: int = 20) -> dict:
    """Distrugge l'adjacency numerica preservando frequenza e co-occorrenza."""
    log.info("=" * 70)
    log.info("TEST A — Label-shuffle ambetto (vicinanza_D20 W=125)")
    log.info("=" * 70)

    # Baseline originale
    log.info("Baseline originale (vicinanza_D20 W=125)...")
    baseline = backtest(rows, "vicinanza_D20", 125)
    baseline_random_hit = baseline_random(rows, n_sim=3)
    baseline["ratio_vs_random"] = baseline["hit_rate"] / baseline_random_hit if baseline_random_hit > 0 else 0
    log.info(f"  Hit rate: {baseline['hit_rate']*100:.3f}%  vs random {baseline_random_hit*100:.3f}%")
    log.info(f"  Ratio: {baseline['ratio_vs_random']:.4f}x")

    # Permutazioni
    log.info(f"\n{n_permutations} permutazioni label (preserva co-occorrenza, distrugge adjacency)...")
    perm_ratios = []
    rng = random.Random(42)
    for p_idx in range(n_permutations):
        perm = list(range(1, 91))
        rng.shuffle(perm)
        mapping = {i + 1: perm[i] for i in range(90)}
        # Applica permutazione
        shuffled_rows = [[mapping[n] for n in nums] for nums in rows]
        r = backtest(shuffled_rows, "vicinanza_D20", 125)
        ratio = r["hit_rate"] / baseline_random_hit if baseline_random_hit > 0 else 0
        perm_ratios.append(ratio)
        if (p_idx + 1) % 5 == 0:
            log.info(f"  [{p_idx+1}/{n_permutations}] mean so far: {sum(perm_ratios)/len(perm_ratios):.4f}x")

    mean_perm = sum(perm_ratios) / len(perm_ratios)
    sd_perm = (sum((r - mean_perm) ** 2 for r in perm_ratios) / len(perm_ratios)) ** 0.5
    p_value = sum(1 for r in perm_ratios if r >= baseline["ratio_vs_random"]) / len(perm_ratios)

    log.info("")
    log.info(f"Baseline:        ratio {baseline['ratio_vs_random']:.4f}x")
    log.info(f"Permutati mean:  ratio {mean_perm:.4f}x  (SD {sd_perm:.4f})")
    log.info(f"Permutati range: [{min(perm_ratios):.4f}, {max(perm_ratios):.4f}]")
    log.info(f"P-value: {p_value:.4f}")

    if p_value < 0.05:
        verdict = "GEOGRAFIA CONTA: label-shuffle distrugge l'edge → urne fisiche hanno bias reale"
    elif p_value > 0.5:
        verdict = "GEOGRAFIA NON CONTA: label-shuffle mantiene l'edge → artefatto del calcolo"
    else:
        verdict = f"BORDERLINE (p={p_value:.3f}): effetto debole ma presente"
    log.info(f"\nVerdetto: {verdict}")

    return {
        "baseline_ratio": baseline["ratio_vs_random"],
        "perm_mean": mean_perm,
        "perm_sd": sd_perm,
        "perm_min": min(perm_ratios),
        "perm_max": max(perm_ratios),
        "p_value": p_value,
        "verdict": verdict,
    }


# =====================================================================
# FASE 1 — TEST B: Hot-hand per numero × ruota
# =====================================================================


def test_B_hot_hand(data_by_ruota: dict, W: int = 100) -> dict:
    """P(numero esce|freq alta) vs P(|freq bassa) per ogni (numero, ruota)."""
    log.info("=" * 70)
    log.info(f"TEST B — Hot-hand per numero × ruota (W={W})")
    log.info("=" * 70)

    p_single = 5 / 90
    log.info(f"Baseline P(present) = 5/90 = {p_single:.4f}")

    results = {}
    total_samples = 0
    for ruota, rows in data_by_ruota.items():
        if len(rows) < W + 100:
            continue
        ind = indicators_matrix(rows)
        freq = rolling_freq(ind, W)  # (N-W, 91)
        target_ind = ind[W:]  # (N-W, 91)

        # Per ogni numero, per ogni finestra, (freq_n, present_n)
        hi_thresh = W * 5 / 90 + 1.5 * sqrt(W * 5 / 90 * 85 / 90)
        lo_thresh = W * 5 / 90 - 1.5 * sqrt(W * 5 / 90 * 85 / 90)

        for n in range(1, 91):
            hi_mask = freq[:, n] >= hi_thresh
            lo_mask = freq[:, n] <= lo_thresh
            hi_n = int(hi_mask.sum())
            lo_n = int(lo_mask.sum())
            hi_hits = int(target_ind[hi_mask, n].sum())
            lo_hits = int(target_ind[lo_mask, n].sum())
            if hi_n < 30 or lo_n < 30:
                continue
            p_hi = hi_hits / hi_n
            p_lo = lo_hits / lo_n
            se = sqrt(p_single * (1 - p_single) * (1 / hi_n + 1 / lo_n))
            z = (p_hi - p_lo) / se if se > 0 else 0
            results[(ruota, n)] = {"p_hi": p_hi, "p_lo": p_lo, "z": z, "hi_n": hi_n, "lo_n": lo_n}
            total_samples += 1

    # Statistica aggregata
    all_z = [r["z"] for r in results.values()]
    mean_z = sum(all_z) / len(all_z)
    sig_count = sum(1 for z in all_z if abs(z) > 3.0)
    bonf_z = 3.8  # approx 0.05 / 900
    bonf_count = sum(1 for z in all_z if abs(z) > bonf_z)

    log.info(f"Totale (numero, ruota): {total_samples}")
    log.info(f"Mean z: {mean_z:+.3f}")
    log.info(f"|z|>3.0 raw: {sig_count}/{total_samples}")
    log.info(f"|z|>{bonf_z} Bonferroni (0.05/900): {bonf_count}/{total_samples}")

    # Top 10 |z|
    top_z = sorted(results.items(), key=lambda x: -abs(x[1]["z"]))[:10]
    log.info("\nTop 10 |z| (potenziali bias fisici):")
    for (ruota, n), r in top_z:
        log.info(f"  {ruota:<10} n={n:>2}  p_hi={r['p_hi']:.4f}  p_lo={r['p_lo']:.4f}  z={r['z']:+.2f}")

    if bonf_count >= 5:
        verdict = f"BIAS FISICI RILEVATI: {bonf_count} numeri × ruota sopravvivono Bonferroni"
    elif bonf_count >= 1:
        verdict = f"BIAS FISICI BORDERLINE: {bonf_count} numeri × ruota sopra Bonferroni (ma non molti)"
    else:
        verdict = "NESSUN BIAS FISICO rilevato oltre multiple testing"
    log.info(f"\nVerdetto: {verdict}")

    return {
        "total_samples": total_samples,
        "mean_z": mean_z,
        "sig_raw": sig_count,
        "sig_bonf": bonf_count,
        "verdict": verdict,
        "top_10_z": [(r, n, v["z"]) for (r, n), v in top_z],
    }


# =====================================================================
# FASE 1 — TEST C: Stabilita temporale 8-fold decadale
# =====================================================================


def test_C_temporal_8fold(data_with_dates: dict, W: int = 125) -> dict:
    """Divide 80 anni in 8 decenni, verifica ratio in ciascuno."""
    log.info("=" * 70)
    log.info(f"TEST C — Stabilita temporale 8-fold decadale (vicinanza_D20 W={W})")
    log.info("=" * 70)

    # Definisci 8 fold: 1946-55, 1956-65, ..., 2016-26
    decades = [
        (1946, 1955), (1956, 1965), (1966, 1975), (1976, 1985),
        (1986, 1995), (1996, 2005), (2006, 2015), (2016, 2026),
    ]

    fold_results = []
    for ymin, ymax in decades:
        # Raccogli estrazioni di questo decennio per tutte le ruote
        all_rows_decade = []
        for _ruota, sorted_rows in data_with_dates.items():
            for data_str, nums in sorted_rows:
                year = int(data_str[:4])
                if ymin <= year <= ymax:
                    all_rows_decade.append(nums)
        if len(all_rows_decade) < W + 100:
            log.info(f"  {ymin}-{ymax}: pochi dati ({len(all_rows_decade)}), skip")
            continue
        r = backtest(all_rows_decade, "vicinanza_D20", W)
        baseline_r = baseline_random(all_rows_decade, n_sim=2)
        ratio = r["hit_rate"] / baseline_r if baseline_r > 0 else 0
        fold_results.append({
            "decade": f"{ymin}-{ymax}",
            "n_plays": r["n_plays"],
            "wins": r["wins"],
            "hit_rate": r["hit_rate"],
            "baseline_random": baseline_r,
            "ratio": ratio,
        })
        log.info(f"  {ymin}-{ymax}: n={r['n_plays']:>5}  hit={r['hit_rate']*100:.3f}%  base={baseline_r*100:.3f}%  ratio={ratio:+.4f}x")

    # Stabilita: tutti >1.0?, SD, coefficient of variation
    all_ratios = [f["ratio"] for f in fold_results]
    mean_r = sum(all_ratios) / len(all_ratios)
    sd_r = (sum((r - mean_r) ** 2 for r in all_ratios) / len(all_ratios)) ** 0.5
    above_1 = sum(1 for r in all_ratios if r > 1.0)
    above_11 = sum(1 for r in all_ratios if r > 1.1)

    log.info("")
    log.info(f"Mean ratio: {mean_r:+.4f}x, SD: {sd_r:.4f}")
    log.info(f"Sopra 1.0x: {above_1}/{len(all_ratios)}")
    log.info(f"Sopra 1.1x: {above_11}/{len(all_ratios)}")

    if above_1 >= 7:
        verdict = f"PATTERN MOLTO STABILE: {above_1}/{len(all_ratios)} decenni sopra baseline"
    elif above_1 >= 5:
        verdict = f"Pattern stabile: {above_1}/{len(all_ratios)} decenni sopra"
    else:
        verdict = f"Pattern INSTABILE: solo {above_1}/{len(all_ratios)} decenni sopra baseline"
    log.info(f"\nVerdetto: {verdict}")

    return {
        "folds": fold_results,
        "mean_ratio": mean_r,
        "sd_ratio": sd_r,
        "above_1": above_1,
        "above_1_1": above_11,
        "verdict": verdict,
    }


# =====================================================================
# FASE 2 — Window Sweep 8 algoritmi × 150 W × 10 ruote
# =====================================================================


def run_fase2_sweep(data_by_ruota: dict) -> dict:
    """Sweep sistematico per identificare best config per ciascuna ruota."""
    log.info("=" * 70)
    log.info("FASE 2 — Window Sweep 8 algoritmi × 150 finestre × 10 ruote")
    log.info("=" * 70)
    log.info("Cerca il W ottimale per ciascuna ruota e algoritmo.")

    W_list = list(range(5, 151, 5))  # step 5: 5,10,15,...,150 — 30 valori totali
    log.info(f"W testati: {len(W_list)} valori in [5, 149] step 3")
    log.info(f"Algoritmi: {len(ALGOS) + len(ALGOS_COMPLEX)} totali")

    all_algos = {**ALGOS, **ALGOS_COMPLEX}

    results_all = {}
    # Baseline random per ogni ruota (una volta sola)
    baseline_per_ruota = {}
    for ruota, rows in data_by_ruota.items():
        baseline_per_ruota[ruota] = baseline_random(rows, n_sim=2)
        log.info(f"  Baseline random {ruota}: hit_rate {baseline_per_ruota[ruota]*100:.3f}%")

    log.info("")
    total_configs = len(data_by_ruota) * len(all_algos) * len(W_list)
    log.info(f"Configurazioni totali: {total_configs}")

    config_idx = 0
    for ruota, rows in data_by_ruota.items():
        results_all[ruota] = {}
        baseline_r = baseline_per_ruota[ruota]
        ind = indicators_matrix(rows)

        # Precompute freq per ogni W (una volta) — grosso speedup
        freq_cache = {}
        for W in W_list:
            freq_cache[W] = rolling_freq(ind, W)

        log.info(f"  [{ruota}] freq precomputati per {len(W_list)} finestre")

        for algo_name in all_algos:
            best_W = None
            best_ratio = 0
            best_r = None
            for W in W_list:
                config_idx += 1
                r = backtest(rows, algo_name, W, precomputed_freq=freq_cache[W])
                if r["n_plays"] > 0:
                    ratio = r["hit_rate"] / baseline_r if baseline_r > 0 else 0
                    r["ratio_vs_random"] = ratio
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_W = W
                        best_r = r
            if best_W is not None and best_r is not None:
                results_all[ruota][algo_name] = {**best_r, "best_W": best_W}

            log.info(f"  [{config_idx}/{total_configs}] {ruota} {algo_name}: best W={best_W} ratio={best_ratio:+.4f}x")

    # Report best per ruota
    log.info("")
    log.info("=" * 70)
    log.info("BEST CONFIG PER RUOTA (tra tutti gli algoritmi × tutte le W)")
    log.info("=" * 70)
    log.info(f"{'Ruota':<10} {'Algoritmo':<18} {'W':>5} {'Hit rate':>10} {'Ratio':>10}")
    log.info("-" * 70)
    global_best = {}
    for ruota, algos_dict in results_all.items():
        best = max(algos_dict.items(), key=lambda x: x[1]["ratio_vs_random"])
        global_best[ruota] = {"algo": best[0], **best[1]}
        log.info(f"{ruota:<10} {best[0]:<18} {best[1]['best_W']:>5} {best[1]['hit_rate']*100:>9.3f}% {best[1]['ratio_vs_random']:>+9.4f}x")

    return {"per_ruota": results_all, "global_best": global_best}


# =====================================================================
# FASE 3 — Pattern inter-ruota
# =====================================================================


def run_fase3_ruote(data_by_ruota: dict, sweep_results: dict) -> dict:
    """Analizza correlazioni fra ruote."""
    log.info("=" * 70)
    log.info("FASE 3 — Pattern inter-ruota")
    log.info("=" * 70)

    # Per ogni ruota: rate di vittoria di vicinanza_D20 W=125 fisso
    # (stesso algoritmo, stesso W, paragone equo)
    ratios = {}
    baselines = {}
    for ruota, rows in data_by_ruota.items():
        baseline_r = baseline_random(rows, n_sim=3)
        baselines[ruota] = baseline_r
        r = backtest(rows, "vicinanza_D20", 125)
        if baseline_r > 0:
            ratios[ruota] = r["hit_rate"] / baseline_r

    log.info("Vicinanza D20 W=125 per ciascuna ruota:")
    log.info(f"{'Ruota':<10} {'Hit rate':>10} {'Baseline':>10} {'Ratio':>10}")
    log.info("-" * 50)
    for ruota in sorted(ratios, key=lambda r: -ratios[r]):
        log.info(f"{ruota:<10} {backtest(data_by_ruota[ruota], 'vicinanza_D20', 125)['hit_rate']*100:>9.3f}% {baselines[ruota]*100:>9.3f}% {ratios[ruota]:>+9.4f}x")

    # Identifica la ruota migliore (potenziale urna piu "biased")
    best_ruota = max(ratios, key=ratios.get)
    worst_ruota = min(ratios, key=ratios.get)

    log.info("")
    log.info(f"Ruota MIGLIORE per vicinanza D20 W=125: {best_ruota} (ratio {ratios[best_ruota]:+.4f}x)")
    log.info(f"Ruota PEGGIORE: {worst_ruota} (ratio {ratios[worst_ruota]:+.4f}x)")

    gap = ratios[best_ruota] - ratios[worst_ruota]
    log.info(f"Gap fra migliore e peggiore: {gap:.4f}")

    # Per inter-ruota correlation servirebbe la serie temporale dei ratio
    # (troppo costoso per ora). Riportiamo solo i ratio aggregati.

    return {
        "ratios_per_ruota": ratios,
        "baselines": baselines,
        "best_ruota": best_ruota,
        "worst_ruota": worst_ruota,
        "gap": gap,
    }


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    log.info("Caricamento dataset Lotto...")
    data_by_ruota = load_data()
    data_with_dates = load_data_with_dates()
    total_n = sum(len(v) for v in data_by_ruota.values())
    log.info(f"Dataset: {total_n:,} estrazioni-ruota su {len(data_by_ruota)} ruote")
    log.info("")

    out = {"dataset_size": total_n, "ruote": list(data_by_ruota.keys())}

    # Merge tutte le ruote per Test A (bias globale)
    all_rows_merged = []
    for rows in data_by_ruota.values():
        all_rows_merged.extend(rows)
    log.info(f"Merged rows per Test A/C: {len(all_rows_merged):,}")
    log.info("")

    # FASE 1
    out["test_A"] = test_A_label_shuffle(all_rows_merged, n_permutations=20)
    log.info("")
    out["test_B"] = test_B_hot_hand(data_by_ruota, W=100)
    log.info("")
    out["test_C"] = test_C_temporal_8fold(data_with_dates, W=125)
    log.info("")

    # FASE 2
    out["fase2"] = run_fase2_sweep(data_by_ruota)
    log.info("")

    # FASE 3
    out["fase3"] = run_fase3_ruote(data_by_ruota, out["fase2"])

    # Sintesi finale
    log.info("")
    log.info("=" * 70)
    log.info("SINTESI FINALE")
    log.info("=" * 70)
    log.info(f"Test A (label-shuffle):     {out['test_A']['verdict']}")
    log.info(f"Test B (hot-hand):          {out['test_B']['verdict']}")
    log.info(f"Test C (temporal):          {out['test_C']['verdict']}")
    log.info(f"Best ruota (Fase 3):        {out['fase3']['best_ruota']} con ratio {out['fase3']['ratios_per_ruota'][out['fase3']['best_ruota']]:+.4f}x")

    # Salvataggio
    out_path = Path(__file__).parent.parent.parent.parent / "backend" / "lotto_predictor" / "deep_lotto_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Serializable
    import json as _json

    def ser(o):
        if isinstance(o, (np.integer, np.int64, np.int32)):
            return int(o)
        if isinstance(o, (np.floating, np.float64, np.float32)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)

    out_path.write_text(_json.dumps(out, indent=2, default=ser))
    log.info(f"\nRisultati salvati in: {out_path}")


if __name__ == "__main__":
    main()
