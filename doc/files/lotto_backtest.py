#!/usr/bin/env python3
"""
LOTTO ITALIANO - BACKTESTING ENGINE
====================================
Analisi ciclometrica e statistica per ambi secchi.
- Pattern analysis (decine, distanze ciclometriche)
- Monte Carlo baseline (10M simulazioni)
- Backtesting metodi ciclometrici vs random
- Money management / progressione analysis
"""

import csv
import random
import json
from collections import Counter, defaultdict
from itertools import combinations
from datetime import datetime

# ─────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────

WHEELS_ORDER = ['BARI','CAGLIARI','FIRENZE','GENOVA','MILANO',
                'NAPOLI','PALERMO','ROMA','TORINO','VENEZIA','NAZIONALE']

def load_data(path='lotto_archive.csv'):
    """Load and structure extraction data."""
    draws = defaultdict(dict)  # date -> wheel -> [n1..n5]
    with open(path) as f:
        for row in csv.DictReader(f):
            nums = [int(row[f'n{i}']) for i in range(1,6)]
            draws[row['date']][row['wheel']] = nums
    # Sort by date
    sorted_dates = sorted(draws.keys(), key=lambda d: datetime.strptime(d, '%d/%m/%Y'))
    return [(d, draws[d]) for d in sorted_dates]

# ─────────────────────────────────────────────
# 2. CYCLOMETRIC UTILITIES
# ─────────────────────────────────────────────

def cyclo_distance(a, b):
    """Distanza ciclometrica (0-45)."""
    d = abs(a - b)
    return d if d <= 45 else 90 - d

def diametrale(n):
    """Diametrale: n+45 mod 90 (1-90)."""
    r = (n + 45) % 90
    return r if r != 0 else 90

def fuori90(n):
    """Riduzione fuori 90."""
    while n > 90:
        n -= 90
    return n if n > 0 else n + 90

def get_decade(n):
    """Decade di appartenenza (0-8 per 1-10, 11-20, ..., 81-90)."""
    return (n - 1) // 10

def get_cadenza(n):
    """Cadenza (ultima cifra, 0=decine di 10,20,..,90)."""
    return n % 10

def get_figura(n):
    """Figura (somma iterata delle cifre fino a 1 cifra)."""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n

# ─────────────────────────────────────────────
# 3. PATTERN ANALYSIS - DECINE
# ─────────────────────────────────────────────

