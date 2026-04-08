"""Motore di convergenza V4 — Lotto Convergent.

Segnali separati per ambo secco e ambetto, ognuno con la sua
finestra ottimale validata con fold scorrevole e 5-fold CV.

AMBO SECCO (coppia #1):
  Segnale: freq_rit_fib (W=75)
  Coppia uscita >=2 volte, in ritardo, distanza Fibonacci
  Ratio: 1.159x, 30% finestre sopra breakeven

AMBETTO (coppie #2-5):
  Segnale: somma72 (W=150)
  Coppia con somma 72, frequente e in ritardo
  Ratio: 1.239x (media), min fold 1.178x — il piu' stabile

STRATEGIA:
  Coppia #1: EUR 1 ambo secco + EUR 1 ambetto (freq_rit_fib)
  Coppie #2-4: EUR 1 ambetto ciascuna (somma72)
  Totale: EUR 5 per estrazione, EUR 45 per ciclo (9 estrazioni)
  Vincita ambetto (EUR 65) copre 1.44 cicli
  Vincita ambo (EUR 250) copre 5.5 cicli
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist

logger = logging.getLogger(__name__)

FIB_DISTS = {1, 2, 3, 5, 8, 13, 21, 34}

# Finestre ottimali validate (fold scorrevole + 5-fold CV)
W_AMBO_FIB = 75  # freq_rit_fib per ambo secco
W_AMBETTO_S72 = 150  # somma72 per ambetto
W_AMBETTO_FIB = 125  # freq_rit_fib per ambetto (backup)


@dataclass
class SegnaleV4:
    """Segnale generato dal motore V4."""

    ambo: tuple[int, int]
    ruota: str
    score: float = 0.0
    metodo: str = ""
    tipo_giocata: str = ""  # "ambo_secco" o "ambetto"
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


def _segnali_fib(dati, idx, ruota, finestra, max_n=5):
    """freq_rit_fib: coppia freq>=2, ritardo, distanza Fibonacci."""
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


def _segnali_s72(dati, idx, ruota, finestra, max_n=5):
    """somma72: coppia con somma 72, frequente, in ritardo."""
    if idx < finestra:
        return []
    pf, pl = _features(dati, idx, ruota, finestra)
    soglia = finestra // 3
    risultati = []
    for pair, freq in pf.items():
        if freq < 1:
            continue
        a, b = pair
        if a + b != 72:
            continue
        last = pl.get(pair, finestra)
        if last < soglia:
            continue
        score = freq + last / soglia
        risultati.append((pair, score, freq, last))
    risultati.sort(key=lambda x: -x[1])
    return risultati[:max_n]


def genera_giocata_v4(
    dati,
    n_ambetti: int = 3,
    ruote: list[str] | None = None,
) -> dict:
    """Genera la giocata completa V4.

    Produce:
    - 1 coppia per ambo secco (freq_rit_fib, W=75)
    - N coppie per ambetto (somma72, W=150)

    Args:
        dati: dati storici (data, {ruota: [n1..n5]})
        n_ambetti: numero di coppie ambetto (default 3, max 4)
        ruote: lista ruote (default: tutte)

    Returns:
        dict con 'ambo_secco' (1 coppia) e 'ambetti' (N coppie),
        'costo_estrazione', 'costo_ciclo'
    """
    if not dati:
        return {"ambo_secco": None, "ambetti": [], "costo_estrazione": 0, "costo_ciclo": 0}

    idx = len(dati) - 1
    target_ruote = ruote or list(RUOTE)

    # 1. Trova la migliore coppia per AMBO SECCO (freq_rit_fib, W=75)
    best_ambo = None
    for ruota in target_ruote:
        segnali = _segnali_fib(dati, idx, ruota, W_AMBO_FIB, max_n=1)
        for pair, score, freq, rit in segnali:
            if best_ambo is None or score > best_ambo.score:
                best_ambo = SegnaleV4(
                    ambo=pair,
                    ruota=ruota,
                    score=score,
                    metodo="freq_rit_fib",
                    tipo_giocata="ambo_secco",
                    frequenza=freq,
                    ritardo=rit,
                    dettagli=f"W={W_AMBO_FIB},f={freq},r={rit},d={cyclo_dist(pair[0], pair[1])}",
                )

    # 2. Trova le migliori coppie per AMBETTO (somma72, W=150)
    tutti_ambetti = []
    for ruota in target_ruote:
        segnali = _segnali_s72(dati, idx, ruota, W_AMBETTO_S72, max_n=3)
        for pair, score, freq, rit in segnali:
            tutti_ambetti.append(
                SegnaleV4(
                    ambo=pair,
                    ruota=ruota,
                    score=score,
                    metodo="somma72",
                    tipo_giocata="ambetto",
                    frequenza=freq,
                    ritardo=rit,
                    dettagli=f"W={W_AMBETTO_S72},freq={freq},rit={rit},somma=72",
                )
            )

    tutti_ambetti.sort(key=lambda x: -x.score)

    # Evita di mettere la stessa coppia dell'ambo anche negli ambetti
    ambetti_finali = []
    for s in tutti_ambetti:
        if best_ambo and s.ambo == best_ambo.ambo and s.ruota == best_ambo.ruota:
            continue
        ambetti_finali.append(s)
        if len(ambetti_finali) >= n_ambetti:
            break

    # Costi
    # Coppia #1: EUR 1 ambo + EUR 1 ambetto = EUR 2
    # Coppie #2-N: EUR 1 ambetto ciascuna
    costo = 2 + len(ambetti_finali) if best_ambo else len(ambetti_finali)

    logger.info(
        "V4: 1 ambo (%s) + %d ambetti, costo EUR %d/estrazione",
        best_ambo.ruota if best_ambo else "nessuno",
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
    """Formatta la giocata V4 per output."""
    lines = []
    lines.append("GIOCATA V4 — Segnali separati ambo/ambetto")
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
    lines.append("  AMBETTO (EUR 1 ciascuno):")
    for i, s in enumerate(giocata["ambetti"], 1):
        a, b = s.ambo
        lines.append(
            f"    #{i + 1} {a:>2}-{b:<2} su {s.ruota} "
            f"(somma72 W=150, score={s.score:.1f}, {s.dettagli})"
        )

    lines.append("")
    ce = giocata["costo_estrazione"]
    cc = giocata["costo_ciclo"]
    lines.append(f"  Costo: EUR {ce}/estrazione, EUR {cc}/ciclo")
    lines.append(f"  Vincita ambetto (EUR 65) copre {65 / cc * 100:.0f}% del ciclo")
    if cc > 0:
        lines.append(f"  Vincita ambo (EUR 250) copre {250 / cc * 100:.0f}% del ciclo")

    return "\n".join(lines)
