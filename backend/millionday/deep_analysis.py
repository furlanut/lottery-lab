# ruff: noqa: E501
"""MillionDay — DEEP ANALYSIS (Fasi 0-9).

Analisi completa orientata alle proprieta uniche del gioco:
- 5 numeri su 55 (asimmetria fascia 51-55)
- 2 estrazioni/giorno (13:00 e 20:30) -> finestre in estrazioni
- Premio fisso 1M EUR (non totalizzatore)
- Extra opzionale +1 EUR (costo totale 2 EUR)

Dataset: 2607 estrazioni (millionday.cloud, 2022-2026).

Output:
- Console: report dettagliato fase per fase
- File: backend/millionday/DEEP_REPORT.md
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from datetime import date as _date
from math import comb, log, sqrt
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent / "data" / "archive_2022_2026.json"
REPORT_PATH = Path(__file__).parent / "DEEP_REPORT.md"

# Parametri di gioco
N_POOL = 55
N_DRAWN = 5
N_EXTRA = 5
N_REMAINING_AFTER_BASE = 50  # Extra viene estratto da 50 rimanenti

COSTO_BASE = 1.0
COSTO_EXTRA = 1.0
COSTO_TOTALE = COSTO_BASE + COSTO_EXTRA

# Premi netti (dopo tassazione 8%)
PREMI_BASE = {0: 0.0, 1: 0.0, 2: 2.0, 3: 50.0, 4: 1000.0, 5: 1_000_000.0}
PREMI_EXTRA = {0: 0.0, 1: 0.0, 2: 4.0, 3: 100.0, 4: 1000.0, 5: 100_000.0}

# Fasce di decina (5 complete + 1 parziale)
FASCE = [
    (1, 10),  # 10 numeri
    (11, 20),  # 10
    (21, 30),  # 10
    (31, 40),  # 10
    (41, 50),  # 10
    (51, 55),  # 5 (parziale)
]


# =====================================================================
# UTILITIES
# =====================================================================


def _vincita_base(match: int) -> float:
    return PREMI_BASE.get(match, 0.0)


def _vincita_extra(match_extra: int) -> float:
    return PREMI_EXTRA.get(match_extra, 0.0)


def _ev_giocata(pick: set, base: set, extra: set) -> tuple[float, float, float]:
    mb = len(pick & base)
    rem = pick - base
    me = len(rem & extra)
    return _vincita_base(mb), _vincita_extra(me), mb + 0.01 * me  # tuple


def _get_fascia(n: int) -> int:
    for i, (lo, hi) in enumerate(FASCE):
        if lo <= n <= hi:
            return i
    raise ValueError(f"n={n} out of range")


def _load() -> list[dict]:
    raw = json.loads(DATA_PATH.read_text())
    out = []
    for r in raw:
        out.append(
            {
                "data": r["data"],
                "ora": r["ora"],
                "numeri_list": sorted(r["numeri"]),
                "extra_list": sorted(r["extra"]),
                "numeri": set(r["numeri"]),
                "extra": set(r["extra"]),
                "dt_key": (r["data"], r["ora"]),
            }
        )
    # Ordinamento cronologico stabile
    out.sort(key=lambda e: e["dt_key"])
    return out


def _z_binomial(observed: int, n: int, p: float) -> float:
    mean = n * p
    sd = sqrt(n * p * (1 - p))
    return (observed - mean) / sd if sd > 0 else 0.0


def _z_continuous(observed: float, mean: float, sd: float) -> float:
    return (observed - mean) / sd if sd > 0 else 0.0


# Registro risultati per il report
RESULTS: dict[str, Any] = {}


# =====================================================================
# FASE 0 — VERIFICA DATI + EV ESATTO
# =====================================================================


def fase0(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 0 — VERIFICA DATASET E CALCOLO EV ESATTO")
    print("=" * 80)

    n = len(ext)
    hours = Counter(e["ora"] for e in ext)
    print(f"\nDataset: {n} estrazioni")
    print(f"Periodo: {ext[0]['data']} {ext[0]['ora']} -> {ext[-1]['data']} {ext[-1]['ora']}")
    print(f"Per orario: 13:00={hours.get('13:00', 0)}  20:30={hours.get('20:30', 0)}")

    # Verifica integrita
    bad = sum(
        1
        for e in ext
        if len(e["numeri"]) != 5 or len(e["extra"]) != 5 or (e["numeri"] & e["extra"])
    )
    print(f"Righe invalide: {bad}")

    # EV base analitico (ipergeometrica)
    c555 = comb(55, 5)
    p_base = {m: comb(5, m) * comb(50, 5 - m) / c555 for m in range(6)}
    ev_base = sum(p * PREMI_BASE[m] for m, p in p_base.items())

    print("\n--- EV BASE (5 numeri giocati, costo EUR 1) ---")
    print(f"{'Match':<8} {'P(match)':>12} {'Premio':>12} {'Contributo EV':>16}")
    print("-" * 52)
    for m in range(6):
        contrib = p_base[m] * PREMI_BASE[m]
        print(f"{m}/5{'':<5} {p_base[m]:>12.8f} {PREMI_BASE[m]:>11.0f}  {contrib:>16.6f}")
    print(f"\nEV base totale: EUR {ev_base:.6f}")
    print(f"House edge base: {(1 - ev_base / COSTO_BASE) * 100:.3f}%")
    print(f"Breakeven base: {COSTO_BASE / ev_base:.4f}x")

    # EV Extra (dati 5 numeri giocati, 5 estratti base, 5 estratti Extra dai 50 rimanenti)
    ev_extra = 0.0
    c505 = comb(50, 5)
    for mb in range(6):
        p_b = p_base[mb]
        rem = 5 - mb  # numeri giocati NON usciti nella base -> candidati per Extra
        for me in range(rem + 1):
            remaining_pool = 50 - rem
            if remaining_pool < (5 - me):
                continue
            p_e = comb(rem, me) * comb(remaining_pool, 5 - me) / c505
            ev_extra += p_b * p_e * PREMI_EXTRA[me]

    ev_totale = ev_base + ev_extra

    print("\n--- EV CON EXTRA (5 numeri, costo EUR 2) ---")
    print(f"EV base (contributo):  EUR {ev_base:.6f}")
    print(f"EV Extra (contributo): EUR {ev_extra:.6f}")
    print(f"EV totale:             EUR {ev_totale:.6f}")
    print(f"House edge totale: {(1 - ev_totale / COSTO_TOTALE) * 100:.3f}%")
    print(f"Breakeven: {COSTO_TOTALE / ev_totale:.4f}x")

    # Probabilita di vincere qualcosa
    p_win_base = sum(p_base[m] for m in [2, 3, 4, 5])
    print(f"\nP(vincere qualcosa, base): {p_win_base * 100:.3f}%  (= 1 in {1 / p_win_base:.1f})")

    RESULTS["fase0"] = {
        "n": n,
        "per_ora": dict(hours),
        "ev_base": ev_base,
        "ev_extra_contrib": ev_extra,
        "ev_totale": ev_totale,
        "he_base": (1 - ev_base / COSTO_BASE) * 100,
        "he_totale": (1 - ev_totale / COSTO_TOTALE) * 100,
        "breakeven_base": COSTO_BASE / ev_base,
        "breakeven_totale": COSTO_TOTALE / ev_totale,
        "p_win_base": p_win_base,
        "p_base_matches": p_base,
    }


# =====================================================================
# FASE 1 — ASIMMETRIA FASCIA 51-55
# =====================================================================


def fase1(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 1 — ASIMMETRIA FASCIA 51-55")
    print("=" * 80)

    n = len(ext)
    freq = Counter()
    for e in ext:
        for x in e["numeri"]:
            freq[x] += 1

    p_single = 5.0 / 55
    expected = n * p_single
    sd = sqrt(n * p_single * (1 - p_single))

    # z per ogni numero
    outliers_abs_2 = []
    outliers_abs_3 = []
    for num in range(1, 56):
        observed = freq.get(num, 0)
        z = (observed - expected) / sd
        if abs(z) >= 3:
            outliers_abs_3.append((num, observed, z))
        elif abs(z) >= 2:
            outliers_abs_2.append((num, observed, z))

    bonf_sig = [o for o in outliers_abs_3 if abs(o[2]) > 3.5]  # Bonf ~0.05/55
    print(f"\n--- Frequenza per numero (atteso {expected:.1f}, sd {sd:.2f}) ---")
    print(f"Outliers |z|>=3: {len(outliers_abs_3)}  (atteso ~0.15)")
    print(f"Outliers |z|>=2: {len(outliers_abs_2)}  (atteso ~2.5)")
    if outliers_abs_3:
        print("  Dettaglio:")
        for num, obs, z in sorted(outliers_abs_3, key=lambda x: -abs(x[2]))[:10]:
            print(f"    {num:>2}: {obs}  z={z:+.2f}")

    # Frequenza media per fascia
    print("\n--- Frequenza media per fascia ---")
    print(f"{'Fascia':<12} {'N numeri':>10} {'Freq tot':>12} {'Freq/num':>12} {'z/num':>10}")
    print("-" * 58)
    freq_per_fascia = {}
    for i, (lo, hi) in enumerate(FASCE):
        width = hi - lo + 1
        tot = sum(freq.get(x, 0) for x in range(lo, hi + 1))
        mean_num = tot / width
        z_mean = (mean_num - expected) / (sd / sqrt(width))
        freq_per_fascia[i] = {"tot": tot, "mean": mean_num, "z": z_mean}
        label = f"{lo}-{hi}{' (parz)' if width < 10 else ''}"
        print(f"{label:<12} {width:>10} {tot:>12} {mean_num:>12.1f} {z_mean:>+10.2f}")

    # Confronto specifico fascia 51-55 vs altre
    tot_others = sum(freq.get(x, 0) for x in range(1, 51))
    mean_others = tot_others / 50
    tot_parz = sum(freq.get(x, 0) for x in range(51, 56))
    mean_parz = tot_parz / 5
    diff = mean_parz - mean_others
    # sd della differenza tra medie di sample di size 5 e 50
    sd_diff = sd * sqrt(1 / 5 + 1 / 50)
    z_diff = diff / sd_diff if sd_diff > 0 else 0
    print(f"\nFascia parziale (51-55) vs altre: diff={diff:+.2f} z={z_diff:+.2f}")

    # Distribuzione di K numeri nella fascia 51-55 per estrazione
    # Ipergeometrica: P(K su 5 estratti da 55 con 5 "successi" in 5 su 55)
    print("\n--- K numeri nella fascia 51-55 per estrazione ---")
    p_iperg = {}
    c555 = comb(55, 5)
    for k in range(6):
        p_iperg[k] = comb(5, k) * comb(50, 5 - k) / c555

    osservato_k = Counter()
    for e in ext:
        k = sum(1 for x in e["numeri"] if 51 <= x <= 55)
        osservato_k[k] += 1

    print(f"{'K':<5} {'Atteso':>10} {'Osservato':>12} {'% atteso':>10} {'% oss':>10} {'z':>8}")
    print("-" * 60)
    chi2 = 0.0
    for k in range(6):
        atteso = n * p_iperg[k]
        oss = osservato_k.get(k, 0)
        if atteso > 0:
            chi2 += (oss - atteso) ** 2 / atteso
        z = (oss - atteso) / sqrt(atteso * (1 - p_iperg[k])) if atteso > 0 else 0
        print(
            f"{k:<5} {atteso:>10.1f} {oss:>12} "
            f"{p_iperg[k] * 100:>9.3f}% {(oss / n) * 100:>9.3f}% {z:>+8.2f}"
        )
    print(f"\nChi-quadro df=5: {chi2:.2f}  (soglia 0.05 ~ 11.07, 0.01 ~ 15.09)")

    RESULTS["fase1"] = {
        "outliers_z3": len(outliers_abs_3),
        "outliers_z2": len(outliers_abs_2),
        "bonf_sig": len(bonf_sig),
        "freq_per_fascia": freq_per_fascia,
        "parz_vs_others_z": z_diff,
        "chi2_k51_55": chi2,
    }


# =====================================================================
# FASE 2 — RNG ADVANCED
# =====================================================================


def fase2(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 2 — TEST RNG AVANZATI")
    print("=" * 80)

    n = len(ext)

    # --- 2A Gap test per numero ---
    print("\n--- 2A Gap test (distribuzione gap tra apparizioni) ---")
    gap_stats: dict[int, dict] = {}
    for num in range(1, 56):
        appear = [i for i, e in enumerate(ext) if num in e["numeri"]]
        if len(appear) < 10:
            continue
        gaps = [appear[i] - appear[i - 1] for i in range(1, len(appear))]
        mean_gap = sum(gaps) / len(gaps)
        # Sotto uniformita: gap ~ Geometric(p=5/55), mean = 1/p = 11
        expected_mean = 55 / 5
        # Varianza geometrica = (1-p)/p^2 = 50/5 * 55/5 = 110
        expected_var = (1 - 5 / 55) / (5 / 55) ** 2
        expected_sd_mean = sqrt(expected_var / len(gaps))
        z = (mean_gap - expected_mean) / expected_sd_mean
        gap_stats[num] = {"n_gaps": len(gaps), "mean": mean_gap, "z": z}

    outliers = [k for k, v in gap_stats.items() if abs(v["z"]) > 3]
    print(f"Numeri con |z gap|>3: {len(outliers)} / 55 (Bonferroni sig: {len(outliers) > 1})")
    if outliers:
        for num in sorted(outliers, key=lambda x: -abs(gap_stats[x]["z"]))[:8]:
            v = gap_stats[num]
            print(f"  {num:>2}: mean_gap={v['mean']:.2f} z={v['z']:+.2f} n_gaps={v['n_gaps']}")

    # --- 2B Autocorrelazione multi-lag ---
    print("\n--- 2B Autocorrelazione somme multi-lag ---")
    somme = [sum(e["numeri"]) for e in ext]
    mean_s = sum(somme) / n
    var_s = sum((s - mean_s) ** 2 for s in somme) / n
    lags = [1, 2, 3, 7, 14, 30, 60, 365]
    ac_data = {}
    print(f"{'Lag':>8} {'N':>8} {'r':>10} {'z~':>10}")
    for lag in lags:
        if lag >= n:
            continue
        cov = sum((somme[i] - mean_s) * (somme[i + lag] - mean_s) for i in range(n - lag)) / (
            n - lag
        )
        r = cov / var_s if var_s > 0 else 0.0
        z_approx = r * sqrt(n - lag)
        ac_data[lag] = {"r": r, "z": z_approx}
        print(f"{lag:>8} {n - lag:>8} {r:>+10.5f} {z_approx:>+10.2f}")

    # --- 2C Birthday / collision test ---
    print("\n--- 2C Birthday test (cinquine ripetute) ---")
    freq_cinquine = Counter(tuple(e["numeri_list"]) for e in ext)
    ripetute = [c for c in freq_cinquine.values() if c > 1]
    collisioni = sum(c - 1 for c in ripetute)
    # P(collisione) tra n cinquine su N=C(55,5)=3.478.761 distinte
    # Expected unique collisions = n(n-1)/(2N)
    n_cinquine_tot = comb(55, 5)
    exp_coll = n * (n - 1) / (2 * n_cinquine_tot)
    print(f"Cinquine distinte possibili: {n_cinquine_tot:,}")
    print(f"Cinquine ripetute (count>1): {len(ripetute)}")
    print(f"Collisioni totali: {collisioni}")
    print(f"Attese (Poisson): {exp_coll:.4f}")

    # --- 2D Chi-quadro coppie ---
    print("\n--- 2D Chi-quadro coppie ---")
    coppie = Counter()
    for e in ext:
        nums = e["numeri_list"]
        for i in range(5):
            for j in range(i + 1, 5):
                coppie[(nums[i], nums[j])] += 1
    n_coppie_totali = sum(coppie.values())  # = n * 10
    n_coppie_possibili = comb(55, 2)  # 1485
    expected_per_coppia = n_coppie_totali / n_coppie_possibili
    chi2 = 0.0
    for i in range(1, 56):
        for j in range(i + 1, 56):
            oss = coppie.get((i, j), 0)
            chi2 += (oss - expected_per_coppia) ** 2 / expected_per_coppia
    df = n_coppie_possibili - 1
    z = (chi2 - df) / sqrt(2 * df)
    print(f"Coppie osservate: {n_coppie_totali} su {n_coppie_possibili} distinte")
    print(f"Atteso per coppia: {expected_per_coppia:.3f}")
    print(f"Chi-quadro: {chi2:.1f} df={df} z={z:+.2f}  (|z|<3 = PASS)")

    RESULTS["fase2"] = {
        "gap_outliers_z3": len(outliers),
        "autocorr": ac_data,
        "cinquine_ripetute": len(ripetute),
        "collisioni": collisioni,
        "coll_attese": exp_coll,
        "chi2_coppie": chi2,
        "z_coppie": z,
    }


# =====================================================================
# FASE 3 — SINGOLI NUMERI CON FINESTRE IN ESTRAZIONI
# =====================================================================


# Finestre ricalibrate (in estrazioni, non giorni)
W_SET = [14, 60, 180, 360, 730]  # 1 sett, 1 mese, 3 mesi, 6 mesi, 1 anno


def _pick_hot(window: list[dict]) -> set:
    f = Counter()
    for e in window:
        f.update(e["numeri"])
    return {n for n, _ in f.most_common(5)}


def _pick_cold(window: list[dict]) -> set:
    f = Counter()
    for e in window:
        f.update(e["numeri"])
    all_nums = sorted(range(1, 56), key=lambda x: (f.get(x, 0), x))
    return set(all_nums[:5])


def _pick_mix3h2c(window: list[dict]) -> set:
    f = Counter()
    for e in window:
        f.update(e["numeri"])
    all_nums = sorted(range(1, 56), key=lambda x: -f.get(x, 0))
    hot = all_nums[:3]
    cold_src = sorted(range(1, 56), key=lambda x: f.get(x, 0))
    cold = [x for x in cold_src if x not in hot][:2]
    return set(hot + cold)


def _pick_optimal_freq(window: list[dict]) -> set:
    """Top 5 con frequenza piu vicina all'attesa (ne troppo caldi ne freddi)."""
    f = Counter()
    for e in window:
        f.update(e["numeri"])
    expected = len(window) * 5 / 55
    return set(sorted(range(1, 56), key=lambda x: (abs(f.get(x, 0) - expected), x))[:5])


