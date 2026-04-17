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

# Import VinciCasa, 10eLotto, MillionDay models to register in the shared Base metadata
from diecielotto.models.database import DiecieLottoEstrazione, DiecieLottoPrevisione
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from millionday.models.database import MillionDayEstrazione
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


class MillionDayEstrazioneOut(BaseModel):
    """Singola estrazione MillionDay (5 base + 5 Extra su 55)."""

    id: int
    data: date
    ora: str  # "13:00" o "20:30"
    numeri: list[int]
    extra: list[int]
    created_at: datetime


class MillionDayStatusOut(BaseModel):
    """Stato complessivo MillionDay."""

    estrazioni_totali: int
    data_prima: Optional[date] = None
    data_ultima: Optional[date] = None


class MillionDayPrevisioneGenerata(BaseModel):
    """Previsione MillionDay generata al volo (optfreq W=60)."""

    numeri: list[int]
    frequenze: dict[str, int] = Field(default_factory=dict)
    expected: float = 0.0
    data_generazione: date
    finestra: int
    dettagli: str = ""
    testo: str = ""
    score: float = 1.343
    house_edge: float = 33.69


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


@app.get(f"{PREFIX}/lotto/storico-completo")
def lotto_storico_completo(limit: int = Query(50, ge=1, le=500)):
    """Storico Lotto retroattivo: previsione V6 vs estrazione per ogni data."""
    from collections import defaultdict

    from lotto_predictor.analyzer.convergence_v6 import genera_giocata_v6

    session = get_session()
    try:
        rows = (
            session.execute(select(Estrazione).order_by(Estrazione.data, Estrazione.ruota))
            .scalars()
            .all()
        )
        grouped: dict[date, dict[str, list[int]]] = defaultdict(dict)
        for r in rows:
            grouped[r.data][r.ruota] = r.numeri

        date_list = sorted(grouped.keys())
        dati = [(d.isoformat(), grouped[d]) for d in date_list]

        if len(dati) < 100:
            return []

        records = []
        start = max(100, len(dati) - limit)

        for idx in range(start, len(dati)):
            target_date = date_list[idx]
            dati_prima = dati[:idx]

            try:
                giocata = genera_giocata_v6(dati_prima)
            except Exception:  # noqa: S112
                continue

            ruote_giorno = grouped[target_date]

            for segnale in giocata.get("ambetti") or []:
                estratti = ruote_giorno.get(segnale.ruota, [])
                ambo = set(segnale.ambo)
                estratti_set = set(estratti)
                hit = ambo.issubset(estratti_set)
                # Ambetto check
                a, b = segnale.ambo
                ambetto_hit = False
                for n1 in estratti:
                    for n2 in estratti:
                        if (
                            n1 != n2
                            and not hit
                            and (
                                (abs(n1 - a) <= 1 and abs(n2 - b) <= 1)
                                or (abs(n1 - b) <= 1 and abs(n2 - a) <= 1)
                            )
                        ):
                            ambetto_hit = True

                vincita = 0.0
                if hit:
                    vincita = 250.0
                elif ambetto_hit:
                    vincita = 65.0

                records.append(
                    {
                        "data": str(target_date),
                        "previsione": {
                            "numeri": list(segnale.ambo),
                            "ruota": segnale.ruota,
                            "metodo": segnale.metodo,
                            "tipo": segnale.tipo_giocata,
                            "score": round(segnale.score, 2),
                        },
                        "estrazione": {
                            "numeri": estratti,
                            "ruota": segnale.ruota,
                        },
                        "match": 2 if hit else (1 if ambetto_hit else 0),
                        "vincita": vincita,
                        "costo": 1.0,
                        "pnl": vincita - 1.0,
                        "stato": ("AMBO" if hit else ("AMBETTO" if ambetto_hit else "PERSA")),
                    }
                )

            if giocata.get("ambo_secco"):
                s = giocata["ambo_secco"]
                estratti = ruote_giorno.get(s.ruota, [])
                hit = set(s.ambo).issubset(set(estratti))
                vincita = 250.0 if hit else 0.0
                records.append(
                    {
                        "data": str(target_date),
                        "previsione": {
                            "numeri": list(s.ambo),
                            "ruota": s.ruota,
                            "metodo": s.metodo,
                            "tipo": s.tipo_giocata,
                            "score": round(s.score, 2),
                        },
                        "estrazione": {
                            "numeri": estratti,
                            "ruota": s.ruota,
                        },
                        "match": 2 if hit else 0,
                        "vincita": vincita,
                        "costo": 1.0,
                        "pnl": vincita - 1.0,
                        "stato": "AMBO" if hit else "PERSA",
                    }
                )

        records.reverse()
        return records
    finally:
        session.close()


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


