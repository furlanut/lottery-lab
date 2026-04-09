from __future__ import annotations

"""Modelli database VinciCasa.

2 tabelle: vincicasa_estrazioni, vincicasa_previsioni.
Condivide il metadata (Base) col Lotto per coesistere nello stesso DB.
"""

from datetime import date, datetime
from typing import Optional

# Riusa Base dal Lotto per condividere il metadata (stesso DB)
from lotto_predictor.models.database import Base
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class VinciCasaEstrazione(Base):
    """Singola estrazione VinciCasa (5 numeri su 40, giornaliera)."""

    __tablename__ = "vincicasa_estrazioni"
    __table_args__ = (
        UniqueConstraint("concorso", name="uq_vc_concorso"),
        UniqueConstraint("data", name="uq_vc_data"),
        CheckConstraint("n1 BETWEEN 1 AND 40", name="ck_vc_n1"),
        CheckConstraint("n2 BETWEEN 1 AND 40", name="ck_vc_n2"),
        CheckConstraint("n3 BETWEEN 1 AND 40", name="ck_vc_n3"),
        CheckConstraint("n4 BETWEEN 1 AND 40", name="ck_vc_n4"),
        CheckConstraint("n5 BETWEEN 1 AND 40", name="ck_vc_n5"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concorso: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    n1: Mapped[int] = mapped_column(Integer, nullable=False)
    n2: Mapped[int] = mapped_column(Integer, nullable=False)
    n3: Mapped[int] = mapped_column(Integer, nullable=False)
    n4: Mapped[int] = mapped_column(Integer, nullable=False)
    n5: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @property
    def numeri(self) -> list[int]:
        """Ritorna i 5 numeri estratti come lista ordinata."""
        return sorted([self.n1, self.n2, self.n3, self.n4, self.n5])


class VinciCasaPrevisione(Base):
    """Previsione generata dal sistema per VinciCasa."""

    __tablename__ = "vincicasa_previsioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_generazione: Mapped[date] = mapped_column(Date, nullable=False)
    segnale: Mapped[str] = mapped_column(String(50), nullable=False)
    numeri: Mapped[dict] = mapped_column(JSONB, nullable=False)  # array di numeri
    score: Mapped[float] = mapped_column(Float, nullable=False)
    dettagli: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    stato: Mapped[str] = mapped_column(String(20), default="ATTIVA")
    data_esito: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    categoria_vincita: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
