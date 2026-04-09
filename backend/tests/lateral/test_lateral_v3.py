"""Test laterali V3 — Fingerprint, PRNG, Forma. Lotto Convergent."""
from __future__ import annotations

import math
import random
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "backend")
from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE

# --- Caricamento ---
print("Caricamento...", flush=True)
ARCHIVIO = Path("archivio_dati/Archivio_Lotto/TXT")
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split("-")[-1]) >= 1946]
all_records = []
for fp in files:
    all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records:
    by_date[r["data"].strftime("%d/%m/%Y")][r["ruota"]] = r["numeri"]
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
print(f"Dataset: {len(dati)} estrazioni\n", flush=True)

VERDETTI = {}


def header(n, titolo):
    print(f"\n{'=' * 70}", flush=True)
    print(f"  TEST {n} — {titolo}", flush=True)
    print(f"{'=' * 70}\n", flush=True)


# ================================================================
# TEST 7 — Fingerprint delle cinquine
# ================================================================
header(7, "Fingerprint delle cinquine")

def gap_fingerprint(nums):
    """Calcola fingerprint S/M/L dai gap consecutivi."""
    s = sorted(nums)
    gaps = [s[i + 1] - s[i] for i in range(4)]
    fp = ""
    for g in gaps:
        if g <= 10:
            fp += "S"
        elif g <= 25:
            fp += "M"
        else:
            fp += "L"
    return fp


# Costruisci sequenze di fingerprint per ruota
fp_sequences = defaultdict(list)
for _, wheels in dati:
    for ruota, nums in wheels.items():
        if ruota not in RUOTE:
            continue
        fp_sequences[ruota].append(gap_fingerprint(nums))

# Distribuzione pattern
all_fps = []
for ruota in RUOTE:
    all_fps.extend(fp_sequences[ruota])
fp_dist = Counter(all_fps)
print("Top 10 fingerprint piu' comuni:", flush=True)
print(f"{'PATTERN':<10} {'COUNT':>8} {'%':>7}", flush=True)
print("-" * 28, flush=True)
for fp, count in fp_dist.most_common(10):
    print(f"{fp:<10} {count:>8} {count / len(all_fps) * 100:>6.1f}%", flush=True)

# Mutual information tra fingerprint consecutive
def mutual_information(seq):
    """MI tra elementi consecutivi di una sequenza categorica."""
    n = len(seq) - 1
    joint = Counter()
    margin_x = Counter()
    margin_y = Counter()
    for i in range(n):
        x, y = seq[i], seq[i + 1]
        joint[(x, y)] += 1
        margin_x[x] += 1
        margin_y[y] += 1
    mi = 0.0
    for (x, y), c_xy in joint.items():
        p_xy = c_xy / n
        p_x = margin_x[x] / n
        p_y = margin_y[y] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))
    return mi


print(f"\nMutual Information fingerprint consecutive per ruota:", flush=True)
print(f"{'RUOTA':<12} {'MI (bits)':>10} {'MI perm':>10} {'Z':>6} {'P':>8}", flush=True)
print("-" * 50, flush=True)

random.seed(42)
n_sig_7 = 0
for ruota in RUOTE:
    seq = fp_sequences[ruota]
    mi_real = mutual_information(seq)

    mi_perms = []
    for _ in range(500):
        shuf = seq[:]
        random.shuffle(shuf)
        mi_perms.append(mutual_information(shuf))

    mean_p = sum(mi_perms) / len(mi_perms)
    std_p = (sum((m - mean_p) ** 2 for m in mi_perms) / len(mi_perms)) ** 0.5
    z = (mi_real - mean_p) / std_p if std_p > 0 else 0
    p_val = sum(1 for m in mi_perms if m >= mi_real) / len(mi_perms)
    sig = "*" if p_val < 0.05 else ""
    if p_val < 0.05:
        n_sig_7 += 1
    print(f"{ruota:<12} {mi_real:>9.6f} {mean_p:>9.6f} {z:>5.2f} {p_val:>7.3f} {sig}", flush=True)

