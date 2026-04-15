from __future__ import annotations

"""10eLotto Strategy Lab — Ricerca strategia ottimale.

S1: freq_rit_fib adattato (vincitore Lotto)
S2: Ciclometria su sestine (15 coppie interne)
S3: Extra stream analysis (pattern nei 15 Extra come gioco separato)
S4: Conditional staking (quando giocare di piu)
S5: Wheeling/copertura con piu schedine
S6: Ensemble (fusione top metodi + money management)
"""

import logging
import random
from collections import Counter

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
# Special Time
ST_BASE = {3: 2.00, 4: 11.00, 5: 110.00, 6: 1300.00}
ST_EXTRA = {1: 1.00, 2: 1.00, 3: 7.00, 4: 21.00, 5: 210.00, 6: 3000.00}


def _ev(pick: set, drawn: set, extra: set) -> float:
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)


def _ev_st(pick: set, drawn: set, extra: set) -> float:
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
                "numeri_list": r.numeri,
                "extra_list": r.numeri_extra,
                "ora": r.ora,
            }
            for r in rows
        ]
    finally:
        session.close()


def run_test(estrazioni, selector_fn, label, config, min_w):
    """Framework standard: discovery/validation con EV reale."""
    n = len(estrazioni)
    half = n // 2
    ev_d, ev_v, mb_d, mb_v = 0.0, 0.0, 0.0, 0.0
    nd, nv = 0, 0

    for i in range(min_w, n):
        pick = selector_fn(estrazioni, i)
        if pick is None or len(pick) < K:
            continue
        pick = set(list(pick)[:K])
        drawn = estrazioni[i]["numeri"]
        extra = estrazioni[i]["extra"]
        e = _ev(pick, drawn, extra)
        mb = len(pick & drawn)
        if i < half:
            ev_d += e
            mb_d += mb
            nd += 1
        else:
            ev_v += e
            mb_v += mb
            nv += 1

    avg_d = ev_d / nd if nd else 0
    avg_v = ev_v / nv if nv else 0
    rd = avg_d / EV_BASELINE
    rv = avg_v / EV_BASELINE
    return {
        "label": label,
        "config": config,
        "ev_d": avg_d,
        "ev_v": avg_v,
        "mb_d": mb_d / nd if nd else 0,
        "mb_v": mb_v / nv if nv else 0,
        "rd": rd,
        "rv": rv,
        "nd": nd,
        "nv": nv,
    }


def pr(r):
    print(
        f"  {r['label']:<24} {r['config']:<16} "
        f"mb={r['mb_v']:.3f} EV={r['ev_v']:.4f} "
        f"R={r['rv']:.4f}x  n={r['nv']}"
    )


# ===================================================================
# S1 — freq_rit_fib (Fibonacci ratio selection)
# ===================================================================


def make_s1(w: int):
    """Seleziona numeri con rapporto freq/ritardo vicino a Fibonacci."""
    fib_ratios = [1.0, 1.618, 2.618, 0.618, 0.382]

    def sel(estrazioni, i):
        freq = Counter()
        last_seen = {}
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
                last_seen[num] = j

        scored = []
        for num in range(1, 91):
            f = freq.get(num, 0)
            rit = i - last_seen.get(num, 0)
            if f == 0 or rit == 0:
                continue
            ratio = f / rit
            # Score: quanto vicino a un rapporto Fibonacci?
            min_dist = min(abs(ratio - fr) for fr in fib_ratios)
            # Preferisci alti freq con bassa distanza da Fibonacci
            score = f * (1.0 / (1.0 + min_dist * 10))
            scored.append((num, score))

        scored.sort(key=lambda x: -x[1])
        return {n for n, _ in scored[:K]}

    return sel


# ===================================================================
# S2 — Ciclometria su sestine (coppie interne)
# ===================================================================


def make_s2(w: int):
    """Seleziona 6 numeri le cui 15 coppie interne hanno proprieta
    ciclometriche calde."""

    def sel(estrazioni, i):
        # Conta frequenza di ogni COPPIA nelle ultime W estrazioni
        pair_freq = Counter()
        num_freq = Counter()
        for j in range(i - w, i):
            nums = sorted(estrazioni[j]["numeri"])
            for num in nums:
                num_freq[num] += 1
            # Coppie con proprieta ciclometriche: stessa decina o diametrali
            for a_idx in range(len(nums)):
                for b_idx in range(a_idx + 1, len(nums)):
                    a, b = nums[a_idx], nums[b_idx]
                    # Solo coppie "interessanti": stessa decina, diametrali,
                    # o vicini
                    decade_a = (a - 1) // 10
                    decade_b = (b - 1) // 10
                    diametrale = a + b == 91
                    vicini = abs(a - b) <= 10
                    stessa_dec = decade_a == decade_b

                    if stessa_dec or diametrale or vicini:
                        pair_freq[(a, b)] += 1

        # Seleziona le coppie piu frequenti, poi estrai i numeri unici
        top_pairs = pair_freq.most_common(20)
        pick = set()
        for (a, b), _ in top_pairs:
            pick.add(a)
            pick.add(b)
            if len(pick) >= K:
                break

        # Pad con numeri frequenti
        if len(pick) < K:
            for num, _ in num_freq.most_common():
                pick.add(num)
                if len(pick) >= K:
                    break

        return set(list(pick)[:K])

    return sel


