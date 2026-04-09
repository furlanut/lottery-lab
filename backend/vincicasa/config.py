from __future__ import annotations

"""Configurazione VinciCasa.

Parametri di gioco, premi, scraper e notifiche.
Tutte le variabili d'ambiente usano il prefisso VC_.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class VinciCasaSettings(BaseSettings):
    """Configurazione VinciCasa, caricata da variabili d'ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VC_",
        case_sensitive=False,
    )

    # Gioco
    numeri_totali: int = 40
    numeri_estratti: int = 5

    # Premi (euro)
    premio_5su5: float = 500_000.0  # di cui 300k vincolati a immobile
    premio_4su5: float = 200.0
    premio_3su5: float = 20.0
    premio_2su5: float = 2.60
    costo_giocata: float = 2.0

    # Scraper
    scraper_url: str = "https://www.vincicasa.it"
    scraper_retry: int = 3
    scraper_delay: float = 2.0

    # Notifiche
    ntfy_topic: str = ""


vc_settings = VinciCasaSettings()
