"""Formattazione messaggi notifica — Lotto Convergent."""
from __future__ import annotations

from datetime import date


def formatta_previsioni(previsioni: list[dict], bankroll: float | None = None) -> str:
    """Formatta le previsioni per notifica pre-estrazione.

    Args:
        previsioni: lista di dict con ruota, ambo, score, filtri
        bankroll: saldo corrente (opzionale)

    Returns:
        Messaggio formattato
    """
    oggi = date.today().strftime("%d/%m/%Y")
    lines = [f"LOTTO CONVERGENT — Previsioni {oggi}", ""]

    # Raggruppa per score
    by_score: dict[int, list[dict]] = {}
    for p in previsioni:
        score = p["score"]
        if score not in by_score:
            by_score[score] = []
        by_score[score].append(p)

    for score in sorted(by_score.keys(), reverse=True):
        stars = "*" * score
        lines.append(f"SCORE {score} {stars}")
        for p in by_score[score]:
            a, b = p["ambo"]
            filtri = "+".join(p["filtri"])
            lines.append(f"  {a:2d}-{b:2d} {p['ruota']} ({filtri})")
        lines.append("")

    if not previsioni:
        lines.append("Nessun segnale forte. NON giocare questo turno.")
        lines.append("")

    # Riepilogo costo stimato del ciclo
    n_ambi = len([p for p in previsioni if p["score"] >= 3])
    if n_ambi > 0:
        costo = n_ambi * 1 * 9  # posta * ambi * colpi
        lines.append(f"Ciclo: {n_ambi} ambi x E1 x 9 colpi = E{costo}")

    if bankroll is not None:
        lines.append(f"Bankroll: E{bankroll:.2f}")

    return "\n".join(lines)


def formatta_esiti(
    esiti: list[dict],
    estrazioni: dict[str, list[int]] | None = None,
    bankroll: float | None = None,
) -> str:
    """Formatta gli esiti per notifica post-estrazione.

    Args:
        esiti: lista di dict con ruota, ambo, score, stato, vincita, colpo
        estrazioni: dict {ruota: [numeri]} dell'estrazione
        bankroll: saldo corrente

    Returns:
        Messaggio formattato
    """
    oggi = date.today().strftime("%d/%m/%Y")
    lines = [f"ESITO Estrazione {oggi}", ""]

    # Mostra estrazioni (se disponibili)
    if estrazioni:
        for ruota in sorted(estrazioni.keys()):
            nums = " ".join(f"{n:2d}" for n in estrazioni[ruota])
            lines.append(f"{ruota}: {nums}")
        lines.append("")

    # Mostra esiti: prima le vincite, poi le perdite
    vinte = [e for e in esiti if e.get("stato") == "VINTA"]
    perse = [e for e in esiti if e.get("stato") == "PERSA"]

    if vinte:
        for e in vinte:
            a, b = e["ambo"]
            lines.append(
                f"VINCITA: E{e.get('vincita', 250):.0f} "
                f"(ambo {a}-{b} {e['ruota']}, score {e['score']}, "
                f"colpo {e.get('colpo', '?')})"
            )
    elif perse:
        lines.append("Nessun ambo centrato in questo turno.")

    if bankroll is not None:
        lines.append(f"\nBankroll: E{bankroll:.2f}")

    return "\n".join(lines)


def formatta_status(
    bankroll: float,
    pnl: float,
    previsioni_attive: int,
    hit_rate: float,
    estrazioni: int,
) -> str:
    """Formatta il messaggio di status."""
    return (
        f"LOTTO CONVERGENT — Status\n"
        f"Bankroll: E{bankroll:.2f} | P&L: E{pnl:+.2f}\n"
        f"Previsioni attive: {previsioni_attive}\n"
        f"Hit rate: {hit_rate:.1f}%\n"
        f"Estrazioni nel DB: {estrazioni}"
    )
