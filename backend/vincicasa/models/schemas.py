from __future__ import annotations

"""Pydantic schemas per validazione e serializzazione dati VinciCasa.

Range numeri: 1-40 (5 numeri estratti).
Nessuna dimensione ruota (gioco a estrazione unica).
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

# --- Estrazioni ---


class VCEstrazioneBase(BaseModel):
    """Schema base per un'estrazione VinciCasa."""

    concorso: int = Field(gt=0)
    data: date
    n1: int = Field(ge=1, le=40)
    n2: int = Field(ge=1, le=40)
    n3: int = Field(ge=1, le=40)
    n4: int = Field(ge=1, le=40)
    n5: int = Field(ge=1, le=40)

    @model_validator(mode="after")
    def numeri_distinti_e_ordinati(self) -> VCEstrazioneBase:
        """Verifica che i 5 numeri siano distinti e in ordine crescente."""
        nums = [self.n1, self.n2, self.n3, self.n4, self.n5]
        if len(set(nums)) != 5:
            msg = f"I 5 numeri devono essere distinti: {nums}"
            raise ValueError(msg)
        if nums != sorted(nums):
            msg = f"I numeri devono essere in ordine crescente: {nums}"
            raise ValueError(msg)
        return self


class VCEstrazioneCreate(VCEstrazioneBase):
    """Schema per creazione estrazione VinciCasa."""


class VCEstrazioneRead(VCEstrazioneBase):
    """Schema per lettura estrazione VinciCasa dal DB."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Previsioni ---


class VCPrevisioneBase(BaseModel):
    """Schema base per una previsione VinciCasa."""

    segnale: str = Field(min_length=1, max_length=50)
    numeri: list[int] = Field(min_length=1, max_length=5)
    score: float = Field(ge=0.0)
    dettagli: Optional[dict] = None

    @model_validator(mode="after")
    def numeri_validi(self) -> VCPrevisioneBase:
        """Verifica che i numeri siano nel range 1-40 e distinti."""
        for n in self.numeri:
            if n < 1 or n > 40:
                msg = f"Numero fuori range (1-40): {n}"
                raise ValueError(msg)
        if len(set(self.numeri)) != len(self.numeri):
            msg = f"Numeri non distinti: {self.numeri}"
            raise ValueError(msg)
        return self


class VCPrevisioneCreate(VCPrevisioneBase):
    """Schema per creazione previsione VinciCasa."""


class VCPrevisioneRead(VCPrevisioneBase):
    """Schema per lettura previsione VinciCasa dal DB."""

    id: int
    data_generazione: date
    stato: str
    data_esito: Optional[date] = None
    categoria_vincita: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
