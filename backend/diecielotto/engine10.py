from __future__ import annotations

"""10eLotto engine per 10 numeri + Extra.

Strategia: top 10 numeri piu frequenti nelle ultime W=100 estrazioni.
HE: 34.29% (peggiore del 6+Extra ma piu numeri in gioco).
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from lotto_predictor.models.database import get_session
from sqlalchemy import select

from diecielotto.models.database import DiecieLottoEstrazione

PREMI_BASE_10 = {
    0: 2.00,
    5: 5.00,
    6: 15.00,
    7: 150.00,
    8: 1000.00,
    9: 20000.00,
    10: 1000000.00,
}
PREMI_EXTRA_10 = {
    0: 1.00,
    4: 6.00,
    5: 20.00,
    6: 35.00,
    7: 250.00,
    8: 2000.00,
    9: 40000.00,
    10: 2000000.00,
}
COSTO = 2.0
W = 100


@dataclass
class Previsione10Numeri:
    """Previsione 10eLotto con 10 numeri."""

    numeri: list[int] = field(default_factory=list)
    metodo: str = "top10_freq"
    configurazione: int = 10
    costo: float = 2.0
    data_generazione: date = field(default_factory=date.today)
    dettagli: str = ""
    score: float = 0.0


def genera_previsione_10(session=None) -> Previsione10Numeri:
    """Genera previsione con top 10 numeri frequenti in ultime W estrazioni."""
    own = session is None
    if own:
        session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoEstrazione)
                .order_by(
                    DiecieLottoEstrazione.data.desc(),
                    DiecieLottoEstrazione.ora.desc(),
                )
                .limit(W)
            )
            .scalars()
            .all()
        )

        if len(rows) < 10:
            return Previsione10Numeri(numeri=list(range(1, 11)), dettagli="Dati insufficienti")

        freq = Counter()
        for r in rows:
            for n in r.numeri:
                freq[n] += 1

        top10 = sorted([n for n, _ in freq.most_common(10)])

        return Previsione10Numeri(
            numeri=top10,
            dettagli=f"Top 10 frequenti W={W}",
            score=0.657,
        )
    finally:
        if own:
            session.close()


def verifica_previsione_10(
    previsione: list[int],
    numeri_estratti: list[int],
    numeri_extra: list[int],
) -> dict:
    """Verifica previsione 10 numeri contro estrazione reale."""
    pick = set(previsione)
    drawn = set(numeri_estratti)
    extra = set(numeri_extra)

    mb = len(pick & drawn)
    remaining = pick - drawn
    me = len(remaining & extra)

    vb = PREMI_BASE_10.get(mb, 0.0)
    ve = PREMI_EXTRA_10.get(me, 0.0)
    vincita = vb + ve

    return {
        "match_base": mb,
        "match_extra": me,
        "vincita_base": vb,
        "vincita_extra": ve,
        "vincita_totale": vincita,
        "pnl": vincita - COSTO,
        "numeri_azzeccati": sorted(pick & drawn),
        "numeri_azzeccati_extra": sorted(remaining & extra),
    }
