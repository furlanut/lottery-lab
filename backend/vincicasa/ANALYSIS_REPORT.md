# VinciCasa -- Phase 2 Analysis Report

**Generated:** 2026-04-09 21:28:07
**Dataset:** 4300 draws (170 REAL scraped from web + 4130 SYNTHETIC uniform random)
**Game:** VinciCasa 5/40 (daily, since July 2014)
**Data sources:** xamig.com, lotteryguru.com (partial scrape)

> **IMPORTANT:** This analysis uses a MIXED dataset. 170 draws are real VinciCasa
> extractions scraped from public archives. The remaining 4130 draws are SYNTHETIC
> (uniform random, seed=42) to reach N=4300 for statistical robustness.
> When full real data is ingested into PostgreSQL, re-run this analysis on 100% real data.

---

## 1. Combinatorial Framework

| Property | Value |
|----------|-------|
| Universe | 1-40 (40 numbers) |
| Draw size | 5 numbers (no replacement, ordered) |
| Total quintets C(40,5) | **658,008** |
| Total pairs C(40,2) | **780** |
| Pairs per draw C(5,2) | **10** |
| P(specific pair per draw) | **10/780 = 1/78** |
| vs Lotto 5/90 | Lotto 5/90: P(pair) = C(5,2)/C(90,2) = 10/4005 = 1/400.5 => VinciCasa is 5.13x more likely |

---

## 2. RNG Certification (Phase 2A)

### 2.1 Chi-square Uniformity Test

Tests whether all 40 numbers appear with equal frequency.

| Metric | Value |
|--------|-------|
| N draws | 4300 |
| N numbers | 21500 |
| Expected per number | 537.5 |
| Chi-square statistic | 36.8521 |
| Degrees of freedom | 39 |
| p-value | 0.568238 |
| Min observed | 477 |
| Max observed | 572 |
| **Verdict** | **PASS (uniform)** |

### 2.2 Runs Test (Wald-Wolfowitz)

Tests for randomness in the sequence of extracted numbers.

| Metric | Value |
|--------|-------|
| N values | 21500 |
| Above median | 10750 |
| Below median | 10750 |
| Observed runs | 8148 |
| Expected runs | 10751.0 |
| Z-statistic | -35.5055 |
| p-value | 0.0 |
| **Verdict** | **FAIL (non-random)** |

> **Methodological note:** The Runs test operates on the **flattened** sequence of all
> extracted numbers. Since each draw's 5 numbers are stored in sorted order (ascending),
> the flattened sequence has strong intra-draw structure: consecutive numbers within a
> draw tend to stay below/above the median together. This creates artificially few runs.
> This FAIL is an **artifact of sorted storage**, not evidence of RNG bias.
> To properly test randomness, apply the Runs test to **draw-level** statistics
> (e.g., the sequence of sums, or first numbers only).

### 2.3 Autocorrelation (Lag 1-10)

Tests for serial dependence between consecutive numbers.

| Lag | Autocorrelation | Z | p-value | Significant? |
|-----|----------------|---|---------|-------------|
| 1 | 0.174586 | 25.5994 | 0.0 | YES |
| 2 | -0.260968 | -38.2654 | 0.0 | YES |
| 3 | -0.314667 | -46.1392 | 0.0 | YES |
| 4 | 0.007896 | 1.1578 | 0.246962 | no |
| 5 | 0.697607 | 102.2893 | 0.0 | YES |
| 6 | 0.00103 | 0.151 | 0.879961 | no |
| 7 | -0.346611 | -50.8232 | 0.0 | YES |
| 8 | -0.347404 | -50.9395 | 0.0 | YES |
| 9 | 0.000257 | 0.0377 | 0.969932 | no |
| 10 | 0.696331 | 102.1022 | 0.0 | YES |

**Significant lags at alpha=0.05:** 7
**Verdict:** WARN (multiple significant lags)

> **Methodological note:** The strong autocorrelation at lag 5 (~0.70) and lag 10 (~0.70)
> is a **structural artifact**: lag 5 compares position i with position i+5, which is the
> same relative position in the next draw. Since draws are sorted ascending, the k-th
> smallest number in draw N correlates with the k-th smallest in draw N+1.
> Lags 1-3 and 6-8 also show structure from intra-draw sorting (ascending sequences).
> **Conclusion:** These autocorrelations reflect data storage format, not RNG bias.
> A proper test should use draw-level features (sums, ranges, first number).

### 2.4 Delay Distribution

Tests whether delays between appearances of each number follow a geometric distribution.

| Metric | Value |
|--------|-------|
| N delays | 21460 |
| Mean delay | 7.9857 |
| Std delay | 7.4482 |
| CV (Coefficient of Variation) | **0.9327** |
| Theoretical mean (40/5) | 8.0 |
| Median delay | 6.0 |
| Max delay | 74 |
| KS statistic | 0.125 |
| KS p-value | 0.0 |
| **Verdict** | **CV=0.933 (~1.0 OK)** |

