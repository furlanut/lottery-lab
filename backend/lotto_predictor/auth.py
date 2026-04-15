"""JWT authentication — Lotto Convergent.

Single-user hardcoded credentials, HS256 token, 24 h expiry.
Uses python-jose (already in project dependencies).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

SECRET_KEY = os.environ.get("JWT_SECRET", "lottery-lab-secret-2026-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

VALID_USER = "Luca"
VALID_PASS = "LucaLott2026!?"

security = HTTPBearer(auto_error=False)


def create_token(username: str) -> str:
    """Crea un JWT firmato per l'utente dato."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Valida il Bearer token e restituisce l'username.

    Raise 401 se mancante, scaduto o non valido.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token mancante")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token scaduto") from exc
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token non valido") from exc
