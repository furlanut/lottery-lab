from __future__ import annotations

"""Pydantic schemas per 10eLotto ogni 5 minuti."""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class DiecieLottoEstrazioneBase(BaseModel):
    """Schema base per un'estrazione 10eLotto."""

    concorso: int
    data: date
    ora: time
    numeri: list[int] = Field(min_length=20, max_length=20)
    numero_oro: int = Field(ge=1, le=90)
    doppio_oro: int = Field(ge=1, le=90)
    numeri_extra: list[int] = Field(default_factory=list, max_length=15)


class DiecieLottoEstrazioneRead(DiecieLottoEstrazioneBase):
    """Schema di lettura per un'estrazione 10eLotto."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EVResult(BaseModel):
    """Risultato del calcolo Expected Value per una configurazione."""

    numeri_giocati: int
    opzione: str
    costo_totale: float
    ev_totale: float
    ev_per_euro: float
    house_edge_pct: float
    probabilita_vincita: float
    breakeven_ratio: float


class DiecieLottoStatusOut(BaseModel):
    """Output del comando status."""

    estrazioni_totali: int
    data_prima: Optional[date] = None
    data_ultima: Optional[date] = None
    estrazioni_oggi: int = 0
