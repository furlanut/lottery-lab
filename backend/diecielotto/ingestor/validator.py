from __future__ import annotations

"""Validazione estrazioni 10eLotto ogni 5 minuti."""

from typing import Optional


class DELValidationError(Exception):
    """Errore di validazione per estrazioni 10eLotto."""


def valida_estrazione(
    numeri: list[int],
    numero_oro: int,
    doppio_oro: int,
    numeri_extra: Optional[list[int]] = None,
) -> tuple[list[int], int, int, list[int]]:
    """Valida un'estrazione 10eLotto.

    Checks:
    - Exactly 20 numbers
    - All in range 1-90
    - All distinct
    - Numero Oro is in the 20
    - Doppio Oro is in the 20 and different from Oro
    - Extra (if present): exactly 15 numbers, range 1-90, all distinct,
      no overlap with the 20

    Returns:
        Tuple (numeri_ordinati, numero_oro, doppio_oro, extra_ordinati).

    Raises:
        DELValidationError: se i dati non sono validi.
    """
    if len(numeri) != 20:
        msg = f"Attesi 20 numeri, trovati {len(numeri)}"
        raise DELValidationError(msg)

    if len(set(numeri)) != 20:
        msg = f"Numeri duplicati: {numeri}"
        raise DELValidationError(msg)

    for n in numeri:
        if not (1 <= n <= 90):
            msg = f"Numero fuori range: {n}"
            raise DELValidationError(msg)

    if numero_oro not in numeri:
        msg = f"Numero Oro {numero_oro} non presente nei 20 estratti"
        raise DELValidationError(msg)

    if doppio_oro not in numeri:
        msg = f"Doppio Oro {doppio_oro} non presente nei 20 estratti"
        raise DELValidationError(msg)

    if numero_oro == doppio_oro:
        msg = f"Numero Oro e Doppio Oro uguali: {numero_oro}"
        raise DELValidationError(msg)

    extra_validati: list[int] = []
    if numeri_extra:
        if len(numeri_extra) != 15:
            msg = f"Attesi 15 numeri Extra, trovati {len(numeri_extra)}"
            raise DELValidationError(msg)
        if len(set(numeri_extra)) != 15:
            msg = "Numeri Extra duplicati"
            raise DELValidationError(msg)
        for n in numeri_extra:
            if not (1 <= n <= 90):
                msg = f"Numero Extra fuori range: {n}"
                raise DELValidationError(msg)
        overlap = set(numeri) & set(numeri_extra)
        if overlap:
            msg = f"Numeri Extra sovrapposti con i 20: {overlap}"
            raise DELValidationError(msg)
        extra_validati = sorted(numeri_extra)

    return sorted(numeri), numero_oro, doppio_oro, extra_validati
