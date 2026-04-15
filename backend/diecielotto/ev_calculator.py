"""Motore di calcolo Expected Value per 10eLotto ogni 5 minuti.

Calcola EV, house edge e probabilita per tutte le configurazioni di gioco:
Base, Numero Oro, Doppio Oro, Extra, GONG e relative combinazioni.

Regole: 90 numeri totali, 20 estratti, il giocatore sceglie K numeri (1-10).
Premi gia al netto della ritenuta dell'11%.
"""

from __future__ import annotations

import logging
from math import comb
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tabelle premi (moltiplicatori per 1 euro di posta, netti 11%)
# Struttura: {K_numeri_giocati: {m_indovinati: premio}}
# ---------------------------------------------------------------------------

PREMI_BASE: dict[int, dict[int, float]] = {
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

PREMI_ORO: dict[int, dict[int, float]] = {
    1: {1: 63.00},
    2: {1: 25.00, 2: 70.00},
    3: {1: 15.00, 2: 25.00, 3: 130.00},
    4: {1: 10.00, 2: 15.00, 3: 40.00, 4: 300.00},
    5: {1: 10.00, 2: 14.00, 3: 20.00, 4: 30.00, 5: 300.00},
    6: {1: 10.00, 2: 10.00, 3: 10.00, 4: 20.00, 5: 200.00, 6: 2500.00},
    7: {1: 10.00, 2: 7.00, 3: 7.00, 4: 10.00, 5: 75.00, 6: 750.00, 7: 5000.00},
    8: {1: 8.00, 2: 3.00, 3: 5.00, 4: 10.00, 5: 45.00, 6: 450.00, 7: 2000.00, 8: 30000.00},
    9: {
        1: 5.00,
        2: 3.00,
        3: 5.00,
        4: 10.00,
        5: 25.00,
        6: 80.00,
        7: 800.00,
        8: 5000.00,
        9: 250000.00,
    },
    10: {
        1: 10.00,
        2: 3.00,
        3: 3.00,
        4: 5.00,
        5: 20.00,
        6: 25.00,
        7: 250.00,
        8: 2500.00,
        9: 50000.00,
        10: 2500000.00,
    },
}

PREMI_DOPPIO_ORO: dict[int, dict[int, float]] = {
    2: {2: 250.00},
    3: {2: 75.00, 3: 300.00},
    4: {2: 40.00, 3: 80.00, 4: 800.00},
    5: {2: 25.00, 3: 40.00, 4: 100.00, 5: 1000.00},
    6: {2: 20.00, 3: 25.00, 4: 50.00, 5: 500.00, 6: 6000.00},
    7: {2: 15.00, 3: 25.00, 4: 40.00, 5: 150.00, 6: 1500.00, 7: 15000.00},
    8: {2: 10.00, 3: 15.00, 4: 25.00, 5: 100.00, 6: 1000.00, 7: 5000.00, 8: 100000.00},
    9: {2: 10.00, 3: 15.00, 4: 25.00, 5: 50.00, 6: 200.00, 7: 2000.00, 8: 20000.00, 9: 500000.00},
    10: {
        2: 10.00,
        3: 15.00,
        4: 20.00,
        5: 30.00,
        6: 70.00,
        7: 500.00,
        8: 5000.00,
        9: 100000.00,
        10: 5000000.00,
    },
}

PREMI_EXTRA: dict[int, dict[int, float]] = {
    1: {1: 4.00},
    2: {1: 1.00, 2: 16.00},
    3: {1: 0.00, 2: 4.00, 3: 100.00},
    4: {2: 2.00, 3: 25.00, 4: 225.00},
    5: {2: 2.00, 3: 10.00, 4: 30.00, 5: 300.00},
    6: {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00},
    7: {3: 5.00, 4: 15.00, 5: 75.00, 6: 750.00, 7: 5000.00},
    8: {3: 3.00, 4: 10.00, 5: 45.00, 6: 450.00, 7: 2000.00, 8: 20000.00},
    9: {0: 1.00, 4: 10.00, 5: 20.00, 6: 75.00, 7: 500.00, 8: 5000.00, 9: 250000.00},
    10: {0: 1.00, 4: 6.00, 5: 20.00, 6: 35.00, 7: 250.00, 8: 2000.00, 9: 40000.00, 10: 2000000.00},
}

# GONG: 1 numero su 90, premio = 65x la posta base
GONG_PROB: float = 1.0 / 90.0
GONG_PREMIO: float = 65.0


# ---------------------------------------------------------------------------
# Funzioni di probabilita
# ---------------------------------------------------------------------------


def p_match_base(k: int, m: int) -> float:
    """P(esattamente m match | K giocati, 20 estratti da 90).

    Distribuzione ipergeometrica: C(K,m) * C(90-K, 20-m) / C(90, 20).
    """
    if m < 0 or m > k or m > 20 or (20 - m) > (90 - k):
        return 0.0
    return comb(k, m) * comb(90 - k, 20 - m) / comb(90, 20)


def p_oro_e_m_match(k: int, m: int) -> float:
    """P(Numero Oro centrato AND esattamente m match totali).

    L'Oro e il primo dei 20 estratti. Se e tra i K del giocatore:
    - P(Oro tra i K) = K/90
    - Dati i rimanenti K-1 numeri del giocatore, servono m-1 match
      dai rimanenti 19 estratti su 89 numeri nel pool.
    - P(m-1 match | Oro hit) = C(K-1, m-1) * C(90-K, 20-m) / C(89, 19)
    """
    if k < 1 or m < 1 or m > k or m > 20:
        return 0.0
    if (20 - m) > (90 - k):
        return 0.0
    p_oro_hit = k / 90.0
    # Rimanenti: K-1 numeri giocatore, 19 estratti, pool 89
    p_resto = comb(k - 1, m - 1) * comb(90 - k, 20 - m) / comb(89, 19)
    return p_oro_hit * p_resto


def p_doppio_oro_e_m_match(k: int, m: int) -> float:
    """P(sia Oro che Doppio Oro centrati AND esattamente m match totali).

    - P(entrambi tra i K) = K/90 * (K-1)/89
    - Dati K-2 rimanenti del giocatore, servono m-2 match
      dai rimanenti 18 estratti su 88 nel pool.
    """
    if k < 2 or m < 2 or m > k or m > 20:
        return 0.0
    if (20 - m) > (90 - k):
        return 0.0
    p_entrambi = (k / 90.0) * ((k - 1) / 89.0)
    p_resto = comb(k - 2, m - 2) * comb(90 - k, 20 - m) / comb(88, 18)
    return p_entrambi * p_resto


def p_extra_match(remaining: int, m_extra: int) -> float:
    """P(m_extra match nell'Extra | 'remaining' numeri non matchati vs 15 Extra da 70).

    Dopo l'estrazione principale di 20 numeri, ne vengono estratti altri 15
    dai 70 rimanenti. I numeri 'remaining' = K - m_base del giocatore sono
    nel pool dei 70.
    """
    if remaining < 0 or m_extra < 0:
        return 0.0
    if m_extra > remaining or m_extra > 15:
        return 0.0
    if (15 - m_extra) > (70 - remaining):
        return 0.0
    return comb(remaining, m_extra) * comb(70 - remaining, 15 - m_extra) / comb(70, 15)


# ---------------------------------------------------------------------------
# Calcolo EV per singola opzione
# ---------------------------------------------------------------------------


def calcola_ev_base(k: int) -> dict:
    """Calcola l'EV dell'opzione Base per K numeri giocati.

    Ritorna dizionario con EV, costo, house_edge, dettaglio per m.
    """
    if k < 1 or k > 10:
        raise ValueError(f"K deve essere tra 1 e 10, ricevuto {k}")

    tabella = PREMI_BASE[k]
    breakdown: list[dict] = []
    ev_totale = 0.0
    p_vincita = 0.0

    for m in range(0, k + 1):
        prob = p_match_base(k, m)
        premio = tabella.get(m, 0.0)
        contributo = prob * premio
        ev_totale += contributo
        if premio > 0:
            p_vincita += prob
        breakdown.append(
            {
                "m": m,
                "prob": prob,
                "premio": premio,
                "contributo_ev": contributo,
            }
        )

    costo = 1.0
    house_edge = 1.0 - ev_totale / costo

    logger.debug("EV Base K=%d: EV=%.6f, house_edge=%.4f%%", k, ev_totale, house_edge * 100)

    return {
        "K": k,
        "opzione": "base",
        "costo": costo,
        "ev": ev_totale,
        "ev_per_euro": ev_totale / costo,
        "house_edge": house_edge,
        "p_vincita": p_vincita,
        "breakdown": breakdown,
    }


def calcola_ev_oro(k: int) -> dict:
    """Calcola l'EV aggiuntivo dell'opzione Numero Oro per K numeri.

    Il premio Oro e AGGIUNTIVO rispetto al Base. Costo aggiuntivo: 1 euro.
    """
    if k < 1 or k > 10:
        raise ValueError(f"K deve essere tra 1 e 10, ricevuto {k}")

    tabella = PREMI_ORO[k]
    breakdown: list[dict] = []
    ev_oro = 0.0

    for m in range(1, k + 1):
        prob = p_oro_e_m_match(k, m)
        premio = tabella.get(m, 0.0)
        contributo = prob * premio
        ev_oro += contributo
        if premio > 0:
            breakdown.append(
                {
                    "m": m,
                    "prob": prob,
                    "premio": premio,
                    "contributo_ev": contributo,
                }
            )

    costo_aggiuntivo = 1.0

    return {
        "K": k,
        "opzione": "oro",
        "costo_aggiuntivo": costo_aggiuntivo,
        "ev": ev_oro,
        "breakdown": breakdown,
    }


def calcola_ev_doppio_oro(k: int) -> dict:
    """Calcola l'EV aggiuntivo dell'opzione Doppio Oro per K numeri.

    Richiede K >= 2. Il premio Doppio Oro e AGGIUNTIVO a Base e Oro.
    Costo aggiuntivo: 1 euro (totale 3 con base+oro).
    """
    if k < 2 or k > 10:
        if k == 1:
            return {
                "K": k,
                "opzione": "doppio_oro",
                "costo_aggiuntivo": 1.0,
                "ev": 0.0,
                "breakdown": [],
                "nota": "Doppio Oro non disponibile per K=1",
            }
        raise ValueError(f"K deve essere tra 1 e 10, ricevuto {k}")

    tabella = PREMI_DOPPIO_ORO[k]
    breakdown: list[dict] = []
    ev_doppio = 0.0

    for m in range(2, k + 1):
        prob = p_doppio_oro_e_m_match(k, m)
        premio = tabella.get(m, 0.0)
        contributo = prob * premio
        ev_doppio += contributo
        if premio > 0:
            breakdown.append(
                {
                    "m": m,
                    "prob": prob,
                    "premio": premio,
                    "contributo_ev": contributo,
                }
            )

    return {
        "K": k,
        "opzione": "doppio_oro",
        "costo_aggiuntivo": 1.0,
        "ev": ev_doppio,
        "breakdown": breakdown,
    }


def calcola_ev_extra(k: int) -> dict:
    """Calcola l'EV aggiuntivo dell'opzione Extra per K numeri.

    Dopo i 20 numeri principali, vengono estratti 15 numeri dai 70 rimanenti.
    I numeri non matchati del giocatore (K - m_base) sono verificati contro
    i 15 Extra. Costo aggiuntivo: 1 euro.
    """
    if k < 1 or k > 10:
        raise ValueError(f"K deve essere tra 1 e 10, ricevuto {k}")

    tabella = PREMI_EXTRA[k]
    ev_extra = 0.0
    breakdown: list[dict] = []

    # Per ogni possibile m_base (match nella principale)
    for m_base in range(0, min(k, 20) + 1):
        p_base = p_match_base(k, m_base)
        if p_base < 1e-30:
            continue

        remaining = k - m_base  # numeri non matchati nella principale

        # Per ogni possibile m_extra (match nell'Extra)
        for m_extra in range(0, min(remaining, 15) + 1):
            premio = tabella.get(m_extra, 0.0)
            if premio <= 0:
                continue

            p_ext = p_extra_match(remaining, m_extra)
            if p_ext < 1e-30:
                continue

            contributo = p_base * p_ext * premio
            ev_extra += contributo

    # Riepilogo per m_extra (aggregato su tutti i m_base)
    for m_extra in sorted(tabella.keys()):
        premio = tabella[m_extra]
        if premio <= 0:
            continue
        # Calcola prob marginale di ottenere m_extra match Extra
        p_marginale = 0.0
        for m_base in range(0, min(k, 20) + 1):
            p_base = p_match_base(k, m_base)
            remaining = k - m_base
            p_ext = p_extra_match(remaining, m_extra)
            p_marginale += p_base * p_ext
        breakdown.append(
            {
                "m_extra": m_extra,
                "prob_marginale": p_marginale,
                "premio": premio,
                "contributo_ev": p_marginale * premio,
            }
        )

    return {
        "K": k,
        "opzione": "extra",
        "costo_aggiuntivo": 1.0,
        "ev": ev_extra,
        "breakdown": breakdown,
    }


def calcola_ev_gong() -> dict:
    """Calcola l'EV dell'opzione GONG.

    1 numero su 90, premio 65x la posta. Costo: raddoppia la posta base.
    """
    ev = GONG_PROB * GONG_PREMIO
    return {
        "opzione": "gong",
        "costo_aggiuntivo": 1.0,  # raddoppia la posta base
        "ev": ev,
        "prob": GONG_PROB,
        "premio": GONG_PREMIO,
        "house_edge": 1.0 - ev,
    }


# ---------------------------------------------------------------------------
# Calcolo completo di tutte le configurazioni
# ---------------------------------------------------------------------------


def _crea_config(
    k: int,
    opzione: str,
    costo: float,
    ev: float,
    p_vincita: Optional[float] = None,
) -> dict:
    """Helper per creare un record di configurazione."""
    ev_per_euro = ev / costo if costo > 0 else 0.0
    house_edge = 1.0 - ev_per_euro
    return {
        "K": k,
        "opzione": opzione,
        "costo": costo,
        "ev": ev,
        "ev_per_euro": ev_per_euro,
        "house_edge": house_edge,
        "p_vincita": p_vincita,
        "breakeven": 1.0 / (1.0 - house_edge) if house_edge < 1.0 else float("inf"),
    }


def calcola_ev_completo() -> list[dict]:
    """Calcola EV per tutte le configurazioni possibili.

    Per ogni K da 1 a 10, genera le combinazioni:
    - base
    - base+oro
    - base+oro+doppio_oro (K >= 2)
    - base+extra
    - base+gong
    - base+oro+extra
    - base+oro+doppio_oro+extra (K >= 2)
    - base+oro+gong
    - base+extra+gong
    - base+oro+extra+gong
    - base+oro+doppio_oro+gong (K >= 2)
    - base+oro+doppio_oro+extra+gong (K >= 2)

    Ritorna lista di dizionari ordinata per K e opzione.
    """
    risultati: list[dict] = []
    gong = calcola_ev_gong()
    ev_gong = gong["ev"]

    for k in range(1, 11):
        base = calcola_ev_base(k)
        oro = calcola_ev_oro(k)
        doppio = calcola_ev_doppio_oro(k)
        extra = calcola_ev_extra(k)

        ev_b = base["ev"]
        ev_o = oro["ev"]
        ev_d = doppio["ev"]
        ev_e = extra["ev"]
        p_v = base["p_vincita"]

        # base
        risultati.append(_crea_config(k, "base", 1.0, ev_b, p_v))

        # base+oro
        risultati.append(_crea_config(k, "base+oro", 2.0, ev_b + ev_o))

        # base+oro+doppio_oro (K >= 2)
        if k >= 2:
            risultati.append(_crea_config(k, "base+oro+doppio_oro", 3.0, ev_b + ev_o + ev_d))

        # base+extra
        risultati.append(_crea_config(k, "base+extra", 2.0, ev_b + ev_e))

        # base+gong
        risultati.append(_crea_config(k, "base+gong", 2.0, ev_b + ev_gong))

        # base+oro+extra
        risultati.append(_crea_config(k, "base+oro+extra", 3.0, ev_b + ev_o + ev_e))

        # base+oro+doppio_oro+extra (K >= 2)
        if k >= 2:
            risultati.append(
                _crea_config(k, "base+oro+doppio_oro+extra", 4.0, ev_b + ev_o + ev_d + ev_e)
            )

        # base+oro+gong
        risultati.append(_crea_config(k, "base+oro+gong", 3.0, ev_b + ev_o + ev_gong))

        # base+extra+gong
        risultati.append(_crea_config(k, "base+extra+gong", 3.0, ev_b + ev_e + ev_gong))

        # base+oro+extra+gong
        risultati.append(_crea_config(k, "base+oro+extra+gong", 4.0, ev_b + ev_o + ev_e + ev_gong))

        # base+oro+doppio_oro+gong (K >= 2)
        if k >= 2:
            risultati.append(
                _crea_config(k, "base+oro+doppio_oro+gong", 4.0, ev_b + ev_o + ev_d + ev_gong)
            )

        # base+oro+doppio_oro+extra+gong (K >= 2)
        if k >= 2:
            risultati.append(
                _crea_config(
                    k,
                    "base+oro+doppio_oro+extra+gong",
                    5.0,
                    ev_b + ev_o + ev_d + ev_e + ev_gong,
                )
            )

    return risultati


# ---------------------------------------------------------------------------
# Report formattato
# ---------------------------------------------------------------------------


def formatta_report_ev(report: Optional[list[dict]] = None) -> str:
    """Genera un report formattato con tutte le configurazioni EV.

    Ordina per house_edge crescente (migliore prima) e evidenzia le top 5.
    Mostra il GONG come baseline (27.8% house edge) per confronto.
    """
    if report is None:
        report = calcola_ev_completo()

    # Ordina per house_edge crescente
    ordinato = sorted(report, key=lambda r: r["house_edge"])

    linee: list[str] = []
    linee.append("")
    linee.append("=" * 100)
    linee.append("  10eLOTTO OGNI 5 MINUTI — ANALISI EXPECTED VALUE COMPLETA")
    linee.append("=" * 100)
    linee.append("")

    # GONG baseline
    gong = calcola_ev_gong()
    linee.append(
        f"  GONG baseline: EV = {gong['ev']:.4f}, House Edge = {gong['house_edge'] * 100:.2f}%"
    )
    linee.append("")

    # Header tabella
    header = (
        f"{'#':>3}  {'K':>2}  {'Opzione':<35}  {'Costo':>6}  "
        f"{'EV':>8}  {'EV/EUR':>7}  {'H.Edge':>8}  {'P(win)':>8}"
    )
    linee.append(header)
    linee.append("-" * 100)

    for i, r in enumerate(ordinato):
        marker = " *** " if i < 5 else "     "
        p_win = f"{r['p_vincita'] * 100:.2f}%" if r["p_vincita"] is not None else "  n/a  "
        linea = (
            f"{i + 1:>3}{marker}"
            f"{r['K']:>2}  "
            f"{r['opzione']:<35}  "
            f"{r['costo']:>5.1f}E  "
            f"{r['ev']:>8.4f}  "
            f"{r['ev_per_euro']:>7.4f}  "
            f"{r['house_edge'] * 100:>7.2f}%  "
            f"{p_win:>8}"
        )
        linee.append(linea)

    linee.append("-" * 100)
    linee.append("")

    # Top 5
    linee.append("  TOP 5 CONFIGURAZIONI (house edge piu basso):")
    linee.append("")
    for i, r in enumerate(ordinato[:5]):
        linee.append(
            f"    {i + 1}. K={r['K']:>2} {r['opzione']:<35} "
            f"HE={r['house_edge'] * 100:.2f}%  "
            f"EV/EUR={r['ev_per_euro']:.4f}"
        )

    linee.append("")

    # Peggiori 5
    linee.append("  PEGGIORI 5 CONFIGURAZIONI (house edge piu alto):")
    linee.append("")
    for i, r in enumerate(reversed(ordinato[-5:])):
        linee.append(
            f"    {i + 1}. K={r['K']:>2} {r['opzione']:<35} "
            f"HE={r['house_edge'] * 100:.2f}%  "
            f"EV/EUR={r['ev_per_euro']:.4f}"
        )

    linee.append("")
    linee.append("=" * 100)
    linee.append(
        "  Nota: tutti i premi sono gia al netto della ritenuta 11%. "
        "House Edge > 0 = vantaggio banco."
    )
    linee.append("=" * 100)
    linee.append("")

    return "\n".join(linee)


# ---------------------------------------------------------------------------
# Verifica K=1
# ---------------------------------------------------------------------------


def _verifica_k1() -> None:
    """Verifica che i calcoli per K=1 siano corretti.

    P(1 match) = C(1,1)*C(89,19)/C(90,20) = 20/90 = 2/9 ~ 0.2222
    EV_base = 0.2222 * 3.00 = 0.6667
    House edge = 33.3%
    """
    p1 = p_match_base(1, 1)
    atteso_p1 = 20.0 / 90.0
    assert abs(p1 - atteso_p1) < 1e-10, f"P(1 match, K=1) atteso {atteso_p1}, ottenuto {p1}"

    ev = p1 * 3.00
    atteso_ev = atteso_p1 * 3.00
    assert abs(ev - atteso_ev) < 1e-10, f"EV base K=1 atteso {atteso_ev}, ottenuto {ev}"

    he = 1.0 - ev
    he_atteso = 1.0 - 2.0 / 3.0
    assert abs(he - he_atteso) < 1e-10, f"HE K=1: {he * 100:.2f}%"

    print(f"  Verifica K=1: P(1)={p1:.6f}, EV={ev:.6f}, HE={he * 100:.2f}% -- OK")


# ---------------------------------------------------------------------------
# Entry point standalone
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n--- Verifica calcoli K=1 ---")
    _verifica_k1()

    print("\n--- Dettaglio EV Base per ogni K ---")
    for k in range(1, 11):
        r = calcola_ev_base(k)
        print(
            f"  K={k:>2}: EV={r['ev']:.6f}, "
            f"HE={r['house_edge'] * 100:.2f}%, "
            f"P(win)={r['p_vincita'] * 100:.2f}%"
        )

    print("\n--- Dettaglio EV Oro aggiuntivo per ogni K ---")
    for k in range(1, 11):
        r = calcola_ev_oro(k)
        print(f"  K={k:>2}: EV_oro={r['ev']:.6f}")

    print("\n--- Dettaglio EV Doppio Oro aggiuntivo per ogni K ---")
    for k in range(2, 11):
        r = calcola_ev_doppio_oro(k)
        print(f"  K={k:>2}: EV_doppio_oro={r['ev']:.6f}")

    print("\n--- Dettaglio EV Extra aggiuntivo per ogni K ---")
    for k in range(1, 11):
        r = calcola_ev_extra(k)
        print(f"  K={k:>2}: EV_extra={r['ev']:.6f}")

    print("\n--- GONG ---")
    g = calcola_ev_gong()
    print(f"  EV={g['ev']:.6f}, HE={g['house_edge'] * 100:.2f}%")

    # Report completo
    report = calcola_ev_completo()
    print(formatta_report_ev(report))