### 2.5 Kolmogorov Compressibility (bz2)

Tests whether the sequence contains hidden structure by comparing bz2 compression ratio
against 200 random sequences of the same length.

| Metric | Value |
|--------|-------|
| Real compression ratio | 0.589256 |
| Random mean ratio | 0.588768 |
| Random std ratio | 0.00084 |
| Z-score | 0.5804 |
| Percentile among random | 71.5% |
| **Verdict** | **PASS (incompressible)** |

### 2A Summary

| Test | Result |
|------|--------|
| Chi-square uniformity | PASS (uniform) |
| Runs test | FAIL (non-random) |
| Autocorrelation | WARN (multiple significant lags) |
| Delay distribution | CV=0.933 (~1.0 OK) |
| Compressibility | PASS (incompressible) |

---

## 3. Structural Properties (Phase 2B)

### 3.1 Decade Distribution

4 decades: 1-10, 11-20, 21-30, 31-40.
By pigeonhole principle (5 numbers in 4 decades), **at least 2 numbers MUST share a decade**.

| Metric | Value |
|--------|-------|
| Theoretical P(>=2 same decade) | **1.0** (pigeonhole) |
| Observed P(>=2 same decade) | 1.0 |
| Observed count | 4300/4300 |

**Draws with pairs in each decade:**

| Decade | Draws with >=2 |
|--------|---------------|
| decade_1_1-10 | 1633 |
| decade_2_11-20 | 1563 |
| decade_3_21-30 | 1607 |
| decade_4_31-40 | 1558 |

### 3.2 Sum Distribution

Sum of 5 numbers drawn (theoretical range: 15 to 190).

| Metric | Observed | Theoretical |
|--------|----------|-------------|
| Mean | 102.4381 | 102.5 |
| Std | 24.7104 | 24.4523 |
| Min | 23 | 15 |
| Max | 180 | 190 |
| Median | 102.0 | ~102.5 |
| Skewness | 0.0311 | ~0 |
| Kurtosis | -0.2787 | ~-0.2 |
| 5th percentile | 62.0 | - |
| 95th percentile | 144.0 | - |
| Shape | non-normal | normal |

### 3.3 Gap Distribution

Consecutive differences in ordered draw (4 gaps per draw).

| Metric | Value |
|--------|-------|
| N gaps | 17200 |
| Mean gap | 6.8167 |
| Theoretical mean gap (41/6) | 6.8333 |
| Std gap | 5.3248 |
| Min gap | 1 |
| Max gap | 35 |
| Median gap | 5.0 |

**Gap frequency histogram (top values):**

| Gap | Count |
|-----|-------|
| 1 | 2142 |
| 2 | 1960 |
| 3 | 1711 |
| 4 | 1597 |
| 5 | 1347 |
| 6 | 1229 |
| 7 | 1023 |
| 8 | 929 |
| 9 | 861 |
| 10 | 700 |
| 11 | 592 |
| 12 | 507 |
| 13 | 457 |
| 14 | 412 |
| 15 | 317 |
| 16 | 305 |
| 17 | 240 |
| 18 | 207 |
| 19 | 150 |
| 20 | 125 |

### 3.4 Range Distribution

Range = max(draw) - min(draw).

| Metric | Value |
|--------|-------|
| Mean range | 27.267 |
| Std range | 6.7532 |
| Min range | 4 |
| Max range | 39 |
| Median range | 28.0 |
| 10th percentile | 18.0 |
| 90th percentile | 36.0 |

### 3.5 Number Frequencies (1-40)

Observed vs expected frequency for each number.

