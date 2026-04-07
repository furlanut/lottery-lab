from __future__ import annotations

from typing import Optional

"""CLI — Lotto Convergent.

Entry point per tutti i comandi del sistema.
Usa Typer per un'interfaccia utente ricca con output Rich.
"""

import logging
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
    csv_file: Optional[Path] = typer.Option(None, "--csv", help="Percorso file CSV da importare"),
    txt_file: Optional[Path] = typer.Option(None, "--txt", help="Percorso file TXT da importare"),
    archivio: Optional[Path] = typer.Option(None, "--archivio", help="Directory archivio TXT"),
    anno_inizio: Optional[int] = typer.Option(None, "--anno-inizio", help="Anno di partenza"),
    anno_fine: Optional[int] = typer.Option(None, "--anno-fine", help="Anno di fine"),
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
            "[red]Errore: specificare almeno una sorgente (--csv, --txt, o --archivio)[/red]"
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
            console.print(f"  Filtro anni: {anno_inizio or '...'} — {anno_fine or '...'}")
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
        n_attive = (
            session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "ATTIVA"))
            or 0
        )
        n_vinte = (
            session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "VINTA"))
            or 0
        )
        n_perse = (
            session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "PERSA"))
            or 0
        )

        # Bankroll
        ultimo_saldo = session.scalar(select(Bankroll.saldo).order_by(Bankroll.id.desc()).limit(1))

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
        raise typer.Exit(code=1) from e


@app.command()
def predict(
    csv_file: Optional[Path] = typer.Option(None, "--csv", help="File CSV sorgente dati"),
    min_score: int = typer.Option(3, "--min-score", help="Score minimo"),
    top_n: int = typer.Option(20, "--top-n", help="Numero massimo risultati"),
) -> None:
    """Genera previsioni basate sull'ultima estrazione disponibile."""
    from lotto_predictor.predictor.generator import carica_dati_csv, genera_previsioni

    if csv_file:
        dati = carica_dati_csv(csv_file)
    else:
        console.print("[red]Specificare --csv (supporto DB in arrivo)[/red]")
        raise typer.Exit(code=1)

    previsioni = genera_previsioni(dati, min_score=min_score, top_n=top_n)

    if not previsioni:
        console.print(
            "\n[yellow]Nessun segnale con score >= {min_score}. "
            "NON giocare questo turno.[/yellow]\n"
        )
        return

    table = Table(title=f"Previsioni (score >= {min_score})")
    table.add_column("#", style="bold")
    table.add_column("Ruota")
    table.add_column("Ambo")
    table.add_column("Score")
    table.add_column("Filtri")

    for i, p in enumerate(previsioni, 1):
        a, b = p["ambo"]
        filtri = "+".join(p["filtri"])
        table.add_row(str(i), p["ruota"], f"{a:2d}-{b:2d}", str(p["score"]), filtri)

    console.print(table)
    console.print()


@app.command()
def backtest(
    csv_file: Optional[Path] = typer.Option(None, "--csv", help="File CSV sorgente dati"),
    min_score: int = typer.Option(2, "--min-score", help="Score minimo"),
    max_colpi: int = typer.Option(9, "--max-colpi", help="Colpi massimi per ciclo"),
    train_ratio: float = typer.Option(0.7, "--train-ratio", help="Ratio train/test"),
) -> None:
    """Esegue backtesting con split temporale."""
    from lotto_predictor.analyzer.backtester import esegui_backtest, formatta_report
    from lotto_predictor.predictor.generator import carica_dati_csv

    if csv_file:
        dati = carica_dati_csv(csv_file)
    else:
        console.print("[red]Specificare --csv (supporto DB in arrivo)[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Backtesting su {len(dati)} estrazioni...[/bold]\n")
    report = esegui_backtest(
        dati, min_score=min_score, max_colpi=max_colpi, train_ratio=train_ratio
    )
    console.print(formatta_report(report))
    console.print()


