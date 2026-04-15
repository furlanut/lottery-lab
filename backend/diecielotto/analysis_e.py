from __future__ import annotations

"""10eLotto — Test E1-E4.

E1: Special Time EV
E2: Portafoglio multi-ticket
E3: Approfondimento distanza Oro-DoppioOro
E4: EV per distribuzione spaziale dei 6 numeri
"""

import logging
import random
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

# Prize tables
PREMI_BASE = {
    1: {1: 3.00},
    2: {2: 14.00},
    3: {2: 2.00, 3: 45.00},
    4: {2: 1.00, 3: 10.00, 4: 90.00},
    5: {2: 1.00, 3: 4.00, 4: 15.00, 5: 140.00},
    6: {3: 2.00, 4: 10.00, 5: 100.00, 6: 1000.00},
    7: {0: 1.00, 4: 4.00, 5: 40.00, 6: 400.00, 7: 1600.00},
    8: {0: 1.00, 5: 20.00, 6: 200.00, 7: 800.00, 8: 10000.00},
    9: {0: 2.00, 5: 10.00, 6: 40.00, 7: 400.00, 8: 2000.00, 9: 100000.00},
    10: {0: 2.00, 5: 5.00, 6: 15.00, 7: 150.00, 8: 1000.00, 9: 20000.00, 10: 1000000.00},
}
PREMI_EXTRA = {
    1: {1: 4.00},
    2: {1: 1.00, 2: 16.00},
    3: {2: 4.00, 3: 100.00},
    4: {2: 2.00, 3: 25.00, 4: 225.00},
    5: {2: 2.00, 3: 10.00, 4: 30.00, 5: 300.00},
    6: {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00},
    7: {3: 5.00, 4: 15.00, 5: 75.00, 6: 750.00, 7: 5000.00},
    8: {3: 3.00, 4: 10.00, 5: 45.00, 6: 450.00, 7: 2000.00, 8: 20000.00},
    9: {0: 1.00, 4: 10.00, 5: 20.00, 6: 75.00, 7: 500.00, 8: 5000.00, 9: 250000.00},
    10: {0: 1.00, 4: 6.00, 5: 20.00, 6: 35.00, 7: 250.00, 8: 2000.00, 9: 40000.00, 10: 2000000.00},
}
PREMI_ORO = {
    1: {1: 63.00},
    2: {1: 25.00, 2: 70.00},
    3: {1: 15.00, 2: 25.00, 3: 130.00},
}

POOL = list(range(1, 91))


def _sim_draw():
    """Simula un'estrazione: 20 da 90, poi 15 Extra dai 70 rimanenti."""
    drawn20 = random.sample(POOL, 20)
    oro = drawn20[0]
    doppio_oro = drawn20[1]
    remaining70 = [x for x in POOL if x not in drawn20]
    extra15 = random.sample(remaining70, 15)
    return set(drawn20), set(extra15), oro, doppio_oro


def _vincita_base(pick: set, drawn: set, k: int) -> float:
    """Vincita base per k numeri giocati."""
    m = len(pick & drawn)
    return PREMI_BASE.get(k, {}).get(m, 0.0)


def _vincita_extra(pick: set, drawn: set, extra: set, k: int) -> float:
    """Vincita Extra per k numeri giocati."""
    remaining = pick - drawn
    me = len(remaining & extra)
    return PREMI_EXTRA.get(k, {}).get(me, 0.0)


def _vincita_oro(pick: set, oro: int, drawn: set, k: int) -> float:
    """Vincita Numero Oro."""
    if oro not in pick:
        return 0.0
    m = len(pick & drawn)
    return PREMI_ORO.get(k, {}).get(m, 0.0)


# ===================================================================
# TEST E1 — Special Time
# ===================================================================