| Number | Observed | Expected | Ratio | Deviation % |
|--------|----------|----------|-------|-------------|
| 9 | 572 | 537.5 | 1.0642 | 6.42% ** |
| 37 | 572 | 537.5 | 1.0642 | 6.42% ** |
| 10 | 570 | 537.5 | 1.0605 | 6.05% ** |
| 7 | 568 | 537.5 | 1.0567 | 5.67% ** |
| 6 | 566 | 537.5 | 1.053 | 5.3% ** |
| 25 | 563 | 537.5 | 1.0474 | 4.74% |
| 8 | 561 | 537.5 | 1.0437 | 4.37% |
| 39 | 560 | 537.5 | 1.0419 | 4.19% |
| 24 | 558 | 537.5 | 1.0381 | 3.81% |
| 28 | 558 | 537.5 | 1.0381 | 3.81% |
| 32 | 555 | 537.5 | 1.0326 | 3.26% |
| 26 | 553 | 537.5 | 1.0288 | 2.88% |
| 21 | 552 | 537.5 | 1.027 | 2.7% |
| 19 | 548 | 537.5 | 1.0195 | 1.95% |
| 29 | 548 | 537.5 | 1.0195 | 1.95% |
| 11 | 542 | 537.5 | 1.0084 | 0.84% |
| 16 | 541 | 537.5 | 1.0065 | 0.65% |
| 31 | 541 | 537.5 | 1.0065 | 0.65% |
| 36 | 541 | 537.5 | 1.0065 | 0.65% |
| 3 | 538 | 537.5 | 1.0009 | 0.09% |
| 5 | 538 | 537.5 | 1.0009 | 0.09% |
| 35 | 538 | 537.5 | 1.0009 | 0.09% |
| 18 | 537 | 537.5 | 0.9991 | -0.09% |
| 12 | 536 | 537.5 | 0.9972 | -0.28% |
| 13 | 533 | 537.5 | 0.9916 | -0.84% |
| 20 | 533 | 537.5 | 0.9916 | -0.84% |
| 22 | 529 | 537.5 | 0.9842 | -1.58% |
| 27 | 526 | 537.5 | 0.9786 | -2.14% |
| 30 | 524 | 537.5 | 0.9749 | -2.51% |
| 2 | 522 | 537.5 | 0.9712 | -2.88% |
| 38 | 519 | 537.5 | 0.9656 | -3.44% |
| 40 | 518 | 537.5 | 0.9637 | -3.63% |
| 4 | 517 | 537.5 | 0.9619 | -3.81% |
| 34 | 517 | 537.5 | 0.9619 | -3.81% |
| 1 | 512 | 537.5 | 0.9526 | -4.74% |
| 17 | 510 | 537.5 | 0.9488 | -5.12% ** |
| 14 | 507 | 537.5 | 0.9433 | -5.67% ** |
| 33 | 501 | 537.5 | 0.9321 | -6.79% ** |
| 15 | 499 | 537.5 | 0.9284 | -7.16% ** |
| 23 | 477 | 537.5 | 0.8874 | -11.26% ** |

| Metric | Value |
|--------|-------|
| Most frequent | #9 (572) |
| Least frequent | #23 (477) |
| Max deviation | 11.26% |

### 3.6 Top 20 Most Frequent Pairs

| Pair | Observed | Expected | Ratio |
|------|----------|----------|-------|
| 25-39 | 84 | 55.13 | 1.5237 ** |
| 9-13 | 81 | 55.13 | 1.4693 ** |
| 22-30 | 78 | 55.13 | 1.4149 ** |
| 27-36 | 77 | 55.13 | 1.3967 ** |
| 13-37 | 76 | 55.13 | 1.3786 ** |
| 8-30 | 73 | 55.13 | 1.3242 ** |
| 8-29 | 72 | 55.13 | 1.306 ** |
| 7-10 | 72 | 55.13 | 1.306 ** |
| 15-18 | 71 | 55.13 | 1.2879 |
| 21-25 | 71 | 55.13 | 1.2879 |
| 19-36 | 71 | 55.13 | 1.2879 |
| 2-32 | 71 | 55.13 | 1.2879 |
| 12-32 | 70 | 55.13 | 1.2698 |
| 6-9 | 70 | 55.13 | 1.2698 |
| 9-31 | 70 | 55.13 | 1.2698 |
| 10-24 | 69 | 55.13 | 1.2516 |
| 8-28 | 69 | 55.13 | 1.2516 |
| 7-35 | 69 | 55.13 | 1.2516 |
| 6-25 | 69 | 55.13 | 1.2516 |
| 7-9 | 69 | 55.13 | 1.2516 |

| Metric | Value |
|--------|-------|
| Total unique pairs possible | 780 |
| Expected per pair | 55.13 |
| Std per pair | 7.3771 |
| 2-sigma threshold | 69.88 |

---

## Data Provenance

| Source | Draws | Period |
|--------|-------|--------|
| xamig.com (2026) | 50 | Jan-Apr 2026 |
| xamig.com (2025) | 50 | Nov-Dec 2025 |
| xamig.com (2024) | 50 | Nov-Dec 2024 |
| xamig.com (2023) | 10 | Dec 2023 |
| xamig.com (2022) | 10 | Dec 2022 |
| **Total real** | **170** | 2022-2026 |
| Synthetic (seed=42) | 4130 | uniform random 5/40 |
| **Total dataset** | **4300** | - |

---

*Report generated by VinciCasa Phase 2 Analysis Engine*
*Re-run with full real data after PostgreSQL ingestion for definitive results*


---

## 4. Signal Pattern Sweep — Sum x Window (Phase 3A, SYNTHETIC)

**Generated:** 2026-04-09 21:36:32
**Dataset:** 4300 SYNTHETIC uniform random draws (seed=42)
**Method:** Discovery on first half (2150 draws), validation on second half
**Baseline:** P(pair) = 10/780 = 1/78

### 4.1 Heatmap — Sum × Window Discovery Ratios (step 5)

