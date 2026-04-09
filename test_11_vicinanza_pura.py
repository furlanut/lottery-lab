"""Test 11 — Filtro vicinanza pura.

Ipotesi: il segnale trovato nei Test 10 (somme alte) e in realta
un proxy per la VICINANZA NUMERICA dei due numeri della coppia.
Coppie con somma 120-170 sono coppie con entrambi i numeri nel range 60-90,
cioe VICINI tra loro. Testiamo il filtro diretto |a-b| <= D.
"""

import sys
sys.path.insert(0, 'backend')

from collections import defaultdict
from itertools import combinations
from pathlib import Path
from datetime import datetime
import random
import math
import httpx

from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import RUOTE

random.seed(42)

# ── Data loading ──────────────────────────────────────────────
print("=== TEST 11 — Filtro vicinanza pura ===", flush=True)
print("Caricamento dati...", flush=True)

ARCHIVIO = Path('archivio_dati/Archivio_Lotto/TXT')
files = [f for f in scan_archivio_txt(ARCHIVIO) if int(f.stem.split('-')[-1]) >= 1946]
all_records = []
for fp in files:
    all_records.extend(parse_file_txt(fp))
by_date = defaultdict(dict)
for r in all_records:
    by_date[r['data'].strftime('%d/%m/%Y')][r['ruota']] = r['numeri']
dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'))

print(f"Estrazioni caricate: {len(dati)}", flush=True)

# ── Pre-compute all pairs per extraction for fast lookup ──────
# For each extraction index, store set of ambo pairs seen across ALL wheels
print("Pre-computing pair index...", flush=True)
pair_at_idx = []  # list of set of (a,b) tuples
for idx, (_, ruote) in enumerate(dati):
    pairs = set()
    for r in RUOTE:
        if r in ruote:
            nums = sorted(ruote[r])
            for a, b in combinations(nums, 2):
                pairs.add((a, b))
    pair_at_idx.append(pairs)
print("Pair index built.", flush=True)

# ── Ambetto check ─────────────────────────────────────────────
def check_ambetto(a, b, estratti):
    e = set(estratti)
    if a in e and b in e:
        return True
    if a in e:
        for n in e:
            if n != a and (n == b - 1 or n == b + 1):
                return True
    if b in e:
        for n in e:
            if n != b and (n == a - 1 or n == a + 1):
                return True
    return False

def check_ambo_secco(a, b, estratti):
    e = set(estratti)
    return a in e and b in e

# ── Probabilita teoriche ──────────────────────────────────────
p_ambo_secco = 1 / math.comb(90, 2)  # 1/4005
p_ambetto_single = 1 / 100.32
p_ambetto_9 = 1 - (1 - p_ambetto_single) ** 9
p_ambo_any = 1 - (1 - p_ambo_secco) ** 10

print(f"P(ambetto, 9 ruote) = {p_ambetto_9:.6f}", flush=True)
print(f"P(ambo secco, 10 ruote) = {p_ambo_any:.6f}", flush=True)

# ── Helper: run proximity filter ──────────────────────────────
def run_proximity(data_slice, D_val, W_val, mode='ambetto', global_offset=0):
    """Run proximity filter on a data slice. Returns (signals, hits, ratio).
    global_offset: offset into dati for pair_at_idx lookup.
    """
    signals = 0
    hits = 0

    for idx in range(W_val, len(data_slice)):
        global_idx = global_offset + idx

        # Build window: count pairs with |a-b| <= D from sampled wheel
        window_pairs = defaultdict(int)
        for w in range(idx - W_val, idx):
            _, ruote_w = data_slice[w]
            available = [r for r in RUOTE if r in ruote_w]
            if not available:
                continue
            ruota = random.choice(available)
            nums = sorted(ruote_w[ruota])
            for a, b in combinations(nums, 2):
                if abs(a - b) <= D_val:
                    window_pairs[(a, b)] += 1

        # Filter: freq >= 1, delay >= W/3
        delay_threshold = W_val // 3
        candidates = []
        for (a, b), freq in window_pairs.items():
            if freq < 1:
                continue
            # Check delay using precomputed pair index
            last_seen = None
            for back in range(global_idx - 1, max(global_idx - W_val - 1, -1), -1):
                if back < 0 or back >= len(pair_at_idx):
                    break
                if (a, b) in pair_at_idx[back]:
                    last_seen = global_idx - back
                    break
            if last_seen is None or last_seen >= delay_threshold:
                candidates.append((a, b))

        if not candidates:
            continue

        # Max 3 pairs
        if len(candidates) > 3:
            candidates = random.sample(candidates, 3)

        signals += len(candidates)

        # Check next extraction
        _, ruote_next = data_slice[idx]
        for a, b in candidates:
            if mode == 'ambetto':
                for r in RUOTE:
                    if r in ruote_next:
                        if check_ambetto(a, b, ruote_next[r]):
                            hits += 1
                            break
            else:  # ambo secco
                for r in RUOTE:
                    if r in ruote_next:
                        if check_ambo_secco(a, b, ruote_next[r]):
                            hits += 1
                            break

    if signals == 0:
        return 0, 0, 0.0
    hit_rate = hits / signals
    if mode == 'ambetto':
        ratio = hit_rate / p_ambetto_9
    else:
        ratio = hit_rate / p_ambo_any
    return signals, hits, ratio


