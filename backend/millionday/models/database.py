from __future__ import annotations

"""Modelli database MillionDay.

Tabelle:
- millionday_estrazioni: 5 numeri base su 55 + 5 numeri Extra dai 50 rimanenti
- millionday_previsioni: previsioni optfreq W=60

Pool: 1-55. Due estrazioni/giorno (13:00 e 20:30).
Condivide il metadata (Base) col Lotto per coesistere nello stesso DB.
"""

from datetime import date, datetime, time
from typing import Optional

from lotto_predictor.models.database import Base
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class MillionDayEstrazione(Base):
    """Singola estrazione MillionDay (5 base su 55 + 5 Extra dai 50 rimanenti)."""

    __tablename__ = "millionday_estrazioni"
    __table_args__ = (
        UniqueConstraint("data", "ora", name="uq_md_data_ora"),
        CheckConstraint("n1 BETWEEN 1 AND 55", name="ck_md_n1"),
        CheckConstraint("n2 BETWEEN 1 AND 55", name="ck_md_n2"),
        CheckConstraint("n3 BETWEEN 1 AND 55", name="ck_md_n3"),
        CheckConstraint("n4 BETWEEN 1 AND 55", name="ck_md_n4"),
        CheckConstraint("n5 BETWEEN 1 AND 55", name="ck_md_n5"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ora: Mapped[time] = mapped_column(Time, nullable=False)

    # 5 numeri base
    n1: Mapped[int] = mapped_column(Integer, nullable=False)
    n2: Mapped[int] = mapped_column(Integer, nullable=False)
    n3: Mapped[int] = mapped_column(Integer, nullable=False)
    n4: Mapped[int] = mapped_column(Integer, nullable=False)
    n5: Mapped[int] = mapped_column(Integer, nullable=False)

    # 5 numeri Extra (dai 50 rimanenti)
    e1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    e2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    e3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    e4: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    e5: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @property
    def numeri(self) -> list[int]:
        """Ritorna i 5 numeri base ordinati."""
        return sorted([self.n1, self.n2, self.n3, self.n4, self.n5])

    @property
    def numeri_extra(self) -> list[int]:
        """Ritorna i 5 numeri Extra ordinati (esclusi eventuali None)."""
        return sorted([x for x in [self.e1, self.e2, self.e3, self.e4, self.e5] if x is not None])


class MillionDayPrevisione(Base):
    """Previsione generata dal sistema per MillionDay (strategia optfreq W=60)."""

    __tablename__ = "millionday_previsioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_generazione: Mapped[date] = mapped_column(Date, nullable=False)
    ora_generazione: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    segnale: Mapped[str] = mapped_column(String(50), nullable=False)  # "optfreq_W60"
    numeri: Mapped[dict] = mapped_column(JSONB, nullable=False)  # 5 numeri giocati
    score: Mapped[float] = mapped_column(Float, nullable=False)  # ratio atteso
    dettagli: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    stato: Mapped[str] = mapped_column(String(20), default="ATTIVA")
    data_esito: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    match_base: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    match_extra: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vincita: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
