"""Test meccanicistici per capire perché vicinanza batte dual_target.

Tre test progettati per discriminare fra tre ipotesi alternative:

  H1. Vicinanza sfrutta clustering naturale in 20-su-90 (geometria)
  H2. Vicinanza sfrutta autocorrelazione residua del RNG
  H3. Vicinanza sfrutta il seed-selection (momento frequenziale)

Test 1 — Autocorrelazione spaziale delle estrazioni
    Per ogni estrazione, distribuisce le C(20,2)=190 distanze |a-b| fra coppie.
    Confronta con la distribuzione teorica sotto uniforme (senza ripetizione).
    Se le distanze piccole (d=1..5) sono sovra-rappresentate → clustering strutturale.

Test 2 — Label-shuffle permutation test
    Applica una permutazione random π dei label numerici 1-90 al dataset.
    Sostituisce in ogni estrazione ogni numero n con π(n).
    Questo preserva:
      - Frequenza di ogni "slot numerico"
      - Co-occorrenza di coppie specifiche
    Distrugge:
      - Adiacenza numerica
    Ri-esegue backtest vicinanza. Se il ratio crolla → è la GEOGRAFIA a
    dare l'edge. Se rimane stabile → è un artefatto numerico generico.

Test 3 — Vicinanza con seed random
    Invece di scegliere il seed come numero più frequente in W=100,
    lo sceglie random 1-90. Poi procede come vicinanza classica.
    Se ratio ≥ 1.05 → il vantaggio è giocare un CLUSTER (qualsiasi).
    Se ratio ≤ 1.00 → il vantaggio è nel seed-selection (frequenza-based).
"""

# ruff: noqa: E501, S311
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
log = logging.getLogger("spatial_tests")

K = 6
W = 100
COSTO = 2.0
EV_TEORICO = 1.80


def _load_all() -> list[DiecieLottoEstrazione]:
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
        return list(rows)
    finally:
        s.close()


def _extract_numbers(e):
    """Ritorna (base, extra) come liste, facendo una COPIA per non fare fetch ripetuti."""
    return list(e.numeri), list(e.numeri_extra)


# =====================================================================
# TEST 1 — Autocorrelazione spaziale
# =====================================================================


def _theoretical_dist_distribution(n: int) -> dict[int, float]:
    """Distribuzione teorica di |a-b| per coppia di numeri distinti estratti da 1..N.

    P(|a-b|=d) = 2*(N-d) / (N*(N-1))  per d=1..N-1
    """
    total = n * (n - 1)
    return {d: 2 * (n - d) / total for d in range(1, n)}


