from __future__ import annotations

"""Validazione dati estrazioni — Lotto Convergent.

Verifica integrita dei dati prima dell'inserimento nel database:
- 5 numeri distinti per estrazione
- Range 1-90
- Ruota valida
- Data valida
"""

from datetime import date, datetime

RUOTE_VALIDE = {
    "BARI",
    "CAGLIARI",
    "FIRENZE",
    "GENOVA",
    "MILANO",
    "NAPOLI",
    "PALERMO",
    "ROMA",
    "TORINO",
    "VENEZIA",
}


class ValidationError(Exception):
    """Errore di validazione dati estrazione."""

    def __init__(self, message: str, dettagli: dict | None = None):
        super().__init__(message)
        self.dettagli = dettagli or {}


def valida_numeri(numeri: list[int]) -> None:
    """Valida i 5 numeri di un'estrazione.

    Args:
        numeri: lista di 5 numeri

    Raises:
        ValidationError: se i numeri non sono validi
    """
    if len(numeri) != 5:
        raise ValidationError(
            f"Attesi 5 numeri, ricevuti {len(numeri)}",
            {"numeri": numeri},
        )

    for n in numeri:
        if not isinstance(n, int) or n < 1 or n > 90:
            raise ValidationError(
                f"Numero fuori range (1-90): {n}",
                {"numero": n, "numeri": numeri},
            )

    if len(set(numeri)) != 5:
        raise ValidationError(
            f"Numeri non distinti: {numeri}",
            {"numeri": numeri, "duplicati": [n for n in numeri if numeri.count(n) > 1]},
        )


def valida_ruota(ruota: str) -> str:
    """Valida e normalizza il nome della ruota.

    Args:
        ruota: nome della ruota

    Returns:
        Nome della ruota in maiuscolo

    Raises:
        ValidationError: se la ruota non e valida
    """
    ruota_upper = ruota.strip().upper()
    if ruota_upper not in RUOTE_VALIDE:
        raise ValidationError(
            f"Ruota non valida: '{ruota}'",
            {"ruota": ruota, "valide": sorted(RUOTE_VALIDE)},
        )
    return ruota_upper


def valida_data(data_str: str, formato: str = "%d/%m/%Y") -> date:
    """Valida e converte una stringa data.

    Args:
        data_str: stringa data (es. "31/12/2025")
        formato: formato della data

    Returns:
        Oggetto date

    Raises:
        ValidationError: se la data non e valida
    """
    try:
        return datetime.strptime(data_str.strip(), formato).date()
    except ValueError as e:
        raise ValidationError(
            f"Data non valida: '{data_str}' (formato atteso: {formato})",
            {"data": data_str, "formato": formato},
        ) from e


def valida_concorso(concorso: int | str) -> int:
    """Valida il numero del concorso.

    Args:
        concorso: numero del concorso

    Returns:
        Numero del concorso come intero

    Raises:
        ValidationError: se il concorso non e valido
    """
    try:
        c = int(concorso)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Numero concorso non valido: '{concorso}'") from e

    if c < 1:
        raise ValidationError(f"Numero concorso deve essere positivo: {c}")
    return c
