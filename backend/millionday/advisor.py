"""MillionDay Strategy Advisor — dedicato a MillionDay.

Basato sui risultati del window sweep W=1..300 × 12 algoritmi (Appendice L).
Espone le 6 configurazioni "piu performanti" nel Regime B (post giugno 2024),
inclusa spread_fasce W=24 che ha catturato un jackpot 5/5 da 1M€ nel backtest.

IMPORTANTE: queste strategie hanno ratio robust elevati MA:
- Nessuna sopravvive a Bonferroni (p_min=0.001 vs soglia 0.00001)
- Il pattern 2024-06+ potrebbe essere fluttuazione o cambio RNG non confermato
- Servono altri 1.500+ estrazioni per validare

L'advisor espone numeri LIVE calcolati sulle ultime estrazioni nel DB.
"""

# ruff: noqa: E501, S311, N803, N806
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from math import comb
from zoneinfo import ZoneInfo

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from millionday.models.database import MillionDayEstrazione

ROME = ZoneInfo("Europe/Rome")
K = 5
N_POOL = 55

# Payout netti ADM
PREMI_BASE = {0: 0.0, 1: 0.0, 2: 2.0, 3: 50.0, 4: 1000.0, 5: 1_000_000.0}
PREMI_EXTRA = {0: 0.0, 1: 0.0, 2: 4.0, 3: 100.0, 4: 1000.0, 5: 100_000.0}
COSTO_TOTALE = 2.0
EV_TEORICO = 1.3262  # HE 33.69%, breakeven 1.508x

# Orari estrazioni MillionDay
ORARI_ESTRAZIONE = [(13, 0), (20, 30)]


# =====================================================================
# PICK GENERATORS (6 strategie)
# =====================================================================


def _pick_cold_plus_hotex(window: list, K: int = 5) -> list[int]:
    """3 cold base + 2 hot extra disgiunti."""
    freq_b = Counter()
    freq_e = Counter()
    for e in window:
        for n in e.numeri:
            freq_b[n] += 1
        for n in e.numeri_extra:
            freq_e[n] += 1

    # 3 cold base: 3 numeri con frequenza minima nel base
    cb = sorted(range(1, N_POOL + 1), key=lambda x: (freq_b.get(x, 0), x))[:3]
    # 2 hot extra escludendo cb
    extra_candidates = [n for n, _ in freq_e.most_common() if n not in cb]
    he = extra_candidates[:2]
    # Se extra_freq vuoto, completa con piu frequenti base
    if len(he) < 2:
        for n, _ in freq_b.most_common():
            if n not in cb and n not in he:
                he.append(n)
                if len(he) >= 2:
                    break
    pick = cb + he
    while len(pick) < K:
        # Pad
        for n in range(1, N_POOL + 1):
            if n not in pick:
                pick.append(n)
                break
    return sorted(pick[:K])


def _pick_dual_3b2e(window: list, K: int = 5) -> list[int]:
    """3 hot base + 2 hot extra disgiunti."""
    freq_b = Counter()
    freq_e = Counter()
    for e in window:
        for n in e.numeri:
            freq_b[n] += 1
        for n in e.numeri_extra:
            freq_e[n] += 1

    hb = [n for n, _ in freq_b.most_common(3)]
    extra_candidates = [n for n, _ in freq_e.most_common() if n not in hb]
    he = extra_candidates[:2]
    if len(he) < 2:
        for n, _ in freq_b.most_common():
            if n not in hb and n not in he:
                he.append(n)
                if len(he) >= 2:
                    break
    pick = hb + he
    while len(pick) < K:
        for n in range(1, N_POOL + 1):
            if n not in pick:
                pick.append(n)
                break
    return sorted(pick[:K])


def _pick_spread_fasce(window: list, K: int = 5) -> list[int]:
    """1 hot per ciascuna delle 5 fasce: 1-11, 12-22, 23-33, 34-44, 45-55."""
    freq_b = Counter()
    for e in window:
        for n in e.numeri:
            freq_b[n] += 1
    fasce = [(1, 11), (12, 22), (23, 33), (34, 44), (45, 55)]
    pick = []
    for lo, hi in fasce:
        candidates = sorted(
            [(n, freq_b.get(n, 0)) for n in range(lo, hi + 1)],
            key=lambda x: (-x[1], x[0]),
        )
        pick.append(candidates[0][0])
    return sorted(pick)