# ===================================================================
# S3 — Extra stream: predici i numeri Extra, non i base
# ===================================================================


def make_s3(w: int):
    """Seleziona numeri che sono frequenti nell'EXTRA (non nel base).
    Logica: i numeri Extra sono estratti dai 70 non-base. Se un numero
    appare spesso nell'Extra di estrazioni recenti, e perche esce poco
    nella base (lasciandolo nel pool dei 70)."""

    def sel(estrazioni, i):
        extra_freq = Counter()
        base_freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["extra"]:
                extra_freq[num] += 1
            for num in estrazioni[j]["numeri"]:
                base_freq[num] += 1

        # Score: alta freq Extra + bassa freq base = numero nel pool
        scored = []
        for num in range(1, 91):
            ef = extra_freq.get(num, 0)
            bf = base_freq.get(num, 0)
            # Un numero frequente in Extra e raro in base
            score = ef - bf * 0.5
            scored.append((num, score))

        scored.sort(key=lambda x: -x[1])
        return {n for n, _ in scored[:K]}

    return sel


# ===================================================================
# S4 — Dual target: 3 numeri per base + 3 numeri per Extra
# ===================================================================


def make_s4(w: int):
    """Strategia duale: 3 numeri caldi nel base + 3 numeri caldi
    nell'Extra. Massimizza P(match) su entrambi i fronti."""

    def sel(estrazioni, i):
        base_freq = Counter()
        extra_freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                base_freq[num] += 1
            for num in estrazioni[j]["extra"]:
                extra_freq[num] += 1

        # Top 3 per base
        hot_base = [n for n, _ in base_freq.most_common(6)]
        # Top 3 per extra (diversi da hot_base)
        hot_extra = [n for n, _ in extra_freq.most_common(20) if n not in hot_base][:3]

        pick = set(hot_base[:3] + hot_extra[:3])

        # Pad if needed
        if len(pick) < K:
            for n, _ in base_freq.most_common():
                pick.add(n)
                if len(pick) >= K:
                    break
        return set(list(pick)[:K])

    return sel


# ===================================================================
# S5 — Anti-cluster: numeri piu sparsi possibile
# ===================================================================


def make_s5(w: int):
    """Seleziona 6 numeri equidistanti tra i piu frequenti.
    Massimizza la copertura dello spazio 1-90."""

    def sel(estrazioni, i):
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        # Top 30 frequenti
        candidates = [n for n, _ in freq.most_common(30)]

        # Greedy: parti dal piu frequente, poi aggiungi il piu lontano
        pick = [candidates[0]]
        remaining = candidates[1:]

        while len(pick) < K and remaining:
            # Trova il candidato piu lontano da tutti i gia selezionati
            best = max(remaining, key=lambda x: min(abs(x - p) for p in pick))
            pick.append(best)
            remaining.remove(best)

        return set(pick)

    return sel


# ===================================================================
# S6 — Wheeling: 3 schedine da 6 sulla stessa estrazione
# ===================================================================