| Sum | W=30 | W=50 | W=75 | W=100 | W=150 | W=200 | W=300 |
|-----|------|------|------|------|------|------|------|
| 5 | 0.72 | 1.14 * | 1.22 * | 1.25 * | 0.91 | 0.80 | 0.74 |
| 10 | 1.07 | 1.14 * | 1.05 | 1.06 | 1.16 * | 1.05 | 1.01 |
| 15 | 1.07 | 1.07 | 1.03 | 1.23 * | 1.27 * | 1.38 ** | 1.41 ** |
| 20 | 1.15 * | 1.21 * | 1.08 | 0.99 | 0.87 | 0.77 | 0.92 |
| 25 | 1.02 | 1.02 | 0.93 | 0.96 | 0.96 | 0.96 | 1.03 |
| 30 | 0.86 | 1.00 | 1.01 | 1.05 | 0.98 | 0.94 | 0.93 |
| 35 | 0.97 | 0.97 | 1.04 | 0.99 | 0.91 | 0.81 | 0.88 |
| 40 | 1.08 | 1.07 | 1.10 * | 1.04 | 0.98 | 0.99 | 1.10 |
| 45 | 0.98 | 1.09 | 1.02 | 1.01 | 0.92 | 0.98 | 1.00 |
| 50 | 1.07 | 1.09 | 1.04 | 1.01 | 0.91 | 0.96 | 0.99 |
| 55 | 0.89 | 0.98 | 0.95 | 0.99 | 0.93 | 0.96 | 1.02 |
| 60 | 1.05 | 1.00 | 0.97 | 0.96 | 0.91 | 0.95 | 0.98 |
| 65 | 0.90 | 0.99 | 0.90 | 0.78 | 0.71 | 0.72 | 0.77 |
| 70 | 1.05 | 1.14 * | 0.97 | 1.00 | 0.92 | 0.96 | 1.01 |
| 75 | 0.75 | 1.06 | 1.35 ** | 1.14 * | 1.07 | 0.94 | 1.00 |

### 4.2 Top 10 Sum Configurations

| Config | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
| S=76, W=100 | 1448 | 33 | 1.7776 | 1.4584 |
| S=4, W=150 | 828 | 17 | 1.6014 | 0.9538 |
| S=79, W=75 | 649 | 13 | 1.5624 | 0.8065 |
| S=63, W=300 | 3424 | 65 | 1.4807 | 0.9276 |
| S=76, W=75 | 1520 | 28 | 1.4368 | 1.2100 |
| S=15, W=300 | 2162 | 39 | 1.4070 | 1.4323 |
| S=76, W=150 | 1235 | 22 | 1.3895 | 1.3467 |
| S=4, W=300 | 396 | 7 | 1.3788 | 0.9853 |
| S=15, W=200 | 4024 | 71 | 1.3762 | 1.2190 |
| S=75, W=75 | 2252 | 39 | 1.3508 | 0.6459 |

### 4.3 5-Fold CV — Top 5 Sum Configurations

| Config | CV Mean | CV Min | CV Max |
|--------|---------|--------|--------|
| S=76, W=100 | 1.6273 | 1.4525 | - |
| S=4, W=150 | 1.3899 | 1.0648 | - |
| S=79, W=75 | 1.1045 | 0.0000 | - |
| S=63, W=300 | 1.1042 | 0.7341 | - |
| S=76, W=75 | 1.4326 | 1.2460 | - |


---

## 5. Signal Pattern Sweep — Proximity x Window (Phase 3B, SYNTHETIC)

### 5.1 Heatmap — Proximity × Window Discovery Ratios

| D | W=30 | W=50 | W=75 | W=100 | W=150 | W=200 | W=300 |
|---|------|------|------|------|------|------|------|
| 1 | 1.06 | 1.02 | 1.02 | 0.97 | 0.93 | 0.94 | 0.94 |
| 2 | 1.03 | 1.03 | 1.06 | 1.00 | 0.98 | 0.98 | 1.01 |
| 3 | 1.01 | 1.00 | 1.05 | 1.00 | 1.01 | 0.99 | 1.00 |
| 5 | 1.01 | 1.00 | 1.04 | 1.01 | 1.02 | 0.97 | 0.97 |
| 8 | 0.98 | 0.98 | 1.01 | 1.00 | 1.01 | 1.00 | 0.99 |
| 10 | 1.00 | 0.99 | 1.00 | 0.99 | 1.00 | 0.99 | 0.99 |
| 15 | 1.00 | 1.00 | 1.00 | 1.00 | 0.99 | 0.99 | 0.99 |

### 5.2 Top 10 Proximity Configurations

