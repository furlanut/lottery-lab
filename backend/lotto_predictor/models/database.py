from __future__ import annotations

"""Modelli database — Lotto Convergent.

4 tabelle: estrazioni, previsioni, bankroll, backtest_runs.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from lotto_predictor.config import settings


class Base(DeclarativeBase):
    """Classe base per tutti i modelli."""

    pass


class Estrazione(Base):
    """Singola estrazione di una ruota in un concorso."""

    __tablename__ = "estrazioni"
    __table_args__ = (UniqueConstraint("data", "ruota", name="uq_data_ruota"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concorso: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ruota: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
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
        """Ritorna i 5 numeri estratti come lista."""
        return [self.n1, self.n2, self.n3, self.n4, self.n5]


class Previsione(Base):
    """Previsione generata dal sistema."""

    __tablename__ = "previsioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_generazione: Mapped[date] = mapped_column(Date, nullable=False)
    data_target_inizio: Mapped[date] = mapped_column(Date, nullable=False)
    ruota: Mapped[str] = mapped_column(String(20), nullable=False)
    num_a: Mapped[int] = mapped_column(Integer, nullable=False)
    num_b: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    filtri: Mapped[dict] = mapped_column(JSONB, nullable=False)
    max_colpi: Mapped[int] = mapped_column(Integer, default=9)
    posta: Mapped[float] = mapped_column(Float, default=1.0)
    stato: Mapped[str] = mapped_column(String(20), default="ATTIVA")
    colpo_esito: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_esito: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vincita: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Bankroll(Base):
    """Registro movimenti bankroll."""

    __tablename__ = "bankroll"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    importo: Mapped[float] = mapped_column(Float, nullable=False)
    saldo: Mapped[float] = mapped_column(Float, nullable=False)
    previsione_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("previsioni.id"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class BacktestRun(Base):
    """Log esecuzioni backtesting."""

    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_run: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    parametri: Mapped[dict] = mapped_column(JSONB, nullable=False)
    train_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    train_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    risultati: Mapped[dict] = mapped_column(JSONB, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


def get_engine():
    """Crea engine SQLAlchemy."""
    return create_engine(settings.database_url, echo=settings.debug)


def get_session_factory():
    """Crea factory per le sessioni."""
    engine = get_engine()
    return sessionmaker(bind=engine)


def get_session() -> Session:
    """Ottiene una nuova sessione database."""
    factory = get_session_factory()
    return factory()


def init_db():
    """Crea tutte le tabelle nel database."""
    engine = get_engine()
    Base.metadata.create_all(engine)
