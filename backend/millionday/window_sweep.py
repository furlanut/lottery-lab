"""MillionDay — Window Sweep W=1..300 × 13 algoritmi + Rolling Temporal Analysis.

Obiettivo:
  1. Per ciascun algoritmo, trovare la dimensione di finestra W ottimale
  2. Identificare la configurazione (algoritmo, W) con ratio massimo in validation
  3. Per la best config: analisi rolling temporale per vedere se il ratio e
     stabile nel tempo o dipende da periodi specifici

Ottimizzazione numpy:
  - indicators[N, 56] matrici binarie (base e extra)
  - cumsum per calcolo O(1) della freq in qualunque finestra W
  - loop sui W × algoritmi con pick per-row (logica specifica algo)

Dataset: 2.607 estrazioni MillionDay (2022-2026)
  Split: 50/50 discovery/validation
  EV teorico: 1.326€ per giocata 2€ (HE 33.69%, BE 1.508x)
"""

# ruff: noqa: E501, S311, N802, N803, N806, F841, B007, C416
from __future__ import annotations

import json
import logging
import random
from math import sqrt
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("window_sweep")

# MillionDay constants
N_POOL = 55
N_DRAWN = 5
N_EXTRA = 5
N_POOL_EXTRA = 50  # pool Extra = 55 - 5 = 50 numeri rimanenti
K = 5  # numeri giocati

PREMI_BASE = {0: 0.0, 1: 0.0, 2: 2.0, 3: 50.0, 4: 1000.0, 5: 1_000_000.0}
PREMI_EXTRA = {0: 0.0, 1: 0.0, 2: 4.0, 3: 100.0, 4: 1000.0, 5: 100_000.0}
COSTO_TOTALE = 2.0
EV_TEORICO = 1.3262  # calcolato in deep_analysis, senza jackpot ammortizzato

# CAP per ratio robusto: tutto sopra 500€ viene trattato come 500€.
# Questo esclude i jackpot 1M (5/5 base) e 100k (5/5 Extra) che creano
# distorsione enorme con 3.600 configurazioni testate (P(cattura ≥1 jackpot)=73%).
CAP_PAYOUT = 500.0
# EV teorico CAPPATO (stesso calcolo ma con premi ≤500):
# P(2/5)=5.63% × 2 + P(3/5)=0.35% × 50 + P(4/5)=0.0072% × 500 = 0.1127 + 0.1761 + 0.036 = 0.325
# Extra: P(2/5)=0.68% × 4 + P(3/5)=0.04% × 100 + P(4/5)=0.0013% × 500 = ~0.072
# EV capped ≈ 0.397 per base, piu Extra ≈ 0.71 totale (su 2€)
# In realta calcolo empirico: total_winnings_capped / n giocate
EV_TEORICO_CAPPED = 0.71  # ~HE 65% con cap 500€; usato per normalizzare ratio_robust

# Range di sweep
W_MIN = 1
W_MAX = 300
W_LIST = list(range(W_MIN, W_MAX + 1))

DATA_PATH = Path(__file__).parent / "data" / "archive_2022_2026.json"


# =====================================================================
# Load e preprocessing
# =====================================================================