@app.get(f"{PREFIX}/vincicasa/storico-completo")
def vincicasa_storico_completo(limit: int = Query(30, ge=1, le=500)):
    """Storico VinciCasa retroattivo: top5 freq vs estrazione."""
    from collections import Counter

    session = get_session()
    try:
        all_estr = (
            session.execute(select(VinciCasaEstrazione).order_by(VinciCasaEstrazione.data))
            .scalars()
            .all()
        )

        if len(all_estr) < 6:
            return []

        premi = {5: 500000, 4: 200, 3: 20, 2: 2.60}
        costo = 2.0
        records = []
        start = max(5, len(all_estr) - limit)

        for i in range(start, len(all_estr)):
            # Top 5 frequenti nelle ultime 5 estrazioni
            freq = Counter()
            for j in range(max(0, i - 5), i):
                for n in all_estr[j].numeri:
                    freq[n] += 1
            top5 = sorted([n for n, _ in freq.most_common(5)])

            estr = all_estr[i]
            estratti = estr.numeri
            match = len(set(top5) & set(estratti))
            vincita = premi.get(match, 0.0)

            records.append(
                {
                    "data": str(estr.data),
                    "previsione": {
                        "numeri": top5,
                        "metodo": "top5_freq_N5",
                    },
                    "estrazione": {
                        "numeri": estratti,
                        "concorso": estr.concorso,
                    },
                    "match": match,
                    "vincita": vincita,
                    "costo": costo,
                    "pnl": vincita - costo,
                    "stato": (f"VINTA {match}/5" if vincita > 0 else f"PERSA ({match}/5)"),
                }
            )

        records.reverse()
        return records
    finally:
        session.close()


# ---------------------------------------------------------------------------
# MillionDay endpoints
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/millionday/status", response_model=MillionDayStatusOut)
def millionday_status():
    """Stato complessivo MillionDay: conteggi e date min/max."""
    session = get_session()
    try:
        count = session.scalar(select(func.count(MillionDayEstrazione.id))) or 0
        date_min = session.scalar(select(func.min(MillionDayEstrazione.data)))
        date_max = session.scalar(select(func.max(MillionDayEstrazione.data)))
        return MillionDayStatusOut(
            estrazioni_totali=count,
            data_prima=date_min,
            data_ultima=date_max,
        )
    except Exception as e:
        logger.exception("Errore millionday/status")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/millionday/estrazioni", response_model=list[MillionDayEstrazioneOut])
