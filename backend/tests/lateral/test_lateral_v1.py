"""Test laterali non convenzionali — Lotto Convergent.

6 test che esplorano angoli mai toccati nella ricerca.
Usa dati dall'archivio TXT (no DB PostgreSQL richiesto).
"""
from __future__ import annotations

import math
import random
import sys
import zlib
import bz2
import lzma
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "backend")
from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist

# --- Caricamento dati ---
print("Caricamento archivio...", flush=True)
ARCHIVIO = Path("archivio_dati/Archivio_Lotto/TXT")
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split("-")[-1]) >= 1946]
all_records = []
for fp in files:
    all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records:
    by_date[r["data"].strftime("%d/%m/%Y")][r["ruota"]] = r["numeri"]
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
print(f"Dataset: {len(dati)} estrazioni ({dati[0][0]} - {dati[-1][0]})\n", flush=True)

VERDETTI = {}


def header(n, titolo):
    print(f"\n{'=' * 70}", flush=True)
    print(f"  TEST {n} — {titolo}", flush=True)
    print(f"{'=' * 70}\n", flush=True)


# ================================================================
# TEST 1 — Compressibilita' di Kolmogorov
# ================================================================
header(1, "Compressibilita' di Kolmogorov")
print("Se la sequenza reale si comprime meglio del random → pattern nascosto.", flush=True)
print()

random.seed(42)
N_RANDOM = 100

ruota_ratios = {}
ruota_pvalues = {}

for ruota in RUOTE:
    # Costruisci sequenza reale
    seq_reale = []
    for _, wheels in dati:
        if ruota in wheels:
            seq_reale.extend(wheels[ruota])

    raw = bytes(seq_reale)

    # Comprimi con 3 algoritmi
    real_ratios = {}
    for name, compressor in [("zlib", zlib.compress), ("bz2", bz2.compress), ("lzma", lzma.compress)]:
        compressed = compressor(raw)
        real_ratios[name] = len(compressed) / len(raw)

    # Genera 100 sequenze random
    n_draws = len(seq_reale) // 5
    random_ratios = {k: [] for k in real_ratios}

    for _ in range(N_RANDOM):
        rand_seq = []
        for _ in range(n_draws):
            rand_seq.extend(random.sample(range(1, 91), 5))
        rand_raw = bytes(rand_seq)
        for name, compressor in [("zlib", zlib.compress), ("bz2", bz2.compress), ("lzma", lzma.compress)]:
            compressed = compressor(rand_raw)
            random_ratios[name].append(len(compressed) / len(rand_raw))

    # P-value: quante random si comprimono meglio del reale
    best_algo = "bz2"  # tipicamente il piu' discriminante
    real_r = real_ratios[best_algo]
    rand_rs = random_ratios[best_algo]
    p_val = sum(1 for r in rand_rs if r <= real_r) / len(rand_rs)
    mean_rand = sum(rand_rs) / len(rand_rs)

    ruota_ratios[ruota] = real_r
    ruota_pvalues[ruota] = p_val

print(f"{'RUOTA':<12} {'RATIO REALE':>12} {'RATIO RANDOM':>13} {'DIFF%':>7} {'P-VALUE':>9}", flush=True)
print("-" * 55, flush=True)

any_signal = False
for ruota in RUOTE:
    real_r = ruota_ratios[ruota]
    # Ricalcola mean random
    seq_reale = []
    for _, wheels in dati:
        if ruota in wheels:
            seq_reale.extend(wheels[ruota])
    n_draws = len(seq_reale) // 5
    rand_rs = []
    for _ in range(30):  # quick
        rand_seq = bytes(random.sample(range(1, 91), 5) * n_draws)
        rand_rs.append(len(bz2.compress(bytes(rand_seq[:len(seq_reale)]))) / len(seq_reale))
    mean_r = sum(rand_rs) / len(rand_rs)
    diff = (real_r - mean_r) / mean_r * 100
    p = ruota_pvalues[ruota]
    marker = " <<<" if p < 0.05 else ""
    if p < 0.05:
        any_signal = True
    print(f"{ruota:<12} {real_r:>11.4f} {mean_r:>12.4f} {diff:>+6.1f}% {p:>8.3f}{marker}", flush=True)

