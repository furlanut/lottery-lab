"""Filtro Vincolo Differenziale 90.

Per ogni coppia di ruote, verifica se la somma delle distanze
ciclometriche tra coppie di posizioni vale 45.
Se il vincolo e soddisfatto genera candidati ambo tramite
fuori90 e diametrale.
"""
from __future__ import annotations

from itertools import combinations

from lotto_predictor.analyzer.cyclometry import (
    COPPIE_RUOTE,
    cyclo_dist,
    diametrale,
    fuori90,
    is_valid_ambo,
)
from lotto_predictor.analyzer.filters.base import Candidato, FilterBase


class Vincolo90(FilterBase):
    """Vincolo Differenziale 90 — somma distanze ciclometriche = 45."""

    @property
    def nome(self) -> str:
        return "vincolo90"

    def analizza(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
    ) -> list[Candidato]:
        """Analizza l'estrazione corrente cercando vincoli 45 tra coppie di ruote.

        Per ogni coppia di ruote e ogni combinazione di posizioni,
        verifica se d1 + d2 == 45.  In caso affermativo produce
        candidati ambo con fuori90 e diametrale.
        """
        candidati: list[Candidato] = []
        _, estratti = dati[indice_estrazione]

        # Tutte le coppie di posizioni (0-4)
        posizioni = list(range(5))
        coppie_posizioni = list(combinations(posizioni, 2))

        for w1_name, w2_name in COPPIE_RUOTE:
            # Servono entrambe le ruote nell'estrazione
            if w1_name not in estratti or w2_name not in estratti:
                continue

            w1 = estratti[w1_name]
            w2 = estratti[w2_name]

            # Per ogni coppia distinta di coppie-posizione
            for i, (p1, p2) in enumerate(coppie_posizioni):
                for p3, p4 in coppie_posizioni[i + 1:]:
                    d1 = cyclo_dist(w1[p1], w2[p2])
                    d2 = cyclo_dist(w1[p3], w2[p4])

                    if d1 + d2 != 45:
                        continue

                    # Segnale trovato — genera candidati
                    involved_numbers = [w1[p1], w2[p2], w1[p3], w2[p4]]
                    dettaglio = (
                        f"{w1_name}[{p1+1}]={w1[p1]} "
                        f"{w2_name}[{p2+1}]={w2[p2]} d={d1} | "
                        f"{w1_name}[{p3+1}]={w1[p3]} "
                        f"{w2_name}[{p4+1}]={w2[p4]} d={d2}"
                    )

                    for num in involved_numbers:
                        k1 = fuori90(w1[p1] + w2[p2])
                        k2 = diametrale(k1)

                        # Coppia (K1, numero coinvolto)
                        if is_valid_ambo(k1, num):
                            candidati.append(
                                Candidato(
                                    num_a=k1,
                                    num_b=num,
                                    filtro=self.nome,
                                    dettaglio=f"K1={k1} | {dettaglio}",
                                )
                            )

                        # Coppia (K2, numero coinvolto)
                        if is_valid_ambo(k2, num):
                            candidati.append(
                                Candidato(
                                    num_a=k2,
                                    num_b=num,
                                    filtro=self.nome,
                                    dettaglio=f"K2={k2} | {dettaglio}",
                                )
                            )

        return candidati
