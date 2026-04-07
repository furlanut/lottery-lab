#!/usr/bin/env python3
"""Systematic gap-filling research: sliding-fold window optimization, combos, ROMA 21-30."""
import sys
sys.path.insert(0, 'backend')

from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from datetime import datetime
from statistics import mean, median
import math, httpx

from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist

# ── DATA LOADING ──────────────────────────────────────────────────────────────
print("[LOAD] Loading archive...", flush=True)
ARCHIVIO = Path('archivio_dati/Archivio_Lotto/TXT')
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split('-')[-1]) >= 1946]
all_records = []
for fp in files:
    all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records:
    by_date[r['data'].strftime('%d/%m/%Y')][r['ruota']] = r['numeri']
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'))
print(f"[LOAD] {len(dati)} estrazioni caricate", flush=True)

max_colpi = 9
p_ambo_9 = 1 - (1 - 1 / 400.5) ** max_colpi

# ── BACKTEST FUNCTION ─────────────────────────────────────────────────────────
def bt_signal(dati, start, end, ruota, signal_fn, window):
    signals = 0; hits = 0; soglia_rit = window // 3
    for idx in range(start, min(end, len(dati) - max_colpi)):
        if idx < window:
            continue
        pf = Counter(); pl = {}; nf = Counter()
        for back in range(1, window + 1):
            bi = idx - back
            if bi < 0:
                break
            _, bw = dati[bi]
            if ruota not in bw:
                continue
            for n in bw[ruota]:
                nf[n] += 1
            for a, b in combinations(sorted(bw[ruota]), 2):
                pf[(a, b)] += 1
                if (a, b) not in pl:
                    pl[(a, b)] = back
        avg_nf = sum(nf.values()) / 90 if nf else 1
        ctx = {'nf': nf, 'avg': avg_nf, 'soglia_rit': soglia_rit}
        for pair, freq in pf.items():
            last = pl.get(pair, window)
            if signal_fn(pair, freq, last, ctx):
                signals += 1
                for colpo in range(1, max_colpi + 1):
                    fi = idx + colpo
                    if fi >= len(dati):
                        break
                    _, fw = dati[fi]
                    if ruota in fw:
                        if pair[0] in set(fw[ruota]) and pair[1] in set(fw[ruota]):
                            hits += 1
                            break
                if signals > 1500:
                    break
        if signals > 1500:
            break
    rate = hits / signals if signals > 0 else 0
    return signals, hits, rate / p_ambo_9 if p_ambo_9 > 0 else 0

# ── SIGNAL DEFINITIONS ───────────────────────────────────────────────────────
FIB = {1, 2, 3, 5, 8, 13, 21, 34}

def sig_freq_rit_dec(pair, freq, last, ctx):
    a, b = pair
    return freq >= 1 and last >= ctx['soglia_rit'] and (a - 1) // 10 == (b - 1) // 10

def sig_freq_rit_fig(pair, freq, last, ctx):
    a, b = pair
    fa, fb = a, b
    while fa >= 10:
        fa = sum(int(d) for d in str(fa))
    while fb >= 10:
        fb = sum(int(d) for d in str(fb))
    return freq >= 1 and last >= ctx['soglia_rit'] and fa == fb

def sig_freq_rit_fib(pair, freq, last, ctx):
    a, b = pair
    return freq >= 2 and last >= ctx['soglia_rit'] and cyclo_dist(a, b) in FIB

def sig_somma72(pair, freq, last, ctx):
    return pair[0] + pair[1] == 72 and freq >= 1 and last >= ctx['soglia_rit']

def sig_hot_cold(pair, freq, last, ctx):
    a, b = pair
    ha = ctx['nf'].get(a, 0) > ctx['avg'] * 1.5
    hb = ctx['nf'].get(b, 0) > ctx['avg'] * 1.5
    ca = ctx['nf'].get(a, 0) < ctx['avg'] * 0.5
    cb = ctx['nf'].get(b, 0) < ctx['avg'] * 0.5
    return (ha and cb) or (hb and ca)

def sig_fib_dist(pair, freq, last, ctx):
    return cyclo_dist(pair[0], pair[1]) in FIB and freq >= 1 and last >= ctx['soglia_rit']

def sig_combo_dec_somma72(pair, freq, last, ctx):
    a, b = pair
    is_dec = (a - 1) // 10 == (b - 1) // 10
    is_s72 = a + b == 72
    return freq >= 1 and last >= ctx['soglia_rit'] and (is_dec or is_s72)

# ── EXPERIMENT 1: Sliding-fold window optimization ────────────────────────────
print("\n" + "=" * 70, flush=True)
print("EXPERIMENT 1: Sliding-fold window optimization", flush=True)
print("=" * 70, flush=True)

