"""Motore di convergenza V6 — Lotto Convergent.

Basato su Test 11 (vicinanza pura): la somma era un proxy.
Il filtro vero e' |a-b| <= D con frequenza e ritardo nella finestra.

AMBO SECCO (coppia #1):
  Segnale: freq_rit_fib (W=75)
  Confermato dallo sweep 161 somme: nessuna somma lo batte in stabilita'.
  5-fold CV: media 1.095x, min fold 0.996x.

AMBETTO (coppie #2-4):
  Segnale: vicinanza cross-decina |a-b| <= 20, decine diverse (W=125)
  Scoperta: Test 11 (vicinanza batte somme) + analisi pre-V6 (cross > intra).
  Cross-decina 5-fold CV: media 1.184x, min fold 1.144x — il piu' stabile.
  Coppie al confine tra decine (es. 29-31) dove l'ambetto +-1 e' piu' efficace.

STRATEGIA:
  Coppia #1: EUR 1 ambo + EUR 1 ambetto (freq_rit_fib W=75)
  Coppie #2-4: EUR 1 ambetto (vicinanza |a-b|<=20, W=125)
  Totale: EUR 5/estrazione, EUR 45/ciclo
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist

logger = logging.getLogger(__name__)

FIB_DISTS = {1, 2, 3, 5, 8, 13, 21, 34}

# Configurazione validata
W_AMBO = 75  # freq_rit_fib per ambo secco
W_AMBETTO = 125  # vicinanza pura per ambetto
MAX_DIST = 20  # |a-b| <= 20


@dataclass
class SegnaleV6:
    """Segnale generato dal motore V6."""

    ambo: tuple[int, int]
    ruota: str
    score: float = 0.0
    metodo: str = ""
    tipo_giocata: str = ""
    frequenza: int = 0
    ritardo: int = 0
    dettagli: str = ""


def _features(dati, idx, ruota, finestra):
    """Calcola features nella finestra."""
    pf: Counter = Counter()
    pl: dict = {}
    for back in range(1, finestra + 1):
        bi = idx - back
        if bi < 0:
            break
        _, bw = dati[bi]
        if ruota not in bw:
            continue
        for a, b in combinations(sorted(bw[ruota]), 2):
            pf[(a, b)] += 1
            if (a, b) not in pl:
                pl[(a, b)] = back
    return pf, pl


def segnale_fib(dati, idx, ruota, finestra=W_AMBO, max_n=5):
    """freq_rit_fib: coppia freq>=2, ritardo, distanza Fibonacci.

    Confermato come migliore per ambo secco (sweep 161 somme).
    """
    if idx < finestra:
        return []
    pf, pl = _features(dati, idx, ruota, finestra)
    soglia = finestra // 3
    risultati = []
    for pair, freq in pf.items():
        if freq < 2:
            continue
        a, b = pair
        last = pl.get(pair, finestra)
        if last < soglia:
            continue
        if cyclo_dist(a, b) not in FIB_DISTS:
            continue
        score = freq + last / soglia
        risultati.append((pair, score, freq, last))
    risultati.sort(key=lambda x: -x[1])
    return risultati[:max_n]


def segnale_vicinanza(
    dati,
    idx,
    ruota,
    finestra=W_AMBETTO,
    max_dist=MAX_DIST,
    cross_decina=True,
    max_n=5,
):
    """Vicinanza cross-decina: |a-b| <= D, decine diverse, freq>=1, ritardo.

    Scoperta dal Test 11 + analisi pre-V6:
    - Le coppie vicine ma cross-decina (es. 29-31) battono le intra-decina
    - Cross-decina ratio 1.184x vs intra-decina 1.091x (5-fold CV)
    - Al confine tra decine l'ambetto (+/-1) copre una zona piu' ricca
    """
    if idx < finestra:
        return []
    pf, pl = _features(dati, idx, ruota, finestra)
    soglia = finestra // 3
    risultati = []
    for pair, freq in pf.items():
        if freq < 1:
            continue
        a, b = pair
        if abs(a - b) > max_dist:
            continue
        # Filtro cross-decina: decine diverse
        same_dec = (a - 1) // 10 == (b - 1) // 10
        if cross_decina and same_dec:
            continue
        last = pl.get(pair, finestra)
        if last < soglia:
            continue
        # Score: frequenza + ritardo relativo + bonus vicinanza
        proximity = 1.0 - abs(a - b) / max_dist
        score = freq + last / soglia + proximity
        risultati.append((pair, score, freq, last))
    risultati.sort(key=lambda x: -x[1])
    return risultati[:max_n]


def genera_giocata_v6(
    dati,
    n_ambetti: int = 3,
    ruote: list[str] | None = None,
) -> dict:
    """Genera la giocata completa V6.

    1 coppia ambo secco (freq_rit_fib W=75) +
    N coppie ambetto (vicinanza |a-b|<=20, W=125).
    """
    if not dati:
        return {
            "ambo_secco": None,
            "ambetti": [],
            "costo_estrazione": 0,
            "costo_ciclo": 0,
        }

    idx = len(dati) - 1
    target_ruote = ruote or list(RUOTE)

    # 1. Ambo secco: freq_rit_fib W=75
    best_ambo = None
    for ruota in target_ruote:
        for pair, score, freq, rit in segnale_fib(dati, idx, ruota):
            if best_ambo is None or score > best_ambo.score:
                d = cyclo_dist(pair[0], pair[1])
                best_ambo = SegnaleV6(
                    ambo=pair,
                    ruota=ruota,
                    score=score,
                    metodo="freq_rit_fib",
                    tipo_giocata="ambo_secco",
                    frequenza=freq,
                    ritardo=rit,
                    dettagli=f"W={W_AMBO},f={freq},r={rit},d={d}",
                )

    # 2. Ambetti: vicinanza pura |a-b|<=20, W=125
    tutti_ambetti = []
    for ruota in target_ruote:
        for pair, score, freq, rit in segnale_vicinanza(dati, idx, ruota):
            tutti_ambetti.append(
                SegnaleV6(
                    ambo=pair,
                    ruota=ruota,
                    score=score,
                    metodo="vicinanza",
                    tipo_giocata="ambetto",
                    frequenza=freq,
                    ritardo=rit,
                    dettagli=f"W={W_AMBETTO},f={freq},r={rit},|d|={abs(pair[0] - pair[1])}",
                )
            )

    tutti_ambetti.sort(key=lambda x: -x.score)

    # Evita duplicati con ambo
    ambetti_finali = []
    for s in tutti_ambetti:
        if best_ambo and s.ambo == best_ambo.ambo and s.ruota == best_ambo.ruota:
            continue
        ambetti_finali.append(s)
        if len(ambetti_finali) >= n_ambetti:
            break

    costo = 2 + len(ambetti_finali) if best_ambo else len(ambetti_finali)

    logger.info(
        "V6: 1 ambo (%s) + %d ambetti, EUR %d/estr",
        best_ambo.ruota if best_ambo else "-",
        len(ambetti_finali),
        costo,
    )

    return {
        "ambo_secco": best_ambo,
        "ambetti": ambetti_finali,
        "costo_estrazione": costo,
        "costo_ciclo": costo * 9,
    }


def formatta_giocata(giocata: dict) -> str:
    """Formatta la giocata V6."""
    lines = []
    lines.append("GIOCATA V6 — Vicinanza pura (|a-b|<=20)")
    lines.append("")

    ambo = giocata["ambo_secco"]
    if ambo:
        a, b = ambo.ambo
        lines.append("  AMBO SECCO (EUR 1) + AMBETTO (EUR 1):")
        lines.append(
            f"    {a:>2}-{b:<2} su {ambo.ruota} "
            f"(freq_rit_fib W=75, score={ambo.score:.1f}, {ambo.dettagli})"
        )
        lines.append("    Se esatto: EUR 250 | Se adiacente: EUR 65")
    else:
        lines.append("  Nessun segnale ambo secco disponibile")

    lines.append("")
    lines.append("  AMBETTO (EUR 1 ciascuno) — vicinanza |a-b|<=20, W=125:")
    for i, s in enumerate(giocata["ambetti"], 1):
        a, b = s.ambo
        lines.append(f"    #{i + 1} {a:>2}-{b:<2} su {s.ruota} (score={s.score:.1f}, {s.dettagli})")

    lines.append("")
    ce = giocata["costo_estrazione"]
    cc = giocata["costo_ciclo"]
    lines.append(f"  Costo: EUR {ce}/estrazione, EUR {cc}/ciclo")
    if cc > 0:
        lines.append(f"  Vincita ambetto (EUR 65) copre {65 / cc * 100:.0f}% del ciclo")
        lines.append(f"  Vincita ambo (EUR 250) copre {250 / cc * 100:.0f}% del ciclo")

    return "\n".join(lines)
