from __future__ import annotations

"""10eLotto — Validazione rigorosa top 4 segnali.

Step 1: Permutation test (10K shuffle) + Bonferroni
Step 2: 5-fold CV
Step 3: Simulazione annuale Special Time
Step 4: Sanity check per fascia oraria
"""

import logging
import random
from collections import Counter
from datetime import time
from math import sqrt

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

K = 6
COSTO = 2.0
EV_BASELINE = 1.8013
PREMI_BASE = {3: 2.00, 4: 10.00, 5: 100.00, 6: 1000.00}
PREMI_EXTRA = {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00}
# Special Time prizes for K=6
ST_BASE = {3: 2.00, 4: 11.00, 5: 110.00, 6: 1300.00}
ST_EXTRA = {1: 1.00, 2: 1.00, 3: 7.00, 4: 21.00, 5: 210.00, 6: 3000.00}
BONFERRONI_THRESHOLD = 0.001  # ~0.05/60 rounded


def _ev(pick: set, drawn: set, extra: set) -> float:
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)


def _ev_st(pick: set, drawn: set, extra: set) -> float:
    """EV con premi Special Time."""
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return ST_BASE.get(mb, 0.0) + ST_EXTRA.get(me, 0.0)


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
                "ora": r.ora,
            }
            for r in rows
        ]
    finally:
        session.close()


# === Signal selectors ===


def select_vicinanza(estrazioni: list[dict], i: int, w: int, d: int) -> set:
    freq = Counter()
    for j in range(i - w, i):
        for num in estrazioni[j]["numeri"]:
            freq[num] += 1
    seed = freq.most_common(1)[0][0]
    nearby = sorted(
        [
            (num, freq.get(num, 0))
            for num in range(1, 91)
            if abs(num - seed) <= d and num != seed and freq.get(num, 0) > 0
        ],
        key=lambda x: -x[1],
    )
    pick = {seed}
    for num, _ in nearby:
        pick.add(num)
        if len(pick) >= K:
            break
    if len(pick) < K:
        for num, _ in freq.most_common(K + 10):
            pick.add(num)
            if len(pick) >= K:
                break
    return set(list(pick)[:K])


def select_topfreq(estrazioni: list[dict], i: int, w: int) -> set:
    freq = Counter()
    for j in range(i - w, i):
        for num in estrazioni[j]["numeri"]:
            freq[num] += 1
    return {n for n, _ in freq.most_common(K)}


def select_mix(estrazioni: list[dict], i: int, w: int) -> set:
    freq = Counter()
    for j in range(i - w, i):
        for num in estrazioni[j]["numeri"]:
            freq[num] += 1
    hot = [n for n, _ in freq.most_common(3)]
    all_nums = sorted(range(1, 91), key=lambda x: freq.get(x, 0))
    cold = [n for n in all_nums[:10] if n not in hot][:3]
    return set(hot + cold)


SIGNALS = [
    ("P2 vicinanza W=100 D=5", lambda e, i: select_vicinanza(e, i, 100, 5), 100),
    ("P3 top-freq W=576", lambda e, i: select_topfreq(e, i, 576), 576),
    ("P2 vicinanza W=50 D=5", lambda e, i: select_vicinanza(e, i, 50, 5), 50),
    ("P5 mix W=288", lambda e, i: select_mix(e, i, 288), 288),
]


