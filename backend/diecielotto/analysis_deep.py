from __future__ import annotations

"""10eLotto Deep Analysis — Test D1-D5.

Analisi ordine estrazione, pattern PRNG, dipendenze Extra, lag 288, numeri spia.
"""

import logging
from collections import Counter
from math import sqrt

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def carica_dati() -> list[dict]:
    """Carica estrazioni con ordine originale (n1-n20) e numeri oro."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )
        result = []
        for r in rows:
            # n1-n20 nell'ordine del DB (potrebbe essere originale o ordinato)
            seq = [
                r.n1,
                r.n2,
                r.n3,
                r.n4,
                r.n5,
                r.n6,
                r.n7,
                r.n8,
                r.n9,
                r.n10,
                r.n11,
                r.n12,
                r.n13,
                r.n14,
                r.n15,
                r.n16,
                r.n17,
                r.n18,
                r.n19,
                r.n20,
            ]
            extras = []
            for i in range(1, 16):
                v = getattr(r, f"extra_{i}", None)
                if v is not None:
                    extras.append(v)
            result.append(
                {
                    "seq": seq,
                    "numeri_set": set(seq),
                    "numeri_sorted": sorted(seq),
                    "extra": extras,
                    "extra_set": set(extras),
                    "oro": r.numero_oro,
                    "doppio_oro": r.doppio_oro,
                    "data": r.data,
                    "ora": r.ora,
                }
            )
        return result
    finally:
        session.close()


# ===================================================================
# TEST D1 — L'ordine di estrazione conta?
# ===================================================================


def test_d1(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("TEST D1 — ORDINE DI ESTRAZIONE E NUMERI ORO")
    print("=" * 70)

    # D1.0: Verifica se i dati preservano l'ordine
    sorted_count = 0
    for e in estrazioni[:1000]:
        if e["seq"] == sorted(e["seq"]):
            sorted_count += 1
    pct_sorted = sorted_count / 1000 * 100
    print(f"\n  D1.0: Sequenze ordinate: {pct_sorted:.1f}%")
    if pct_sorted > 95:
        print("  ⚠ I dati sono ORDINATI — l'ordine originale è PERSO.")
        print("  Possiamo comunque analizzare Oro e Doppio Oro (salvati a parte).")
    else:
        print("  ✓ I dati preservano l'ordine originale di estrazione!")

    # D1.1: Distribuzione Numero Oro
    print(f"\n  D1.1: Distribuzione Numero Oro (n={n})")
    oro_freq = Counter(e["oro"] for e in estrazioni)
    expected_oro = n / 90.0
    chi2_oro = sum((oro_freq.get(i, 0) - expected_oro) ** 2 / expected_oro for i in range(1, 91))
    z_oro = (chi2_oro - 89) / sqrt(2 * 89)
    ok = abs(z_oro) < 3.0
    min_oro = min(oro_freq.get(i, 0) for i in range(1, 91))
    max_oro = max(oro_freq.get(i, 0) for i in range(1, 91))
    print(f"     Chi2={chi2_oro:.1f}, z={z_oro:.2f}  {'PASS' if ok else '*** FAIL ***'}")
    print(f"     Atteso={expected_oro:.0f}, min={min_oro}, max={max_oro}")

    # Top/bottom 5 Oro
    top5 = oro_freq.most_common(5)
    bot5 = oro_freq.most_common()[-5:]
    print(f"     Top 5 Oro: {[(n, f, f'+{f - expected_oro:.0f}') for n, f in top5]}")
    print(f"     Bot 5 Oro: {[(n, f, f'{f - expected_oro:.0f}') for n, f in bot5]}")

    # D1.2: Distribuzione Doppio Oro
    doro_freq = Counter(e["doppio_oro"] for e in estrazioni)
    chi2_doro = sum((doro_freq.get(i, 0) - expected_oro) ** 2 / expected_oro for i in range(1, 91))
    z_doro = (chi2_doro - 89) / sqrt(2 * 89)
    ok_do = abs(z_doro) < 3.0
    print("\n  D1.2: Distribuzione Doppio Oro")
    print(f"     Chi2={chi2_doro:.1f}, z={z_doro:.2f}  {'PASS' if ok_do else '*** FAIL ***'}")

    # D1.3: Autocorrelazione sequenza Numeri Oro
    oro_seq = [e["oro"] for e in estrazioni]
    mean_oro = sum(oro_seq) / n
    var_oro = sum((x - mean_oro) ** 2 for x in oro_seq) / n

    print("\n  D1.3: Autocorrelazione Numero Oro")
    max_ac_oro = 0.0
    for lag in [1, 2, 3, 5, 10, 20, 50, 100, 288]:
        if lag >= n:
            continue
        cov = sum(
            (oro_seq[i] - mean_oro) * (oro_seq[i + lag] - mean_oro) for i in range(n - lag)
        ) / (n - lag)
        ac = cov / var_oro if var_oro > 0 else 0
        sig = "***" if abs(ac) > 0.02 else ""
        print(f"     lag {lag:>4}: r={ac:+.5f} {sig}")
        if abs(ac) > max_ac_oro:
            max_ac_oro = abs(ac)
    print(f"     Max |r|={max_ac_oro:.5f}  {'PASS' if max_ac_oro < 0.03 else '*** FAIL ***'}")

    # D1.4: Distanza |Oro_t - Oro_t+1|
    dist_oro = [abs(oro_seq[i] - oro_seq[i + 1]) for i in range(n - 1)]
    mean_dist = sum(dist_oro) / len(dist_oro)
    # Expected mean distance between 2 uniform [1,90]: E(|X-Y|) = (90^2-1)/(3*90) ≈ 29.98
    expected_dist = (90 * 90 - 1) / (3 * 90)
    se_dist = sqrt(sum((d - mean_dist) ** 2 for d in dist_oro) / len(dist_oro)) / sqrt(
        len(dist_oro)
    )
    z_dist = (mean_dist - expected_dist) / se_dist if se_dist > 0 else 0
    print("\n  D1.4: Distanza |Oro_t - Oro_t+1|")
    print(f"     Media={mean_dist:.3f}, attesa={expected_dist:.3f}")
    print(f"     z={z_dist:.2f}  {'PASS' if abs(z_dist) < 3.0 else '*** FAIL ***'}")

    # Distribuzione distanze — bin per decina
    dist_bins = Counter(d // 10 for d in dist_oro)
    print("     Dist per decina: ", end="")
    for b in range(9):
        print(f"[{b * 10}-{b * 10 + 9}]={dist_bins.get(b, 0)} ", end="")
    print()

    # D1.5: Coppia (Oro, Doppio Oro) — distanza
    dist_od = [abs(e["oro"] - e["doppio_oro"]) for e in estrazioni]
    mean_od = sum(dist_od) / n
    # Expected same as |X-Y| uniform
    se_od = sqrt(sum((d - mean_od) ** 2 for d in dist_od) / n) / sqrt(n)
    z_od = (mean_od - expected_dist) / se_od if se_od > 0 else 0
    print("\n  D1.5: Distanza |Oro - DoppioOro|")
    print(f"     Media={mean_od:.3f}, attesa={expected_dist:.3f}")
    print(f"     z={z_od:.2f}  {'PASS' if abs(z_od) < 3.0 else '*** FAIL ***'}")

    # Indipendenza Oro/DoppioOro: chi-quadro su tabella 9x9 decine
    tab = Counter()
    for e in estrazioni:
        d_oro = (e["oro"] - 1) // 10
        d_doro = (e["doppio_oro"] - 1) // 10
        tab[(d_oro, d_doro)] += 1

    chi2_ind = 0.0
    for do in range(9):
        for dd in range(9):
            obs = tab.get((do, dd), 0)
            # Marginali
            row_sum = sum(tab.get((do, j), 0) for j in range(9))
            col_sum = sum(tab.get((i, dd), 0) for i in range(9))
            exp = row_sum * col_sum / n if n > 0 else 1
            if exp > 0:
                chi2_ind += (obs - exp) ** 2 / exp
    df_ind = (9 - 1) * (9 - 1)  # 64
    z_ind = (chi2_ind - df_ind) / sqrt(2 * df_ind)
    print("\n  D1.6: Indipendenza Oro×DoppioOro (decine)")
    print(f"     Chi2={chi2_ind:.1f}, df={df_ind}, z={z_ind:.2f}")
    print(f"     {'PASS' if abs(z_ind) < 3.0 else '*** FAIL — NON INDIPENDENTI ***'}")


# ===================================================================
# TEST D2 — Pattern sequenziali nel PRNG
# ===================================================================


def test_d2(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("TEST D2 — PATTERN SEQUENZIALI NEL PRNG")
    print("=" * 70)

    # Verifica se n1-n20 sono ordinati
    sorted_pct = sum(1 for e in estrazioni if e["seq"] == sorted(e["seq"])) / n * 100

    if sorted_pct > 95:
        print(f"\n  Dati ordinati ({sorted_pct:.0f}%) — test D2 non applicabile.")
        print("  I campi n1-n20 contengono i numeri ordinati, non la sequenza PRNG.")
        print("  Test D2 SKIPPED.")
        return

    print(f"  Dati con ordine originale ({100 - sorted_pct:.0f}% non ordinati)")

    # D2.1: Differenze consecutive nella sequenza
    diffs = []
    for e in estrazioni:
        for i in range(1, 20):
            diffs.append(e["seq"][i] - e["seq"][i - 1])
    mean_diff = sum(diffs) / len(diffs)
    se_diff = sqrt(sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)) / sqrt(len(diffs))
    z_diff = mean_diff / se_diff if se_diff > 0 else 0
    print("\n  D2.1: Differenza media consecutiva seq[k]-seq[k-1]")
    print(f"     Media={mean_diff:.4f} (atteso ~0)")
    print(f"     z={z_diff:.2f}  {'PASS' if abs(z_diff) < 3.0 else '*** FAIL ***'}")

    # D2.2: Somma parziale primi 10 vs ultimi 10
    sum_first10 = [sum(e["seq"][:10]) for e in estrazioni]
    sum_last10 = [sum(e["seq"][10:]) for e in estrazioni]
    mean_f = sum(sum_first10) / n
    mean_l = sum(sum_last10) / n
    diff_fl = [sum_first10[i] - sum_last10[i] for i in range(n)]
    mean_dfl = sum(diff_fl) / n
    se_dfl = sqrt(sum((d - mean_dfl) ** 2 for d in diff_fl) / n) / sqrt(n)
    z_dfl = mean_dfl / se_dfl if se_dfl > 0 else 0
    print("\n  D2.2: Somma primi 10 vs ultimi 10")
    print(f"     Media primi 10={mean_f:.1f}, ultimi 10={mean_l:.1f}")
    print(f"     Diff={mean_dfl:.1f}, z={z_dfl:.2f}")
    print(f"     {'PASS' if abs(z_dfl) < 3.0 else '*** FAIL ***'}")

    # D2.3: Ultimo numero estrazione t correlato con Oro estrazione t+1
    last20 = [e["seq"][19] for e in estrazioni]
    oro_next = [e["oro"] for e in estrazioni]
    # Correlazione tra last20[t] e oro_next[t+1]
    pairs = [(last20[i], oro_next[i + 1]) for i in range(n - 1)]
    mx = sum(p[0] for p in pairs) / len(pairs)
    my = sum(p[1] for p in pairs) / len(pairs)
    cov = sum((p[0] - mx) * (p[1] - my) for p in pairs) / len(pairs)
    sx = sqrt(sum((p[0] - mx) ** 2 for p in pairs) / len(pairs))
    sy = sqrt(sum((p[1] - my) ** 2 for p in pairs) / len(pairs))
    r = cov / (sx * sy) if sx > 0 and sy > 0 else 0
    z_r = r * sqrt(n - 1)
    print("\n  D2.3: Correlazione ultimo_20[t] vs Oro[t+1]")
    print(f"     r={r:.5f}, z={z_r:.2f}")
    print(f"     {'PASS' if abs(z_r) < 3.0 else '*** FAIL — PRNG CONTINUO? ***'}")


# ===================================================================
# TEST D3 — Dipendenza strutturale Extra dato Base
# ===================================================================


def test_d3(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("TEST D3 — DIPENDENZA STRUTTURALE EXTRA DATO BASE")
    print("=" * 70)

    # D3.1: Correlazione count_decina_base vs count_decina_extra
    print("\n  D3.1: Correlazione per decina (base vs extra)")
    for dec in range(9):
        low = dec * 10 + 1
        high = dec * 10 + 10
        base_counts = []
        extra_counts = []
        for e in estrazioni:
            bc = sum(1 for x in e["numeri_sorted"] if low <= x <= high)
            ec = sum(1 for x in e["extra"] if low <= x <= high)
            base_counts.append(bc)
            extra_counts.append(ec)

        mb = sum(base_counts) / n
        me = sum(extra_counts) / n
        covbe = sum((base_counts[i] - mb) * (extra_counts[i] - me) for i in range(n)) / n
        sb = sqrt(sum((x - mb) ** 2 for x in base_counts) / n)
        se = sqrt(sum((x - me) ** 2 for x in extra_counts) / n)
        r = covbe / (sb * se) if sb > 0 and se > 0 else 0
        print(
            f"     Dec {low:>2}-{high:>2}: r={r:+.4f}  (base media={mb:.2f}, extra media={me:.2f})"
        )

    # D3.2: Autocorrelazione distribuzione decine nella base
    print("\n  D3.2: Autocorrelazione distribuzione decine (lag 1)")
    for dec in range(9):
        low = dec * 10 + 1
        high = dec * 10 + 10
        counts = [sum(1 for x in e["numeri_sorted"] if low <= x <= high) for e in estrazioni]
        mc = sum(counts) / n
        vc = sum((x - mc) ** 2 for x in counts) / n
        if vc > 0:
            cov1 = sum((counts[i] - mc) * (counts[i + 1] - mc) for i in range(n - 1)) / (n - 1)
            ac1 = cov1 / vc
        else:
            ac1 = 0
        sig = "***" if abs(ac1) > 0.02 else ""
        print(f"     Dec {low:>2}-{high:>2}: AC(1)={ac1:+.5f} {sig}")


# ===================================================================
# TEST D4 — Lag 288 (ciclo giornaliero)
# ===================================================================


def test_d4(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("TEST D4 — LAG 288 (CICLO GIORNALIERO)")
    print("=" * 70)

    somme = [sum(e["numeri_sorted"]) for e in estrazioni]
    mean_s = sum(somme) / n
    var_s = sum((s - mean_s) ** 2 for s in somme) / n

    # D4.1: Autocorrelazione somme a vari lag
    print("\n  D4.1: Autocorrelazione somma 20 numeri")
    lags = [1, 2, 5, 10, 50, 100, 144, 288, 576, 864]
    for lag in lags:
        if lag >= n:
            continue
        cov = sum((somme[i] - mean_s) * (somme[i + lag] - mean_s) for i in range(n - lag)) / (
            n - lag
        )
        ac = cov / var_s if var_s > 0 else 0
        se_ac = 1.0 / sqrt(n - lag)
        z = ac / se_ac
        sig = "***" if abs(z) > 3.0 else ("*" if abs(z) > 2.0 else "")
        label = ""
        if lag == 144:
            label = " (12h)"
        elif lag == 288:
            label = " (24h)"
        elif lag == 576:
            label = " (48h)"
        elif lag == 864:
            label = " (72h)"
        print(f"     lag {lag:>4}{label:<6}: r={ac:+.6f}  z={z:+.2f} {sig}")

    # D4.2: Overlap medio a lag 288
    expected_ov = 20 * 20 / 90  # 4.444
    print("\n  D4.2: Overlap a lag 288 (1 giorno)")
    for lag in [1, 144, 288, 576]:
        if lag >= n:
            continue
        overlaps = []
        for i in range(lag, n):
            s1 = set(estrazioni[i - lag]["numeri_sorted"])
            s2 = set(estrazioni[i]["numeri_sorted"])
            overlaps.append(len(s1 & s2))
        mo = sum(overlaps) / len(overlaps)
        se_o = sqrt(sum((x - mo) ** 2 for x in overlaps) / len(overlaps)) / sqrt(len(overlaps))
        z_o = (mo - expected_ov) / se_o if se_o > 0 else 0
        sig = "***" if abs(z_o) > 3.0 else ""
        print(f"     lag {lag:>4}: overlap={mo:.4f} ± {se_o:.4f}  z={z_o:+.2f} {sig}")

    # D4.3: Numero Oro a lag 288
    oro_seq = [e["oro"] for e in estrazioni]
    mean_oro = sum(oro_seq) / n
    var_oro = sum((x - mean_oro) ** 2 for x in oro_seq) / n

    print("\n  D4.3: Autocorrelazione Numero Oro")
    for lag in [1, 144, 288, 576]:
        if lag >= n:
            continue
        cov = sum(
            (oro_seq[i] - mean_oro) * (oro_seq[i + lag] - mean_oro) for i in range(n - lag)
        ) / (n - lag)
        ac = cov / var_oro if var_oro > 0 else 0
        se_ac = 1.0 / sqrt(n - lag)
        z = ac / se_ac
        sig = "***" if abs(z) > 3.0 else ""
        print(f"     lag {lag:>4}: r={ac:+.6f}  z={z:+.2f} {sig}")


# ===================================================================
# TEST D5 — Numeri spia con Bonferroni
# ===================================================================


def test_d5(estrazioni: list[dict]):
    n = len(estrazioni)
    print("\n" + "=" * 70)
    print("TEST D5 — NUMERI SPIA (8010 coppie, Bonferroni)")
    print("=" * 70)

    baseline = 20.0 / 90.0  # P(Y nella ventina) = 0.2222
    n_tests = 90 * 89  # 8010

    # Per velocità, precalcola le presenze
    log.info("Precalcolo presenze per 90 numeri...")
    presence = {}
    for num in range(1, 91):
        presence[num] = [num in e["numeri_set"] for e in estrazioni]

    log.info("Calcolo 8010 coppie...")
    significant = []
    max_z = 0.0
    max_pair = (0, 0)

    for x in range(1, 91):
        for y in range(1, 91):
            if x == y:
                continue
            # Quando X presente in t, conta se Y presente in t+1
            hits = 0
            total = 0
            for t in range(n - 1):
                if presence[x][t]:
                    total += 1
                    if presence[y][t + 1]:
                        hits += 1

            if total < 100:
                continue

            p_obs = hits / total
            se = sqrt(baseline * (1 - baseline) / total)
            z = (p_obs - baseline) / se if se > 0 else 0

            if abs(z) > max_z:
                max_z = abs(z)
                max_pair = (x, y)

            # Bonferroni: soglia = 3.89 per alpha=0.05 su 8010 test
            bonferroni_z = 4.27  # alpha=0.01/8010
            if abs(z) > bonferroni_z:
                significant.append((x, y, p_obs, baseline, z, total))

    print(f"\n  Baseline P(Y in ventina) = {baseline:.4f}")
    print(f"  Coppie testate: {n_tests}")
    print(f"  Soglia Bonferroni (α=0.01/{n_tests}): z > 4.27")
    print(f"\n  Coppia con max |z|: ({max_pair[0]}, {max_pair[1]})")
    print(f"  Max |z| = {max_z:.2f}")
    print(f"\n  Coppie significative dopo Bonferroni: {len(significant)}")

    if significant:
        print("\n  DETTAGLIO COPPIE SIGNIFICATIVE:")
        for x, y, p_obs, bl, z, tot in sorted(significant, key=lambda r: -abs(r[4])):
            print(f"    ({x:>2}, {y:>2}): P={p_obs:.4f} vs {bl:.4f}, z={z:+.2f}, n={tot}")
        print(f"\n  *** {len(significant)} COPPIE SIGNIFICATIVE — POSSIBILE BIAS PRNG ***")
    else:
        print("\n  PASS — Nessuna coppia significativa. I numeri sono indipendenti.")


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 70)
    print("10eLOTTO — DEEP ANALYSIS (D1-D5)")
    print("=" * 70)

    log.info("Caricamento dati...")
    estrazioni = carica_dati()
    n = len(estrazioni)
    print(f"\nDataset: {n} estrazioni")
    print(f"Periodo: {estrazioni[0]['data']} — {estrazioni[-1]['data']}")

    test_d1(estrazioni)
    test_d2(estrazioni)
    test_d3(estrazioni)
    test_d4(estrazioni)
    test_d5(estrazioni)

    print("\n" + "=" * 70)
    print("RIEPILOGO")
    print("=" * 70)
    print("""
  D1 (Oro/DoppioOro): vedi sopra
  D2 (Seq PRNG):      vedi sopra
  D3 (Extra|Base):    vedi sopra
  D4 (Lag 288):       vedi sopra
  D5 (Numeri spia):   vedi sopra
    """)


if __name__ == "__main__":
    main()
