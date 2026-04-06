from __future__ import annotations

"""Money management — Lotto Convergent.

Strategia flat betting con controllo del rischio.
Gestisce bankroll, decisioni di gioco, registrazione giocate e vincite.

Regole:
  - Posta per ambo: €1 (configurabile)
  - Max 3 ambi per ciclo, 9 colpi per ciclo
  - Bankroll minimo per giocare: €100
  - Score < 3: non giocare mai
  - Score == 3 e bankroll < €300: non giocare
  - Score >= 4: gioca sempre (se bankroll sufficiente)
  - Stop loss: -€750
"""

import logging
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from lotto_predictor.config import settings
from lotto_predictor.models.database import Bankroll, Previsione

logger = logging.getLogger(__name__)

# Soglia bankroll per score == 3
_BANKROLL_SOGLIA_SCORE_3 = 300.0


# ---------------------------------------------------------------------------
# Decisione di gioco
# ---------------------------------------------------------------------------

def decide_play(
    bankroll: float,
    score: int,
    config: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Decide se giocare in base a bankroll e punteggio di convergenza.

    Applica le regole di money management:
    1. Score < 3 -> non giocare mai
    2. Bankroll sotto il minimo -> non giocare
    3. Stop loss raggiunto -> non giocare
    4. Score == 3 e bankroll < 300 -> non giocare
    5. Score >= 4 -> gioca se bankroll sufficiente

    Args:
        bankroll: saldo corrente.
        score: punteggio di convergenza (0-5).
        config: configurazione opzionale (sovrascrive i defaults).
            Chiavi supportate: bankroll_min_play, stop_loss,
            bankroll_iniziale.

    Returns:
        Tupla (should_play, reason).
    """
    cfg = config or {}
    bankroll_min = cfg.get("bankroll_min_play", settings.bankroll_min_play)
    stop_loss = cfg.get("stop_loss", settings.stop_loss)
    bankroll_iniziale = cfg.get("bankroll_iniziale", settings.bankroll_iniziale)

    # Calcola P&L rispetto al bankroll iniziale
    pnl = bankroll - bankroll_iniziale

    # Regola 1: score insufficiente
    if score < settings.min_score_play:
        return False, f"Score {score} sotto la soglia minima ({settings.min_score_play})"

    # Regola 2: stop loss
    if pnl <= stop_loss:
        return False, f"Stop loss raggiunto: P&L {pnl:.2f}€ (limite {stop_loss:.2f}€)"

    # Regola 3: bankroll insufficiente
    if bankroll < bankroll_min:
        return False, f"Bankroll {bankroll:.2f}€ sotto il minimo ({bankroll_min:.2f}€)"

    # Regola 4: score == 3 con bankroll basso
    if score == 3 and bankroll < _BANKROLL_SOGLIA_SCORE_3:
        return (
            False,
            f"Score 3 con bankroll {bankroll:.2f}€ sotto soglia "
            f"({_BANKROLL_SOGLIA_SCORE_3:.2f}€)",
        )

    # Regola 5: via libera
    return True, f"OK — score {score}, bankroll {bankroll:.2f}€"


# ---------------------------------------------------------------------------
# Calcolo costi
# ---------------------------------------------------------------------------

def calcola_costo_ciclo(
    posta: float,
    n_ambi: int,
    n_colpi: int,
) -> float:
    """Calcola il costo totale di un ciclo di gioco.

    Un ciclo prevede il gioco di ``n_ambi`` per ``n_colpi`` estrazioni
    consecutive, con posta fissa per ambo.

    Args:
        posta: importo per singolo ambo per estrazione.
        n_ambi: numero di ambi giocati nel ciclo.
        n_colpi: numero di estrazioni del ciclo.

    Returns:
        Costo totale del ciclo.
    """
    return posta * n_ambi * n_colpi


# ---------------------------------------------------------------------------
# Registrazione movimenti
# ---------------------------------------------------------------------------

def registra_giocata(
    session: Session,
    previsione_id: int,
    posta: float,
) -> Bankroll:
    """Registra una giocata nel bankroll.

    Crea un movimento di tipo GIOCATA (importo negativo) e aggiorna
    il saldo corrente.

    Args:
        session: sessione SQLAlchemy attiva.
        previsione_id: ID della previsione associata.
        posta: importo della giocata (valore positivo, verra negato).

    Returns:
        Record Bankroll creato.
    """
    saldo_corrente = get_bankroll_attuale(session)
    nuovo_saldo = saldo_corrente - posta

    record = Bankroll(
        data=date.today(),
        tipo="GIOCATA",
        importo=-posta,
        saldo=nuovo_saldo,
        previsione_id=previsione_id,
        note=f"Giocata previsione #{previsione_id}",
    )
    session.add(record)
    session.flush()

    logger.info(
        "Registrata giocata: -%.2f€ (prev #%d), saldo %.2f€",
        posta, previsione_id, nuovo_saldo,
    )
    return record


def registra_vincita(
    session: Session,
    previsione_id: int,
    vincita: float,
) -> Bankroll:
    """Registra una vincita nel bankroll.

    Crea un movimento di tipo VINCITA (importo positivo) e aggiorna
    il saldo corrente.

    Args:
        session: sessione SQLAlchemy attiva.
        previsione_id: ID della previsione associata.
        vincita: importo della vincita.

    Returns:
        Record Bankroll creato.
    """
    saldo_corrente = get_bankroll_attuale(session)
    nuovo_saldo = saldo_corrente + vincita

    record = Bankroll(
        data=date.today(),
        tipo="VINCITA",
        importo=vincita,
        saldo=nuovo_saldo,
        previsione_id=previsione_id,
        note=f"Vincita previsione #{previsione_id}",
    )
    session.add(record)
    session.flush()

    logger.info(
        "Registrata vincita: +%.2f€ (prev #%d), saldo %.2f€",
        vincita, previsione_id, nuovo_saldo,
    )
    return record


# ---------------------------------------------------------------------------
# Interrogazioni bankroll
# ---------------------------------------------------------------------------

def get_bankroll_attuale(session: Session) -> float:
    """Restituisce il saldo corrente del bankroll.

    Legge il saldo dall'ultimo movimento registrato. Se non ci sono
    movimenti, restituisce il bankroll iniziale dalla configurazione.

    Args:
        session: sessione SQLAlchemy attiva.

    Returns:
        Saldo corrente.
    """
    # Prendi il saldo dall'ultimo movimento (ordinato per id desc)
    ultimo = (
        session.query(Bankroll.saldo)
        .order_by(Bankroll.id.desc())
        .first()
    )
    if ultimo is not None:
        return float(ultimo[0])
    return settings.bankroll_iniziale


def get_riepilogo_pnl(session: Session) -> dict[str, Any]:
    """Restituisce il riepilogo profitti e perdite.

    Calcola totale giocate, totale vincite, P&L netto,
    numero operazioni e saldo corrente.

    Args:
        session: sessione SQLAlchemy attiva.

    Returns:
        Dizionario con chiavi:
            - bankroll_iniziale (float)
            - saldo_corrente (float)
            - totale_giocate (float): somma importi giocata (negativo)
            - totale_vincite (float): somma importi vincita (positivo)
            - pnl (float): profitto/perdita netto
            - n_giocate (int): numero giocate effettuate
            - n_vincite (int): numero vincite registrate
    """
    # Totale e conteggio giocate
    giocate = (
        session.query(
            func.coalesce(func.sum(Bankroll.importo), 0.0),
            func.count(Bankroll.id),
        )
        .filter(Bankroll.tipo == "GIOCATA")
        .one()
    )
    totale_giocate = float(giocate[0])
    n_giocate = int(giocate[1])

    # Totale e conteggio vincite
    vincite = (
        session.query(
            func.coalesce(func.sum(Bankroll.importo), 0.0),
            func.count(Bankroll.id),
        )
        .filter(Bankroll.tipo == "VINCITA")
        .one()
    )
    totale_vincite = float(vincite[0])
    n_vincite = int(vincite[1])

    saldo = get_bankroll_attuale(session)
    pnl = saldo - settings.bankroll_iniziale

    return {
        "bankroll_iniziale": settings.bankroll_iniziale,
        "saldo_corrente": saldo,
        "totale_giocate": totale_giocate,
        "totale_vincite": totale_vincite,
        "pnl": pnl,
        "n_giocate": n_giocate,
        "n_vincite": n_vincite,
    }
