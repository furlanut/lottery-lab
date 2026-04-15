"""10eLotto prediction engine — S4 dual-target strategy (W=100)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

PREMI_BASE_6 = {3: 2.00, 4: 10.00, 5: 100.00, 6: 1000.00}
PREMI_EXTRA_6 = {1: 1.00, 2: 1.00, 3: 7.00, 4: 20.00, 5: 200.00, 6: 2000.00}
COSTO = 2.0
W = 100  # window


@dataclass
class Previsione10eLotto:
    numeri: list[int]
    metodo: str = "S4_dual_target"
    configurazione: int = 6
    costo: float = 2.0
    data_generazione: date = field(default_factory=date.today)
    dettagli: str = ""
    score: float = 0.0


def genera_previsione(session: Optional[object] = None) -> Previsione10eLotto:
    """Genera previsione con S4 dual-target W=100."""
    own = session is None
    if own:
        session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoEstrazione)
                .order_by(DiecieLottoEstrazione.data.desc(), DiecieLottoEstrazione.ora.desc())
                .limit(W)
            )
            .scalars()
            .all()
        )

        if len(rows) < 10:
            return Previsione10eLotto(numeri=[1, 2, 3, 4, 5, 6], dettagli="Dati insufficienti")

        base_freq: Counter = Counter()
        extra_freq: Counter = Counter()
        for r in rows:
            for n in r.numeri:
                base_freq[n] += 1
            for n in r.numeri_extra:
                extra_freq[n] += 1

        hot_base = [n for n, _ in base_freq.most_common(6)]
        hot_extra = [n for n, _ in extra_freq.most_common(20) if n not in hot_base][:3]
        pick = hot_base[:3] + hot_extra[:3]

        if len(pick) < 6:
            for n, _ in base_freq.most_common():
                if n not in pick:
                    pick.append(n)
                if len(pick) >= 6:
                    break

        return Previsione10eLotto(
            numeri=sorted(pick[:6]),
            dettagli=f"S4 dual-target W={W}: 3 hot base + 3 hot extra",
            score=1.103,
        )
    finally:
        if own:
            session.close()


def verifica_previsione(
    previsione: list[int],
    numeri_estratti: list[int],
    numeri_extra: list[int],
) -> dict:
    """Verifica una previsione contro un'estrazione reale."""
    pick = set(previsione)
    drawn = set(numeri_estratti)
    extra = set(numeri_extra)

    match_base = len(pick & drawn)
    remaining = pick - drawn
    match_extra = len(remaining & extra)

    vincita_base = PREMI_BASE_6.get(match_base, 0.0)
    vincita_extra = PREMI_EXTRA_6.get(match_extra, 0.0)
    vincita_totale = vincita_base + vincita_extra

    return {
        "match_base": match_base,
        "match_extra": match_extra,
        "vincita_base": vincita_base,
        "vincita_extra": vincita_extra,
        "vincita_totale": vincita_totale,
        "pnl": vincita_totale - COSTO,
        "numeri_azzeccati_base": sorted(pick & drawn),
        "numeri_azzeccati_extra": sorted(remaining & extra),
    }


def formatta_previsione(prev: Previsione10eLotto) -> str:
    nums = " ".join(f"{n:2d}" for n in prev.numeri)
    return f"10eLotto 6+Extra: [{nums}] ({prev.metodo}, score {prev.score:.3f})"
