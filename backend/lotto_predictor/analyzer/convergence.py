"""Motore di convergenza — Lotto Convergent.

Combina i 5 filtri indipendenti e assegna un punteggio di convergenza
(0-5) a ciascun ambo candidato. Piu filtri convergono sullo stesso
ambo, piu forte e il segnale.

Score:
  0-2: rumore, NON giocare
  3: segnale moderato
  4-5: segnale forte, priorita massima
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from lotto_predictor.analyzer.cyclometry import RUOTE, cyclo_dist, decade, is_valid_ambo
from lotto_predictor.analyzer.filters.base import Candidato


@dataclass
class SegnaleConvergente:
    """Un ambo con punteggio di convergenza.

    Attributes:
        ambo: coppia ordinata (min, max)
        score: punteggio convergenza (0-5)
        filtri: lista dei filtri che hanno generato il segnale
        dettagli: informazioni aggiuntive per ogni filtro
        ruota: ruota target
    """
    ambo: tuple[int, int]
    score: int
    filtri: list[str] = field(default_factory=list)
    dettagli: list[str] = field(default_factory=list)
    ruota: str = ""


def calcola_convergenza(
    dati: list[tuple[str, dict[str, list[int]]]],
    indice_estrazione: int,
    ruota: str,
    min_score: int = 2,
    soglia_ritardo: int = 150,
    soglia_ritardo_diametrale: int = 15,
) -> list[SegnaleConvergente]:
    """Combina tutti i filtri e calcola il punteggio di convergenza.

    Per ogni coppia candidata, conta quanti filtri indipendenti la supportano.

    Args:
        dati: lista di tuple (data, {ruota: [n1..n5]})
        indice_estrazione: indice dell'estrazione corrente
        ruota: ruota target
        min_score: punteggio minimo per includere nei risultati
        soglia_ritardo: soglia per il filtro ritardo critico
        soglia_ritardo_diametrale: soglia per il filtro somma 91

    Returns:
        Lista di SegnaleConvergente ordinata per score decrescente (max 10)
    """
    # Importa i filtri qui per evitare import circolari
    from lotto_predictor.analyzer.filters.vincolo90 import Vincolo90
    from lotto_predictor.analyzer.filters.isotopismo import Isotopismo
    from lotto_predictor.analyzer.filters.somma91 import Somma91

    # Passo 1: raccolta candidati dai filtri generativi
    all_pairs = defaultdict(lambda: {"score": 0, "filtri": [], "dettagli": []})

    # Filtro 1: Vincolo Differenziale 90
    f_v90 = Vincolo90()
    candidati_v90 = f_v90.analizza(dati, indice_estrazione, ruota)
    for c in candidati_v90:
        pair = c.coppia
        if not is_valid_ambo(pair[0], pair[1]):
            continue
        if "vincolo90" not in all_pairs[pair]["filtri"]:
            all_pairs[pair]["score"] += 1
            all_pairs[pair]["filtri"].append("vincolo90")
            all_pairs[pair]["dettagli"].append(c.dettaglio)

    # Filtro 2: Isotopismo
    f_iso = Isotopismo()
    candidati_iso = f_iso.analizza(dati, indice_estrazione, ruota)
    for c in candidati_iso:
        pair = c.coppia
        if not is_valid_ambo(pair[0], pair[1]):
            continue
        if "isotopismo" not in all_pairs[pair]["filtri"]:
            all_pairs[pair]["score"] += 1
            all_pairs[pair]["filtri"].append("isotopismo")
            all_pairs[pair]["dettagli"].append(c.dettaglio)

    # Filtro 5: Somma 91
    f_s91 = Somma91(soglia_ritardo=soglia_ritardo_diametrale)
    candidati_s91 = f_s91.analizza(dati, indice_estrazione, ruota)
    for c in candidati_s91:
        pair = c.coppia
        if not is_valid_ambo(pair[0], pair[1]):
            continue
        if "somma91" not in all_pairs[pair]["filtri"]:
            all_pairs[pair]["score"] += 1
            all_pairs[pair]["filtri"].append("somma91")
            all_pairs[pair]["dettagli"].append(c.dettaglio)

    # Passo 2: applica filtri di punteggio a tutti i candidati
    for pair, info in all_pairs.items():
        # Filtro 4: coerenza di decina
        if decade(pair[0]) == decade(pair[1]):
            info["score"] += 1
            info["filtri"].append("decade")

        # Filtro 3: ritardo critico
        ritardo = _calcola_ritardo(dati, indice_estrazione, ruota, pair)
        if ritardo >= soglia_ritardo:
            info["score"] += 1
            info["filtri"].append(f"ritardo({ritardo})")

    # Passo 3: filtra per punteggio minimo e costruisci i risultati
    risultati = []
    for pair, info in all_pairs.items():
        if info["score"] >= min_score:
            risultati.append(SegnaleConvergente(
                ambo=pair,
                score=info["score"],
                filtri=info["filtri"],
                dettagli=info["dettagli"],
                ruota=ruota,
            ))

    # Ordina per score decrescente, prendi i primi 10
    risultati.sort(key=lambda x: -x.score)
    return risultati[:10]


def _calcola_ritardo(
    dati: list[tuple[str, dict[str, list[int]]]],
    indice_estrazione: int,
    ruota: str,
    coppia: tuple[int, int],
    max_lookback: int = 500,
) -> int:
    """Calcola il ritardo corrente di un ambo su una ruota.

    Args:
        dati: dati storici
        indice_estrazione: indice corrente
        ruota: ruota target
        coppia: coppia di numeri (a, b)
        max_lookback: massimo numero di estrazioni da controllare

    Returns:
        Numero di estrazioni consecutive senza la coppia
    """
    ritardo = 0
    for back in range(1, min(indice_estrazione + 1, max_lookback)):
        idx = indice_estrazione - back
        if idx < 0:
            break
        _, wheels = dati[idx]
        if ruota in wheels:
            nums_set = set(wheels[ruota])
            if coppia[0] in nums_set and coppia[1] in nums_set:
                break
            ritardo += 1
    return ritardo
