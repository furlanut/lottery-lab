"""Test laterali V4 — Forma corretta + Sweep somme×finestre."""
from __future__ import annotations
import math, random, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "backend")
from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE

print("Caricamento...", flush=True)
ARCHIVIO = Path("archivio_dati/Archivio_Lotto/TXT")
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split("-")[-1]) >= 1946]
all_records = []
for fp in files: all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records: by_date[r["data"].strftime("%d/%m/%Y")][r["ruota"]] = r["numeri"]
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
print(f"Dataset: {len(dati)} estrazioni\n", flush=True)

# ================================================================
# TEST 9B — Forma con baseline MARGINALE + MI + permutazioni
# ================================================================
print("=" * 70, flush=True)
print("  TEST 9B — Transizioni forma: baseline marginale + MI", flush=True)
print("=" * 70, flush=True)

def classify(nums):
    s = sorted(nums)
    return {
        'parita': sum(1 for n in nums if n % 2 == 0),
        'somma': 'bassa' if sum(nums) < 180 else ('alta' if sum(nums) > 270 else 'media'),
        'spread': 'compatta' if s[-1]-s[0] < 40 else ('larga' if s[-1]-s[0] > 60 else 'media'),
        'decine': len(set((n-1)//10 for n in nums)),
    }

prop_seq = defaultdict(lambda: defaultdict(list))
for _, wheels in dati:
    for ruota, nums in wheels.items():
        if ruota not in RUOTE: continue
        for k, v in classify(nums).items():
            prop_seq[ruota][k].append(v)

def calc_mi(seq):
    """Mutual information I(X_t; X_{t+1})."""
    n = len(seq) - 1
    joint = Counter()
    mx = Counter()
    my = Counter()
    for i in range(n):
        joint[(seq[i], seq[i+1])] += 1
        mx[seq[i]] += 1
        my[seq[i+1]] += 1
    h_y = -sum((c/n)*math.log2(c/n) for c in my.values() if c > 0)
    # H(Y|X)
    h_y_given_x = 0
    for x_val in mx:
        nx = mx[x_val]
        for y_val in my:
            nxy = joint.get((x_val, y_val), 0)
            if nxy > 0:
                h_y_given_x -= (nxy/n) * math.log2(nxy/nx)
    return h_y - h_y_given_x

def chi2_row_marginal(seq):
    """Chi2 per ogni riga della matrice di transizione vs marginale."""
    n = len(seq) - 1
    states = sorted(set(seq))
    margin = Counter(seq[1:])
    total_m = sum(margin.values())
    p_marg = {s: margin.get(s, 0)/total_m for s in states}
    trans = Counter()
    from_c = Counter()
    for i in range(n):
        trans[(seq[i], seq[i+1])] += 1
        from_c[seq[i]] += 1
    chi2_total = 0; df_total = 0
    for s_from in states:
        tf = from_c[s_from]
        if tf < 20: continue
        valid_tos = [s for s in states if tf * p_marg[s] >= 1]
        for s_to in valid_tos:
            exp = tf * p_marg[s_to]
            obs = trans.get((s_from, s_to), 0)
            chi2_total += (obs - exp)**2 / exp
        df_total += len(valid_tos) - 1
    return chi2_total, df_total

random.seed(42)
N_PERM = 500
bonferroni_count = 0

# Conta test totali per Bonferroni
for prop in ['parita', 'somma', 'spread', 'decine']:
    for ruota in RUOTE:
        seq = prop_seq[ruota][prop]
        states = sorted(set(seq))
        from_c = Counter()
        for i in range(len(seq)-1): from_c[seq[i]] += 1
        bonferroni_count += sum(1 for s in states if from_c[s] >= 20)

bonf_threshold = 0.05 / bonferroni_count if bonferroni_count > 0 else 0.05
print(f"\nTest totali (righe matrice): {bonferroni_count}", flush=True)
print(f"Soglia Bonferroni: p < {bonf_threshold:.6f}\n", flush=True)

# Chi2 per proprietà×ruota
print(f"{'PROP':<10} {'RUOTA':<10} {'CHI2':>8} {'DF':>4} {'P_APPROX':>10} {'MI_REAL':>8} {'MI_PERM':>8} {'MI_P':>6}", flush=True)
print("-" * 72, flush=True)

n_chi2_sig = 0
n_mi_sig = 0
total_prop_tests = 0

for prop in ['parita', 'somma', 'spread', 'decine']:
    for ruota in RUOTE:
        seq = prop_seq[ruota][prop]
        total_prop_tests += 1
        
        chi2, df = chi2_row_marginal(seq)
        # p-value approssimato dal chi2
        # Per df grande: z = sqrt(2*chi2) - sqrt(2*df-1)
        if df > 0:
            z_chi = (math.sqrt(2*chi2) - math.sqrt(2*df - 1)) if df > 1 else chi2/df
            p_chi = 0.5 * math.erfc(z_chi / math.sqrt(2)) if z_chi > 0 else 1.0
        else:
            p_chi = 1.0
        
        # MI con permutazioni
        mi_real = calc_mi(seq)
        mi_perms = []
        for _ in range(N_PERM):
            shuf = seq[:]
            random.shuffle(shuf)
            mi_perms.append(calc_mi(shuf))
        mi_mean = sum(mi_perms)/len(mi_perms)
        mi_p = sum(1 for m in mi_perms if m >= mi_real) / len(mi_perms)
        
        chi_sig = p_chi < 0.05
        mi_sig = mi_p < 0.05
        if chi_sig: n_chi2_sig += 1
        if mi_sig: n_mi_sig += 1
        
        flag = ""
        if chi_sig and mi_sig: flag = " **"
        elif chi_sig or mi_sig: flag = " *"
        
        if flag:
            print(f"{prop:<10} {ruota:<10} {chi2:>7.1f} {df:>4} {p_chi:>9.4f} {mi_real:>7.5f} {mi_mean:>7.5f} {mi_p:>5.3f}{flag}", flush=True)

exp_chi = total_prop_tests * 0.05
exp_mi = total_prop_tests * 0.05
print(f"\nChi2 significativi: {n_chi2_sig}/{total_prop_tests} (attesi: {exp_chi:.1f})", flush=True)
print(f"MI significativi: {n_mi_sig}/{total_prop_tests} (attesi: {exp_mi:.1f})", flush=True)

verdict_9b = "SEGNALE" if n_chi2_sig > exp_chi * 2 and n_mi_sig > exp_mi * 2 else (
    "APPROFONDIRE" if n_chi2_sig > exp_chi * 1.5 or n_mi_sig > exp_mi * 1.5 else "NESSUN SEGNALE")
print(f"\nVERDETTO 9B: {verdict_9b}", flush=True)

# ================================================================
# TEST 10 — Sweep somme×finestre con protezione anti-overfitting
# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST 10 — Sweep somme x finestre (discovery + validazione)", flush=True)
print("=" * 70, flush=True)

p_ambetto = 1/100.32
p_ambetto_9 = 1 - (1 - p_ambetto) ** 9
half = len(dati) // 2
WINDOWS = [50, 75, 100, 125, 150, 200]
SUMS = list(range(10, 171))  # 10 a 170

def check_ambetto(a, b, estratti):
    e = set(estratti)
    if a in e and b in e: return True
    if a in e:
        for n in e:
            if n != a and (n == b-1 or n == b+1): return True
    if b in e:
        for n in e:
            if n != b and (n == a-1 or n == a+1): return True
    return False

def bt_sum_ambetto(data, start, end, target_sum, window):
    """Backtest ambetto per coppie con somma=target_sum."""
    signals = 0; hits = 0; soglia = window // 3
    for idx in range(start, min(end, len(data) - 9)):
        if idx < window: continue
        for ruota in random.sample(list(RUOTE), 1):
            pf = Counter(); pl = {}
            for back in range(1, window + 1):
                bi = idx - back
                if bi < 0: break
                _, bw = data[bi]
                if ruota not in bw: continue
                for a, b in combinations(sorted(bw[ruota]), 2):
                    pf[(a,b)] += 1
                    if (a,b) not in pl: pl[(a,b)] = back
            count = 0
            for pair, freq in pf.items():
                a, b = pair
                if a + b != target_sum: continue
                if freq < 1: continue
                if pl.get(pair, window) < soglia: continue
                signals += 1
                for colpo in range(1, 10):
                    fi = idx + colpo
                    if fi >= len(data): break
                    _, fw = data[fi]
                    if ruota in fw:
                        if check_ambetto(a, b, fw[ruota]):
                            hits += 1; break
                count += 1
                if count >= 3: break
    rate = hits/signals if signals > 0 else 0
    return signals, hits, rate/p_ambetto_9 if p_ambetto_9 > 0 else 0

# FASE 1: Discovery (prima meta')
print(f"\n--- FASE 1: Discovery (prima meta', {half} estrazioni) ---", flush=True)
print(f"Sweep: {len(SUMS)} somme × {len(WINDOWS)} finestre = {len(SUMS)*len(WINDOWS)} combinazioni\n", flush=True)

random.seed(42)
discovery = {}  # (S, W) -> ratio
prog = 0
total_combos = len(SUMS) * len(WINDOWS)

for S in SUMS:
    for W in WINDOWS:
        s, h, ratio = bt_sum_ambetto(dati, 0, half, S, W)
        if s >= 10:  # minimo segnali per essere valido
            discovery[(S, W)] = (s, h, ratio)
        prog += 1
        if prog % 200 == 0:
            print(f"  {prog}/{total_combos} ({prog/total_combos*100:.0f}%)...", flush=True)

# Top 20
valid = [(k, v) for k, v in discovery.items() if v[0] >= 10]
valid.sort(key=lambda x: -x[1][2])
top20 = valid[:20]

print(f"\nCombinazioni valide (>=10 segnali): {len(valid)}", flush=True)
print(f"\n--- TOP 20 Discovery ---", flush=True)
print(f"{'#':>3} {'SOMMA':>6} {'W':>4} {'SEGN':>6} {'HIT':>5} {'RATIO':>7} {'S72?':>5}", flush=True)
print("-" * 40, flush=True)
s72_in_top20 = False
for i, ((S, W), (sig, hit, ratio)) in enumerate(top20, 1):
    is_72 = "<<<" if S == 72 else ""
    if S == 72: s72_in_top20 = True
    print(f"{i:>3} {S:>6} {W:>4} {sig:>6} {hit:>5} {ratio:>6.3f}x {is_72}", flush=True)

# Heatmap testuale (raggruppato per somme a step 10)
print(f"\n--- Heatmap somme (step 10) × finestre ---", flush=True)
print(f"{'SOMMA':>10}", end="", flush=True)
for W in WINDOWS:
    print(f" W={W:>3}", end="")
print(flush=True)
print("-" * (10 + len(WINDOWS) * 6), flush=True)

for S_start in range(10, 171, 10):
    S_end = min(S_start + 9, 170)
    label = f"{S_start}-{S_end}"
    print(f"{label:>10}", end="", flush=True)
    for W in WINDOWS:
        # Media ratio nel range
        ratios = [discovery[(S, W)][2] for S in range(S_start, S_end + 1) if (S, W) in discovery]
        avg = sum(ratios)/len(ratios) if ratios else 0
        marker = "##" if avg > 1.2 else ("#" if avg > 1.1 else ("." if avg > 0.9 else " "))
        print(f" {avg:>4.2f}{marker}", end="")
    print(flush=True)

# Cluster analysis
top20_sums = [S for (S, W), _ in top20]
print(f"\nSomme nella top 20: {sorted(set(top20_sums))}", flush=True)
min_s, max_s = min(top20_sums), max(top20_sums)
print(f"Range: {min_s}-{max_s} (span={max_s-min_s})", flush=True)
if max_s - min_s < 30:
    print(">>> CLUSTER: le somme vincenti sono raggruppate!", flush=True)
else:
    print(">>> SPARSE: le somme vincenti sono distribuite", flush=True)

# FASE 2: Validazione (seconda meta')
print(f"\n--- FASE 2: Validazione (seconda meta') ---", flush=True)
print(f"{'#':>3} {'S':>4} {'W':>4} {'DISC':>7} {'VAL SEGN':>8} {'VAL HIT':>7} {'VAL RATIO':>10} {'TIENE?':>7}", flush=True)
print("-" * 55, flush=True)

val_results = []
for i, ((S, W), (disc_s, disc_h, disc_r)) in enumerate(top20, 1):
    s, h, ratio = bt_sum_ambetto(dati, half, len(dati), S, W)
    tiene = "SI" if ratio > 1.0 else "NO"
    val_results.append((S, W, disc_r, ratio))
    marker = " <<<" if ratio > 1.2 else ""
    print(f"{i:>3} {S:>4} {W:>4} {disc_r:>6.3f}x {s:>8} {h:>7} {ratio:>9.3f}x {tiene:>6}{marker}", flush=True)

# 5-fold CV sulle top 5 validazione
print(f"\n--- 5-fold CV sulle top 5 dalla validazione ---", flush=True)
val_sorted = sorted(val_results, key=lambda x: -x[3])[:5]

test_data = dati[-3000:]
fold_size = 600

print(f"{'S':>4} {'W':>4}", end="", flush=True)
for f in range(5): print(f"   F{f+1}", end="")
print(f"  {'MEDIA':>7} {'MIN':>7}", flush=True)
print("-" * 55, flush=True)

for S, W, disc_r, val_r in val_sorted:
    folds = []
    for fold in range(5):
        s, h, ratio = bt_sum_ambetto(test_data, fold*fold_size, (fold+1)*fold_size, S, W)
        folds.append(ratio)
    mean_r = sum(folds)/len(folds)
    min_r = min(folds)
    fold_str = "".join(f" {r:>5.2f}" for r in folds)
    print(f"{S:>4} {W:>4}{fold_str}  {mean_r:>6.3f}x {min_r:>6.3f}x", flush=True)

# Risposte alle 4 domande
print(f"\n{'=' * 70}", flush=True)
print("  RISPOSTE", flush=True)
print("=" * 70, flush=True)
print(f"\n1. Somma 72 nella top 20 discovery? {'SI' if s72_in_top20 else 'NO — cherry-picking!'}", flush=True)
print(f"2. Cluster? Range somme top20: {min_s}-{max_s} (span {max_s-min_s})", flush=True)
best_val = val_sorted[0] if val_sorted else None
if best_val:
    print(f"3. Miglior discovery tiene in validazione? S={best_val[0]} disc={best_val[2]:.3f}x val={best_val[3]:.3f}x", flush=True)
    print(f"4. Batte somma72 W=150? ", end="", flush=True)
    s72_val = next((r for s, w, d, r in val_results if s == 72 and w == 150), None)
    if s72_val:
        print(f"somma72 val={s72_val:.3f}x vs best val={best_val[3]:.3f}x → {'SI' if best_val[3] > s72_val else 'NO'}", flush=True)
    else:
        print("somma72 W=150 non nella top 20", flush=True)

# Notifica
import httpx
msg = f"TEST 9B: {verdict_9b}\nTEST 10: top discovery S={top20[0][0][0]} W={top20[0][0][1]} ratio={top20[0][1][2]:.3f}x\n"
msg += f"S72 in top20: {'SI' if s72_in_top20 else 'NO'}"
try:
    httpx.post('https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=msg.encode('utf-8'),
        headers={'Title': 'Test 9B + 10 Risultati', 'Priority': '5'}, timeout=10.0)
except: pass
print("\nDone.", flush=True)