def test1_spatial_autocorr(estrazioni: list) -> dict:
    """Aggrega tutte le distanze |a-b| nelle coppie e confronta con teorico."""
    log.info("=" * 70)
    log.info("TEST 1 — Autocorrelazione spaziale")
    log.info("=" * 70)

    pb = _theoretical_dist_distribution(90)

    # Per ciascuna estrazione, raccogli le 190 distanze fra coppie dei 20 base
    obs = Counter()
    total_pairs = 0
    for e in estrazioni:
        nums, _ = _extract_numbers(e)
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                d = abs(nums[i] - nums[j])
                obs[d] += 1
                total_pairs += 1

    # Confronto: frequenza osservata vs attesa
    # Per distanze d=1..10 mostriamo in dettaglio
    log.info(f"Estrazioni: {len(estrazioni)}")
    log.info(f"Coppie totali (190 per estrazione): {total_pairs}")
    log.info("")
    log.info(f"{'d':>4} {'Oss':>8} {'Atteso':>8} {'Diff%':>7} {'z':>8} {'Cum oss':>10} {'Cum teor':>10}")
    log.info("-" * 70)

    cum_obs = 0
    cum_theor = 0.0
    agg_small_obs = 0
    agg_small_theor = 0.0
    for d in range(1, 11):
        o = obs.get(d, 0)
        t = pb[d] * total_pairs
        diff_pct = (o - t) / t * 100 if t > 0 else 0
        # SE binomiale approssimata
        sd = (t * (1 - pb[d])) ** 0.5
        z = (o - t) / sd if sd > 0 else 0
        cum_obs += o
        cum_theor += t
        log.info(f"{d:>4} {o:>8} {t:>8.0f} {diff_pct:>+6.2f}% {z:>+8.2f} {cum_obs:>10} {cum_theor:>10.0f}")
        agg_small_obs += o
        agg_small_theor += t

    # Distanze piccole (d ≤ 5) — il cluster di vicinanza è proprio questo range
    small_obs = sum(obs.get(d, 0) for d in range(1, 6))
    small_theor = sum(pb[d] for d in range(1, 6)) * total_pairs
    small_diff_pct = (small_obs - small_theor) / small_theor * 100
    # SE per binomiale
    p_small = sum(pb[d] for d in range(1, 6))
    sd_small = (total_pairs * p_small * (1 - p_small)) ** 0.5
    z_small = (small_obs - small_theor) / sd_small if sd_small > 0 else 0
    log.info("")
    log.info("Aggregato d ≤ 5 (zona cluster vicinanza):")
    log.info(f"  Osservato: {small_obs:,}")
    log.info(f"  Teorico:   {small_theor:,.0f}")
    log.info(f"  Differenza: {small_diff_pct:+.3f}%")
    log.info(f"  Z-score: {z_small:+.2f}")

    # Distanze grandi (d >= 40)
    large_obs = sum(obs.get(d, 0) for d in range(40, 90))
    large_theor = sum(pb[d] for d in range(40, 90)) * total_pairs
    large_diff_pct = (large_obs - large_theor) / large_theor * 100
    p_large = sum(pb[d] for d in range(40, 90))
    sd_large = (total_pairs * p_large * (1 - p_large)) ** 0.5
    z_large = (large_obs - large_theor) / sd_large if sd_large > 0 else 0
    log.info("")
    log.info("Aggregato d ≥ 40 (zona 'spread'):")
    log.info(f"  Osservato: {large_obs:,}")
    log.info(f"  Teorico:   {large_theor:,.0f}")
    log.info(f"  Differenza: {large_diff_pct:+.3f}%")
    log.info(f"  Z-score: {z_large:+.2f}")

    verdict = "NESSUNA autocorr spaziale significativa"
    if abs(z_small) > 3.0 or abs(z_large) > 3.0:
        verdict = (
            "AUTOCORR SPAZIALE RILEVATA: "
            f"d≤5 diff {small_diff_pct:+.2f}%, d≥40 diff {large_diff_pct:+.2f}%"
        )
    log.info(f"\nVerdetto: {verdict}")

    return {
        "total_pairs": total_pairs,
        "obs_d_le_5": small_obs,
        "theor_d_le_5": small_theor,
        "diff_pct_d_le_5": small_diff_pct,
        "z_d_le_5": z_small,
        "obs_d_ge_40": large_obs,
        "theor_d_ge_40": large_theor,
        "diff_pct_d_ge_40": large_diff_pct,
        "z_d_ge_40": z_large,
        "verdict": verdict,
    }


# =====================================================================
# BACKTEST INFRASTRUCTURE — riusato da test 2 e 3
# =====================================================================


def _pick_vicinanza_classic(window: list) -> list[int]:
    """Strategia vicinanza classica: seed = most_common(base), 5 vicini più frequenti."""
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
    # pad
    if len(pick) < K:
        for n, _ in freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= K:
                break
    return sorted(pick[:K])


def _pick_vicinanza_random_seed(window: list, rng: random.Random) -> list[int]:
    """Come vicinanza, ma il seed e' un numero random 1-90."""
    freq = Counter()
    for e in window:
        for n in e["numeri"]:
            freq[n] += 1
    seed = rng.randint(1, 90)  # noqa: S311
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
    return sorted(pick[:K])


def _run_backtest(data: list[dict], strategy: str, rng=None) -> dict:
    """Esegue backtest su una lista di estrazioni, ritorna stats."""
    pb = PREMI_BASE.get(K, {})
    pe = PREMI_EXTRA.get(K, {})

    giocate, vinte, totale_vinto, big_wins = 0, 0, 0.0, 0
    match_base_dist: dict[int, int] = {}

    for i in range(W, len(data)):
        window = data[max(0, i - W) : i]
        estr = data[i]

        if strategy == "vicinanza":
            pick = _pick_vicinanza_classic(window)
        elif strategy == "vicinanza_random_seed":
            pick = _pick_vicinanza_random_seed(window, rng)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        drawn = set(estr["numeri"])
        extra = set(estr["extra"])
        pick_set = set(pick)

        mb = len(pick_set & drawn)
        me = len((pick_set - drawn) & extra)
        v = pb.get(mb, 0.0) + pe.get(me, 0.0)

        giocate += 1
        totale_vinto += v
        if v > 0:
            vinte += 1
        if v >= 20:
            big_wins += 1
        match_base_dist[mb] = match_base_dist.get(mb, 0) + 1

    totale_giocato = giocate * COSTO
    pnl = totale_vinto - totale_giocato
    avg_vincita = totale_vinto / giocate if giocate else 0
    ratio = avg_vincita / EV_TEORICO if EV_TEORICO else 0
    roi = pnl / totale_giocato * 100 if totale_giocato else 0

    return {
        "giocate": giocate,
        "vinte": vinte,
        "big_wins": big_wins,
        "hit_rate": round(vinte / giocate * 100, 2) if giocate else 0,
        "totale_giocato": totale_giocato,
        "totale_vinto": round(totale_vinto, 2),
        "pnl": round(pnl, 2),
        "roi": round(roi, 4),
        "ratio_vs_ev": round(ratio, 4),
        "jackpots_base": match_base_dist.get(5, 0) + match_base_dist.get(6, 0),
    }


