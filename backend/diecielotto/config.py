from __future__ import annotations

"""Configurazione 10eLotto ogni 5 minuti.

Parametri di gioco, premi, scraper e notifiche.
Tutte le variabili d'ambiente usano il prefisso DEL_.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DiecieLottoSettings(BaseSettings):
    """Configurazione 10eLotto ogni 5 minuti, caricata da variabili d'ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DEL_",
        case_sensitive=False,
    )

    # Gioco
    numeri_totali: int = 90
    numeri_estratti: int = 20
    numeri_giocabili_min: int = 1
    numeri_giocabili_max: int = 10
    numeri_extra: int = 15

    # Posta
    posta_minima: float = 1.0
    posta_incremento: float = 0.50
    vincita_massima: float = 6_000_000.0

    # Estrazioni
    estrazioni_al_giorno: int = 288
    intervallo_minuti: int = 5

    # Scraper
    scraper_url: str = "https://www.lottologia.com/10elotto5minuti/"
    scraper_retry: int = 3
    scraper_delay: float = 1.0

    # Notifiche
    ntfy_topic: str = ""


del_settings = DiecieLottoSettings()
