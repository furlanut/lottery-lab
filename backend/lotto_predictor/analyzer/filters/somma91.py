"""Filtro Somma 91 — Diametrali Caldi.

Per ogni numero estratto sulla ruota, calcola il diametrale
(complemento a 91).  Se il diametrale ha un ritardo >= 15
sulla stessa ruota, genera la coppia (numero, diametrale)
come candidato ambo.
"""

from __future__ import annotations

from lotto_predictor.analyzer.cyclometry import diametrale, is_valid_ambo
from lotto_predictor.analyzer.filters.base import Candidato, FilterBase

# Soglia minima di ritardo del diametrale per generare segnale
_DEFAULT_DELAY_THRESHOLD = 15


class Somma91(FilterBase):
    """Somma 91 — segnala diametrali in ritardo."""

    def __init__(self, soglia_ritardo: int = _DEFAULT_DELAY_THRESHOLD) -> None:
        self._soglia_ritardo = soglia_ritardo

    @property
    def nome(self) -> str:
        return "somma91"

    def analizza(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
    ) -> list[Candidato]:
        """Genera candidati per numeri il cui diametrale e in ritardo.

        Scorre i 5 numeri estratti sulla ruota target.
        Per ciascuno calcola il diametrale e ne misura il ritardo
        (quante estrazioni consecutive non compare sulla stessa ruota).
        Se il ritardo supera la soglia, genera il candidato ambo.
        """
        candidati: list[Candidato] = []

        _, estratti = dati[indice_estrazione]
        if ruota not in estratti:
            return candidati

        numeri = estratti[ruota]

        for num in numeri:
            diam = diametrale(num)

            if not is_valid_ambo(num, diam):
                continue

            delay = self._ritardo_numero(dati, indice_estrazione, ruota, diam)

            if delay >= self._soglia_ritardo:
                candidati.append(
                    Candidato(
                        num_a=num,
                        num_b=diam,
                        filtro=self.nome,
                        dettaglio=(
                            f"num={num} diam={diam} "
                            f"ritardo_diam={delay} "
                            f"soglia={self._soglia_ritardo}"
                        ),
                    )
                )

        return candidati

    # ------------------------------------------------------------------
    # Utilita interne
    # ------------------------------------------------------------------

    @staticmethod
    def _ritardo_numero(
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
        numero: int,
    ) -> int:
        """Conta quante estrazioni consecutive il numero non esce sulla ruota.

        Parte dall'estrazione precedente a quella corrente e va a ritroso.
        """
        delay = 0
        for idx in range(indice_estrazione - 1, -1, -1):
            _, estratti = dati[idx]
            if ruota not in estratti:
                delay += 1
                continue

            if numero in estratti[ruota]:
                return delay

            delay += 1

        # Mai uscito: ritardo massimo
        return delay
