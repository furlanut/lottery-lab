from __future__ import annotations

"""Calendario estrazioni VinciCasa.

VinciCasa si estrae TUTTI I GIORNI (dal luglio 2014).
Nessuna logica di giorni specifici come il Lotto tradizionale.
"""

from datetime import date, timedelta

# Data di inizio estrazioni VinciCasa
DATA_INIZIO_VINCICASA = date(2014, 7, 28)

# Orario estrazione (solo informativo, non usato per scheduling)
ORA_ESTRAZIONE = "20:00"


def is_draw_day(target: date) -> bool:
    """Verifica se una data e un giorno di estrazione.

    VinciCasa si estrae ogni giorno, quindi qualsiasi data
    a partire dal 28 luglio 2014 e valida.

    Args:
        target: data da verificare

    Returns:
        True se la data e un giorno di estrazione valido
    """
    return target >= DATA_INIZIO_VINCICASA


def next_draw_date(from_date: date | None = None) -> date:
    """Calcola la prossima data di estrazione.

    Dato che VinciCasa si estrae ogni giorno, la prossima
    estrazione e domani (o oggi se from_date e None).

    Args:
        from_date: data di riferimento (default: oggi)

    Returns:
        Data della prossima estrazione
    """
    if from_date is None:
        from_date = date.today()

    # Se siamo prima dell'inizio di VinciCasa, la prima estrazione valida
    if from_date < DATA_INIZIO_VINCICASA:
        return DATA_INIZIO_VINCICASA

    # L'estrazione di oggi potrebbe non essere ancora avvenuta,
    # quindi la prossima e domani
    return from_date + timedelta(days=1)


def prev_draw_date(from_date: date | None = None) -> date:
    """Calcola la data dell'ultima estrazione passata.

    Args:
        from_date: data di riferimento (default: oggi)

    Returns:
        Data dell'ultima estrazione gia avvenuta

    Raises:
        ValueError: se non ci sono estrazioni precedenti
    """
    if from_date is None:
        from_date = date.today()

    # L'estrazione di ieri e l'ultima sicuramente conclusa
    prev = from_date - timedelta(days=1)

    if prev < DATA_INIZIO_VINCICASA:
        msg = f"Nessuna estrazione VinciCasa prima del {DATA_INIZIO_VINCICASA}"
        raise ValueError(msg)

    return prev


def draw_dates_range(start: date, end: date) -> list[date]:
    """Genera la lista di tutte le date di estrazione in un intervallo.

    Args:
        start: data di inizio (inclusa)
        end: data di fine (inclusa)

    Returns:
        Lista di date di estrazione nell'intervallo

    Raises:
        ValueError: se l'intervallo non e valido
    """
    if start > end:
        msg = f"Data inizio ({start}) successiva a data fine ({end})"
        raise ValueError(msg)

    # Aggiusta l'inizio al minimo storico
    effective_start = max(start, DATA_INIZIO_VINCICASA)

    # Giornaliero: ogni giorno e un'estrazione
    dates: list[date] = []
    current = effective_start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    return dates
