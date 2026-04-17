"""MillionDay — Analisi estesa su 2607 estrazioni (millionday.cloud 2022-2026).

Ripete tutti i test dell'analisi originale + due aggiunte:
- Fase 4: sub-periodi annuali (stabilita temporale)
- Fase 5: rolling window per segnale migliore
"""

import json
import random
from collections import Counter
from math import comb, sqrt
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "archive_2022_2026.json"

N_TOTAL = 55
N_DRAWN = 5
N_EXTRA = 5
N_REMAINING = 50
K = 5
COSTO_TOTALE = 2.0

PREMI_BASE = {2: 2.0, 3: 50.0, 4: 1000.0, 5: 1000000.0}
PREMI_EXTRA = {2: 4.0, 3: 100.0, 4: 1000.0, 5: 100000.0}


def _ev_giocata(pick, drawn, extra):
    mb = len(pick & drawn)
    rem = pick - drawn
    me = len(rem & extra)
    return PREMI_BASE.get(mb, 0.0) + PREMI_EXTRA.get(me, 0.0)


def carica():
    with open(DATA_PATH) as f:
        raw = json.load(f)
    return [
        {
            "numeri": set(r["numeri"]),
            "extra": set(r.get("extra", [])),
            "data": r["data"],
            "ora": r["ora"],
        }
        for r in raw
    ]


def ev_baseline():
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
    return ev_base + ev_extra


def fase1_rng(estrazioni):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("FASE 1 — CERTIFICAZIONE RNG (dataset esteso)")
    print("=" * 70)

    freq = Counter()
    for e in estrazioni:
        for num in e["numeri"]:
            freq[num] += 1
    expected = n * N_DRAWN / N_TOTAL
    chi2 = sum((freq.get(i, 0) - expected) ** 2 / expected for i in range(1, N_TOTAL + 1))
    df = N_TOTAL - 1
    z = (chi2 - df) / sqrt(2 * df)
    print(f"\n  Chi-quadro: {'PASS' if abs(z) < 3 else 'FAIL'}")
    print(f"    chi2={chi2:.1f} df={df} z={z:.2f}")
    print(
        f"    atteso={expected:.1f} "
        f"min={min(freq.get(i, 0) for i in range(1, N_TOTAL + 1))} "
        f"max={max(freq.get(i, 0) for i in range(1, N_TOTAL + 1))}"
    )

    overlaps = [len(estrazioni[i - 1]["numeri"] & estrazioni[i]["numeri"]) for i in range(1, n)]
    mean_ov = sum(overlaps) / len(overlaps)
    exp_ov = N_DRAWN * N_DRAWN / N_TOTAL
    se_ov = sqrt(sum((x - mean_ov) ** 2 for x in overlaps) / len(overlaps)) / sqrt(len(overlaps))
    z_ov = (mean_ov - exp_ov) / se_ov if se_ov > 0 else 0
    print(f"\n  Overlap consecutivo: {'PASS' if abs(z_ov) < 3 else 'FAIL'}")
    print(f"    media={mean_ov:.4f} atteso={exp_ov:.4f} z={z_ov:.2f}")

    somme = [sum(e["numeri"]) for e in estrazioni]
    mean_s = sum(somme) / n
    var_s = sum((s - mean_s) ** 2 for s in somme) / n
    max_ac = 0.0
    for lag in [1, 2, 5, 10, 20]:
        if lag >= n:
            continue
        cov = sum((somme[i] - mean_s) * (somme[i + lag] - mean_s) for i in range(n - lag)) / (
            n - lag
        )
        ac = cov / var_s if var_s > 0 else 0
        if abs(ac) > max_ac:
            max_ac = abs(ac)
    print(f"\n  Autocorrelazione: {'PASS' if max_ac < 0.1 else 'FAIL'}")
    print(f"    max |r|={max_ac:.4f}")