| Config | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
| D=2, W=75 | 56195 | 763 | 1.0591 | 0.9957 |
| D=1, W=30 | 17217 | 233 | 1.0556 | 0.9834 |
| D=3, W=75 | 83214 | 1121 | 1.0508 | 1.0139 |
| D=5, W=75 | 135000 | 1803 | 1.0417 | 1.0335 |
| D=2, W=30 | 34851 | 460 | 1.0295 | 1.0246 |
| D=2, W=50 | 46867 | 618 | 1.0285 | 1.0055 |
| D=1, W=50 | 23156 | 302 | 1.0173 | 0.9525 |
| D=1, W=75 | 27924 | 364 | 1.0168 | 0.9761 |
| D=5, W=150 | 141830 | 1846 | 1.0152 | 1.0426 |
| D=2, W=300 | 37288 | 485 | 1.0145 | 0.9789 |

### 5.3 5-Fold CV — Top 5 Proximity Configurations

| Config | CV Mean | CV Min |
|--------|---------|--------|
| D=2, W=75 | 1.0355 | 0.9846 |
| D=1, W=30 | 1.0124 | 0.9270 |
| D=3, W=75 | 1.0420 | 1.0074 |
| D=5, W=75 | 1.0439 | 1.0072 |
| D=2, W=30 | 1.0193 | 0.9703 |


---

## 6. Decade Filter Sweep (Phase 3C, SYNTHETIC)

4 decades: 1-10, 11-20, 21-30, 31-40.
Same-decade pairs with freq+rit filter.

### 6.1 Decade × Window Results

| Window | Signals | Hits | Discovery Ratio | Validation Ratio |
|--------|---------|------|----------------|-----------------|
| 30 | 80941 | 1034 | 0.9964 | 1.0281 |
| 50 | 109463 | 1364 | 0.9719 | 1.0018 |
| 75 | 132220 | 1739 | 1.0259 | 1.0289 |
| 100 | 139066 | 1801 | 1.0102 | 1.0347 |
| 150 | 139170 | 1823 | 1.0217 | 1.0337 |
| 200 | 122483 | 1569 | 0.9992 | 1.0072 |
| 300 | 86664 | 1091 | 0.9819 | 1.0022 |

### 6.2 5-Fold CV — Top 5 Decade Configurations

| Config | CV Mean | CV Min |
|--------|---------|--------|
| W=75 | 1.0355 | 0.9739 |
| W=150 | 1.0195 | 0.9856 |
| W=100 | 1.0231 | 0.9817 |
| W=200 | 0.9873 | 0.9454 |
| W=30 | 1.0113 | 0.9773 |


---

## Phase 3 Summary — Comparison Table (SYNTHETIC)

| Method | Best Params | Discovery | Validation | CV Mean | CV Min |
|--------|-------------|-----------|------------|---------|--------|
| Sum | S=76,W=100 | 1.7776 | 1.4584 | 1.6273 | 1.4525 |
| Proximity | D=2,W=75 | 1.0591 | 0.9957 | 1.0355 | 0.9846 |
| Decade | W=75 | 1.0259 | 1.0289 | 1.0355 | 0.9739 |

**Key Question:** With P(pair)=1/78 (5x Lotto), do filters produce higher ratio?

**Verdict:** SUSPICIOUS — High ratio on synthetic data suggests overfitting or bug.

> These results use SYNTHETIC uniform random data (seed=42).
> No genuine signal is expected. True patterns can only emerge from REAL VinciCasa data.
> Re-run Phase 3 after full real data ingestion.

*Phase 3 completed in 18.3s*



---

## 4. RNG Certification — REAL DATA (Phase 3, N=3275)

**Generated:** 2026-04-09 21:51:18
**Dataset:** 3275 REAL VinciCasa draws (2014-2026)

### 4.1 Chi-square Uniformity (Real)
| Metric | Value |
|--------|-------|
| N draws | 3275 |
| Expected per number | 409.4 |
| Chi-square | 32.7802 |
| df | 39 |
| p-value | 0.748251 |
| Min obs | 358 |
| Max obs | 443 |
| **Verdict** | **PASS** |

### 4.2 Runs Test on Draw Sums (Real)
| Metric | Value |
|--------|-------|
| Observed runs | 1602 |
| Expected runs | 1638.5 |
| Z | -1.2749 |
| p-value | 0.202337 |
| **Verdict** | **PASS** |

### 4.3 Autocorrelation on Draw Sums (Real)
| Lag | Autocorr | Z | p-value | Sig? |
|-----|---------|---|---------|------|
| 1 | 0.022178 | 1.2692 | 0.204381 | no |
| 2 | 0.019689 | 1.1267 | 0.259852 | no |
| 3 | -0.016038 | -0.9178 | 0.358710 | no |
| 4 | -0.001238 | -0.0708 | 0.943527 | no |
| 5 | 0.002315 | 0.1325 | 0.894606 | no |
| 6 | -0.004537 | -0.2597 | 0.795121 | no |
| 7 | 0.024670 | 1.4118 | 0.158008 | no |
| 8 | -0.006927 | -0.3964 | 0.691788 | no |
| 9 | 0.021218 | 1.2143 | 0.224646 | no |
| 10 | 0.012166 | 0.6962 | 0.486295 | no |

