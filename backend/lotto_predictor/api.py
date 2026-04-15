"""FastAPI application — Lotto Convergent.

API REST per accedere al sistema predittivo Lotto e VinciCasa.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

# Import VinciCasa and 10eLotto models to register them in the shared Base metadata
from diecielotto.models.database import DiecieLottoEstrazione, DiecieLottoPrevisione
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from vincicasa.models.database import VinciCasaEstrazione, VinciCasaPrevisione

from lotto_predictor.auth import VALID_PASS, VALID_USER, create_token, verify_token
from lotto_predictor.config import settings
from lotto_predictor.models.database import (
    Estrazione,
    Previsione,
    get_session,
)
from lotto_predictor.models.schemas import HealthResponse

logger = logging.getLogger(__name__)

ROME_TZ = ZoneInfo("Europe/Rome")

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class LottoEstrazioneOut(BaseModel):
    """Singola estrazione Lotto (una ruota)."""

    id: int
    concorso: int
    data: date
    ruota: str
    numeri: list[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class LottoStatusOut(BaseModel):
    """Stato complessivo del gioco Lotto."""

    estrazioni_totali: int
    data_prima: Optional[date] = None
    data_ultima: Optional[date] = None
    previsioni_attive: int = 0
    previsioni_vinte: int = 0
    previsioni_perse: int = 0


class LottoPrevisioneGenerata(BaseModel):
    """Previsione V6 generata al volo."""

    ambo_secco: Optional[dict] = None
    ambetti: list[dict] = Field(default_factory=list)
    costo_estrazione: int = 0
    costo_ciclo: int = 0
    testo: str = ""


class LottoPrevisioneOut(BaseModel):
    """Previsione Lotto storica dal DB."""

    id: int
    data_generazione: date
    data_target_inizio: date
    ruota: str
    num_a: int
    num_b: int
    score: int
    filtri: dict
    max_colpi: int
    posta: float
    stato: str
    colpo_esito: Optional[int] = None
    data_esito: Optional[date] = None
    vincita: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VinciCasaEstrazioneOut(BaseModel):
    """Singola estrazione VinciCasa."""

    id: int
    concorso: int
    data: date
    numeri: list[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class VinciCasaStatusOut(BaseModel):
    """Stato complessivo VinciCasa."""

    estrazioni_totali: int
    data_prima: Optional[date] = None
    data_ultima: Optional[date] = None


class VinciCasaPrevisioneGenerata(BaseModel):
    """Previsione VinciCasa generata al volo."""

    numeri: list[int]
    frequenze: dict[str, int] = Field(default_factory=dict)
    data_generazione: date
    finestra: int
    dettagli: str = ""
    testo: str = ""


class VinciCasaPrevisioneOut(BaseModel):
    """Previsione VinciCasa storica dal DB."""

    id: int
    data_generazione: date
    segnale: str
    numeri: dict  # JSONB
    score: float
    dettagli: Optional[dict] = None
    stato: str
    data_esito: Optional[date] = None
    categoria_vincita: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CalendarioEntry(BaseModel):
    """Singola data del calendario estrazioni."""

    gioco: str
    data: date
    giorno: str
    ora: str = "20:00"


class DashboardOut(BaseModel):
    """Overview combinata per la dashboard."""

    lotto: LottoStatusOut
    vincicasa: VinciCasaStatusOut
    prossime_estrazioni: list[CalendarioEntry]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Lotto Convergent",
    description="Sistema predittivo per ambi secchi del Lotto Italiano e VinciCasa",
    version="0.1.0",
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.api_prefix


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


@app.post(f"{PREFIX}/auth/login")
def login(body: dict) -> dict:
    """Login con credenziali hardcoded. Restituisce JWT Bearer token."""
    if body.get("username") == VALID_USER and body.get("password") == VALID_PASS:
        return {"token": create_token(VALID_USER), "username": VALID_USER}
    raise HTTPException(status_code=401, detail="Credenziali non valide")


@app.get(f"{PREFIX}/auth/me")
def auth_me(user: str = Depends(verify_token)) -> dict:
    """Restituisce l'utente corrente (richiede token valido)."""
    return {"username": user}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _segnale_to_dict(s) -> dict:
    """Converte un SegnaleV6 dataclass in dict serializzabile."""
    return {
        "ambo": list(s.ambo),
        "ruota": s.ruota,
        "score": round(s.score, 2),
        "metodo": s.metodo,
        "tipo_giocata": s.tipo_giocata,
        "frequenza": s.frequenza,
        "ritardo": s.ritardo,
        "dettagli": s.dettagli,
    }