def test_e1():
    print("\n" + "=" * 70)
    print("TEST E1 — SPECIAL TIME EV")
    print("=" * 70)

    # Special Time: dalle 16:05 alle 18:00, premi maggiorati del 30%
    # (fonte: regolamento ADM/Sisal)
    # Non tutti i siti riportano i moltiplicatori esatti.
    # Il bonus standard è +30% su tutti i premi base.
    # NOTA: se il moltiplicatore reale è diverso, l'EV cambia.

    multiplier = 1.30  # bonus Special Time standard

    print(f"\n  Special Time: bonus {(multiplier - 1) * 100:.0f}% sui premi base")
    print("  Orario: 16:05 — 18:00 (~24 estrazioni in 2 ore)")
    print()

    # Calcolo analitico EV per 6+Extra durante Special Time
    ev_base_normal = 0.62495
    ev_extra_normal = 1.17632
    ev_base_special = ev_base_normal * multiplier

    # Scenario A: solo base maggiorata
    ev_total_a = ev_base_special + ev_extra_normal
    he_a = 1 - ev_total_a / 2.0

    # Scenario B: anche Extra maggiorato
    ev_total_b = ev_base_special + ev_extra_normal * multiplier
    he_b = 1 - ev_total_b / 2.0

    # Scenario C: moltiplicatore 50% (alcune fonti dicono così)
    mult_c = 1.50
    ev_total_c = ev_base_normal * mult_c + ev_extra_normal
    he_c = 1 - ev_total_c / 2.0

    print(f"  {'Scenario':<35}  {'EV':>8}  {'HE':>8}  {'Breakeven':>10}")
    print("  " + "-" * 65)
    print(
        f"  {'Normale (no bonus)':<35}  {ev_base_normal + ev_extra_normal:>8.4f}  "
        f"{(1 - (ev_base_normal + ev_extra_normal) / 2) * 100:>7.2f}%  {'1.11x':>10}"
    )
    print(
        f"  {'Special +30% solo base':<35}  {ev_total_a:>8.4f}  "
        f"{he_a * 100:>7.2f}%  {1 / (ev_total_a / 2):>10.4f}x"
    )
    print(
        f"  {'Special +30% base+extra':<35}  {ev_total_b:>8.4f}  "
        f"{he_b * 100:>7.2f}%  {1 / (ev_total_b / 2):>10.4f}x"
    )
    print(
        f"  {'Special +50% solo base':<35}  {ev_total_c:>8.4f}  "
        f"{he_c * 100:>7.2f}%  {1 / (ev_total_c / 2):>10.4f}x"
    )

    if ev_total_b > 2.0:
        print("\n  *** Se Special +30% si applica anche all'Extra: EV > COSTO! ***")
        print(f"  *** Profitto: EUR {ev_total_b - 2:.4f}/giocata ***")

    # Verifica con dati reali: le estrazioni Special Time hanno premi diversi?
    print("\n  NOTA: il calcolo sopra è analitico. Per conferma serve il")
    print("  regolamento ufficiale ADM sul bonus Special Time.")
    print("  Il bonus potrebbe essere +30% o +50% e applicarsi solo al base.")


# ===================================================================
# TEST E2 — Portafoglio multi-ticket
# ===================================================================