def test_s6_wheeling(estrazioni: list[dict]):
    """Simula 3 schedine da 6 numeri con overlap parziale."""
    n = len(estrazioni)
    half = n // 2
    w = 100

    log.info("S6 wheeling (3 schedine x EUR 2 = EUR 6)...")

    ev_single_v = 0.0
    ev_wheel_v = 0.0
    nv = 0

    for i in range(w, n):
        if i < half:
            continue

        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        # Top 12 numeri frequenti, divisi in 3 sestine con overlap
        top12 = [n for n, _ in freq.most_common(12)]
        s1 = set(top12[0:6])  # primi 6
        s2 = set(top12[3:9])  # overlap di 3
        s3 = set(top12[6:12])  # overlap di 3

        drawn = estrazioni[i]["numeri"]
        extra = estrazioni[i]["extra"]

        # EV singola (solo s1)
        ev_single_v += _ev(s1, drawn, extra)

        # EV wheeling (somma delle 3)
        ev_wheel_v += _ev(s1, drawn, extra)
        ev_wheel_v += _ev(s2, drawn, extra)
        ev_wheel_v += _ev(s3, drawn, extra)

        nv += 1

    avg_single = ev_single_v / nv if nv else 0
    avg_wheel = ev_wheel_v / nv if nv else 0

    print("\n  S6 Wheeling (3 schedine, EUR 6/estr):")
    print(f"    Singola 6+Extra (EUR 2): EV={avg_single:.4f}, R={avg_single / EV_BASELINE:.4f}x")
    print(f"    Wheel 3x6+Extra (EUR 6): EV={avg_wheel:.4f}, EV/EUR={avg_wheel / 6:.4f}")
    print(f"    Singola EV/EUR: {avg_single / 2:.4f}")
    print(f"    Wheel EV/EUR:   {avg_wheel / 6:.4f}")
    print(
        f"    Wheeling {'MIGLIORE' if avg_wheel / 6 > avg_single / 2 else 'PEGGIORE'} del singolo"
    )


# ===================================================================
# S7 — Conditional staking (money management adattivo)
# ===================================================================


def test_s7_conditional(estrazioni: list[dict]):
    """Raddoppia la posta dopo N estrazioni senza vincita base (>=3/6)."""
    n = len(estrazioni)
    half = n // 2
    w = 100

    log.info("S7 conditional staking...")

    print("\n  S7 Conditional Staking:")
    print("  Strategia: posta EUR 2 base. Dopo N giocate senza 3+/6,")
    print("  raddoppia la posta per le prossime 5 giocate.")
    print()

    for trigger_n in [10, 20, 30, 50]:
        bankroll = 1000.0
        max_bankroll = bankroll
        posta_base = 2.0
        streak_no_win = 0
        boosted = 0
        n_giocate = 0
        n_boosted = 0

        for i in range(w, n):
            if i < half:
                continue

            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            pick = {n for n, _ in freq.most_common(K)}

            drawn = estrazioni[i]["numeri"]
            extra = estrazioni[i]["extra"]

            # Determina posta
            if boosted > 0:
                posta = posta_base * 2
                boosted -= 1
                n_boosted += 1
            else:
                posta = posta_base

            mb = len(pick & drawn)
            rem = pick - drawn
            me = len(rem & extra)

            # Vincita proporzionale alla posta (i premi sono per EUR 1)
            vincita = (PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)) * (posta / posta_base)

            bankroll -= posta
            bankroll += vincita
            n_giocate += 1

            if bankroll > max_bankroll:
                max_bankroll = bankroll

            # Tracking streak
            if mb >= 3:
                streak_no_win = 0
            else:
                streak_no_win += 1

            if streak_no_win >= trigger_n and boosted == 0:
                boosted = 5
                streak_no_win = 0

        pnl = bankroll - 1000.0
        costo_tot = n_giocate * posta_base + n_boosted * posta_base
        roi = pnl / costo_tot * 100 if costo_tot > 0 else 0

        print(
            f"    Trigger={trigger_n:>3}: P&L={pnl:+8.2f}  "
            f"ROI={roi:+.2f}%  boosted={n_boosted}/{n_giocate}"
        )


# ===================================================================
# S8 — Ensemble: fusione top metodi con voting
# ===================================================================


def make_s8(w: int):
    """Ensemble: 4 metodi votano, i 6 numeri piu votati vincono."""

    def sel(estrazioni, i):
        votes = Counter()

        # Metodo 1: top freq
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        for n, _ in freq.most_common(6):
            votes[n] += 3

        # Metodo 2: freq_rit_fib
        fib_ratios = [1.0, 1.618, 0.618]
        last_seen = {}
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                last_seen[num] = j
        for num in range(1, 91):
            f = freq.get(num, 0)
            rit = i - last_seen.get(num, 0)
            if f > 0 and rit > 0:
                ratio = f / rit
                min_dist = min(abs(ratio - fr) for fr in fib_ratios)
                if min_dist < 0.1:
                    votes[num] += 2

        # Metodo 3: vicinanza D=5 dal seed
        seed = freq.most_common(1)[0][0]
        for num in range(max(1, seed - 5), min(91, seed + 6)):
            if num != seed and freq.get(num, 0) > 0:
                votes[num] += 1
        votes[seed] += 2

        # Metodo 4: extra-frequent
        extra_freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["extra"]:
                extra_freq[num] += 1
        for n, _ in extra_freq.most_common(6):
            votes[n] += 1

        return {n for n, _ in votes.most_common(K)}

    return sel


