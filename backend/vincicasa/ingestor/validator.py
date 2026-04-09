from __future__ import annotations

"""Validazione dati estrazioni — VinciCasa.

Verifica integrita dei dati prima dell'inserimento nel database:
- 5 numeri distinti per estrazione
- Range 1-40
- Ordine crescente
- Data valida (dal luglio 2014 in poi)
- Nessuna dimensione ruota (gioco a estrazione unica giornaliera)
"""

from datetime import date, datetime

# Data di inizio estrazioni VinciCasa
DATA_INIZIO_VINCICASA = date(2014, 7, 28)

# Costanti di gioco
NUMERI_TOTALI = 40
NUMERI_ESTRATTI = 5


class VCValidationError(Exception):
    """Errore di validazione dati estrazione VinciCasa."""

    def __init__(self, message: str, dettagli: dict | None = None):
        super().__init__(message)
        self.dettagli = dettagli or {}


def valida_numeri(numeri: list[int]) -> list[int]:
    """Valida i 5 numeri di un'estrazione VinciCasa.

    Controlla quantita, range 1-40, unicita e ordine crescente.

    Args:
        numeri: lista di 5 numeri

    Returns:
        Lista di 5 numeri ordinati in modo crescente

    Raises:
        VCValidationError: se i numeri non sono validi
    """
    if len(numeri) != NUMERI_ESTRATTI:
        raise VCValidationError(
            f"Attesi {NUMERI_ESTRATTI} numeri, ricevuti {len(numeri)}",
            {"numeri": numeri},
        )

    for n in numeri:
        if not isinstance(n, int) or n < 1 or n > NUMERI_TOTALI:
            raise VCValidationError(
                f"Numero fuori range (1-{NUMERI_TOTALI}): {n}",
                {"numero": n, "numeri": numeri},
            )

    if len(set(numeri)) != NUMERI_ESTRATTI:
        duplicati = [n for n in numeri if numeri.count(n) > 1]
        raise VCValidationError(
            f"Numeri non distinti: {numeri}",
            {"numeri": numeri, "duplicati": duplicati},
        )

    # Ordina in modo crescente (convenzione VinciCasa)
    return sorted(numeri)


def valida_data(data_str: str, formato: str = "%d/%m/%Y") -> date:
    """Valida e converte una stringa data per VinciCasa.

    Verifica che la data sia successiva all'inizio delle estrazioni (luglio 2014).

    Args:
        data_str: stringa data (es. "28/07/2014")
        formato: formato della data

    Returns:
        Oggetto date

    Raises:
        VCValidationError: se la data non e valida
    """
    try:
        parsed = datetime.strptime(data_str.strip(), formato).date()
    except ValueError as e:
        raise VCValidationError(
            f"Data non valida: '{data_str}' (formato atteso: {formato})",
            {"data": data_str, "formato": formato},
        ) from e

    if parsed < DATA_INIZIO_VINCICASA:
        raise VCValidationError(
            f"Data antecedente all'inizio di VinciCasa ({DATA_INIZIO_VINCICASA}): {parsed}",
            {"data": str(parsed), "data_inizio": str(DATA_INIZIO_VINCICASA)},
        )

    return parsed


def valida_concorso(concorso: int | str) -> int:
    """Valida il numero del concorso VinciCasa.

    Args:
        concorso: numero del concorso

    Returns:
        Numero del concorso come intero

    Raises:
        VCValidationError: se il concorso non e valido
    """
    try:
        c = int(concorso)
    except (ValueError, TypeError) as e:
        raise VCValidationError(f"Numero concorso non valido: '{concorso}'") from e

    if c < 1:
        raise VCValidationError(f"Numero concorso deve essere positivo: {c}")

    return c


def valida_estrazione(
    concorso: int | str,
    data_str: str,
    numeri: list[int],
    formato_data: str = "%d/%m/%Y",
) -> tuple[int, date, list[int]]:
    """Valida un'intera riga di estrazione VinciCasa.

    Funzione di comodo che combina tutte le validazioni.

    Args:
        concorso: numero del concorso
        data_str: stringa data
        numeri: lista di 5 numeri
        formato_data: formato della stringa data

    Returns:
        Tupla (concorso_validato, data_validata, numeri_ordinati)

    Raises:
        VCValidationError: se un qualsiasi campo non e valido
    """
    concorso_ok = valida_concorso(concorso)
    data_ok = valida_data(data_str, formato_data)
    numeri_ok = valida_numeri(numeri)

    return concorso_ok, data_ok, numeri_ok
