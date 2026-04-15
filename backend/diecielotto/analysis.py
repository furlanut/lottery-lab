from __future__ import annotations

"""10eLotto ogni 5 minuti — Analisi completa 33K+ estrazioni.

6 fasi: RNG, overlap, frequenza, composizione sestina, pattern orari, EV finale.
Target: 6 numeri + Extra (HE 9.94%, breakeven 1.11x).
"""

import logging
import random
import zlib
from collections import Counter
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

# ---------------------------------------------------------------------------
# Prize tables for 6 numeri
# ---------------------------------------------------------------------------
PREMI_BASE_6 = {3: 2.00, 4: 10.00, 5: 100.00, 6: 1000.00}
PREMI_EXTRA_6 = {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00}
COSTO = 2.0
EV_BASELINE = 1.80127  # analitico, confermato Monte Carlo


def _ev_giocata(pick6: set, drawn20: set, extra15: set) -> float:
    """Calcola vincita per una giocata 6+Extra."""
    mb = len(pick6 & drawn20)
    remaining = pick6 - drawn20
    me = len(remaining & extra15)
    return PREMI_BASE_6.get(mb, 0.0) + PREMI_EXTRA_6.get(me, 0.0)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def carica_dati() -> list[dict]:
    """Carica tutte le estrazioni ordinate cronologicamente."""
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
                "numeri": r.numeri,
                "extra": r.numeri_extra,
                "oro": r.numero_oro,
                "data": r.data,
                "ora": r.ora,
            }
            for r in rows
        ]
    finally:
        session.close()


# ===================================================================
# FASE 1 — RNG CERTIFICATION
# ===================================================================


