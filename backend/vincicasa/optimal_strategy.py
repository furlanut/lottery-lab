"""VinciCasa Optimal Strategy — V10/V11/V12."""
from __future__ import annotations
import sys; sys.path.insert(0, 'backend')
import math, random
from collections import Counter
from sqlalchemy import select
from lotto_predictor.models.database import get_session
from vincicasa.models.database import VinciCasaEstrazione
import httpx

session = get_session()
rows = session.execute(select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data)).scalars().all()
dati = [sorted([r.n1, r.n2, r.n3, r.n4, r.n5]) for r in rows]
session.close()
print(f"Dataset: {len(dati)} estrazioni\n", flush=True)

PREMI = {0: 0, 1: 0, 2: 2.60, 3: 20, 4: 200, 5: 500000}
N = 5
BASELINE_2 = math.comb(5,2)*math.comb(35,3)/math.comb(40,5)

# ================================================================
print("=" * 70, flush=True)
print("  TEST V10 — Pool esteso + dispersione", flush=True)
print("=" * 70, flush=True)

def get_freq_pool(dati, idx, n_window=5):
    freq = Counter()
    for back in range(n_window):
        if idx - back < 0: break
        for n in dati[idx - back]:
            freq[n] += 1
    return freq

def build_dispersed_tickets(pool, n_tickets):
    """Costruisci n_tickets cinquine in dispersione dal pool."""
    tickets = []
    used = set()
    remaining = list(pool)
    for _ in range(n_tickets):
        ticket = []
        for n in remaining:
            if n not in used and len(ticket) < 5:
                ticket.append(n)
                used.add(n)
        if len(ticket) == 5:
            tickets.append(sorted(ticket))
        remaining = [n for n in remaining if n not in used]
    return tickets

print(f"\n{'POOL':>6} {'TICKETS':>8} {'COSTO':>6} {'P(>=2/5)':>9} {'P(>=3/5)':>9} {'EV':>8} {'ROI':>8}", flush=True)
print("-" * 60, flush=True)

configs_v10 = {}
for pool_size in [5, 10, 15, 20, 25]:
    n_tickets = pool_size // 5
    
    any_2_count = 0; any_3_count = 0; total_ev = 0; total = 0
    
    for idx in range(N, len(dati) - 1):
        freq = get_freq_pool(dati, idx, N)
        top_pool = [n for n, _ in freq.most_common(pool_size)]
        
        if len(top_pool) < pool_size:
            continue
        
        tickets = build_dispersed_tickets(top_pool, n_tickets)
        if len(tickets) < n_tickets:
            continue
        
        draw = set(dati[idx + 1])
        round_ev = 0; best_k = 0
        for ticket in tickets:
            k = len(set(ticket) & draw)
            round_ev += PREMI[k]
            best_k = max(best_k, k)
        
        if best_k >= 2: any_2_count += 1
        if best_k >= 3: any_3_count += 1
        total_ev += round_ev
        total += 1
    
    costo = n_tickets * 2
    ev = total_ev / total if total > 0 else 0
    p2 = any_2_count / total * 100 if total > 0 else 0
    p3 = any_3_count / total * 100 if total > 0 else 0
    roi = (ev - costo) / costo * 100 if costo > 0 else 0
    configs_v10[pool_size] = (p2, p3, ev, costo, roi, total)
    
    print(f"{pool_size:>6} {n_tickets:>8} {costo:>5}€ {p2:>8.2f}% {p3:>8.2f}% {ev:>7.3f}€ {roi:>+7.1f}%", flush=True)

