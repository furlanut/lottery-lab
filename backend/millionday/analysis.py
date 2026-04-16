from __future__ import annotations

"""MillionDay — Analisi completa su 496 estrazioni.

RNG certification + signal tests + confronto con VinciCasa.
5 numeri su 55, Extra 5 dai 50 rimanenti.
"""

import json
import logging
import random
from collections import Counter
from math import comb, sqrt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

N_TOTAL = 55
N_DRAWN = 5
N_EXTRA = 5
N_REMAINING = 50
K = 5
COSTO_BASE = 1.0
COSTO_EXTRA = 1.0
COSTO_TOTALE = 2.0

PREMI_BASE = {2: 2.0, 3: 50.0, 4: 1000.0, 5: 1000000.0}
PREMI_EXTRA = {2: 4.0, 3: 100.0, 4: 1000.0, 5: 100000.0}


def _ev_giocata(pick: set, drawn: set, extra: set) -> float:
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)


def carica():
    with open("/tmp/millionday_archive.json") as f:  # noqa: S108
        raw = json.load(f)
    return [
        {
            "numeri": set(r["numeri"]),
            "extra": set(r.get("extra", [])),
            "numeri_list": r["numeri"],
            "extra_list": r.get("extra", []),
            "data": r["data"],
            "ora": r["ora"],
        }
        for r in raw
    ]


def fase1_rng(estrazioni):
    n = len(estrazioni)
    print("\n" + "=" * 60)
    print("FASE 1 — CERTIFICAZIONE RNG")
    print("=" * 60)

    # Chi-quadro
    freq = Counter()
    for e in estrazioni:
        for num in e["numeri"]:
            freq[num] += 1
    expected = n * N_DRAWN / N_TOTAL
    chi2 = sum((freq.get(i, 0) - expected) ** 2 / expected for i in range(1, N_TOTAL + 1))
    df = N_TOTAL - 1
    z = (chi2 - df) / sqrt(2 * df)
    ok = abs(z) < 3.0
    print(f"\n  Chi-quadro: {'PASS' if ok else 'FAIL'}")
    print(f"    chi2={chi2:.1f} df={df} z={z:.2f}")
    print(
        f"    atteso={expected:.1f} min={min(freq.get(i, 0) for i in range(1, N_TOTAL + 1))}"
        f" max={max(freq.get(i, 0) for i in range(1, N_TOTAL + 1))}"
    )

    # Overlap
    overlaps = [len(estrazioni[i - 1]["numeri"] & estrazioni[i]["numeri"]) for i in range(1, n)]
    mean_ov = sum(overlaps) / len(overlaps)
    exp_ov = N_DRAWN * N_DRAWN / N_TOTAL  # 5*5/55 = 0.4545
    se_ov = sqrt(sum((x - mean_ov) ** 2 for x in overlaps) / len(overlaps)) / sqrt(len(overlaps))
    z_ov = (mean_ov - exp_ov) / se_ov if se_ov > 0 else 0
    ok_ov = abs(z_ov) < 3.0
    print(f"\n  Overlap consecutivo: {'PASS' if ok_ov else 'FAIL'}")
    print(f"    media={mean_ov:.4f} atteso={exp_ov:.4f} z={z_ov:.2f}")

    # Autocorrelazione somme
    somme = [sum(e["numeri"]) for e in estrazioni]
    mean_s = sum(somme) / n
    var_s = sum((s - mean_s) ** 2 for s in somme) / n
    max_ac = 0.0
    for lag in [1, 2, 5, 10]:
        if lag >= n:
            continue
        cov = sum((somme[i] - mean_s) * (somme[i + lag] - mean_s) for i in range(n - lag)) / (
            n - lag
        )
        ac = cov / var_s if var_s > 0 else 0
        if abs(ac) > max_ac:
            max_ac = abs(ac)
    ok_ac = max_ac < 0.1
    print(f"\n  Autocorrelazione: {'PASS' if ok_ac else 'FAIL'}")
    print(f"    max |r|={max_ac:.4f}")