def fase1_rng(estrazioni: list[dict]) -> bool:
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("FASE 1 — CERTIFICAZIONE RNG")
    print("=" * 70)

    all_pass = True

    # 1a. Chi-quadro uniformità
    freq = Counter()
    for e in estrazioni:
        for num in e["numeri"]:
            freq[num] += 1
    expected = n * 20.0 / 90.0
    chi2 = sum((freq.get(i, 0) - expected) ** 2 / expected for i in range(1, 91))
    df = 89
    z = (chi2 - df) / sqrt(2 * df)
    ok = abs(z) < 3.0
    all_pass &= ok
    print(f"\n  1. Chi-quadro uniformita: {'PASS' if ok else '*** FAIL ***'}")
    print(f"     chi2={chi2:.1f}, df={df}, z={z:.2f}")
    print(
        f"     freq attesa={expected:.0f}, min={min(freq.get(i, 0) for i in range(1, 91))}, "
        f"max={max(freq.get(i, 0) for i in range(1, 91))}"
    )

    # 1b. Runs test sulle somme dei 20 numeri
    somme = [sum(e["numeri"]) for e in estrazioni]
    mediana = sorted(somme)[n // 2]
    binary = [1 if s >= mediana else 0 for s in somme]
    runs = 1 + sum(1 for i in range(1, n) if binary[i] != binary[i - 1])
    n1 = sum(binary)
    n0 = n - n1
    if n1 > 0 and n0 > 0:
        mu_runs = 1 + 2 * n0 * n1 / n
        var_runs = 2 * n0 * n1 * (2 * n0 * n1 - n) / (n * n * (n - 1))
        z_runs = (runs - mu_runs) / sqrt(var_runs) if var_runs > 0 else 0
    else:
        z_runs = 99
    ok = abs(z_runs) < 3.0
    all_pass &= ok
    print(f"\n  2. Runs test (somme): {'PASS' if ok else '*** FAIL ***'}")
    print(f"     runs={runs}, attesi={mu_runs:.0f}, z={z_runs:.2f}")
    print(f"     somma media={sum(somme) / n:.1f}, mediana={mediana}")

    # 1c. Autocorrelazione lag 1-20 sulle somme
    mean_s = sum(somme) / n
    var_s = sum((s - mean_s) ** 2 for s in somme) / n
    max_ac = 0.0
    ac_values = {}
    for lag in range(1, 21):
        cov = sum((somme[i] - mean_s) * (somme[i + lag] - mean_s) for i in range(n - lag)) / (
            n - lag
        )
        ac = cov / var_s if var_s > 0 else 0
        ac_values[lag] = ac
        if abs(ac) > max_ac:
            max_ac = abs(ac)
    ok = max_ac < 0.03
    all_pass &= ok
    print(f"\n  3. Autocorrelazione somme: {'PASS' if ok else '*** FAIL ***'}")
    print(f"     max |r| = {max_ac:.5f} (soglia 0.03)")
    print(
        f"     lag 1={ac_values[1]:.5f}, lag 5={ac_values[5]:.5f}, "
        f"lag 10={ac_values[10]:.5f}, lag 20={ac_values[20]:.5f}"
    )

    # 1d. Distribuzione ritardi — CV atteso ≈ 1.0
    cvs = []
    for num in range(1, 91):
        gaps = []
        last = -1
        for i, e in enumerate(estrazioni):
            if num in e["numeri"]:
                if last >= 0:
                    gaps.append(i - last)
                last = i
        if len(gaps) > 20:
            mg = sum(gaps) / len(gaps)
            sg = sqrt(sum((g - mg) ** 2 for g in gaps) / len(gaps))
            cvs.append(sg / mg if mg > 0 else 0)
    mean_cv = sum(cvs) / len(cvs) if cvs else 0
    ok = abs(mean_cv - 1.0) < 0.15
    all_pass &= ok
    print(f"\n  4. Distribuzione ritardi: {'PASS' if ok else '*** FAIL ***'}")
    print(f"     CV medio={mean_cv:.4f} (atteso ~1.0)")
    print(f"     CV min={min(cvs):.3f}, max={max(cvs):.3f}")

    # 1e. Compressibilità
    real_bytes = ",".join(str(n) for e in estrazioni for n in e["numeri"]).encode()
    real_compressed = len(zlib.compress(real_bytes, 9))
    real_ratio = real_compressed / len(real_bytes)

    random.seed(42)
    rand_ratios = []
    for _ in range(200):
        fake = []
        for _ in range(n):
            fake.extend(sorted(random.sample(range(1, 91), 20)))
        fb = ",".join(str(x) for x in fake).encode()
        rand_ratios.append(len(zlib.compress(fb, 9)) / len(fb))
    mean_rand = sum(rand_ratios) / len(rand_ratios)
    std_rand = sqrt(sum((r - mean_rand) ** 2 for r in rand_ratios) / len(rand_ratios))
    z_comp = (real_ratio - mean_rand) / std_rand if std_rand > 0 else 0

    ok = abs(z_comp) < 3.0
    all_pass &= ok
    print(f"\n  5. Compressibilita: {'PASS' if ok else '*** FAIL ***'}")
    print(f"     ratio reale={real_ratio:.4f}, random medio={mean_rand:.4f}")
    print(f"     z={z_comp:.2f}")

    verdict = "5/5 PASS — RNG certificato" if all_pass else "*** FAIL — APPROFONDIRE ***"
    print(f"\n  VERDETTO RNG: {verdict}")
    return all_pass


# ===================================================================
# FASE 2 — PERSISTENZA E OVERLAP
# ===================================================================


def fase2_overlap(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("FASE 2 — PERSISTENZA E OVERLAP")
    print("=" * 70)

    expected = 20 * 20 / 90  # 4.444

    for lag in [1, 2, 5, 10, 50, 100, 288]:
        if lag >= n:
            continue
        overlaps = []
        for i in range(lag, n):
            s1 = set(estrazioni[i - lag]["numeri"])
            s2 = set(estrazioni[i]["numeri"])
            overlaps.append(len(s1 & s2))
        mean_ov = sum(overlaps) / len(overlaps)
        std_ov = sqrt(sum((x - mean_ov) ** 2 for x in overlaps) / len(overlaps))
        se = std_ov / sqrt(len(overlaps))
        z = (mean_ov - expected) / se if se > 0 else 0
        sig = "*" if abs(z) > 2.0 else ""
        print(
            f"  Lag {lag:>4}: overlap={mean_ov:.4f} ± {se:.4f}  "
            f"(atteso {expected:.3f})  z={z:+.2f} {sig}"
        )

    print(f"\n  Errore standard su lag 1: ~{std_ov / sqrt(n - 1):.4f} numeri")
    print(f"  Con {n} estrazioni, deviazioni di 0.02+ sono rilevabili.")


# ===================================================================
# FASE 3 — SEGNALE FREQUENZA A BREVE TERMINE
# ===================================================================


def fase3_frequenza(estrazioni: list[dict]) -> dict:
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 70)
    print("FASE 3 — SEGNALE FREQUENZA (top 6 hot numbers)")
    print("=" * 70)

    # Match atteso per 6 random su 20/90
    e_match = 6 * 20 / 90  # 1.333
    print(f"\n  Match atteso (6 random su 20/90): {e_match:.3f}")
    print(f"  EV baseline: EUR {EV_BASELINE:.4f} su EUR {COSTO:.2f}")
    print()

    best = {"window": 0, "val_ratio": 0.0}

    header = (
        f"  {'W':>5}  {'Match D':>8}  {'Match V':>8}  "
        f"{'EV D':>8}  {'EV V':>8}  {'Rat D':>7}  {'Rat V':>7}"
    )
    print(header)
    print("  " + "-" * 72)

    for w in [3, 5, 10, 20, 50]:
        ev_disc, ev_val = 0.0, 0.0
        match_disc, match_val = 0.0, 0.0
        n_disc, n_val = 0, 0

        for i in range(w, n):
            freq = Counter()
            for j in range(i - w, i):
                for num in estrazioni[j]["numeri"]:
                    freq[num] += 1
            top6 = {num for num, _ in freq.most_common(6)}

            drawn = set(estrazioni[i]["numeri"])
            extra = set(estrazioni[i]["extra"])

            mb = len(top6 & drawn)
            remaining = top6 - drawn
            me = len(remaining & extra)
            ev = PREMI_BASE_6.get(mb, 0.0) + PREMI_EXTRA_6.get(me, 0.0)

            if i < half:
                ev_disc += ev
                match_disc += mb
                n_disc += 1
            else:
                ev_val += ev
                match_val += mb
                n_val += 1

        avg_match_d = match_disc / n_disc if n_disc else 0
        avg_match_v = match_val / n_val if n_val else 0
        avg_ev_d = ev_disc / n_disc if n_disc else 0
        avg_ev_v = ev_val / n_val if n_val else 0
        ratio_d = avg_ev_d / EV_BASELINE
        ratio_v = avg_ev_v / EV_BASELINE

        print(
            f"  {w:>5}  {avg_match_d:>10.4f}  {avg_match_v:>10.4f}  "
            f"{avg_ev_d:>9.4f}  {avg_ev_v:>9.4f}  {ratio_d:>7.4f}x  {ratio_v:>7.4f}x"
        )

        if ratio_v > best["val_ratio"]:
            best = {
                "window": w,
                "val_ratio": ratio_v,
                "val_ev": avg_ev_v,
                "val_match": avg_match_v,
                "disc_ratio": ratio_d,
            }

    # Permutation test per il miglior segnale
    w = best["window"]
    if w > 0:
        log.info("Permutation test per W=%d (1000 shuffle)...", w)
        observed_ev = best["val_ev"]
        n_perm = 1000
        count_ge = 0
        val_indices = list(range(half, n))
        random.seed(42)

        for _ in range(n_perm):
            random.shuffle(val_indices)
            perm_ev = 0.0
            for idx, i in enumerate(val_indices[: min(500, len(val_indices))]):
                freq = Counter()
                for j in range(i - w, i):
                    for num in estrazioni[j]["numeri"]:
                        freq[num] += 1
                # Shuffle: usa i top6 della posizione originale ma confronta con estrazione shuffled
                top6 = {num for num, _ in freq.most_common(6)}
                target_i = val_indices[(idx + 137) % len(val_indices)]  # pseudo-random target
                drawn = set(estrazioni[target_i]["numeri"])
                extra = set(estrazioni[target_i]["extra"])
                perm_ev += _ev_giocata(top6, drawn, extra)
            perm_avg = perm_ev / min(500, len(val_indices))
            if perm_avg >= observed_ev:
                count_ge += 1

        p_value = count_ge / n_perm
        print(f"\n  Permutation test (W={w}): p-value = {p_value:.4f}")

    return best


# ===================================================================
# FASE 4 — COMPOSIZIONE SESTINA
# ===================================================================


def fase4_composizione(estrazioni: list[dict]):
    n = len(estrazioni)
    half = n // 2
    print("\n" + "=" * 70)
    print("FASE 4 — COMPOSIZIONE SESTINA")
    print("=" * 70)

    strategies = {}

    for i in range(20, n):
        freq = Counter()
        for j in range(i - 20, i):
            for num in estrazioni[j]["numeri"]:
                freq[num] += 1

        # Strategia 1: Top 6 dispersi (già testato, ripeto per confronto)
        dispersa = {num for num, _ in freq.most_common(6)}

        # Strategia 2: Cluster vicini — numero più frequente + 5 vicini
        best_num = freq.most_common(1)[0][0]
        candidates = sorted(range(1, 91), key=lambda x: (abs(x - best_num), -freq.get(x, 0)))
        cluster = set(candidates[:6])

        # Strategia 3: Per decine — 1 dalla decina più calda di 6 decine
        decade_freq = Counter()
        for num, f in freq.items():
            decade_freq[(num - 1) // 10] += f
        top_decades = [d for d, _ in decade_freq.most_common(6)]
        per_decine = set()
        for dec in top_decades:
            nums_in_dec = [
                (num, freq.get(num, 0))
                for num in range(dec * 10 + 1, dec * 10 + 11)
                if 1 <= num <= 90
            ]
            if nums_in_dec:
                per_decine.add(max(nums_in_dec, key=lambda x: x[1])[0])
        # Pad if needed
        if len(per_decine) < 6:
            for num, _ in freq.most_common():
                per_decine.add(num)
                if len(per_decine) >= 6:
                    break

        drawn = set(estrazioni[i]["numeri"])
        extra = set(estrazioni[i]["extra"])

        phase = "disc" if i < half else "val"

        for name, pick in [("dispersa", dispersa), ("cluster", cluster), ("decine", per_decine)]:
            if name not in strategies:
                strategies[name] = {"disc_ev": 0, "val_ev": 0, "disc_n": 0, "val_n": 0}
            ev = _ev_giocata(pick, drawn, extra)
            strategies[name][f"{phase}_ev"] += ev
            strategies[name][f"{phase}_n"] += 1

    print(f"\n  {'Strategia':<15}  {'EV disc':>9}  {'EV val':>9}  {'Ratio D':>8}  {'Ratio V':>8}")
    print("  " + "-" * 55)

    for name in ["dispersa", "cluster", "decine"]:
        s = strategies[name]
        ev_d = s["disc_ev"] / s["disc_n"] if s["disc_n"] else 0
        ev_v = s["val_ev"] / s["val_n"] if s["val_n"] else 0
        print(
            f"  {name:<15}  {ev_d:>9.4f}  {ev_v:>9.4f}  "
            f"{ev_d / EV_BASELINE:>7.4f}x  {ev_v / EV_BASELINE:>7.4f}x"
        )


# ===================================================================
# FASE 5 — PATTERN TEMPORALI INTRA-GIORNALIERI
# ===================================================================


def fase5_pattern_orari(estrazioni: list[dict]):
    print("\n" + "=" * 70)
    print("FASE 5 — PATTERN TEMPORALI INTRA-GIORNALIERI")
    print("=" * 70)

    # Raggruppa per ora
    by_hour: dict[int, list[dict]] = {}
    for e in estrazioni:
        h = e["ora"].hour
        if h not in by_hour:
            by_hour[h] = []
        by_hour[h].append(e)

    print(f"\n  {'Ora':>4}  {'N':>6}  {'Somma':>10}  {'Overlap':>10}  {'MaxDev%':>10}")
    print("  " + "-" * 60)

    hour_stats = {}
    for h in sorted(by_hour.keys()):
        group = by_hour[h]
        ng = len(group)

        # Somma media
        somme = [sum(e["numeri"]) for e in group]
        mean_somma = sum(somme) / ng

        # Frequenze per quest'ora
        freq_h = Counter()
        for e in group:
            for num in e["numeri"]:
                freq_h[num] += 1
        expected_h = ng * 20 / 90
        max_dev = max(abs(freq_h.get(i, 0) - expected_h) / expected_h for i in range(1, 91))

        # Overlap tra estrazioni consecutive in quest'ora
        overlaps = []
        for i in range(1, ng):
            s1 = set(group[i - 1]["numeri"])
            s2 = set(group[i]["numeri"])
            overlaps.append(len(s1 & s2))
        mean_ov = sum(overlaps) / len(overlaps) if overlaps else 0

        hour_stats[h] = {"n": ng, "somma": mean_somma, "overlap": mean_ov, "max_dev": max_dev}
        print(f"  {h:>4}  {ng:>6}  {mean_somma:>10.1f}  {mean_ov:>10.3f}  {max_dev:>9.2f}%")

    # Chi-quadro per uniformità tra ore
    somme_per_ora = [hour_stats[h]["somma"] for h in sorted(hour_stats)]
    grand_mean = sum(somme_per_ora) / len(somme_per_ora)
    var_between = sum((s - grand_mean) ** 2 for s in somme_per_ora) / len(somme_per_ora)
    print(f"\n  Varianza somma tra ore: {var_between:.2f} (dovrebbe essere ~0)")

    overlaps_by_hour = [hour_stats[h]["overlap"] for h in sorted(hour_stats)]
    grand_ov = sum(overlaps_by_hour) / len(overlaps_by_hour)
    var_ov = sum((o - grand_ov) ** 2 for o in overlaps_by_hour) / len(overlaps_by_hour)
    print(f"  Varianza overlap tra ore: {var_ov:.6f} (dovrebbe essere ~0)")

    # Fascia oraria migliore/peggiore per overlap
    best_h = max(hour_stats, key=lambda h: hour_stats[h]["overlap"])
    worst_h = min(hour_stats, key=lambda h: hour_stats[h]["overlap"])
    print(f"  Overlap max: ore {best_h}:00 ({hour_stats[best_h]['overlap']:.3f})")
    print(f"  Overlap min: ore {worst_h}:00 ({hour_stats[worst_h]['overlap']:.3f})")
    print("  Atteso: 4.444")


# ===================================================================
# FASE 6 — EV FINALE E STRATEGIA
# ===================================================================


def fase6_verdetto(estrazioni: list[dict], best_signal: dict):
    print("\n" + "=" * 70)
    print("FASE 6 — EV FINALE E VERDETTO")
    print("=" * 70)

    ratio = best_signal.get("val_ratio", 0)
    val_ev = best_signal.get("val_ev", 0)
    w = best_signal.get("window", 0)

    print(f"\n  Miglior segnale: hot numbers W={w}")
    print(f"  EV validazione: EUR {val_ev:.4f} / giocata EUR {COSTO:.2f}")
    print(f"  EV baseline:    EUR {EV_BASELINE:.4f}")
    print(f"  Ratio:          {ratio:.4f}x")
    print("  Breakeven:      1.1103x")

    if ratio >= 1.11:
        print(f"\n  *** EDGE TROVATO! Ratio {ratio:.4f}x > breakeven 1.11x ***")
        print(f"  Profitto atteso: EUR {val_ev - COSTO:.4f}/giocata")
        print(f"  Su 288 giocate/giorno: EUR {(val_ev - COSTO) * 288:.2f}/giorno")
    elif ratio >= 1.05:
        print(f"\n  Segnale promettente ({ratio:.4f}x) ma sotto breakeven.")
        print(f"  Riduzione house edge: da 9.94% a {(1 - ratio * EV_BASELINE / COSTO) * 100:.2f}%")
    elif ratio >= 1.00:
        print(f"\n  Segnale debole ({ratio:.4f}x). Nessun edge pratico.")
    else:
        print(f"\n  Nessun segnale ({ratio:.4f}x). RNG perfettamente random.")

    # Confronto con altri giochi
    print("\n  " + "-" * 50)
    print("  CONFRONTO LOTTERY LAB:")
    print(f"  {'Gioco':<20}  {'HE':>8}  {'Breakeven':>10}  {'Segnale':>10}")
    print("  " + "-" * 50)
    print(f"  {'Lotto ambo V6':<20}  {'37.6%':>8}  {'1.60x':>10}  {'1.18x':>10}")
    print(f"  {'VinciCasa top5':<20}  {'37.3%':>8}  {'1.60x':>10}  {'1.22x':>10}")
    print(f"  {'10eLotto 6+Extra':<20}  {'9.94%':>8}  {'1.11x':>10}  {f'{ratio:.2f}x':>10}")
    print()


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 70)
    print("10eLOTTO OGNI 5 MINUTI — ANALISI COMPLETA")
    print("=" * 70)

    log.info("Caricamento dati...")
    estrazioni = carica_dati()
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")
    print(f"Periodo: {estrazioni[0]['data']} — {estrazioni[-1]['data']}")
    n_extra = sum(1 for e in estrazioni if e["extra"])
    print(f"Con Extra: {n_extra} ({n_extra / n * 100:.1f}%)")

    # FASE 1
    rng_ok = fase1_rng(estrazioni)
    if not rng_ok:
        print("\n*** RNG NON CERTIFICATO — APPROFONDIRE PRIMA DI PROSEGUIRE ***")

    # FASE 2
    fase2_overlap(estrazioni)

    # FASE 3
    best = fase3_frequenza(estrazioni)

    # FASE 4
    fase4_composizione(estrazioni)

    # FASE 5
    fase5_pattern_orari(estrazioni)

    # FASE 6
    fase6_verdetto(estrazioni, best)


if __name__ == "__main__":
    main()