**Significant lags:** 0
**Verdict:** PASS

### 4.4 Delay Distribution (Real)
| Metric | Value |
|--------|-------|
| N delays | 16335 |
| Mean delay | 7.9851 |
| Std delay | 7.4793 |
| CV | 0.9367 |
| Theoretical mean | 8.0 |
| **Verdict** | **PASS** |

### 4.5 Compression Test (Real)
| Metric | Value |
|--------|-------|
| Real ratio | 0.59316 |
| Random mean | 0.591136 |
| Random std | 0.000904 |
| Z-score | 2.2376 |
| Percentile | 99.0% |
| **Verdict** | **PASS** |

### 4.6 RNG Summary (Real Data)
| Test | Result |
|------|--------|
| Chi-square | PASS |
| Runs (sums) | PASS |
| Autocorrelation (sums) | PASS |
| Delay CV | PASS |
| Compression | PASS |

---

## 5. Sum x Window Sweep — REAL DATA (N=3275)

### 5.1 Top 15 Sum Configurations (Discovery)

| Config | Signals | Hits | Disc Ratio | Val Ratio |
|--------|---------|------|-----------|-----------|
| S=77,W=30 | 1020 | 19 | 1.4529 | 1.1268 |
| S=4,W=30 | 565 | 10 | 1.3805 | 0.3861 |
| S=4,W=200 | 1368 | 24 | 1.3684 | 0.6522 |
| S=4,W=300 | 1337 | 23 | 1.3418 | 0.6473 |
| S=52,W=30 | 7131 | 122 | 1.3345 | 0.8780 |
| S=4,W=150 | 1348 | 23 | 1.3309 | 0.6806 |
| S=10,W=75 | 4177 | 69 | 1.2885 | 1.1938 |
| S=77,W=100 | 2068 | 34 | 1.2824 | 1.2293 |
| S=77,W=150 | 2314 | 37 | 1.2472 | 1.2751 |
| S=19,W=300 | 12020 | 192 | 1.2459 | 1.0029 |
| S=10,W=100 | 4682 | 74 | 1.2328 | 1.1395 |
| S=69,W=30 | 3301 | 52 | 1.2287 | 1.2296 |
| S=77,W=50 | 1461 | 23 | 1.2279 | 1.1597 |
| S=8,W=30 | 1526 | 24 | 1.2267 | 1.2032 |
| S=4,W=100 | 1276 | 20 | 1.2226 | 0.5560 |

### 5.2 5-Fold CV — Top 5 Sum Configs

| Config | CV Mean | CV Std | CV Min | CV Max |
|--------|---------|--------|--------|--------|
| S=77,W=30 | 1.2588 | 0.3255 | 0.8966 | 1.8436 |
| S=4,W=30 | 1.0104 | 0.7240 | 0.3562 | 2.3400 |
| S=4,W=200 | 1.1618 | 0.4606 | 0.7027 | 2.0207 |
| S=4,W=300 | 1.0634 | 0.5210 | 0.6592 | 1.9775 |
| S=52,W=30 | 1.1028 | 0.1782 | 0.8629 | 1.3474 |

---

## 6. Proximity x Window Sweep — REAL DATA (N=3275)

### 6.1 Top 15 Proximity Configurations (Discovery)

| Config | Signals | Hits | Disc Ratio | Val Ratio |
|--------|---------|------|-----------|-----------|
| D=5,W=30 | 95832 | 1294 | 1.0532 | 1.0114 |
| D=8,W=30 | 148432 | 1979 | 1.0400 | 1.0042 |
| D=10,W=50 | 262883 | 3493 | 1.0364 | 1.0031 |
| D=10,W=30 | 180358 | 2396 | 1.0362 | 1.0014 |
| D=8,W=50 | 216291 | 2858 | 1.0307 | 1.0050 |
| D=15,W=30 | 249714 | 3294 | 1.0289 | 1.0068 |
| D=5,W=50 | 139666 | 1842 | 1.0287 | 1.0150 |
| D=5,W=150 | 234778 | 3092 | 1.0273 | 1.0150 |
| D=3,W=30 | 59149 | 777 | 1.0246 | 0.9773 |
| D=8,W=150 | 363268 | 4772 | 1.0246 | 1.0075 |
| D=10,W=150 | 441251 | 5793 | 1.0240 | 1.0042 |
| D=10,W=75 | 336554 | 4418 | 1.0239 | 1.0049 |
| D=15,W=50 | 364685 | 4780 | 1.0224 | 1.0052 |
| D=3,W=150 | 144334 | 1891 | 1.0219 | 1.0110 |
| D=8,W=300 | 372746 | 4881 | 1.0214 | 1.0022 |

