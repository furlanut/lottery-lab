"""Test specifico: cross-window adjacency-filtered lag correlation.

Proposta originaria (Appendice H.8):
  Per ogni numero x, finestra A finisce al tempo t, finestra B inizia al tempo t+L.
  Correlare freq(x, A) con freq(x+d, B) per d in {-5..+5} e L in {1, 50, 100, 200, 500}.

Interpretazione:
  Se corr(freq(x, A), freq(x+1, B)) > 0 per lag L positivo:
    "quando x e caldo in A, x+1 diventa caldo in B (dopo lag L)"
    → esiste un meccanismo di 'trasferimento spazio-temporale' della frequenza
    → il PRNG ha memoria lag-L con adjacency shift

  Se corr = 0 per ogni (L, d):
    il PRNG non ha dipendenze spazio-temporali a lungo raggio

Si aspetta:
  Baseline (stesso numero, d=0): corr potrebbe essere debolmente positiva per
  autocorrelazione marginale, o zero per PRNG perfetto.
  Offset d=±1..±5: se c'e meccanismo, corr decrescente con |d|.
  Valori di L brevi (1, 50): piu forte se il meccanismo e transient.
  Valori di L lunghi (500): piu debole, ma il segnale vero dovrebbe sopravvivere.
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
log = logging.getLogger("lag_adjacency")


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


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom > 0 else 0.0


def _compute_freq_array(window: list[dict]) -> list[int]:
    """Ritorna array di 91 elementi [0, freq[1], freq[2], ..., freq[90]]."""
    freq = Counter()
    for e in window:
        for n in e["numeri"]:
            freq[n] += 1
    return [freq.get(i, 0) for i in range(91)]


def test_lag_adjacency(
    data: list[dict],
    W: int,
    lag: int,
    offsets: list[int],
    stride: int = 10,
) -> dict:
    """Per ogni t (stride apart), compute freq(A ending at t) e freq(B ending at t+lag).
    Per ogni offset d in offsets: accumula pairs (freq_A[x], freq_B[x+d]) per x in 1..90.
    Poi calcola Pearson r per ogni d.
    """
    # Struttura: pairs[d] = (xs, ys)
    pairs: dict[int, tuple[list, list]] = {d: ([], []) for d in offsets}

    # sliding windows
    last_t = len(data) - lag
    step_count = 0
    for t in range(W, last_t, stride):
        win_a = data[t - W : t]
        win_b = data[t + lag - W : t + lag]
        freq_a = _compute_freq_array(win_a)
        freq_b = _compute_freq_array(win_b)
        for d in offsets:
            xs, ys = pairs[d]
            for x in range(1, 91):
                xd = x + d
                if 1 <= xd <= 90:
                    xs.append(freq_a[x])
                    ys.append(freq_b[xd])
        step_count += 1

    results = {}
    for d in offsets:
        xs, ys = pairs[d]
        r = _pearson(xs, ys)
        n = len(xs)
        # Fisher z: sd(r) ≈ 1/sqrt(n-3); z = r * sqrt(n-3) approx
        # But our samples are NOT independent (rolling windows share data),
        # we estimate effective N as step_count (number of distinct time points)
        eff_n = step_count
        z_approx = r * sqrt(eff_n - 3) if eff_n > 3 else 0
        results[d] = {"r": r, "n_samples": n, "eff_n": eff_n, "z": z_approx}

    return {"W": W, "lag": lag, "step_count": step_count, "offsets": results}


def main() -> None:
    log.info("Caricamento dataset...")
    data = _load()
    N = len(data)
    log.info(f"Dataset: {N:,} estrazioni\n")

    W = 100
    lags = [1, 50, 100, 200, 500, 1000]
    offsets = list(range(-5, 6))  # -5..+5
    stride = W  # non-overlapping windows for independence

    log.info("=" * 90)
    log.info(f"CROSS-WINDOW ADJACENCY-FILTERED LAG CORRELATION (W={W}, stride={stride})")
    log.info("=" * 90)
    log.info("Per ogni (lag L, offset d), calcola corr Pearson:")
    log.info("  freq(x, window A ending at t) vs freq(x+d, window B ending at t+L)")
    log.info("")

    all_results = {}
    for L in lags:
        log.info(f">>> lag L = {L}")
        r = test_lag_adjacency(data, W=W, lag=L, offsets=offsets, stride=stride)
        all_results[L] = r
        log.info(f"    step count: {r['step_count']}, n samples per d: ~{list(r['offsets'].values())[0]['n_samples']}")

    # Tabella risultati
    log.info("")
    log.info("=" * 90)
    log.info("MATRICE CORRELAZIONE r[L][d]")
    log.info("=" * 90)

    # Header
    header = "L\\d  " + "  ".join(f"{d:>+3}" for d in offsets)
    log.info(header)
    log.info("-" * len(header))
    for L in lags:
        row = f"{L:>4} "
        for d in offsets:
            r = all_results[L]["offsets"][d]["r"]
            row += f"  {r:>+.3f}"
        log.info(row)

    log.info("")
    log.info("=" * 90)
    log.info("MATRICE Z-SCORE approssimato (indipendenza stride=W assunta)")
    log.info("=" * 90)
    header = "L\\d  " + "  ".join(f"{d:>+3}" for d in offsets)
    log.info(header)
    log.info("-" * len(header))
    for L in lags:
        row = f"{L:>4} "
        for d in offsets:
            z = all_results[L]["offsets"][d]["z"]
            marker = " "
            if abs(z) > 3.0:
                marker = "*"  # significativo
            if abs(z) > 5.0:
                marker = "**"
            row += f"  {z:>+.2f}{marker}"
        log.info(row)

    # Focus: r per d=0 (baseline autocorrelazione), d=1 (adjacency), d=5 (edge), d=-5
    log.info("")
    log.info("=" * 90)
    log.info("SINTESI: correlation per adjacency offsets critici")
    log.info("=" * 90)
    log.info(f"{'L':>6}  {'r(d=0)':>10}  {'r(d=1)':>10}  {'r(d=-1)':>10}  {'r(d=5)':>10}  {'r(d=-5)':>10}")
    log.info("-" * 80)
    for L in lags:
        o = all_results[L]["offsets"]
        log.info(
            f"{L:>6}  {o[0]['r']:>+10.4f}  {o[1]['r']:>+10.4f}  {o[-1]['r']:>+10.4f}  "
            f"{o[5]['r']:>+10.4f}  {o[-5]['r']:>+10.4f}"
        )

    # VERDETTO
    log.info("")
    log.info("=" * 90)
    log.info("VERDETTO")
    log.info("=" * 90)

    # CRITICO: a L < W le finestre A e B si sovrappongono (overlap = W-L).
    # Questo produce correlazione spuria r ≈ (W-L)/W a d=0, NON un meccanismo RNG.
    # Il test vero e per L >= W (finestre disgiunte).

    log.info("AVVISO: a L<W le finestre A e B si sovrappongono (overlap=W-L).")
    log.info("r(d=0) ≈ (W-L)/W e' artefatto dell'overlap, non segnale PRNG.")
    log.info("")
    log.info("Verifica artefatto overlap:")
    for L in lags:
        if L < W:
            expected_r = (W - L) / W
            actual_r = all_results[L]["offsets"][0]["r"]
            log.info(f"  L={L:>4}: r(d=0) atteso (overlap) = {expected_r:.3f}, osservato = {actual_r:+.3f}")
    log.info("")

    # Test GENUINO: lag >= W (finestre disgiunte), d != 0 (adjacency shift)
    max_z_genuine = 0.0
    max_L_genuine = None
    for L in lags:
        if L < W:
            continue
        for d in offsets:
            if d == 0:
                continue
            z = all_results[L]["offsets"][d]["z"]
            if abs(z) > max_z_genuine:
                max_z_genuine = abs(z)
                max_L_genuine = (L, d)

    # Test baseline: d=0 per L>=W (persistenza stesso numero a lag lungo)
    max_z_diag = 0.0
    max_L_diag = None
    for L in lags:
        if L < W:
            continue
        z = all_results[L]["offsets"][0]["z"]
        if abs(z) > max_z_diag:
            max_z_diag = abs(z)
            max_L_diag = (L, 0)

    log.info(f"Test GENUINO (finestre disgiunte, L >= W={W}):")
    log.info(f"  Max |z| per d ≠ 0 (adjacency): {max_z_genuine:.2f} a {max_L_genuine}")
    log.info(f"  Max |z| per d = 0 (persistenza): {max_z_diag:.2f} a {max_L_diag}")

    # Bonferroni su test genuine: (n_lags >= W) * (n_offsets - 1)
    genuine_lags = [L for L in lags if L >= W]
    n_tests = len(genuine_lags) * (len(offsets) - 1)
    bonf_z = 2.8 + 0.3  # approssimato per ~40 test multipli

    if max_z_genuine > bonf_z:
        log.info(f"\n*** ADJACENCY CROSS-WINDOW SIGNIFICATIVA (z>{bonf_z:.2f}, Bonferroni {n_tests} test) ***")
    else:
        log.info(f"\nCONFERMA: nessun pattern lag-adjacency. max |z|={max_z_genuine:.2f} < Bonferroni {bonf_z:.2f}.")
        log.info("Il PRNG 10eLotto non ha memoria cross-finestra con shift numerico.")


if __name__ == "__main__":
    main()
