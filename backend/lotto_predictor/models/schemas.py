from __future__ import annotations

"""Pydantic schemas per validazione e serializzazione dati."""

from datetime import date, datetime

from pydantic import BaseModel, Field

# --- Estrazioni ---


class EstrazioneBase(BaseModel):
    """Schema base per un'estrazione."""

    concorso: int
    data: date
    ruota: str
    n1: int = Field(ge=1, le=90)
    n2: int = Field(ge=1, le=90)
    n3: int = Field(ge=1, le=90)
    n4: int = Field(ge=1, le=90)
    n5: int = Field(ge=1, le=90)


class EstrazioneRead(EstrazioneBase):
    """Schema per lettura estrazione dal DB."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Previsioni ---


class PrevisioneBase(BaseModel):
    """Schema base per una previsione."""

    ruota: str
    num_a: int = Field(ge=1, le=90)
    num_b: int = Field(ge=1, le=90)
    score: int = Field(ge=0, le=5)
    filtri: list[str]
    max_colpi: int = 9
    posta: float = 1.0


class PrevisioneRead(PrevisioneBase):
    """Schema per lettura previsione dal DB."""

    id: int
    data_generazione: date
    data_target_inizio: date
    stato: str
    colpo_esito: int | None = None
    data_esito: date | None = None
    vincita: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Bankroll ---


class BankrollRead(BaseModel):
    """Schema per lettura movimento bankroll."""

    id: int
    data: date
    tipo: str
    importo: float
    saldo: float
    previsione_id: int | None = None
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Status ---


class StatusResponse(BaseModel):
    """Risposta per il comando status."""

    bankroll_attuale: float
    pnl_totale: float
    previsioni_attive: int
    previsioni_vinte: int
    previsioni_perse: int
    hit_rate: float
    estrazioni_totali: int


# --- Health ---


class HealthResponse(BaseModel):
    """Risposta per health check."""

    status: str
    database: str
    estrazioni_count: int
    version: str