def load_data() -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Carica dati e converte in indicator matrices.

    Returns:
        ind_base: (N, 56) int8 - indicator[i, n] = 1 se n e nei 5 base di estrazione i
        ind_extra: (N, 56) int8 - idem per Extra
        dates: lista date ISO
    """
    raw = json.loads(DATA_PATH.read_text())
    N = len(raw)
    log.info(f"Dataset: {N:,} estrazioni")

    ind_base = np.zeros((N, 56), dtype=np.int32)  # indice 1..55
    ind_extra = np.zeros((N, 56), dtype=np.int32)
    dates = []
    for i, rec in enumerate(raw):
        for n in rec["numeri"]:
            ind_base[i, n] = 1
        for n in rec["extra"]:
            ind_extra[i, n] = 1
        dates.append(f"{rec['data']} {rec['ora']}")

    return ind_base, ind_extra, dates


def compute_rolling_freq(indicators: np.ndarray, W: int) -> np.ndarray:
    """Calcola freq[i, n] = conteggio di n in finestra [i-W, i-1] per i >= W.

    Returns:
        freq: (N-W, 56) int16 - freq[i, n] conta le apparizioni di n in [i-W+W, i-1+W]
              ovvero freq[j] usa finestra [j+W-W, j+W-1] = [j, j+W-1], target e j+W
    """
    cs = np.cumsum(indicators, axis=0)
    # freq_window ending at i-1 (exclusive) = cs[i-1] - cs[i-W-1]
    # Per target estrazione i, finestra e [i-W, i-1]
    # cs[i-1] somma indicators[0..i-1], cs[i-W-1] somma indicators[0..i-W-1]
    # diff = indicators[i-W..i-1] = finestra richiesta
    N = indicators.shape[0]
    # freq[i] corrisponde a target extraction = i+W (quindi i va da 0 a N-W-1)
    # finestra di freq[i] = indicators[i..i+W-1] = cs[i+W-1] - cs[i-1]
    # Per i=0: freq[0] = cs[W-1] (somma di indicators[0..W-1])
    # Per i>=1: freq[i] = cs[i+W-1] - cs[i-1]
    freq = np.zeros((N - W, 56), dtype=np.int32)
    freq[0] = cs[W - 1]
    if N - W > 1:
        # freq[1..N-W-1]: cs[W..N-2] - cs[0..N-W-2]
        freq[1:] = cs[W:N - 1] - cs[:N - W - 1]
    return freq


# =====================================================================
# Algoritmi di pick (ritornano array (N-W, K) di int)
# =====================================================================


def algo_hot(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """Top K piu frequenti nel base."""
    # np.argpartition per top-K, poi sort
    # Trucco: freq[:, 0] e' placeholder (numero 0 non esiste), mettiamo -1 per escluderlo
    f = freq_base.copy()
    f[:, 0] = -1
    # Ordina per -freq: top 5 e' argsort descrescente
    top_idx = np.argpartition(-f, K, axis=1)[:, :K]
    return np.sort(top_idx, axis=1)


def algo_cold(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """Top K MENO frequenti nel base."""
    f = freq_base.astype(np.int64).copy()
    f[:, 0] = 10**9  # escludi 0
    top_idx = np.argpartition(f, K, axis=1)[:, :K]
    return np.sort(top_idx, axis=1)


def algo_optfreq(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """Top K con |freq - expected| minima (ne caldi ne freddi)."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    # expected = W * 5 / 55
    # Per ogni riga dobbiamo calcolare expected specifico
    # Ma possiamo farlo con broadcasting
    for i in range(n_windows):
        # W varia ma internamente e' la stessa riga, quindi usiamo max
        W = int(freq_base[i].sum() / N_DRAWN)  # somma / 5 = W (approssimativo, corretto se completo)
        expected = W * N_DRAWN / N_POOL
        diff = np.abs(freq_base[i].astype(float) - expected)
        diff[0] = 1e9  # escludi numero 0
        top_idx = np.argpartition(diff, K)[:K]
        result[i] = np.sort(top_idx)
    return result