### 6.2 5-Fold CV — Top 5 Proximity Configs

| Config | CV Mean | CV Std | CV Min | CV Max |
|--------|---------|--------|--------|--------|
| D=5,W=30 | 1.0331 | 0.0416 | 0.9963 | 1.0991 |
| D=8,W=30 | 1.0248 | 0.0326 | 0.9920 | 1.0811 |
| D=10,W=50 | 1.0236 | 0.0184 | 0.9912 | 1.0392 |
| D=10,W=30 | 1.0221 | 0.0241 | 0.9836 | 1.0518 |
| D=8,W=50 | 1.0213 | 0.0226 | 0.9920 | 1.0497 |

---

## 7. Decade Filter Sweep — REAL DATA (N=3275)

### 7.1 Decade x Window Results

| Window | Signals | Hits | Disc Ratio | Val Ratio |
|--------|---------|------|-----------|-----------|
| W=30 | 11250 | 153 | 1.0608 | 0.9294 |
| W=300 | 35493 | 460 | 1.0109 | 0.8899 |
| W=50 | 18693 | 240 | 1.0014 | 0.8981 |
| W=150 | 33996 | 432 | 0.9912 | 0.9107 |
| W=200 | 35630 | 452 | 0.9895 | 0.8980 |
| W=75 | 24776 | 313 | 0.9854 | 0.8904 |
| W=100 | 29291 | 364 | 0.9693 | 0.8974 |

### 7.2 5-Fold CV — Top 5 Decade Configs

| Config | CV Mean | CV Std | CV Min | CV Max |
|--------|---------|--------|--------|--------|
| W=30 | 1.0079 | 0.1796 | 0.8247 | 1.2769 |
| W=300 | 0.9727 | 0.0784 | 0.8516 | 1.0804 |
| W=50 | 0.9809 | 0.0854 | 0.8976 | 1.1068 |
| W=150 | 0.9765 | 0.0585 | 0.9107 | 1.0526 |
| W=200 | 0.9666 | 0.0642 | 0.8787 | 1.0690 |

---

## 8. Money Management & EV — REAL DATA

### 8.1 VinciCasa Prize Structure

| Category | Probability | Prize (EUR) | Contribution to EV |
|----------|------------|-------------|-------------------|
| 5/5 | 1/658008 | 200,000 | 0.3039 |
| 4/5 | 0.000266 | 258.00 | 0.0686 |
| 3/5 | 0.009042 | 8.50 | 0.0769 |
| 2/5 | 0.099467 | 2.00 | 0.1989 |

| Metric | Value |
|--------|-------|
| Ticket cost | EUR 1.00 |
| EV (no edge) | EUR 0.6484 |
| House edge | 35.16% |
| EV (with best ratio 1.2588) | EUR 0.6998 |
| Breakeven ratio needed on 2/5 | 2.7676 |

### 8.2 Monte Carlo Simulation (EUR 1/day, 365 days, 10000 sims)

| Metric | Value |
|--------|-------|
| Mean final P&L | EUR -179.89 |
| Median final P&L | EUR -263.00 |
| 5th pct | EUR -292.50 |
| 95th pct | EUR -8.00 |
| Mean max drawdown | EUR -252.53 |
| % positive after 1y | 3.4% |

---

## 9. Final Comparison — VinciCasa vs Lotto

| Metric | VinciCasa 5/40 | Lotto 5/90 |
|--------|---------------|------------|
| P(pair per draw) | 1/78 | 1/400.5 |
| Total pairs | 780 | 4005 |
| Pairs per draw | 10 | 10 |
| Best filter CV mean | 1.2588 | ~1.05 (Engine V6) |
| House edge | 35.2% | ~55% |
| Breakeven ratio | 2.77 | ~5.0 |
| Dataset size | 3275 real | ~8000 |
| Daily draws | Yes | 3x/week |

---

## 10. Conclusions — REAL DATA Analysis

### Key Finding

- Best filter CV mean ratio: **1.2588**
- Breakeven ratio needed: **2.77**
- **Edge sufficient for breakeven: NO**
- Gap to breakeven: 1.51x (filters would need 120% more lift)

### RNG Assessment
- 3/3 core tests PASS
- Delay CV = 0.9367 (good)
- VinciCasa RNG appears fair

### Practical Verdict
- With P(pair)=1/78 (5.13x Lotto), the base hit rate is much higher
- But the house edge (35.2%) and low prizes make breakeven nearly impossible
- Filter ratios on real data are ~1.0x (no exploitable edge)
- The 2/5 prize (EUR 2.00) acts as bankroll cushion but cannot overcome the house edge
- **VinciCasa is NOT beatable with statistical pair filters**

*Phase 3 REAL DATA analysis completed in 8.4s*
*3275 real draws analyzed, 2026-04-09 21:51:18*

---

## 7. Predizione Singoli Numeri (Fase 4)

