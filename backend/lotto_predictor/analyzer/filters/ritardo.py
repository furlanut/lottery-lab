"""Filtro Ritardo Critico.

Filtro di scoring: prende candidati esistenti e assegna un peso
in base al ritardo (numero di estrazioni dall'ultima apparizione
della coppia sulla ruota target).
Piu alto il ritardo, piu alto il peso.
"""

from __future__ import annotations

from lotto_predictor.analyzer.filters.base import Candidato, FilterBase

# Soglia minima di ritardo per assegnare punteggio
_DEFAULT_THRESHOLD = 150


class RitardoCritico(FilterBase):
    """Ritardo Critico — punteggio basato sul ritardo dell'ambo."""

    def __init__(self, soglia: int = _DEFAULT_THRESHOLD) -> None:
        self._soglia = soglia

    @property
    def nome(self) -> str:
        return "ritardo"

    # ------------------------------------------------------------------
    # Metodo pubblico di scoring (non genera candidati propri)
    # ------------------------------------------------------------------

    def punteggio(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
        candidati: list[Candidato],
    ) -> list[Candidato]:
        """Assegna un peso ai candidati in base al ritardo.

        Scorre le estrazioni a ritroso sulla ruota target.
        Se entrambi i numeri della coppia compaiono nella stessa
        estrazione, quello e l'ultimo sorteggio della coppia.
        Il ritardo e il numero di estrazioni trascorse da allora.

        Se ritardo >= soglia il candidato riceve peso proporzionale.
        """
        scored: list[Candidato] = []

        for cand in candidati:
            delay = self._calcola_ritardo(dati, indice_estrazione, ruota, cand.num_a, cand.num_b)

            if delay >= self._soglia:
                # Peso normalizzato: ritardo / soglia (minimo 1.0)
                weight = delay / self._soglia
                scored.append(
                    Candidato(
                        num_a=cand.num_a,
                        num_b=cand.num_b,
                        filtro=self.nome,
                        dettaglio=(f"ritardo={delay} soglia={self._soglia} origine={cand.filtro}"),
                        peso=weight,
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
    def _calcola_ritardo(
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
        num_a: int,
        num_b: int,
    ) -> int:
        """Calcola quante estrazioni sono passate dall'ultima uscita della coppia.

        Cerca a ritroso dalla estrazione corrente (esclusa) se entrambi
        i numeri compaiono tra i 5 estratti della ruota.
        """
        delay = 0
        for idx in range(indice_estrazione - 1, -1, -1):
            _, estratti = dati[idx]
            if ruota not in estratti:
                delay += 1
                continue

            numeri = set(estratti[ruota])
            if num_a in numeri and num_b in numeri:
                return delay

            delay += 1

        # Mai uscita: ritardo massimo
        return delay