def algo_hot_extra(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """Top K piu frequenti nell'Extra."""
    f = freq_extra.copy()
    f[:, 0] = -1
    top_idx = np.argpartition(-f, K, axis=1)[:, :K]
    return np.sort(top_idx, axis=1)


def algo_dual_3b2e(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """3 hot base + 2 hot extra disgiunti."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    fb = freq_base.copy()
    fb[:, 0] = -1
    fe = freq_extra.copy()
    fe[:, 0] = -1
    for i in range(n_windows):
        # 3 hot base
        hb = np.argpartition(-fb[i], 3)[:3]
        # 2 hot extra escludendo hb
        mask = np.ones(56, dtype=bool)
        mask[hb] = False
        mask[0] = False
        fe_filt = np.where(mask, fe[i], -1)
        he = np.argpartition(-fe_filt, 2)[:2]
        pick = np.concatenate([hb, he])
        result[i] = np.sort(pick)
    return result


def algo_dual_2b3e(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """2 hot base + 3 hot extra disgiunti."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    fb = freq_base.copy()
    fb[:, 0] = -1
    fe = freq_extra.copy()
    fe[:, 0] = -1
    for i in range(n_windows):
        hb = np.argpartition(-fb[i], 2)[:2]
        mask = np.ones(56, dtype=bool)
        mask[hb] = False
        mask[0] = False
        fe_filt = np.where(mask, fe[i], -1)
        he = np.argpartition(-fe_filt, 3)[:3]
        pick = np.concatenate([hb, he])
        result[i] = np.sort(pick)
    return result


def algo_cold_plus_hotex(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """3 cold base + 2 hot extra."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    fb = freq_base.copy()
    fb[:, 0] = 999999
    fe = freq_extra.copy()
    fe[:, 0] = -1
    for i in range(n_windows):
        cb = np.argpartition(fb[i], 3)[:3]
        mask = np.ones(56, dtype=bool)
        mask[cb] = False
        mask[0] = False
        fe_filt = np.where(mask, fe[i], -1)
        he = np.argpartition(-fe_filt, 2)[:2]
        pick = np.concatenate([cb, he])
        result[i] = np.sort(pick)
    return result


def algo_mix3h2c(freq_base: np.ndarray, freq_extra: np.ndarray, K: int = 5) -> np.ndarray:
    """3 hot + 2 cold del base."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    fb = freq_base.copy()
    fb[:, 0] = -1
    for i in range(n_windows):
        hb = np.argpartition(-fb[i], 3)[:3]
        # cold: 2 meno frequenti esclusi hb
        mask = np.ones(56, dtype=bool)
        mask[hb] = False
        mask[0] = False
        fb_filt = np.where(mask, fb[i], 999999)
        cb = np.argpartition(fb_filt, 2)[:2]
        pick = np.concatenate([hb, cb])
        result[i] = np.sort(pick)
    return result


def _vicinanza_pick(freq_row: np.ndarray, D: int, K: int = 5) -> np.ndarray:
    """seed = most_freq del base + K-1 vicini +/- D piu frequenti."""
    f = freq_row.copy()
    f[0] = -1
    seed = int(np.argmax(f))
    # Candidati: numeri in [seed-D, seed+D], escludere seed
    low = max(1, seed - D)
    high = min(55, seed + D)
    candidates = [n for n in range(low, high + 1) if n != seed]
    # Ordina per freq desc
    candidates.sort(key=lambda n: -int(f[n]))
    pick = [seed] + candidates[: K - 1]
    # Pad se servono ancora (cluster troppo piccolo)
    if len(pick) < K:
        extra = np.argsort(-f)[: K * 3]
        for n in extra:
            if int(n) not in pick and n > 0:
                pick.append(int(n))
                if len(pick) >= K:
                    break
    return np.sort(np.array(pick[:K], dtype=np.int64))


def algo_vicinanza_D3(freq_base, freq_extra, K=5):
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    for i in range(n_windows):
        result[i] = _vicinanza_pick(freq_base[i], D=3, K=K)
    return result


def algo_vicinanza_D5(freq_base, freq_extra, K=5):
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    for i in range(n_windows):
        result[i] = _vicinanza_pick(freq_base[i], D=5, K=K)
    return result


def algo_vicinanza_D10(freq_base, freq_extra, K=5):
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    for i in range(n_windows):
        result[i] = _vicinanza_pick(freq_base[i], D=10, K=K)
    return result


def algo_spread_fasce(freq_base, freq_extra, K=5):
    """1 numero piu frequente per ciascuna delle 5 fasce: 1-11, 12-22, 23-33, 34-44, 45-55."""
    n_windows = freq_base.shape[0]
    result = np.zeros((n_windows, K), dtype=np.int64)
    # 5 fasce: 1-11, 12-22, 23-33, 34-44, 45-55 (fasce di 11 numeri, totale 55)
    fasce = [(1, 11), (12, 22), (23, 33), (34, 44), (45, 55)]
    for i in range(n_windows):
        pick = []
        for lo, hi in fasce:
            segment = freq_base[i, lo:hi + 1]
            local_argmax = int(np.argmax(segment))
            pick.append(lo + local_argmax)
        result[i] = np.sort(pick)
    return result


# Registry
ALGOS = {
    "hot": algo_hot,
    "cold": algo_cold,
    "optfreq": algo_optfreq,
    "hot_extra": algo_hot_extra,
    "dual_3b2e": algo_dual_3b2e,
    "dual_2b3e": algo_dual_2b3e,
    "cold_plus_hotex": algo_cold_plus_hotex,
    "mix3h2c": algo_mix3h2c,
    "vicinanza_D3": algo_vicinanza_D3,
    "vicinanza_D5": algo_vicinanza_D5,
    "vicinanza_D10": algo_vicinanza_D10,
    "spread_fasce": algo_spread_fasce,
}


# =====================================================================
# Evaluation
# =====================================================================


def evaluate_picks(
    picks: np.ndarray,
    ind_base: np.ndarray,
    ind_extra: np.ndarray,
    W: int,
) -> np.ndarray:
    """Per ciascuna riga di picks, calcola vincita totale base+extra per estrazione i=W+row_idx.

    Returns:
        winnings: (N-W,) float, vincita monetaria per ogni giocata
    """
    n_windows = picks.shape[0]
    winnings = np.zeros(n_windows, dtype=np.float64)
    for i in range(n_windows):
        target_extraction = W + i
        pick = picks[i]
        mb = int(sum(ind_base[target_extraction, n] for n in pick))
        rem = [n for n in pick if ind_base[target_extraction, n] == 0]
        me = int(sum(ind_extra[target_extraction, n] for n in rem))
        w = PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)
        winnings[i] = w
    return winnings


# =====================================================================
# Main sweep
# =====================================================================


def run_sweep(
    ind_base: np.ndarray,
    ind_extra: np.ndarray,
    w_list: list[int],
    algos: dict,
) -> dict:
    """Esegue sweep W × algoritmo, ritorna dict {(algo, W): stats}."""
    N = ind_base.shape[0]
    half = N // 2
    results = {}

    total_configs = len(algos) * len(w_list)
    log.info(f"Sweep: {len(algos)} algoritmi × {len(w_list)} finestre = {total_configs} configurazioni")
    log.info(f"Dataset: {N} estrazioni, split disc [0..{half}), val [{half}..{N})")

    config_idx = 0
    for algo_name, algo_fn in algos.items():
        for W in w_list:
            config_idx += 1
            # Compute freq arrays
            freq_base = compute_rolling_freq(ind_base, W)
            freq_extra = compute_rolling_freq(ind_extra, W)

            # Generate picks
            picks = algo_fn(freq_base, freq_extra, K)

            # Evaluate
            winnings = evaluate_picks(picks, ind_base, ind_extra, W)

            # Split disc/val (target_extraction = W + i, quindi i = target - W)
            disc_idx_end = max(0, half - W)  # target < half
            ev_disc = winnings[:disc_idx_end].mean() if disc_idx_end > 0 else 0
            ev_val = winnings[disc_idx_end:].mean() if len(winnings) > disc_idx_end else 0
            ratio_disc = ev_disc / EV_TEORICO if EV_TEORICO else 0
            ratio_val = ev_val / EV_TEORICO if EV_TEORICO else 0

            # Ratio robust: cap payout a 500€ per escludere jackpot distorcenti
            winnings_capped = np.minimum(winnings, CAP_PAYOUT)
            ev_disc_cap = winnings_capped[:disc_idx_end].mean() if disc_idx_end > 0 else 0
            ev_val_cap = winnings_capped[disc_idx_end:].mean() if len(winnings_capped) > disc_idx_end else 0
            ratio_disc_cap = ev_disc_cap / EV_TEORICO_CAPPED if EV_TEORICO_CAPPED else 0
            ratio_val_cap = ev_val_cap / EV_TEORICO_CAPPED if EV_TEORICO_CAPPED else 0

            # Conteggio jackpot (>=500€) per trasparenza
            n_big_disc = int((winnings[:disc_idx_end] >= CAP_PAYOUT).sum()) if disc_idx_end > 0 else 0
            n_big_val = int((winnings[disc_idx_end:] >= CAP_PAYOUT).sum()) if len(winnings) > disc_idx_end else 0

            n_disc = disc_idx_end
            n_val = len(winnings) - disc_idx_end

            results[(algo_name, W)] = {
                "algo": algo_name,
                "W": W,
                "ev_disc": float(ev_disc),
                "ev_val": float(ev_val),
                "ratio_disc": float(ratio_disc),
                "ratio_val": float(ratio_val),
                "ratio_disc_robust": float(ratio_disc_cap),
                "ratio_val_robust": float(ratio_val_cap),
                "n_big_disc": n_big_disc,
                "n_big_val": n_big_val,
                "n_disc": int(n_disc),
                "n_val": int(n_val),
            }

            if config_idx % 100 == 0:
                log.info(f"  [{config_idx}/{total_configs}] ultimo: {algo_name} W={W} ratio_val={ratio_val:.4f}x")

    log.info(f"Sweep completato: {len(results)} configurazioni")
    return results


# =====================================================================
# Permutation test
# =====================================================================


def permutation_test(
    ind_base: np.ndarray,
    ind_extra: np.ndarray,
    algo_fn,
    W: int,
    n_perm: int = 2000,
) -> float:
    """Permutation test per una configurazione specifica su validation set."""
    N = ind_base.shape[0]
    half = N // 2

    # Generate picks e winnings come nello sweep
    freq_base = compute_rolling_freq(ind_base, W)
    freq_extra = compute_rolling_freq(ind_extra, W)
    picks = algo_fn(freq_base, freq_extra, K)
    winnings = evaluate_picks(picks, ind_base, ind_extra, W)

    # Validation slice
    disc_idx_end = max(0, half - W)
    val_picks = picks[disc_idx_end:]
    val_winnings = winnings[disc_idx_end:]
    obs_ev = val_winnings.mean()

    # Val estrazioni indices
    val_estr_idx = list(range(half, N))
    if len(val_picks) != len(val_estr_idx):
        # aggiusta
        val_estr_idx = list(range(W + disc_idx_end, N))

    n_val = len(val_picks)
    if n_val < 10:
        return 1.0

    # Precompute base and extra sets per estrazione (set per-estrazione)
    estr_base_sets = [set(np.where(ind_base[j] == 1)[0]) for j in val_estr_idx]
    estr_extra_sets = [set(np.where(ind_extra[j] == 1)[0]) for j in val_estr_idx]
    pick_sets = [set(p) for p in val_picks]

    rng = random.Random(42)
    count_ge = 0
    for _ in range(n_perm):
        offset = rng.randint(1, n_val - 1)
        total = 0.0
        for idx in range(n_val):
            j = (idx + offset) % n_val
            pick_s = pick_sets[idx]
            drawn = estr_base_sets[j]
            extra = estr_extra_sets[j]
            mb = len(pick_s & drawn)
            rem = pick_s - drawn
            me = len(rem & extra)
            total += PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)
        if total / n_val >= obs_ev:
            count_ge += 1

    return count_ge / n_perm


# =====================================================================
# Rolling temporal analysis (per la best config)
# =====================================================================


def rolling_temporal_analysis(
    ind_base: np.ndarray,
    ind_extra: np.ndarray,
    dates: list[str],
    algo_fn,
    W: int,
    bucket_size: int = 300,
    stride: int = 100,
) -> list[dict]:
    """Per la best config, applica rolling bucket su tutto il dataset.

    Ritorna per ogni bucket temporale: date_start, ratio, pnl, hit_rate, big_wins.
    """
    log.info(f"Rolling analysis: bucket {bucket_size}, stride {stride}")

    # Prima genera picks + winnings per TUTTO il dataset (W..N)
    freq_base = compute_rolling_freq(ind_base, W)
    freq_extra = compute_rolling_freq(ind_extra, W)
    picks = algo_fn(freq_base, freq_extra, K)
    winnings = evaluate_picks(picks, ind_base, ind_extra, W)

    N = ind_base.shape[0]
    n_plays = len(winnings)

    buckets = []
    for start in range(0, n_plays - bucket_size, stride):
        end = start + bucket_size
        bucket_win = winnings[start:end]
        # target_extraction = W + start ... W + end - 1
        date_start = dates[W + start]
        date_end = dates[W + end - 1]
        ev_avg = bucket_win.mean()
        ratio = ev_avg / EV_TEORICO
        pnl = bucket_win.sum() - bucket_size * COSTO_TOTALE
        hit_rate = (bucket_win > 0).mean() * 100
        big_wins = int((bucket_win >= 20).sum())

        buckets.append({
            "start_idx": W + start,
            "end_idx": W + end,
            "date_start": date_start,
            "date_end": date_end,
            "n_plays": bucket_size,
            "ev_avg": float(ev_avg),
            "ratio": float(ratio),
            "pnl": float(pnl),
            "roi": float(pnl / (bucket_size * COSTO_TOTALE) * 100),
            "hit_rate": float(hit_rate),
            "big_wins": big_wins,
        })

    return buckets


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    log.info("=" * 80)
    log.info("MILLIONDAY — WINDOW SWEEP (W=1..300 × 12 algoritmi)")
    log.info("=" * 80)
    log.info(f"EV teorico (K=5 base+Extra): {EV_TEORICO:.4f}€ / 2€  (HE {(1-EV_TEORICO/COSTO_TOTALE)*100:.2f}%, BE {COSTO_TOTALE/EV_TEORICO:.3f}x)")
    log.info("")

    ind_base, ind_extra, dates = load_data()
    N = ind_base.shape[0]

    # Main sweep
    results = run_sweep(ind_base, ind_extra, W_LIST, ALGOS)

    # =================================================================
    # Ranking globale — due versioni: naive e robust
    # =================================================================
    log.info("")
    log.info("=" * 80)
    log.info("TOP 20 RATIO_VAL_ROBUST (cap payout 500€, esclude jackpot distorcenti)")
    log.info("=" * 80)
    sorted_by_robust = sorted(results.values(), key=lambda r: -r["ratio_val_robust"])
    log.info(f"{'rank':>4} {'algoritmo':<18} {'W':>5} {'R_disc_rob':>11} {'R_val_rob':>11} {'big_v':>6} {'ratio_val_naive':>16}")
    log.info("-" * 90)
    for rank, r in enumerate(sorted_by_robust[:20], 1):
        log.info(f"{rank:>4} {r['algo']:<18} {r['W']:>5} {r['ratio_disc_robust']:>+11.4f}x {r['ratio_val_robust']:>+11.4f}x {r['n_big_val']:>6} {r['ratio_val']:>+15.4f}x")

    log.info("")
    log.info("=" * 80)
    log.info("TOP 10 RATIO_VAL NAIVE (include jackpot — INTERPRETARE CON CAUTELA)")
    log.info("=" * 80)
    sorted_configs = sorted(results.values(), key=lambda r: -r["ratio_val"])
    log.info(f"{'rank':>4} {'algoritmo':<18} {'W':>5} {'ratio_disc':>11} {'ratio_val':>11} {'big_v':>6}")
    log.info("-" * 80)
    for rank, r in enumerate(sorted_configs[:10], 1):
        log.info(f"{rank:>4} {r['algo']:<18} {r['W']:>5} {r['ratio_disc']:>+11.4f}x {r['ratio_val']:>+11.4f}x {r['n_big_val']:>6}")

    # =================================================================
    # Best W per algoritmo (usa ratio robust)
    # =================================================================
    log.info("")
    log.info("=" * 80)
    log.info("BEST W PER ALGORITMO (basato su ratio_val_robust)")
    log.info("=" * 80)
    log.info(f"{'algoritmo':<18} {'best W':>8} {'R_val_rob':>11} {'R_disc_rob':>11} {'coerenza':>10}")
    log.info("-" * 80)
    by_algo = {}
    for (algo, W), r in results.items():
        if algo not in by_algo or r["ratio_val_robust"] > by_algo[algo]["ratio_val_robust"]:
            by_algo[algo] = r
    for algo, r in sorted(by_algo.items(), key=lambda x: -x[1]["ratio_val_robust"]):
        coerenza = "✓" if abs(r["ratio_disc_robust"] - r["ratio_val_robust"]) < 0.10 else "⚠"
        log.info(f"{algo:<18} {r['W']:>8} {r['ratio_val_robust']:>+11.4f}x {r['ratio_disc_robust']:>+11.4f}x {coerenza:>10}")

    # =================================================================
    # Permutation test top 5 ROBUST
    # =================================================================
    log.info("")
    log.info("=" * 80)
    log.info("PERMUTATION TEST sulle top 5 configurazioni ROBUST")
    log.info("=" * 80)
    bonf_threshold = 0.05 / len(results)
    log.info(f"Bonferroni soglia ({len(results)} test): {bonf_threshold:.5f}")
    log.info("")
    log.info(f"{'algoritmo':<18} {'W':>5} {'R_val_rob':>11} {'p_value':>10} {'Bonf-sig?':>10}")
    log.info("-" * 80)
    perm_results = []
    for r in sorted_by_robust[:5]:
        log.info(f"Testing {r['algo']} W={r['W']}...")
        p = permutation_test(ind_base, ind_extra, ALGOS[r["algo"]], r["W"], n_perm=2000)
        sig = "YES" if p < bonf_threshold else ("raw-sig" if p < 0.05 else "NO")
        log.info(f"{r['algo']:<18} {r['W']:>5} {r['ratio_val_robust']:>+11.4f}x {p:>10.4f} {sig:>10}")
        perm_results.append({**r, "p_value": p, "bonf_sig": p < bonf_threshold})

    # =================================================================
    # Rolling temporal analysis on best ROBUST config
    # =================================================================
    best = sorted_by_robust[0]
    log.info("")
    log.info("=" * 80)
    log.info(f"ROLLING TEMPORAL ANALYSIS — best config: {best['algo']} W={best['W']}")
    log.info("=" * 80)
    bucket_size = 300
    stride = 100
    buckets = rolling_temporal_analysis(
        ind_base, ind_extra, dates, ALGOS[best["algo"]], best["W"],
        bucket_size=bucket_size, stride=stride,
    )

    log.info(f"Bucket: {bucket_size} giocate ciascuno, stride {stride}")
    log.info(f"Totale bucket: {len(buckets)}")
    log.info("")
    log.info(f"{'#':>3} {'data_start':<20} {'ratio':>10} {'ROI%':>7} {'hit%':>6} {'big':>5} {'PnL':>10}")
    log.info("-" * 80)
    ratios = []
    for idx, b in enumerate(buckets, 1):
        log.info(f"{idx:>3} {b['date_start']:<20} {b['ratio']:>+9.4f}x {b['roi']:>+6.1f}% {b['hit_rate']:>5.1f}% {b['big_wins']:>5} {b['pnl']:>+9.0f}€")
        ratios.append(b["ratio"])

    mean_ratio = sum(ratios) / len(ratios)
    sd_ratio = sqrt(sum((r - mean_ratio) ** 2 for r in ratios) / len(ratios))
    log.info("")
    log.info(f"Ratio rolling: mean={mean_ratio:.4f}x, SD={sd_ratio:.4f}")
    log.info(f"Min: {min(ratios):.4f}x, Max: {max(ratios):.4f}x")
    bucket_above_be = sum(1 for r in ratios if r >= 1.508)
    bucket_above_1 = sum(1 for r in ratios if r >= 1.0)
    log.info(f"Bucket sopra breakeven (1.508x): {bucket_above_be}/{len(ratios)}")
    log.info(f"Bucket sopra baseline (1.0x): {bucket_above_1}/{len(ratios)}")

    # =================================================================
    # Salva risultati JSON
    # =================================================================
    out = {
        "dataset_size": N,
        "algorithms": list(ALGOS.keys()),
        "w_list": W_LIST,
        "ev_teorico": EV_TEORICO,
        "sweep": [
            {**r, "key": f"{r['algo']}_W{r['W']}"}
            for r in sorted_configs
        ],
        "best_per_algo": {a: r for a, r in by_algo.items()},
        "permutation_top5": perm_results,
        "rolling_buckets": buckets,
        "mean_rolling_ratio": mean_ratio,
        "sd_rolling_ratio": sd_ratio,
    }
    out_path = Path(__file__).parent / "window_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    log.info(f"\nRisultati salvati in: {out_path}")


if __name__ == "__main__":
    main()
