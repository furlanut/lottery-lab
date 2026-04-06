"""Parser per file TXT dell'archivio storico del Lotto.

Formato file TXT (tab-separated):
  Riga 1: "Lotto"
  Riga 2: "Archivio estrazioni Lotto anno YYYY aggiornato al DD/MM/YYYY"
  Riga 3: "Concorso\tData\tBari\tCagliari\t..."  (header)
  Riga 4+: "208\t30/12/2025\t15 65 34 86 47\t70 20 89 2 86\t..."

Ogni cella ruota contiene 5 numeri separati da spazi.
La ruota NAZIONALE e presente nei file ma viene esclusa dall'import.
"""

import logging
import re
from pathlib import Path

from lotto_predictor.ingestor.validator import (
    ValidationError,
    valida_concorso,
    valida_data,
    valida_numeri,
    valida_ruota,
)

logger = logging.getLogger(__name__)

# Mapping colonne header -> nome ruota
COLONNE_RUOTE = [
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
    "NAZIONALE",
]


def parse_numeri_cella(cella: str) -> list[int]:
    """Estrae i 5 numeri da una cella del file TXT.

    Args:
        cella: stringa con 5 numeri separati da spazi (es. "15 65 34 86 47")

    Returns:
        Lista di 5 interi
    """
    numeri_str = cella.strip().split()
    return [int(n) for n in numeri_str if n.strip()]


def parse_file_txt(filepath: Path) -> list[dict]:
    """Parsa un file TXT dell'archivio storico.

    Args:
        filepath: percorso del file TXT

    Returns:
        Lista di dizionari con chiavi:
        - concorso: int
        - data: date
        - ruota: str
        - numeri: list[int] (5 numeri)

    Raises:
        FileNotFoundError: se il file non esiste
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")

    risultati = []
    errori = []

    with open(filepath, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Salta le prime 3 righe (titolo, descrizione, header)
    data_lines = [line for line in lines[3:] if line.strip()]

    for line_num, line in enumerate(data_lines, start=4):
        try:
            campi = line.rstrip("\n").split("\t")

            # Minimo: concorso + data + 10 ruote = 12 campi
            if len(campi) < 12:
                continue

            concorso = valida_concorso(campi[0].strip())
            data_estrazione = valida_data(campi[1].strip())

            # Parsa ogni ruota (colonne 2-12, indice 0-10 in COLONNE_RUOTE)
            for i, nome_ruota in enumerate(COLONNE_RUOTE):
                col_idx = i + 2

                # Salta NAZIONALE
                if nome_ruota == "NAZIONALE":
                    continue

                if col_idx >= len(campi):
                    continue

                cella = campi[col_idx].strip()
                if not cella:
                    continue

                try:
                    numeri = parse_numeri_cella(cella)
                    if len(numeri) != 5:
                        logger.warning(
                            "File %s, riga %d, ruota %s: %d numeri invece di 5",
                            filepath.name,
                            line_num,
                            nome_ruota,
                            len(numeri),
                        )
                        continue

                    valida_numeri(numeri)
                    ruota = valida_ruota(nome_ruota)

                    risultati.append(
                        {
                            "concorso": concorso,
                            "data": data_estrazione,
                            "ruota": ruota,
                            "numeri": numeri,
                        }
                    )
                except ValidationError as e:
                    errori.append(f"Riga {line_num}, {nome_ruota}: {e}")

        except (ValidationError, ValueError, IndexError) as e:
            errori.append(f"Riga {line_num}: {e}")

    if errori:
        logger.warning(
            "File %s: %d errori su %d righe processate",
            filepath.name,
            len(errori),
            len(data_lines),
        )
        for err in errori[:10]:
            logger.debug("  %s", err)

    logger.info(
        "File %s: %d estrazioni valide estratte",
        filepath.name,
        len(risultati),
    )
    return risultati


def scan_archivio_txt(directory: Path) -> list[Path]:
    """Trova tutti i file TXT dell'archivio in una directory.

    Args:
        directory: percorso della directory

    Returns:
        Lista di percorsi file TXT, ordinati per anno
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory non trovata: {directory}")

    pattern = re.compile(r"Lotto-archivio-estrazioni-(\d{4})\.txt")
    files = []

    for f in directory.iterdir():
        if f.is_file() and pattern.match(f.name):
            files.append(f)

    files.sort(key=lambda f: f.name)
    logger.info("Trovati %d file TXT in %s", len(files), directory)
    return files