# Confronto con random dispersione
print(f"\n--- Confronto con dispersione RANDOM ---", flush=True)
random.seed(42)
for pool_size in [5, 10, 15, 20, 25]:
    n_tickets = pool_size // 5
    any_2_count = 0; total_ev = 0; total = 0
    
    for idx in range(N, len(dati) - 1):
        rand_pool = random.sample(range(1, 41), pool_size)
        tickets = build_dispersed_tickets(rand_pool, n_tickets)
        if len(tickets) < n_tickets: continue
        
        draw = set(dati[idx + 1])
        round_ev = 0; best_k = 0
        for ticket in tickets:
            k = len(set(ticket) & draw)
            round_ev += PREMI[k]
            best_k = max(best_k, k)
        
        if best_k >= 2: any_2_count += 1
        total_ev += round_ev
        total += 1
    
    costo = n_tickets * 2
    ev = total_ev / total if total > 0 else 0
    p2 = any_2_count / total * 100 if total > 0 else 0
    p2_cald = configs_v10[pool_size][0]
    diff = p2_cald - p2
    print(f"  Pool {pool_size}: random P(2/5)={p2:.2f}%, caldi P(2/5)={p2_cald:.2f}%, diff={diff:+.2f}%", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V11 — Frequenza vs recenza", flush=True)
print("=" * 70, flush=True)

strategies_v11 = {
    "top5_freq": lambda idx: [n for n, _ in get_freq_pool(dati, idx, 5).most_common(5)],
    "ultima (t)": lambda idx: list(dati[idx]),
    "penultima (t-1)": lambda idx: list(dati[idx-1]) if idx > 0 else [],
    "t-2": lambda idx: list(dati[idx-2]) if idx > 1 else [],
    "anti_recenti": lambda idx: sorted(range(1,41), key=lambda n: -min(
        (back for back in range(5) if idx-back >= 0 and n in dati[idx-back]),
        default=99
    ))[:5],
    "freq_pura (2+)": lambda idx: [n for n, c in get_freq_pool(dati, idx, 5).most_common() if c >= 2][:5],
}

print(f"\n{'STRATEGIA':>20} {'2/5 RATE':>9} {'BASELINE':>9} {'DIFF':>7} {'3/5 RATE':>9}", flush=True)
print("-" * 58, flush=True)

for name, fn in strategies_v11.items():
    hits_2 = 0; hits_3 = 0; total = 0
    for idx in range(N, len(dati) - 1):
        selected = fn(idx)
        if not selected or len(selected) < 5: continue
        selected = selected[:5]
        k = len(set(selected) & set(dati[idx + 1]))
        if k >= 2: hits_2 += 1
        if k >= 3: hits_3 += 1
        total += 1
    
    r2 = hits_2/total*100 if total > 0 else 0
    r3 = hits_3/total*100 if total > 0 else 0
    diff = r2 - BASELINE_2*100
    marker = " <<<" if diff > 1.5 else (" <" if diff > 0.5 else "")
    print(f"{name:>20} {r2:>8.2f}% {BASELINE_2*100:>8.2f}% {diff:>+6.2f}%{marker} {r3:>8.2f}%", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V12 — Permutation + split per miglior dispersione", flush=True)
print("=" * 70, flush=True)

# Miglior config dal V10: troviamola
best_pool = max(configs_v10, key=lambda k: configs_v10[k][0] - configs_v10[k][3]/2)  # P(2/5) normalizzato per costo
print(f"  Miglior pool: {best_pool} numeri ({best_pool//5} cinquine)\n", flush=True)

# Funzione per la miglior strategia
def calc_rate_dispersed(data_seq, pool_size=best_pool, n_window=5):
    n_tickets = pool_size // 5
    any_2 = 0; total = 0
    for idx in range(n_window, len(data_seq) - 1):
        freq = Counter()
        for back in range(n_window):
            if idx - back < 0: break
            for n in data_seq[idx - back]:
                freq[n] += 1
        top = [n for n, _ in freq.most_common(pool_size)]
        if len(top) < pool_size: continue
        tickets = build_dispersed_tickets(top, n_tickets)
        if len(tickets) < n_tickets: continue
        draw = set(data_seq[idx + 1])
        best_k = max(len(set(t) & draw) for t in tickets)
        if best_k >= 2: any_2 += 1
        total += 1
    return any_2 / total if total > 0 else 0, any_2, total

rate_obs, h_obs, t_obs = calc_rate_dispersed(dati)
print(f"  Rate P(>=2/5) osservato: {rate_obs*100:.3f}% ({h_obs}/{t_obs})", flush=True)

# Permutation test
print(f"\n  Permutation test (10.000 shuffle)...", flush=True)
random.seed(42)
perm_rates = []
for p in range(10000):
    shuf = dati[:]
    random.shuffle(shuf)
    r, _, _ = calc_rate_dispersed(shuf)
    perm_rates.append(r)
    if (p+1) % 2000 == 0:
        print(f"    {p+1}/10000...", flush=True)

p_value = sum(1 for r in perm_rates if r >= rate_obs) / len(perm_rates)
mean_p = sum(perm_rates)/len(perm_rates)
std_p = (sum((r-mean_p)**2 for r in perm_rates)/len(perm_rates))**0.5
z = (rate_obs - mean_p)/std_p if std_p > 0 else 0

print(f"\n  Osservato:  {rate_obs*100:.3f}%", flush=True)
print(f"  Perm media: {mean_p*100:.3f}%", flush=True)
print(f"  Z-score:    {z:.3f}", flush=True)
print(f"  P-value:    {p_value:.4f}", flush=True)
print(f"  Sig 5%?     {'SI' if p_value < 0.05 else 'NO'}", flush=True)

# Split temporale
half = len(dati) // 2
r1, h1, t1 = calc_rate_dispersed(dati[:half])
r2, h2, t2 = calc_rate_dispersed(dati[half:])
print(f"\n  Split: prima {r1*100:.2f}% ({h1}/{t1}), seconda {r2*100:.2f}% ({h2}/{t2})", flush=True)
print(f"  Stabile? {'SI' if r1 > mean_p and r2 > mean_p else 'NO'}", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  STRATEGIA OPERATIVA VINCICASA", flush=True)
print("=" * 70, flush=True)

best_p2 = configs_v10[best_pool][0]
best_ev = configs_v10[best_pool][2]
best_costo = configs_v10[best_pool][3]
n_tickets = best_pool // 5

# Confronto con random
rand_p2_baseline = {5: 10.88, 10: 18.61, 15: 26.49, 20: 34.24, 25: 39.50}

print(f"""
  CONFIGURAZIONE OTTIMALE:
    Pool: top {best_pool} numeri dalle ultime 5 estrazioni
    Cinquine: {n_tickets} in dispersione (nessun numero ripetuto)
    Costo: EUR {best_costo}/giorno
    P(almeno 2/5): {best_p2:.1f}%
    EV: EUR {best_ev:.3f}
    
  PROTOCOLLO:
    1. Guarda le ultime 5 estrazioni VinciCasa
    2. Conta la frequenza di ogni numero (1-40)
    3. Prendi i top {best_pool} per frequenza
    4. Distribuiscili in {n_tickets} cinquine senza overlap
    5. Gioca le {n_tickets} cinquine (EUR {best_costo})
    6. Ripeti domani con le ultime 5 aggiornate
""", flush=True)

msg = f"VINCICASA STRATEGIA OTTIMALE\n\n"
msg += f"Pool: top {best_pool}, {n_tickets} cinquine\n"
msg += f"P(2/5): {best_p2:.1f}%\n"
msg += f"Permutation p={p_value:.4f}\n"
msg += f"Costo: EUR {best_costo}/giorno"
try:
    httpx.post(NTFY, content=msg.encode('utf-8'),
        headers={'Title': 'VinciCasa Strategia Ottimale', 'Priority': '5'}, timeout=10.0)
except: pass
print("Done.", flush=True)