# ── PHASE 1: Discovery (first half) ──────────────────────────
print("\n" + "=" * 60, flush=True)
print("FASE 1 — Discovery (prima meta del dataset)", flush=True)
print("=" * 60, flush=True)

half = len(dati) // 2
first_half = dati[:half]
second_half = dati[half:]

print(f"Prima meta: {len(first_half)} estrazioni", flush=True)
print(f"Seconda meta: {len(second_half)} estrazioni", flush=True)

D_values = [3, 5, 8, 10, 13, 15, 20]
W_values = [50, 75, 100, 125, 150, 200]

results_discovery = []

for D in D_values:
    for W in W_values:
        signals, hits, ratio = run_proximity(first_half, D, W, mode='ambetto', global_offset=0)
        results_discovery.append((D, W, signals, hits, ratio))
        hr = hits / signals if signals > 0 else 0
        print(f"  D={D:2d}, W={W:3d} => segnali={signals:5d}, hit={hits:4d}, "
              f"rate={hr:.4f}, ratio={ratio:.3f}x", flush=True)

# Sort by ratio descending
results_discovery.sort(key=lambda x: x[4], reverse=True)

print("\n--- Top 10 Discovery (ambetto) ---", flush=True)
print(f"{'Rank':>4} {'D':>3} {'W':>4} {'Segnali':>8} {'Hit':>5} {'Rate':>8} {'Ratio':>8}", flush=True)
top10 = results_discovery[:10]
for i, (D, W, sig, hit, ratio) in enumerate(top10, 1):
    hr = hit / sig if sig > 0 else 0
    print(f"{i:4d} {D:3d} {W:4d} {sig:8d} {hit:5d} {hr:8.4f} {ratio:8.3f}x", flush=True)


# ── PHASE 2: Validation (second half) ────────────────────────
print("\n" + "=" * 60, flush=True)
print("FASE 2 — Validation (seconda meta del dataset)", flush=True)
print("=" * 60, flush=True)

results_validation = []
for D, W, _, _, disc_ratio in top10:
    signals, hits, ratio = run_proximity(second_half, D, W, mode='ambetto', global_offset=half)
    hr = hits / signals if signals > 0 else 0
    results_validation.append((D, W, signals, hits, ratio, disc_ratio))
    print(f"  D={D:2d}, W={W:3d} => segnali={signals:5d}, hit={hits:4d}, "
          f"rate={hr:.4f}, ratio={ratio:.3f}x (disc={disc_ratio:.3f}x)", flush=True)


# ── PHASE 3: 5-fold CV on top 5 ──────────────────────────────
print("\n" + "=" * 60, flush=True)
print("FASE 3 — 5-fold CV (ultime 3000 estrazioni)", flush=True)
print("=" * 60, flush=True)

# Pick top 5 by validation ratio
results_validation.sort(key=lambda x: x[4], reverse=True)
top5_val = results_validation[:5]

last3000 = dati[-3000:]
fold_size = 600
offset_3000 = len(dati) - 3000

cv_results = []
for D, W, _, _, val_ratio, disc_ratio in top5_val:
    fold_ratios = []
    for fold in range(5):
        start = fold * fold_size
        end = start + fold_size
        fold_data = last3000[start:end]
        if len(fold_data) < W + 10:
            continue
        _, _, ratio = run_proximity(fold_data, D, W, mode='ambetto',
                                     global_offset=offset_3000 + start)
        fold_ratios.append(ratio)

    if fold_ratios:
        mean_r = sum(fold_ratios) / len(fold_ratios)
        min_r = min(fold_ratios)
        max_r = max(fold_ratios)
    else:
        mean_r = min_r = max_r = 0.0

    cv_results.append((D, W, disc_ratio, val_ratio, mean_r, min_r, max_r, fold_ratios))
    print(f"  D={D:2d}, W={W:3d} => disc={disc_ratio:.3f}x, val={val_ratio:.3f}x, "
          f"CV mean={mean_r:.3f}x, min={min_r:.3f}x, max={max_r:.3f}x", flush=True)
    for fi, fr in enumerate(fold_ratios):
        print(f"    fold {fi}: {fr:.3f}x", flush=True)


# ── PHASE 3b: Ambo secco test on best (D,W) ──────────────────
print("\n" + "=" * 60, flush=True)
print("FASE 3b — Ambo secco (top 3 combinazioni)", flush=True)
print("=" * 60, flush=True)