def _prossime_estrazioni_lotto(n: int = 5) -> list[CalendarioEntry]:
    """Calcola le prossime N date di estrazione del Lotto (Mar/Gio/Sab)."""
    # Lotto: martedi=1, giovedi=3, sabato=5
    giorni_lotto = {1, 3, 5}
    now = datetime.now(ROME_TZ)
    oggi = now.date()
    # Se oggi e' giorno di estrazione e siamo prima delle 20:00, includiamolo
    risultati: list[CalendarioEntry] = []
    d = oggi
    if now.hour >= 20 and d.weekday() in giorni_lotto:
        d += timedelta(days=1)
    while len(risultati) < n:
        if d.weekday() in giorni_lotto:
            nome_giorno = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][d.weekday()]
            risultati.append(
                CalendarioEntry(
                    gioco="Lotto",
                    data=d,
                    giorno=nome_giorno,
                    ora="20:00",
                )
            )
        d += timedelta(days=1)
    return risultati


def _prossime_estrazioni_vincicasa(n: int = 5) -> list[CalendarioEntry]:
    """Calcola le prossime N date di estrazione VinciCasa (giornaliera)."""
    now = datetime.now(ROME_TZ)
    oggi = now.date()
    d = oggi
    if now.hour >= 20:
        d += timedelta(days=1)
    risultati: list[CalendarioEntry] = []
    while len(risultati) < n:
        nome_giorno = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][d.weekday()]
        risultati.append(
            CalendarioEntry(
                gioco="VinciCasa",
                data=d,
                giorno=nome_giorno,
                ora="20:00",
            )
        )
        d += timedelta(days=1)
    return risultati


def _lotto_status(session) -> LottoStatusOut:
    """Calcola lo status del Lotto da una sessione DB aperta."""
    count = session.scalar(select(func.count(Estrazione.id))) or 0
    date_min = session.scalar(select(func.min(Estrazione.data)))
    date_max = session.scalar(select(func.max(Estrazione.data)))

    attive = (
        session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "ATTIVA")) or 0
    )
    vinte = (
        session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "VINTA")) or 0
    )
    perse = (
        session.scalar(select(func.count(Previsione.id)).where(Previsione.stato == "PERSA")) or 0
    )

    return LottoStatusOut(
        estrazioni_totali=count,
        data_prima=date_min,
        data_ultima=date_max,
        previsioni_attive=attive,
        previsioni_vinte=vinte,
        previsioni_perse=perse,
    )


def _vincicasa_status(session) -> VinciCasaStatusOut:
    """Calcola lo status di VinciCasa da una sessione DB aperta."""
    count = session.scalar(select(func.count(VinciCasaEstrazione.id))) or 0
    date_min = session.scalar(select(func.min(VinciCasaEstrazione.data)))
    date_max = session.scalar(select(func.max(VinciCasaEstrazione.data)))

    return VinciCasaStatusOut(
        estrazioni_totali=count,
        data_prima=date_min,
        data_ultima=date_max,
    )


# ---------------------------------------------------------------------------
# General endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/health", response_model=HealthResponse)
def health_check():
    """Verifica stato di salute del sistema."""
    session = get_session()
    try:
        session.execute(text("SELECT 1"))
        db_status = "ok"

        count = session.scalar(select(func.count(Estrazione.id))) or 0

        version_file = Path(__file__).parent.parent.parent / "version.json"
        version = "0.1.0"
        if version_file.exists():
            with open(version_file) as f:
                version = json.load(f).get("version", version)

        return HealthResponse(
            status="ok",
            database=db_status,
            estrazioni_count=count,
            version=version,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Il servizio non e disponibile",
                    "details": [str(e)],
                    "request_id": "",
                }
            },
        ) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/dashboard", response_model=DashboardOut)
def dashboard():
    """Overview combinata per entrambi i giochi."""
    session = get_session()
    try:
        lotto = _lotto_status(session)
        vincicasa = _vincicasa_status(session)

        prossime = sorted(
            _prossime_estrazioni_lotto(3) + _prossime_estrazioni_vincicasa(3),
            key=lambda e: e.data,
        )[:5]

        return DashboardOut(
            lotto=lotto,
            vincicasa=vincicasa,
            prossime_estrazioni=prossime,
        )
    except Exception as e:
        logger.exception("Errore dashboard")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Calendario combinato
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/calendario", response_model=list[CalendarioEntry])
def calendario_combinato():
    """Prossime estrazioni per entrambi i giochi, ordinate per data."""
    entries = _prossime_estrazioni_lotto(5) + _prossime_estrazioni_vincicasa(5)
    entries.sort(key=lambda e: e.data)
    return entries[:10]


