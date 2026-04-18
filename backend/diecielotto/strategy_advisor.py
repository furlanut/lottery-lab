"""Strategy Advisor — consiglia strategie di gioco ottimali per obiettivi diversi.

Nessuna strategia supera il breakeven (HE 9.94%), ma:
- Max P(vincita qualsiasi ≥1€): ~73%, invariante fra strategie
- Max P(vincita ≥10€): Vicinanza W=100 (2.82%)
- Max P(vincita ≥100€): Spalmati random/hot-per-decina (~0.25%)

Special Time (16:05-18:00) riduce HE da 9.94% a 6.30% → +4 pp EV.
"""

# ruff: noqa: E501, S311
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from math import comb
from zoneinfo import ZoneInfo

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA
from diecielotto.models.database import DiecieLottoEstrazione

ROME = ZoneInfo("Europe/Rome")
K = 6
W = 100
COSTO = 2.0


# =====================================================================
# Strategie (pick generators)
# =====================================================================


def _pick_vicinanza(window: list) -> list[int]:
    freq = Counter(n for e in window for n in e.numeri)
    seed = freq.most_common(1)[0][0] if freq else 1
    nearby = sorted(
        [(n, freq.get(n, 0)) for n in range(1, 91)
         if abs(n - seed) <= 5 and n != seed and freq.get(n, 0) > 0],
        key=lambda x: -x[1],
    )
    pick = [seed]
    for n, _ in nearby:
        pick.append(n)
        if len(pick) >= K:
            break
    if len(pick) < K:
        for n, _ in freq.most_common():
            if n not in pick:
                pick.append(n)
            if len(pick) >= K:
                break
    return sorted(pick[:K])


def _pick_spread_hot(window: list) -> list[int]:
    """Top freq per ciascuna delle prime 6 decine (1-10, 11-20, ..., 51-60)."""
    freq = Counter(n for e in window for n in e.numeri)
    pick = []
    for lo in [1, 11, 21, 31, 41, 51]:
        hi = lo + 9
        candidates = sorted(
            [(n, freq.get(n, 0)) for n in range(lo, hi + 1)],
            key=lambda x: -x[1],
        )
        pick.append(candidates[0][0])
    return sorted(pick)


def _pick_hot(window: list) -> list[int]:
    freq = Counter(n for e in window for n in e.numeri)
    return sorted([n for n, _ in freq.most_common(K)])


# =====================================================================
# EV Analitico per un pick custom
# =====================================================================


def ev_analitico(pick: list[int]) -> dict:
    """EV analitico per un pick di K=6 numeri giocati con Extra. Ipergeometrica.

    Non dipende dai NUMERI specifici, solo da K (per RNG uniforme).
    Ma ritorniamo la distribuzione completa per chiarezza.
    """
    n_pool = 90
    n_drawn = 20
    k = len(pick)
    total = comb(n_pool, n_drawn)
    p_base = {}
    ev_base = 0.0
    for m in range(k + 1):
        p = comb(k, m) * comb(n_pool - k, n_drawn - m) / total
        p_base[m] = p
        ev_base += p * PREMI_BASE.get(k, {}).get(m, 0.0)

    # Extra: 15 da 70 rimanenti
    c70_15 = comb(70, 15)
    p_extra = {}
    ev_extra = 0.0
    for mb in range(k + 1):
        pb = p_base[mb]
        rem = k - mb
        for me in range(rem + 1):
            pool_rem = 70 - rem
            if pool_rem < (15 - me):
                continue
            p_e = comb(rem, me) * comb(pool_rem, 15 - me) / c70_15
            joint = pb * p_e
            ev_extra += joint * PREMI_EXTRA.get(k, {}).get(me, 0.0)
            p_extra[me] = p_extra.get(me, 0) + joint

    ev_tot = ev_base + ev_extra
    costo = 2.0
    he = (1 - ev_tot / costo) * 100
    be = costo / ev_tot

    return {
        "ev_base": round(ev_base, 4),
        "ev_extra": round(ev_extra, 4),
        "ev_totale": round(ev_tot, 4),
        "house_edge": round(he, 3),
        "breakeven": round(be, 4),
        "p_base": {str(m): round(p, 6) for m, p in p_base.items()},
        "p_win_qualsiasi": round(sum(p for m, p in p_base.items() if m >= 3) +
                                sum(p for m, p in p_extra.items() if m >= 1), 4),
    }


# =====================================================================
# Special Time helpers
# =====================================================================


