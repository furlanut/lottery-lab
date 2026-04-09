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