# ---------------------------------------------------------------------------
# Lotto endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/lotto/status", response_model=LottoStatusOut)
def lotto_status():
    """Stato complessivo del Lotto: conteggi e date."""
    session = get_session()
    try:
        return _lotto_status(session)
    except Exception as e:
        logger.exception("Errore lotto/status")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/lotto/estrazioni", response_model=list[LottoEstrazioneOut])
def lotto_estrazioni(limit: int = Query(10, ge=1, le=500)):
    """Ultime N estrazioni Lotto (tutte le ruote, ordinate per data desc)."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(Estrazione).order_by(Estrazione.data.desc(), Estrazione.ruota).limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            LottoEstrazioneOut(
                id=r.id,
                concorso=r.concorso,
                data=r.data,
                ruota=r.ruota,
                numeri=r.numeri,
                created_at=r.created_at,
            )
            for r in rows
        ]
    except Exception as e:
        logger.exception("Errore lotto/estrazioni")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/lotto/previsione", response_model=LottoPrevisioneGenerata)
def lotto_previsione():
    """Genera la previsione V6 corrente leggendo le estrazioni dal DB."""
    from lotto_predictor.analyzer.convergence_v6 import (
        formatta_giocata,
        genera_giocata_v6,
    )

    session = get_session()
    try:
        # Carica tutte le estrazioni ordinate per data
        rows = (
            session.execute(select(Estrazione).order_by(Estrazione.data, Estrazione.ruota))
            .scalars()
            .all()
        )

        if not rows:
            return LottoPrevisioneGenerata(testo="Nessuna estrazione disponibile nel DB")

        # Raggruppa per data: [(data_str, {ruota: [n1..n5]}), ...]
        grouped: dict[date, dict[str, list[int]]] = defaultdict(dict)
        for r in rows:
            grouped[r.data][r.ruota] = r.numeri

        dati = [(d.isoformat(), ruote) for d, ruote in sorted(grouped.items())]

        giocata = genera_giocata_v6(dati)
        testo = formatta_giocata(giocata)

        ambo_dict = _segnale_to_dict(giocata["ambo_secco"]) if giocata["ambo_secco"] else None
        ambetti_dict = [_segnale_to_dict(s) for s in giocata["ambetti"]]

        return LottoPrevisioneGenerata(
            ambo_secco=ambo_dict,
            ambetti=ambetti_dict,
            costo_estrazione=giocata["costo_estrazione"],
            costo_ciclo=giocata["costo_ciclo"],
            testo=testo,
        )
    except Exception as e:
        logger.exception("Errore lotto/previsione")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/lotto/previsioni", response_model=list[LottoPrevisioneOut])
def lotto_previsioni(limit: int = Query(20, ge=1, le=200)):
    """Lista delle previsioni Lotto storiche dal DB."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(Previsione).order_by(Previsione.data_generazione.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return [LottoPrevisioneOut.model_validate(r) for r in rows]
    except Exception as e:
        logger.exception("Errore lotto/previsioni")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/lotto/calendario", response_model=list[CalendarioEntry])
def lotto_calendario():
    """Prossime 5 date di estrazione del Lotto (Mar/Gio/Sab ore 20:00)."""
    return _prossime_estrazioni_lotto(5)


# ---------------------------------------------------------------------------
# VinciCasa endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/vincicasa/status", response_model=VinciCasaStatusOut)
def vincicasa_status():
    """Stato complessivo VinciCasa: conteggi e date."""
    session = get_session()
    try:
        return _vincicasa_status(session)
    except Exception as e:
        logger.exception("Errore vincicasa/status")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/vincicasa/estrazioni", response_model=list[VinciCasaEstrazioneOut])
