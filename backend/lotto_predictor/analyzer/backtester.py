"""Backtester — Lotto Convergent.

Framework di backtesting con split temporale train/test.
Verifica l'hit rate dei segnali convergenti out-of-sample.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field

from lotto_predictor.analyzer.cyclometry import RUOTE

logger = logging.getLogger(__name__)


@dataclass
class RisultatoBacktest:
    """Risultati aggregati del backtesting.

    Attributes:
        score: livello di score analizzato
        segnali: numero totale di segnali generati
        hit: numero di ambi centrati
        hit_rate: percentuale di hit
        baseline: hit rate atteso dal caso
        ratio: rapporto hit_rate / baseline
        colpi_medi: colpo medio di uscita per gli hit
    """

    score: int
    segnali: int = 0
    hit: int = 0
    hit_rate: float = 0.0
    baseline: float = 0.0
    ratio: float = 0.0
    colpi_medi: float = 0.0
    colpi: list[int] = field(default_factory=list)


@dataclass
class ReportBacktest:
    """Report completo del backtesting."""

    dataset_size: int
    train_size: int
    test_size: int
    date_range: str
    risultati_per_score: dict[int, RisultatoBacktest] = field(default_factory=dict)
    totale_segnali: int = 0
    totale_hit: int = 0


def esegui_backtest(
    dati: list[tuple[str, dict[str, list[int]]]],
    min_score: int = 2,
    max_colpi: int = 9,
    train_ratio: float = 0.7,
) -> ReportBacktest:
    """Esegue il backtesting con split temporale.

    Train: calibra soglie (non usato attivamente, ma separa i dati).
    Test: misura hit rate out-of-sample.

    Args:
        dati: lista completa di estrazioni (data, {ruota: [numeri]})
        min_score: score minimo per generare segnali
        max_colpi: massimo colpi di verifica dopo il segnale
        train_ratio: proporzione dati per training (default 0.7)

    Returns:
        ReportBacktest con risultati aggregati per livello di score
    """
    from lotto_predictor.analyzer.convergence import calcola_convergenza

    split = int(len(dati) * train_ratio)

    report = ReportBacktest(
        dataset_size=len(dati),
        train_size=split,
        test_size=len(dati) - split,
        date_range=f"{dati[0][0]} - {dati[-1][0]}",
    )

    risultati_per_score = defaultdict(lambda: RisultatoBacktest(score=0))

    for draw_idx in range(split, len(dati) - max_colpi):
        for ruota in RUOTE:
            previsioni = calcola_convergenza(dati, draw_idx, ruota, min_score=min_score)

            for pred in previsioni:
                score = pred.score
                ambo = pred.ambo

                if score not in risultati_per_score:
                    risultati_per_score[score] = RisultatoBacktest(score=score)

                risultati_per_score[score].segnali += 1
                report.totale_segnali += 1

                # Verifica nei prossimi max_colpi estrazioni
                for colpo in range(1, max_colpi + 1):
                    future_idx = draw_idx + colpo
                    if future_idx >= len(dati):
                        break
                    _, future_wheels = dati[future_idx]
                    if ruota in future_wheels:
                        future_nums = set(future_wheels[ruota])
                        if ambo[0] in future_nums and ambo[1] in future_nums:
                            risultati_per_score[score].hit += 1
                            risultati_per_score[score].colpi.append(colpo)
                            report.totale_hit += 1
                            break

    # Calcola metriche derivate
    p_baseline_single = 1 / 400.5
    baseline_cycle = 1 - (1 - p_baseline_single) ** max_colpi

    for score, r in risultati_per_score.items():
        r.score = score
        if r.segnali > 0:
            r.hit_rate = r.hit / r.segnali
            r.baseline = baseline_cycle
            r.ratio = r.hit_rate / baseline_cycle if baseline_cycle > 0 else 0
            if r.colpi:
                r.colpi_medi = sum(r.colpi) / len(r.colpi)

    report.risultati_per_score = dict(risultati_per_score)
    return report


def formatta_report(report: ReportBacktest) -> str:
    """Formatta il report di backtesting per output testuale.

    Args:
        report: risultati del backtesting

    Returns:
        Stringa formattata per la console
    """
    lines = []
    lines.append("=" * 60)
    lines.append("BACKTEST FILTRI CONVERGENTI")
    lines.append("=" * 60)
    lines.append(f"Dataset: {report.dataset_size} estrazioni ({report.date_range})")
    lines.append(f"Train: {report.train_size} | Test: {report.test_size}")
    lines.append(f"Totale segnali: {report.totale_segnali}")
    lines.append(f"Totale hit: {report.totale_hit}")
    lines.append("")
    header = (
        f"{'SCORE':>5} {'SEGNALI':>8} {'HIT':>6} {'HIT%':>7} {'BASE%':>7} {'RATIO':>7} {'COLPO':>6}"
    )
    lines.append(header)
    lines.append("-" * 55)

    for score in sorted(report.risultati_per_score.keys()):
        r = report.risultati_per_score[score]
        marker = " <<<" if r.ratio > 1.5 else (" <" if r.ratio > 1.2 else "")
        lines.append(
            f"{r.score:>5} {r.segnali:>8} {r.hit:>6} "
            f"{r.hit_rate * 100:>6.2f}% {r.baseline * 100:>6.2f}% "
            f"{r.ratio:>6.2f}x {r.colpi_medi:>5.1f}{marker}"
        )

    lines.append("-" * 55)
    lines.append("< = interessante (>1.2x)  <<< = significativo (>1.5x)")
    return "\n".join(lines)