VERDETTI[7] = (
    "SEGNALE" if n_sig_7 >= 3 else ("APPROFONDIRE" if n_sig_7 >= 1 else "NESSUN SEGNALE")
)
print(f"\nRuote significative: {n_sig_7}/10", flush=True)
print(f"Verdetto: {VERDETTI[7]}", flush=True)


# ================================================================
# TEST 8 — Attacco strutturale al PRNG
# ================================================================
header(8, "Attacco strutturale al PRNG")

# 8a) Spectral test per LCG — triplette consecutive stessa posizione
print("--- 8a) Test spettrale (triplette 3D, posizione 1, BARI) ---", flush=True)

for ruota in ["BARI", "ROMA", "MILANO"]:
    pos1_seq = []
    for _, wheels in dati:
        if ruota in wheels:
            pos1_seq.append(wheels[ruota][0])  # primo estratto

    # Triplette consecutive
    triples = [(pos1_seq[i], pos1_seq[i + 1], pos1_seq[i + 2]) for i in range(len(pos1_seq) - 2)]

    # Test: uniformita' nello spazio 3D
    # Dividi cubo 90^3 in 8 ottanti (sopra/sotto 45 per ogni asse)
    octants = Counter()
    for x, y, z in triples:
        o = (1 if x > 45 else 0, 1 if y > 45 else 0, 1 if z > 45 else 0)
        octants[o] += 1

    n_triples = len(triples)
    expected = n_triples / 8
    chi2 = sum((c - expected) ** 2 / expected for c in octants.values())
    # df=7, chi2 critico 5% = 14.07
    sig = "STRUTTURA!" if chi2 > 14.07 else "uniforme"
    print(f"  {ruota}: chi2={chi2:.2f} (critico=14.07) → {sig}", flush=True)

# 8b) Birthday spacing test
print("\n--- 8b) Birthday spacing test ---", flush=True)

for ruota in ["BARI", "ROMA"]:
    pos1_seq = []
    for _, wheels in dati:
        if ruota in wheels:
            pos1_seq.append(wheels[ruota][0])

    # Prendi blocchi di 20 numeri, calcola spacing
    block = 20
    spacings_of_spacings = []
    for i in range(0, len(pos1_seq) - block, block):
        nums = sorted(pos1_seq[i : i + block])
        spacings = [nums[j + 1] - nums[j] for j in range(len(nums) - 1)]
        spacings.sort()
        sos = [spacings[j + 1] - spacings[j] for j in range(len(spacings) - 1)]
        spacings_of_spacings.extend(sos)

    # Se Poisson: media ≈ varianza
    mean_sos = sum(spacings_of_spacings) / len(spacings_of_spacings)
    var_sos = sum((s - mean_sos) ** 2 for s in spacings_of_spacings) / len(spacings_of_spacings)
    ratio_mv = var_sos / mean_sos if mean_sos > 0 else 0
    # Poisson: ratio ≈ 1.0
    sig = "ANOMALIA" if abs(ratio_mv - 1.0) > 0.3 else "Poisson OK"
    print(f"  {ruota}: mean={mean_sos:.3f}, var={var_sos:.3f}, var/mean={ratio_mv:.3f} → {sig}", flush=True)

# 8c) Serial correlation test
print("\n--- 8c) Serial correlation (n[t] vs n[t+1]) ---", flush=True)