def test_e2():
    print("\n" + "=" * 70)
    print("TEST E2 — PORTAFOGLIO MULTI-TICKET")
    print("=" * 70)

    n_sim = 1_000_000
    random.seed(42)

    results = {}

    # --- Scenario 0: Baseline — singolo 6+Extra (€2) ---
    log.info("E2 Scenario 0: baseline 6+Extra...")
    total_0 = 0.0
    wins_0 = 0
    for _ in range(n_sim):
        pick = set(random.sample(POOL, 6))
        drawn, extra, oro, doro = _sim_draw()
        v = _vincita_base(pick, drawn, 6) + _vincita_extra(pick, drawn, extra, 6)
        total_0 += v
        if v > 0:
            wins_0 += 1
    results["0_baseline"] = {
        "costo": 2.0,
        "ev": total_0 / n_sim,
        "p_win": wins_0 / n_sim,
    }

    # --- Scenario 1 (€4): 6+Extra + 1 Oro (sovrapposti) ---
    log.info("E2 Scenario 1: 6+Extra + 1 Oro sovrapposto...")
    total_1 = 0.0
    wins_1 = 0
    for _ in range(n_sim):
        pick6 = set(random.sample(POOL, 6))
        pick1 = {list(pick6)[0]}  # primo dei 6
        drawn, extra, oro, doro = _sim_draw()
        v_6base = _vincita_base(pick6, drawn, 6)
        v_6extra = _vincita_extra(pick6, drawn, extra, 6)
        v_1oro = _vincita_oro(pick1, oro, drawn, 1)
        v = v_6base + v_6extra + v_1oro
        total_1 += v
        if v > 0:
            wins_1 += 1
    results["1_6extra_1oro_overlap"] = {
        "costo": 4.0,
        "ev": total_1 / n_sim,
        "p_win": wins_1 / n_sim,
    }

    # --- Scenario 2 (€5): 6+Extra + 3 base + 1 Oro (sovrapposti) ---
    log.info("E2 Scenario 2: 6+Extra + 3 base + 1 Oro...")
    total_2 = 0.0
    wins_2 = 0
    for _ in range(n_sim):
        pick6 = list(random.sample(POOL, 6))
        pick3 = set(pick6[:3])
        pick1 = {pick6[0]}
        pick6s = set(pick6)
        drawn, extra, oro, doro = _sim_draw()
        v = (
            _vincita_base(pick6s, drawn, 6)
            + _vincita_extra(pick6s, drawn, extra, 6)
            + _vincita_base(pick3, drawn, 3)
            + _vincita_oro(pick1, oro, drawn, 1)
        )
        total_2 += v
        if v > 0:
            wins_2 += 1
    results["2_6extra_3base_1oro"] = {
        "costo": 5.0,
        "ev": total_2 / n_sim,
        "p_win": wins_2 / n_sim,
    }

    # --- Scenario 3 (€4): 6+Extra + 1 Oro (diverso, NON sovrapposto) ---
    log.info("E2 Scenario 3: 6+Extra + 1 Oro indipendente...")
    total_3 = 0.0
    wins_3 = 0
    for _ in range(n_sim):
        all7 = random.sample(POOL, 7)
        pick6 = set(all7[:6])
        pick1 = {all7[6]}  # numero diverso dai 6
        drawn, extra, oro, doro = _sim_draw()
        v = (
            _vincita_base(pick6, drawn, 6)
            + _vincita_extra(pick6, drawn, extra, 6)
            + _vincita_oro(pick1, oro, drawn, 1)
        )
        total_3 += v
        if v > 0:
            wins_3 += 1
    results["3_6extra_1oro_indep"] = {
        "costo": 4.0,
        "ev": total_3 / n_sim,
        "p_win": wins_3 / n_sim,
    }

    # --- Scenario 4 (€4): due schedine 6+Extra indipendenti (2 estrazioni) ---
    # Per confronto: stessa spesa ma su 2 estrazioni diverse
    log.info("E2 Scenario 4: 2x 6+Extra su 2 estrazioni diverse...")
    total_4 = 0.0
    wins_4 = 0
    for _ in range(n_sim):
        # Estrazione 1
        pick_a = set(random.sample(POOL, 6))
        drawn_a, extra_a, _, _ = _sim_draw()
        va = _vincita_base(pick_a, drawn_a, 6) + _vincita_extra(pick_a, drawn_a, extra_a, 6)
        # Estrazione 2
        pick_b = set(random.sample(POOL, 6))
        drawn_b, extra_b, _, _ = _sim_draw()
        vb = _vincita_base(pick_b, drawn_b, 6) + _vincita_extra(pick_b, drawn_b, extra_b, 6)
        v = va + vb
        total_4 += v
        if v > 0:
            wins_4 += 1
    results["4_2x6extra_2draws"] = {
        "costo": 4.0,
        "ev": total_4 / n_sim,
        "p_win": wins_4 / n_sim,
    }

    # Print results
    print(f"\n  Simulazioni: {n_sim:,}")
    print(f"\n  {'Scenario':<35}  {'Costo':>6}  {'EV':>8}  {'EV/EUR':>7}  {'HE':>8}  {'P(win)':>8}")
    print("  " + "-" * 75)

    for name, r in results.items():
        ev_eur = r["ev"] / r["costo"]
        he = (1 - ev_eur) * 100
        print(
            f"  {name:<35}  {r['costo']:>6.2f}  {r['ev']:>8.4f}  "
            f"{ev_eur:>7.4f}  {he:>7.2f}%  {r['p_win'] * 100:>7.2f}%"
        )

    # Best
    best = min(results.items(), key=lambda x: 1 - x[1]["ev"] / x[1]["costo"])
    print(f"\n  Miglior portafoglio: {best[0]}")
    print(
        f"  EV/EUR = {best[1]['ev'] / best[1]['costo']:.4f} "
        f"(HE = {(1 - best[1]['ev'] / best[1]['costo']) * 100:.2f}%)"
    )