def fase2_segnali(estrazioni):
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 60)
    print("FASE 2 — TEST SEGNALI (come VinciCasa)")
    print("=" * 60)

    # EV baseline analitico
    c55 = comb(55, 5)
    c50 = comb(50, 5)
    ev_base = sum(
        comb(K, m) * comb(N_TOTAL - K, N_DRAWN - m) / c55 * PREMI_BASE.get(m, 0)
        for m in range(K + 1)
    )
    ev_extra = 0.0
    for mb in range(K + 1):
        pb = comb(K, mb) * comb(N_TOTAL - K, N_DRAWN - mb) / c55
        rem = K - mb
        for me in range(rem + 1):
            if (N_REMAINING - rem) < (N_EXTRA - me):
                continue
            pe = comb(rem, me) * comb(N_REMAINING - rem, N_EXTRA - me) / c50
            ev_extra += pb * pe * PREMI_EXTRA.get(me, 0)
    ev_baseline = ev_base + ev_extra
    print(f"\n  EV baseline: {ev_baseline:.4f} / EUR {COSTO_TOTALE}")

    print(f"\n  {'Metodo':<20} {'W':>4} {'EV disc':>9} {'EV val':>9} {'Ratio D':>8} {'Ratio V':>8}")
    print("  " + "-" * 60)

    best = {"name": "", "ratio": 0.0}

    # Test A: Top 5 frequenti (il segnale VinciCasa)
    for w in [3, 5, 10, 20, 50]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            top5 = {num for num, _ in freq.most_common(K)}
            ev = _ev_giocata(top5, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd = avg_d / ev_baseline
        rv = avg_v / ev_baseline
        print(f"  {'top5_freq':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} {rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"top5_freq W={w}", "ratio": rv, "ev": avg_v}

    # Test B: Cold numbers
    for w in [10, 20, 50]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            all_nums = sorted(range(1, N_TOTAL + 1), key=lambda x: freq.get(x, 0))
            cold5 = set(all_nums[:K])
            ev = _ev_giocata(cold5, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd = avg_d / ev_baseline
        rv = avg_v / ev_baseline
        print(f"  {'cold':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} {rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"cold W={w}", "ratio": rv, "ev": avg_v}

    # Test C: Hot Extra
    for w in [5, 10, 20]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j].get("extra", set()):
                    freq[num] += 1
            if not freq:
                continue
            top5 = {num for num, _ in freq.most_common(K)}
            ev = _ev_giocata(top5, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd = avg_d / ev_baseline
        rv = avg_v / ev_baseline
        print(f"  {'hot_extra':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} {rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"hot_extra W={w}", "ratio": rv, "ev": avg_v}

    # Test D: Vicinanza
    for w in [10, 20, 50]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            seed = freq.most_common(1)[0][0]
            nearby = sorted(
                [
                    (num, freq.get(num, 0))
                    for num in range(1, N_TOTAL + 1)
                    if abs(num - seed) <= 5 and num != seed and freq.get(num, 0) > 0
                ],
                key=lambda x: -x[1],
            )
            pick = {seed}
            for num, _ in nearby:
                pick.add(num)
                if len(pick) >= K:
                    break
            if len(pick) < K:
                for num, _ in freq.most_common():
                    pick.add(num)
                    if len(pick) >= K:
                        break
            pick = set(list(pick)[:K])
            ev = _ev_giocata(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd = avg_d / ev_baseline
        rv = avg_v / ev_baseline
        print(f"  {'vicinanza D=5':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} {rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"vicinanza W={w}", "ratio": rv, "ev": avg_v}

    return best


def fase3_permutation(estrazioni, best):
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 60)
    print(f"FASE 3 — PERMUTATION TEST: {best['name']}")
    print("=" * 60)

    # Parse best config
    name = best["name"]
    obs_ev = best["ev"]

    n_perm = 5000
    random.seed(42)

    # Precalculate picks and draws for validation set
    w = int(name.split("W=")[1]) if "W=" in name else 5
    start = max(w, half)
    nn = n - start

    picks = []
    draws = []
    for i in range(start, n):
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        top5 = {num for num, _ in freq.most_common(K)}
        picks.append(top5)
        draws.append((estrazioni[i]["numeri"], estrazioni[i]["extra"]))

    count_ge = 0
    for _ in range(n_perm):
        offset = random.randint(1, nn - 1)  # noqa: S311
        perm_total = sum(
            _ev_giocata(picks[idx], draws[(idx + offset) % nn][0], draws[(idx + offset) % nn][1])
            for idx in range(nn)
        )
        if perm_total / nn >= obs_ev:
            count_ge += 1

    p_value = count_ge / n_perm
    print(f"\n  Observed EV: {obs_ev:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Significativo (p<0.05): {'SI' if p_value < 0.05 else 'NO'}")
    return p_value


def main():
    print("=" * 60)
    print("MILLIONDAY — ANALISI COMPLETA")
    print("=" * 60)

    estrazioni = carica()
    n = len(estrazioni)
    n_extra = sum(1 for e in estrazioni if e["extra"])
    print(f"\nDataset: {n} estrazioni")
    print(f"Con Extra: {n_extra}")
    print(f"Periodo: {estrazioni[0]['data']} — {estrazioni[-1]['data']}")

    fase1_rng(estrazioni)
    best = fase2_segnali(estrazioni)

    print(f"\n  MIGLIOR SEGNALE: {best['name']} (ratio {best['ratio']:.4f}x)")

    if best["ratio"] > 1.0:
        p = fase3_permutation(estrazioni, best)
    else:
        print("\n  Nessun segnale sopra baseline. Permutation test non necessario.")
        p = 1.0

    print("\n" + "=" * 60)
    print("VERDETTO MILLIONDAY")
    print("=" * 60)
    print(f"  Dataset: {n} estrazioni")
    print("  HE base: 35.2%, HE base+Extra: 33.7%")
    print("  Breakeven: 1.51x")
    print(f"  Miglior segnale: {best['name']} ({best['ratio']:.4f}x)")
    print(f"  p-value: {p:.4f}")

    if p < 0.05 and best["ratio"] > 1.0:
        print(f"\n  *** SEGNALE SIGNIFICATIVO (p={p:.4f}) ***")
    else:
        print("\n  Nessun edge trovato. RNG confermato.")

    # Confronto
    print("\n  CONFRONTO:")
    print(f"  {'Gioco':<20} {'HE':>8} {'BE':>8} {'Segnale':>10} {'p':>8}")
    print(f"  {'-' * 55}")
    print(f"  {'Lotto ambetto':<20} {'37.6%':>8} {'1.60x':>8} {'1.18x':>10} {'CV':>8}")
    print(f"  {'VinciCasa':<20} {'37.3%':>8} {'1.60x':>8} {'1.22x':>10} {'0.01':>8}")
    print(f"  {'10eLotto 6+Extra':<20} {'9.94%':>8} {'1.11x':>8} {'0.99x':>10} {'0.05':>8}")
    ratio_str = f"{best['ratio']:.2f}x"
    p_str = f"{p:.3f}"
    print(f"  {'MillionDay b+E':<20} {'33.7%':>8} {'1.51x':>8} {ratio_str:>10} {p_str:>8}")


if __name__ == "__main__":
    main()