def _next_special_time(now: datetime) -> datetime:
    """Prossima finestra Special Time: 16:05-18:00 ora italiana."""
    today_start = now.replace(hour=16, minute=5, second=0, microsecond=0)
    today_end = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if now < today_start:
        return today_start
    if now < today_end:
        return now  # dentro la finestra
    # dopo 18:00 -> domani 16:05
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=16, minute=5, second=0, microsecond=0)


def _is_in_special_time(now: datetime) -> bool:
    start = now.replace(hour=16, minute=5, second=0, microsecond=0)
    end = now.replace(hour=18, minute=0, second=0, microsecond=0)
    return start <= now < end


# =====================================================================
# Main status endpoint
# =====================================================================


def get_status() -> dict:
    """Ritorna lo stato completo per la Strategy Advisor."""
    s = get_session()
    try:
        # Ultime 100 estrazioni
        rows = (
            s.execute(
                select(DiecieLottoEstrazione)
                .order_by(DiecieLottoEstrazione.data.desc(), DiecieLottoEstrazione.ora.desc())
                .limit(W)
            )
            .scalars()
            .all()
        )
        window = list(reversed(rows))  # cronologico ascendente

        # Hot numbers (top 20)
        freq = Counter()
        for e in window:
            for n in e.numeri:
                freq[n] += 1
        expected = W * 20 / 90  # ~22.2 per numero
        hot_numbers = []
        for n, f in freq.most_common(20):
            deviazione = f - expected
            hot_numbers.append({
                "numero": n,
                "frequenza": f,
                "attesa": round(expected, 1),
                "deviazione": round(deviazione, 1),
            })

        # Cold numbers (bottom 20)
        cold_list = sorted(range(1, 91), key=lambda x: freq.get(x, 0))[:20]
        cold_numbers = [
            {"numero": n, "frequenza": freq.get(n, 0), "attesa": round(expected, 1),
             "deviazione": round(freq.get(n, 0) - expected, 1)}
            for n in cold_list
        ]

        # Le 3 strategie consigliate
        pick_vicinanza = _pick_vicinanza(window)
        pick_spread = _pick_spread_hot(window)
        pick_hot_only = _pick_hot(window)

        # Time info
        now = datetime.now(ROME)
        next_st = _next_special_time(now)
        in_st = _is_in_special_time(now)
        seconds_to_st = int((next_st - now).total_seconds()) if not in_st else 0

        # EV analitico (stesso per qualsiasi pick di 6 numeri distinti)
        ev_info = ev_analitico(pick_vicinanza)

        # Last extraction info
        last_extr = rows[0] if rows else None
        last_info = None
        if last_extr:
            last_info = {
                "data": str(last_extr.data),
                "ora": last_extr.ora.strftime("%H:%M"),
                "numeri": last_extr.numeri,
                "numero_oro": last_extr.numero_oro,
                "numeri_extra": last_extr.numeri_extra,
            }

        return {
            "dataset": {
                "finestra_estrazioni": len(window),
                "W": W,
                "ultima_estrazione": last_info,
                "totale_db": s.scalar(select(DiecieLottoEstrazione.id).order_by(
                    DiecieLottoEstrazione.id.desc()).limit(1)),
            },
            "hot_numbers": hot_numbers,
            "cold_numbers": cold_numbers,
            "strategies": [
                {
                    "id": "vicinanza",
                    "label": "Vicinanza W=100",
                    "obiettivo": "Max P(vincita ≥10€)",
                    "desc": "6 numeri vicini (±5) al seed piu frequente, filtrati per frequenza recente.",
                    "numeri": pick_vicinanza,
                    "p_win_any_osservata": 73.18,
                    "p_win_10plus_osservata": 2.82,
                    "p_win_100plus_osservata": 0.245,
                    "ratio_backtest": 1.059,
                    "note": "Miglior ratio osservato su 34.744 giocate. Non supera breakeven 1.11x.",
                },
                {
                    "id": "spread_hot",
                    "label": "Spalmati Hot per Decina",
                    "obiettivo": "Max P(vincita ≥100€) + Bilanciamento",
                    "desc": "1 numero piu frequente da ciascuna delle prime 6 decine (1-10, 11-20, ... 51-60).",
                    "numeri": pick_spread,
                    "p_win_any_osservata": 73.26,
                    "p_win_10plus_osservata": 2.70,
                    "p_win_100plus_osservata": 0.231,
                    "ratio_backtest": 1.049,
                    "note": "Distribuito sul wheel, riduce la varianza. Adatto se preferisci vittorie piccole piu frequenti.",
                },
                {
                    "id": "hot",
                    "label": "Hot Numbers",
                    "obiettivo": "Nessun obiettivo specifico (NON consigliato)",
                    "desc": "Top 6 numeri piu frequenti in W=100. Strategia intuitiva ma peggiore in backtest.",
                    "numeri": pick_hot_only,
                    "p_win_any_osservata": 73.44,
                    "p_win_10plus_osservata": 2.53,
                    "p_win_100plus_osservata": 0.165,
                    "ratio_backtest": 0.930,
                    "note": "Piu concentrata sui top → varianza piu bassa → meno big wins. Sotto baseline.",
                },
            ],
            "special_time": {
                "in_corso": in_st,
                "prossima_start_iso": next_st.isoformat(),
                "secondi_a_inizio": seconds_to_st,
                "he_normale": 9.94,
                "he_special_time": 6.30,
                "vantaggio_pp": 3.64,
            },
            "ev_analitico": ev_info,
            "invarianti": {
                "p_vincita_qualsiasi_media": 73.5,
                "note_invariante": "P(vincere almeno 1€) è ~73.5% per QUALSIASI scelta dei 6 numeri. Non si può ottimizzare.",
                "he_base": 9.94,
                "breakeven_base": 1.11,
            },
        }
    finally:
        s.close()


