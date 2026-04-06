"""Notifiche push via ntfy.sh — Lotto Convergent."""
from __future__ import annotations

import logging

import httpx

from lotto_predictor.config import settings

logger = logging.getLogger(__name__)


def invia_notifica(
    messaggio: str,
    titolo: str = "Lotto Convergent",
    priorita: int = 3,
    topic: str | None = None,
) -> bool:
    """Invia una notifica push via ntfy.

    Args:
        messaggio: corpo del messaggio
        titolo: titolo della notifica
        priorita: priorita (1=min, 5=max, 3=default)
        topic: topic ntfy (usa config se non specificato)

    Returns:
        True se inviata con successo, False altrimenti
    """
    topic = topic or settings.ntfy_topic
    if not topic:
        logger.warning("NTFY_TOPIC non configurato, notifica non inviata")
        return False

    url = f"{settings.ntfy_server}/{topic}"

    try:
        response = httpx.post(
            url,
            content=messaggio.encode("utf-8"),
            headers={
                "Title": titolo,
                "Priority": str(priorita),
            },
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("Notifica inviata con successo a %s", url)
        return True
    except httpx.HTTPError as e:
        logger.error("Errore invio notifica ntfy: %s", e)
        return False


def notifica_previsioni(previsioni: list[dict], bankroll: float | None = None) -> bool:
    """Invia notifica con le previsioni pre-estrazione."""
    from lotto_predictor.notifier.formatter import formatta_previsioni

    messaggio = formatta_previsioni(previsioni, bankroll)
    # Priorita alta se ci sono previsioni con score >= 4
    priorita = 4 if any(p["score"] >= 4 for p in previsioni) else 3
    return invia_notifica(messaggio, titolo="Previsioni Lotto", priorita=priorita)


def notifica_esiti(esiti: list[dict], bankroll: float | None = None) -> bool:
    """Invia notifica con gli esiti post-estrazione."""
    from lotto_predictor.notifier.formatter import formatta_esiti

    messaggio = formatta_esiti(esiti, bankroll=bankroll)
    # Priorita massima se c'e' una vincita
    ha_vincita = any(e.get("stato") == "VINTA" for e in esiti)
    priorita = 5 if ha_vincita else 3
    titolo = "VINCITA Lotto!" if ha_vincita else "Esito Lotto"
    return invia_notifica(messaggio, titolo=titolo, priorita=priorita)


def notifica_test() -> bool:
    """Invia notifica di test."""
    return invia_notifica(
        "Notifica di test — il sistema funziona correttamente.",
        titolo="Test Lotto Convergent",
        priorita=2,
    )