def analyze_decades(data):
    """Analizza frequenza di ambi intra-decina nelle estrazioni reali."""
    print("\n" + "="*60)
    print("ANALISI DECINE - Ambi nella stessa decina")
    print("="*60)
    
    total_draws = 0
    draws_with_intradec = 0
    intradec_ambi_count = 0
    decade_pair_freq = Counter()
    
    for date, wheels in data:
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            total_draws += 1
            decades = [get_decade(n) for n in nums]
            dec_counter = Counter(decades)
            
            has_pair = False
            for dec, count in dec_counter.items():
                if count >= 2:
                    has_pair = True
                    pairs = count * (count - 1) // 2
                    intradec_ambi_count += pairs
                    decade_pair_freq[dec] += pairs
            
            if has_pair:
                draws_with_intradec += 1
    
    pct = draws_with_intradec / total_draws * 100
    print(f"\nEstrazioni totali analizzate (esclusa Nazionale): {total_draws}")
    print(f"Estrazioni con almeno un ambo intra-decina: {draws_with_intradec} ({pct:.1f}%)")
    print(f"Totale ambi intra-decina trovati: {intradec_ambi_count}")
    
    # Monte Carlo comparison
    mc_hits = 0
    mc_total = 100000
    for _ in range(mc_total):
        nums = random.sample(range(1, 91), 5)
        decades = [get_decade(n) for n in nums]
        if len(decades) != len(set(decades)):
            mc_hits += 1
    mc_pct = mc_hits / mc_total * 100
    
    print(f"\nBaseline Monte Carlo (100K sim): {mc_pct:.1f}%")
    print(f"Dato reale: {pct:.1f}%")
    print(f"Differenza: {pct - mc_pct:+.1f} punti percentuali")
    
    print(f"\nDistribuzione per decina:")
    for dec in range(9):
        freq = decade_pair_freq.get(dec, 0)
        rng = f"{dec*10+1:2d}-{dec*10+10:2d}"
        bar = "█" * (freq // 5)
        print(f"  Decina {rng}: {freq:4d} ambi  {bar}")
    
    return pct, mc_pct

# ─────────────────────────────────────────────
# 4. CYCLOMETRIC DISTANCE ANALYSIS
# ─────────────────────────────────────────────

def analyze_distances(data):
    """Analizza distribuzione delle distanze ciclometriche tra numeri estratti."""
    print("\n" + "="*60)
    print("ANALISI DISTANZE CICLOMETRICHE")
    print("="*60)
    
    dist_freq = Counter()
    total_pairs = 0
    
    for date, wheels in data:
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            for a, b in combinations(nums, 2):
                d = cyclo_distance(a, b)
                dist_freq[d] += 1
                total_pairs += 1
    
    # Theoretical distribution for uniform random
    # P(distance=d) for d in 1..44 is 2/90, for d=45 is 1/90
    print(f"\nTotale coppie analizzate: {total_pairs}")
    print(f"\nDistanze più frequenti (top 10):")
    for dist, count in dist_freq.most_common(10):
        expected = total_pairs * (2/89 if dist < 45 else 1/89)
        ratio = count / expected
        print(f"  Distanza {dist:2d}: {count:5d} (atteso: {expected:.0f}, ratio: {ratio:.3f})")
    
    print(f"\nDistanze meno frequenti (bottom 5):")
    for dist, count in dist_freq.most_common()[-5:]:
        expected = total_pairs * (2/89 if dist < 45 else 1/89)
        ratio = count / expected
        print(f"  Distanza {dist:2d}: {count:5d} (atteso: {expected:.0f}, ratio: {ratio:.3f})")
    
    # Check distance 45 (diametrali) specifically
    d45 = dist_freq.get(45, 0)
    d45_exp = total_pairs / 89
    print(f"\nDistanza 45 (diametrali): {d45} (atteso: {d45_exp:.0f}, ratio: {d45/d45_exp:.3f})")
    
    return dist_freq

# ─────────────────────────────────────────────
# 5. INTER-WHEEL CORRELATION
# ─────────────────────────────────────────────

def analyze_interwheel(data):
    """Analizza correlazioni tra ruote consecutive (base per ciclometria)."""
    print("\n" + "="*60)
    print("ANALISI INTER-RUOTA (correlazioni posizionali)")
    print("="*60)
    
    # Check if same-position numbers on consecutive wheels have preferred distances
    consecutive_pairs = [
        ('BARI','CAGLIARI'), ('CAGLIARI','FIRENZE'), ('FIRENZE','GENOVA'),
        ('GENOVA','MILANO'), ('MILANO','NAPOLI'), ('NAPOLI','PALERMO'),
        ('PALERMO','ROMA'), ('ROMA','TORINO'), ('TORINO','VENEZIA')
    ]
    
    dist_by_pair = defaultdict(Counter)
    
    for date, wheels in data:
        for w1, w2 in consecutive_pairs:
            if w1 not in wheels or w2 not in wheels:
                continue
            for pos in range(5):
                d = cyclo_distance(wheels[w1][pos], wheels[w2][pos])
                dist_by_pair[(w1,w2)][d] += 1
    
    # Focus on distance 9 (key for Ponfig method)
    print(f"\nDistanza 9 tra ruote consecutive (stessa posizione):")
    print(f"(Chiave del metodo Ponfig di ciclometria)")
    for w1, w2 in consecutive_pairs:
        d9_count = dist_by_pair[(w1,w2)].get(9, 0)
        total = sum(dist_by_pair[(w1,w2)].values())
        expected = total / 45  # uniform: each distance ~equally likely
        ratio = d9_count / expected if expected > 0 else 0
        print(f"  {w1:10s}-{w2:10s}: {d9_count:3d}/{total:4d} (atteso: {expected:.1f}, ratio: {ratio:.2f})")
    
    return dist_by_pair

# ─────────────────────────────────────────────
# 6. CYCLOMETRIC METHOD BACKTEST
# ─────────────────────────────────────────────

def method_ponfig(data, max_colpi=9):
    """
    Backtest del metodo Ponfig (distanza ciclometrica 9).
    Cerca coppie con distanza 9 sulla stessa posizione tra ruote consecutive,
    genera ambata + ambi secchi, verifica nei colpi successivi.
    """
    print("\n" + "="*60)
    print(f"BACKTEST METODO PONFIG (distanza 9) - max {max_colpi} colpi")
    print("="*60)
    
    consecutive_pairs = [
        ('BARI','CAGLIARI'), ('CAGLIARI','FIRENZE'), ('FIRENZE','GENOVA'),
        ('GENOVA','MILANO'), ('MILANO','NAPOLI'), ('NAPOLI','PALERMO'),
        ('PALERMO','ROMA'), ('ROMA','TORINO'), ('TORINO','VENEZIA')
    ]
    
    signals = 0
    ambata_hits = 0
    ambo_hits = 0
    hit_colpi = []
    
    for i, (date, wheels) in enumerate(data):
        for w1, w2 in consecutive_pairs:
            if w1 not in wheels or w2 not in wheels:
                continue
            for pos in range(5):
                n1 = wheels[w1][pos]
                n2 = wheels[w2][pos]
                d = cyclo_distance(n1, n2)
                if d != 9:
                    continue
                
                # Generate prediction
                ambata = fuori90(n1 + n2)
                abbinamenti = []
                v = n1
                for _ in range(3):
                    v = fuori90(v * 2)
                    abbinamenti.append(v)
                v = n2
                for _ in range(3):
                    v = fuori90(v * 2)
                    abbinamenti.append(v)
                
                # Remove duplicates, replace with diametrali
                seen = set()
                clean_abb = []
                for a in abbinamenti:
                    if a in seen:
                        a = diametrale(a)
                    if a not in seen:
                        seen.add(a)
                        clean_abb.append(a)
                
                ambi_secchi = [(ambata, a) for a in clean_abb]
                signals += 1
                
                # Check in next max_colpi draws
                found_ambata = False
                found_ambo = False
                for j in range(i+1, min(i+1+max_colpi, len(data))):
                    future_date, future_wheels = data[j]
                    for target_wheel in [w1, w2]:
                        if target_wheel not in future_wheels:
                            continue
                        future_nums = set(future_wheels[target_wheel])
                        
                        if ambata in future_nums and not found_ambata:
                            found_ambata = True
                            ambata_hits += 1
                        
                        for am_a, am_b in ambi_secchi:
                            if am_a in future_nums and am_b in future_nums and not found_ambo:
                                found_ambo = True
                                ambo_hits += 1
                                hit_colpi.append(j - i)
                    
                    if found_ambo:
                        break
    
    # Baseline: random ambo probability on 2 wheels in max_colpi draws
    p_ambo_single = 1/400.5
    p_ambo_cycle = 1 - (1 - p_ambo_single * 2) ** max_colpi  # 2 wheels
    p_ambo_6ambi = 1 - (1 - p_ambo_cycle) ** 6  # 6 ambi
    
    if signals > 0:
        print(f"\nSegnali trovati: {signals}")
        print(f"Ambate centrate: {ambata_hits} ({ambata_hits/signals*100:.1f}%)")
        print(f"Ambi secchi centrati: {ambo_hits} ({ambo_hits/signals*100:.1f}%)")
        print(f"\nBaseline random (6 ambi, 2 ruote, {max_colpi} colpi): {p_ambo_6ambi*100:.1f}%")
        print(f"Hit rate metodo: {ambo_hits/signals*100:.1f}%")
        print(f"Ratio vs baseline: {(ambo_hits/signals) / p_ambo_6ambi:.2f}x")
        
        if hit_colpi:
            avg_colpo = sum(hit_colpi) / len(hit_colpi)
            print(f"\nColpo medio di uscita: {avg_colpo:.1f}")
            colpo_dist = Counter(hit_colpi)
            for c in sorted(colpo_dist.keys()):
                bar = "█" * colpo_dist[c]
                print(f"  Colpo {c}: {colpo_dist[c]} {bar}")
    else:
        print("Nessun segnale trovato nel dataset.")
    
    return signals, ambo_hits

# ─────────────────────────────────────────────
# 7. DECADE-BASED AMBO METHOD
# ─────────────────────────────────────────────

def method_intradecade(data, max_colpi=9):
    """
    Metodo basato sulle decine: quando in un'estrazione escono 2+ numeri
    della stessa decina, gioca ambi intra-decina nella stessa ruota.
    """
    print("\n" + "="*60)
    print(f"BACKTEST METODO INTRA-DECINA - max {max_colpi} colpi")
    print("="*60)
    
    signals = 0
    hits = 0
    hit_colpi = []
    
    for i, (date, wheels) in enumerate(data):
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            
            decades = defaultdict(list)
            for n in nums:
                decades[get_decade(n)].append(n)
            
            for dec, dec_nums in decades.items():
                if len(dec_nums) < 2:
                    continue
                
                # Signal: 2+ numbers in same decade
                # Predict: other numbers from same decade will appear
                remaining_in_dec = [n for n in range(dec*10+1, dec*10+11) if n not in dec_nums and 1 <= n <= 90]
                
                # Generate ambi: pair each remaining with each extracted
                ambi = []
                for existing in dec_nums:
                    for target in remaining_in_dec[:3]:  # top 3 targets
                        ambi.append((existing, target))
                
                if not ambi:
                    continue
                
                signals += 1
                found = False
                
                for j in range(i+1, min(i+1+max_colpi, len(data))):
                    future_date, future_wheels = data[j]
                    if wheel not in future_wheels:
                        continue
                    future_nums = set(future_wheels[wheel])
                    
                    for am_a, am_b in ambi:
                        if am_a in future_nums and am_b in future_nums:
                            found = True
                            hits += 1
                            hit_colpi.append(j - i)
                            break
                    if found:
                        break
    
    n_ambi_avg = 6  # approximate
    p_baseline = 1 - (1 - 1/400.5) ** (max_colpi * n_ambi_avg)
    
    if signals > 0:
        print(f"\nSegnali trovati: {signals}")
        print(f"Ambi centrati: {hits} ({hits/signals*100:.1f}%)")
        print(f"Baseline random ({n_ambi_avg} ambi, 1 ruota, {max_colpi} colpi): {p_baseline*100:.1f}%")
        print(f"Hit rate metodo: {hits/signals*100:.1f}%")
        print(f"Ratio vs baseline: {(hits/signals) / p_baseline:.2f}x")
        
        if hit_colpi:
            avg_colpo = sum(hit_colpi) / len(hit_colpi)
            print(f"\nColpo medio: {avg_colpo:.1f}")
    
    return signals, hits

# ─────────────────────────────────────────────
# 8. DIAMETRALE PAIR ANALYSIS
# ─────────────────────────────────────────────

def method_diametrali(data, max_colpi=9):
    """
    Analisi coppie diametrali (somma 91).
    Se esce un numero, gioca il suo diametrale.
    """
    print("\n" + "="*60)
    print(f"BACKTEST METODO DIAMETRALI (somma 91) - max {max_colpi} colpi")
    print("="*60)
    
    signals = 0
    hits = 0
    
    for i, (date, wheels) in enumerate(data):
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            
            # For each extracted number, predict its diametrale
            for n in nums:
                diam = diametrale(n)
                if diam == n:
                    continue
                
                signals += 1
                found = False
                
                for j in range(i+1, min(i+1+max_colpi, len(data))):
                    future_date, future_wheels = data[j]
                    if wheel not in future_wheels:
                        continue
                    if diam in future_wheels[wheel]:
                        found = True
                        hits += 1
                        break
    
    p_baseline = 1 - (85/90) ** max_colpi  # P(specific number in max_colpi draws)
    
    if signals > 0:
        print(f"\nSegnali (numeri base): {signals}")
        print(f"Diametrali usciti entro {max_colpi} colpi: {hits} ({hits/signals*100:.1f}%)")
        print(f"Baseline random (1 numero, 1 ruota, {max_colpi} colpi): {p_baseline*100:.1f}%")
        print(f"Ratio vs baseline: {(hits/signals) / p_baseline:.2f}x")
    
    return signals, hits

# ─────────────────────────────────────────────
# 9. VINCOLO DIFFERENZIALE 90
# ─────────────────────────────────────────────

def method_vincolo90(data, max_colpi=9):
    """
    Metodo Vincolo Differenziale 90 di Fabarri.
    Cerca quadrature ciclometriche con vincolo = 90.
    """
    print("\n" + "="*60)
    print(f"BACKTEST VINCOLO DIFFERENZIALE 90 - max {max_colpi} colpi")
    print("="*60)
    
    wheel_pairs = [
        ('BARI','MILANO'), ('BARI','CAGLIARI'), ('ROMA','TORINO'),
        ('NAPOLI','PALERMO'), ('FIRENZE','GENOVA'), ('MILANO','NAPOLI')
    ]
    
    signals = 0
    hits = 0
    hit_colpi = []
    
    for i, (date, wheels) in enumerate(data):
        for w1, w2 in wheel_pairs:
            if w1 not in wheels or w2 not in wheels:
                continue
            
            nums1 = wheels[w1]
            nums2 = wheels[w2]
            
            # Find pairs across wheels where sum of cyclo distances = 90
            for pos1 in range(5):
                for pos2 in range(5):
                    a, b = nums1[pos1], nums2[pos2]
                    d_ab = cyclo_distance(a, b)
                    
                    for pos3 in range(5):
                        for pos4 in range(5):
                            if pos3 == pos1 and pos4 == pos2:
                                continue
                            c, d_val = nums1[pos3], nums2[pos4]
                            d_cd = cyclo_distance(c, d_val)
                            
                            if d_ab + d_cd == 45:  # half-circle condition
                                # Generate prediction
                                k1 = fuori90(a + b)
                                k2 = diametrale(k1)
                                ambi = [(k1, a), (k1, b), (k1, c), (k1, d_val),
                                        (k2, a), (k2, b), (k2, c), (k2, d_val)]
                                
                                signals += 1
                                found = False
                                
                                for j in range(i+1, min(i+1+max_colpi, len(data))):
                                    fd, fw = data[j]
                                    for tw in [w1, w2]:
                                        if tw not in fw:
                                            continue
                                        fn = set(fw[tw])
                                        for am_a, am_b in ambi:
                                            if am_a in fn and am_b in fn:
                                                found = True
                                                hits += 1
                                                hit_colpi.append(j - i)
                                                break
                                        if found:
                                            break
                                    if found:
                                        break
                                
                                if signals >= 500:  # limit for performance
                                    break
                        if signals >= 500:
                            break
                    if signals >= 500:
                        break
                if signals >= 500:
                    break
            if signals >= 500:
                break
        if signals >= 500:
            break
    
    n_ambi = 8
    p_baseline = 1 - (1 - 2/400.5) ** (max_colpi * n_ambi)
    
    if signals > 0:
        print(f"\nSegnali trovati: {signals}")
        print(f"Ambi centrati: {hits} ({hits/signals*100:.1f}%)")
        print(f"Baseline random ({n_ambi} ambi, 2 ruote, {max_colpi} colpi): {p_baseline*100:.1f}%")
        print(f"Hit rate metodo: {hits/signals*100:.1f}%")
        if p_baseline > 0:
            print(f"Ratio vs baseline: {(hits/signals) / p_baseline:.2f}x")
        if hit_colpi:
            print(f"Colpo medio: {sum(hit_colpi)/len(hit_colpi):.1f}")
    
    return signals, hits

# ─────────────────────────────────────────────
# 10. MONEY MANAGEMENT SIMULATION
# ─────────────────────────────────────────────

def simulate_progression(hit_rate, n_ambi=3, n_colpi=10, n_cycles=1000, payout=250):
    """
    Simula una progressione flat per ambi secchi.
    """
    print("\n" + "="*60)
    print(f"SIMULAZIONE MONEY MANAGEMENT")
    print(f"Hit rate: {hit_rate*100:.1f}%, Ambi: {n_ambi}, Colpi: {n_colpi}")
    print("="*60)
    
    posta = 1  # €1 per ambo per colpo
    costo_ciclo = posta * n_ambi * n_colpi
    
    bankroll = 500  # starting bankroll
    max_bankroll = bankroll
    min_bankroll = bankroll
    wins = 0
    total_cycles = n_cycles
    
    bankroll_history = [bankroll]
    
    for cycle in range(total_cycles):
        cycle_won = False
        for colpo in range(n_colpi):
            bankroll -= posta * n_ambi  # pay for this draw
            
            for _ in range(n_ambi):
                if random.random() < hit_rate:
                    bankroll += posta * payout
                    cycle_won = True
            
            if cycle_won:
                break
        
        if cycle_won:
            wins += 1
        
        max_bankroll = max(max_bankroll, bankroll)
        min_bankroll = min(min_bankroll, bankroll)
        bankroll_history.append(bankroll)
    
    print(f"\nBankroll iniziale: €{500}")
    print(f"Bankroll finale: €{bankroll:.0f}")
    print(f"Max drawdown: €{500 - min_bankroll:.0f}")
    print(f"Picco massimo: €{max_bankroll:.0f}")
    print(f"Cicli vincenti: {wins}/{total_cycles} ({wins/total_cycles*100:.1f}%)")
    print(f"P&L: €{bankroll - 500:+.0f}")
    print(f"ROI: {(bankroll - 500) / (costo_ciclo * total_cycles) * 100:+.1f}%")
    
    return bankroll_history

# ─────────────────────────────────────────────
# 11. COMPREHENSIVE PAIR FREQUENCY ANALYSIS
# ─────────────────────────────────────────────

def analyze_pair_frequencies(data):
    """Trova gli ambi più frequenti per ruota."""
    print("\n" + "="*60)
    print("AMBI PIÙ FREQUENTI PER RUOTA (top 5)")
    print("="*60)
    
    pair_freq = defaultdict(Counter)
    
    for date, wheels in data:
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            for a, b in combinations(sorted(nums), 2):
                pair_freq[wheel][(a,b)] += 1
    
    for wheel in WHEELS_ORDER:
        if wheel == 'NAZIONALE':
            continue
        print(f"\n  {wheel}:")
        for (a, b), count in pair_freq[wheel].most_common(5):
            d = cyclo_distance(a, b)
            dec_a, dec_b = get_decade(a), get_decade(b)
            same_dec = "★" if dec_a == dec_b else " "
            print(f"    {a:2d}-{b:2d}  freq={count}  dist={d:2d}  {same_dec}")

# ─────────────────────────────────────────────
# 12. RITARDI AMBI (delay analysis)
# ─────────────────────────────────────────────

def analyze_ritardi(data, sample_pairs=20):
    """Analisi ritardi degli ambi: distribuzione e confronto con atteso."""
    print("\n" + "="*60)
    print("ANALISI RITARDI AMBI")
    print("="*60)
    
    # Track delays for a random sample of pairs on all wheels
    random.seed(42)
    sample = [(random.randint(1,90), random.randint(1,90)) for _ in range(sample_pairs*2)]
    sample = [(min(a,b), max(a,b)) for a,b in sample if a != b][:sample_pairs]
    
    delays = defaultdict(list)
    last_seen = {}
    
    for draw_idx, (date, wheels) in enumerate(data):
        for wheel, nums in wheels.items():
            if wheel == 'NAZIONALE':
                continue
            nums_set = set(nums)
            for pair in sample:
                key = (wheel, pair)
                if pair[0] in nums_set and pair[1] in nums_set:
                    if key in last_seen:
                        delay = draw_idx - last_seen[key]
                        delays[pair].append(delay)
                    last_seen[key] = draw_idx
    
    all_delays = []
    for pair, d_list in delays.items():
        all_delays.extend(d_list)
    
    if all_delays:
        avg_delay = sum(all_delays) / len(all_delays)
        max_delay = max(all_delays)
        theoretical = 400.5 / 10  # expected delay per wheel ≈ 40 draws
        print(f"\nCampione di {sample_pairs} ambi casuali:")
        print(f"Ritardo medio osservato: {avg_delay:.1f} estrazioni")
        print(f"Ritardo teorico (1 ruota): ~{theoretical:.0f} estrazioni")  
        print(f"Ritardo massimo osservato: {max_delay}")
        print(f"Occorrenze totali: {len(all_delays)}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  LOTTO ITALIANO - BACKTESTING ENGINE v1.0           ║")
    print("║  Analisi Ciclometrica & Statistica per Ambi Secchi  ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    data = load_data()
    print(f"\nDataset: {len(data)} estrazioni ({data[0][0]} → {data[-1][0]})")
    
    results = {}
    
    # 1. Decade analysis
    real_pct, mc_pct = analyze_decades(data)
    results['decade_real'] = real_pct
    results['decade_mc'] = mc_pct
    
    # 2. Distance analysis
    dist_freq = analyze_distances(data)
    
    # 3. Inter-wheel correlation
    analyze_interwheel(data)
    
    # 4. Pair frequencies
    analyze_pair_frequencies(data)
    
    # 5. Delay analysis
    analyze_ritardi(data)
    
    # 6. Method backtests
    print("\n\n" + "▓"*60)
    print("  BACKTESTING DEI METODI PREVISIONALI")
    print("▓"*60)
    
    s1, h1 = method_ponfig(data, max_colpi=9)
    results['ponfig'] = (s1, h1)
    
    s2, h2 = method_intradecade(data, max_colpi=9)
    results['intradecade'] = (s2, h2)
    
    s3, h3 = method_diametrali(data, max_colpi=9)
    results['diametrali'] = (s3, h3)
    
    s4, h4 = method_vincolo90(data, max_colpi=9)
    results['vincolo90'] = (s4, h4)
    
    # 7. Money management
    print("\n\n" + "▓"*60)
    print("  SIMULAZIONI MONEY MANAGEMENT")
    print("▓"*60)
    
    # Baseline (random)
    print("\n--- Scenario A: Baseline (probabilità casuale) ---")
    simulate_progression(1/400.5, n_ambi=3, n_colpi=10, n_cycles=500)
    
    # If method gives 2x advantage
    print("\n--- Scenario B: Metodo con 2x vantaggio ---")
    simulate_progression(2/400.5, n_ambi=3, n_colpi=10, n_cycles=500)
    
    # If method gives 3x advantage
    print("\n--- Scenario C: Metodo con 3x vantaggio ---")
    simulate_progression(3/400.5, n_ambi=3, n_colpi=10, n_cycles=500)
    
    # SUMMARY
    print("\n\n" + "="*60)
    print("RIEPILOGO FINALE")
    print("="*60)
    
    print(f"""
┌─────────────────────────────────────────────────────┐
│ Ambi intra-decina: {results['decade_real']:.1f}% reale vs {results['decade_mc']:.1f}% atteso │
├─────────────────────────────────────────────────────┤
│ METODO              SEGNALI  HITS   HIT%            │""")
    
    for name, key in [('Ponfig (dist.9)','ponfig'), ('Intra-decina','intradecade'),
                       ('Diametrali','diametrali'), ('Vincolo 90','vincolo90')]:
        s, h = results[key]
        pct = h/s*100 if s > 0 else 0
        print(f"│ {name:20s} {s:6d}  {h:5d}  {pct:5.1f}%            │")
    
    print(f"""├─────────────────────────────────────────────────────┤
│ NOTA: Il dataset contiene {len(data):4d} estrazioni.           │
│ Per risultati più robusti servono 1500+ estrazioni. │
│ Ratio > 1.5x vs baseline = segnale interessante.   │
│ Ratio > 2.0x = statisticamente significativo.       │
└─────────────────────────────────────────────────────┘
""")
    
    # Save results as JSON
    with open('backtest_results.json', 'w') as f:
        json.dump({
            'dataset_size': len(data),
            'date_range': f"{data[0][0]} - {data[-1][0]}",
            'decade_analysis': {'real_pct': real_pct, 'mc_pct': mc_pct},
            'methods': {k: {'signals': v[0], 'hits': v[1], 
                           'hit_rate': v[1]/v[0] if v[0]>0 else 0}
                       for k, v in results.items() if isinstance(v, tuple)}
        }, f, indent=2)

if __name__ == '__main__':
    random.seed(42)
    main()