VERDETTI[1] = "APPROFONDIRE" if any_signal else "NESSUN SEGNALE"
print(f"\nVerdetto: {VERDETTI[1]}", flush=True)

# ================================================================
# TEST 2 — Autocorrelazione sulle meta-proprieta'
# ================================================================
header(2, "Autocorrelazione sulle meta-proprieta'")
print("Autocorrelazione su somma, range, pari, decine, gap, std per ruota.", flush=True)
print()

max_lag = 20
n_draws_per_ruota = defaultdict(int)
meta_series = defaultdict(lambda: defaultdict(list))

for _, wheels in dati:
    for ruota, nums in wheels.items():
        if ruota not in RUOTE:
            continue
        n_draws_per_ruota[ruota] += 1
        s = sorted(nums)
        meta_series[ruota]["somma"].append(sum(nums))
        meta_series[ruota]["range"].append(s[-1] - s[0])
        meta_series[ruota]["pari"].append(sum(1 for n in nums if n % 2 == 0))
        meta_series[ruota]["decine"].append(len(set((n - 1) // 10 for n in nums)))
        meta_series[ruota]["gap_max"].append(max(s[i + 1] - s[i] for i in range(4)))
        mean_n = sum(nums) / 5
        meta_series[ruota]["std"].append((sum((n - mean_n) ** 2 for n in nums) / 5) ** 0.5)


def autocorr(series, lag):
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / n
    if var == 0:
        return 0
    cov = sum((series[i] - mean) * (series[i + lag] - mean) for i in range(n - lag)) / (n - lag)
    return cov / var


props = ["somma", "range", "pari", "decine", "gap_max", "std"]
sig_count = 0
total_tests = 0

print(f"{'PROPRIETA':<10} {'RUOTA':<10} {'LAG':>4} {'R':>7} {'SOGLIA':>8} {'SIG':>4}", flush=True)
print("-" * 50, flush=True)

for prop in props:
    for ruota in RUOTE:
        series = meta_series[ruota][prop]
        N = len(series)
        soglia = 2 / math.sqrt(N)
        for lag in range(1, max_lag + 1):
            r = autocorr(series, lag)
            total_tests += 1
            if abs(r) > soglia:
                sig_count += 1
                if lag <= 3:  # mostra solo lag bassi
                    print(f"{prop:<10} {ruota:<10} {lag:>4} {r:>+6.3f} {soglia:>+7.3f}    *", flush=True)

expected_sig = total_tests * 0.05
print(f"\nTest totali: {total_tests}", flush=True)
print(f"Significativi: {sig_count} (attesi per caso: {expected_sig:.0f})", flush=True)
ratio_sig = sig_count / expected_sig if expected_sig > 0 else 0
VERDETTI[2] = "SEGNALE" if ratio_sig > 2.0 else ("APPROFONDIRE" if ratio_sig > 1.5 else "NESSUN SEGNALE")
print(f"Ratio sig/attesi: {ratio_sig:.2f}x", flush=True)
print(f"Verdetto: {VERDETTI[2]}", flush=True)

# ================================================================
# TEST 3 — Rete negativa (predizione per esclusione)
# ================================================================
header(3, "Rete negativa (predizione per esclusione)")
print("I 20% ambi piu' freddi nella finestra escono meno del 20% atteso?", flush=True)
print()

p_ambo = 1 / 400.5
max_colpi_test = 9

print(f"{'W':>4} {'FREDDI%':>8} {'HIT%':>7} {'ATTESO%':>8} {'RATIO':>7} {'EDGE':>7}", flush=True)
print("-" * 48, flush=True)

best_edge = 0
for W in [50, 100, 150, 200, 300]:
    cold_hits = 0
    cold_total = 0
    hot_hits = 0
    hot_total = 0

    for idx in range(W + 200, len(dati) - max_colpi_test, 10):  # step 10 per velocita
        for ruota in random.sample(list(RUOTE), 2):
            # Conta frequenze nella finestra
            pf = Counter()
            for back in range(1, W + 1):
                bi = idx - back
                if bi < 0:
                    break
                _, bw = dati[bi]
                if ruota not in bw:
                    continue
                for a, b in combinations(sorted(bw[ruota]), 2):
                    pf[(a, b)] += 1

            if not pf:
                continue

            # 20% piu' freddi (freq 0 o minima)
            all_pairs_seen = list(pf.keys())
            all_pairs_seen.sort(key=lambda p: pf[p])
            n_cold = max(1, len(all_pairs_seen) // 5)
            cold_pairs = set(all_pairs_seen[:n_cold])
            hot_pairs = set(all_pairs_seen[n_cold:])

            # Verifica
            for colpo in range(1, max_colpi_test + 1):
                fi = idx + colpo
                if fi >= len(dati):
                    break
                _, fw = dati[fi]
                if ruota in fw:
                    for a, b in combinations(sorted(fw[ruota]), 2):
                        if (a, b) in cold_pairs:
                            cold_hits += 1
                            cold_total += 1
                        elif (a, b) in hot_pairs:
                            hot_hits += 1
                            hot_total += 1
                    break

    cold_rate = cold_hits / cold_total * 100 if cold_total > 0 else 0
    hot_rate = hot_hits / hot_total * 100 if hot_total > 0 else 0
    # Se cold_rate < 20%, abbiamo un edge escludendoli
    edge = (20 - cold_rate) / 20 * 100 if cold_rate < 20 else 0
    if edge > best_edge:
        best_edge = edge
    marker = " <" if cold_rate < 18 else ""
    print(f"{W:>4} {cold_rate:>7.2f}% {hot_rate:>6.2f}% {'20.00%':>8} {cold_rate / 20:>6.3f}x {edge:>+5.1f}%{marker}", flush=True)

VERDETTI[3] = "SEGNALE" if best_edge > 5 else ("APPROFONDIRE" if best_edge > 2 else "NESSUN SEGNALE")
print(f"\nMiglior edge per esclusione: {best_edge:.1f}%", flush=True)
print(f"Verdetto: {VERDETTI[3]}", flush=True)

# ================================================================
# TEST 4 — Transfer entropy di Schreiber
# ================================================================
header(4, "Transfer entropy di Schreiber")
print("Quanta info l'estrazione t fornisce su t+1 (stessa ruota)?", flush=True)
print()

N_PERM = 200


def discretize(values, n_bins=5):
    """Discretizza in n_bins equiprobabili."""
    sorted_v = sorted(values)
    thresholds = [sorted_v[int(len(sorted_v) * i / n_bins)] for i in range(1, n_bins)]
    result = []
    for v in values:
        b = 0
        for t in thresholds:
            if v > t:
                b += 1
        result.append(b)
    return result


def transfer_entropy(source, target, lag=1):
    """TE = H(Y_t+1 | Y_t) - H(Y_t+1 | Y_t, X_t)"""
    n = len(source) - lag
    # Conta
    joint_yx = Counter()  # (y_t, y_t+1)
    joint_yxy = Counter()  # (y_t, x_t, y_t+1)
    count_y = Counter()  # y_t
    count_yx = Counter()  # (y_t, x_t)

    for i in range(n):
        yt = target[i]
        yt1 = target[i + lag]
        xt = source[i]
        joint_yx[(yt, yt1)] += 1
        joint_yxy[(yt, xt, yt1)] += 1
        count_y[yt] += 1
        count_yx[(yt, xt)] += 1

    # H(Y_t+1 | Y_t)
    h_y_given_y = 0
    for (yt, yt1), c in joint_yx.items():
        p = c / count_y[yt]
        if p > 0:
            h_y_given_y -= (c / n) * math.log2(p)

    # H(Y_t+1 | Y_t, X_t)
    h_y_given_yx = 0
    for (yt, xt, yt1), c in joint_yxy.items():
        p = c / count_yx[(yt, xt)]
        if p > 0:
            h_y_given_yx -= (c / n) * math.log2(p)

    return h_y_given_y - h_y_given_yx


print(f"{'RUOTA':<12} {'TE (bits)':>10} {'TE random':>10} {'Z':>6} {'P':>8} {'SIG':>4}", flush=True)
print("-" * 55, flush=True)

te_signals = 0
for ruota in RUOTE:
    # Serie: somma dei 5 numeri per estrazione
    sums = []
    for _, wheels in dati:
        if ruota in wheels:
            sums.append(sum(wheels[ruota]))

    disc = discretize(sums)
    te_real = transfer_entropy(disc, disc, lag=1)

    # Permutazioni
    te_perms = []
    for _ in range(N_PERM):
        shuffled = disc[:]
        random.shuffle(shuffled)
        te_perms.append(transfer_entropy(shuffled, disc, lag=1))

    mean_perm = sum(te_perms) / len(te_perms)
    std_perm = (sum((t - mean_perm) ** 2 for t in te_perms) / len(te_perms)) ** 0.5
    z = (te_real - mean_perm) / std_perm if std_perm > 0 else 0
    p_val = sum(1 for t in te_perms if t >= te_real) / len(te_perms)

    sig = "*" if p_val < 0.05 else ""
    if p_val < 0.05:
        te_signals += 1
    print(f"{ruota:<12} {te_real:>9.6f} {mean_perm:>9.6f} {z:>5.2f} {p_val:>7.3f} {sig:>4}", flush=True)

VERDETTI[4] = "SEGNALE" if te_signals >= 3 else ("APPROFONDIRE" if te_signals >= 1 else "NESSUN SEGNALE")
print(f"\nRuote con TE significativa: {te_signals}/10", flush=True)
print(f"Verdetto: {VERDETTI[4]}", flush=True)

# ================================================================
# TEST 5 — Regime detection (fallback media mobile)
# ================================================================
header(5, "Regime detection (media mobile + soglie)")
print("Fitta ON/OFF sulla serie ratio freq+rit+dec W=150 scorrevole.", flush=True)
print()

# Calcola serie ratio scorrevole (dai risultati precedenti, ricalcolo veloce)
W_regime = 150
step_regime = 30
p_ambo_9 = 1 - (1 - 1 / 400.5) ** 9

ratio_series = []
for start in range(W_regime, len(dati) - W_regime - 9, step_regime):
    end = start + W_regime
    signals = 0
    hits = 0
    for idx in range(start, end):
        if idx < W_regime:
            continue
        for ruota in random.sample(list(RUOTE), 1):
            pf = Counter()
            pl = {}
            for back in range(1, W_regime + 1):
                bi = idx - back
                if bi < 0:
                    break
                _, bw = dati[bi]
                if ruota not in bw:
                    continue
                for a, b in combinations(sorted(bw[ruota]), 2):
                    pf[(a, b)] += 1
                    if (a, b) not in pl:
                        pl[(a, b)] = back
            soglia = W_regime // 3
            count = 0
            for pair, freq in pf.items():
                a, b = pair
                if freq < 1 or (a - 1) // 10 != (b - 1) // 10:
                    continue
                if pl.get(pair, W_regime) < soglia:
                    continue
                signals += 1
                for colpo in range(1, 10):
                    fi = idx + colpo
                    if fi >= len(dati):
                        break
                    _, fw = dati[fi]
                    if ruota in fw:
                        fn = set(fw[ruota])
                        if a in fn and b in fn:
                            hits += 1
                            break
                count += 1
                if count >= 3:
                    break
        if signals > 500:
            break

    rate = hits / signals if signals > 0 else 0
    ratio = rate / p_ambo_9 if p_ambo_9 > 0 else 0
    dt = datetime.strptime(dati[start][0], "%d/%m/%Y")
    ratio_series.append((dt.year + dt.month / 12, ratio))

# Media mobile a 5 punti
ma_window = 5
ma_series = []
for i in range(len(ratio_series) - ma_window):
    avg = sum(r for _, r in ratio_series[i : i + ma_window]) / ma_window
    year = ratio_series[i + ma_window // 2][0]
    ma_series.append((year, avg))

# Classifica ON/OFF
on_count = sum(1 for _, r in ma_series if r > 1.1)
off_count = sum(1 for _, r in ma_series if r < 0.9)
trans_count = len(ma_series) - on_count - off_count

# Stato attuale
last_5 = ma_series[-5:] if len(ma_series) >= 5 else ma_series
current_avg = sum(r for _, r in last_5) / len(last_5) if last_5 else 0

print(f"Punti nella serie: {len(ma_series)}", flush=True)
print(f"ON (>1.1):   {on_count} ({on_count / len(ma_series) * 100:.0f}%)", flush=True)
print(f"OFF (<0.9):  {off_count} ({off_count / len(ma_series) * 100:.0f}%)", flush=True)
print(f"Transizione: {trans_count} ({trans_count / len(ma_series) * 100:.0f}%)", flush=True)
print(f"\nStato attuale (media ultimi 5): {current_avg:.3f}x", flush=True)
if current_avg > 1.1:
    stato = "ON"
elif current_avg < 0.9:
    stato = "OFF"
else:
    stato = "TRANSIZIONE"
print(f"Regime: {stato}", flush=True)

# Accuracy retrospettiva: quante volte ON prevede ratio>1.0 nel periodo successivo
correct = 0
total = 0
for i in range(len(ma_series) - 3):
    _, r_now = ma_series[i]
    _, r_next = ma_series[i + 1]
    if r_now > 1.1:
        total += 1
        if r_next > 1.0:
            correct += 1
    elif r_now < 0.9:
        total += 1
        if r_next < 1.0:
            correct += 1

accuracy = correct / total * 100 if total > 0 else 0
print(f"Accuracy regime->prossimo: {correct}/{total} = {accuracy:.1f}%", flush=True)

VERDETTI[5] = "SEGNALE" if accuracy > 65 else ("APPROFONDIRE" if accuracy > 55 else "NESSUN SEGNALE")
print(f"Verdetto: {VERDETTI[5]}", flush=True)

# ================================================================
# TEST 6 — Differenze per giorno della settimana
# ================================================================
header(6, "Differenze per giorno della settimana")
print("Martedi vs Giovedi vs Sabato: stesse distribuzioni?", flush=True)
print()

day_data = defaultdict(lambda: defaultdict(list))

for date_str, wheels in dati:
    dt = datetime.strptime(date_str, "%d/%m/%Y")
    dow = dt.weekday()  # 0=lun, 1=mar, 3=gio, 5=sab
    day_name = {1: "MAR", 3: "GIO", 5: "SAB"}.get(dow, f"D{dow}")

    for ruota, nums in wheels.items():
        if ruota not in RUOTE:
            continue
        day_data[day_name]["somma"].append(sum(nums))
        day_data[day_name]["range"].append(max(nums) - min(nums))
        day_data[day_name]["pari"].append(sum(1 for n in nums if n % 2 == 0))
        s = sorted(nums)
        day_data[day_name]["intradec"].append(
            1 if len(set((n - 1) // 10 for n in nums)) < 5 else 0
        )

# Kruskal-Wallis approssimato (confronto ranghi)
days_of_interest = [d for d in day_data if d in ("MAR", "GIO", "SAB")]

print(f"{'PROPRIETA':<12}", end="", flush=True)
for d in days_of_interest:
    print(f" {d:>8}", end="")
print(f" {'H-STAT':>8} {'SIG':>5}", flush=True)
print("-" * 55, flush=True)

n_sig = 0
for prop in ["somma", "range", "pari", "intradec"]:
    means = {}
    for d in days_of_interest:
        vals = day_data[d][prop]
        means[d] = sum(vals) / len(vals) if vals else 0

    # Kruskal-Wallis: H = 12/(N(N+1)) * sum(R_i^2/n_i) - 3(N+1)
    all_vals = []
    for d in days_of_interest:
        for v in day_data[d][prop]:
            all_vals.append((v, d))

    all_vals.sort(key=lambda x: x[0])
    N = len(all_vals)
    ranks = defaultdict(list)
    for rank, (val, d) in enumerate(all_vals, 1):
        ranks[d].append(rank)

    H = 0
    for d in days_of_interest:
        n_i = len(ranks[d])
        R_i = sum(ranks[d])
        if n_i > 0:
            H += R_i**2 / n_i
    H = 12 / (N * (N + 1)) * H - 3 * (N + 1)

    # df=2, chi2 critico al 5% = 5.991
    sig = "*" if H > 5.991 else ""
    if H > 5.991:
        n_sig += 1

    row = f"{prop:<12}"
    for d in days_of_interest:
        row += f" {means[d]:>8.2f}"
    row += f" {H:>8.2f} {sig:>5}"
    print(row, flush=True)

VERDETTI[6] = "SEGNALE" if n_sig >= 2 else ("APPROFONDIRE" if n_sig >= 1 else "NESSUN SEGNALE")
print(f"\nProprieta' significative: {n_sig}/4", flush=True)
print(f"Verdetto: {VERDETTI[6]}", flush=True)

# ================================================================
# RIEPILOGO FINALE
# ================================================================
print(f"\n{'=' * 70}", flush=True)
print(f"  RIEPILOGO — 6 TEST LATERALI", flush=True)
print(f"{'=' * 70}\n", flush=True)

print(f"{'#':>2} {'TEST':<40} {'VERDETTO':<15}", flush=True)
print("-" * 60, flush=True)

test_names = {
    1: "Compressibilita' di Kolmogorov",
    2: "Autocorrelazione meta-proprieta'",
    3: "Rete negativa (esclusione)",
    4: "Transfer entropy di Schreiber",
    5: "Regime detection (media mobile)",
    6: "Differenze giorno settimana",
}

for i in range(1, 7):
    v = VERDETTI.get(i, "?")
    marker = " <<<" if v == "SEGNALE" else (" <" if v == "APPROFONDIRE" else "")
    print(f"{i:>2} {test_names[i]:<40} {v:<15}{marker}", flush=True)

segnali = sum(1 for v in VERDETTI.values() if v == "SEGNALE")
approf = sum(1 for v in VERDETTI.values() if v == "APPROFONDIRE")
print(f"\nSEGNALE: {segnali}/6 | APPROFONDIRE: {approf}/6 | NESSUN SEGNALE: {6 - segnali - approf}/6", flush=True)

if segnali > 0:
    print("\n>>> Test con SEGNALE da integrare nell'Engine V4!", flush=True)
elif approf > 0:
    print("\n>>> Test da APPROFONDIRE con campione piu' grande.", flush=True)
else:
    print("\n>>> Nessun segnale laterale trovato.", flush=True)

# Notifica
import httpx

msg = "6 TEST LATERALI\n\n"
for i in range(1, 7):
    msg += f"{i}. {test_names[i]}: {VERDETTI.get(i, '?')}\n"
msg += f"\nSegnali: {segnali}, Approfondire: {approf}"
try:
    httpx.post(
        "https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM",
        content=msg.encode("utf-8"),
        headers={"Title": "6 Test Laterali", "Priority": "5"},
        timeout=10.0,
    )
except Exception:
    pass

print("\nDone.", flush=True)