SIGNALS = {
    'freq_rit_dec': sig_freq_rit_dec,
    'freq_rit_fig': sig_freq_rit_fig,
    'freq_rit_fib': sig_freq_rit_fib,
    'somma72': sig_somma72,
    'hot_cold': sig_hot_cold,
    'fib_dist': sig_fib_dist,
}
WINDOWS = [50, 75, 100, 125, 150, 175, 200]
SAMPLE_RUOTE = ['BARI', 'ROMA', 'NAPOLI']  # 3 wheels for speed
STEP = 50

exp1_results = {}
best_windows = {}

for sig_name, sig_fn in SIGNALS.items():
    print(f"\n--- Signal: {sig_name} ---", flush=True)
    exp1_results[sig_name] = {}
    for W in WINDOWS:
        ratios = []
        for ruota in SAMPLE_RUOTE:
            fold_start = W
            while fold_start + W < len(dati) - max_colpi:
                fold_end = fold_start + W
                sigs, hits, ratio = bt_signal(dati, fold_start, fold_end, ruota, sig_fn, W)
                if sigs >= 5:  # minimum significance
                    ratios.append(ratio)
                fold_start += STEP
        if ratios:
            m = mean(ratios)
            md = median(ratios)
            above1 = sum(1 for r in ratios if r >= 1.0) / len(ratios) * 100
            above16 = sum(1 for r in ratios if r >= 1.6) / len(ratios) * 100
            exp1_results[sig_name][W] = {
                'mean': m, 'median': md,
                'above1': above1, 'above16': above16,
                'n_folds': len(ratios)
            }
            print(f"  W={W:3d}: mean={m:.3f} med={md:.3f} >1.0={above1:.0f}% >1.6={above16:.0f}% (n={len(ratios)})", flush=True)
        else:
            exp1_results[sig_name][W] = {'mean': 0, 'median': 0, 'above1': 0, 'above16': 0, 'n_folds': 0}
            print(f"  W={W:3d}: no data", flush=True)
    # Find best window by mean ratio
    valid = {w: v for w, v in exp1_results[sig_name].items() if v['n_folds'] > 0}
    if valid:
        best_w = max(valid, key=lambda w: valid[w]['mean'])
        best_windows[sig_name] = best_w
        print(f"  >> Best W for {sig_name}: {best_w} (mean={valid[best_w]['mean']:.3f})", flush=True)

# ── EXPERIMENT 2: Combinations ───────────────────────────────────────────────
print("\n" + "=" * 70, flush=True)
print("EXPERIMENT 2: Signal combinations", flush=True)
print("=" * 70, flush=True)

def sig_dec_AND_somma72(pair, freq, last, ctx):
    return sig_freq_rit_dec(pair, freq, last, ctx) and sig_somma72(pair, freq, last, ctx)

def sig_dec_AND_fib(pair, freq, last, ctx):
    return sig_freq_rit_dec(pair, freq, last, ctx) and sig_fib_dist(pair, freq, last, ctx)

def sig_dec_OR_fig(pair, freq, last, ctx):
    return sig_freq_rit_dec(pair, freq, last, ctx) or sig_freq_rit_fig(pair, freq, last, ctx)

COMBOS = {
    'dec_AND_somma72': sig_dec_AND_somma72,
    'dec_AND_fib_dist': sig_dec_AND_fib,
    'dec_OR_fig': sig_dec_OR_fig,
}

# Use best window from experiment 1 for the primary signal
combo_W = best_windows.get('freq_rit_dec', 100)
print(f"Using W={combo_W} from exp1 best for freq_rit_dec", flush=True)

exp2_results = {}
for combo_name, combo_fn in COMBOS.items():
    print(f"\n--- Combo: {combo_name} (W={combo_W}) ---", flush=True)
    ratios = []
    total_sigs = 0
    total_hits = 0
    for ruota in SAMPLE_RUOTE:
        fold_start = combo_W
        while fold_start + combo_W < len(dati) - max_colpi:
            fold_end = fold_start + combo_W
            sigs, hits, ratio = bt_signal(dati, fold_start, fold_end, ruota, combo_fn, combo_W)
            if sigs >= 3:
                ratios.append(ratio)
            total_sigs += sigs
            total_hits += hits
            fold_start += STEP
    if ratios:
        m = mean(ratios)
        md = median(ratios)
        above1 = sum(1 for r in ratios if r >= 1.0) / len(ratios) * 100
        above16 = sum(1 for r in ratios if r >= 1.6) / len(ratios) * 100
        global_ratio = (total_hits / total_sigs / p_ambo_9) if total_sigs > 0 else 0
        exp2_results[combo_name] = {
            'mean': m, 'median': md, 'above1': above1, 'above16': above16,
            'n_folds': len(ratios), 'total_sigs': total_sigs, 'total_hits': total_hits,
            'global_ratio': global_ratio
        }
        print(f"  mean={m:.3f} med={md:.3f} >1.0={above1:.0f}% >1.6={above16:.0f}% (n={len(ratios)}, sigs={total_sigs}, hits={total_hits}, global={global_ratio:.3f})", flush=True)
    else:
        exp2_results[combo_name] = {'mean': 0, 'median': 0, 'above1': 0, 'above16': 0, 'n_folds': 0, 'total_sigs': 0, 'total_hits': 0, 'global_ratio': 0}
        print(f"  no data", flush=True)