@app.command()
def notify(
    test: bool = typer.Option(False, "--test", help="Invia notifica di test"),
) -> None:
    """Invia notifiche via ntfy."""
    from lotto_predictor.notifier.ntfy import notifica_test

    if test:
        ok = notifica_test()
        if ok:
            console.print("[green]Notifica di test inviata.[/green]")
        else:
            console.print("[red]Errore invio notifica. Verifica NTFY_TOPIC.[/red]")
            raise typer.Exit(code=1)
    else:
        console.print("[yellow]Usa --test per inviare una notifica di prova.[/yellow]")


@app.command(name="predict-v2")
def predict_v2(
    archivio: Optional[Path] = typer.Option(None, "--archivio", help="Directory archivio TXT"),
    csv_file: Optional[Path] = typer.Option(None, "--csv", help="File CSV sorgente dati"),
    top_n: int = typer.Option(20, "--top-n", help="Numero massimo risultati"),
    finestra_dec: int = typer.Option(150, "--w-dec", help="Finestra freq+rit+dec"),
    finestra_fig: int = typer.Option(70, "--w-fig", help="Finestra freq+rit+fig"),
) -> None:
    """Previsioni V2 — segnale validato freq+rit+dec (W=150) + freq+rit+fig (W=70)."""
    from lotto_predictor.analyzer.convergence_v2 import genera_segnali_v2

    dati = _carica_dati(archivio, csv_file)
    if dati is None:
        raise typer.Exit(code=1)

    console.print(
        f"\n[bold]PREDICT V2[/bold] — {len(dati)} estrazioni, "
        f"W_dec={finestra_dec}, W_fig={finestra_fig}\n"
    )

    segnali = genera_segnali_v2(
        dati, top_n=top_n, finestra_dec=finestra_dec, finestra_fig=finestra_fig
    )

    if not segnali:
        console.print("[yellow]Nessun segnale. NON giocare questo turno.[/yellow]\n")
        return

    table = Table(title=f"Previsioni V2 (top {top_n})")
    table.add_column("#", style="bold")
    table.add_column("Ruota")
    table.add_column("Ambo")
    table.add_column("Score")
    table.add_column("Metodo")
    table.add_column("Freq")
    table.add_column("Ritardo")
    table.add_column("Dettagli")

    for i, s in enumerate(segnali, 1):
        a, b = s["ambo"]
        table.add_row(
            str(i),
            s["ruota"],
            f"{a:2d}-{b:2d}",
            str(s["score"]),
            s["metodo"],
            str(s["frequenza"]),
            str(s["ritardo"]),
            s["dettagli"],
        )

    console.print(table)

    # Riepilogo
    dec_count = sum(1 for s in segnali if s["metodo"] == "freq+rit+dec")
    fig_count = sum(1 for s in segnali if s["metodo"] == "freq+rit+fig")
    console.print(
        f"\n[bold]Riepilogo:[/bold] {dec_count} segnali freq+rit+dec (W={finestra_dec}), "
        f"{fig_count} segnali freq+rit+fig (W={finestra_fig})\n"
    )


def _carica_dati(archivio=None, csv_file=None):
    """Carica dati da archivio TXT o CSV."""
    if archivio:
        from collections import defaultdict
        from datetime import datetime

        from lotto_predictor.ingestor.txt_parser import parse_file_txt, scan_archivio_txt

        console.print(f"[bold]Caricamento archivio:[/bold] {archivio}")
        files = [f for f in scan_archivio_txt(archivio) if int(f.stem.split("-")[-1]) >= 1946]
        all_records = []
        for fp in files:
            all_records.extend(parse_file_txt(fp))
        by_date = defaultdict(dict)
        for r in all_records:
            by_date[r["data"].strftime("%d/%m/%Y")][r["ruota"]] = r["numeri"]
        dati = sorted(by_date.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
        console.print(f"  Caricate {len(dati)} estrazioni")
        return dati
    elif csv_file:
        from lotto_predictor.predictor.generator import carica_dati_csv

        return carica_dati_csv(csv_file)
    else:
        console.print("[red]Specificare --archivio o --csv[/red]")
        return None


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
