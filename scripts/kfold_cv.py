#!/usr/bin/env python3
"""K-fold temporal cross-validation for optimal window size — optimized."""

import sys; sys.path.insert(0, 'backend')
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from datetime import datetime
from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist
import random, math, httpx, time

random.seed(42)

# ── DATA LOADING ──
print("Loading data...")
ARCHIVIO = Path('archivio_dati/Archivio_Lotto/TXT')
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split('-')[-1]) >= 1946]
all_records = []
for fp in files: all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records: by_date[r['data'].strftime('%d/%m/%Y')][r['ruota']] = r['numeri']
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'))
print(f"Loaded {len(dati)} extractions")

# ── HELPERS ──
def figura(n):
    while n >= 10: n = sum(int(d) for d in str(n))
    return n

FIB_DISTS = {1, 2, 3, 5, 8, 13, 21, 34}
max_colpi = 9
p_ambo_9 = 1 - (1 - 1/400.5) ** max_colpi

# Precompute figura and decade for all numbers
FIGURA = {n: figura(n) for n in range(1, 91)}
DECADE = {n: (n - 1) // 10 for n in range(1, 91)}
# Precompute cyclo_dist for all pairs
CDIST = {}
for a in range(1, 91):
    for b in range(a+1, 91):
        CDIST[(a, b)] = cyclo_dist(a, b)

# Precompute: for each ruota, build index of which dates have which numbers
# and ambo pairs for quick lookup
print("Building indices...")

# For each extraction index, store {ruota: set(numeri)} for quick hit checking
dati_nums = []
for dt, ruote in dati:
    entry = {}
    for ruota, nums in ruote.items():
        entry[ruota] = set(nums)
    dati_nums.append(entry)

def check_hit(start_idx, ruota, pair, max_draws=9):
    """Check if pair appears on ruota within next max_draws extractions."""
    a, b = pair
    count = 0
    for i in range(start_idx, min(start_idx + max_draws + 50, len(dati_nums))):
        entry = dati_nums[i]
        if ruota in entry:
            nums = entry[ruota]
            if a in nums and b in nums:
                return True
            count += 1
            if count >= max_draws:
                break
    return False

def compute_window_features(window_start, window_end, ruota):
    """Efficiently compute pair freq, num freq, and recent pair set for a window."""
    pair_freq = Counter()
    num_freq = Counter()

    for i in range(window_start, window_end):
        entry = dati_nums[i]
        if ruota in entry:
            nums = sorted(entry[ruota])
            for n in nums:
                num_freq[n] += 1
            for j in range(len(nums)):
                for k in range(j+1, len(nums)):
                    pair_freq[(nums[j], nums[k])] += 1

    return pair_freq, num_freq

def compute_recent_pairs(recent_start, recent_end, ruota):
    """Get set of pairs seen in recent period."""
    recent_pairs = set()
    for i in range(recent_start, recent_end):
        entry = dati_nums[i]
        if ruota in entry:
            nums = sorted(entry[ruota])
            for j in range(len(nums)):
                for k in range(j+1, len(nums)):
                    recent_pairs.add((nums[j], nums[k]))
    return recent_pairs

# ── SIGNAL DEFINITIONS (work on precomputed data) ──
def eval_signals_batch(pair_freq, num_freq, recent_pairs, N):
    """Evaluate all 5 signals for all candidate pairs at once.
    Returns dict: signal_name -> list of firing pairs (sorted by pair_freq desc, top 5).
    """
    # Compute avg frequency
    total_nums = sum(num_freq.values())
    avg = total_nums / 90.0 if total_nums > 0 else 1.0

    # Collect all candidate pairs: those with freq>=1 OR involving hot/cold numbers
    hot_nums = {n for n in range(1, 91) if num_freq.get(n, 0) > 1.5 * avg}
    cold_nums = {n for n in range(1, 91) if num_freq.get(n, 0) < 0.5 * avg}

    # Candidate pairs: all pairs that appeared + hot-cold combos
    candidates = set(pair_freq.keys())
    # Add hot-cold pairs (limit to keep it fast)
    for h in hot_nums:
        for c in cold_nums:
            a, b = min(h, c), max(h, c)
            candidates.add((a, b))

    results = {s: [] for s in ['freq_rit+fib', 'freq+rit+dec', 'hot_cold', 'freq+rit+fig', 'TOP6']}

    for pair in candidates:
        a, b = pair
        pf = pair_freq.get(pair, 0)
        fa = num_freq.get(a, 0)
        fb = num_freq.get(b, 0)
        in_ritardo = pair not in recent_pairs
        cd = CDIST.get((a, b), CDIST.get((b, a), 0))
        is_fib = cd in FIB_DISTS
        same_dec = DECADE[a] == DECADE[b]
        same_fig = FIGURA[a] == FIGURA[b]
        hot_a = fa > 1.5 * avg
        hot_b = fb > 1.5 * avg
        cold_a = fa < 0.5 * avg
        cold_b = fb < 0.5 * avg
        is_hot_cold = (hot_a and cold_b) or (hot_b and cold_a)

        # Signal 1: freq_rit+fib
        if pf >= 2 and in_ritardo and is_fib:
            results['freq_rit+fib'].append((pair, pf))

        # Signal 2: freq+rit+dec
        if pf >= 1 and in_ritardo and same_dec:
            results['freq+rit+dec'].append((pair, pf))

        # Signal 3: hot_cold
        if is_hot_cold:
            results['hot_cold'].append((pair, pf))

        # Signal 4: freq+rit+fig
        if pf >= 1 and in_ritardo and same_fig:
            results['freq+rit+fig'].append((pair, pf))

        # Signal 5: TOP6 (>=4 of 6 sub-signals)
        count = 0
        if is_hot_cold: count += 1
        if hot_a or hot_b: count += 1
        if in_ritardo: count += 1
        if pf >= 1 and in_ritardo: count += 1
        if is_fib: count += 1
        if pf >= 1: count += 1
        if count >= 4:
            results['TOP6'].append((pair, pf))

    # Sort each by pair_freq desc and take top 5
    for sig in results:
        results[sig].sort(key=lambda x: -x[1])
        results[sig] = [p for p, _ in results[sig][:5]]

    return results

# ── EXPERIMENT SETUP ──
WINDOW_SIZES = [30, 40, 50, 60, 70, 75, 80, 90, 100, 120, 150, 200]
N_FOLDS = 5
BLOCK_SIZE = 600
TOTAL_NEEDED = BLOCK_SIZE * N_FOLDS  # 3000
WHEELS_PER_EXT = 3
TOP_K = 5

pre_context_start = len(dati) - TOTAL_NEEDED
print(f"Using last {TOTAL_NEEDED} extractions for CV")
print(f"Date range: {dati[pre_context_start][0]} to {dati[-1][0]}")

# Split into 5 blocks (indices relative to full dati array)
blocks = []
for i in range(N_FOLDS):
    s = pre_context_start + i * BLOCK_SIZE
    e = pre_context_start + (i + 1) * BLOCK_SIZE
    blocks.append((s, e))

# Results: results[signal][N] = [ratio per fold]
results = defaultdict(lambda: defaultdict(list))

t0 = time.time()

for fold in range(N_FOLDS):
    test_start, test_end = blocks[fold]
    print(f"\n=== FOLD {fold+1}/{N_FOLDS} === test: idx {test_start}-{test_end} ({dati[test_start][0]} to {dati[test_end-1][0]})")
    fold_t0 = time.time()

    for N in WINDOW_SIZES:
        sig_hits = defaultdict(int)
        sig_trials = defaultdict(int)

        # Sample every 6th extraction for speed (100 per fold)
        step = max(1, BLOCK_SIZE // 100)
        test_indices = range(test_start, test_end, step)

        for idx in test_indices:
            if idx < N or idx + max_colpi >= len(dati):
                continue

            window_start = idx - N
            window_end = idx
            recent_start = idx - max(1, N // 3)
            recent_end = idx

            # Sample 3 wheels
            wheels = random.sample(RUOTE, WHEELS_PER_EXT)

            for ruota in wheels:
                pair_freq, num_freq = compute_window_features(window_start, window_end, ruota)
                recent_pairs = compute_recent_pairs(recent_start, recent_end, ruota)

                sig_pairs = eval_signals_batch(pair_freq, num_freq, recent_pairs, N)

                for sig_name, pairs in sig_pairs.items():
                    for pair in pairs:
                        sig_trials[sig_name] += 1
                        if check_hit(idx, ruota, pair, max_colpi):
                            sig_hits[sig_name] += 1

        for sig_name in ['freq_rit+fib', 'freq+rit+dec', 'hot_cold', 'freq+rit+fig', 'TOP6']:
            trials = sig_trials[sig_name]
            if trials > 0:
                hit_rate = sig_hits[sig_name] / trials
                ratio = hit_rate / p_ambo_9
            else:
                ratio = 0.0
            results[sig_name][N].append(ratio)
            if trials > 0:
                print(f"  {sig_name:20s} N={N:4d}: {sig_hits[sig_name]:3d}/{trials:4d} rate={hit_rate:.4f} ratio={ratio:.2f}")

    print(f"  Fold time: {time.time() - fold_t0:.0f}s")

total_elapsed = time.time() - t0
print(f"\nTotal time: {total_elapsed:.0f}s")

# ── REPORT ──
SIG_NAMES = ['freq_rit+fib', 'freq+rit+dec', 'hot_cold', 'freq+rit+fig', 'TOP6']

print("\n" + "=" * 90)
print("CROSS-VALIDATION RESULTS: mean ratio and min ratio across 5 folds")
print("=" * 90)
header = f"{'Signal':20s} {'N':>5s} {'Mean':>7s} {'Min':>7s} {'Max':>7s} {'Std':>7s} {'Status':>10s}"
print(header)
print("-" * 90)

report_lines = []
best_configs = {}

for sig_name in SIG_NAMES:
    best_mean = 0
    best_N = None
    for N in WINDOW_SIZES:
        ratios = results[sig_name][N]
        if not ratios or len(ratios) < N_FOLDS:
            continue
        mean_r = sum(ratios) / len(ratios)
        min_r = min(ratios)
        max_r = max(ratios)
        std_r = (sum((r - mean_r)**2 for r in ratios) / len(ratios)) ** 0.5
        status = "OK" if min_r > 1.0 else "WEAK"
        line = f"{sig_name:20s} {N:5d} {mean_r:7.3f} {min_r:7.3f} {max_r:7.3f} {std_r:7.3f} {status:>10s}"
        print(line)
        report_lines.append(line)

        if mean_r > best_mean and min_r > 1.0:
            best_mean = mean_r
            best_N = N

    if best_N is not None:
        best_configs[sig_name] = (best_N, best_mean)
    else:
        # Fallback: best mean
        bm, bn = 0, None
        for N in WINDOW_SIZES:
            ratios = results[sig_name][N]
            if ratios:
                m = sum(ratios) / len(ratios)
                if m > bm:
                    bm = m; bn = N
        best_configs[sig_name] = (bn, bm)
    print()

print("=" * 60)
print("OPTIMAL WINDOW SIZES")
print("=" * 60)
optimal_lines = []
for sig_name in SIG_NAMES:
    best_N, best_mean = best_configs[sig_name]
    if best_N is None:
        line = f"  {sig_name:20s} -> NO DATA"
    else:
        ratios = results[sig_name][best_N]
        min_r = min(ratios) if ratios else 0
        robust = "ROBUST" if min_r > 1.0 else "fragile"
        line = f"  {sig_name:20s} -> N={best_N:4d}  mean={best_mean:.3f}  min={min_r:.3f}  [{robust}]"
    print(line)
    optimal_lines.append(line)

# ── SEND TO NTFY ──
title = "K-Fold CV Results - Optimal Window Sizes"
msg_parts = ["K-FOLD TEMPORAL CROSS-VALIDATION", f"5 folds x 600 draws, {total_elapsed:.0f}s", ""]
msg_parts.append(f"p_ambo_9 = {p_ambo_9:.6f}")
msg_parts.append("")
msg_parts.append("OPTIMAL WINDOWS:")
for line in optimal_lines:
    msg_parts.append(line)
msg_parts.append("")
msg_parts.append("FULL TABLE:")
msg_parts.append(header)
for line in report_lines:
    msg_parts.append(line)

msg = "\n".join(msg_parts)
msg = msg.encode('ascii', errors='replace').decode('ascii')
title = title.encode('ascii', errors='replace').decode('ascii')

try:
    resp = httpx.post(
        'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=msg.encode('utf-8'),
        headers={'Title': title, 'Priority': '5'},
        timeout=10.0
    )
    print(f"\nntfy sent: {resp.status_code}")
except Exception as e:
    print(f"\nntfy error: {e}")

print("\nDone.")
