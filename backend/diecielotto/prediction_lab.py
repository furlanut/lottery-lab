from __future__ import annotations

"""10eLotto Prediction Lab — 8 test predittivi completi.

P1: freq+rit+dec (vincitore paper Lotto)
P2: vicinanza pura (sweep D×W)
P3: top N frequenti (sweep finestre lunghe)
P4: anti-frequenti (numeri freddi)
P5: mix caldi+freddi
P6: overlap-based (persistenza scoring)
P7: somma ottimale (regressione alla media)
P8: ML ensemble (gradient boosting)

Target: 6 numeri + Extra, costo EUR 2, EV baseline 1.8013.
Breakeven Special Time: 1.067x.
"""

import logging
from collections import Counter
from typing import Optional

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Constants ---
K = 6
COSTO = 2.0
EV_BASELINE = 1.8013
BREAKEVEN_ST = 1.067  # Special Time breakeven
PREMI_BASE = {3: 2.00, 4: 10.00, 5: 100.00, 6: 1000.00}
PREMI_EXTRA = {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00}


def _ev(pick6: set, drawn20: set, extra15: set) -> float:
    mb = len(pick6 & drawn20)
    rem = pick6 - drawn20
    me = len(rem & extra15)
    return PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)


def _match_base(pick6: set, drawn20: set) -> int:
    return len(pick6 & drawn20)


# --- Data ---
def carica() -> list[dict]:
    session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "numeri": set(r.numeri),
                "extra": set(r.numeri_extra),
                "numeri_list": r.numeri,
            }
            for r in rows
        ]
    finally:
        session.close()


# --- Test framework ---
def run_test(
    estrazioni: list[dict],
    selector_fn,
    label: str,
    config_str: str = "",
):
    """Esegue un test predittivo con discovery/validation split."""
    n = len(estrazioni)
    half = n // 2

    ev_disc, ev_val = 0.0, 0.0
    mb_disc, mb_val = 0.0, 0.0
    n_disc, n_val = 0, 0
    start = selector_fn("_get_min_w_", None, None)
    if start is None:
        start = 50

    for i in range(start, n):
        pick = selector_fn(estrazioni, i, None)
        if pick is None or len(pick) < K:
            continue
        pick = set(list(pick)[:K])

        drawn = estrazioni[i]["numeri"]
        extra = estrazioni[i]["extra"]
        e = _ev(pick, drawn, extra)
        mb = _match_base(pick, drawn)

        if i < half:
            ev_disc += e
            mb_disc += mb
            n_disc += 1
        else:
            ev_val += e
            mb_val += mb
            n_val += 1

    avg_ev_d = ev_disc / n_disc if n_disc else 0
    avg_ev_v = ev_val / n_val if n_val else 0
    avg_mb_d = mb_disc / n_disc if n_disc else 0
    avg_mb_v = mb_val / n_val if n_val else 0
    ratio_d = avg_ev_d / EV_BASELINE if EV_BASELINE > 0 else 0
    ratio_v = avg_ev_v / EV_BASELINE if EV_BASELINE > 0 else 0
    supera = "SI" if ratio_v >= BREAKEVEN_ST else "no"

    return {
        "label": label,
        "config": config_str,
        "ev_disc": avg_ev_d,
        "ev_val": avg_ev_v,
        "mb_disc": avg_mb_d,
        "mb_val": avg_mb_v,
        "ratio_d": ratio_d,
        "ratio_v": ratio_v,
        "n_disc": n_disc,
        "n_val": n_val,
        "supera_be": supera,
    }


def print_result(r: dict):
    print(
        f"  {r['label']:<22} {r['config']:<14} "
        f"mb_d={r['mb_disc']:.3f} mb_v={r['mb_val']:.3f}  "
        f"EV_d={r['ev_disc']:.4f} EV_v={r['ev_val']:.4f}  "
        f"R_d={r['ratio_d']:.4f}x R_v={r['ratio_v']:.4f}x  "
        f"BE_ST={r['supera_be']}"
    )