def vincicasa_estrazioni(limit: int = Query(10, ge=1, le=500)):
    """Ultime N estrazioni VinciCasa ordinate per data desc."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            VinciCasaEstrazioneOut(
                id=r.id,
                concorso=r.concorso,
                data=r.data,
                numeri=r.numeri,
                created_at=r.created_at,
            )
            for r in rows
        ]
    except Exception as e:
        logger.exception("Errore vincicasa/estrazioni")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/vincicasa/previsione", response_model=VinciCasaPrevisioneGenerata)
def vincicasa_previsione():
    """Genera la previsione VinciCasa del giorno."""
    from vincicasa.engine import formatta_previsione, genera_previsione

    try:
        prev = genera_previsione()
        testo = formatta_previsione(prev)

        # Converti le chiavi int delle frequenze in str per JSON
        freq_str = {str(k): v for k, v in prev.frequenze.items()}

        return VinciCasaPrevisioneGenerata(
            numeri=prev.numeri,
            frequenze=freq_str,
            data_generazione=prev.data_generazione,
            finestra=prev.finestra,
            dettagli=prev.dettagli,
            testo=testo,
        )
    except Exception as e:
        logger.exception("Errore vincicasa/previsione")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(f"{PREFIX}/vincicasa/previsioni", response_model=list[VinciCasaPrevisioneOut])
def vincicasa_previsioni(limit: int = Query(20, ge=1, le=200)):
    """Lista delle previsioni VinciCasa storiche dal DB."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(VinciCasaPrevisione)
                .order_by(VinciCasaPrevisione.data_generazione.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [VinciCasaPrevisioneOut.model_validate(r) for r in rows]
    except Exception as e:
        logger.exception("Errore vincicasa/previsioni")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/vincicasa/calendario", response_model=list[CalendarioEntry])
def vincicasa_calendario():
    """Prossime 5 date di estrazione VinciCasa (giornaliera ore 20:00)."""
    return _prossime_estrazioni_vincicasa(5)


# ---------------------------------------------------------------------------
# 10eLotto endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/diecielotto/status")
def diecielotto_status():
    """Stato complessivo 10eLotto: conteggi e date."""
    session = get_session()
    try:
        count = session.scalar(select(func.count(DiecieLottoEstrazione.id))) or 0
        date_min = session.scalar(select(func.min(DiecieLottoEstrazione.data)))
        date_max = session.scalar(select(func.max(DiecieLottoEstrazione.data)))
        return {"estrazioni_totali": count, "data_prima": date_min, "data_ultima": date_max}
    finally:
        session.close()


@app.get(f"{PREFIX}/diecielotto/estrazioni")
def diecielotto_estrazioni(limit: int = Query(20, ge=1, le=500)):
    """Ultime N estrazioni 10eLotto ordinate per data desc."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoEstrazione)
                .order_by(DiecieLottoEstrazione.data.desc(), DiecieLottoEstrazione.ora.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "concorso": r.concorso,
                "data": r.data,
                "ora": str(r.ora),
                "numeri": r.numeri,
                "numero_oro": r.numero_oro,
                "doppio_oro": r.doppio_oro,
                "numeri_extra": r.numeri_extra,
            }
            for r in rows
        ]
    finally:
        session.close()


@app.get(f"{PREFIX}/diecielotto/previsione")
def diecielotto_previsione():
    """Genera la previsione 10eLotto corrente (S4 dual-target)."""
    from diecielotto.engine import formatta_previsione, genera_previsione

    prev = genera_previsione()
    return {
        "numeri": prev.numeri,
        "metodo": prev.metodo,
        "score": prev.score,
        "costo": prev.costo,
        "configurazione": prev.configurazione,
        "dettagli": prev.dettagli,
        "testo": formatta_previsione(prev),
    }


@app.get(f"{PREFIX}/diecielotto/previsioni")
def diecielotto_previsioni_storico(limit: int = Query(50, ge=1, le=500)):
    """Lista delle previsioni 10eLotto storiche dal DB."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(DiecieLottoPrevisione)
                .order_by(DiecieLottoPrevisione.data_generazione.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "data": r.data_generazione,
                "numeri": r.numeri,
                "segnale": r.segnale,
                "score": r.score,
                "stato": r.stato,
                "vincita": r.vincita,
            }
            for r in rows
        ]
    finally:
        session.close()