# ===================================================================
# PERMUTATION TEST
# ===================================================================


def permutation_test(estrazioni, selector_fn, min_w, label, n_perm=5000):
    """Permutation test ottimizzato."""
    n = len(estrazioni)
    half = n // 2
    start = max(half, min_w)
    nn = n - start

    # Precalcola
    picks = []
    draws = []
    obs_total = 0.0
    for i in range(start, n):
        pick = selector_fn(estrazioni, i)
        if pick is None or len(pick) < K:
            pick = set(range(1, K + 1))
        pick = set(list(pick)[:K])
        drawn = estrazioni[i]["numeri"]
        extra = estrazioni[i]["extra"]
        picks.append(pick)
        draws.append((drawn, extra))
        obs_total += _ev(pick, drawn, extra)
    obs_mean = obs_total / nn

    count_ge = 0
    random.seed(42)
    for _ in range(n_perm):
        offset = random.randint(1, nn - 1)  # noqa: S311
        perm_total = sum(
            _ev(picks[idx], draws[(idx + offset) % nn][0], draws[(idx + offset) % nn][1])
            for idx in range(nn)
        )
        if perm_total / nn >= obs_mean:
            count_ge += 1

    p_value = count_ge / n_perm
    ratio = obs_mean / EV_BASELINE
    return {
        "label": label,
        "ev": obs_mean,
        "ratio": ratio,
        "p_value": p_value,
        "n": nn,
    }


# ===================================================================
# SIMULAZIONE ANNUALE COMPLETA
# ===================================================================


