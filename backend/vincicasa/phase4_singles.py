"""VinciCasa Fase 4 — Predizione singoli numeri + cinquine ottimali.

Approccio corretto: VinciCasa premia quanti numeri indovini (2/5, 3/5, 4/5, 5/5),
non le coppie. Predire singoli numeri e costruire cinquine ottimali.
"""
from __future__ import annotations

import math
import random
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "backend")

# --- Caricamento dati reali ---
print("Caricamento VinciCasa reale...", flush=True)
DATA_DIR = Path("backend/vincicasa/data")

dati = []  # lista di (date_str, [n1,n2,n3,n4,n5])
for fp in sorted(DATA_DIR.glob("VinciCasa-archivio-estrazioni-*.txt")):
    with open(fp, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for line in lines[3:]:
        parts = line.strip().split("\t")
        if len(parts) < 7:
            continue
        try:
            concorso = int(parts[0].strip())
            data_str = parts[1].strip()
            nums = sorted([int(parts[i].strip()) for i in range(2, 7)])
            if all(1 <= n <= 40 for n in nums) and len(set(nums)) == 5:
                dati.append((data_str, nums))
        except (ValueError, IndexError):
            continue

# Ordina per data
dati.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
print(f"Dataset: {len(dati)} estrazioni reali ({dati[0][0]} - {dati[-1][0]})", flush=True)

half = len(dati) // 2
WINDOWS = [30, 50, 75, 100, 150, 200, 300]

# --- Distribuzione ipergeometrica attesa ---
def hypergeom_pmf(k, N, K, n):
    """P(X=k) per ipergeometrica: N totali, K successi, n estratti."""
    return math.comb(K, k) * math.comb(N - K, n - k) / math.comb(N, n)

# Distribuzione attesa: scelgo 5 numeri su 40, ne estraggono 5 su 40
print("\n--- Distribuzione match attesa (ipergeometrica 5/40 vs 5/40) ---", flush=True)
for k in range(6):
    p = hypergeom_pmf(k, 40, 5, 5)
    print(f"  P({k}/5) = {p:.6f} = 1/{1/p:.0f}" if p > 0 else f"  P({k}/5) = {p:.10f}", flush=True)

# ================================================================
print("\n" + "=" * 70, flush=True)
print("  TEST A — Frequenza singoli numeri nella finestra", flush=True)
print("=" * 70, flush=True)

def test_frequency(dati, start, end, W, strategy="top"):
    """Seleziona 5 numeri per frequenza e conta match."""
    matches = Counter()  # k -> count
    total = 0
    
    for idx in range(start, min(end, len(dati) - 1)):
        if idx < W:
            continue
        # Frequenza nelle ultime W estrazioni
        freq = Counter()
        for back in range(1, W + 1):
            bi = idx - back
            if bi < 0:
                break
            for n in dati[bi][1]:
                freq[n] += 1
        
        if strategy == "top":
            selected = [n for n, _ in freq.most_common(5)]
        elif strategy == "bottom":
            all_nums = list(range(1, 41))
            all_nums.sort(key=lambda n: freq.get(n, 0))
            selected = all_nums[:5]
        elif strategy == "ritardo":
            # Numeri con ritardo piu' alto (non usciti da piu' tempo)
            last_seen = {}
            for back in range(1, W + 1):
                bi = idx - back
                if bi < 0:
                    break
                for n in dati[bi][1]:
                    if n not in last_seen:
                        last_seen[n] = back
            all_nums = list(range(1, 41))
            all_nums.sort(key=lambda n: last_seen.get(n, W + 1), reverse=True)
            selected = all_nums[:5]
        else:
            selected = list(range(1, 6))
        
        # Conta match con estrazione successiva
        actual = set(dati[idx + 1][1])
        k = len(set(selected) & actual)
        matches[k] += 1
        total += 1
    
    return matches, total

print(f"\n{'W':>4} {'STRAT':>8} {'0/5':>7} {'1/5':>7} {'2/5':>7} {'3/5':>7} {'4/5':>7} {'5/5':>7} {'EV':>8}", flush=True)
print("-" * 70, flush=True)

# Premi
PREMI = {0: 0, 1: 0, 2: 2.60, 3: 20, 4: 200, 5: 500000}
COSTO = 2.0

# Baseline ipergeometrica
base_ev = sum(hypergeom_pmf(k, 40, 5, 5) * PREMI[k] for k in range(6))
print(f"{'---':>4} {'BASE':>8}", end="", flush=True)
for k in range(6):
    p = hypergeom_pmf(k, 40, 5, 5)
    print(f" {p*100:>6.2f}%", end="")
print(f" {base_ev:>7.3f}", flush=True)

best_results = {}
for strategy in ["top", "bottom", "ritardo"]:
    for W in WINDOWS:
        matches, total = test_frequency(dati, half, len(dati), W, strategy)
        ev = sum(matches.get(k, 0) / total * PREMI[k] for k in range(6)) if total > 0 else 0
        
        row = f"{W:>4} {strategy:>8}"
        for k in range(6):
            pct = matches.get(k, 0) / total * 100 if total > 0 else 0
            row += f" {pct:>6.2f}%"
        
        marker = " <<<" if ev > base_ev * 1.1 else (" <" if ev > base_ev * 1.05 else "")
        row += f" {ev:>7.3f}{marker}"
        print(row, flush=True)
        
        best_results[(strategy, W)] = ev

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST B — Numeri caldi + ritardo combinato", flush=True)
print("=" * 70, flush=True)

def test_hot_delayed(dati, start, end, W):
    """Numeri attivi nella finestra ma con ritardo alto."""
    matches = Counter()
    total = 0
    
    for idx in range(start, min(end, len(dati) - 1)):
        if idx < W:
            continue
        freq = Counter()
        last_seen = {}
        for back in range(1, W + 1):
            bi = idx - back
            if bi < 0:
                break
            for n in dati[bi][1]:
                freq[n] += 1
                if n not in last_seen:
                    last_seen[n] = back
        
        # Attivi (freq >= 1) ma in ritardo (last_seen alto)
        active = [n for n in range(1, 41) if freq.get(n, 0) >= 1]
        active.sort(key=lambda n: last_seen.get(n, 0), reverse=True)
        selected = active[:5]
        
        if len(selected) < 5:
            continue
        
        actual = set(dati[idx + 1][1])
        k = len(set(selected) & actual)
        matches[k] += 1
        total += 1
    
    return matches, total

print(f"\n{'W':>4} {'STRAT':>10} {'0/5':>7} {'1/5':>7} {'2/5':>7} {'3/5':>7} {'4/5':>7} {'EV':>8}", flush=True)
print("-" * 60, flush=True)

for W in WINDOWS:
    matches, total = test_hot_delayed(dati, half, len(dati), W)
    ev = sum(matches.get(k, 0) / total * PREMI[k] for k in range(6)) if total > 0 else 0
    row = f"{W:>4} {'hot+delay':>10}"
    for k in range(6):
        if k == 5:
            continue
        pct = matches.get(k, 0) / total * 100 if total > 0 else 0
        row += f" {pct:>6.2f}%"
    marker = " <<<" if ev > base_ev * 1.1 else (" <" if ev > base_ev * 1.05 else "")
    row += f" {ev:>7.3f}{marker}"
    print(row, flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST C — EV reale per categoria", flush=True)
print("=" * 70, flush=True)

# Calcola EV dettagliato per il miglior filtro
print(f"\nEV baseline (casuale):", flush=True)
for k in range(6):
    p = hypergeom_pmf(k, 40, 5, 5)
    premio = PREMI[k]
    ev_k = p * premio
    print(f"  {k}/5: P={p:.6f} × EUR {premio:>10.2f} = EUR {ev_k:.4f}", flush=True)
print(f"  EV totale = EUR {base_ev:.4f}", flush=True)
print(f"  Costo = EUR {COSTO:.2f}", flush=True)
print(f"  House edge = {(1 - base_ev/COSTO)*100:.2f}%", flush=True)

# Quanto deve migliorare P(2/5) per breakeven?
# Se miglioriamo P(match) del x%, ogni categoria migliora
# EV(boost) = sum(P_k * boost_k * premio_k)
print(f"\n--- Sensibilita' al boost ---", flush=True)
print(f"Se il filtro aumenta P(ogni match) del X%:", flush=True)

for boost_pct in [5, 10, 15, 20, 30, 50]:
    boost = 1 + boost_pct / 100
    ev_boosted = sum(hypergeom_pmf(k, 40, 5, 5) * boost * PREMI[k] for k in range(6))
    gap = COSTO - ev_boosted
    print(f"  +{boost_pct}%: EV = EUR {ev_boosted:.4f}, gap = EUR {gap:+.4f} {'PROFITTO!' if gap < 0 else ''}", flush=True)

breakeven_boost = COSTO / base_ev
print(f"\n  Breakeven boost: {(breakeven_boost-1)*100:.1f}% su tutte le categorie", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST D — Costruzione cinquina ottimale", flush=True)
print("=" * 70, flush=True)

strategies_d = {
    "top5_freq": lambda freq, last, W: sorted(freq.keys(), key=lambda n: -freq[n])[:5],
    "top5_rit": lambda freq, last, W: sorted(range(1,41), key=lambda n: last.get(n, W+1), reverse=True)[:5],
    "3freq+2rit": lambda freq, last, W: _mix_strategy(freq, last, W),
    "4decine": lambda freq, last, W: _decade_strategy(freq, last),
    "1decina": lambda freq, last, W: _single_decade(freq, last),
    "media_sum": lambda freq, last, W: _target_sum(freq, last, 102.5),
}

def _mix_strategy(freq, last, W):
    top_freq = sorted(freq.keys(), key=lambda n: -freq[n])[:3]
    remaining = [n for n in range(1,41) if n not in top_freq and freq.get(n,0) >= 1]
    remaining.sort(key=lambda n: last.get(n, W+1), reverse=True)
    return top_freq + remaining[:2]

def _decade_strategy(freq, last):
    result = []
    for d in range(4):
        dec_nums = [n for n in range(d*10+1, d*10+11)]
        dec_nums.sort(key=lambda n: -freq.get(n, 0))
        if dec_nums:
            result.append(dec_nums[0])
    # 5° da decina con piu' frequenza
    all_remaining = [n for n in range(1,41) if n not in result]
    all_remaining.sort(key=lambda n: -freq.get(n, 0))
    if all_remaining:
        result.append(all_remaining[0])
    return result[:5]

def _single_decade(freq, last):
    # Decina con piu' frequenza totale
    dec_freq = Counter()
    for n, f in freq.items():
        dec_freq[(n-1)//10] += f
    best_dec = dec_freq.most_common(1)[0][0] if dec_freq else 0
    dec_nums = [n for n in range(best_dec*10+1, best_dec*10+11)]
    dec_nums.sort(key=lambda n: -freq.get(n, 0))
    return dec_nums[:5]

def _target_sum(freq, last, target):
    # Scegli 5 numeri la cui somma sia vicina al target
    best = None
    best_diff = 999
    candidates = sorted(freq.keys(), key=lambda n: -freq[n])[:15]
    for combo in combinations(candidates, 5):
        diff = abs(sum(combo) - target)
        if diff < best_diff:
            best_diff = diff
            best = list(combo)
    return best if best else list(range(1,6))

# Test tutte le strategie con W=50 (discovery su prima meta')
W_test = 50

print(f"\nW={W_test}, discovery su prima meta':", flush=True)
print(f"{'STRATEGIA':>15} {'0/5':>7} {'1/5':>7} {'2/5':>7} {'3/5':>7} {'4/5':>7} {'EV':>8} {'vs BASE':>8}", flush=True)
print("-" * 70, flush=True)

strategy_evs = {}
for name, fn in strategies_d.items():
    matches = Counter()
    total = 0
    for idx in range(W_test, half):
        freq = Counter()
        last_seen = {}
        for back in range(1, W_test + 1):
            bi = idx - back
            if bi < 0:
                break
            for n in dati[bi][1]:
                freq[n] += 1
                if n not in last_seen:
                    last_seen[n] = back
        
        selected = fn(freq, last_seen, W_test)
        if not selected or len(selected) < 5:
            continue
        
        actual = set(dati[idx + 1][1] if idx + 1 < len(dati) else [])
        k = len(set(selected) & actual)
        matches[k] += 1
        total += 1
    
    ev = sum(matches.get(k, 0) / total * PREMI[k] for k in range(6)) if total > 0 else 0
    ratio = ev / base_ev if base_ev > 0 else 0
    strategy_evs[name] = (ev, ratio, matches, total)
    
    row = f"{name:>15}"
    for k in range(6):
        if k == 5:
            continue
        pct = matches.get(k, 0) / total * 100 if total > 0 else 0
        row += f" {pct:>6.2f}%"
    marker = " <<<" if ratio > 1.1 else (" <" if ratio > 1.05 else "")
    row += f" {ev:>7.3f} {ratio:>7.3f}x{marker}"
    print(row, flush=True)

# Top 3 per validazione
print(f"\n--- Validazione seconda meta' e 5-fold CV (top 3) ---", flush=True)
ranked = sorted(strategy_evs.items(), key=lambda x: -x[1][1])[:3]

for name, (ev_disc, ratio_disc, _, _) in ranked:
    fn = strategies_d[name]
    # Validazione
    matches_val = Counter()
    total_val = 0
    for idx in range(half, len(dati) - 1):
        if idx < W_test:
            continue
        freq = Counter()
        last_seen = {}
        for back in range(1, W_test + 1):
            bi = idx - back
            if bi < 0:
                break
            for n in dati[bi][1]:
                freq[n] += 1
                if n not in last_seen:
                    last_seen[n] = back
        selected = fn(freq, last_seen, W_test)
        if not selected or len(selected) < 5:
            continue
        actual = set(dati[idx + 1][1])
        k = len(set(selected) & actual)
        matches_val[k] += 1
        total_val += 1
    
    ev_val = sum(matches_val.get(k, 0) / total_val * PREMI[k] for k in range(6)) if total_val > 0 else 0
    ratio_val = ev_val / base_ev if base_ev > 0 else 0
    
    # 5-fold CV
    fold_size = len(dati) // 5
    fold_ratios = []
    for fold in range(5):
        s = fold * fold_size
        e = s + fold_size
        m_f = Counter(); t_f = 0
        for idx in range(s, min(e, len(dati) - 1)):
            if idx < W_test:
                continue
            freq = Counter(); last_seen = {}
            for back in range(1, W_test + 1):
                bi = idx - back
                if bi < 0: break
                for n in dati[bi][1]:
                    freq[n] += 1
                    if n not in last_seen: last_seen[n] = back
            sel = fn(freq, last_seen, W_test)
            if not sel or len(sel) < 5: continue
            actual = set(dati[idx + 1][1])
            k = len(set(sel) & actual)
            m_f[k] += 1; t_f += 1
        ev_f = sum(m_f.get(k, 0) / t_f * PREMI[k] for k in range(6)) if t_f > 0 else 0
        fold_ratios.append(ev_f / base_ev if base_ev > 0 else 0)
    
    mean_cv = sum(fold_ratios) / len(fold_ratios)
    min_cv = min(fold_ratios)
    fold_str = " ".join(f"{r:.3f}" for r in fold_ratios)
    print(f"  {name}: disc={ratio_disc:.3f}x val={ratio_val:.3f}x CV=[{fold_str}] mean={mean_cv:.3f}x min={min_cv:.3f}x", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  VERDETTO FINALE", flush=True)
print("=" * 70, flush=True)

print(f"""
EV baseline: EUR {base_ev:.4f} per giocata
Costo: EUR {COSTO:.2f}
House edge: {(1-base_ev/COSTO)*100:.2f}%
Breakeven boost: +{(breakeven_boost-1)*100:.1f}% su tutte le categorie

Per diventare profittevole serve che OGNI categoria di match
migliori del {(breakeven_boost-1)*100:.1f}% rispetto al caso.
""", flush=True)

# Notifica
import httpx
msg = f"VINCICASA SINGOLI NUMERI\n\nEV baseline: {base_ev:.3f}\nBreakeven: +{(breakeven_boost-1)*100:.0f}%\n"
msg += "Dettagli nel terminale."
try:
    httpx.post('https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=msg.encode('utf-8'),
        headers={'Title': 'VinciCasa Singoli Numeri', 'Priority': '5'},
        timeout=10.0)
except Exception:
    pass

print("\nDone.", flush=True)