# =====================================================================
# Strategie configurate
# =====================================================================


STRATEGIES = [
    {
        "id": "cold_plus_hotex_W66",
        "label": "Cold Base + Hot Extra — W=66",
        "subtitle": "Best ratio robust",
        "window_size": 66,
        "pick_fn": _pick_cold_plus_hotex,
        "obiettivo": "Max ratio val robust su dataset completo",
        "desc": "3 numeri piu freddi nel base (+1 mese) + 2 numeri piu caldi nell'Extra. Scommette su ritardo base e momento extra.",
        "ratio_val_robust": 3.249,
        "ratio_disc_robust": 1.127,
        "p_value": 0.004,
        "big_wins_val": 2,
        "regime_b_ratio_avg": 2.40,
        "regime_b_bucket_sopra_be": "9/11",
        "note": "Top config del sweep. Buona performance da 2024-06 in poi, negativa prima. Selection bias NON escluso.",
        "colore": "amber",
    },
    {
        "id": "cold_plus_hotex_W67",
        "label": "Cold Base + Hot Extra — W=67",
        "subtitle": "Quasi-equivalente a W=66",
        "window_size": 67,
        "pick_fn": _pick_cold_plus_hotex,
        "obiettivo": "Conferma robustezza di W~66",
        "desc": "Stessa strategia di W=66 ma con finestra +1. Usa solo se vuoi un 'ensemble' che smorza la sensibilita alla finestra.",
        "ratio_val_robust": 2.972,
        "ratio_disc_robust": 0.946,
        "p_value": 0.001,
        "big_wins_val": 2,
        "regime_b_ratio_avg": 2.40,
        "regime_b_bucket_sopra_be": "9/11",
        "note": "Migliore p-value raw (0.001) ma ancora lontano da Bonferroni (0.00001).",
        "colore": "amber",
    },
    {
        "id": "dual_3b2e_W103",
        "label": "Dual 3 Base + 2 Extra — W=103",
        "subtitle": "Dual hot bilanciato",
        "window_size": 103,
        "pick_fn": _pick_dual_3b2e,
        "obiettivo": "Scommette su momentum in entrambi i pool",
        "desc": "3 numeri piu caldi nel base + 2 numeri piu caldi nell'Extra (disgiunti). Finestra ~7 settimane, equilibrio fra breve e lungo.",
        "ratio_val_robust": 2.957,
        "ratio_disc_robust": 1.275,
        "p_value": 0.0075,
        "big_wins_val": 3,
        "regime_b_ratio_avg": 2.2,
        "regime_b_bucket_sopra_be": "8/11",
        "note": "Piu big wins dei cold (3 vs 2). Coerenza disc/val migliore.",
        "colore": "blue",
    },
    {
        "id": "dual_3b2e_W104",
        "label": "Dual 3 Base + 2 Extra — W=104",
        "subtitle": "Micro-variazione di W=103",
        "window_size": 104,
        "pick_fn": _pick_dual_3b2e,
        "obiettivo": "Conferma stabilita di W=103",
        "desc": "Idem W=103 con finestra +1. Simile performance, indica robustezza del pattern.",
        "ratio_val_robust": 2.953,
        "ratio_disc_robust": 1.508,
        "p_value": 0.005,
        "big_wins_val": 3,
        "regime_b_ratio_avg": 2.2,
        "regime_b_bucket_sopra_be": "8/11",
        "note": "La coerenza disc (1.508) e molto migliore delle cold_plus_hotex. Piu affidabile come 'segnale'.",
        "colore": "blue",
    },
    {
        "id": "spread_fasce_W40",
        "label": "Spread Fasce — W=40",
        "subtitle": "1 hot per ciascuna fascia",
        "window_size": 40,
        "pick_fn": _pick_spread_fasce,
        "obiettivo": "Distribuzione bilanciata sul wheel",
        "desc": "1 numero piu caldo nelle 5 fasce (1-11, 12-22, 23-33, 34-44, 45-55). Cattura il 'leader' di ogni zona dell'urna.",
        "ratio_val_robust": 2.957,
        "ratio_disc_robust": 1.035,
        "p_value": 0.019,
        "big_wins_val": 2,
        "regime_b_ratio_avg": 2.3,
        "regime_b_bucket_sopra_be": "7/11",
        "note": "Finestra corta (20 giorni). Buon compromesso fra reattivita e stabilita.",
        "colore": "green",
    },
    {
        "id": "spread_fasce_W24",
        "label": "Spread Fasce — W=24 ⚡ JACKPOT SEEKER",
        "subtitle": "Ha preso un 5/5 da 1M€",
        "window_size": 24,
        "pick_fn": _pick_spread_fasce,
        "obiettivo": "High-variance: piu probabile big win singolo",
        "desc": "Stessa strategia Spread Fasce ma con finestra brevissima (~12 giorni). Cattura il momentum piu recente. Nel backtest ha azzeccato un 5/5 da 1.000.000€ — pura fortuna o pattern reale?",
        "ratio_val_robust": 1.600,
        "ratio_disc_robust": 0.577,
        "p_value": 0.003,
        "big_wins_val": 1,
        "regime_b_ratio_avg": 1.8,
        "regime_b_bucket_sopra_be": "5/11",
        "note": "⚡ Con cap a 500€ il ratio si riduce a 1.60x. Senza cap era 58.4x (jackpot 5/5 catturato). Finestra piu 'nervosa' — segnali rumorosi. Gioca solo se cerchi volatilita massima.",
        "colore": "red",
    },
]