def simula_anno(estrazioni, selector_fn, min_w, label, solo_st=True):
    """Simula 1 anno di gioco con la strategia data."""
    n = len(estrazioni)
    half = n // 2
    start = max(half, min_w)

    from datetime import time

    bankroll = 200.0
    max_br = bankroll
    min_br = bankroll
    max_dd = 0.0
    n_giocate = 0
    n_vincite_base = 0
    random.seed(42)

    for i in range(start, n):
        ora = estrazioni[i]["ora"]

        if solo_st and not (time(16, 5) <= ora <= time(18, 0)):
            continue

        pick = selector_fn(estrazioni, i)
        if pick is None or len(pick) < K:
            continue
        pick = set(list(pick)[:K])

        drawn = estrazioni[i]["numeri"]
        extra = estrazioni[i]["extra"]

        is_special = random.random() < 0.25  # noqa: S311
        vincita = _ev_st(pick, drawn, extra) if is_special else _ev(pick, drawn, extra)

        bankroll -= COSTO
        bankroll += vincita
        n_giocate += 1

        mb = len(pick & drawn)
        if mb >= 3:
            n_vincite_base += 1

        if bankroll > max_br:
            max_br = bankroll
        if bankroll < min_br:
            min_br = bankroll
        dd = max_br - bankroll
        if dd > max_dd:
            max_dd = dd

    pnl = bankroll - 200.0
    roi = pnl / (n_giocate * COSTO) * 100 if n_giocate > 0 else 0

    return {
        "label": label,
        "bankroll": bankroll,
        "pnl": pnl,
        "roi": roi,
        "max_dd": max_dd,
        "min_br": min_br,
        "n_giocate": n_giocate,
        "n_vincite": n_vincite_base,
    }


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 75)
    print("10eLOTTO STRATEGY LAB — RICERCA STRATEGIA OTTIMALE")
    print("=" * 75)

    log.info("Caricamento dati...")
    estrazioni = carica()
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")
    print(f"Baseline: EV={EV_BASELINE:.4f}, breakeven ST=1.067x")

    all_results = []

    # --- S1: freq_rit_fib ---
    print("\n--- S1: freq_rit_fib (Fibonacci ratio) ---")
    for w in [50, 75, 100, 150, 200, 288]:
        log.info("S1 W=%d...", w)
        r = run_test(estrazioni, make_s1(w), "S1 freq_rit_fib", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- S2: Ciclometria coppie ---
    print("\n--- S2: Ciclometria coppie interne ---")
    for w in [50, 100, 200, 288]:
        log.info("S2 W=%d...", w)
        r = run_test(estrazioni, make_s2(w), "S2 ciclometria", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- S3: Extra stream ---
    print("\n--- S3: Extra stream (numeri caldi nell'Extra) ---")
    for w in [20, 50, 100, 200]:
        log.info("S3 W=%d...", w)
        r = run_test(estrazioni, make_s3(w), "S3 extra-stream", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- S4: Dual target ---
    print("\n--- S4: Dual target (3 hot base + 3 hot Extra) ---")
    for w in [50, 100, 200, 288]:
        log.info("S4 W=%d...", w)
        r = run_test(estrazioni, make_s4(w), "S4 dual-target", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- S5: Anti-cluster ---
    print("\n--- S5: Anti-cluster (numeri sparsi tra i frequenti) ---")
    for w in [50, 100, 200, 288]:
        log.info("S5 W=%d...", w)
        r = run_test(estrazioni, make_s5(w), "S5 anti-cluster", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- S8: Ensemble ---
    print("\n--- S8: Ensemble (voting 4 metodi) ---")
    for w in [50, 100, 200, 288]:
        log.info("S8 W=%d...", w)
        r = run_test(estrazioni, make_s8(w), "S8 ensemble", f"W={w}", w)
        pr(r)
        all_results.append(r)

    # --- Classifica ---
    all_results.sort(key=lambda x: -x["rv"])

    print("\n" + "=" * 75)
    print("CLASSIFICA (top 15 per EV validazione)")
    print("=" * 75)
    print(f"  {'#':>3}  {'Metodo':<24} {'Config':<16} {'EV val':>8} {'Ratio':>8}")
    print("  " + "-" * 62)
    for i, r in enumerate(all_results[:15]):
        marker = " *" if r["rv"] >= 1.067 else ""
        print(
            f"  {i + 1:>3}  {r['label']:<24} {r['config']:<16} "
            f"{r['ev_v']:>8.4f} {r['rv']:>7.4f}x{marker}"
        )

    # --- S6: Wheeling ---
    test_s6_wheeling(estrazioni)

    # --- S7: Conditional staking ---
    test_s7_conditional(estrazioni)

    # --- Permutation test top 3 ---
    top3 = all_results[:3]
    print("\n" + "=" * 75)
    print("PERMUTATION TEST (5000 shuffle) — TOP 3")
    print("=" * 75)

    for r in top3:
        label = f"{r['label']} {r['config']}"
        min_w = int(r["config"].split("=")[1]) if "=" in r["config"] else 100
        if "S1" in r["label"]:
            fn = make_s1(min_w)
        elif "S2" in r["label"]:
            fn = make_s2(min_w)
        elif "S3" in r["label"]:
            fn = make_s3(min_w)
        elif "S4" in r["label"]:
            fn = make_s4(min_w)
        elif "S5" in r["label"]:
            fn = make_s5(min_w)
        elif "S8" in r["label"]:
            fn = make_s8(min_w)
        else:
            continue

        log.info("Permutation: %s...", label)
        pt = permutation_test(estrazioni, fn, min_w, label)
        print(f"  {pt['label']:<40} EV={pt['ev']:.4f}  R={pt['ratio']:.4f}x  p={pt['p_value']:.4f}")

    # --- Simulazione annuale best ---
    best = all_results[0]
    min_w_best = int(best["config"].split("=")[1]) if "=" in best["config"] else 100
    if "S1" in best["label"]:
        fn_best = make_s1(min_w_best)
    elif "S8" in best["label"]:
        fn_best = make_s8(min_w_best)
    else:
        fn_best = make_s1(min_w_best)

    print("\n" + "=" * 75)
    print("SIMULAZIONE SPECIAL TIME (fascia 16:05-18:00)")
    print("=" * 75)

    sim = simula_anno(estrazioni, fn_best, min_w_best, best["label"])
    print(f"  Strategia: {sim['label']}")
    print(f"  Giocate: {sim['n_giocate']} (solo fascia ST)")
    print(f"  Bankroll: EUR 200 -> EUR {sim['bankroll']:.2f}")
    print(f"  P&L: EUR {sim['pnl']:+.2f}")
    print(f"  ROI: {sim['roi']:+.2f}%")
    print(f"  Max drawdown: EUR {sim['max_dd']:.2f}")

    # --- Verdetto finale ---
    print("\n" + "=" * 75)
    print("VERDETTO FINALE")
    print("=" * 75)
    best_ratio = all_results[0]["rv"]
    print(f"  Miglior ratio validazione: {best_ratio:.4f}x")
    print("  Breakeven Special Time:    1.067x")
    print("  Breakeven normale:         1.11x")

    if best_ratio >= 1.11:
        print("  >>> EDGE TROVATO (supera breakeven normale) <<<")
    elif best_ratio >= 1.067:
        print("  >>> EDGE Special Time (profittevole solo in fascia ST) <<<")
    elif best_ratio >= 1.0:
        print("  Segnale positivo ma sotto breakeven.")
    else:
        print("  Nessun edge. RNG perfetto.")


if __name__ == "__main__":
    main()