# =====================================================================
# TEST 2 — Label-shuffle permutation test
# =====================================================================


def _apply_label_permutation(estrazioni: list, seed: int) -> list[dict]:
    """Applica una permutazione dei label 1-90, mantenendo co-occorrenza."""
    rng = random.Random(seed)
    perm = list(range(1, 91))
    rng.shuffle(perm)
    # perm[i-1] e' il nuovo label per il numero i
    mapping = {i + 1: perm[i] for i in range(90)}

    shuffled = []
    for e in estrazioni:
        nums, extra = _extract_numbers(e)
        new_nums = [mapping[n] for n in nums]
        new_extra = [mapping[n] for n in extra]
        shuffled.append({"numeri": new_nums, "extra": new_extra})
    return shuffled


def _dict_view(estrazioni: list) -> list[dict]:
    """Converte ORM objects in dict plain per velocita."""
    return [
        {"numeri": list(e.numeri), "extra": list(e.numeri_extra)} for e in estrazioni
    ]


def test2_label_shuffle(estrazioni: list, n_permutations: int = 20) -> dict:
    """Esegue vicinanza su N dataset con label permutati + baseline."""
    log.info("=" * 70)
    log.info(f"TEST 2 — Label-shuffle ({n_permutations} permutations)")
    log.info("=" * 70)

    # Baseline: vicinanza sull'originale
    log.info("Calcolo baseline (vicinanza su dataset originale)...")
    baseline = _run_backtest(_dict_view(estrazioni), "vicinanza")
    log.info(
        f"  Baseline: ratio {baseline['ratio_vs_ev']:.4f}x  ROI {baseline['roi']:+.2f}%"
    )

    # Permuted: vicinanza su dataset permutati
    log.info(f"\nEsecuzione su {n_permutations} permutazioni label casuali...")
    ratios = []
    rois = []
    for pi in range(n_permutations):
        shuffled = _apply_label_permutation(estrazioni, seed=42 + pi)
        stats = _run_backtest(shuffled, "vicinanza")
        ratios.append(stats["ratio_vs_ev"])
        rois.append(stats["roi"])
        if (pi + 1) % 5 == 0:
            log.info(
                f"  [{pi+1}/{n_permutations}] median ratio: {sorted(ratios)[len(ratios)//2]:.4f}x"
            )

    mean_perm = sum(ratios) / len(ratios)
    sd_perm = (sum((r - mean_perm) ** 2 for r in ratios) / len(ratios)) ** 0.5
    mean_roi = sum(rois) / len(rois)

    # P-value: frazione di permutazioni con ratio >= osservato
    p_value = sum(1 for r in ratios if r >= baseline["ratio_vs_ev"]) / len(ratios)

    log.info("")
    log.info(f"Baseline (originale):           ratio {baseline['ratio_vs_ev']:.4f}x  ROI {baseline['roi']:+.2f}%")
    log.info(f"Permutati mean ± SD:            ratio {mean_perm:.4f}x ± {sd_perm:.4f}  ROI {mean_roi:+.2f}%")
    log.info(f"Permutati range [min, max]:     [{min(ratios):.4f}, {max(ratios):.4f}]")
    log.info(f"P-value (permutati ≥ baseline): {p_value:.4f}")

    if p_value < 0.05:
        verdict = (
            "LA GEOGRAFIA CONTA: il dataset originale ha adjacency-edge che i permutati perdono. "
            "Vicinanza sfrutta una proprietà spaziale reale."
        )
    elif p_value > 0.5:
        verdict = (
            "LA GEOGRAFIA NON CONTA: i permutati sono comparabili o migliori. "
            "L'edge di vicinanza NON viene dall'adjacency ma dalla selezione del seed o varianza."
        )
    else:
        verdict = (
            f"BORDERLINE (p={p_value:.3f}): effetto debole ma presente. "
            "Servono più permutazioni o più dati."
        )
    log.info(f"\nVerdetto: {verdict}")

    return {
        "baseline_ratio": baseline["ratio_vs_ev"],
        "baseline_roi": baseline["roi"],
        "permuted_ratios": ratios,
        "permuted_mean": mean_perm,
        "permuted_sd": sd_perm,
        "permuted_min": min(ratios),
        "permuted_max": max(ratios),
        "p_value": p_value,
        "n_permutations": n_permutations,
        "verdict": verdict,
    }