def millionday_estrazioni(limit: int = Query(20, ge=1, le=500)):
    """Ultime N estrazioni MillionDay ordinate per data+ora desc."""
    session = get_session()
    try:
        rows = (
            session.execute(
                select(MillionDayEstrazione)
                .order_by(MillionDayEstrazione.data.desc(), MillionDayEstrazione.ora.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            MillionDayEstrazioneOut(
                id=r.id,
                data=r.data,
                ora=r.ora.strftime("%H:%M"),
                numeri=r.numeri,
                extra=r.numeri_extra,
                created_at=r.created_at,
            )
            for r in rows
        ]
    except Exception as e:
        logger.exception("Errore millionday/estrazioni")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@app.get(f"{PREFIX}/millionday/previsione", response_model=MillionDayPrevisioneGenerata)
def millionday_previsione():
    """Genera la previsione MillionDay del prossimo turno (optfreq W=60 + Extra)."""
    from millionday.engine import (
        HE_TOTALE,
        SCORE_BACKTEST,
        formatta_previsione,
        genera_previsione,
    )

    try:
        prev = genera_previsione()
        testo = formatta_previsione(prev)
        # Keys int -> str per JSON
        freq_str = {str(k): v for k, v in prev.frequenze.items()}

        return MillionDayPrevisioneGenerata(
            numeri=prev.numeri,
            frequenze=freq_str,
            expected=prev.expected,
            data_generazione=prev.data_generazione,
            finestra=prev.finestra,
            dettagli=prev.dettagli,
            testo=testo,
            score=SCORE_BACKTEST,
            house_edge=HE_TOTALE,
        )
    except Exception as e:
        logger.exception("Errore millionday/previsione")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(f"{PREFIX}/millionday/calendario", response_model=list[CalendarioEntry])
def millionday_calendario():
    """Prossime estrazioni MillionDay (2/giorno: 13:00 e 20:30)."""
    now = datetime.now(ROME_TZ)
    oggi = now.date()
    risultati: list[CalendarioEntry] = []
    d = oggi
    nome_giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    while len(risultati) < 5:
        for ora_str, ora_time in [("13:00", (13, 0)), ("20:30", (20, 30))]:
            if d == oggi and (now.hour, now.minute) >= ora_time:
                continue
            risultati.append(
                CalendarioEntry(
                    gioco="MillionDay",
                    data=d,
                    giorno=nome_giorni[d.weekday()],
                    ora=ora_str,
                )
            )
            if len(risultati) >= 5:
                break
        d += timedelta(days=1)
    return risultati


@app.get(f"{PREFIX}/millionday/storico-completo")
def millionday_storico_completo(limit: int = Query(30, ge=1, le=500)):
    """Storico MillionDay retroattivo: optfreq W=60 vs estrazione reale.

    Per ogni estrazione cronologica a partire dall'indice W, genera la previsione
    con le 60 estrazioni precedenti e confronta con l'estrazione reale.
    Ritorna gli ultimi `limit` record (piu recenti prima).
    """
    from collections import Counter

    from millionday.engine import (
        COSTO_TOTALE,
        N_WINDOW,
        PREMI_BASE,
        PREMI_EXTRA,
    )

    session = get_session()
    try:
        all_estr = (
            session.execute(
                select(MillionDayEstrazione).order_by(
                    MillionDayEstrazione.data, MillionDayEstrazione.ora
                )
            )
            .scalars()
            .all()
        )

        if len(all_estr) < N_WINDOW + 1:
            return []

        records = []
        start = max(N_WINDOW, len(all_estr) - limit)

        for i in range(start, len(all_estr)):
            # optfreq W=60: top 5 con frequenza piu vicina all'attesa
            window = all_estr[i - N_WINDOW : i]
            freq = Counter()
            for e in window:
                for n in e.numeri:
                    freq[n] += 1
            expected = N_WINDOW * 5 / 55
            pick = sorted(
                range(1, 56),
                key=lambda x: (abs(freq.get(x, 0) - expected), x),
            )[:5]

            estr = all_estr[i]
            base = set(estr.numeri)
            extra = set(estr.numeri_extra)
            match_base = len(set(pick) & base)
            match_extra = len((set(pick) - base) & extra)
            v_base = PREMI_BASE.get(match_base, 0.0)
            v_extra = PREMI_EXTRA.get(match_extra, 0.0)
            vincita = v_base + v_extra
            pnl = vincita - COSTO_TOTALE

            stato = "VINTA" if vincita > 0 else "PERSA"
            cat = f"{match_base}/5"
            if match_extra > 0:
                cat += f" +{match_extra}E"

            records.append(
                {
                    "data": str(estr.data),
                    "ora": estr.ora.strftime("%H:%M"),
                    "previsione": {
                        "numeri": pick,
                        "metodo": "optfreq_W60",
                    },
                    "estrazione": {
                        "numeri": estr.numeri,
                        "extra": estr.numeri_extra,
                    },
                    "match_base": match_base,
                    "match_extra": match_extra,
                    "vincita_base": v_base,
                    "vincita_extra": v_extra,
                    "vincita": vincita,
                    "costo": COSTO_TOTALE,
                    "pnl": pnl,
                    "stato": f"{stato} {cat}",
                }
            )

        records.reverse()
        return records
    finally:
        session.close()


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


@app.get(f"{PREFIX}/diecielotto/metodi")
def diecielotto_metodi():
    """Lista dei metodi predittivi disponibili per K=6."""
    return [
        {
            "id": "vicinanza",
            "label": "Vicinanza D=5",
            "desc": "Seed + 5 vicini (1.080x)",
            "spiegazione": (
                "Identifica il numero piu frequente nelle ultime 100 estrazioni (il 'seed'), "
                "poi seleziona i 5 numeri piu vicini ad esso (distanza massima 5 posizioni) "
                "che sono anche frequenti. Produce una sestina di numeri raggruppati. "
                "Ratio backtest: 1.080x — il migliore per K=6. HE effettivo: 2.7%."
            ),
        },
        {
            "id": "dual_target",
            "label": "Dual Target",
            "desc": "3 hot base + 3 hot extra (1.059x)",
            "spiegazione": (
                "Divide i 6 numeri tra Base e Extra: 3 numeri piu frequenti nelle estrazioni "
                "base (20 numeri) + 3 numeri piu frequenti nelle estrazioni Extra (15 numeri), "
                "evitando sovrapposizioni. Sfrutta il fatto che Base e Extra hanno pool diversi. "
                "Ratio backtest: 1.059x."
            ),
        },
        {
            "id": "hot",
            "label": "Hot Numbers",
            "desc": "Top 6 frequenti (0.950x)",
            "spiegazione": (
                "Seleziona i 6 numeri che sono apparsi piu spesso nelle ultime 100 estrazioni. "
                "Strategia semplice e intuitiva. "
                "Ratio backtest: 0.950x — sotto baseline. Non consigliato."
            ),
        },
        {
            "id": "cold",
            "label": "Cold Numbers",
            "desc": "6 meno frequenti (0.990x)",
            "spiegazione": (
                "Seleziona i 6 numeri meno frequenti (piu 'freddi') nelle ultime 100 estrazioni. "
                "Basato sull'idea che i numeri in ritardo siano 'dovuti'. "
                "Ratio backtest: 0.990x — vicino a baseline ma non migliore."
            ),
        },
        {
            "id": "freq_rit_dec",
            "label": "Freq+Rit+Dec",
            "desc": "Frequenti in ritardo + decina (0.942x)",
            "spiegazione": (
                "Combina frequenza e ritardo: seleziona numeri che sono stati frequenti MA "
                "non sono usciti nelle ultime W/5 estrazioni, "
                "preferendo quelli nella stessa decina. "
                "Metodo derivato dal paper Lotto (vincitore per K=3). "
                "Ratio backtest: 0.942x per K=6."
            ),
        },
    ]


@app.get(f"{PREFIX}/diecielotto/storico-completo")
def diecielotto_storico_completo(
    limit: int = Query(500, ge=1, le=5000),
    metodo: str = Query("vicinanza"),
):
    """Storico 10eLotto K=6: retroattivo con metodo selezionabile."""
    from collections import Counter

    from diecielotto.ev_calculator import PREMI_BASE, PREMI_EXTRA

    session = get_session()
    try:
        all_estr = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )

        w = 100
        k = 6
        pb = PREMI_BASE.get(k, {})
        pe = PREMI_EXTRA.get(k, {})
        costo = 2.0

        if len(all_estr) < w + 1:
            return []

        start = max(w, len(all_estr) - limit)
        records = []

        for i in range(start, len(all_estr)):
            estr = all_estr[i]
            window = all_estr[max(0, i - w) : i]

            # Generate prediction with selected method
            freq = Counter()
            extra_freq = Counter()
            last_seen: dict[int, int] = {}
            for j, e in enumerate(window):
                for n in e.numeri:
                    freq[n] += 1
                    last_seen[n] = i - len(window) + j
                for n in e.numeri_extra:
                    extra_freq[n] += 1

            if metodo == "vicinanza":
                seed = freq.most_common(1)[0][0]
                nearby = sorted(
                    [
                        (n, freq.get(n, 0))
                        for n in range(1, 91)
                        if abs(n - seed) <= 5 and n != seed and freq.get(n, 0) > 0
                    ],
                    key=lambda x: -x[1],
                )
                pick_list = [seed]
                for n, _ in nearby:
                    pick_list.append(n)
                    if len(pick_list) >= k:
                        break
            elif metodo == "dual_target":
                hb = [n for n, _ in freq.most_common(k)][:3]
                he = [n for n, _ in extra_freq.most_common(20) if n not in hb][:3]
                pick_list = hb + he
            elif metodo == "cold":
                all_n = sorted(range(1, 91), key=lambda x: freq.get(x, 0))
                pick_list = all_n[:k]
            elif metodo == "freq_rit_dec":
                rit_soglia = len(window) // 5
                candidates = []
                for n in range(1, 91):
                    f = freq.get(n, 0)
                    ls = last_seen.get(n, -1)
                    rit = i - ls if ls >= 0 else len(window)
                    if f >= 3 and rit >= rit_soglia:
                        candidates.append((n, f + rit / len(window) * 3))
                candidates.sort(key=lambda x: -x[1])
                pick_list = [n for n, _ in candidates[:k]]
            else:  # hot (default fallback)
                pick_list = [n for n, _ in freq.most_common(k)]

            # Pad if needed
            if len(pick_list) < k:
                for n, _ in freq.most_common():
                    if n not in pick_list:
                        pick_list.append(n)
                    if len(pick_list) >= k:
                        break
            pick_list = sorted(pick_list[:k])

            # Verify
            pick_set = set(pick_list)
            drawn = set(estr.numeri)
            extra_set = set(estr.numeri_extra)
            mb = len(pick_set & drawn)
            rem = pick_set - drawn
            me = len(rem & extra_set)
            vb = pb.get(mb, 0.0)
            ve = pe.get(me, 0.0)
            vincita = vb + ve

            records.append(
                {
                    "previsione": {
                        "numeri": pick_list,
                        "metodo": metodo,
                        "score": 0,
                        "stato": "VINTA" if vincita > 0 else "PERSA",
                    },
                    "estrazione": {
                        "concorso": estr.concorso,
                        "data": str(estr.data),
                        "ora": str(estr.ora),
                        "numeri": estr.numeri,
                        "numero_oro": estr.numero_oro,
                        "doppio_oro": estr.doppio_oro,
                        "numeri_extra": estr.numeri_extra,
                        "match_base": mb,
                        "match_extra": me,
                        "numeri_azzeccati": sorted(pick_set & drawn),
                        "numeri_azzeccati_extra": sorted(rem & extra_set),
                        "vincita_base": vb,
                        "vincita_extra": ve,
                        "vincita_totale": vincita,
                        "pnl": vincita - costo,
                    },
                    "costo": costo,
                }
            )

        records.reverse()
        return records
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 10eLotto K numeri (parametrico, K=1-10)
# ---------------------------------------------------------------------------


@app.get(f"{PREFIX}/diecielotto-k/previsione")
def diecielotto_k_previsione(k: int = Query(6, ge=1, le=10)):
    """Genera previsione 10eLotto con K numeri (motore ottimale)."""
    from diecielotto.engine_k import STRATEGY_NAMES, calcola_he, genera_previsione_k

    session = get_session()
    try:
        all_estr = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )
        pick = genera_previsione_k(k, all_estr)
        he = calcola_he(k)
        strategy = STRATEGY_NAMES.get(k, "dual_target")
        return {
            "numeri": pick,
            "metodo": strategy,
            "configurazione": k,
            "costo": 2.0,
            "he": round(he, 2),
            "dettagli": f"{strategy} W=100 (motore ottimale)",
        }
    finally:
        session.close()