def simulate_custom_pick(numeri: list[int], limit_backtest: int = 1000) -> dict:
    """Simula un pick custom: EV analitico + backtest su ultime N estrazioni.

    Args:
        numeri: lista di 6 numeri distinti 1-90
        limit_backtest: quante estrazioni usare per il backtest osservato
    """
    if len(numeri) != K:
        return {"error": f"Servono esattamente {K} numeri, ricevuti {len(numeri)}"}
    if len(set(numeri)) != K:
        return {"error": "I numeri devono essere distinti"}
    if not all(1 <= n <= 90 for n in numeri):
        return {"error": "Numeri devono essere fra 1 e 90"}

    pick = set(numeri)

    # Analitico
    ev = ev_analitico(sorted(numeri))

    # Backtest sulle ultime N estrazioni
    s = get_session()
    try:
        rows = (
            s.execute(
                select(DiecieLottoEstrazione)
                .order_by(DiecieLottoEstrazione.data.desc(), DiecieLottoEstrazione.ora.desc())
                .limit(limit_backtest)
            )
            .scalars()
            .all()
        )

        pb = PREMI_BASE.get(K, {})
        pe = PREMI_EXTRA.get(K, {})
        giocate = len(rows)
        vinte_1 = vinte_10 = vinte_100 = 0
        tot_vinto = 0.0
        match_dist: dict[int, int] = {}
        for r in rows:
            drawn = set(r.numeri)
            extra = set(r.numeri_extra)
            mb = len(pick & drawn)
            me = len((pick - drawn) & extra)
            v = pb.get(mb, 0) + pe.get(me, 0)
            tot_vinto += v
            if v >= 1:
                vinte_1 += 1
            if v >= 10:
                vinte_10 += 1
            if v >= 100:
                vinte_100 += 1
            match_dist[mb] = match_dist.get(mb, 0) + 1

        pnl = tot_vinto - giocate * COSTO
        roi = pnl / (giocate * COSTO) * 100 if giocate else 0
        ratio = (tot_vinto / giocate) / 1.80 if giocate else 0

        return {
            "input": {
                "numeri": sorted(numeri),
                "costo": COSTO,
            },
            "ev_analitico": ev,
            "backtest": {
                "estrazioni_testate": giocate,
                "vincite_1plus": vinte_1,
                "vincite_10plus": vinte_10,
                "vincite_100plus": vinte_100,
                "p_1plus_oss": round(vinte_1 / giocate * 100, 2) if giocate else 0,
                "p_10plus_oss": round(vinte_10 / giocate * 100, 3) if giocate else 0,
                "p_100plus_oss": round(vinte_100 / giocate * 100, 4) if giocate else 0,
                "totale_vinto": round(tot_vinto, 2),
                "totale_giocato": giocate * COSTO,
                "pnl": round(pnl, 2),
                "roi": round(roi, 2),
                "ratio_vs_ev": round(ratio, 4),
                "match_base_dist": match_dist,
            },
        }
    finally:
        s.close()
