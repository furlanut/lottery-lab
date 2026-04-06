"""Classe base astratta per i filtri convergenti.

Ogni filtro implementa l'interfaccia FilterBase e produce
candidati ambo con metadati sul metodo di generazione.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Candidato:
    """Un ambo candidato generato da un filtro.

    Attributes:
        num_a: primo numero dell'ambo
        num_b: secondo numero dell'ambo
        filtro: nome del filtro che ha generato il candidato
        dettaglio: informazioni aggiuntive sul segnale
        peso: peso del segnale (default 1.0)
    """
    num_a: int
    num_b: int
    filtro: str
    dettaglio: str = ""
    peso: float = 1.0

    @property
    def coppia(self) -> tuple[int, int]:
        """Coppia ordinata per confronto."""
        return (min(self.num_a, self.num_b), max(self.num_a, self.num_b))


@dataclass
class DrawData:
    """Dati di un'estrazione per una ruota.

    Attributes:
        data: data dell'estrazione (stringa dd/mm/yyyy)
        ruota: nome della ruota
        numeri: lista dei 5 numeri estratti
    """
    data: str
    ruota: str
    numeri: list[int] = field(default_factory=list)


class FilterBase(ABC):
    """Classe base per tutti i filtri convergenti.

    Ogni filtro riceve i dati storici e l'indice dell'estrazione corrente,
    e ritorna una lista di candidati ambo.
    """

    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome identificativo del filtro."""
        ...

    @abstractmethod
    def analizza(
        self,
        dati: list[tuple[str, dict[str, list[int]]]],
        indice_estrazione: int,
        ruota: str,
    ) -> list[Candidato]:
        """Analizza un'estrazione e genera candidati.

        Args:
            dati: lista di tuple (data, {ruota: [n1..n5]})
            indice_estrazione: indice dell'estrazione corrente nei dati
            ruota: ruota target per l'analisi

        Returns:
            Lista di candidati ambo generati dal filtro
        """
        ...
