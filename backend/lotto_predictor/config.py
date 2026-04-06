"""Configurazione centralizzata — Lotto Convergent."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurazione dell'applicazione, caricata da variabili d'ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://lotto:lotto@localhost:5432/lotto_convergent"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    debug: bool = False

    # JWT
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Scraper
    scraper_base_url: str = "https://www.archivioestrazionilotto.it"
    scraper_retry: int = 3
    scraper_delay: float = 2.0

    # Filtri
    filter_ritardo_soglia: int = 150
    filter_iso_lookback: int = 5
    filter_iso_min_repeat: int = 2
    filter_s91_ritardo_diametrale: int = 15

    # Scoring
    min_score_play: int = 3
    min_score_strong: int = 4

    # Money management
    posta_default: float = 1.0
    max_ambi_per_ciclo: int = 3
    max_colpi: int = 9
    payout_ambo: int = 250
    bankroll_iniziale: float = 600.0
    stop_loss: float = -750.0
    bankroll_min_play: float = 100.0

    # Notifiche
    ntfy_topic: str = ""
    ntfy_server: str = "https://ntfy.sh"

    # Scheduling
    giorni_estrazione: list[int] = [1, 3, 5]
    ora_previsione: str = "18:00"
    ora_verifica: str = "21:30"

    # Backtesting
    backtest_train_ratio: float = 0.7


settings = Settings()
