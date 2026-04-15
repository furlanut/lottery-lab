from __future__ import annotations

"""CLI 10eLotto ogni 5 minuti — Sistema predittivo."""

import logging

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="diecielotto",
    help="10eLotto ogni 5 minuti — Sistema predittivo.",
    no_args_is_help=True,
)
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


@app.command(name="init-db")
def init_db() -> None:
    """Inizializza il database creando le tabelle 10eLotto."""
    from lotto_predictor.models.database import Base, get_engine

    import diecielotto.models.database  # noqa: F401

    console.print("[bold]Inizializzazione tabelle 10eLotto...[/bold]")
    engine = get_engine()
    Base.metadata.create_all(engine)
    console.print("[green]Tabelle 10eLotto create con successo.[/green]")


@app.command()
def status() -> None:
    """Mostra stato del sistema: estrazioni nel DB, range date."""
    from lotto_predictor.models.database import get_session
    from sqlalchemy import func, select

    from diecielotto.models.database import DiecieLottoEstrazione

    session = get_session()
    try:
        n = session.scalar(select(func.count(DiecieLottoEstrazione.id))) or 0
        data_min = session.scalar(select(func.min(DiecieLottoEstrazione.data)))
        data_max = session.scalar(select(func.max(DiecieLottoEstrazione.data)))

        console.print("\n[bold]10eLOTTO OGNI 5 MINUTI — Status[/bold]\n")
        table = Table(show_header=False, box=None)
        table.add_column("Chiave", style="bold")
        table.add_column("Valore")
        table.add_row("Estrazioni nel DB", str(n))
        if data_min and data_max:
            table.add_row("Prima estrazione", str(data_min))
            table.add_row("Ultima estrazione", str(data_max))
        console.print(table)
        console.print()
    finally:
        session.close()


@app.command()
def ev() -> None:
    """Calcola e mostra il confronto EV per tutte le configurazioni."""
    from diecielotto.ev_calculator import calcola_ev_completo, formatta_report_ev

    report = calcola_ev_completo()
    console.print(formatta_report_ev(report))


@app.command()
def calendario() -> None:
    """Mostra info sulle prossime estrazioni (ogni 5 minuti, 24h/24)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Rome")
    now = datetime.now(tz)

    # Next extraction is at the next 5-minute mark
    minute = now.minute
    next_min = ((minute // 5) + 1) * 5
    next_hour = now.hour
    if next_min >= 60:
        next_min = 0
        next_hour = (next_hour + 1) % 24

    console.print("\n[bold]10eLOTTO OGNI 5 MINUTI — Calendario[/bold]\n")
    console.print("Estrazioni: ogni 5 minuti, 24 ore su 24, 7 giorni su 7")
    console.print("~288 estrazioni al giorno")
    console.print(f"\nProssima estrazione: ore {next_hour:02d}:{next_min:02d}")
    console.print()


if __name__ == "__main__":
    app()
