"""Filtro Coerenza Decina.

Filtro di scoring: assegna un punteggio ai candidati in base
alla coerenza di decina tra i due numeri dell'ambo.
- Stessa decina:           1.0
- Distanza ciclometrica <= 10: 0.5
- Altrimenti:              0.0
"""

from __future__ import annotations

from lotto_predictor.analyzer.cyclometry import cyclo_dist, decade
from lotto_predictor.analyzer.filters.base import Candidato, FilterBase


class CoerenzaDecina(FilterBase):
    """Coerenza Decina — punteggio basato sulla vicinanza di decina."""

    @property
    def nome(self) -> str:
        return "decade"

    # ------------------------------------------------------------------
    # Metodo pubblico di scoring
    # ------------------------------------------------------------------

    def punteggio(self, candidati: list[Candidato]) -> list[Candidato]:
        """Assegna un peso ai candidati in base alla coerenza di decina.

        Regole:
        - Stessa decina  -> peso 1.0
        - Distanza <= 10 -> peso 0.5
        - Altrimenti     -> peso 0.0 (candidato scartato)
        """
        scored: list[Candidato] = []

        for cand in candidati:
            score = self._calcola_score(cand.num_a, cand.num_b)
            if score > 0.0:
                scored.append(
                    Candidato(
                        num_a=cand.num_a,
                        num_b=cand.num_b,
                        filtro=self.nome,
                        dettaglio=(
                            f"dec_a={decade(cand.num_a)} "
                            f"dec_b={decade(cand.num_b)} "
                            f"dist={cyclo_dist(cand.num_a, cand.num_b)} "
                            f"score={score} origine={cand.filtro}"
                        ),
                        peso=score,
                    )
                )

        return scored

    # ------------------------------------------------------------------
    # analizza: interfaccia base (non genera candidati propri)
    # ------------------------------------------------------------------

    def analizza(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
    ) -> list[Candidato]:
        """Non genera candidati — questo filtro e solo di scoring.

        Usare il metodo `punteggio()` passando candidati esistenti.
        """
        return []

    # ------------------------------------------------------------------
    # Utilita interne
    # ------------------------------------------------------------------

    @staticmethod
    def _calcola_score(a: int, b: int) -> float:
        """Calcola il punteggio di coerenza tra due numeri.

        Stessa decina = 1.0, distanza <= 10 = 0.5, altrimenti 0.0.
        """
        if decade(a) == decade(b):
            return 1.0
        if cyclo_dist(a, b) <= 10:
            return 0.5
        return 0.0
