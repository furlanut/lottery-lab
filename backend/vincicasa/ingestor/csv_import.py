from __future__ import annotations

"""Import dati VinciCasa da file CSV — Lottery Lab.

Formato CSV atteso:
    concorso,data,n1,n2,n3,n4,n5
    1,09/07/2014,5,13,17,25,39
    2,10/07/2014,3,8,22,30,36

Separatore: virgola. Encoding: UTF-8.
La prima riga e l'header (obbligatorio).
"""

import csv
import logging
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class VCImportError(Exception):
    """Errore durante l'import CSV VinciCasa."""


def parse_csv_vincicasa(filepath: Path) -> list[dict]:
    """Parsa un file CSV con estrazioni VinciCasa.

    Args:
        filepath: percorso del file CSV.

    Returns:
        Lista di dizionari con chiavi:
            - concorso: int
            - data: date
            - n1..n5: int

    Raises:
        FileNotFoundError: se il file non esiste.
        VCImportError: se il file e vuoto o ha formato errato.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")

    risultati: list[dict] = []
    errori: list[str] = []
    row_num = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Verifica che l'header contenga le colonne attese
        if reader.fieldnames is None:
            raise VCImportError(f"File vuoto o senza header: {filepath}")

        colonne_attese = {"concorso", "data", "n1", "n2", "n3", "n4", "n5"}
        colonne_presenti = {c.strip().lower() for c in reader.fieldnames}
        mancanti = colonne_attese - colonne_presenti
        if mancanti:
            raise VCImportError(
                f"Colonne mancanti nel CSV: {sorted(mancanti)}. "
                f"Formato atteso: concorso,data,n1,n2,n3,n4,n5"
            )

        for row_num, row in enumerate(reader, start=2):
            try:
                record = _parse_riga(row, row_num)
                risultati.append(record)
            except (ValueError, KeyError) as e:
                errori.append(f"Riga {row_num}: {e}")

    if errori:
        logger.warning(
            "File %s: %d errori su %d righe",
            filepath.name,
            len(errori),
            row_num,
        )
        for err in errori[:10]:
            logger.warning("  %s", err)

    logger.info(
        "File %s: %d estrazioni VinciCasa valide importate",
        filepath.name,
        len(risultati),
    )
    return risultati


def _parse_riga(row: dict, row_num: int) -> dict:
    """Parsa una singola riga del CSV.

    Args:
        row: dizionario dalla riga CSV.
        row_num: numero riga per messaggi di errore.

    Returns:
        Dizionario con concorso, data, n1..n5.

    Raises:
        ValueError: se i dati non sono validi.
    """
    # Parsing concorso
    concorso_raw = row.get("concorso", "").strip()
    concorso = int(concorso_raw) if concorso_raw else 0

    # Parsing data — supporta dd/mm/yyyy e yyyy-mm-dd
    data_raw = row["data"].strip()
    data_estrazione = _parse_data(data_raw)

    # Parsing numeri
    numeri: list[int] = []
    for i in range(1, 6):
        chiave = f"n{i}"
        valore = row[chiave].strip()
        numero = int(valore)
        numeri.append(numero)

    # Validazione range 1-40
    for i, n in enumerate(numeri, start=1):
        if not 1 <= n <= 40:
            raise ValueError(f"n{i}={n} fuori range 1-40 alla riga {row_num}")

    # Validazione unicita
    if len(set(numeri)) != 5:
        raise ValueError(f"Numeri duplicati alla riga {row_num}: {numeri}")

    return {
        "concorso": concorso,
        "data": data_estrazione,
        "n1": numeri[0],
        "n2": numeri[1],
        "n3": numeri[2],
        "n4": numeri[3],
        "n5": numeri[4],
    }


def _parse_data(data_str: str) -> date:
    """Parsa una stringa data in formato dd/mm/yyyy o yyyy-mm-dd.

    Args:
        data_str: stringa con la data.

    Returns:
        Oggetto date.

    Raises:
        ValueError: se il formato non e riconosciuto.
    """
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(
        f"Formato data non riconosciuto: '{data_str}'. Formati accettati: dd/mm/yyyy, yyyy-mm-dd"
    )