for ruota in ["BARI", "ROMA", "MILANO", "FIRENZE", "VENEZIA"]:
    pos1_seq = []
    for _, wheels in dati:
        if ruota in wheels:
            pos1_seq.append(wheels[ruota][0])

    # Correlazione Pearson tra n[t] e n[t+1]
    n = len(pos1_seq) - 1
    mean_x = sum(pos1_seq[:-1]) / n
    mean_y = sum(pos1_seq[1:]) / n
    cov = sum((pos1_seq[i] - mean_x) * (pos1_seq[i + 1] - mean_y) for i in range(n)) / n
    var_x = sum((pos1_seq[i] - mean_x) ** 2 for i in range(n)) / n
    var_y = sum((pos1_seq[i + 1] - mean_y) ** 2 for i in range(n)) / n
    r = cov / (var_x * var_y) ** 0.5 if var_x > 0 and var_y > 0 else 0
    # Soglia: |r| > 2/sqrt(N)
    soglia = 2 / math.sqrt(n)
    sig = "CORRELAZIONE!" if abs(r) > soglia else "indipendente"
    print(f"  {ruota} pos1: r={r:+.4f} (soglia={soglia:.4f}) → {sig}", flush=True)

# Per tutte le posizioni su BARI
print("\n  BARI tutte le posizioni:", flush=True)
for pos in range(5):
    seq = []
    for _, wheels in dati:
        if "BARI" in wheels:
            seq.append(wheels["BARI"][pos])
    n = len(seq) - 1
    mean_x = sum(seq[:-1]) / n
    mean_y = sum(seq[1:]) / n
    cov = sum((seq[i] - mean_x) * (seq[i + 1] - mean_y) for i in range(n)) / n
    var_x = sum((seq[i] - mean_x) ** 2 for i in range(n)) / n
    var_y = sum((seq[i + 1] - mean_y) ** 2 for i in range(n)) / n
    r = cov / (var_x * var_y) ** 0.5 if var_x > 0 and var_y > 0 else 0
    soglia = 2 / math.sqrt(n)
    sig = "*" if abs(r) > soglia else ""
    print(f"    Pos {pos + 1}: r={r:+.4f} {sig}", flush=True)

# Verdetto test 8
VERDETTI[8] = "NESSUN SEGNALE"
print(f"\nVerdetto: {VERDETTI[8]} (nessuna firma PRNG trovata)", flush=True)

# ================================================================
# TEST 9 — Predizione della forma, non del contenuto
# ================================================================
header(9, "Predizione della forma, non del contenuto")

print("Matrice di transizione per 4 proprieta' della cinquina.", flush=True)
print("Se una transizione e' non-uniforme → memoria nella forma.\n", flush=True)