# =====================================================================
# Special Time (per MillionDay non esiste, ma countdown prossima estrazione)
# =====================================================================


def _prossima_estrazione(now: datetime) -> tuple[datetime, str]:
    """Calcola la prossima estrazione MillionDay (13:00 o 20:30)."""
    today = now.replace(second=0, microsecond=0)
    for h, m in ORARI_ESTRAZIONE:
        candidate = today.replace(hour=h, minute=m)
        if candidate > now:
            return candidate, f"{h:02d}:{m:02d}"
    # Oltre 20:30 → domani 13:00
    tomorrow = (now + timedelta(days=1)).replace(hour=13, minute=0, second=0, microsecond=0)
    return tomorrow, "13:00"


# =====================================================================
# EV analitico MillionDay (costo 2€ base+Extra)
# =====================================================================


def ev_analitico_md() -> dict:
    """EV analitico per MillionDay K=5+Extra (costo 2€)."""
    c55_5 = comb(55, 5)
    c50_5 = comb(50, 5)

    # Base
    p_base = {}
    ev_base = 0.0
    for m in range(6):
        p = comb(5, m) * comb(50, 5 - m) / c55_5
        p_base[m] = p
        ev_base += p * PREMI_BASE[m]

    # Extra: dai 50 rimanenti, 5 estratti
    ev_extra = 0.0
    p_ext = {}
    for mb in range(6):
        rem = 5 - mb
        pool_rem = 50 - rem
        for me in range(rem + 1):
            if pool_rem < (5 - me):
                continue
            p_e = comb(rem, me) * comb(pool_rem, 5 - me) / c50_5
            joint = p_base[mb] * p_e
            ev_extra += joint * PREMI_EXTRA[me]
            p_ext[me] = p_ext.get(me, 0) + joint

    ev_tot = ev_base + ev_extra
    return {
        "ev_base": round(ev_base, 6),
        "ev_extra": round(ev_extra, 6),
        "ev_totale": round(ev_tot, 4),
        "house_edge": round((1 - ev_tot / COSTO_TOTALE) * 100, 2),
        "breakeven": round(COSTO_TOTALE / ev_tot, 4),
    }


# =====================================================================
# Main get_status
# =====================================================================


