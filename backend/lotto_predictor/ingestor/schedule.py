from __future__ import annotations

"""Calendario estrazioni Lotto Italiano — Lotto Convergent.

Il Lotto viene estratto il martedi, giovedi e sabato alle ore 20:00.
Questo modulo calcola date e orari delle estrazioni.
"""

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Timezone italiana (CET/CEST)
TZ_ROMA = ZoneInfo("Europe/Rome")

# Giorni della settimana con estrazione (0=lunedi, 1=martedi, ...)
# Martedi=1, Giovedi=3, Sabato=5
GIORNI_ESTRAZIONE = {1, 3, 5}

# Orario previsto dell'estrazione
ORA_ESTRAZIONE = time(20, 0, tzinfo=TZ_ROMA)

# Mappa giorno -> nome italiano
_NOMI_GIORNI = {
    0: "lunedi",
    1: "martedi",
    2: "mercoledi",
    3: "giovedi",
    4: "venerdi",
    5: "sabato",
    6: "domenica",
}


def e_giorno_estrazione(data: date | None = None) -> bool:
    """Verifica se una data e un giorno di estrazione.

    Args:
        data: data da verificare (default: oggi).

    Returns:
        True se la data cade in un giorno di estrazione (mar/gio/sab).
    """
    if data is None:
        data = _oggi()
    return data.weekday() in GIORNI_ESTRAZIONE


def prossima_estrazione(da: date | None = None) -> dict:
    """Calcola la data della prossima estrazione.

    Se oggi e giorno di estrazione e l'orario non e ancora passato,
    restituisce oggi. Altrimenti restituisce il prossimo giorno valido.

    Args:
        da: data/ora di riferimento (default: adesso).

    Returns:
        Dict con:
            - 'data': date della prossima estrazione
            - 'giorno': nome del giorno in italiano
            - 'ora_prevista': stringa HH:MM
            - 'datetime': datetime completo con timezone
            - 'ore_mancanti': float con ore mancanti all'estrazione
    """
    adesso = _adesso()
    data_rif = da or adesso.date()

    # Se oggi e giorno di estrazione e non sono ancora le 20:00
    if e_giorno_estrazione(data_rif):
        orario_estrazione = datetime.combine(data_rif, ORA_ESTRAZIONE)
        if adesso < orario_estrazione:
            return _build_info_estrazione(data_rif, adesso)

    # Cerca il prossimo giorno di estrazione
    prossimo = data_rif + timedelta(days=1)
    while prossimo.weekday() not in GIORNI_ESTRAZIONE:
        prossimo += timedelta(days=1)

    return _build_info_estrazione(prossimo, adesso)


def ultima_estrazione_passata(da: date | None = None) -> dict:
    """Calcola la data dell'ultima estrazione gia avvenuta.

    Args:
        da: data di riferimento (default: oggi).

    Returns:
        Dict con data, giorno, ora_prevista, datetime.
    """
    adesso = _adesso()
    data_rif = da or adesso.date()

    # Se oggi e giorno di estrazione e le 20:00 sono passate
    if e_giorno_estrazione(data_rif):
        orario_estrazione = datetime.combine(data_rif, ORA_ESTRAZIONE)
        if adesso >= orario_estrazione:
            return _build_info_estrazione(data_rif, adesso)

    # Vai indietro fino al giorno di estrazione precedente
    precedente = data_rif - timedelta(days=1)
    while precedente.weekday() not in GIORNI_ESTRAZIONE:
        precedente -= timedelta(days=1)

    return _build_info_estrazione(precedente, adesso)


def ieri_era_estrazione() -> bool:
    """Verifica se ieri c'e stata un'estrazione.

    Utile per decidere se scaricare i risultati la mattina dopo.

    Returns:
        True se ieri era giorno di estrazione.
    """
    ieri = _oggi() - timedelta(days=1)
    return e_giorno_estrazione(ieri)


def ore_alla_prossima_estrazione() -> float:
    """Calcola le ore mancanti alla prossima estrazione.

    Returns:
        Numero di ore (float) fino alla prossima estrazione.
    """
    info = prossima_estrazione()
    return info["ore_mancanti"]


def giorni_estrazione_precedenti(
    da_data: date,
    n: int = 5,
) -> list[date]:
    """Calcola le date delle N estrazioni precedenti a una data.

    Utile per scaricare piu estrazioni dal sito.

    Args:
        da_data: data di partenza (esclusa).
        n: numero di date da calcolare.

    Returns:
        Lista di date ordinate dalla piu recente alla piu vecchia.
    """
    risultati: list[date] = []
    corrente = da_data - timedelta(days=1)

    while len(risultati) < n:
        if e_giorno_estrazione(corrente):
            risultati.append(corrente)
        corrente -= timedelta(days=1)

    return risultati


def prossime_n_estrazioni(n: int = 5, da: date | None = None) -> list[dict]:
    """Calcola le prossime N date di estrazione.

    Args:
        n: numero di estrazioni future.
        da: data di partenza (default: oggi).

    Returns:
        Lista di dict con informazioni sulle prossime estrazioni.
    """
    adesso = _adesso()
    data_rif = da or adesso.date()
    risultati: list[dict] = []

    corrente = data_rif
    # Se oggi e giorno di estrazione e l'ora non e passata, includiamolo
    if e_giorno_estrazione(corrente):
        orario = datetime.combine(corrente, ORA_ESTRAZIONE)
        if adesso < orario:
            risultati.append(_build_info_estrazione(corrente, adesso))

    while len(risultati) < n:
        corrente += timedelta(days=1)
        if e_giorno_estrazione(corrente):
            risultati.append(_build_info_estrazione(corrente, adesso))

    return risultati


# ---- Funzioni interne ----


def _build_info_estrazione(data_estrazione: date, adesso: datetime) -> dict:
    """Costruisce il dict informativo per una data di estrazione.

    Args:
        data_estrazione: data dell'estrazione.
        adesso: datetime corrente per calcolo ore mancanti.

    Returns:
        Dict con data, giorno, ora_prevista, datetime, ore_mancanti.
    """
    orario = datetime.combine(data_estrazione, ORA_ESTRAZIONE)
    delta = orario - adesso
    ore_mancanti = delta.total_seconds() / 3600

    return {
        "data": data_estrazione,
        "giorno": _NOMI_GIORNI[data_estrazione.weekday()],
        "ora_prevista": "20:00",
        "datetime": orario,
        "ore_mancanti": round(ore_mancanti, 1),
    }


def _oggi() -> date:
    """Data odierna nel timezone italiano."""
    return datetime.now(tz=TZ_ROMA).date()


def _adesso() -> datetime:
    """Datetime corrente nel timezone italiano."""
    return datetime.now(tz=TZ_ROMA)
