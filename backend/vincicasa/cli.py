from __future__ import annotations

from typing import Optional

"""CLI — VinciCasa.

Entry point per tutti i comandi del gioco VinciCasa.
Usa Typer per un'interfaccia utente ricca con output Rich.
VinciCasa: 5 numeri su 40, estrazione giornaliera (tutti i giorni).
"""

import logging
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="vincicasa",
    help="VinciCasa — Sistema predittivo 5/40.",
    no_args_is_help=True,
)
console = Console()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

# Timezone italiana
TZ_ROMA = ZoneInfo("Europe/Rome")

# VinciCasa si estrae tutti i giorni alle 20:00
ORA_ESTRAZIONE = time(20, 0, tzinfo=TZ_ROMA)

# Nomi giorni italiani
_NOMI_GIORNI = {
    0: "lunedi",
    1: "martedi",
    2: "mercoledi",
    3: "giovedi",
    4: "venerdi",
    5: "sabato",
    6: "domenica",
}


@app.command(name="init-db")
def init_db() -> None:
    """Inizializza il database creando le tabelle VinciCasa."""
    from lotto_predictor.models.database import Base, get_engine

    # Importa i modelli VinciCasa per registrarli nel metadata
    import vincicasa.models.database  # noqa: F401

    console.print("[bold]Inizializzazione tabelle VinciCasa...[/bold]")
    engine = get_engine()
    Base.metadata.create_all(engine)
    console.print("[green]Tabelle VinciCasa create con successo.[/green]")


@app.command()
def ingest(
    csv_file: Optional[Path] = typer.Option(None, "--csv", help="Percorso file CSV da importare"),
    scrape: bool = typer.Option(False, "--scrape", help="Scarica estrazioni dal sito web"),
) -> None:
    """Importa estrazioni VinciCasa da CSV o dal sito web."""
    if not csv_file and not scrape:
        console.print("[red]Errore: specificare --csv <file> o --scrape[/red]")
        raise typer.Exit(code=1)

    if csv_file:
        console.print(f"[bold]Importazione CSV VinciCasa:[/bold] {csv_file}")
        stats = _importa_csv(csv_file)
        _mostra_stats(stats)

    if scrape:
        console.print("[bold]Scraping VinciCasa dal sito web...[/bold]")
        console.print(
            "[yellow]Scraper non ancora implementato. Usa --csv per importare da file.[/yellow]"
        )


@app.command()
def status() -> None:
    """Mostra stato del sistema: estrazioni nel DB, range date."""
    from lotto_predictor.models.database import get_session
    from sqlalchemy import func, select

    from vincicasa.models.database import VinciCasaEstrazione

    session = get_session()
    try:
        # Conteggio estrazioni
        n_estrazioni = session.scalar(select(func.count(VinciCasaEstrazione.id))) or 0

        # Range date
        data_min = session.scalar(select(func.min(VinciCasaEstrazione.data)))
        data_max = session.scalar(select(func.max(VinciCasaEstrazione.data)))

        # Output
        console.print("\n[bold]VINCICASA — Status[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Chiave", style="bold")
        table.add_column("Valore")

        table.add_row("Estrazioni nel DB", str(n_estrazioni))
        if data_min and data_max:
            table.add_row("Prima estrazione", str(data_min))
            table.add_row("Ultima estrazione", str(data_max))
        else:
            table.add_row("Range date", "Nessuna estrazione presente")

        console.print(table)
        console.print()

    finally:
        session.close()


@app.command()
def calendario() -> None:
    """Mostra la prossima data di estrazione VinciCasa.

    VinciCasa si estrae tutti i giorni alle 20:00.
    """
    now = datetime.now(TZ_ROMA)
    today = now.date()

    # Se non e ancora passata l'ora, la prossima e oggi; altrimenti domani
    estrazione_oggi = datetime.combine(today, ORA_ESTRAZIONE)
    next_draw = today if now < estrazione_oggi else today + timedelta(days=1)

    next_draw_dt = datetime.combine(next_draw, ORA_ESTRAZIONE)
    delta = next_draw_dt - now
    ore_mancanti = delta.total_seconds() / 3600

    console.print("\n[bold]VINCICASA — Calendario[/bold]\n")
    console.print(
        f"Prossima estrazione: [bold]{_NOMI_GIORNI[next_draw.weekday()]} "
        f"{next_draw}[/bold] ore 20:00"
    )

    if ore_mancanti < 1:
        console.print(f"[yellow]Tra {ore_mancanti * 60:.0f} minuti![/yellow]")
    elif ore_mancanti < 6:
        console.print(f"[yellow]Tra {ore_mancanti:.1f} ore[/yellow]")
    else:
        console.print(f"Tra {ore_mancanti:.1f} ore")

    console.print("\n[dim]VinciCasa si estrae tutti i giorni alle 20:00.[/dim]\n")


# ---------------------------------------------------------------------------
# Funzioni private
# ---------------------------------------------------------------------------


def _importa_csv(csv_path: Path) -> dict:
    """Importa estrazioni VinciCasa da file CSV.

    Formato atteso: concorso,data,n1,n2,n3,n4,n5
    La data puo essere in formato DD/MM/YYYY o YYYY-MM-DD.
    """
    import csv

    from lotto_predictor.models.database import get_session

    from vincicasa.ingestor.validator import (
        VCValidationError,
        valida_estrazione,
    )
    from vincicasa.models.database import VinciCasaEstrazione

    session = get_session()
    inserite = 0
    duplicate = 0
    errori = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            for row in reader:
                # Salta righe vuote o header
                if not row or not row[0].strip().isdigit():
                    continue

                try:
                    concorso_raw = row[0].strip()
                    data_str = row[1].strip()
                    numeri = [int(row[i].strip()) for i in range(2, 7)]

                    # Rileva formato data
                    formato = "%Y-%m-%d" if "-" in data_str else "%d/%m/%Y"
                    concorso, data, numeri_ok = valida_estrazione(
                        concorso_raw, data_str, numeri, formato_data=formato
                    )

                    est = VinciCasaEstrazione(
                        concorso=concorso,
                        data=data,
                        n1=numeri_ok[0],
                        n2=numeri_ok[1],
                        n3=numeri_ok[2],
                        n4=numeri_ok[3],
                        n5=numeri_ok[4],
                    )
                    session.merge(est)
                    inserite += 1

                except VCValidationError as e:
                    console.print(f"[yellow]Riga ignorata: {e}[/yellow]")
                    errori += 1
                except (IndexError, ValueError) as e:
                    console.print(f"[yellow]Riga malformata: {e}[/yellow]")
                    errori += 1

        session.commit()

    except Exception as e:
        session.rollback()
        console.print(f"[red]Errore importazione: {e}[/red]")
        raise typer.Exit(code=1) from e
    finally:
        session.close()

    return {
        "inserite": inserite,
        "duplicate": duplicate,
        "errori": errori,
        "file": str(csv_path),
    }


def _mostra_stats(stats: dict) -> None:
    """Mostra statistiche di importazione."""
    table = Table(show_header=False, box=None)
    table.add_column("Metrica", style="bold")
    table.add_column("Valore")

    for key, value in stats.items():
        if key != "file":
            table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