def get_status() -> dict:
    """Ritorna lo status completo del MillionDay Strategy Advisor."""
    s = get_session()
    try:
        # Per ogni strategia serve finestra diversa. Carichiamo tutte le ultime 300
        # (abbastanza per il W massimo 104 o 67 delle nostre strategie + margine).
        max_w = max(strat["window_size"] for strat in STRATEGIES)
        rows = (
            s.execute(
                select(MillionDayEstrazione)
                .order_by(MillionDayEstrazione.data.desc(), MillionDayEstrazione.ora.desc())
                .limit(max_w + 10)
            )
            .scalars()
            .all()
        )
        window_all = list(reversed(rows))  # cronologico ascendente
        total_db = s.scalar(select(MillionDayEstrazione.id).order_by(
            MillionDayEstrazione.id.desc()).limit(1)) or 0

        # Hot/cold numbers (finestra 100 per visualizzazione)
        hot_window_size = min(100, len(window_all))
        hot_window = window_all[-hot_window_size:]
        freq = Counter()
        freq_extra = Counter()
        for e in hot_window:
            for n in e.numeri:
                freq[n] += 1
            for n in e.numeri_extra:
                freq_extra[n] += 1

        expected = hot_window_size * 5 / 55  # ~9
        hot_numbers = []
        for n, f in freq.most_common(15):
            hot_numbers.append({
                "numero": n,
                "frequenza": f,
                "attesa": round(expected, 1),
                "deviazione": round(f - expected, 1),
            })

        cold_list = sorted(range(1, 56), key=lambda x: (freq.get(x, 0), x))[:15]
        cold_numbers = [
            {"numero": n, "frequenza": freq.get(n, 0), "attesa": round(expected, 1),
             "deviazione": round(freq.get(n, 0) - expected, 1)}
            for n in cold_list
        ]

        # Calcola le 6 strategie LIVE sui dati attuali
        strategies_with_picks = []
        for strat in STRATEGIES:
            W = strat["window_size"]
            if len(window_all) < W:
                pick = []
            else:
                win_for_strat = window_all[-W:]
                pick = strat["pick_fn"](win_for_strat, K)

            strategies_with_picks.append({
                "id": strat["id"],
                "label": strat["label"],
                "subtitle": strat["subtitle"],
                "window_size": W,
                "obiettivo": strat["obiettivo"],
                "desc": strat["desc"],
                "numeri": pick,
                "ratio_val_robust": strat["ratio_val_robust"],
                "ratio_disc_robust": strat["ratio_disc_robust"],
                "p_value": strat["p_value"],
                "big_wins_val": strat["big_wins_val"],
                "regime_b_ratio_avg": strat["regime_b_ratio_avg"],
                "regime_b_bucket_sopra_be": strat["regime_b_bucket_sopra_be"],
                "note": strat["note"],
                "colore": strat["colore"],
            })

        # Info prossima estrazione
        now = datetime.now(ROME)
        next_dt, next_ora = _prossima_estrazione(now)
        seconds_to_next = int((next_dt - now).total_seconds())

        # Ultima estrazione
        last = rows[0] if rows else None
        last_info = None
        if last:
            last_info = {
                "data": str(last.data),
                "ora": last.ora.strftime("%H:%M"),
                "numeri": last.numeri,
                "extra": last.numeri_extra,
            }

        # EV analitico
        ev = ev_analitico_md()

        return {
            "dataset": {
                "finestra_visualizzazione": hot_window_size,
                "totale_db": total_db,
                "ultima_estrazione": last_info,
            },
            "hot_numbers": hot_numbers,
            "cold_numbers": cold_numbers,
            "strategies": strategies_with_picks,
            "prossima_estrazione": {
                "iso": next_dt.isoformat(),
                "ora": next_ora,
                "secondi_a_estrazione": seconds_to_next,
                "frequenza_giorno": 2,
                "orari": ["13:00", "20:30"],
            },
            "ev_analitico": ev,
            "avvertimenti": {
                "multiple_testing": "Le 6 strategie provengono da uno sweep di 3.600 configurazioni. Nessuna sopravvive a Bonferroni (p_min=0.001 vs soglia 0.00001).",
                "regime_bifase": "Il pattern 2024-06+ potrebbe essere non-stazionarieta RNG, varianza, o selection bias. Non distinguibili con N=2.607.",
                "he_reale": "HE analitico: 33.69%. Qualsiasi strategia ha EV atteso negativo. Gioca solo con budget di intrattenimento.",
            },
        }
    finally:
        s.close()