@app.get(f"{PREFIX}/diecielotto/storico-completo")
def diecielotto_storico_completo(limit: int = Query(100, ge=1, le=1000)):
    """Storico 10eLotto: ogni estrazione con previsione abbinata e P&L."""
    session = get_session()
    try:
        # Get all predictions ordered by date+ora
        preds = (
            session.execute(
                select(DiecieLottoPrevisione)
                .order_by(
                    DiecieLottoPrevisione.data_generazione.desc(),
                )
                .limit(limit)
            )
            .scalars()
            .all()
        )

        records = []
        premi_base = {3: 2.0, 4: 10.0, 5: 100.0, 6: 1000.0}
        premi_extra = {1: 1.0, 2: 1.0, 3: 7.0, 4: 20.0, 5: 200.0, 6: 2000.0}
        costo = 2.0

        for p in preds:
            numeri_prev = p.numeri if isinstance(p.numeri, list) else list(p.numeri)

            # Find matching extraction (by date+ora if available, else closest)
            estr_data = {}
            estr = None
            if p.ora_generazione:
                estr = session.execute(
                    select(DiecieLottoEstrazione).where(
                        DiecieLottoEstrazione.data == p.data_generazione,
                        DiecieLottoEstrazione.ora == p.ora_generazione,
                    )
                ).scalar_one_or_none()
            if estr is None and p.data_esito:
                # Fallback: find any extraction on the esito date
                estr = session.execute(
                    select(DiecieLottoEstrazione)
                    .where(DiecieLottoEstrazione.data == p.data_esito)
                    .order_by(DiecieLottoEstrazione.ora.desc())
                    .limit(1)
                ).scalar_one_or_none()
            if estr is None:
                # Last fallback: closest extraction to generation date
                estr = session.execute(
                    select(DiecieLottoEstrazione)
                    .where(DiecieLottoEstrazione.data == p.data_generazione)
                    .order_by(DiecieLottoEstrazione.ora.desc())
                    .limit(1)
                ).scalar_one_or_none()
                if estr:
                    pick = set(numeri_prev)
                    drawn = set(estr.numeri)
                    extra_set = set(estr.numeri_extra)
                    mb = len(pick & drawn)
                    rem = pick - drawn
                    me = len(rem & extra_set)
                    vb = premi_base.get(mb, 0.0)
                    ve = premi_extra.get(me, 0.0)
                    vincita = vb + ve

                    estr_data = {
                        "concorso": estr.concorso,
                        "data": str(estr.data),
                        "ora": str(estr.ora),
                        "numeri": estr.numeri,
                        "numero_oro": estr.numero_oro,
                        "doppio_oro": estr.doppio_oro,
                        "numeri_extra": estr.numeri_extra,
                        "match_base": mb,
                        "match_extra": me,
                        "numeri_azzeccati": sorted(pick & drawn),
                        "numeri_azzeccati_extra": sorted(rem & extra_set),
                        "vincita_base": vb,
                        "vincita_extra": ve,
                        "vincita_totale": vincita,
                        "pnl": vincita - costo,
                    }

            records.append(
                {
                    "previsione": {
                        "numeri": numeri_prev,
                        "metodo": p.segnale,
                        "score": p.score,
                        "stato": p.stato,
                    },
                    "estrazione": estr_data,
                    "costo": costo,
                }
            )

        return records
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Paper Trading endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/paper-trading/riepilogo")
def paper_trading_riepilogo():
    """P&L complessivo di tutti i giochi in paper trading."""
    from paper_trading.service import riepilogo

    return riepilogo()


@app.get(f"{PREFIX}/paper-trading/storico")
def paper_trading_storico(
    gioco: str = Query("all"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Storico cronologico delle giocate in paper trading."""
    from paper_trading.service import storico

    return storico(gioco=gioco, limit=limit)


@app.post(f"{PREFIX}/paper-trading/run")
def paper_trading_run(user: str = Depends(verify_token)):
    """Genera e salva le previsioni del giorno per tutti i giochi."""
    from paper_trading.service import (
        paper_trade_diecielotto,
        paper_trade_lotto,
        paper_trade_vincicasa,
    )

    return {
        "lotto": paper_trade_lotto(),
        "vincicasa": paper_trade_vincicasa(),
        "diecielotto": paper_trade_diecielotto(),
    }


@app.post(f"{PREFIX}/paper-trading/verifica")
def paper_trading_verifica(user: str = Depends(verify_token)):
    """Verifica le previsioni attive contro le ultime estrazioni."""
    from paper_trading.service import (
        verifica_diecielotto,
        verifica_lotto,
        verifica_vincicasa,
    )

    return {
        "lotto": verifica_lotto(),
        "vincicasa": verifica_vincicasa(),
        "diecielotto": verifica_diecielotto(),
    }