# ===================================================================
# P1 — freq+rit+dec
# ===================================================================
def make_p1(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        freq = Counter()
        last_seen = {}
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
                last_seen[num] = j

        ritardo_soglia = w // 5
        candidates = []
        for num in range(1, 91):
            f = freq.get(num, 0)
            ls = last_seen.get(num, -1)
            rit = i - ls if ls >= 0 else w
            if f >= 3 and rit >= ritardo_soglia:
                dec = (num - 1) // 10
                candidates.append((num, f, rit, dec))

        if len(candidates) < K:
            # Fallback: top freq
            top = freq.most_common(K)
            return {n for n, _ in top}

        # Score: freq + ritardo normalizzato, prefer same decade pairs
        candidates.sort(key=lambda x: -(x[1] + x[2] / w * 5))
        pick = set()
        for num, _f, _rit, _dec in candidates:
            pick.add(num)
            if len(pick) >= K:
                break
        return pick

    return selector


# ===================================================================
# P2 — Vicinanza pura
# ===================================================================
def make_p2(w: int, d: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        # Seed = most frequent
        seed = freq.most_common(1)[0][0]
        # Nearby + frequent
        nearby = [
            (num, freq.get(num, 0))
            for num in range(1, 91)
            if abs(num - seed) <= d and num != seed and freq.get(num, 0) > 0
        ]
        nearby.sort(key=lambda x: -x[1])
        pick = {seed}
        for num, _ in nearby:
            pick.add(num)
            if len(pick) >= K:
                break
        # Pad if not enough
        if len(pick) < K:
            for num, _ in freq.most_common(K + 10):
                pick.add(num)
                if len(pick) >= K:
                    break
        return pick

    return selector


# ===================================================================
# P3 — Top N frequenti
# ===================================================================
def make_p3(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        return {n for n, _ in freq.most_common(K)}

    return selector


# ===================================================================
# P4 — Anti-frequenti (numeri freddi)
# ===================================================================
def make_p4(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        all_nums = list(range(1, 91))
        all_nums.sort(key=lambda x: freq.get(x, 0))
        return set(all_nums[:K])

    return selector


# ===================================================================
# P5 — Mix caldi+freddi
# ===================================================================
def make_p5(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        hot = [n for n, _ in freq.most_common(3)]
        all_nums = list(range(1, 91))
        all_nums.sort(key=lambda x: freq.get(x, 0))
        cold = [n for n in all_nums[:10] if n not in hot][:3]
        return set(hot + cold)

    return selector


# ===================================================================
# P6 — Overlap-based (persistence scoring)
# ===================================================================
def make_p6(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        scores = Counter()
        for j in range(max(0, i - w), i):
            for num in estrazioni[j]["numeri"]:
                scores[num] += 1
        # Weight recent more: consecutive presence bonus
        for lag in range(1, min(4, i + 1)):
            for num in estrazioni[i - lag]["numeri"]:
                scores[num] += 4 - lag  # bonus 3,2,1
        return {n for n, _ in scores.most_common(K)}

    return selector


# ===================================================================
# P7 — Somma regressione alla media
# ===================================================================
def make_p7(w: int):
    def selector(estrazioni, i, _extra):
        if estrazioni == "_get_min_w_":
            return w
        # Media somma ultimi W draw
        somme = [sum(estrazioni[j]["numeri"]) for j in range(i - w, i)]
        mean_s = sum(somme) / len(somme)
        last_s = sum(estrazioni[i - 1]["numeri"])
        # Target: regress toward mean
        bias = -1 if last_s > mean_s else 1

        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        # Score = freq + bias toward direction
        scored = []
        for num in range(1, 91):
            f = freq.get(num, 0)
            direction_bonus = 0
            if bias < 0 and num < 45 or bias > 0 and num > 45:
                direction_bonus = 2
            scored.append((num, f + direction_bonus))
        scored.sort(key=lambda x: -x[1])
        return {n for n, _ in scored[:K]}

    return selector


# ===================================================================
# P8 — ML ensemble (lightweight)
# ===================================================================
def test_p8(estrazioni: list[dict]) -> Optional[dict]:
    """Gradient boosting per predire apparizione numeri."""
    try:
        from sklearn.ensemble import GradientBoostingClassifier
    except ImportError:
        print("  P8 SKIPPED — sklearn non installato")
        return None

    n = len(estrazioni)
    half = n // 2
    w = 100

    log.info("P8: Costruzione features (W=%d)...", w)

    def build_features(idx: int):
        """Feature vector per ogni numero a estrazione idx."""
        freq = Counter()
        last_seen = {}
        for j in range(max(0, idx - w), idx):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
                last_seen[num] = j

        prev_set = estrazioni[idx - 1]["numeri"] if idx > 0 else set()
        prev2 = estrazioni[idx - 2]["numeri"] if idx > 1 else set()

        rows = []
        for num in range(1, 91):
            f = freq.get(num, 0) / max(w, 1)
            rit = (idx - last_seen.get(num, 0)) / w
            dec = (num - 1) // 10
            parity = num % 2
            in_prev = 1 if num in prev_set else 0
            in_prev2 = 1 if num in prev2 else 0
            rows.append([f, rit, dec / 9.0, parity, in_prev, in_prev2, num / 90.0])
        return rows

    # Build train set (subsample for speed)
    log.info("P8: Building train set...")
    x_train = []
    y_train = []
    step = 5  # subsample
    for idx in range(w, half, step):
        features = build_features(idx)
        target_set = estrazioni[idx]["numeri"]
        for num_idx, row in enumerate(features):
            x_train.append(row)
            y_train.append(1 if (num_idx + 1) in target_set else 0)

    log.info("P8: Training GBM (%d samples)...", len(x_train))
    clf = GradientBoostingClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    clf.fit(x_train, y_train)

    # Predict on validation set
    log.info("P8: Predicting on validation set...")
    ev_val = 0.0
    mb_val = 0.0
    n_val = 0

    for idx in range(half, n, 3):  # subsample for speed
        features = build_features(idx)
        probs = clf.predict_proba(features)
        # Get probability of class 1
        scores = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]

        # Top 6 by predicted probability
        top6_indices = sorted(range(90), key=lambda x: -scores[x])[:K]
        pick = {i + 1 for i in top6_indices}

        drawn = estrazioni[idx]["numeri"]
        extra = estrazioni[idx]["extra"]
        e = _ev(pick, drawn, extra)
        mb = _match_base(pick, drawn)
        ev_val += e
        mb_val += mb
        n_val += 1

    avg_ev = ev_val / n_val if n_val else 0
    avg_mb = mb_val / n_val if n_val else 0
    ratio = avg_ev / EV_BASELINE
    supera = "SI" if ratio >= BREAKEVEN_ST else "no"

    return {
        "label": "P8 ML-GBM",
        "config": f"W={w}",
        "ev_disc": 0,
        "ev_val": avg_ev,
        "mb_disc": 0,
        "mb_val": avg_mb,
        "ratio_d": 0,
        "ratio_v": ratio,
        "n_disc": 0,
        "n_val": n_val,
        "supera_be": supera,
    }


# ===================================================================
# MAIN
# ===================================================================
def main():
    print("=" * 80)
    print("10eLOTTO PREDICTION LAB — 8 TEST PREDITTIVI")
    print("=" * 80)

    log.info("Caricamento dati...")
    estrazioni = carica()
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")
    print(f"Discovery: primi {n // 2}, Validazione: ultimi {n - n // 2}")
    print(f"Baseline: match={6 * 20 / 90:.3f}, EV=EUR {EV_BASELINE:.4f}")
    print(f"Breakeven ST: {BREAKEVEN_ST:.3f}x (EUR {EV_BASELINE * BREAKEVEN_ST:.4f})")

    all_results = []

    # P1 — freq+rit+dec
    print("\n--- P1: freq+rit+dec ---")
    for w in [50, 100, 200, 288, 500]:
        log.info("P1 W=%d...", w)
        r = run_test(estrazioni, make_p1(w), "P1 freq+rit+dec", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P2 — Vicinanza
    print("\n--- P2: vicinanza pura ---")
    for w in [50, 100, 200, 288]:
        for d in [5, 10, 15, 20, 30]:
            log.info("P2 W=%d D=%d...", w, d)
            r = run_test(estrazioni, make_p2(w, d), "P2 vicinanza", f"W={w} D={d}")
            print_result(r)
            all_results.append(r)

    # P3 — Top freq
    print("\n--- P3: top 6 frequenti ---")
    for w in [5, 10, 20, 50, 100, 200, 288, 576]:
        log.info("P3 W=%d...", w)
        r = run_test(estrazioni, make_p3(w), "P3 top-freq", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P4 — Freddi
    print("\n--- P4: numeri freddi ---")
    for w in [50, 100, 200, 288]:
        log.info("P4 W=%d...", w)
        r = run_test(estrazioni, make_p4(w), "P4 freddi", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P5 — Mix
    print("\n--- P5: mix caldi+freddi ---")
    for w in [50, 100, 200, 288]:
        log.info("P5 W=%d...", w)
        r = run_test(estrazioni, make_p5(w), "P5 mix", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P6 — Overlap
    print("\n--- P6: overlap scoring ---")
    for w in [10, 20, 50, 100]:
        log.info("P6 W=%d...", w)
        r = run_test(estrazioni, make_p6(w), "P6 overlap", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P7 — Somma
    print("\n--- P7: somma regressione ---")
    for w in [50, 100, 200, 288]:
        log.info("P7 W=%d...", w)
        r = run_test(estrazioni, make_p7(w), "P7 somma-reg", f"W={w}")
        print_result(r)
        all_results.append(r)

    # P8 — ML
    print("\n--- P8: ML ensemble ---")
    r8 = test_p8(estrazioni)
    if r8:
        print_result(r8)
        all_results.append(r8)

    # === CLASSIFICA FINALE ===
    print("\n" + "=" * 80)
    print("CLASSIFICA FINALE (ordinata per EV validazione)")
    print("=" * 80)
    all_results.sort(key=lambda x: -x["ratio_v"])

    print(f"\n  {'#':>3}  {'Metodo':<22} {'Config':<14} {'EV val':>8} {'Ratio':>8} {'BE_ST':>6}")
    print("  " + "-" * 68)

    for i, r in enumerate(all_results[:20]):
        print(
            f"  {i + 1:>3}  {r['label']:<22} {r['config']:<14} "
            f"{r['ev_val']:>8.4f} {r['ratio_v']:>7.4f}x {r['supera_be']:>6}"
        )

    # Best
    best = all_results[0]
    print(f"\n  MIGLIOR SEGNALE: {best['label']} {best['config']}")
    print(f"  EV validazione: EUR {best['ev_val']:.4f}")
    print(f"  Ratio: {best['ratio_v']:.4f}x")
    be_st = "*** SUPERATO ***" if best["ratio_v"] >= BREAKEVEN_ST else "NON superato"
    be_base = "*** SUPERATO ***" if best["ratio_v"] >= 1.11 else "NON superato"
    print(f"  Breakeven ST (1.067x): {be_st}")
    print(f"  Breakeven base (1.11x): {be_base}")


if __name__ == "__main__":
    main()