# =====================================================================
# TEST 3 — Vicinanza con seed random
# =====================================================================


def test3_random_seed(estrazioni: list, n_trials: int = 10) -> dict:
    """Confronta vicinanza classica vs vicinanza con seed random."""
    log.info("=" * 70)
    log.info(f"TEST 3 — Vicinanza con seed random ({n_trials} trials)")
    log.info("=" * 70)

    data = _dict_view(estrazioni)

    # Classica (deterministica)
    log.info("Calcolo vicinanza classica (seed = most_frequent)...")
    classic = _run_backtest(data, "vicinanza")
    log.info(f"  Classica: ratio {classic['ratio_vs_ev']:.4f}x  ROI {classic['roi']:+.2f}%")

    # Random seed: media su N trial
    log.info(f"\nCalcolo vicinanza random-seed ({n_trials} trials)...")
    ratios = []
    rois = []
    for ti in range(n_trials):
        rng = random.Random(42 + ti)
        stats = _run_backtest(data, "vicinanza_random_seed", rng=rng)
        ratios.append(stats["ratio_vs_ev"])
        rois.append(stats["roi"])
        log.info(
            f"  [{ti+1}/{n_trials}] ratio {stats['ratio_vs_ev']:.4f}x  ROI {stats['roi']:+.2f}%"
        )

    mean_r = sum(ratios) / len(ratios)
    sd_r = (sum((r - mean_r) ** 2 for r in ratios) / len(ratios)) ** 0.5
    mean_roi = sum(rois) / len(rois)

    log.info("")
    log.info(f"Classica (seed=most_freq):      ratio {classic['ratio_vs_ev']:.4f}x  ROI {classic['roi']:+.2f}%")
    log.info(f"Random-seed mean ± SD:          ratio {mean_r:.4f}x ± {sd_r:.4f}  ROI {mean_roi:+.2f}%")
    log.info(f"Random-seed range [min, max]:   [{min(ratios):.4f}, {max(ratios):.4f}]")

    # Verdetto
    if mean_r > 1.05:
        verdict = (
            "IL CLUSTER BASTA: random-seed resta > 1.05. "
            "Il vantaggio di vicinanza è GIOCARE CON UN CLUSTER, "
            "non quale cluster. La selezione del seed e' marginale."
        )
    elif mean_r < 1.00:
        verdict = (
            "IL SEED CONTA: random-seed crolla sotto baseline. "
            "L'edge di vicinanza è il SEED-SELECTION (frequenza-based), "
            "non la forma-cluster in se'."
        )
    else:
        verdict = (
            f"SEED + CLUSTER INSIEME: random-seed ({mean_r:.4f}x) è intermedio "
            f"tra classica ({classic['ratio_vs_ev']:.4f}x) e baseline (1.000x). "
            "Entrambi i fattori contribuiscono."
        )
    log.info(f"\nVerdetto: {verdict}")

    return {
        "classic_ratio": classic["ratio_vs_ev"],
        "classic_roi": classic["roi"],
        "random_seed_ratios": ratios,
        "random_seed_mean": mean_r,
        "random_seed_sd": sd_r,
        "random_seed_min": min(ratios),
        "random_seed_max": max(ratios),
        "n_trials": n_trials,
        "verdict": verdict,
    }


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    log.info("Caricamento dataset dal DB locale...")
    estrazioni = _load_all()
    log.info(f"Dataset: {len(estrazioni):,} estrazioni 10eLotto")
    log.info("")

    results = {}
    results["test1"] = test1_spatial_autocorr(estrazioni)
    log.info("")
    results["test2"] = test2_label_shuffle(estrazioni, n_permutations=20)
    log.info("")
    results["test3"] = test3_random_seed(estrazioni, n_trials=10)

    log.info("")
    log.info("=" * 70)
    log.info("SINTESI FINALE")
    log.info("=" * 70)
    log.info("")
    log.info(f"Test 1 (spatial autocorr): {results['test1']['verdict']}")
    log.info(f"Test 2 (label-shuffle):    {results['test2']['verdict']}")
    log.info(f"Test 3 (random seed):      {results['test3']['verdict']}")


if __name__ == "__main__":
    main()