def compute_ev_series(estrazioni: list[dict], selector_fn, start: int, end: int) -> list[float]:
    """Calcola la serie di EV per ogni estrazione."""
    evs = []
    for i in range(start, end):
        pick = selector_fn(estrazioni, i)
        e = _ev(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
        evs.append(e)
    return evs


# ===================================================================
# STEP 1 — Permutation test
# ===================================================================


def step1_permutation(estrazioni: list[dict]):
    n = len(estrazioni)
    half = n // 2
    n_perm = 10_000

    print("\n" + "=" * 70)
    print("STEP 1 — PERMUTATION TEST (10.000 shuffle, Bonferroni p < 0.001)")
    print("=" * 70)

    passed = []

    for name, selector_fn, min_w in SIGNALS:
        log.info("Permutation: %s — precalcolo picks...", name)

        start = max(half, min_w)
        nn = n - start

        # Precalcola picks e EV osservati (UNA SOLA VOLTA)
        picks = []
        draws = []
        observed_total = 0.0
        for i in range(start, n):
            pick = selector_fn(estrazioni, i)
            drawn = estrazioni[i]["numeri"]
            extra = estrazioni[i]["extra"]
            picks.append(pick)
            draws.append((drawn, extra))
            observed_total += _ev(pick, drawn, extra)
        observed_mean = observed_total / nn

        # Permutation: shuffle solo i target (offset circolare)
        log.info("  Precalcolo fatto. 10K permutazioni...")
        count_ge = 0
        random.seed(42)

        for p in range(n_perm):
            offset = random.randint(1, nn - 1)  # noqa: S311
            perm_total = 0.0
            for idx in range(nn):
                target = (idx + offset) % nn
                e = _ev(picks[idx], draws[target][0], draws[target][1])
                perm_total += e
            if perm_total / nn >= observed_mean:
                count_ge += 1

            if (p + 1) % 2000 == 0:
                log.info("  ... %d/%d permutazioni", p + 1, n_perm)

        p_value = count_ge / n_perm
        ratio = observed_mean / EV_BASELINE
        ok = p_value < BONFERRONI_THRESHOLD
        status = "*** PASS ***" if ok else "FAIL"

        print(
            f"\n  {name}:"
            f"\n    EV osservato: {observed_mean:.4f} (ratio {ratio:.4f}x)"
            f"\n    p-value: {p_value:.4f} (soglia {BONFERRONI_THRESHOLD})"
            f"\n    {status}"
        )

        if ok:
            passed.append((name, selector_fn, min_w, p_value, ratio))

    if not passed:
        print(
            "\n  NESSUN SEGNALE PASSA BONFERRONI."
            "\n  I risultati del prediction lab sono falsi positivi"
            " da test multipli."
        )
    else:
        print(f"\n  {len(passed)} segnale/i passano Bonferroni:")
        for name, _, _, pv, ratio in passed:
            print(f"    {name}: p={pv:.4f}, ratio={ratio:.4f}x")

    return passed


# ===================================================================
# STEP 2 — 5-fold CV
# ===================================================================


def step2_cv(estrazioni: list[dict], passed: list):
    if not passed:
        return []

    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("STEP 2 — 5-FOLD CROSS VALIDATION")
    print("=" * 70)

    cv_passed = []

    for name, selector_fn, min_w, _pv, _ in passed:
        log.info("5-fold CV: %s...", name)

        usable_n = n - min_w
        fold_size = usable_n // 5
        fold_ratios = []

        for fold in range(5):
            test_start = min_w + fold * fold_size
            test_end = min_w + (fold + 1) * fold_size
            if fold == 4:
                test_end = n  # last fold takes remainder

            evs = compute_ev_series(estrazioni, selector_fn, test_start, test_end)
            avg = sum(evs) / len(evs) if evs else 0
            ratio = avg / EV_BASELINE
            fold_ratios.append(ratio)

        mean_r = sum(fold_ratios) / len(fold_ratios)
        min_r = min(fold_ratios)
        max(fold_ratios)
        std_r = sqrt(sum((r - mean_r) ** 2 for r in fold_ratios) / len(fold_ratios))

        print(f"\n  {name}:")
        for i, r in enumerate(fold_ratios):
            marker = " <-- min" if r == min_r else ""
            print(f"    Fold {i + 1}: {r:.4f}x{marker}")
        print(f"    Media: {mean_r:.4f}x ± {std_r:.4f}")
        print(f"    Min fold: {min_r:.4f}x")

        ok = min_r >= 1.0
        status = "PASS (min fold >= 1.0x)" if ok else "FAIL (min fold < 1.0x)"
        print(f"    {status}")

        if ok:
            cv_passed.append((name, selector_fn, min_w, mean_r, min_r))

    if not cv_passed:
        print("\n  Nessun segnale passa la CV. Segnali fragili.")
    return cv_passed


# ===================================================================
# STEP 3 — Simulazione annuale Special Time
# ===================================================================


def step3_simulazione(estrazioni: list[dict], cv_passed: list):
    if not cv_passed:
        return

    print("\n" + "=" * 70)
    print("STEP 3 — SIMULAZIONE ANNUALE SPECIAL TIME")
    print("=" * 70)

    n = len(estrazioni)
    # Use second half as simulation data
    half = n // 2

    for name, selector_fn, min_w, _cv_mean, _cv_min in cv_passed:
        log.info("Simulazione: %s...", name)

        start = max(half, min_w)
        bankroll_init = 200.0
        bankroll = bankroll_init
        max_bankroll = bankroll
        min_bankroll = bankroll
        max_drawdown = 0.0
        n_giocate = 0
        n_special = 0

        # Simulate: play only during Special Time window (16:05-18:00)
        # Of 24 draws in that window, 6 are Special (random)
        random.seed(42)

        for i in range(start, n):
            ora = estrazioni[i]["ora"]
            # Only play 16:05-18:00
            if not (time(16, 5) <= ora <= time(18, 0)):
                continue

            pick = selector_fn(estrazioni, i)
            drawn = estrazioni[i]["numeri"]
            extra = estrazioni[i]["extra"]

            # 25% chance this is a Special Time draw
            is_special = random.random() < 0.25  # noqa: S311
            if is_special:
                vincita = _ev_st(pick, drawn, extra)
                n_special += 1
            else:
                vincita = _ev(pick, drawn, extra)

            bankroll -= COSTO
            bankroll += vincita
            n_giocate += 1

            if bankroll > max_bankroll:
                max_bankroll = bankroll
            if bankroll < min_bankroll:
                min_bankroll = bankroll
            dd = max_bankroll - bankroll
            if dd > max_drawdown:
                max_drawdown = dd

        pnl = bankroll - bankroll_init
        roi = pnl / (n_giocate * COSTO) * 100 if n_giocate > 0 else 0

        print(f"\n  {name}:")
        print(f"    Giocate: {n_giocate} (di cui ~{n_special} Special)")
        print(f"    Bankroll iniziale: EUR {bankroll_init:.2f}")
        print(f"    Bankroll finale:   EUR {bankroll:.2f}")
        print(f"    P&L: EUR {pnl:+.2f}")
        print(f"    ROI: {roi:+.2f}%")
        print(f"    Max drawdown: EUR {max_drawdown:.2f}")
        print(f"    Min bankroll: EUR {min_bankroll:.2f}")

        if pnl > 0:
            print("    *** PROFITTO ***")
        else:
            print("    Perdita.")


# ===================================================================
# STEP 4 — Sanity check per fascia oraria
# ===================================================================


def step4_fasce_orarie(estrazioni: list[dict], cv_passed: list):
    if not cv_passed:
        return

    n = len(estrazioni)
    half = n // 2

    print("\n" + "=" * 70)
    print("STEP 4 — RATIO PER FASCIA ORARIA")
    print("=" * 70)

    fasce = {
        "00:05-16:00": (time(0, 5), time(16, 0)),
        "16:05-18:00 (ST)": (time(16, 5), time(18, 0)),
        "18:05-23:55": (time(18, 5), time(23, 55)),
    }

    for name, selector_fn, min_w, _, _ in cv_passed:
        log.info("Fasce orarie: %s...", name)
        print(f"\n  {name}:")

        start = max(half, min_w)

        for fascia_name, (ora_min, ora_max) in fasce.items():
            ev_tot = 0.0
            count = 0
            for i in range(start, n):
                ora = estrazioni[i]["ora"]
                if ora_min <= ora <= ora_max:
                    pick = selector_fn(estrazioni, i)
                    e = _ev(
                        pick,
                        estrazioni[i]["numeri"],
                        estrazioni[i]["extra"],
                    )
                    ev_tot += e
                    count += 1

            avg_ev = ev_tot / count if count else 0
            ratio = avg_ev / EV_BASELINE
            print(f"    {fascia_name:<20}: n={count:>5}  EV={avg_ev:.4f}  ratio={ratio:.4f}x")


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 70)
    print("10eLOTTO — VALIDAZIONE RIGOROSA TOP 4 SEGNALI")
    print("=" * 70)

    log.info("Caricamento dati...")
    estrazioni = carica()
    print(f"Dataset: {len(estrazioni)} estrazioni")

    # Step 1
    passed = step1_permutation(estrazioni)

    # Step 2
    cv_passed = step2_cv(estrazioni, passed)

    # Step 3
    step3_simulazione(estrazioni, cv_passed)

    # Step 4
    step4_fasce_orarie(estrazioni, cv_passed)

    # Verdetto finale
    print("\n" + "=" * 70)
    print("VERDETTO FINALE")
    print("=" * 70)

    if cv_passed:
        print(f"\n  {len(cv_passed)} segnale/i superano TUTTI i test:")
        for name, _, _, mean_r, min_r in cv_passed:
            print(f"    {name}: CV mean={mean_r:.4f}x, min={min_r:.4f}x")
        print("\n  RACCOMANDAZIONE: procedere con test live su paper trading.")
    else:
        if passed:
            print(
                "\n  Segnali significativi (Bonferroni) ma fragili (CV)."
                "\n  NON profittevoli in modo consistente."
            )
        else:
            print(
                "\n  NESSUN segnale supera il permutation test con Bonferroni."
                "\n  I risultati del prediction lab erano falsi positivi"
                " da test multipli."
                "\n  Il 10eLotto ogni 5 minuti è un RNG perfetto."
                "\n  La configurazione 6+Extra rimane la giocata piu'"
                " efficiente"
                "\n  (HE 9.94% normale, 6.30% Special Time) ma senza edge"
                " predittivo."
            )


if __name__ == "__main__":
    main()