# ── EXPERIMENT 3: ROMA 21-30 window optimization ─────────────────────────────
print("\n" + "=" * 70, flush=True)
print("EXPERIMENT 3: ROMA decina 21-30 window optimization", flush=True)
print("=" * 70, flush=True)

def sig_roma_dec2130(pair, freq, last, ctx):
    a, b = pair
    return (freq >= 1 and last >= ctx['soglia_rit']
            and 21 <= a <= 30 and 21 <= b <= 30)

STEP3 = 30
exp3_results = {}
for W in WINDOWS:
    ratios = []
    total_sigs = 0
    total_hits = 0
    fold_start = W
    while fold_start + W < len(dati) - max_colpi:
        fold_end = fold_start + W
        sigs, hits, ratio = bt_signal(dati, fold_start, fold_end, 'ROMA', sig_roma_dec2130, W)
        if sigs >= 2:
            ratios.append(ratio)
        total_sigs += sigs
        total_hits += hits
        fold_start += STEP3
    if ratios:
        m = mean(ratios)
        md = median(ratios)
        above1 = sum(1 for r in ratios if r >= 1.0) / len(ratios) * 100
        above16 = sum(1 for r in ratios if r >= 1.6) / len(ratios) * 100
        global_ratio = (total_hits / total_sigs / p_ambo_9) if total_sigs > 0 else 0
        exp3_results[W] = {
            'mean': m, 'median': md, 'above1': above1, 'above16': above16,
            'n_folds': len(ratios), 'total_sigs': total_sigs, 'total_hits': total_hits,
            'global_ratio': global_ratio
        }
        print(f"  W={W:3d}: mean={m:.3f} med={md:.3f} >1.0={above1:.0f}% >1.6={above16:.0f}% (n={len(ratios)}, sigs={total_sigs}, global={global_ratio:.3f})", flush=True)
    else:
        exp3_results[W] = {'mean': 0, 'median': 0, 'above1': 0, 'above16': 0, 'n_folds': 0, 'total_sigs': 0, 'total_hits': 0, 'global_ratio': 0}
        print(f"  W={W:3d}: no data", flush=True)

valid3 = {w: v for w, v in exp3_results.items() if v['n_folds'] > 0}
best_w3 = max(valid3, key=lambda w: valid3[w]['mean']) if valid3 else 0
print(f"  >> Best W for ROMA 21-30: {best_w3} (mean={valid3[best_w3]['mean']:.3f})" if valid3 else "  >> No data", flush=True)

# ── SUMMARY & NTFY ───────────────────────────────────────────────────────────
print("\n" + "=" * 70, flush=True)
print("FINAL SUMMARY", flush=True)
print("=" * 70, flush=True)

lines = []
lines.append("=== EXP1: Optimal Windows ===")
for sig_name in SIGNALS:
    bw = best_windows.get(sig_name, '?')
    r = exp1_results[sig_name].get(bw, {})
    lines.append(f"{sig_name}: W={bw} mean={r.get('mean',0):.3f} med={r.get('median',0):.3f} >1.0={r.get('above1',0):.0f}% >1.6={r.get('above16',0):.0f}%")

lines.append("")
lines.append("=== EXP2: Combos ===")
for cn, cr in exp2_results.items():
    lines.append(f"{cn}: mean={cr['mean']:.3f} med={cr['median']:.3f} >1.0={cr['above1']:.0f}% >1.6={cr['above16']:.0f}% global={cr['global_ratio']:.3f} (sigs={cr['total_sigs']})")

lines.append("")
lines.append(f"=== EXP3: ROMA 21-30 (best W={best_w3}) ===")
for W in WINDOWS:
    r = exp3_results[W]
    lines.append(f"W={W}: mean={r['mean']:.3f} med={r['median']:.3f} >1.0={r['above1']:.0f}% >1.6={r['above16']:.0f}% global={r['global_ratio']:.3f}")

summary = "\n".join(lines)
print(summary, flush=True)

# Send to ntfy
try:
    resp = httpx.post(
        'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=summary.encode('utf-8'),
        headers={'Title': 'Research Gaps: 3 experiments complete', 'Priority': '5'},
        timeout=10.0
    )
    print(f"\n[NTFY] Sent ({resp.status_code})", flush=True)
except Exception as e:
    print(f"\n[NTFY] Failed: {e}", flush=True)

print("\nDONE.", flush=True)
