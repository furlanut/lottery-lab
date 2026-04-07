#!/usr/bin/env python3
"""Autocorrelation analysis of lottery signal strength periodicities.

Analyzes freq_rit+fib signal (N=75) for natural cycles using:
- Rolling hit rate autocorrelation
- Raw pair appearance autocorrelation
- Simple spectral analysis (DFT-based)
"""
import sys
import math
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt
from lotto_predictor.analyzer.cyclometry import fuori90, RUOTE

# ── Parameters ──────────────────────────────────────────────────────
N_WINDOW = 75          # lookback window for freq_rit+fib
HIT_HORIZON = 9        # draws to check for hit
LAST_DRAWS = 3000      # total draws to load
ANALYSIS_DRAWS = 2000  # draws to analyze (within the 3000)
SMOOTHING_KS = [20, 50, 100]
MAX_LAG = 300
TOP_PAIRS_FOR_RAW = 10
SPECTRAL_FREQS = 500   # number of frequencies to test

# Fibonacci numbers up to 90 for filtering
FIB_SET = set()
a, b = 1, 1
while a <= 90:
    FIB_SET.add(a)
    a, b = b, a + b

print(f"Fibonacci set (1-90): {sorted(FIB_SET)}")
print(f"Parameters: N={N_WINDOW}, horizon={HIT_HORIZON}, analysis={ANALYSIS_DRAWS}")

# ── Load data ───────────────────────────────────────────────────────
t0 = time.time()
archivio_dir = Path(__file__).resolve().parent.parent / "archivio_dati" / "Archivio_Lotto" / "TXT"
files = scan_archivio_txt(archivio_dir)

# Filter 1946+
files = [f for f in files if int(f.stem.split("-")[-1]) >= 1946]
print(f"Loading {len(files)} files (1946+)...")

all_records = []
for f in files:
    all_records.extend(parse_file_txt(f))

# Group by (concorso, data) to get unique draws
draws_map = defaultdict(dict)
for rec in all_records:
    key = (rec["concorso"], rec["data"])
    draws_map[key][rec["ruota"]] = rec["numeri"]

# Sort by date, then concorso
sorted_keys = sorted(draws_map.keys(), key=lambda k: (k[1], k[0]))
draws = [(str(k[1]), draws_map[k]) for k in sorted_keys]

print(f"Total unique draws loaded: {len(draws)}")
draws = draws[-LAST_DRAWS:]
print(f"Using last {len(draws)} draws (from {draws[0][0]} to {draws[-1][0]})")
t_load = time.time() - t0
print(f"Load time: {t_load:.1f}s")