@app.get(f"{PREFIX}/diecielotto-k/storico")
def diecielotto_k_storico(
    k: int = Query(6, ge=1, le=10),
    limit: int = Query(500, ge=1, le=5000),
):
    """Storico retroattivo 10eLotto con K numeri e P&L (motore ottimale)."""
    from diecielotto.engine_k import (
        STRATEGY_NAMES,
        genera_previsione_k,
        verifica_previsione_k,
    )

    session = get_session()
    try:
        all_estr = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )

        w = 100
        if len(all_estr) < w + 1:
            return []

        start = max(w, len(all_estr) - limit)
        records = []

        for i in range(start, len(all_estr)):
            estr = all_estr[i]
            pick = genera_previsione_k(k, all_estr[:i])
            result = verifica_previsione_k(k, pick, estr.numeri, estr.numeri_extra)

            records.append(
                {
                    "previsione": {
                        "numeri": pick,
                        "metodo": STRATEGY_NAMES.get(k, "dual_target"),
                        "configurazione": k,
                    },
                    "estrazione": {
                        "concorso": estr.concorso,
                        "data": str(estr.data),
                        "ora": str(estr.ora),
                        "numeri": estr.numeri,
                        "numero_oro": estr.numero_oro,
                        "doppio_oro": estr.doppio_oro,
                        "numeri_extra": estr.numeri_extra,
                        "match_base": result["match_base"],
                        "match_extra": result["match_extra"],
                        "numeri_azzeccati": result["numeri_azzeccati"],
                        "numeri_azzeccati_extra": result["numeri_azzeccati_extra"],
                        "vincita_base": result["vincita_base"],
                        "vincita_extra": result["vincita_extra"],
                        "vincita_totale": result["vincita_totale"],
                        "pnl": result["pnl"],
                    },
                    "costo": 2.0,
                }
            )

        records.reverse()
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