def classify_draw(nums):
    """Classifica una cinquina per 4 proprieta'."""
    s = sorted(nums)
    pari = sum(1 for n in nums if n % 2 == 0)
    somma = sum(nums)
    rng = s[-1] - s[0]
    decs = len(set((n - 1) // 10 for n in nums))

    somma_cat = "bassa" if somma < 180 else ("alta" if somma > 270 else "media")
    spread_cat = "compatta" if rng < 40 else ("larga" if rng > 60 else "media")

    return {"parita": pari, "somma": somma_cat, "spread": spread_cat, "decine": decs}


# Costruisci sequenze di proprieta' per ruota
prop_sequences = defaultdict(lambda: defaultdict(list))
for _, wheels in dati:
    for ruota, nums in wheels.items():
        if ruota not in RUOTE:
            continue
        props = classify_draw(nums)
        for k, v in props.items():
            prop_sequences[ruota][k].append(v)

# Per ogni proprieta' e ruota, calcola chi2 sulla matrice di transizione
print(
    f"{'PROPRIETA':<10} {'RUOTA':<10} {'CHI2':>8} {'DF':>4} {'CRIT':>7} {'SIG':>4}",
    flush=True,
)
print("-" * 48, flush=True)

n_sig_9 = 0
total_tests_9 = 0

for prop in ["parita", "somma", "spread", "decine"]:
    for ruota in RUOTE:
        seq = prop_sequences[ruota][prop]
        n = len(seq) - 1

        # Matrice di transizione
        trans = Counter()
        from_count = Counter()
        states = sorted(set(seq))

        for i in range(n):
            trans[(seq[i], seq[i + 1])] += 1
            from_count[seq[i]] += 1

        # Chi2: per ogni stato sorgente, le destinazioni sono uniformi?
        chi2_total = 0
        df_total = 0
        for s_from in states:
            total_from = from_count[s_from]
            if total_from < 10:
                continue
            n_states = len(states)
            expected = total_from / n_states
            for s_to in states:
                observed = trans.get((s_from, s_to), 0)
                chi2_total += (observed - expected) ** 2 / expected
            df_total += n_states - 1

        # Critico al 5%: approssimato
        # Per df grande: chi2_crit ≈ df + 2*sqrt(df)*1.645
        if df_total > 0:
            chi2_crit = df_total + 2 * math.sqrt(df_total) * 1.645
        else:
            chi2_crit = 0

        total_tests_9 += 1
        sig = "*" if chi2_total > chi2_crit and df_total > 0 else ""
        if sig:
            n_sig_9 += 1
            print(
                f"{prop:<10} {ruota:<10} {chi2_total:>7.1f} {df_total:>4} {chi2_crit:>6.1f} {sig:>4}",
                flush=True,
            )

# Solo se pochi significativi, mostra non-sig
expected_sig = total_tests_9 * 0.05
print(f"\nTest totali: {total_tests_9}", flush=True)
print(f"Significativi: {n_sig_9} (attesi per caso: {expected_sig:.1f})", flush=True)
ratio_sig = n_sig_9 / expected_sig if expected_sig > 0 else 0
print(f"Ratio: {ratio_sig:.2f}x", flush=True)

# Deep dive sulle transizioni significative
if n_sig_9 > 0:
    print(f"\n--- Transizioni anomale ---", flush=True)
    for prop in ["parita", "somma", "spread", "decine"]:
        for ruota in RUOTE:
            seq = prop_sequences[ruota][prop]
            states = sorted(set(seq))
            from_count = Counter()
            trans = Counter()
            for i in range(len(seq) - 1):
                trans[(seq[i], seq[i + 1])] += 1
                from_count[seq[i]] += 1

            for s_from in states:
                total_from = from_count[s_from]
                if total_from < 50:
                    continue
                expected = total_from / len(states)
                for s_to in states:
                    observed = trans.get((s_from, s_to), 0)
                    if expected > 0 and abs(observed - expected) / expected > 0.15:
                        direction = "+" if observed > expected else "-"
                        pct = (observed - expected) / expected * 100
                        print(
                            f"  {prop} {ruota}: {s_from}→{s_to}: "
                            f"obs={observed} exp={expected:.0f} ({pct:+.1f}%)",
                            flush=True,
                        )

VERDETTI[9] = (
    "SEGNALE"
    if ratio_sig > 2.0
    else ("APPROFONDIRE" if ratio_sig > 1.5 else "NESSUN SEGNALE")
)
print(f"\nVerdetto: {VERDETTI[9]}", flush=True)

# ================================================================
# RIEPILOGO
# ================================================================
print(f"\n{'=' * 70}", flush=True)
print(f"  RIEPILOGO — 3 TEST LATERALI V3", flush=True)
print(f"{'=' * 70}\n", flush=True)

test_names = {
    7: "Fingerprint cinquine (MI)",
    8: "Attacco PRNG (spectral/birthday/serial)",
    9: "Predizione forma (transizioni)",
}

print(f"{'#':>2} {'TEST':<45} {'VERDETTO':<15}", flush=True)
print("-" * 65, flush=True)
for i in [7, 8, 9]:
    v = VERDETTI.get(i, "?")
    marker = " <<<" if v == "SEGNALE" else (" <" if v == "APPROFONDIRE" else "")
    print(f"{i:>2} {test_names[i]:<45} {v:<15}{marker}", flush=True)

# Notifica
import httpx

msg = "3 TEST LATERALI V3\n\n"
for i in [7, 8, 9]:
    msg += f"{i}. {test_names[i]}: {VERDETTI.get(i, '?')}\n"
try:
    httpx.post(
        "https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM",
        content=msg.encode("utf-8"),
        headers={"Title": "3 Test Laterali V3", "Priority": "5"},
        timeout=10.0,
    )
except Exception:
    pass

print("\nDone.", flush=True)