top3_for_ambo = top5_val[:3]
ambo_results = []
for D, W, _, _, _, _ in top3_for_ambo:
    signals, hits, ratio = run_proximity(second_half, D, W, mode='ambo_secco', global_offset=half)
    hr = hits / signals if signals > 0 else 0
    ambo_results.append((D, W, signals, hits, ratio))
    print(f"  D={D:2d}, W={W:3d} => segnali={signals:5d}, hit={hits:4d}, "
          f"rate={hr:.6f}, ratio={ratio:.3f}x", flush=True)


# ── PHASE 4: Comparison table ─────────────────────────────────
print("\n" + "=" * 60, flush=True)
print("FASE 4 — Tabella comparativa", flush=True)
print("=" * 60, flush=True)

print(f"\n{'Metodo':<25} {'Parametri':<20} {'Discovery':>10} {'Validation':>11} "
      f"{'CV mean':>8} {'CV min':>8}", flush=True)
print("-" * 85, flush=True)

if cv_results:
    best = cv_results[0]
    D_b, W_b, disc_r, val_r, mean_r, min_r, max_r, _ = best
    print(f"{'vicinanza pura':<25} {'D='+str(D_b)+', W='+str(W_b):<20} "
          f"{disc_r:10.3f}x {val_r:11.3f}x {mean_r:8.3f}x {min_r:8.3f}x", flush=True)

print(f"{'somma160 W=100':<25} {'S=160, W=100':<20} "
      f"{'1.386':>10}x {'1.316':>11}x {'1.203':>8}x {'1.107':>8}x", flush=True)
print(f"{'somma72 W=150':<25} {'S=72, W=150':<20} "
      f"{'n/a':>10} {'~1.0':>11}x {'1.219':>8}x {'1.178':>8}x", flush=True)

# ── Conclusion ────────────────────────────────────────────────
print("\n" + "=" * 60, flush=True)
print("CONCLUSIONI", flush=True)
print("=" * 60, flush=True)

if cv_results:
    best_D, best_W, best_disc, best_val, best_mean, best_min, _, _ = cv_results[0]
    if best_mean > 1.20:
        verdict = (f"Vicinanza pura (D={best_D}, W={best_W}) SUPERA somma-based: "
                   f"CV mean {best_mean:.3f}x > 1.20x. "
                   f"La somma era un PROXY per la prossimita.")
    elif best_mean > 1.10:
        verdict = (f"Vicinanza pura (D={best_D}, W={best_W}) COMPARABILE a somma-based: "
                   f"CV mean {best_mean:.3f}x. Segnale presente ma non superiore.")
    else:
        verdict = (f"Vicinanza pura (D={best_D}, W={best_W}) NON supera somma-based: "
                   f"CV mean {best_mean:.3f}x. La somma cattura qualcos'altro.")
else:
    verdict = "Nessun risultato CV disponibile."

print(verdict, flush=True)

if ambo_results:
    best_ambo = max(ambo_results, key=lambda x: x[4])
    D_a, W_a, sig_a, hit_a, ratio_a = best_ambo
    print(f"\nAmbo secco: D={D_a}, W={W_a} => ratio={ratio_a:.3f}x "
          f"({'SEGNALE' if ratio_a > 1.1 else 'no segnale'})", flush=True)

print("\nTest 11 completato.", flush=True)

# ── Notify via ntfy ───────────────────────────────────────────
lines = ["Test 11 - Filtro vicinanza pura\n"]
lines.append("== Top 5 Discovery ==")
for i, (D, W, sig, hit, ratio) in enumerate(results_discovery[:5], 1):
    lines.append(f"{i}. D={D}, W={W}: ratio={ratio:.3f}x")

lines.append("\n== Validation ==")
for D, W, sig, hit, ratio, disc in results_validation[:5]:
    lines.append(f"D={D}, W={W}: val={ratio:.3f}x (disc={disc:.3f}x)")

lines.append("\n== 5-fold CV ==")
for D, W, disc_r, val_r, mean_r, min_r, max_r, _ in cv_results:
    lines.append(f"D={D}, W={W}: mean={mean_r:.3f}x, min={min_r:.3f}x")

lines.append(f"\n== Ambo secco ==")
for D, W, sig, hit, ratio in ambo_results:
    lines.append(f"D={D}, W={W}: ratio={ratio:.3f}x")

lines.append(f"\n{verdict}")

msg = "\n".join(lines)

try:
    resp = httpx.post(
        'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=msg.encode('utf-8'),
        headers={'Title': 'Test 11 Vicinanza Pura', 'Priority': '5'},
        timeout=10.0,
    )
    print(f"\nNotifica ntfy: {resp.status_code}", flush=True)
except Exception as e:
    print(f"\nErrore ntfy: {e}", flush=True)