def test_top5_freq(estrazioni, w, start, end):
    """Ritorna EV medio per top5_freq con finestra W in range [start, end)."""
    ev_sum, n_plays = 0.0, 0
    for i in range(max(w, start), end):
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1
        pick = {num for num, _ in freq.most_common(K)}
        ev_sum += _ev_giocata(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
        n_plays += 1
    return ev_sum / n_plays if n_plays else 0, n_plays


def fase2_segnali(estrazioni, ev_base):
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 70)
    print(f"FASE 2 — TEST SEGNALI (split {half}/{n-half})")
    print("=" * 70)
    print(f"\n  EV baseline: {ev_base:.4f}")
    print(f"\n  {'Metodo':<20} {'W':>4} {'EV disc':>9} {'EV val':>9} "
          f"{'Ratio D':>8} {'Ratio V':>8}")
    print("  " + "-" * 70)

    best = {"name": "", "ratio": 0.0, "ev": 0.0, "w": 0}

    # Test A: top5_freq
    for w in [3, 5, 10, 20, 50, 100]:
        avg_d, _ = test_top5_freq(estrazioni, w, 0, half)
        avg_v, _ = test_top5_freq(estrazioni, w, half, n)
        rd, rv = avg_d / ev_base, avg_v / ev_base
        print(f"  {'top5_freq':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} "
              f"{rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"top5_freq W={w}", "ratio": rv, "ev": avg_v, "w": w,
                    "family": "top5_freq"}

    # Test B: cold
    for w in [10, 20, 50, 100]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            all_nums = sorted(range(1, N_TOTAL + 1), key=lambda x: freq.get(x, 0))
            pick = set(all_nums[:K])
            ev = _ev_giocata(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd, rv = avg_d / ev_base, avg_v / ev_base
        print(f"  {'cold':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} "
              f"{rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"cold W={w}", "ratio": rv, "ev": avg_v, "w": w, "family": "cold"}

    # Test C: hot_extra
    for w in [5, 10, 20, 50]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j].get("extra", set()):
                    freq[num] += 1
            if not freq:
                continue
            pick = {num for num, _ in freq.most_common(K)}
            ev = _ev_giocata(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd, rv = avg_d / ev_base, avg_v / ev_base
        print(f"  {'hot_extra':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} "
              f"{rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"hot_extra W={w}", "ratio": rv, "ev": avg_v, "w": w,
                    "family": "hot_extra"}

    # Test D: vicinanza D=5
    for w in [10, 20, 50, 100]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            seed = freq.most_common(1)[0][0]
            nearby = sorted(
                [(num, freq.get(num, 0)) for num in range(1, N_TOTAL + 1)
                 if abs(num - seed) <= 5 and num != seed and freq.get(num, 0) > 0],
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
        rd, rv = avg_d / ev_base, avg_v / ev_base
        print(f"  {'vicinanza D=5':<20} {w:>4} {avg_d:>9.4f} {avg_v:>9.4f} "
              f"{rd:>7.4f}x {rv:>7.4f}x")
        if rv > best["ratio"]:
            best = {"name": f"vicinanza W={w}", "ratio": rv, "ev": avg_v, "w": w,
                    "family": "vicinanza"}

    return best


def fase3_permutation(estrazioni, best, n_perm=10000):
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 70)
    print(f"FASE 3 — PERMUTATION TEST: {best['name']} ({n_perm} iterazioni)")
    print("=" * 70)

    obs_ev = best["ev"]
    w = best["w"]
    start = max(w, half)
    nn = n - start

    # Precalcola pick e draw per validation
    picks, draws = [], []
    for i in range(start, n):
        freq = Counter()
        for j in range(i - w, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        fam = best["family"]
        if fam == "top5_freq":
            pick = {num for num, _ in freq.most_common(K)}
        elif fam == "cold":
            all_n = sorted(range(1, N_TOTAL + 1), key=lambda x: freq.get(x, 0))
            pick = set(all_n[:K])
        elif fam == "hot_extra":
            freqe = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j].get("extra", set()):
                    freqe[num] += 1
            pick = {num for num, _ in freqe.most_common(K)}
        elif fam == "vicinanza":
            seed = freq.most_common(1)[0][0]
            nearby = sorted(
                [(num, freq.get(num, 0)) for num in range(1, N_TOTAL + 1)
                 if abs(num - seed) <= 5 and num != seed and freq.get(num, 0) > 0],
                key=lambda x: -x[1],
            )
            pick = {seed}
            for num, _ in nearby:
                pick.add(num)
                if len(pick) >= K:
                    break
            pick = set(list(pick)[:K])
        else:
            pick = set()

        picks.append(pick)
        draws.append((estrazioni[i]["numeri"], estrazioni[i]["extra"]))

    random.seed(42)
    count_ge = 0
    for _ in range(n_perm):
        offset = random.randint(1, nn - 1)  # noqa: S311
        perm_total = sum(
            _ev_giocata(picks[idx], draws[(idx + offset) % nn][0],
                        draws[(idx + offset) % nn][1])
            for idx in range(nn)
        )
        if perm_total / nn >= obs_ev:
            count_ge += 1

    p_value = count_ge / n_perm
    print(f"\n  Observed EV: {obs_ev:.4f}")
    print(f"  p-value: {p_value:.4f}")
    bonf = 0.05 / 18  # 18 test totali in fase 2
    print(f"  Bonferroni threshold (0.05/18): {bonf:.4f}")
    print(f"  Significativo (raw p<0.05): {'SI' if p_value < 0.05 else 'NO'}")
    print(f"  Significativo (Bonf): {'SI' if p_value < bonf else 'NO'}")
    return p_value


def fase4_temporale(estrazioni, ev_base):
    """Stabilita del segnale top5_freq W=5 per anno."""
    print("\n" + "=" * 70)
    print("FASE 4 — STABILITA TEMPORALE (top5_freq W=5 per anno)")
    print("=" * 70)

    by_year = {}
    for e in estrazioni:
        y = e["data"][:4]
        by_year.setdefault(y, []).append(e)

    print(f"\n  {'Anno':<6} {'N':>5} {'Ratio':>8}")
    print("  " + "-" * 22)
    for y in sorted(by_year):
        sub = by_year[y]
        if len(sub) < 20:
            continue
        ev_sum, npl = 0.0, 0
        w = 5
        for i in range(w, len(sub)):
            freq = Counter()
            for j in range(i - w, i):
                for num in sub[j]["numeri"]:
                    freq[num] += 1
            pick = {num for num, _ in freq.most_common(K)}
            ev_sum += _ev_giocata(pick, sub[i]["numeri"], sub[i]["extra"])
            npl += 1
        avg = ev_sum / npl if npl else 0
        print(f"  {y:<6} {len(sub):>5} {avg/ev_base:>7.4f}x")


def fase5_rolling(estrazioni, ev_base, w=5):
    """Rolling window: ratio su finestre di 500 giocate."""
    print("\n" + "=" * 70)
    print(f"FASE 5 — ROLLING WINDOW (top5_freq W={w}, bucket=500)")
    print("=" * 70)

    n = len(estrazioni)
    bucket = 500
    print(f"\n  {'Range':<20} {'Ratio':>8}")
    print("  " + "-" * 30)
    for start in range(w, n, bucket):
        end = min(start + bucket, n)
        if end - start < 100:
            continue
        ev_sum, npl = 0.0, 0
        for i in range(start, end):
            freq = Counter()
            for j in range(max(0, i - w), i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            pick = {num for num, _ in freq.most_common(K)}
            ev_sum += _ev_giocata(pick, estrazioni[i]["numeri"], estrazioni[i]["extra"])
            npl += 1
        avg = ev_sum / npl if npl else 0
        range_lbl = f"{start}-{end}"
        print(f"  {range_lbl:<20} {avg/ev_base:>7.4f}x")


def main():
    print("=" * 70)
    print("MILLIONDAY — ANALISI ESTESA (millionday.cloud archive)")
    print("=" * 70)

    estrazioni = carica()
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")
    print(f"Periodo: {estrazioni[0]['data']} {estrazioni[0]['ora']} — "
          f"{estrazioni[-1]['data']} {estrazioni[-1]['ora']}")

    ev_base = ev_baseline()
    print(f"EV baseline analitico: {ev_base:.4f}")

    fase1_rng(estrazioni)
    best = fase2_segnali(estrazioni, ev_base)

    print(f"\n  MIGLIOR SEGNALE (validation): {best['name']} "
          f"(ratio {best['ratio']:.4f}x)")

    if best["ratio"] > 1.0:
        p = fase3_permutation(estrazioni, best)
    else:
        print("\n  Nessun segnale sopra baseline.")
        p = 1.0

    fase4_temporale(estrazioni, ev_base)
    fase5_rolling(estrazioni, ev_base)

    print("\n" + "=" * 70)
    print("VERDETTO MILLIONDAY (dataset esteso)")
    print("=" * 70)
    print(f"  Dataset: {n} estrazioni")
    print("  HE: 33.7%, Breakeven: 1.51x")
    print(f"  Miglior segnale: {best['name']} ({best['ratio']:.4f}x)")
    print(f"  p-value: {p:.4f}")
    print(f"  Rapporto dataset precedente (496): {n/496:.2f}x")


if __name__ == "__main__":
    main()
