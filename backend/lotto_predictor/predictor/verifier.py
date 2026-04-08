from __future__ import annotations

"""Verifica previsioni — Lotto Convergent.

Confronta le previsioni attive con i risultati reali dell'estrazione
per determinare vincite e perdite.

Un ambo e VINTO quando entrambi i numeri della previsione compaiono
nei 5 numeri estratti sulla ruota prevista.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from lotto_predictor.config import settings

logger = logging.getLogger(__name__)


def verifica_previsioni(
    previsioni: list[dict],
    estrazione: dict[str, list[int]],
) -> list[dict]:
    """Confronta previsioni con estrazione reale.

    Per ogni previsione, verifica se l'ambo previsto e presente
    nei numeri estratti sulla ruota indicata.

    Args:
        previsioni: lista di dict con almeno:
            - 'ruota': str (nome ruota in maiuscolo)
            - 'ambo': tuple/list di 2 interi
            - 'score': int
            - 'colpo': int (numero del colpo corrente, 1-based)
            - 'max_colpi': int (massimo colpi del ciclo)
            Campi opzionali: 'metodo', 'filtri', 'posta'
        estrazione: dict {ruota: [n1, n2, n3, n4, n5]}
            I numeri estratti per ciascuna ruota.

    Returns:
        Lista di dict con la previsione originale arricchita con:
            - 'stato': 'VINTA' o 'IN_CORSO' o 'PERSA'
            - 'numeri_estratti': lista dei 5 numeri della ruota
            - 'vincita': float (importo vincita, 0 se persa)
            - 'ambo_trovato': bool
    """
    if not previsioni:
        logger.info("Nessuna previsione da verificare")
        return []

    risultati: list[dict] = []

    for prev in previsioni:
        ruota = prev["ruota"].upper()
        ambo = tuple(prev["ambo"])
        colpo = prev.get("colpo", 1)
        max_colpi = prev.get("max_colpi", settings.max_colpi)
        posta = prev.get("posta", settings.posta_default)

        # Cerca i numeri estratti per questa ruota
        numeri_estratti = estrazione.get(ruota)
        if numeri_estratti is None:
            logger.warning(
                "Ruota '%s' non trovata nell'estrazione, previsione saltata",
                ruota,
            )
            continue

        # Verifica se entrambi i numeri dell'ambo sono presenti
        set_estratti = set(numeri_estratti)
        ambo_trovato = ambo[0] in set_estratti and ambo[1] in set_estratti

        # Determina lo stato
        if ambo_trovato:
            stato = "VINTA"
            vincita = posta * settings.payout_ambo
        elif colpo >= max_colpi:
            # Ultimo colpo del ciclo, previsione persa definitivamente
            stato = "PERSA"
            vincita = 0.0
        else:
            # Non centrato ma ci sono ancora colpi disponibili
            stato = "IN_CORSO"
            vincita = 0.0

        risultato = {
            **prev,
            "stato": stato,
            "numeri_estratti": numeri_estratti,
            "vincita": vincita,
            "ambo_trovato": ambo_trovato,
            "colpo": colpo,
        }
        risultati.append(risultato)

        # Log dettagliato
        a, b = ambo
        if ambo_trovato:
            logger.info(
                "VINTA! Ambo %d-%d su %s (colpo %d, vincita E%.2f)",
                a,
                b,
                ruota,
                colpo,
                vincita,
            )
        else:
            logger.debug(
                "Non centrato: ambo %d-%d su %s (colpo %d/%d, estratti: %s)",
                a,
                b,
                ruota,
                colpo,
                max_colpi,
                numeri_estratti,
            )

    # Riepilogo
    vinte = sum(1 for r in risultati if r["stato"] == "VINTA")
    in_corso = sum(1 for r in risultati if r["stato"] == "IN_CORSO")
    perse = sum(1 for r in risultati if r["stato"] == "PERSA")
    logger.info(
        "Verifica completata: %d vinte, %d in corso, %d perse su %d previsioni",
        vinte,
        in_corso,
        perse,
        len(risultati),
    )

    return risultati


def verifica_previsioni_db(
    session: Session,
    estrazione: dict[str, list[int]],
    data_estrazione: date | None = None,
) -> list[dict]:
    """Verifica le previsioni attive dal database.

    Cerca tutte le previsioni con stato ATTIVA, le confronta
    con l'estrazione reale, e aggiorna lo stato nel database.

    Args:
        session: sessione SQLAlchemy attiva.
        estrazione: dict {ruota: [n1, n2, n3, n4, n5]}.
        data_estrazione: data dell'estrazione (default: oggi).

    Returns:
        Lista di dict con i risultati della verifica.
    """
    from sqlalchemy import select

    from lotto_predictor.models.database import Previsione

    oggi = data_estrazione or date.today()

    # Cerca previsioni attive
    stmt = select(Previsione).where(Previsione.stato == "ATTIVA")
    previsioni_db = session.scalars(stmt).all()

    if not previsioni_db:
        logger.info("Nessuna previsione attiva nel database")
        return []

    # Converti in formato dict per la verifica
    previsioni_dict: list[dict] = []
    for p in previsioni_db:
        # Calcola il colpo corrente (quante estrazioni dall'inizio)
        delta_giorni = (oggi - p.data_target_inizio).days
        # Approssimazione: circa 3 estrazioni a settimana
        colpo_stimato = max(1, (delta_giorni // 2) + 1)

        previsioni_dict.append(
            {
                "id": p.id,
                "ruota": p.ruota,
                "ambo": (p.num_a, p.num_b),
                "score": p.score,
                "colpo": min(colpo_stimato, p.max_colpi),
                "max_colpi": p.max_colpi,
                "posta": p.posta,
                "filtri": p.filtri.get("filtri", []) if p.filtri else [],
                "metodo": "convergenza",
            }
        )

    # Verifica
    risultati = verifica_previsioni(previsioni_dict, estrazione)

    # Aggiorna lo stato nel database
    for ris in risultati:
        if "id" not in ris:
            continue

        prev_db = session.get(Previsione, ris["id"])
        if prev_db is None:
            continue

        if ris["stato"] == "VINTA":
            prev_db.stato = "VINTA"
            prev_db.colpo_esito = ris["colpo"]
            prev_db.data_esito = oggi
            prev_db.vincita = ris["vincita"]
        elif ris["stato"] == "PERSA":
            prev_db.stato = "PERSA"
            prev_db.colpo_esito = ris["colpo"]
            prev_db.data_esito = oggi
            prev_db.vincita = 0.0
        # IN_CORSO: non aggiorniamo, resta ATTIVA

    session.flush()
    logger.info("Database aggiornato con esiti verifica")

    return risultati


def riepilogo_verifica(risultati: list[dict]) -> dict:
    """Genera un riepilogo statistico della verifica.

    Args:
        risultati: lista di risultati da verifica_previsioni.

    Returns:
        Dict con:
            - 'totale': numero totale previsioni verificate
            - 'vinte': numero vincite
            - 'perse': numero perdite
            - 'in_corso': numero ancora in gioco
            - 'vincita_totale': somma vincite
            - 'costo_totale': somma poste
            - 'profitto': vincita_totale - costo_totale
            - 'hit_rate': percentuale vincite su (vinte + perse)
    """
    vinte = [r for r in risultati if r["stato"] == "VINTA"]
    perse = [r for r in risultati if r["stato"] == "PERSA"]
    in_corso = [r for r in risultati if r["stato"] == "IN_CORSO"]

    vincita_totale = sum(r["vincita"] for r in vinte)
    costo_totale = sum(r.get("posta", settings.posta_default) for r in risultati)

    totale_chiuse = len(vinte) + len(perse)
    hit_rate = (len(vinte) / totale_chiuse * 100) if totale_chiuse > 0 else 0.0

    return {
        "totale": len(risultati),
        "vinte": len(vinte),
        "perse": len(perse),
        "in_corso": len(in_corso),
        "vincita_totale": vincita_totale,
        "costo_totale": costo_totale,
        "profitto": vincita_totale - costo_totale,
        "hit_rate": hit_rate,
    }
