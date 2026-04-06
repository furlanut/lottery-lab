"""FastAPI application — Lotto Convergent.

API REST per accedere al sistema predittivo.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from sqlalchemy import func, select, text

from lotto_predictor.config import settings
from lotto_predictor.models.database import Estrazione, get_session
from lotto_predictor.models.schemas import HealthResponse

app = FastAPI(
    title="Lotto Convergent",
    description="Sistema predittivo per ambi secchi del Lotto Italiano",
    version="0.1.0",
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse)
def health_check():
    """Verifica stato di salute del sistema."""
    session = get_session()
    try:
        # Verifica connessione DB
        session.execute(text("SELECT 1"))
        db_status = "ok"

        # Conteggio estrazioni
        count = session.scalar(select(func.count(Estrazione.id))) or 0

        # Versione
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
