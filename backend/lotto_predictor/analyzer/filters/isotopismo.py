"""Filtro Isotopismo Distanziale.

Per ogni posizione (1a-5a), calcola la distanza ciclometrica tra il
numero corrente e lo stesso slot nelle estrazioni precedenti.
Se la stessa distanza si ripete 2+ volte, proietta il prossimo
numero sommando/sottraendo la distanza ripetuta.
"""
from __future__ import annotations

from collections import Counter

from lotto_predictor.analyzer.cyclometry import cyclo_dist, fuori90, is_valid_ambo
from lotto_predictor.analyzer.filters.base import Candidato, FilterBase

# Numero di estrazioni precedenti da esaminare
_DEFAULT_LOOKBACK = 5
# Numero minimo di ripetizioni di una distanza per generare segnale
_MIN_RIPETIZIONI = 2


class Isotopismo(FilterBase):
    """Isotopismo Distanziale — distanze ripetute sulla stessa posizione."""

    def __init__(self, lookback: int = _DEFAULT_LOOKBACK) -> None:
        self._lookback = lookback

    @property
    def nome(self) -> str:
        return "isotopismo"

    def analizza(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
    ) -> list[Candidato]:
        """Cerca distanze ciclometriche ripetute per posizione.

        Per ogni posizione (0-4), raccoglie le distanze tra estrazioni
        consecutive nel lookback.  Se una distanza compare almeno
        _MIN_RIPETIZIONI volte, genera candidati proiettando
        base +/- distanza.
        """
        candidati: list[Candidato] = []

        # Serve almeno lookback+1 estrazioni precedenti
        if indice_estrazione < self._lookback:
            return candidati

        _, estratti_corrente = dati[indice_estrazione]
        if ruota not in estratti_corrente:
            return candidati

        numeri_corrente = estratti_corrente[ruota]

        for pos in range(5):
            # Raccolta distanze tra estrazioni consecutive nel lookback
            distances: list[int] = []
            for step in range(self._lookback):
                idx_a = indice_estrazione - step
                idx_b = indice_estrazione - step - 1
                if idx_b < 0:
                    break

                _, est_a = dati[idx_a]
                _, est_b = dati[idx_b]

                if ruota not in est_a or ruota not in est_b:
                    continue

                d = cyclo_dist(est_a[ruota][pos], est_b[ruota][pos])
                distances.append(d)

            # Verifica se qualche distanza si ripete
            counter = Counter(distances)
            for dist, count in counter.items():
                if count < _MIN_RIPETIZIONI or dist == 0:
                    continue

                # Proiezione: base +/- distanza ripetuta
                base = numeri_corrente[pos]
                projected_plus = fuori90(base + dist)
                projected_minus = fuori90(base - dist)

                dettaglio = (
                    f"pos={pos+1} base={base} dist={dist} "
                    f"ripetizioni={count} lookback={self._lookback}"
                )

                # Coppia (base, proiezione+)
                if is_valid_ambo(base, projected_plus):
                    candidati.append(
                        Candidato(
                            num_a=base,
                            num_b=projected_plus,
                            filtro=self.nome,
                            dettaglio=f"proj+ | {dettaglio}",
                        )
                    )

                # Coppia (base, proiezione-)
                if is_valid_ambo(base, projected_minus):
                    candidati.append(
                        Candidato(
                            num_a=base,
                            num_b=projected_minus,
                            filtro=self.nome,
                            dettaglio=f"proj- | {dettaglio}",
                        )
                    )

        return candidati