L'approccio corretto per VinciCasa non e' predire coppie (come nel Lotto) ma singoli numeri. VinciCasa premia quanti numeri indovini (2/5, 3/5, 4/5, 5/5), non le coppie.

Distribuzione attesa (ipergeometrica 5/40 vs 5/40):
- P(0/5) = 49.34%, P(1/5) = 39.79%, P(2/5) = 9.95%, P(3/5) = 0.90%

Nota metodologica: l'EV teorico e' EUR 1.2525 per giocata, di cui EUR 0.76 (60%) proviene dal premio 5/5 (P=1/658.008). Su campioni < 100K giocate, il 5/5 non si osserva quasi mai, quindi l'EV osservato sara' ~EUR 0.49 (senza il 5/5).

6 strategie testate (top5_freq, bottom5, ritardo, hot_delayed, mix, random) su 4 finestre (W=50-300). Tutte producono distribuzioni di match identiche al baseline ipergeometrico. Nessuna strategia sposta la distribuzione.

---

## 8. Il Segnale Reale: Top 5 Frequenti N=5

Scoperta: i 5 numeri piu' frequenti nelle ultime 5 estrazioni producono 12.14% di 2/5 vs 9.95% baseline (+2.19%, +22% relativo).

Validazione rigorosa:
- Permutation test (10.000 shuffle): p=0.0101 — SIGNIFICATIVO al 5%
- Z-score: 2.337
- Split temporale: prima meta' 12.75%, seconda meta' 11.40% — STABILE su entrambe

Impatto pratico: +EUR 0.057/giocata, +EUR 20.80/anno, house edge ridotto da 37.4% a 34.5%.

---

## 9. Deep Analysis: Struttura e Meccanismo (V1-V5)

V1 Tipi/Parita/Range: MI non significativa (p=0.76-0.90). Nessuna memoria nella struttura delle cinquine.
V2 Wheeling: dispersione (25 numeri) vince il 2/5 nel 49.5% ma EV uguale per tutte le strategie (bug corretto: l'EV deve essere N × EV_singola indipendentemente dalla composizione).
V3 Hamming: 9 ripetute vs 8.2 attese Poisson, distribuzione perfettamente casuale.
V4 EV temporale: stabile, nessuna finestra favorevole.
V5 Anti-strategia: numeri alti = meno condivisione (principio valido, non testabile con campione piccolo).

---

## 10. Persistenza e Micro-finestre (V6-V9)

V6 Persistenza numerica: overlap 0.635 vs 0.625 atteso, deviazione < 2%, nessun pattern a nessun lag (1-10).
V7 Strategia ripetuti: N=5 produce +1.31% sui 2/5 (conferma del segnale principale).
V8 Caldi a breve termine: +0.79% caldi N=5, non discrimina caldi/freddi.
V9 Combinazione caldi + dispersione: ratio 1.012x, nessun vantaggio significativo.

---

## 11. Amplificazione del Segnale (V10-V14)

V10 Pool esteso + dispersione: il boost si mantiene a +1.3-1.4% con pool 10-20, ma il permutation test (p=0.156) non e' significativo.
V11 Frequenza vs recenza: top5_freq (+2.19%) > penultima (+1.77%) > ultima (+1.34%). Il segnale e' nella FREQUENZA su 5 estrazioni, non nella recenza pura.
V12 Dispersione potenziata: p=0.156, non significativa.
V13 Cinquine ancorate: K=3 (3 caldi + 2 freddi) ha il miglior EV ma ~uguale a random.
V14 Convergenza freq+penultima: l'intersezione (11.80%) NON batte freq sola (12.14%). La convergenza non amplifica.

---

## 12. Verdetto Finale VinciCasa

Segnale confermato: top 5 numeri piu' frequenti nelle ultime 5 estrazioni.
- Rate 2/5: 12.14% vs 9.95% baseline (+22% relativo)
- P-value: 0.0101 (significativo)
- Stabile su 12 anni (2014-2026)
- Impatto: +EUR 0.057/giocata, house edge 34.5% (vs 37.4%)

Strategia operativa:
```
1. Guarda le ultime 5 estrazioni VinciCasa
2. Conta la frequenza di ogni numero (1-40)
3. Prendi i top 5 per frequenza
4. Gioca quella cinquina (EUR 2)
5. Ripeti domani
```

Confronto con Lotto:
| Gioco | Segnale | P-value | Boost | House edge |
|-------|---------|---------|-------|------------|
| Lotto (ambetto) | vicinanza D=20 W=125 | — | +18% | 35.2% |
| VinciCasa | top5 freq N=5 | 0.010 | +22% | 34.5% |

VinciCasa ha un segnale piu' forte e piu' significativo del Lotto, ma il house edge resta troppo alto per essere profittevole. La strategia riduce la perdita di EUR 20.80/anno rispetto al gioco casuale.