# ── Helper: freq_rit+fib signal generator ───────────────────────────
def compute_freq_rit_fib_signals(draws, idx, window, ruota):
    """Generate pairs matching freq_rit+fib criteria for a given extraction.
    
    Logic:
    - Look at last `window` draws on `ruota`
    - Count frequency of each number
    - Find numbers with high frequency (top quartile)
    - Find numbers with high delay (not seen recently)  
    - Intersect with Fibonacci numbers
    - Generate pairs from the intersection
    
    Simplified version: pairs where both numbers are frequent AND
    at least one has Fibonacci distance from the other.
    """
    if idx < window:
        return []
    
    # Count frequency in window
    freq = defaultdict(int)
    last_seen = {}
    
    for i in range(idx - window, idx):
        _, ruote_data = draws[i]
        if ruota in ruote_data:
            for n in ruote_data[ruota]:
                freq[n] = freq.get(n, 0) + 1
                last_seen[n] = i
    
    # Compute delay for each number
    delays = {}
    for n in range(1, 91):
        if n in last_seen:
            delays[n] = idx - last_seen[n]
        else:
            delays[n] = window  # max delay
    
    # Top frequency numbers (above median frequency)
    if not freq:
        return []
    freq_values = sorted(freq.values())
    median_freq = freq_values[len(freq_values) // 2]
    high_freq_nums = {n for n, f in freq.items() if f >= median_freq}
    
    # High delay numbers (above median delay)
    delay_values = sorted(delays.values())
    median_delay = delay_values[len(delay_values) // 2]
    high_delay_nums = {n for n, d in delays.items() if d >= median_delay}
    
    # Generate pairs: one from high_freq, one from high_delay,
    # with Fibonacci cyclo-distance
    signals = []
    freq_list = sorted(high_freq_nums)
    delay_list = sorted(high_delay_nums)
    
    for a in freq_list:
        for b in delay_list:
            if a >= b:
                continue
            # Check if distance is Fibonacci
            dist = abs(a - b)
            if dist > 45:
                dist = 90 - dist
            if dist in FIB_SET:
                signals.append((a, b))
    
    return signals


def check_hit(draws, idx, horizon, ruota, pair):
    """Check if pair (a,b) appears on ruota in draws[idx+1 : idx+1+horizon]."""
    a, b = pair
    for i in range(idx + 1, min(idx + 1 + horizon, len(draws))):
        _, ruote_data = draws[i]
        if ruota in ruote_data:
            nums = set(ruote_data[ruota])
            if a in nums and b in nums:
                return True
    return False


# ── PART 1: Hit rate time series ────────────────────────────────────
print("\n" + "="*70)
print("PART 1: Computing hit rate time series (freq_rit+fib, N=75)")
print("="*70)

t1 = time.time()
start_idx = len(draws) - ANALYSIS_DRAWS
# We need room for hit_horizon after the last index
end_idx = len(draws) - HIT_HORIZON

hit_rate_series = []
signal_counts = []
hit_counts = []

for idx in range(start_idx, end_idx):
    total_signals = 0
    total_hits = 0
    
    for ruota in RUOTE:
        signals = compute_freq_rit_fib_signals(draws, idx, N_WINDOW, ruota)
        total_signals += len(signals)
        for pair in signals:
            if check_hit(draws, idx, HIT_HORIZON, ruota, pair):
                total_hits += 1
    
    rate = total_hits / total_signals if total_signals > 0 else 0.0
    hit_rate_series.append(rate)
    signal_counts.append(total_signals)
    hit_counts.append(total_hits)
    
    if (idx - start_idx) % 200 == 0:
        elapsed = time.time() - t1
        pct = (idx - start_idx) / (end_idx - start_idx) * 100
        print(f"  Progress: {pct:.0f}% ({idx - start_idx}/{end_idx - start_idx}) "
              f"[{elapsed:.0f}s] signals={total_signals} hits={total_hits} rate={rate:.4f}")

t_part1 = time.time() - t1
n_points = len(hit_rate_series)
print(f"\nCompleted: {n_points} data points in {t_part1:.1f}s")

avg_signals = sum(signal_counts) / len(signal_counts)
avg_hits = sum(hit_counts) / len(hit_counts)
avg_rate = sum(hit_rate_series) / len(hit_rate_series)
print(f"Average signals/draw: {avg_signals:.1f}")
print(f"Average hits/draw: {avg_hits:.1f}")
print(f"Average hit rate: {avg_rate:.4f} ({avg_rate*100:.2f}%)")

# ── PART 2: Autocorrelation of smoothed hit rate ────────────────────
print("\n" + "="*70)
print("PART 2: Autocorrelation of smoothed hit rate")
print("="*70)

def rolling_average(series, k):
    """Compute rolling average with window k."""
    result = []
    for i in range(len(series)):
        start = max(0, i - k + 1)
        window = series[start:i+1]
        result.append(sum(window) / len(window))
    return result

def autocorrelation(series, max_lag):
    """Compute autocorrelation at lags 1..max_lag.
    r(k) = sum((x[t]-mean)*(x[t+k]-mean)) / sum((x[t]-mean)^2)
    """
    n = len(series)
    mean = sum(series) / n
    
    # Denominator: variance * n
    denom = sum((x - mean)**2 for x in series)
    if denom == 0:
        return [0.0] * max_lag
    
    result = []
    for lag in range(1, max_lag + 1):
        if lag >= n:
            result.append(0.0)
            continue
        numer = sum((series[t] - mean) * (series[t + lag] - mean) 
                    for t in range(n - lag))
        result.append(numer / denom)
    
    return result

def find_peaks(acf, min_prominence=0.05):
    """Find peaks in autocorrelation (local maxima above threshold)."""
    peaks = []
    for i in range(1, len(acf) - 1):
        if acf[i] > acf[i-1] and acf[i] > acf[i+1] and acf[i] > min_prominence:
            # Check prominence: must be higher than neighbors by min_prominence
            left_min = min(acf[max(0,i-5):i])
            right_min = min(acf[i+1:min(len(acf),i+6)])
            prominence = acf[i] - max(left_min, right_min)
            if prominence > min_prominence * 0.5:
                peaks.append((i + 1, acf[i], prominence))  # lag is 1-indexed
    
    peaks.sort(key=lambda x: -x[2])  # sort by prominence
    return peaks

all_acf_results = {}

for k in SMOOTHING_KS:
    print(f"\n--- Smoothing K={k} ---")
    smoothed = rolling_average(hit_rate_series, k)
    
    # Skip first k points (warm-up)
    analysis_series = smoothed[k:]
    
    acf = autocorrelation(analysis_series, min(MAX_LAG, len(analysis_series) // 3))
    all_acf_results[k] = acf
    
    # Find peaks
    peaks = find_peaks(acf)
    
    print(f"  Series length: {len(analysis_series)}")
    print(f"  ACF computed for lags 1-{len(acf)}")
    
    if peaks:
        print(f"  Top peaks (lag, r, prominence):")
        for lag, r, prom in peaks[:10]:
            mult3 = " [*3]" if lag % 3 == 0 else ""
            print(f"    lag={lag:4d}  r={r:+.4f}  prom={prom:.4f}{mult3}")
    else:
        print(f"  NO significant peaks found (all < 0.05)")
    
    # Show ACF at specific lags of interest
    interest_lags = [3, 6, 9, 10, 15, 18, 20, 25, 30, 36, 50, 75, 100, 150]
    print(f"  ACF at key lags:")
    for lag in interest_lags:
        if lag <= len(acf):
            print(f"    lag={lag:4d}  r={acf[lag-1]:+.4f}")

# Also compute raw (unsmoothed) autocorrelation
print(f"\n--- Raw (unsmoothed) hit rate ---")
acf_raw = autocorrelation(hit_rate_series, min(MAX_LAG, len(hit_rate_series) // 3))
all_acf_results["raw"] = acf_raw
peaks_raw = find_peaks(acf_raw, min_prominence=0.02)

print(f"  Top peaks (lag, r, prominence):")
if peaks_raw:
    for lag, r, prom in peaks_raw[:10]:
        mult3 = " [*3]" if lag % 3 == 0 else ""
        print(f"    lag={lag:4d}  r={r:+.4f}  prom={prom:.4f}{mult3}")
else:
    print("  NO significant peaks found")


# ── PART 3: Autocorrelation of raw pair appearances ─────────────────
print("\n" + "="*70)
print("PART 3: Autocorrelation of top pair appearances")
print("="*70)

# Find the 10 most frequent pairs across all ruote
t3 = time.time()
pair_freq = defaultdict(int)
for idx in range(len(draws)):
    for ruota in RUOTE:
        _, ruote_data = draws[idx]
        if ruota in ruote_data:
            nums = sorted(ruote_data[ruota])
            for i in range(len(nums)):
                for j in range(i+1, len(nums)):
                    pair_freq[(nums[i], nums[j], ruota)] += 1

# Top 10 pairs
top_pairs = sorted(pair_freq.items(), key=lambda x: -x[1])[:TOP_PAIRS_FOR_RAW]
print(f"Top {TOP_PAIRS_FOR_RAW} most frequent pairs:")
for (a, b, r), count in top_pairs:
    print(f"  ({a:2d},{b:2d}) on {r:10s}: {count} appearances")

# Compute binary appearance series and autocorrelation for each
for (a, b, r), count in top_pairs[:5]:  # Top 5 only for speed
    binary = []
    for idx in range(len(draws)):
        _, ruote_data = draws[idx]
        if r in ruote_data:
            nums = set(ruote_data[r])
            binary.append(1 if (a in nums and b in nums) else 0)
        else:
            binary.append(0)
    
    appearances = sum(binary)
    rate_pct = appearances / len(binary) * 100
    
    acf_pair = autocorrelation(binary, min(200, len(binary) // 3))
    peaks_pair = find_peaks(acf_pair, min_prominence=0.01)
    
    print(f"\n  Pair ({a},{b}) on {r}: {appearances} in {len(binary)} draws ({rate_pct:.2f}%)")
    if peaks_pair:
        print(f"    Top peaks:")
        for lag, r_val, prom in peaks_pair[:5]:
            print(f"      lag={lag:4d}  r={r_val:+.4f}  prom={prom:.4f}")
    else:
        print(f"    No significant peaks")

t_part3 = time.time() - t3
print(f"\nPart 3 completed in {t_part3:.1f}s")


# ── PART 4: Spectral analysis ──────────────────────────────────────
print("\n" + "="*70)
print("PART 4: Spectral analysis (DFT) of hit rate")
print("="*70)

t4 = time.time()

# Use smoothed series (K=20) for spectral analysis
smoothed_20 = rolling_average(hit_rate_series, 20)
series_for_fft = smoothed_20[20:]  # skip warm-up
n_spec = len(series_for_fft)
mean_spec = sum(series_for_fft) / n_spec
centered = [x - mean_spec for x in series_for_fft]

# Compute power at different frequencies
# frequency = k/N, period = N/k
# Test frequencies from period=4 to period=N/2
print(f"  Series length for spectral: {n_spec}")
print(f"  Testing periods from 4 to {n_spec//2}")

spectral_power = []
max_k = n_spec // 2  # Nyquist

for k in range(1, min(max_k, SPECTRAL_FREQS) + 1):
    # DFT at frequency k/N
    cos_sum = 0.0
    sin_sum = 0.0
    for t in range(n_spec):
        angle = 2 * math.pi * k * t / n_spec
        cos_sum += centered[t] * math.cos(angle)
        sin_sum += centered[t] * math.sin(angle)
    
    power = (cos_sum**2 + sin_sum**2) / n_spec
    period = n_spec / k
    spectral_power.append((k, period, power))

# Sort by power, get top results
spectral_power.sort(key=lambda x: -x[2])
top_spectral = spectral_power[:15]

print(f"\n  Top 15 spectral peaks:")
print(f"  {'Rank':>4s}  {'Freq k':>6s}  {'Period':>8s}  {'Power':>10s}")
for rank, (k, period, power) in enumerate(top_spectral, 1):
    mult3 = " [*3]" if abs(period - round(period/3)*3) < 1 else ""
    print(f"  {rank:4d}  {k:6d}  {period:8.1f}  {power:10.6f}{mult3}")

t_part4 = time.time() - t4
print(f"\nPart 4 completed in {t_part4:.1f}s")


# ── PART 5: Interpretation ──────────────────────────────────────────
print("\n" + "="*70)
print("INTERPRETATION")
print("="*70)

# Collect all significant findings
interpretation_lines = []

# Check raw ACF
if peaks_raw:
    best_raw_lag = peaks_raw[0][0]
    best_raw_r = peaks_raw[0][1]
    interpretation_lines.append(
        f"Raw hit rate: strongest cycle at lag {best_raw_lag} (r={best_raw_r:+.4f})"
    )
else:
    interpretation_lines.append("Raw hit rate: NO significant periodicity detected")

# Check smoothed ACFs
for k in SMOOTHING_KS:
    acf = all_acf_results[k]
    peaks = find_peaks(acf)
    if peaks:
        top = peaks[0]
        interpretation_lines.append(
            f"Smoothed K={k}: strongest cycle at lag {top[0]} "
            f"(r={top[1]:+.4f}, prom={top[2]:.4f})"
        )
        # Check if 75 is near a peak
        near_75 = [p for p in peaks if abs(p[0] - 75) <= 5]
        if near_75:
            interpretation_lines.append(
                f"  -> Peak near 75 found at lag {near_75[0][0]}! "
                f"Confirms window choice."
            )
    else:
        interpretation_lines.append(f"Smoothed K={k}: no significant peaks")

# Check spectral
if top_spectral:
    top_period = top_spectral[0][1]
    interpretation_lines.append(
        f"Spectral: dominant period = {top_period:.1f} extractions"
    )
    # Check if any period near 75
    near_75_spec = [s for s in top_spectral[:10] if abs(s[1] - 75) < 10]
    if near_75_spec:
        interpretation_lines.append(
            f"  -> Spectral peak near period 75 at {near_75_spec[0][1]:.1f}!"
        )

# Day-of-week check
multiples_of_3 = []
for k in SMOOTHING_KS:
    peaks = find_peaks(all_acf_results[k])
    for lag, r, prom in peaks[:5]:
        if lag % 3 == 0:
            multiples_of_3.append((k, lag, r))

if multiples_of_3:
    interpretation_lines.append(
        f"Day-of-week effect: {len(multiples_of_3)} peaks at multiples of 3 "
        f"(3 draws/week)"
    )
else:
    interpretation_lines.append("No day-of-week effect detected")

# Overall verdict
any_strong = False
for k in SMOOTHING_KS:
    peaks = find_peaks(all_acf_results[k])
    if peaks and peaks[0][1] > 0.15:
        any_strong = True
        break

if any_strong:
    interpretation_lines.append(
        "\nVERDICT: Signal shows PERIODIC structure. "
        "Natural cycle lengths identified above should be tested as window sizes."
    )
elif peaks_raw or any(find_peaks(all_acf_results[k]) for k in SMOOTHING_KS):
    interpretation_lines.append(
        "\nVERDICT: WEAK periodicity detected. "
        "Some structure exists but cycles are not strongly dominant."
    )
else:
    interpretation_lines.append(
        "\nVERDICT: Signal appears RANDOM. "
        "No natural cycle length found; window choice is arbitrary."
    )

for line in interpretation_lines:
    print(line)


# ── PART 6: Summary for notification ───────────────────────────────
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

summary_lines = [
    f"Autocorrelation Analysis - freq_rit+fib N={N_WINDOW}",
    f"Data: last {len(draws)} draws, analyzed {n_points} points",
    f"Avg hit rate: {avg_rate:.4f} ({avg_rate*100:.2f}%)",
    f"Avg signals/draw: {avg_signals:.1f}, hits/draw: {avg_hits:.1f}",
    "",
]

# Compact ACF results
for k in SMOOTHING_KS:
    peaks = find_peaks(all_acf_results[k])
    if peaks:
        top3 = ", ".join(f"L{p[0]}(r={p[1]:+.3f})" for p in peaks[:3])
        summary_lines.append(f"K={k}: {top3}")
    else:
        summary_lines.append(f"K={k}: no peaks")

# Raw
if peaks_raw:
    top3 = ", ".join(f"L{p[0]}(r={p[1]:+.3f})" for p in peaks_raw[:3])
    summary_lines.append(f"Raw: {top3}")
else:
    summary_lines.append("Raw: no peaks")

# Spectral
if top_spectral:
    top3_spec = ", ".join(f"P={s[1]:.0f}" for s in top_spectral[:3])
    summary_lines.append(f"Spectral top: {top3_spec}")

summary_lines.append("")
for line in interpretation_lines:
    summary_lines.append(line)

summary = "\n".join(summary_lines)
print(summary)

# ── Send notification ───────────────────────────────────────────────
print("\n" + "="*70)
print("Sending notification...")
print("="*70)

import httpx

title = "Autocorrelation Analysis - Periodicities"
msg = summary

try:
    resp = httpx.post(
        'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
        content=msg.encode('utf-8'),
        headers={'Title': title, 'Priority': '5'},
        timeout=10.0,
    )
    print(f"Notification sent: {resp.status_code}")
except Exception as e:
    print(f"Notification failed: {e}")

total_time = time.time() - t0
print(f"\nTotal runtime: {total_time:.1f}s")
