"""Central paper trading service for all lottery games."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Optional

from diecielotto.models.database import DiecieLottoEstrazione, DiecieLottoPrevisione
from lotto_predictor.models.database import Estrazione, Previsione, get_session
from sqlalchemy import func, select
from vincicasa.models.database import VinciCasaEstrazione, VinciCasaPrevisione

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generate & Save
# ---------------------------------------------------------------------------


def paper_trade_lotto(session: Optional[object] = None) -> dict:
    """Generate Lotto V6 prediction, save to DB, return summary."""
    from lotto_predictor.analyzer.convergence_v6 import genera_giocata_v6

    own = session is None
    if own:
        session = get_session()
    try:
        rows = (
            session.execute(select(Estrazione).order_by(Estrazione.data, Estrazione.ruota))
            .scalars()
            .all()
        )
        grouped: dict = defaultdict(dict)
        for r in rows:
            grouped[r.data][r.ruota] = r.numeri
        dati = [(d.isoformat(), ruote) for d, ruote in sorted(grouped.items())]

        giocata = genera_giocata_v6(dati)

        saved = []
        today = date.today()
        for segnale in giocata.get("ambetti", []):
            p = Previsione(
                data_generazione=today,
                data_target_inizio=today,
                ruota=segnale.ruota,
                num_a=segnale.ambo[0],
                num_b=segnale.ambo[1],
                score=int(segnale.score),
                filtri={
                    "metodo": segnale.metodo,
                    "tipo": segnale.tipo_giocata,
                    "dettagli": segnale.dettagli,
                },
                max_colpi=9,
                posta=1.0,
                stato="ATTIVA",
            )
            session.merge(p)
            saved.append(
                {
                    "ruota": segnale.ruota,
                    "ambo": list(segnale.ambo),
                    "tipo": segnale.tipo_giocata,
                }
            )

        if giocata.get("ambo_secco"):
            s = giocata["ambo_secco"]
            p = Previsione(
                data_generazione=today,
                data_target_inizio=today,
                ruota=s.ruota,
                num_a=s.ambo[0],
                num_b=s.ambo[1],
                score=int(s.score),
                filtri={"metodo": s.metodo, "tipo": s.tipo_giocata, "dettagli": s.dettagli},
                max_colpi=9,
                posta=1.0,
                stato="ATTIVA",
            )
            session.merge(p)
            saved.append({"ruota": s.ruota, "ambo": list(s.ambo), "tipo": s.tipo_giocata})

        session.commit()
        return {"gioco": "lotto", "previsioni_salvate": len(saved), "dettagli": saved}
    except Exception as e:
        session.rollback()
        log.error("Errore paper_trade_lotto: %s", e)
        return {"gioco": "lotto", "errore": str(e)}
    finally:
        if own:
            session.close()


def paper_trade_vincicasa(session: Optional[object] = None) -> dict:
    """Generate VinciCasa prediction, save to DB."""
    from vincicasa.engine import genera_previsione as vc_genera

    own = session is None
    if own:
        session = get_session()
    try:
        prev = vc_genera(session)
        today = date.today()

        existing = session.scalar(
            select(func.count(VinciCasaPrevisione.id)).where(
                VinciCasaPrevisione.data_generazione == today
            )
        )
        if existing and existing > 0:
            return {"gioco": "vincicasa", "msg": "Previsione già esistente per oggi"}

        p = VinciCasaPrevisione(
            data_generazione=today,
            segnale="top5_freq_N5",
            numeri=prev.numeri,
            score=1.22,
            dettagli={
                "metodo": "top5_freq",
                "finestra": prev.finestra,
                "frequenze": dict(prev.frequenze),
            },
            stato="ATTIVA",
        )
        session.add(p)
        session.commit()
        return {"gioco": "vincicasa", "numeri": prev.numeri, "salvata": True}
    except Exception as e:
        session.rollback()
        log.error("Errore paper_trade_vincicasa: %s", e)
        return {"gioco": "vincicasa", "errore": str(e)}
    finally:
        if own:
            session.close()


def paper_trade_diecielotto(session: Optional[object] = None) -> dict:
    """Generate 10eLotto prediction, save to DB."""
    from diecielotto.engine import genera_previsione as del_genera

    own = session is None
    if own:
        session = get_session()
    try:
        prev = del_genera(session)
        today = date.today()

        p = DiecieLottoPrevisione(
            data_generazione=today,
            segnale="S4_dual_target",
            configurazione=6,
            numeri=prev.numeri,
            opzioni={"extra": True},
            score=prev.score,
            dettagli={"metodo": prev.metodo, "info": prev.dettagli},
            stato="ATTIVA",
        )
        session.add(p)
        session.commit()
        return {"gioco": "diecielotto", "numeri": prev.numeri, "salvata": True}
    except Exception as e:
        session.rollback()
        log.error("Errore paper_trade_diecielotto: %s", e)
        return {"gioco": "diecielotto", "errore": str(e)}
    finally:
        if own:
            session.close()


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def verifica_lotto(session: Optional[object] = None) -> list[dict]:
    """Verify active Lotto predictions against latest extraction."""
    own = session is None
    if own:
        session = get_session()
    try:
        latest_date = session.scalar(select(func.max(Estrazione.data)))
        if not latest_date:
            return []

        estrazioni = (
            session.execute(select(Estrazione).where(Estrazione.data == latest_date))
            .scalars()
            .all()
        )
        ruote = {e.ruota: e.numeri for e in estrazioni}

        attive = (
            session.execute(select(Previsione).where(Previsione.stato == "ATTIVA")).scalars().all()
        )

        esiti = []
        for p in attive:
            estratti = ruote.get(p.ruota, [])
            if not estratti:
                continue

            ambo = {p.num_a, p.num_b}
            hit = ambo.issubset(set(estratti))

            ambetto_hit = False
            for n in estratti:
                for m in estratti:
                    if n != m and (
                        {n, m} == ambo
                        or {n, m} == {p.num_a + 1, p.num_b}
                        or {n, m} == {p.num_a - 1, p.num_b}
                        or {n, m} == {p.num_a, p.num_b + 1}
                        or {n, m} == {p.num_a, p.num_b - 1}
                    ):
                        ambetto_hit = True

            if p.data_target_inizio:
                days = (latest_date - p.data_target_inizio).days
                colpo = max(1, days // 2)
            else:
                colpo = 1

            vincita = 0.0
            tipo = p.filtri.get("tipo", "ambetto") if isinstance(p.filtri, dict) else "ambetto"

            if hit:
                vincita = 250.0 * p.posta if tipo == "ambo_secco" else 65.0 * p.posta
                p.stato = "VINTA"
                p.vincita = vincita
                p.data_esito = latest_date
                p.colpo_esito = colpo
            elif ambetto_hit and tipo == "ambetto":
                vincita = 65.0 * p.posta
                p.stato = "VINTA"
                p.vincita = vincita
                p.data_esito = latest_date
                p.colpo_esito = colpo
            elif colpo >= p.max_colpi:
                p.stato = "PERSA"
                p.data_esito = latest_date
                p.colpo_esito = colpo

            esiti.append(
                {
                    "ruota": p.ruota,
                    "ambo": [p.num_a, p.num_b],
                    "stato": p.stato,
                    "vincita": vincita,
                    "colpo": colpo,
                }
            )

        session.commit()
        return esiti
    except Exception as e:
        session.rollback()
        log.error("Errore verifica_lotto: %s", e)
        return []
    finally:
        if own:
            session.close()


def verifica_vincicasa(session: Optional[object] = None) -> list[dict]:
    """Verify active VinciCasa predictions."""
    own = session is None
    if own:
        session = get_session()
    try:
        latest_date = session.scalar(select(func.max(VinciCasaEstrazione.data)))
        if not latest_date:
            return []

        estrazione = session.execute(
            select(VinciCasaEstrazione).where(VinciCasaEstrazione.data == latest_date)
        ).scalar_one_or_none()
        if not estrazione:
            return []

        estratti = set(estrazione.numeri)
        premi = {5: 500000, 4: 200, 3: 20, 2: 2.60}

        attive = (
            session.execute(
                select(VinciCasaPrevisione).where(VinciCasaPrevisione.stato == "ATTIVA")
            )
            .scalars()
            .all()
        )

        esiti = []
        for p in attive:
            numeri_prev = p.numeri if isinstance(p.numeri, list) else list(p.numeri)
            match = len(set(numeri_prev) & estratti)
            vincita = premi.get(match, 0.0)

            p.stato = "VINTA" if vincita > 0 else "PERSA"
            p.data_esito = latest_date
            p.categoria_vincita = match if match >= 2 else None

            esiti.append(
                {
                    "numeri": numeri_prev,
                    "match": match,
                    "stato": p.stato,
                    "vincita": vincita,
                }
            )

        session.commit()
        return esiti
    except Exception as e:
        session.rollback()
        log.error("Errore verifica_vincicasa: %s", e)
        return []
    finally:
        if own:
            session.close()


def verifica_diecielotto(session: Optional[object] = None) -> list[dict]:
    """Verify active 10eLotto predictions."""
    from diecielotto.engine import verifica_previsione

    own = session is None
    if own:
        session = get_session()
    try:
        latest = session.execute(
            select(DiecieLottoEstrazione)
            .order_by(DiecieLottoEstrazione.data.desc(), DiecieLottoEstrazione.ora.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not latest:
            return []

        attive = (
            session.execute(
                select(DiecieLottoPrevisione).where(DiecieLottoPrevisione.stato == "ATTIVA")
            )
            .scalars()
            .all()
        )

        esiti = []
        for p in attive:
            numeri = p.numeri if isinstance(p.numeri, list) else list(p.numeri)
            result = verifica_previsione(numeri, latest.numeri, latest.numeri_extra)

            vincita = result["vincita_totale"]
            p.stato = "VINTA" if vincita > 0 else "PERSA"
            p.data_esito = latest.data
            p.vincita = vincita

            esiti.append(
                {
                    "numeri": numeri,
                    "match_base": result["match_base"],
                    "match_extra": result["match_extra"],
                    "vincita": vincita,
                    "stato": p.stato,
                }
            )

        session.commit()
        return esiti
    except Exception as e:
        session.rollback()
        log.error("Errore verifica_diecielotto: %s", e)
        return []
    finally:
        if own:
            session.close()


# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------


def riepilogo(session: Optional[object] = None) -> dict:
    """P&L summary for all games."""
    own = session is None
    if own:
        session = get_session()
    try:
        result: dict = {"giochi": {}, "totale": {}}

        # Lotto
        _lq = select(func.count(Previsione.id))
        lotto_vinte = session.scalar(_lq.where(Previsione.stato == "VINTA")) or 0
        lotto_perse = session.scalar(_lq.where(Previsione.stato == "PERSA")) or 0
        lotto_attive = session.scalar(_lq.where(Previsione.stato == "ATTIVA")) or 0
        lotto_vincite_sum = (
            session.scalar(
                select(func.coalesce(func.sum(Previsione.vincita), 0)).where(
                    Previsione.stato == "VINTA"
                )
            )
            or 0
        )
        lotto_tot = lotto_vinte + lotto_perse
        lotto_giocato = lotto_tot * 1.0

        result["giochi"]["lotto"] = {
            "giocate": lotto_tot,
            "attive": lotto_attive,
            "vinte": lotto_vinte,
            "perse": lotto_perse,
            "totale_giocato": lotto_giocato,
            "totale_vinto": float(lotto_vincite_sum),
            "pnl": float(lotto_vincite_sum) - lotto_giocato,
            "hit_rate": lotto_vinte / lotto_tot * 100 if lotto_tot > 0 else 0,
        }

        # VinciCasa
        _vcq = select(func.count(VinciCasaPrevisione.id))
        vc_vinte = session.scalar(_vcq.where(VinciCasaPrevisione.stato == "VINTA")) or 0
        vc_perse = session.scalar(_vcq.where(VinciCasaPrevisione.stato == "PERSA")) or 0
        vc_attive = session.scalar(_vcq.where(VinciCasaPrevisione.stato == "ATTIVA")) or 0
        vc_tot = vc_vinte + vc_perse
        vc_giocato = vc_tot * 2.0

        vc_vincite = 0.0
        vc_rows = (
            session.execute(
                select(VinciCasaPrevisione.categoria_vincita).where(
                    VinciCasaPrevisione.stato == "VINTA"
                )
            )
            .scalars()
            .all()
        )
        premi_vc = {5: 500000, 4: 200, 3: 20, 2: 2.60}
        for cat in vc_rows:
            vc_vincite += premi_vc.get(cat, 0)

        result["giochi"]["vincicasa"] = {
            "giocate": vc_tot,
            "attive": vc_attive,
            "vinte": vc_vinte,
            "perse": vc_perse,
            "totale_giocato": vc_giocato,
            "totale_vinto": vc_vincite,
            "pnl": vc_vincite - vc_giocato,
            "hit_rate": vc_vinte / vc_tot * 100 if vc_tot > 0 else 0,
        }

        # 10eLotto
        del_vinte = (
            session.scalar(
                select(func.count(DiecieLottoPrevisione.id)).where(
                    DiecieLottoPrevisione.stato == "VINTA"
                )
            )
            or 0
        )
        del_perse = (
            session.scalar(
                select(func.count(DiecieLottoPrevisione.id)).where(
                    DiecieLottoPrevisione.stato == "PERSA"
                )
            )
            or 0
        )
        del_attive = (
            session.scalar(
                select(func.count(DiecieLottoPrevisione.id)).where(
                    DiecieLottoPrevisione.stato == "ATTIVA"
                )
            )
            or 0
        )
        del_tot = del_vinte + del_perse
        del_giocato = del_tot * 2.0
        del_vincite = (
            session.scalar(
                select(func.coalesce(func.sum(DiecieLottoPrevisione.vincita), 0)).where(
                    DiecieLottoPrevisione.stato == "VINTA"
                )
            )
            or 0
        )

        result["giochi"]["diecielotto"] = {
            "giocate": del_tot,
            "attive": del_attive,
            "vinte": del_vinte,
            "perse": del_perse,
            "totale_giocato": del_giocato,
            "totale_vinto": float(del_vincite),
            "pnl": float(del_vincite) - del_giocato,
            "hit_rate": del_vinte / del_tot * 100 if del_tot > 0 else 0,
        }

        # Totale
        tot_giocato = lotto_giocato + vc_giocato + del_giocato
        tot_vinto = float(lotto_vincite_sum) + vc_vincite + float(del_vincite)
        result["totale"] = {
            "totale_giocato": tot_giocato,
            "totale_vinto": tot_vinto,
            "pnl": tot_vinto - tot_giocato,
            "roi": (tot_vinto - tot_giocato) / tot_giocato * 100 if tot_giocato > 0 else 0,
        }

        return result
    finally:
        if own:
            session.close()


def storico(gioco: str = "all", limit: int = 100, session: Optional[object] = None) -> list[dict]:
    """Get chronological history of paper trades."""
    own = session is None
    if own:
        session = get_session()
    try:
        records: list[dict] = []

        if gioco in ("all", "vincicasa"):
            vc_preds = (
                session.execute(
                    select(VinciCasaPrevisione)
                    .order_by(VinciCasaPrevisione.data_generazione.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            for p in vc_preds:
                estr = session.execute(
                    select(VinciCasaEstrazione).where(
                        VinciCasaEstrazione.data == p.data_generazione
                    )
                ).scalar_one_or_none()

                records.append(
                    {
                        "data": str(p.data_generazione),
                        "gioco": "vincicasa",
                        "previsione": {
                            "numeri": p.numeri if isinstance(p.numeri, list) else list(p.numeri),
                            "metodo": p.segnale,
                        },
                        "estrazione": {"numeri": estr.numeri if estr else []},
                        "match": p.categoria_vincita or 0,
                        "stato": p.stato,
                        "costo": 2.0,
                        "vincita": {5: 500000, 4: 200, 3: 20, 2: 2.60}.get(p.categoria_vincita, 0)
                        if p.categoria_vincita
                        else 0,
                    }
                )

        if gioco in ("all", "diecielotto"):
            del_preds = (
                session.execute(
                    select(DiecieLottoPrevisione)
                    .order_by(DiecieLottoPrevisione.data_generazione.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            for p in del_preds:
                # Find matching extraction
                det = p.dettagli if isinstance(p.dettagli, dict) else {}
                ora_gen = p.ora_generazione
                estr_data: dict = {}
                if ora_gen:
                    estr = session.execute(
                        select(DiecieLottoEstrazione).where(
                            DiecieLottoEstrazione.data == p.data_generazione,
                            DiecieLottoEstrazione.ora == ora_gen,
                        )
                    ).scalar_one_or_none()
                    if estr:
                        estr_data = {
                            "numeri": estr.numeri,
                            "numero_oro": estr.numero_oro,
                            "doppio_oro": estr.doppio_oro,
                            "numeri_extra": estr.numeri_extra,
                        }

                records.append(
                    {
                        "data": str(p.data_generazione),
                        "ora": str(ora_gen) if ora_gen else "",
                        "gioco": "diecielotto",
                        "previsione": {
                            "numeri": p.numeri if isinstance(p.numeri, list) else list(p.numeri),
                            "metodo": p.segnale,
                        },
                        "estrazione": estr_data,
                        "match": det.get("match_base", 0),
                        "match_extra": det.get("match_extra", 0),
                        "stato": p.stato,
                        "costo": 2.0,
                        "vincita": float(p.vincita) if p.vincita else 0,
                    }
                )

        if gioco in ("all", "lotto"):
            l_preds = (
                session.execute(
                    select(Previsione).order_by(Previsione.data_generazione.desc()).limit(limit)
                )
                .scalars()
                .all()
            )
            for p in l_preds:
                # Find extraction for this date+ruota
                estr = session.execute(
                    select(Estrazione).where(
                        Estrazione.data == p.data_generazione,
                        Estrazione.ruota == p.ruota,
                    )
                ).scalar_one_or_none()
                filtri = p.filtri if isinstance(p.filtri, dict) else {}

                records.append(
                    {
                        "data": str(p.data_generazione),
                        "gioco": "lotto",
                        "previsione": {
                            "numeri": [p.num_a, p.num_b],
                            "ruota": p.ruota,
                            "metodo": filtri.get("metodo", ""),
                            "tipo": filtri.get("tipo", "ambetto"),
                        },
                        "estrazione": {
                            "numeri": estr.numeri if estr else [],
                            "ruota": p.ruota,
                        },
                        "match": 2 if p.stato == "VINTA" else 0,
                        "stato": p.stato,
                        "costo": p.posta,
                        "vincita": float(p.vincita) if p.vincita else 0,
                    }
                )

        records.sort(key=lambda x: x["data"], reverse=True)
        return records[:limit]
    finally:
        if own:
            session.close()
