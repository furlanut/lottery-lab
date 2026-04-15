from __future__ import annotations

"""Modelli SQLAlchemy per 10eLotto ogni 5 minuti."""

from datetime import date, datetime, time
from typing import Optional

from lotto_predictor.models.database import Base
from sqlalchemy import (
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


class DiecieLottoEstrazione(Base):
    """Estrazione 10eLotto ogni 5 minuti."""

    __tablename__ = "diecielotto_estrazioni"
    __table_args__ = (UniqueConstraint("data", "ora", name="uq_del_data_ora"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concorso: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ora: Mapped[time] = mapped_column(Time, nullable=False)

    # 20 numeri estratti (ordinati)
    n1: Mapped[int] = mapped_column(Integer, nullable=False)
    n2: Mapped[int] = mapped_column(Integer, nullable=False)
    n3: Mapped[int] = mapped_column(Integer, nullable=False)
    n4: Mapped[int] = mapped_column(Integer, nullable=False)
    n5: Mapped[int] = mapped_column(Integer, nullable=False)
    n6: Mapped[int] = mapped_column(Integer, nullable=False)
    n7: Mapped[int] = mapped_column(Integer, nullable=False)
    n8: Mapped[int] = mapped_column(Integer, nullable=False)
    n9: Mapped[int] = mapped_column(Integer, nullable=False)
    n10: Mapped[int] = mapped_column(Integer, nullable=False)
    n11: Mapped[int] = mapped_column(Integer, nullable=False)
    n12: Mapped[int] = mapped_column(Integer, nullable=False)
    n13: Mapped[int] = mapped_column(Integer, nullable=False)
    n14: Mapped[int] = mapped_column(Integer, nullable=False)
    n15: Mapped[int] = mapped_column(Integer, nullable=False)
    n16: Mapped[int] = mapped_column(Integer, nullable=False)
    n17: Mapped[int] = mapped_column(Integer, nullable=False)
    n18: Mapped[int] = mapped_column(Integer, nullable=False)
    n19: Mapped[int] = mapped_column(Integer, nullable=False)
    n20: Mapped[int] = mapped_column(Integer, nullable=False)

    # Numero Oro = primo estratto, Doppio Oro = secondo estratto
    numero_oro: Mapped[int] = mapped_column(Integer, nullable=False)
    doppio_oro: Mapped[int] = mapped_column(Integer, nullable=False)

    # Extra: 15 numeri (nullable, potremmo non averli)
    extra_1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_4: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_5: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_6: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_7: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_8: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_9: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_10: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_11: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_12: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_13: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_14: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_15: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @property
    def numeri(self) -> list[int]:
        """Restituisce i 20 numeri estratti ordinati."""
        return sorted(
            [
                self.n1,
                self.n2,
                self.n3,
                self.n4,
                self.n5,
                self.n6,
                self.n7,
                self.n8,
                self.n9,
                self.n10,
                self.n11,
                self.n12,
                self.n13,
                self.n14,
                self.n15,
                self.n16,
                self.n17,
                self.n18,
                self.n19,
                self.n20,
            ]
        )

    @property
    def numeri_extra(self) -> list[int]:
        """Restituisce i numeri Extra ordinati (esclusi i None)."""
        extras = [
            self.extra_1,
            self.extra_2,
            self.extra_3,
            self.extra_4,
            self.extra_5,
            self.extra_6,
            self.extra_7,
            self.extra_8,
            self.extra_9,
            self.extra_10,
            self.extra_11,
            self.extra_12,
            self.extra_13,
            self.extra_14,
            self.extra_15,
        ]
        return sorted([x for x in extras if x is not None])


class DiecieLottoPrevisione(Base):
    """Previsione 10eLotto ogni 5 minuti."""

    __tablename__ = "diecielotto_previsioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_generazione: Mapped[date] = mapped_column(Date, nullable=False)
    ora_generazione: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    segnale: Mapped[str] = mapped_column(String(50), nullable=False)
    configurazione: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # quanti numeri giocati (1-10)
    numeri: Mapped[dict] = mapped_column(JSONB, nullable=False)
    opzioni: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # oro, doppio_oro, extra, gong
    score: Mapped[float] = mapped_column(Float, nullable=False)
    dettagli: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    stato: Mapped[str] = mapped_column(String(20), default="ATTIVA")
    data_esito: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vincita: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