# ===================================================================
# TEST E3 — Approfondimento distanza Oro-DoppioOro
# ===================================================================


def test_e3():
    print("\n" + "=" * 70)
    print("TEST E3 — DISTANZA ORO-DOPPIOORO (approfondimento z=3.08)")
    print("=" * 70)

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
        estrazioni = [{"oro": r.numero_oro, "doppio_oro": r.doppio_oro} for r in rows]
    finally:
        session.close()

    n = len(estrazioni)
    half = n // 2

    # E3.1: Split temporale
    dist_all = [abs(e["oro"] - e["doppio_oro"]) for e in estrazioni]
    dist_1h = dist_all[:half]
    dist_2h = dist_all[half:]
    expected = (90 * 90 - 1) / (3 * 90)  # 29.996

    for label, dists in [("Tutto", dist_all), ("1a meta", dist_1h), ("2a meta", dist_2h)]:
        m = sum(dists) / len(dists)
        se = sqrt(sum((d - m) ** 2 for d in dists) / len(dists)) / sqrt(len(dists))
        z = (m - expected) / se if se > 0 else 0
        print(f"  {label:<10}: media={m:.3f}, attesa={expected:.3f}, z={z:.2f}, n={len(dists)}")

    # E3.2: Autocorrelazione della distanza
    mean_d = sum(dist_all) / n
    var_d = sum((x - mean_d) ** 2 for x in dist_all) / n
    print("\n  Autocorrelazione distanza |Oro-DoppioOro|:")
    for lag in [1, 2, 5, 10, 50, 288]:
        if lag >= n:
            continue
        cov = sum((dist_all[i] - mean_d) * (dist_all[i + lag] - mean_d) for i in range(n - lag)) / (
            n - lag
        )
        ac = cov / var_d if var_d > 0 else 0
        z = ac * sqrt(n - lag)
        sig = "***" if abs(z) > 3.0 else ""
        print(f"    lag {lag:>4}: r={ac:+.5f}  z={z:+.2f} {sig}")

    # E3.3: Istogramma distanze (bin di 5)
    print("\n  Distribuzione distanze |Oro-DoppioOro| (bin=5):")
    bins = Counter(d // 5 for d in dist_all)
    # Atteso per distribuzione triangolare: P(|X-Y|=d) = 2*(90-d)/(90*89)
    for b in range(18):
        low = b * 5
        high = b * 5 + 4
        obs = sum(bins.get(low // 5 + i, 0) for i in range(1)) if b < 18 else 0
        obs = bins.get(b, 0)
        # Expected count for this bin
        exp = sum(2 * (90 - d) / (90 * 89) for d in range(low, min(high + 1, 90))) * n
        ratio = obs / exp if exp > 0 else 0
        bar = "#" * int(obs / n * 500)
        print(f"    [{low:>2}-{high:>2}]: obs={obs:>5}  exp={exp:>7.0f}  ratio={ratio:.3f}  {bar}")

    # E3.4: Sfruttabilità
    print("\n  Sfruttabilità con Doppio Oro:")
    # Se la distanza media è 30.35 vs 29.99, il bias è +0.35 (1.2%)
    bias_pct = (sum(dist_all) / n - expected) / expected * 100
    print(f"    Bias distanza: {bias_pct:+.2f}%")
    print("    Effetto su P(DoppioOro hit): trascurabile")
    print("    P(DoppioOro) = K*(K-1)/(90*89) indipendentemente dalla distanza")
    print("    Il bias nella distanza NON cambia la probabilità di vincita")
    print("    → NON sfruttabile")


# ===================================================================
# TEST E4 — EV per distribuzione spaziale
# ===================================================================


def test_e4():
    print("\n" + "=" * 70)
    print("TEST E4 — EV PER DISTRIBUZIONE SPAZIALE DEI 6 NUMERI")
    print("=" * 70)

    n_sim = 1_000_000
    random.seed(42)

    configs = {
        "consecutivi_42_47": [42, 43, 44, 45, 46, 47],
        "sparsi_equidist": [5, 20, 35, 50, 65, 80],
        "tutti_bassi_1_6": [1, 2, 3, 4, 5, 6],
        "tutti_alti_85_90": [85, 86, 87, 88, 89, 90],
        "decine_miste": [5, 15, 25, 35, 45, 55],
        "random_medio": None,  # random ogni volta
    }

    print(f"\n  Simulazioni: {n_sim:,} per configurazione")
    print(
        f"\n  {'Config':<22}  {'EV base':>8}  {'EV extra':>9}  "
        f"{'EV tot':>8}  {'EV/EUR':>7}  {'HE':>8}"
    )
    print("  " + "-" * 70)

    for name, fixed_nums in configs.items():
        ev_base_tot = 0.0
        ev_extra_tot = 0.0

        for _ in range(n_sim):
            pick = set(random.sample(POOL, 6)) if fixed_nums is None else set(fixed_nums)

            drawn, extra, _, _ = _sim_draw()
            vb = _vincita_base(pick, drawn, 6)
            ve = _vincita_extra(pick, drawn, extra, 6)
            ev_base_tot += vb
            ev_extra_tot += ve

        ev_b = ev_base_tot / n_sim
        ev_e = ev_extra_tot / n_sim
        ev_t = ev_b + ev_e
        ev_eur = ev_t / 2.0
        he = (1 - ev_eur) * 100
        print(
            f"  {name:<22}  {ev_b:>8.4f}  {ev_e:>9.4f}  {ev_t:>8.4f}  {ev_eur:>7.4f}  {he:>7.2f}%"
        )

    print("\n  Se tutti gli EV sono ~1.80: la distribuzione spaziale NON conta.")
    print("  L'ipergeometrica è invariante per permutazione del pool.")


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 70)
    print("10eLOTTO — TEST E1-E4 (angoli inesplorati)")
    print("=" * 70)

    test_e1()
    test_e2()
    test_e3()
    test_e4()

    print("\n" + "=" * 70)
    print("RIEPILOGO FINALE")
    print("=" * 70)
    print("""
  E1 Special Time: potenziale riduzione HE se bonus applicato a Extra
  E2 Multi-ticket: confronto portafogli
  E3 Oro-DoppioOro: stabilita' del z=3.08
  E4 Spaziale: invarianza EV per distribuzione numeri
    """)


if __name__ == "__main__":
    main()