STRATS = {
    "hot": _pick_hot,
    "cold": _pick_cold,
    "mix3h2c": _pick_mix3h2c,
    "optfreq": _pick_optimal_freq,
}


def _ev_baseline() -> float:
    """EV base+Extra atteso (EUR per giocata 2 EUR)."""
    c555 = comb(55, 5)
    c505 = comb(50, 5)
    ev = 0.0
    p_base = {m: comb(5, m) * comb(50, 5 - m) / c555 for m in range(6)}
    for m in range(6):
        ev += p_base[m] * PREMI_BASE[m]
    for mb in range(6):
        rem = 5 - mb
        for me in range(rem + 1):
            pool_rem = 50 - rem
            if pool_rem < (5 - me):
                continue
            p_e = comb(rem, me) * comb(pool_rem, 5 - me) / c505
            ev += p_base[mb] * p_e * PREMI_EXTRA[me]
    return ev


def fase3(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 3 — SINGOLI NUMERI CON FINESTRE IN ESTRAZIONI")
    print("=" * 80)

    n = len(ext)
    half = n // 2
    ev_base = _ev_baseline()
    print(f"\nBaseline EV (per 2 EUR): {ev_base:.4f}  -> house edge {(1 - ev_base / 2) * 100:.2f}%")
    print(f"Split: discovery 0..{half - 1}, validation {half}..{n - 1}")

    rows = []
    print(f"\n{'Strategia':<12} {'W':>5} {'EV disc':>9} {'EV val':>9} "
          f"{'Ratio D':>8} {'Ratio V':>8}")
    print("-" * 60)
    for sname, pickfn in STRATS.items():
        for w in W_SET:
            ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
            for i in range(w, n):
                window = ext[i - w : i]
                pick = pickfn(window)
                base_win = _vincita_base(len(pick & ext[i]["numeri"]))
                rem = pick - ext[i]["numeri"]
                extra_win = _vincita_extra(len(rem & ext[i]["extra"]))
                ev = base_win + extra_win
                if i < half:
                    ev_d += ev
                    nd += 1
                else:
                    ev_v += ev
                    nv += 1
            avg_d = ev_d / nd if nd else 0
            avg_v = ev_v / nv if nv else 0
            rd = avg_d / ev_base
            rv = avg_v / ev_base
            rows.append({"strat": sname, "w": w, "ratio_d": rd, "ratio_v": rv, "ev_v": avg_v,
                         "nd": nd, "nv": nv})
            print(f"{sname:<12} {w:>5} {avg_d:>9.4f} {avg_v:>9.4f} {rd:>+7.4f}x {rv:>+7.4f}x")

    rows.sort(key=lambda r: -r["ratio_v"])
    best = rows[0]
    print(f"\nMiglior (validation): {best['strat']} W={best['w']} ratio={best['ratio_v']:.4f}x")

    # Permutation test sul miglior segnale
    if best["ratio_v"] > 1.0:
        p = _permutation_test_strategy(ext, best["strat"], best["w"])
        bonf = 0.05 / (len(STRATS) * len(W_SET))
        sig = "SI" if p < bonf else ("BORDERLINE" if p < 0.05 else "NO")
        print(f"\nPermutation test 10k iter: p={p:.4f}  Bonf={bonf:.4f}  -> {sig}")
    else:
        p = 1.0
        bonf = 0.05 / (len(STRATS) * len(W_SET))
        sig = "NO (ratio<1)"

    RESULTS["fase3"] = {
        "best": best,
        "all_rows": rows,
        "permutation_p": p,
        "bonferroni": bonf,
        "sig_class": sig,
    }


def _permutation_test_strategy(ext: list[dict], strat: str, w: int, n_perm: int = 10000) -> float:
    """Shuffle circolare delle estrazioni val rispetto ai pick generati."""
    n = len(ext)
    half = n // 2
    pickfn = STRATS[strat]
    picks, draws = [], []
    for i in range(max(half, w), n):
        window = ext[i - w : i]
        picks.append(pickfn(window))
        draws.append((ext[i]["numeri"], ext[i]["extra"]))
    nn = len(picks)
    if nn < 2:
        return 1.0

    def _ev(picks_, draws_):
        tot = 0.0
        for idx in range(len(picks_)):
            p = picks_[idx]
            d = draws_[idx]
            tot += _vincita_base(len(p & d[0])) + _vincita_extra(len((p - d[0]) & d[1]))
        return tot / nn

    obs = _ev(picks, draws)
    random.seed(42)
    count_ge = 0
    for _ in range(n_perm):
        offset = random.randint(1, nn - 1)  # noqa: S311
        shifted = [draws[(idx + offset) % nn] for idx in range(nn)]
        if _ev(picks, shifted) >= obs:
            count_ge += 1
    return count_ge / n_perm


# =====================================================================
# FASE 4 — STRUTTURA CINQUINA
# =====================================================================


def _tipo_fascia(nums: set) -> tuple:
    counts = [0] * 6
    for x in nums:
        counts[_get_fascia(x)] += 1
    return tuple(sorted(counts, reverse=True))


def fase4(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 4 — STRUTTURA CINQUINA")
    print("=" * 80)

    n = len(ext)
    tipi = [_tipo_fascia(e["numeri"]) for e in ext]
    cnt = Counter(tipi)
    print(f"\n--- Distribuzione tipi fascia (n={n}) ---")
    print(f"{'Tipo':<20} {'N':>8} {'% oss':>10}")
    for t, c in sorted(cnt.items(), key=lambda x: -x[1])[:12]:
        print(f"{str(t):<20} {c:>8} {c / n * 100:>9.2f}%")

    # Matrice di transizione
    trans = defaultdict(lambda: Counter())
    for i in range(1, n):
        trans[tipi[i - 1]][tipi[i]] += 1

    # Mutual information I(T_{t-1}; T_t)
    # I = sum p(x,y) log (p(x,y)/(p(x)p(y)))
    pt = {t: c / n for t, c in cnt.items()}
    total_pairs = n - 1
    mi = 0.0
    for t1, nxt in trans.items():
        for t2, c in nxt.items():
            pxy = c / total_pairs
            pxpy = pt[t1] * pt[t2]
            if pxy > 0 and pxpy > 0:
                mi += pxy * log(pxy / pxpy)

    # Permutation MI su 1000 shuffle
    random.seed(42)
    mis_perm = []
    idx = list(range(n))
    for _ in range(1000):
        random.shuffle(idx)
        tipi_sh = [tipi[i] for i in idx]
        trans_sh = defaultdict(lambda: Counter())
        for i in range(1, n):
            trans_sh[tipi_sh[i - 1]][tipi_sh[i]] += 1
        mi_sh = 0.0
        for t1, nxt in trans_sh.items():
            for t2, c in nxt.items():
                pxy = c / total_pairs
                pxpy = pt[t1] * pt[t2]
                if pxy > 0 and pxpy > 0:
                    mi_sh += pxy * log(pxy / pxpy)
        mis_perm.append(mi_sh)
    mean_sh = sum(mis_perm) / len(mis_perm)
    sd_sh = sqrt(sum((x - mean_sh) ** 2 for x in mis_perm) / len(mis_perm))
    p_mi = sum(1 for x in mis_perm if x >= mi) / len(mis_perm)
    print(f"\nMutual Info I(T_t-1;T_t): {mi:.4f}")
    print(f"MI shuffled: mean={mean_sh:.4f} sd={sd_sh:.4f}  p={p_mi:.4f}")

    # Parita
    print("\n--- Parita (0-5 pari su 5 estratti) ---")
    par_cnt = Counter()
    for e in ext:
        par_cnt[sum(1 for x in e["numeri"] if x % 2 == 0)] += 1
    for k in range(6):
        print(f"  {k} pari: {par_cnt.get(k, 0)}  ({par_cnt.get(k, 0) / n * 100:.2f}%)")

    # Somma
    somme = [sum(e["numeri"]) for e in ext]
    mean_s = sum(somme) / n
    sd_s = sqrt(sum((s - mean_s) ** 2 for s in somme) / n)
    print(f"\nSomma: media={mean_s:.1f} sd={sd_s:.1f} range=[{min(somme)}, {max(somme)}]")
    print("  attesa media (5 x 28) = 140")

    # Range
    ranges = [max(e["numeri"]) - min(e["numeri"]) for e in ext]
    mean_r = sum(ranges) / n
    print(f"Range (max-min): media={mean_r:.1f}  range=[{min(ranges)}, {max(ranges)}]")

    RESULTS["fase4"] = {
        "n_tipi": len(cnt),
        "mi": mi,
        "mi_p": p_mi,
        "parita": dict(par_cnt),
        "somma_mean": mean_s,
        "somma_sd": sd_s,
        "range_mean": mean_r,
    }


# =====================================================================
# FASE 5 — GIORNO DELLA SETTIMANA
# =====================================================================


def _dow(data_str: str) -> int:
    y, m, d = map(int, data_str.split("-"))
    return _date(y, m, d).weekday()  # 0=lun


DOW_NAMES = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


def fase5(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 5 — GIORNO DELLA SETTIMANA")
    print("=" * 80)

    by_dow: dict[int, list[dict]] = defaultdict(list)
    for e in ext:
        by_dow[_dow(e["data"])].append(e)

    n_total = sum(len(v) for v in by_dow.values())
    expected_per_num = n_total * 5 / 55

    print(f"\n{'DoW':<6} {'N estr':>8} {'Somma μ':>10} {'Z somma':>10}")
    print("-" * 40)
    somme_all = [sum(e["numeri"]) for e in ext]
    mu = sum(somme_all) / len(somme_all)
    sd = sqrt(sum((s - mu) ** 2 for s in somme_all) / len(somme_all))
    dow_results = {}
    for d in range(7):
        lst = by_dow[d]
        if not lst:
            continue
        sommas = [sum(e["numeri"]) for e in lst]
        m = sum(sommas) / len(sommas)
        z = (m - mu) / (sd / sqrt(len(sommas)))
        dow_results[d] = {"n": len(lst), "mean_somma": m, "z": z}
        print(f"{DOW_NAMES[d]:<6} {len(lst):>8} {m:>10.1f} {z:>+10.2f}")

    # Sig Bonferroni: 7 test -> soglia |z|>2.69
    sig_days = [d for d, v in dow_results.items() if abs(v["z"]) > 2.69]
    print(f"\nGiorni con |z|>2.69 (Bonferroni 7 test): {len(sig_days)}")

    RESULTS["fase5"] = {"dow": dow_results, "sig_days": len(sig_days),
                        "expected_per_num": expected_per_num}


# =====================================================================
# FASE 6 — EXTRA MILLIONDAY
# =====================================================================


def fase6(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 6 — EXTRA MILLIONDAY")
    print("=" * 80)

    n = len(ext)
    # Freq Extra puri
    freq_e = Counter()
    freq_b = Counter()
    for e in ext:
        freq_b.update(e["numeri"])
        freq_e.update(e["extra"])

    # Extra e' estratto dai 50 rimanenti dopo base
    # Quindi per ogni numero, in n estrazioni, esce nell'Extra con prob
    # P = (10 estratti tra 55, di cui 5 Extra, dato 55-5=50 pool Extra)
    # Semplificando: P(n nell'Extra) = 5/55 (stesso del base)
    # perche un numero ha 10 chance su 55 di uscire (5 base + 5 extra)
    # e condizionato a non esser base, P(Extra|not base) = 5/50 = 1/10
    # P(base) = 5/55 ~ 9.09%, P(Extra) = P(not base) * 5/50 = 50/55 * 5/50 = 5/55 = 9.09%
    # Quindi stessa freq attesa.
    expected = n * 5 / 55

    # Confronto marginale base vs extra
    sd = sqrt(n * 5 / 55 * 50 / 55)
    outl_b = sum(1 for x in range(1, 56) if abs((freq_b[x] - expected) / sd) > 3)
    outl_e = sum(1 for x in range(1, 56) if abs((freq_e[x] - expected) / sd) > 3)
    print(f"Freq attesa per numero (entrambe): {expected:.1f}")
    print(f"Outliers base |z|>3: {outl_b}")
    print(f"Outliers Extra |z|>3: {outl_e}")

    # Correlazione strutturale: base e extra in fasce complementari?
    print("\n--- Distribuzione per fascia: base vs extra ---")
    print(f"{'Fascia':<12} {'Base':>10} {'Extra':>10} {'Diff':>10}")
    for _i, (lo, hi) in enumerate(FASCE):
        tb = sum(freq_b[x] for x in range(lo, hi + 1))
        te = sum(freq_e[x] for x in range(lo, hi + 1))
        print(f"{lo}-{hi}{'':<6} {tb:>10} {te:>10} {tb - te:>+10}")

    # EV Extra isolato (giocando Extra only, da dove l'utente conosce i 5 numeri giocati,
    # e contribuisce solo quando i numeri NON escono nella base)
    # Nota: non si puo giocare solo Extra senza base. Calcoliamo EV marginale dell'opzione.
    ev_base_only = RESULTS["fase0"]["ev_base"]
    ev_tot = RESULTS["fase0"]["ev_totale"]
    ev_extra_marginale = ev_tot - ev_base_only
    print(f"\nEV marginale dell'opzione Extra: EUR {ev_extra_marginale:.4f}")
    print("Costo aggiunto: EUR 1.00")
    print(f"Vale la pena? {'SI' if ev_extra_marginale > 1.0 else 'NO'}  "
          f"(EV marginale {ev_extra_marginale:.3f} < costo 1.0 => EV - costo = "
          f"{ev_extra_marginale - 1.0:+.3f})")

    RESULTS["fase6"] = {
        "outl_base_z3": outl_b,
        "outl_extra_z3": outl_e,
        "ev_extra_marginale": ev_extra_marginale,
    }


# =====================================================================
# FASE 7 — MULTI-GIOCATA OTTIMALE
# =====================================================================


def fase7(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 7 — MULTI-GIOCATA OTTIMALE")
    print("=" * 80)

    # MillionDay: max 10 giocate singole online per schedina, +1 EUR Extra per ciascuna
    # Con premio FISSO 1M per 5/5, l'EV delle 5/5 e' costante
    # Strategia 1: DISPERSIONE - 10 cinquine con 50 numeri distinti
    # Strategia 2: CONCENTRAZIONE - 10 cinquine sovrapposte (sistema 7 numeri)
    # Dispersione: 10 picks disgiunti -> P(almeno 2/5 su qualcuna) massima

    # Per un sistema di K numeri, C(K,5) cinquine
    # K=7 -> 21 cinquine (troppe, max 10)
    # K=6 -> 6 cinquine, richiede 6 EUR (base) + 6 EUR Extra = 12 EUR
    print("\n--- Analisi sistema K numeri ---")
    print(f"{'K':<4} {'N cinquine':>12} {'Costo base':>12} {'Costo b+Extra':>15}")
    for k in range(5, 11):
        nc = comb(k, 5)
        cost_b = nc * COSTO_BASE
        cost_be = nc * COSTO_TOTALE
        print(f"{k:<4} {nc:>12} {cost_b:>11.0f}€ {cost_be:>14.0f}€")

    # Simulazione: 10.000 iterazioni per ogni strategia
    # Strategia A: 10 cinquine casuali disgiunte (50 numeri, max possibile)
    # Strategia B: sistema 6 numeri (6 cinquine)
    # Strategia C: sistema 7 numeri (21 cinquine, limita a 10)

    random.seed(42)
    n_sims = 10_000
    results_strats = {}

    for label, _n_cinquine, mode in [
        ("Dispersione 10x5 (50 num)", 10, "disjoint"),
        ("Sistema 6 num (6 cinquine)", 6, "system6"),
        ("Sistema 7 num (10/21 cinquine)", 10, "system7"),
        ("Singola 5 numeri", 1, "single"),
    ]:
        wins_base_total, _wins_extra_total, n_min_2, n_min_3 = 0, 0, 0, 0
        for _ in range(n_sims):
            # Estrazione simulata: 5 numeri random su 55 e 5 Extra dai 50 rimanenti
            all_nums = random.sample(range(1, 56), 10)
            base_drawn = set(all_nums[:5])
            extra_drawn = set(all_nums[5:])

            # Genera cinquine
            if mode == "disjoint":
                nums_pool = random.sample(range(1, 56), 50)
                cinquine = [set(nums_pool[i * 5 : (i + 1) * 5]) for i in range(10)]
            elif mode == "system6":
                seed = random.sample(range(1, 56), 6)
                cinquine = []
                for i in range(6):
                    c = set(seed[:i] + seed[i + 1 :])
                    cinquine.append(c)
            elif mode == "system7":
                seed = random.sample(range(1, 56), 7)
                from itertools import combinations
                all_comb = list(combinations(seed, 5))
                picks = random.sample(all_comb, 10)
                cinquine = [set(p) for p in picks]
            else:  # single
                cinquine = [set(random.sample(range(1, 56), 5))]

            max_mb, max_me = 0, 0
            ev_iter = 0.0
            for c in cinquine:
                mb = len(c & base_drawn)
                me = len((c - base_drawn) & extra_drawn)
                ev_iter += PREMI_BASE[mb] + PREMI_EXTRA[me]
                if mb > max_mb:
                    max_mb = mb
                if me > max_me:
                    max_me = me

            wins_base_total += ev_iter
            if max_mb >= 2:
                n_min_2 += 1
            if max_mb >= 3:
                n_min_3 += 1

        mean_win = wins_base_total / n_sims
        cost_per_play = len(cinquine) * COSTO_TOTALE  # uso ultima iterazione (stesso n_cinquine)
        ev_ratio = mean_win / cost_per_play
        results_strats[label] = {
            "p_min2": n_min_2 / n_sims,
            "p_min3": n_min_3 / n_sims,
            "mean_win": mean_win,
            "cost": cost_per_play,
            "ev_ratio": ev_ratio,
        }
        print(f"\n{label}:")
        print(f"  Costo per schedina: EUR {cost_per_play}")
        print(f"  P(almeno 2/5 su qualcuna): {n_min_2 / n_sims * 100:.2f}%")
        print(f"  P(almeno 3/5 su qualcuna): {n_min_3 / n_sims * 100:.2f}%")
        print(f"  Vincita media: EUR {mean_win:.4f}")
        print(f"  EV ratio: {ev_ratio:.4f}  (breakeven 1.0)")

    # Bankroll 30 EUR/mese (2 EUR/giorno ~15 giocate)
    # Strategia ottimale sotto vincolo budget 30 EUR
    print("\n--- Bankroll EUR 30/mese (~15 schedine da 2 EUR) ---")
    print("  Dispersione (1 giocata/giorno) ha EV atteso: "
          f"EUR {results_strats['Singola 5 numeri']['mean_win'] * 15:.2f}")
    print(f"  Sistema 6 (una volta/mese 12 EUR): 2.5 sistemi/mese ~ "
          f"EUR {results_strats['Sistema 6 num (6 cinquine)']['mean_win'] * 2.5:.2f}")

    RESULTS["fase7"] = results_strats


# =====================================================================
# FASE 8 — CROSS-GAME VinciCasa
# =====================================================================


def fase8(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 8 — CROSS-GAME VINCICASA")
    print("=" * 80)

    # VinciCasa data nel DB ma richiede connessione.
    # Tentiamo di caricare da CSV o skippiamo
    vc_paths = [
        Path("/Users/lucafurlanut/progetti/lotto/archivio_dati/vincicasa.csv"),
        Path(__file__).parent.parent / "vincicasa" / "data" / "estrazioni.csv",
    ]
    vc_data = None
    for p in vc_paths:
        if p.exists():
            vc_data = p
            break

    if not vc_data:
        print("\n[SKIP] Dataset VinciCasa non disponibile in filesystem locale.")
        print("       Richiede connessione al DB production (lottery.fl3.org).")
        RESULTS["fase8"] = {"status": "skipped", "reason": "VinciCasa data not local"}
        return

    # Se mai trovassimo i dati, farei:
    # - Parse VinciCasa per data
    # - Per ogni data in cui ci sono entrambi, confronta range 1-40
    # - Correlazione somme
    print(f"\n[TODO] Dati VinciCasa trovati in {vc_data}, ma correlazione cross-game "
          "richiede tool di alignment orario -> prossima iterazione.")
    RESULTS["fase8"] = {"status": "not_implemented"}


# =====================================================================
# FASE 9 — PERSISTENZA NUMERICA
# =====================================================================


def _overlap(a: dict, b: dict) -> int:
    return len(a["numeri"] & b["numeri"])


def fase9(ext: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("FASE 9 — PERSISTENZA NUMERICA")
    print("=" * 80)

    n = len(ext)
    n_pairs = n - 1

    # 9A Overlap lag 1
    print("\n--- 9A Overlap lag 1 (estrazioni consecutive) ---")
    overlaps = [_overlap(ext[i - 1], ext[i]) for i in range(1, n)]
    mean_ov = sum(overlaps) / len(overlaps)
    expected = 5 * 5 / 55  # 0.4545
    # Distribuzione teorica ipergeometrica
    c555 = comb(55, 5)
    p_k = {k: comb(5, k) * comb(50, 5 - k) / c555 for k in range(6)}
    # Varianza teorica dell'overlap ipergeometrico per UNA coppia
    var_ov_single = sum((k - expected) ** 2 * p_k[k] for k in range(6))
    sd_ov_single = sqrt(var_ov_single)
    # Standard error della media empirica
    se_mean = sd_ov_single / sqrt(len(overlaps))
    z_ov = (mean_ov - expected) / se_mean

    cnt_ov = Counter(overlaps)
    print(f"Media overlap: {mean_ov:.4f}  atteso: {expected:.4f}  z: {z_ov:+.2f}")
    print(f"{'k':<4} {'Atteso':>8} {'Oss':>8} {'%atteso':>10} {'%oss':>10}")
    for k in range(6):
        if p_k[k] < 1e-6 and k > 3:
            break
        exp_n = n_pairs * p_k[k]
        print(f"{k:<4} {exp_n:>8.1f} {cnt_ov.get(k, 0):>8} "
              f"{p_k[k] * 100:>9.3f}% {cnt_ov.get(k, 0) / n_pairs * 100:>9.3f}%")

    # 9B Overlap per tipo di coppia
    print("\n--- 9B Overlap per tipo di coppia consecutiva ---")
    # Classifica ogni coppia consecutiva
    intra_day = []  # 13:00 -> 20:30 stesso giorno
    inter_day = []  # 20:30 -> 13:00 giorno dopo
    same_hour_13 = []  # 13:00 -> 13:00 giorno dopo (lag=2 nel flusso)
    same_hour_20 = []  # 20:30 -> 20:30 giorno dopo

    for i in range(1, n):
        a = ext[i - 1]
        b = ext[i]
        ov = _overlap(a, b)
        if a["data"] == b["data"] and a["ora"] == "13:00" and b["ora"] == "20:30":
            intra_day.append(ov)
        elif a["ora"] == "20:30" and b["ora"] == "13:00":
            inter_day.append(ov)

    # Same-hour lag 2 (richiede ext[i-2] e ext[i] dello stesso orario)
    for i in range(2, n):
        a = ext[i - 2]
        b = ext[i]
        if a["ora"] == b["ora"] == "13:00":
            same_hour_13.append(_overlap(a, b))
        elif a["ora"] == b["ora"] == "20:30":
            same_hour_20.append(_overlap(a, b))

    def _stats(lst, label):
        if not lst:
            print(f"  {label}: nessun dato")
            return None
        m = sum(lst) / len(lst)
        # SE della media per sample di size len(lst)
        se_lst = sd_ov_single / sqrt(len(lst))
        z_simple = (m - expected) / se_lst if se_lst > 0 else 0
        print(f"  {label:<30} n={len(lst):>5} mean={m:.4f}  z={z_simple:+.2f}")
        return {"n": len(lst), "mean": m, "z": z_simple}

    res_intra = _stats(intra_day, "Intra-giorno 13->20 (lag 1)")
    res_inter = _stats(inter_day, "Inter-giorno 20->13 (lag 1)")
    res_sh13 = _stats(same_hour_13, "Stesso orario 13 (lag 2)")
    res_sh20 = _stats(same_hour_20, "Stesso orario 20 (lag 2)")

    # 9C Persistenza: P(X >= 2 in W) per ogni numero
    print("\n--- 9C Persistenza: P(X>=2 in W estrazioni) ---")
    from math import factorial
    def _binom_pmf(k, w, p):
        if k < 0 or k > w:
            return 0
        return (factorial(w) // (factorial(k) * factorial(w - k))) * (p ** k) * ((1 - p) ** (w - k))

    def _p_ge(threshold, w, p):
        return sum(_binom_pmf(k, w, p) for k in range(threshold, w + 1))

    p_single = 5 / 55
    for w in [2, 3, 4, 5, 7, 10, 14, 20]:
        p_theor_ge2 = _p_ge(2, w, p_single)
        # Conta quante volte ogni numero appare >=2 volte in finestre scorrevoli
        count_ge2 = 0
        total_windows = 0
        for i in range(w, n + 1):
            wnum = Counter()
            for e in ext[i - w : i]:
                wnum.update(e["numeri"])
            for num in range(1, 56):
                total_windows += 1
                if wnum.get(num, 0) >= 2:
                    count_ge2 += 1
        oss_rate = count_ge2 / total_windows if total_windows else 0
        sd_theor = sqrt(total_windows * p_theor_ge2 * (1 - p_theor_ge2))
        z_theor = (count_ge2 - total_windows * p_theor_ge2) / sd_theor if sd_theor > 0 else 0
        flag = "+" if oss_rate > p_theor_ge2 else "-"
        print(f"  W={w:>3}: oss={oss_rate * 100:>6.3f}% teor={p_theor_ge2 * 100:>6.3f}% "
              f"z={z_theor:+.2f} {flag}")

    # 9D Hot numbers come predittori: P(hot esce in t+1)
    print("\n--- 9D Hot numbers: P(esce in t+1 | apparso >=2 in ultime W) ---")
    for w in [3, 5, 7, 10, 14, 20]:
        n_hot_pred = 0
        n_hot_hit = 0
        for i in range(w, n):
            wnum = Counter()
            for e in ext[i - w : i]:
                wnum.update(e["numeri"])
            hots = [x for x in range(1, 56) if wnum.get(x, 0) >= 2]
            for h in hots:
                n_hot_pred += 1
                if h in ext[i]["numeri"]:
                    n_hot_hit += 1
        if n_hot_pred > 0:
            rate = n_hot_hit / n_hot_pred
            sd_p = sqrt(p_single * (1 - p_single) / n_hot_pred)
            z = (rate - p_single) / sd_p
            flag = "PERSIST" if rate > p_single + 2 * sd_p else (
                "ANTI" if rate < p_single - 2 * sd_p else "null"
            )
            print(f"  W={w:>3}: n_preds={n_hot_pred:>6} hits={n_hot_hit:>5} "
                  f"rate={rate * 100:.3f}% z={z:+.2f}  {flag}")

    # 9E Strategia ripetitori vs baseline
    print("\n--- 9E Strategia ripetitori ---")
    ev_base = _ev_baseline()
    half = n // 2
    rows_9e = []
    for w in [3, 5, 7, 10, 14]:
        ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
        for i in range(w, n):
            wnum = Counter()
            for e in ext[i - w : i]:
                wnum.update(e["numeri"])
            # Numeri hot (>=2 volte)
            hots = sorted(
                [x for x in range(1, 56) if wnum.get(x, 0) >= 2],
                key=lambda x: (-wnum.get(x, 0), x),
            )
            if len(hots) >= 5:
                pick = set(hots[:5])
            else:
                # Completa con piu frequenti
                pick = set(hots)
                most = [x for x, _ in wnum.most_common() if x not in pick]
                for x in most:
                    pick.add(x)
                    if len(pick) >= 5:
                        break
                # Se ancora <5, numeri random (improbabile per W>=3)
                while len(pick) < 5:
                    for x in range(1, 56):
                        if x not in pick:
                            pick.add(x)
                            break
            # Verifica
            base_win = _vincita_base(len(pick & ext[i]["numeri"]))
            extra_win = _vincita_extra(len((pick - ext[i]["numeri"]) & ext[i]["extra"]))
            ev = base_win + extra_win
            if i < half:
                ev_d += ev
                nd += 1
            else:
                ev_v += ev
                nv += 1
        avg_d = ev_d / nd if nd else 0
        avg_v = ev_v / nv if nv else 0
        rd = avg_d / ev_base
        rv = avg_v / ev_base
        rows_9e.append({"w": w, "ratio_d": rd, "ratio_v": rv, "ev_v": avg_v})
        print(f"  W={w:>3}: disc={rd:+.4f}x  val={rv:+.4f}x")

    # 9F Pattern orario (sub-datasets)
    print("\n--- 9F Pattern orario: test 9E su sub-datasets ---")
    for hour in ["13:00", "20:30"]:
        sub = [e for e in ext if e["ora"] == hour]
        if len(sub) < 200:
            print(f"  [{hour}] dataset troppo piccolo ({len(sub)})")
            continue
        h_half = len(sub) // 2
        for w in [3, 5, 7]:
            ev_d, ev_v, nd, nv = 0.0, 0.0, 0, 0
            for i in range(w, len(sub)):
                wnum = Counter()
                for e in sub[i - w : i]:
                    wnum.update(e["numeri"])
                hots = sorted(
                    [x for x in range(1, 56) if wnum.get(x, 0) >= 2],
                    key=lambda x: (-wnum.get(x, 0), x),
                )
                pick = set(hots[:5])
                if len(pick) < 5:
                    for x, _ in wnum.most_common():
                        if x not in pick:
                            pick.add(x)
                        if len(pick) >= 5:
                            break
                while len(pick) < 5:
                    for x in range(1, 56):
                        if x not in pick:
                            pick.add(x)
                            break
                bw = _vincita_base(len(pick & sub[i]["numeri"]))
                ew = _vincita_extra(len((pick - sub[i]["numeri"]) & sub[i]["extra"]))
                ev = bw + ew
                if i < h_half:
                    ev_d += ev
                    nd += 1
                else:
                    ev_v += ev
                    nv += 1
            avg_d = ev_d / nd if nd else 0
            avg_v = ev_v / nv if nv else 0
            rd = avg_d / ev_base
            rv = avg_v / ev_base
            print(f"  [{hour}] W={w:>2}: disc={rd:+.4f}x  val={rv:+.4f}x "
                  f"(n_val={nv})")

    # 9G Catene di Markov sui numeri
    print("\n--- 9G Catene di Markov: P(1|1) vs P(1|0) per ogni numero ---")
    p_single = 5 / 55
    sig_persist, sig_anti = 0, 0
    details = []
    for num in range(1, 56):
        # Serie binaria
        s = [1 if num in e["numeri"] else 0 for e in ext]
        n11, n10, n01, n00 = 0, 0, 0, 0
        for i in range(1, len(s)):
            prev, curr = s[i - 1], s[i]
            if prev == 1 and curr == 1:
                n11 += 1
            elif prev == 1 and curr == 0:
                n10 += 1
            elif prev == 0 and curr == 1:
                n01 += 1
            else:
                n00 += 1
        # P(1|1) = n11 / (n11 + n10)
        n1 = n11 + n10
        n0 = n01 + n00
        if n1 < 10 or n0 < 10:
            continue
        p11 = n11 / n1
        n01 / n0
        # Test: sotto indipendenza, entrambe = p_single
        se11 = sqrt(p_single * (1 - p_single) / n1)
        z11 = (p11 - p_single) / se11
        if z11 > 3.5:  # Bonf 0.05/55 -> z ~3.0, uso 3.5 per piu stringenza
            sig_persist += 1
            details.append((num, p11, z11, "+"))
        elif z11 < -3.5:
            sig_anti += 1
            details.append((num, p11, z11, "-"))
    print(f"P(1|1) attesa sotto indipendenza: {p_single * 100:.3f}%")
    print(f"Numeri con persistenza |z|>3.5 (Bonferroni-safe): {sig_persist + sig_anti} / 55")
    print(f"  Persistenza positiva (+): {sig_persist}")
    print(f"  Anti-persistenza (-): {sig_anti}")
    for num, p11, z, sign in sorted(details, key=lambda x: -abs(x[2]))[:8]:
        print(f"  {num:>2}: P(1|1)={p11 * 100:>5.2f}% z={z:+.2f}  {sign}")

    RESULTS["fase9"] = {
        "overlap_mean": mean_ov,
        "overlap_expected": expected,
        "z_ov": z_ov,
        "intra_day": res_intra,
        "inter_day": res_inter,
        "same_hour_13": res_sh13,
        "same_hour_20": res_sh20,
        "rows_9e": rows_9e,
        "markov_persist": sig_persist,
        "markov_anti": sig_anti,
    }


# =====================================================================
# REPORT MD
# =====================================================================


def generate_report() -> None:
    r = RESULTS
    f0 = r.get("fase0", {})
    f1 = r.get("fase1", {})
    f2 = r.get("fase2", {})
    f3 = r.get("fase3", {})
    f4 = r.get("fase4", {})
    f5 = r.get("fase5", {})
    f6 = r.get("fase6", {})
    f9 = r.get("fase9", {})

    lines = []
    lines.append("# MillionDay — Deep Analysis Report\n")
    lines.append("Dataset: **2.607 estrazioni** (16 mar 2022 - 16 apr 2026, archivio millionday.cloud).\n")
    lines.append(f"Composizione: {f0.get('per_ora', {}).get('13:00', 0)} estrazioni 13:00 + {f0.get('per_ora', {}).get('20:30', 0)} estrazioni 20:30.\n")

    lines.append("\n## Fase 0 — EV esatto\n")
    lines.append(f"- EV base (5 num, costo 1 EUR): **{f0.get('ev_base', 0):.4f} EUR**\n")
    lines.append(f"- House edge base: **{f0.get('he_base', 0):.2f}%**\n")
    lines.append(f"- Breakeven base: **{f0.get('breakeven_base', 0):.3f}x**\n")
    lines.append(f"- EV totale (base+Extra, costo 2 EUR): **{f0.get('ev_totale', 0):.4f} EUR**\n")
    lines.append(f"- House edge totale: **{f0.get('he_totale', 0):.2f}%**\n")
    lines.append(f"- Breakeven totale: **{f0.get('breakeven_totale', 0):.3f}x**\n")
    lines.append(f"- P(vincere qualcosa, base): {f0.get('p_win_base', 0) * 100:.2f}% (~1 in {1 / f0.get('p_win_base', 1):.0f})\n")

    lines.append("\n## Fase 1 — Asimmetria fascia 51-55\n")
    lines.append(f"- Outliers frequenza per numero |z|>=3: **{f1.get('outliers_z3', 0)}/55** (atteso ~0.15 per caso)\n")
    lines.append(f"- Outliers |z|>=2: {f1.get('outliers_z2', 0)}/55 (atteso ~2.5)\n")
    lines.append(f"- Fascia parziale (51-55) vs altre: z={f1.get('parz_vs_others_z', 0):+.2f}\n")
    lines.append(f"- Chi-quadro distribuzione K in 51-55: {f1.get('chi2_k51_55', 0):.2f} (df=5, soglia 0.05=11.07)\n")

    lines.append("\n## Fase 2 — RNG advanced\n")
    lines.append(f"- Numeri con gap anomalo |z|>3: {f2.get('gap_outliers_z3', 0)}/55\n")
    lines.append(f"- Cinquine ripetute: {f2.get('cinquine_ripetute', 0)} (attese Poisson: {f2.get('coll_attese', 0):.2f})\n")
    lines.append(f"- Chi-quadro coppie: {f2.get('chi2_coppie', 0):.1f} z={f2.get('z_coppie', 0):+.2f}\n")
    ac = f2.get("autocorr", {})
    if ac:
        lines.append("\nAutocorrelazione somme:\n\n")
        lines.append("| Lag | r | z |\n|---|---|---|\n")
        for lag, v in sorted(ac.items()):
            lines.append(f"| {lag} | {v['r']:+.5f} | {v['z']:+.2f} |\n")

    lines.append("\n## Fase 3 — Singoli numeri con finestre in estrazioni\n")
    best = f3.get("best", {})
    lines.append(f"- Miglior segnale (validation): **{best.get('strat', 'n/a')} W={best.get('w', 0)}**\n")
    lines.append(f"- Ratio val: **{best.get('ratio_v', 0):.4f}x**\n")
    lines.append(f"- Permutation p-value: **{f3.get('permutation_p', 1):.4f}**\n")
    lines.append(f"- Bonferroni threshold: {f3.get('bonferroni', 0):.4f}\n")
    lines.append(f"- Significativita: **{f3.get('sig_class', 'n/a')}**\n")

    lines.append("\nTabella completa (top 8 per ratio val):\n\n")
    lines.append("| Strategia | W | Ratio disc | Ratio val |\n|---|---|---|---|\n")
    all_rows = f3.get("all_rows", [])
    for row in all_rows[:8]:
        lines.append(f"| {row['strat']} | {row['w']} | {row['ratio_d']:.4f}x | {row['ratio_v']:.4f}x |\n")

    lines.append("\n## Fase 4 — Struttura cinquina\n")
    lines.append(f"- Tipi fascia distinti osservati: {f4.get('n_tipi', 0)}\n")
    lines.append(f"- Mutual Info I(T_t-1; T_t): {f4.get('mi', 0):.4f} (p={f4.get('mi_p', 1):.4f})\n")
    lines.append(f"- Somma media: {f4.get('somma_mean', 0):.1f} (attesa 140), sd {f4.get('somma_sd', 0):.1f}\n")
    lines.append(f"- Range (max-min) medio: {f4.get('range_mean', 0):.1f}\n")

    lines.append("\n## Fase 5 — Giorno della settimana\n")
    lines.append(f"- Giorni con |z somma|>2.69 (Bonferroni 7 test): {f5.get('sig_days', 0)}\n\n")
    lines.append("| DoW | N | μ somma | z |\n|---|---|---|---|\n")
    for d, v in sorted(f5.get("dow", {}).items()):
        lines.append(f"| {DOW_NAMES[d]} | {v['n']} | {v['mean_somma']:.1f} | {v['z']:+.2f} |\n")

    lines.append("\n## Fase 6 — Extra MillionDay\n")
    lines.append(f"- Outliers base |z|>3: {f6.get('outl_base_z3', 0)}/55\n")
    lines.append(f"- Outliers Extra |z|>3: {f6.get('outl_extra_z3', 0)}/55\n")
    lines.append(f"- EV marginale opzione Extra: EUR {f6.get('ev_extra_marginale', 0):.4f}\n")
    lines.append(f"- Costo opzione: EUR 1.00 -> **{'conviene' if f6.get('ev_extra_marginale', 0) > 1 else 'NON conviene'}** giocare l'Extra\n")

    lines.append("\n## Fase 7 — Multi-giocata ottimale\n\n")
    lines.append("| Strategia | Costo | P(≥2/5) | P(≥3/5) | EV ratio |\n")
    lines.append("|---|---|---|---|---|\n")
    for label, v in r.get("fase7", {}).items():
        lines.append(f"| {label} | {v['cost']:.0f}€ | {v['p_min2'] * 100:.2f}% | "
                     f"{v['p_min3'] * 100:.2f}% | {v['ev_ratio']:.4f}x |\n")

    lines.append("\n## Fase 8 — Cross-game VinciCasa\n")
    f8 = r.get("fase8", {})
    lines.append(f"- Status: {f8.get('status', 'n/a')}\n")
    if "reason" in f8:
        lines.append(f"- Motivo: {f8['reason']}\n")

    lines.append("\n## Fase 9 — Persistenza numerica\n\n")
    lines.append("### 9A Overlap lag 1\n")
    lines.append(f"- Mean overlap: {f9.get('overlap_mean', 0):.4f}  (atteso {f9.get('overlap_expected', 0):.4f})\n")
    lines.append(f"- Z: {f9.get('z_ov', 0):+.2f}\n\n")

    lines.append("### 9B Overlap per tipo di coppia\n\n")
    lines.append("| Tipo | N | Mean | Z |\n|---|---|---|---|\n")
    for key, label in [("intra_day", "13:00->20:30 (lag 1, stesso giorno)"),
                       ("inter_day", "20:30->13:00 (lag 1, giorno dopo)"),
                       ("same_hour_13", "13:00->13:00 (lag 2, same orario)"),
                       ("same_hour_20", "20:30->20:30 (lag 2, same orario)")]:
        v = f9.get(key)
        if v:
            lines.append(f"| {label} | {v['n']} | {v['mean']:.4f} | {v['z']:+.2f} |\n")

    lines.append("\n### 9E Strategia ripetitori\n\n")
    lines.append("| W | Ratio disc | Ratio val |\n|---|---|---|\n")
    for row in f9.get("rows_9e", []):
        lines.append(f"| {row['w']} | {row['ratio_d']:.4f}x | {row['ratio_v']:.4f}x |\n")

    lines.append("\n### 9G Catene di Markov\n")
    lines.append(f"- Numeri con persistenza positiva z>3.5: {f9.get('markov_persist', 0)}/55\n")
    lines.append(f"- Numeri con anti-persistenza z<-3.5: {f9.get('markov_anti', 0)}/55\n")

    # Verdetto finale
    lines.append("\n---\n\n## Verdetto finale\n\n")

    f0.get("ev_base", 0)
    bestratio = best.get("ratio_v", 0)
    pmin = f3.get("permutation_p", 1)
    bf = f3.get("bonferroni", 1)

    if bestratio > 1 and pmin < bf:
        verdict = (
            "**SEGNALE REALE RILEVATO** — la configurazione migliore e statisticamente "
            "significativa a Bonferroni. Raccomandabile investigare strategia operativa."
        )
    elif bestratio > 1 and pmin < 0.05:
        verdict = (
            "**SEGNALE BORDERLINE** — il miglior ratio supera 1 con p<0.05 raw ma non "
            "sopravvive a Bonferroni. Probabile artefatto del multiple testing. "
            "**MillionDay non appare battibile.**"
        )
    elif bestratio > 1:
        verdict = (
            "**NESSUN SEGNALE AFFIDABILE** — nessun ratio supera il breakeven con "
            "significativita statistica. **MillionDay non e battibile con le strategie testate.**"
        )
    else:
        verdict = (
            "**MILLIONDAY NON BATTIBILE** — tutti i ratio sono sotto 1. Nessuna strategia "
            "predittiva produce edge positivo. La strategia razionale e: giocare solo per "
            "divertimento, puntate minime, mai raddoppiare su perdite."
        )
    lines.append(verdict + "\n")

    markov_any = f9.get("markov_persist", 0) + f9.get("markov_anti", 0)
    if markov_any > 0:
        lines.append(f"\n**Attenzione**: {markov_any} numeri mostrano dipendenza Markov significativa dopo Bonferroni. Investigare manualmente.\n")

    REPORT_PATH.write_text("".join(lines))
    print(f"\n[REPORT] Generato: {REPORT_PATH}")


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    print("\n" + "=" * 80)
    print("MILLIONDAY — DEEP ANALYSIS")
    print("=" * 80)

    ext = _load()

    fase0(ext)
    fase1(ext)
    fase2(ext)
    fase3(ext)
    fase4(ext)
    fase5(ext)
    fase6(ext)
    fase7(ext)
    fase8(ext)
    fase9(ext)

    generate_report()

    print("\n" + "=" * 80)
    print("COMPLETATO")
    print("=" * 80)


if __name__ == "__main__":
    main()
