"""VinciCasa Deep Analysis — 5 test sul meccanismo reale del gioco."""
from __future__ import annotations
import sys; sys.path.insert(0, 'backend')
import math, random
from collections import Counter, defaultdict
from itertools import combinations
from sqlalchemy import select
from lotto_predictor.models.database import get_session
from vincicasa.models.database import VinciCasaEstrazione
import httpx

# Carica dal DB
session = get_session()
rows = session.execute(select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data)).scalars().all()
dati = [(r.data, sorted([r.n1, r.n2, r.n3, r.n4, r.n5])) for r in rows]
session.close()
print(f"Dataset: {len(dati)} estrazioni ({dati[0][0]} — {dati[-1][0]})", flush=True)

NTFY = 'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM'

# ================================================================
print("\n" + "=" * 70, flush=True)
print("  TEST V1 — Struttura cinquine: tipi, parita', range", flush=True)
print("=" * 70, flush=True)

def get_type(nums):
    decs = Counter((n-1)//10 for n in nums)
    return tuple(sorted(decs.values(), reverse=True))

def get_parity(nums):
    return sum(1 for n in nums if n % 2 == 0)

def get_range_cat(nums):
    r = max(nums) - min(nums)
    return 'compatto' if r < 15 else ('medio' if r <= 25 else 'largo')

# Distribuzione tipi
type_seq = [get_type(nums) for _, nums in dati]
type_dist = Counter(type_seq)
print(f"\n--- Distribuzione tipi (decade pattern) ---", flush=True)
print(f"{'TIPO':>15} {'OSS':>6} {'%':>7}", flush=True)
for t, c in type_dist.most_common():
    print(f"{str(t):>15} {c:>6} {c/len(dati)*100:>6.1f}%", flush=True)

# MI tra tipi consecutivi
def calc_mi(seq):
    n = len(seq) - 1
    joint = Counter(); mx = Counter(); my = Counter()
    for i in range(n):
        joint[(seq[i], seq[i+1])] += 1
        mx[seq[i]] += 1; my[seq[i+1]] += 1
    h_y = -sum((c/n)*math.log2(c/n) for c in my.values() if c > 0)
    h_y_x = 0
    for x in mx:
        nx = mx[x]
        for y in my:
            nxy = joint.get((x, y), 0)
            if nxy > 0: h_y_x -= (nxy/n) * math.log2(nxy/nx)
    return h_y - h_y_x

random.seed(42)
for prop_name, seq_fn in [("Tipo", get_type), ("Parita'", get_parity), ("Range", get_range_cat)]:
    seq = [seq_fn(nums) for _, nums in dati]
    mi_real = calc_mi(seq)
    mi_perms = []
    for _ in range(1000):
        shuf = seq[:]; random.shuffle(shuf)
        mi_perms.append(calc_mi(shuf))
    mean_p = sum(mi_perms)/len(mi_perms)
    p_val = sum(1 for m in mi_perms if m >= mi_real) / len(mi_perms)
    sig = "SIGNIFICATIVO" if p_val < 0.05 else "non sig."
    print(f"\n  MI {prop_name}: {mi_real:.6f} (perm: {mean_p:.6f}, p={p_val:.3f}) → {sig}", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V2 — Wheeling: 3 strategie di multi-giocata", flush=True)
print("=" * 70, flush=True)

N_SIM = 100000
random.seed(42)
PREMI = {0: 0, 1: 0, 2: 2.60, 3: 20, 4: 200, 5: 500000}

def sim_strategy(tickets, n_sim=N_SIM):
    """Simula n_sim estrazioni e calcola stats per un set di tickets."""
    results = Counter()  # (vincita_totale) -> count
    match_any = {k: 0 for k in range(6)}  # almeno 1 ticket con k match
    total_prizes = 0; total_wins = 0
    
    for _ in range(n_sim):
        draw = sorted(random.sample(range(1, 41), 5))
        draw_set = set(draw)
        round_prize = 0; best_match = 0
        for ticket in tickets:
            k = len(set(ticket) & draw_set)
            round_prize += PREMI[k]
            best_match = max(best_match, k)
        match_any[best_match] += 1
        total_prizes += round_prize
        if round_prize > 0: total_wins += 1
        results[round_prize] += 1
    
    return total_prizes / n_sim, match_any, results

# Strategia A: Dispersione (25 numeri, 5 cinquine senza sovrapposizione)
nums_a = list(range(1, 26))  # 1-25
tickets_a = [sorted(nums_a[i*5:(i+1)*5]) for i in range(5)]

# Strategia B: Concentrazione (10 numeri, 5 migliori cinquine)
pool_b = sorted(random.sample(range(1, 41), 10))
all_combos_b = list(combinations(pool_b, 5))
# Seleziona 5 che massimizzano copertura ambi
def pair_coverage(tickets):
    pairs = set()
    for t in tickets:
        for a, b in combinations(t, 2):
            pairs.add((a, b))
    return len(pairs)

best_set = None; best_cov = 0
for _ in range(5000):  # greedy random
    sample = random.sample(all_combos_b, min(5, len(all_combos_b)))
    cov = pair_coverage(sample)
    if cov > best_cov:
        best_cov = cov; best_set = [sorted(s) for s in sample]
tickets_b = best_set

# Strategia C: Wheeling classico (8 numeri, garanzia 3/5)
pool_c = sorted(random.sample(range(1, 41), 8))
# Genera tutte le cinquine da 8: C(8,5)=56
all_c = [sorted(c) for c in combinations(pool_c, 5)]
# Prendi le prime 5 (subset del wheeling completo)
tickets_c = all_c[:5]

# Simula
print(f"\n{'STRATEGIA':<20} {'COSTO':>6} {'EV':>8} {'P(2+)':>7} {'P(3+)':>7} {'P(4+)':>7} {'ROI':>8}", flush=True)
print("-" * 62, flush=True)

for name, tickets, cost in [
    ("A: Dispersione", tickets_a, 10),
    ("B: Concentrazione", tickets_b, 10),
    ("C: Wheeling 8", tickets_c, 10),
]:
    ev, match_any, results = sim_strategy(tickets)
    p2 = sum(v for k, v in match_any.items() if k >= 2) / N_SIM * 100
    p3 = sum(v for k, v in match_any.items() if k >= 3) / N_SIM * 100
    p4 = sum(v for k, v in match_any.items() if k >= 4) / N_SIM * 100
    roi = (ev - cost) / cost * 100
    print(f"{name:<20} {cost:>5}€ {ev:>7.2f}€ {p2:>6.1f}% {p3:>6.1f}% {p4:>6.1f}% {roi:>+7.1f}%", flush=True)
    
    # Distribuzione ritorni
    top_returns = sorted(results.items(), key=lambda x: -x[1])[:5]
    print(f"  Ritorni: {', '.join(f'€{r:.0f}({c/N_SIM*100:.1f}%)' for r,c in top_returns)}", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V3 — Cinquine ripetute e distanza di Hamming", flush=True)
print("=" * 70, flush=True)

# Cinquine uniche
all_draws = [tuple(nums) for _, nums in dati]
draw_counts = Counter(all_draws)
n_unique = len(draw_counts)
n_repeated = sum(1 for c in draw_counts.values() if c >= 2)
# Atteso sotto Poisson: lambda = N^2 / (2 * C(40,5))
lam = len(dati)**2 / (2 * math.comb(40, 5))
expected_rep = lam  # approssimazione

print(f"\n  Cinquine totali: {len(dati)}", flush=True)
print(f"  Cinquine uniche: {n_unique}", flush=True)
print(f"  Ripetute 2+ volte: {n_repeated} (atteso Poisson: ~{expected_rep:.1f})", flush=True)

if n_repeated > 0:
    for draw, count in draw_counts.most_common(5):
        if count >= 2:
            print(f"    {list(draw)}: {count} volte", flush=True)

# Distanza di Hamming consecutiva
print(f"\n--- Distanza di Hamming tra estrazioni consecutive ---", flush=True)
hamming_dists = []
for i in range(len(dati) - 1):
    s1 = set(dati[i][1]); s2 = set(dati[i+1][1])
    shared = len(s1 & s2)
    hamming = 10 - 2 * shared  # 0=identiche, 10=completamente diverse
    hamming_dists.append(shared)

# Distribuzione numeri condivisi
shared_dist = Counter(hamming_dists)
print(f"\n  {'CONDIVISI':>10} {'OSS':>6} {'OSS%':>7} {'ATTESO%':>8}", flush=True)
print("-" * 35, flush=True)

for k in range(6):
    obs = shared_dist.get(k, 0)
    obs_pct = obs / len(hamming_dists) * 100
    # Atteso: ipergeometrica H(40, 5, 5)
    from math import comb
    exp_pct = comb(5,k) * comb(35, 5-k) / comb(40, 5) * 100
    diff = obs_pct - exp_pct
    marker = " <<<" if abs(diff) > 1 else ""
    print(f"  {k:>10} {obs:>6} {obs_pct:>6.2f}% {exp_pct:>7.2f}% {diff:>+5.2f}%{marker}", flush=True)

avg_shared = sum(hamming_dists) / len(hamming_dists)
exp_shared = 5 * 5 / 40  # = 0.625
print(f"\n  Media condivisi: {avg_shared:.3f} (atteso: {exp_shared:.3f})", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V4 — Analisi temporale EV (semplificata)", flush=True)
print("=" * 70, flush=True)

# Non possiamo scrappare i dettagli dei vincitori, ma possiamo
# analizzare se ci sono periodi con piu' vincite alte
print("\n  Distribuzione vincite per anno (simulata con match reali):", flush=True)

per_anno = defaultdict(lambda: Counter())
for i in range(len(dati) - 1):
    data, nums = dati[i]
    next_nums = set(dati[i+1][1])
    anno = data.year
    # Se giocassimo una cinquina random
    rand_pick = sorted(random.sample(range(1, 41), 5))
    k = len(set(rand_pick) & next_nums)
    per_anno[anno][k] += 1

print(f"  {'ANNO':>6} {'ESTR':>5} {'2/5':>5} {'3/5':>5} {'4/5':>5} {'EV/gioc':>8}", flush=True)
print("-" * 40, flush=True)
for anno in sorted(per_anno):
    d = per_anno[anno]
    total = sum(d.values())
    ev = sum(d.get(k, 0) * PREMI[k] for k in range(6)) / total if total > 0 else 0
    print(f"  {anno:>6} {total:>5} {d.get(2,0):>5} {d.get(3,0):>5} {d.get(4,0):>5} {ev:>7.3f}€", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  TEST V5 — Anti-strategia: numeri impopolari", flush=True)
print("=" * 70, flush=True)

print("""
  Ipotesi: giocando numeri >31 ("brutti", non-compleanni),
  in caso di 5/5 il premio non e' condiviso con chi gioca 1-31.
  
  La P(vincere) non cambia, ma E(premio|vincita) potrebbe essere piu' alto.
""", flush=True)

# Simula: 1000 giocatori, il 30% gioca solo 1-31, il 70% uniforme
N_PLAYERS = 1000
N_SIM_V5 = 50000
random.seed(42)

stats_high = {'wins': 0, 'shared': []}  # gioca >31
stats_low = {'wins': 0, 'shared': []}   # gioca <20

for _ in range(N_SIM_V5):
    draw = set(random.sample(range(1, 41), 5))
    
    # Conta vincitori tra 1000 giocatori
    winners = 0
    for _ in range(N_PLAYERS):
        if random.random() < 0.3:
            # Gioca 1-31
            pick = set(random.sample(range(1, 32), 5))
        else:
            pick = set(random.sample(range(1, 41), 5))
        if pick == draw:
            winners += 1
    
    # Il nostro giocatore "alto" (32-40 + qualcuno)
    high_pick = set(random.sample(range(28, 41), 5))
    if high_pick == draw:
        stats_high['wins'] += 1
        stats_high['shared'].append(winners)
    
    low_pick = set(random.sample(range(1, 20), 5))
    if low_pick == draw:
        stats_low['wins'] += 1
        stats_low['shared'].append(winners)

print(f"  Simulazione: {N_SIM_V5} estrazioni, {N_PLAYERS} giocatori", flush=True)
print(f"  30% gioca 1-31, 70% uniforme", flush=True)
print(f"\n  Giocatore 'alto' (28-40): {stats_high['wins']} vincite 5/5", flush=True)
if stats_high['shared']:
    print(f"    Co-vincitori medi: {sum(stats_high['shared'])/len(stats_high['shared']):.1f}", flush=True)
print(f"  Giocatore 'basso' (1-19): {stats_low['wins']} vincite 5/5", flush=True)
if stats_low['shared']:
    print(f"    Co-vincitori medi: {sum(stats_low['shared'])/len(stats_low['shared']):.1f}", flush=True)

print(f"\n  Nota: con 50K simulazioni e P(5/5)~1/658K,", flush=True)
print(f"  le vincite 5/5 sono estremamente rare (~0.076 attese).", flush=True)
print(f"  Serve un campione di milioni per risultati significativi.", flush=True)
print(f"  Ma il principio e' valido: numeri alti = meno condivisione.", flush=True)

# ================================================================
print(f"\n{'=' * 70}", flush=True)
print("  RIEPILOGO", flush=True)
print("=" * 70, flush=True)

msg = "VinciCasa Deep Analysis\n\n"
msg += "V1 Tipi/Parita/Range: MI vs permutazioni\n"
msg += "V2 Wheeling: 3 strategie confrontate\n"
msg += "V3 Hamming: distanza tra estrazioni consecutive\n"
msg += "V4 EV temporale\nV5 Anti-strategia numeri alti\n"
msg += "Dettagli nel terminale"
try:
    httpx.post(NTFY, content=msg.encode('utf-8'),
        headers={'Title': 'VinciCasa Deep Analysis', 'Priority': '5'}, timeout=10.0)
except: pass

print("\nDone.", flush=True)
