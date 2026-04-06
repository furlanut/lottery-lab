from __future__ import annotations

"""CLI — Lotto Convergent.

Entry point per tutti i comandi del sistema.
Usa Typer per un'interfaccia utente ricca con output Rich.
"""

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="lotto",
    help="Lotto Convergent — Sistema predittivo per ambi secchi.",
    no_args_is_help=True,
)
console = Console()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


@app.command()
def ingest(
    csv_file: Path | None = typer.Option(None, "--csv", help="Percorso file CSV da importare"),
    txt_file: Path | None = typer.Option(None, "--txt", help="Percorso file TXT da importare"),
    archivio: Path | None = typer.Option(None, "--archivio", help="Directory archivio TXT"),
    anno_inizio: int | None = typer.Option(None, "--anno-inizio", help="Anno di partenza"),
    anno_fine: int | None = typer.Option(None, "--anno-fine", help="Anno di fine"),
    init_db: bool = typer.Option(False, "--init-db", help="Inizializza il database prima"),
) -> None:
    """Importa estrazioni nel database da CSV, TXT, o archivio completo."""
    from lotto_predictor.ingestor.service import (
        importa_archivio_completo,
        importa_csv,
        importa_txt,
    )
    from lotto_predictor.models.database import init_db as create_tables

    if init_db:
        console.print("[bold]Inizializzazione database...[/bold]")
        create_tables()
        console.print("[green]Database inizializzato.[/green]")

    if not any([csv_file, txt_file, archivio]):
        console.print(
            "[red]Errore: specificare almeno una sorgente "
            "(--csv, --txt, o --archivio)[/red]"
        )
        raise typer.Exit(code=1)

    if csv_file:
        console.print(f"[bold]Importazione CSV:[/bold] {csv_file}")
        stats = importa_csv(csv_file)
        _mostra_stats(stats)

    if txt_file:
        console.print(f"[bold]Importazione TXT:[/bold] {txt_file}")
        stats = importa_txt(txt_file)
        _mostra_stats(stats)

    if archivio:
        console.print(f"[bold]Importazione archivio:[/bold] {archivio}")
        if anno_inizio or anno_fine:
            console.print(
                f"  Filtro anni: {anno_inizio or '...'} — {anno_fine or '...'}"
            )
        stats = importa_archivio_completo(
            archivio,
            anno_inizio=anno_inizio,
            anno_fine=anno_fine,
        )
        _mostra_stats(stats)


@app.command()
def status() -> None:
    """Mostra stato del sistema: estrazioni, previsioni, bankroll."""
    from sqlalchemy import func, select

    from lotto_predictor.models.database import (
        Bankroll,
        Estrazione,
        Previsione,
        get_session,
    )

    session = get_session()
    try:
        # Conteggio estrazioni
        n_estrazioni = session.scalar(select(func.count(Estrazione.id))) or 0

        # Range date
        data_min = session.scalar(select(func.min(Estrazione.data)))
        data_max = session.scalar(select(func.max(Estrazione.data)))

        # Previsioni per stato
        n_attive = session.scalar(
            select(func.count(Previsione.id)).where(Previsione.stato == "ATTIVA")
        ) or 0
        n_vinte = session.scalar(
            select(func.count(Previsione.id)).where(Previsione.stato == "VINTA")
        ) or 0
        n_perse = session.scalar(
            select(func.count(Previsione.id)).where(Previsione.stato == "PERSA")
        ) or 0

        # Bankroll
        ultimo_saldo = session.scalar(
            select(Bankroll.saldo).order_by(Bankroll.id.desc()).limit(1)
        )

        # Output
        console.print("\n[bold]LOTTO CONVERGENT — Status[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Chiave", style="bold")
        table.add_column("Valore")

        table.add_row("Estrazioni nel DB", str(n_estrazioni))
        if data_min and data_max:
            table.add_row("Range date", f"{data_min} — {data_max}")
        table.add_row("", "")
        table.add_row("Previsioni attive", str(n_attive))
        table.add_row("Previsioni vinte", str(n_vinte))
        table.add_row("Previsioni perse", str(n_perse))

        totale = n_vinte + n_perse
        if totale > 0:
            hit_rate = n_vinte / totale * 100
            table.add_row("Hit rate", f"{hit_rate:.1f}%")

        table.add_row("", "")
        if ultimo_saldo is not None:
            table.add_row("Bankroll attuale", f"€{ultimo_saldo:.2f}")
        else:
            table.add_row("Bankroll", "Non inizializzato")

        console.print(table)
        console.print()

    finally:
        session.close()


@app.command()
def init_db() -> None:
    """Inizializza il database creando tutte le tabelle."""
    from lotto_predictor.models.database import init_db as create_tables

    console.print("[bold]Inizializzazione database...[/bold]")
    create_tables()
    console.print("[green]Tabelle create con successo.[/green]")


@app.command()
def health() -> None:
    """Verifica lo stato di salute del sistema."""
    from lotto_predictor.models.database import get_engine

    console.print("[bold]Health Check[/bold]\n")

    # Verifica database
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        console.print("[green]Database: OK[/green]")
    except Exception as e:
        console.print(f"[red]Database: ERRORE — {e}[/red]")
        raise typer.Exit(code=1)


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
