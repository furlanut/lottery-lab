"""Import dati da file CSV — Lotto Convergent.

Formato CSV atteso:
  date,wheel,n1,n2,n3,n4,n5
  31/12/2015,BARI,33,78,6,89,74
"""

import csv
import logging
from pathlib import Path

from lotto_predictor.ingestor.validator import (
    ValidationError,
    valida_data,
    valida_numeri,
    valida_ruota,
)

logger = logging.getLogger(__name__)


def parse_file_csv(filepath: Path) -> list[dict]:
    """Parsa un file CSV con dati estrazioni.

    Args:
        filepath: percorso del file CSV

    Returns:
        Lista di dizionari con chiavi:
        - concorso: int (0 se non presente nel CSV)
        - data: date
        - ruota: str
        - numeri: list[int]
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")

    risultati = []
    errori = []

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                data_estrazione = valida_data(row["date"])
                ruota = valida_ruota(row["wheel"])

                numeri = [
                    int(row[f"n{i}"]) for i in range(1, 6)
                ]
                valida_numeri(numeri)

                # Il CSV non ha il numero concorso, usiamo 0 come placeholder
                concorso = int(row.get("concorso", 0))

                risultati.append({
                    "concorso": concorso,
                    "data": data_estrazione,
                    "ruota": ruota,
                    "numeri": numeri,
                })
            except (ValidationError, ValueError, KeyError) as e:
                errori.append(f"Riga {row_num}: {e}")

    if errori:
        logger.warning(
            "File %s: %d errori su %d righe",
            filepath.name, len(errori), row_num,
        )

    logger.info(
        "File %s: %d estrazioni valide importate",
        filepath.name, len(risultati),
    )
    return risultati
