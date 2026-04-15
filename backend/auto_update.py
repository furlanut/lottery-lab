"""Lottery Lab auto-updater.

Runs every 5 minutes. For 10eLotto: scrapes live extractions,
generates a prediction for EACH new extraction, and verifies immediately.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date, time, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("auto-update")

W = 100  # prediction window
PREMI_BASE = {3: 2.0, 4: 10.0, 5: 100.0, 6: 1000.0}
PREMI_EXTRA = {1: 1.0, 2: 1.0, 3: 7.0, 4: 20.0, 5: 200.0, 6: 2000.0}


def update_diecielotto():
    """Scrape + predict + verify for EACH new 10eLotto extraction."""
    try:
        from diecielotto.ingestor.scraper import scarica_ultime_estrazioni
        from diecielotto.ingestor.service import inserisci_estrazioni
        from diecielotto.models.database import (
            DiecieLottoEstrazione,
            DiecieLottoPrevisione,
        )
        from lotto_predictor.models.database import get_session
        from sqlalchemy import func, select

        session = get_session()

        # 1. Scrape latest extractions from live endpoint
        try:
            live = scarica_ultime_estrazioni()
            if live:
                stats = inserisci_estrazioni(session, live)
                if stats["inseriti"] > 0:
                    log.info("10eLotto: +%d new extractions", stats["inseriti"])
        except Exception as e:
            log.warning("Live scrape: %s", e)

        # 2. Also try daily archive for backfill
        try:
            import httpx

            api_url = (
                "https://lottologia.com/api/metalotto/data/lottery/10elotto5minuti/draw/bydate"
            )
            for i in range(2):
                d = date.today() - timedelta(days=i)
                try:
                    resp = httpx.get(
                        api_url,
                        params={"date": d.isoformat()},
                        timeout=60,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    draws = resp.json().get("draws", [])
                    records = []
                    for draw in draws:
                        dt = draw["date"]
                        numeri, extra, oro, doro = [], [], 0, 0
                        for g in draw.get("numbers", []):
                            if g["type"] == "draws":
                                numeri = sorted(g["values"])
                            elif g["type"] == "extra":
                                extra = sorted(g["values"])
                            elif g["type"] == "2oro":
                                vals = g["values"]
                                if len(vals) >= 2:
                                    oro, doro = vals[0], vals[1]
                            elif g["type"] == "oro" and not oro:
                                oro = g["values"][0] if g["values"] else 0
                        if len(numeri) == 20:
                            h, m = dt["hour"], dt["minute"]
                            if 0 <= h <= 23:
                                records.append(
                                    {
                                        "concorso": dt.get("day_progressive", 0),
                                        "data": date(dt["year"], dt["month"], dt["day"]),
                                        "ora": time(h, m),
                                        "numeri": numeri,
                                        "numero_oro": oro,
                                        "doppio_oro": doro,
                                        "numeri_extra": extra[:15],
                                    }
                                )
                    if records:
                        inserisci_estrazioni(session, records)
                except Exception as e:
                    log.debug("Archive %s: %s", d, e)
        except Exception as e:
            log.debug("Archive API unavailable: %s", e)

        # 3. Generate predictions for extractions that don't have one
        all_estr = (
            session.execute(
                select(DiecieLottoEstrazione).order_by(
                    DiecieLottoEstrazione.data, DiecieLottoEstrazione.ora
                )
            )
            .scalars()
            .all()
        )

        if len(all_estr) < W + 1:
            log.info("Not enough extractions for predictions (%d)", len(all_estr))
            session.close()
            return

        # Find extractions without predictions (last 50)
        recent = all_estr[-50:]
        new_preds = 0

        for estr in recent:
            # Check if prediction exists for this extraction
            existing = session.scalar(
                select(func.count(DiecieLottoPrevisione.id)).where(
                    DiecieLottoPrevisione.data_generazione == estr.data,
                    DiecieLottoPrevisione.ora_generazione == estr.ora,
                )
            )
            if existing and existing > 0:
                continue

            # Find index of this extraction
            idx = next((i for i, e in enumerate(all_estr) if e.id == estr.id), None)
            if idx is None or idx < W:
                continue

            # Generate prediction using W previous extractions
            base_freq = Counter()
            extra_freq = Counter()
            for j in range(idx - W, idx):
                for n in all_estr[j].numeri:
                    base_freq[n] += 1
                for n in all_estr[j].numeri_extra:
                    extra_freq[n] += 1

            hot_base = [n for n, _ in base_freq.most_common(6)]
            hot_extra = [n for n, _ in extra_freq.most_common(20) if n not in hot_base][:3]
            pick = sorted(hot_base[:3] + hot_extra[:3])
            if len(pick) < 6:
                for n, _ in base_freq.most_common():
                    if n not in pick:
                        pick.append(n)
                    if len(pick) >= 6:
                        break

            # Verify against this extraction
            pick_set = set(pick)
            drawn_set = set(estr.numeri)
            extra_set = set(estr.numeri_extra)
            mb = len(pick_set & drawn_set)
            rem = pick_set - drawn_set
            me = len(rem & extra_set)
            vb = PREMI_BASE.get(mb, 0.0)
            ve = PREMI_EXTRA.get(me, 0.0)
            vincita = vb + ve

            p = DiecieLottoPrevisione(
                data_generazione=estr.data,
                ora_generazione=estr.ora,
                segnale="S4_dual_target",
                configurazione=6,
                numeri=pick,
                opzioni={"extra": True},
                score=1.103,
                dettagli={
                    "metodo": "S4_dual_target",
                    "W": W,
                    "match_base": mb,
                    "match_extra": me,
                },
                stato="VINTA" if vincita > 0 else "PERSA",
                data_esito=estr.data,
                vincita=vincita,
            )
            session.add(p)
            new_preds += 1

        session.commit()
        if new_preds > 0:
            log.info("10eLotto: %d new predictions generated", new_preds)

        total = session.scalar(select(func.count(DiecieLottoEstrazione.id)))
        preds = session.scalar(select(func.count(DiecieLottoPrevisione.id)))
        log.info("10eLotto totals: %d extractions, %d predictions", total, preds)
        session.close()

    except Exception as e:
        log.error("10eLotto update failed: %s", e)


def update_lotto():
    """Scrape latest Lotto extraction."""
    try:
        from lotto_predictor.ingestor.scraper import scarica_ultima_estrazione
        from lotto_predictor.models.database import Estrazione, get_session

        est = scarica_ultima_estrazione()
        session = get_session()
        for ruota, numeri in est["ruote"].items():
            e = Estrazione(
                concorso=est["concorso"],
                data=est["data"],
                ruota=ruota,
                n1=numeri[0],
                n2=numeri[1],
                n3=numeri[2],
                n4=numeri[3],
                n5=numeri[4],
            )
            session.merge(e)
        session.commit()
        session.close()
        log.info("Lotto: scraped #%d (%s)", est["concorso"], est["data"])
    except Exception as e:
        log.error("Lotto update failed: %s", e)


def update_vincicasa():
    """Generate and verify VinciCasa prediction."""
    try:
        from paper_trading.service import paper_trade_vincicasa, verifica_vincicasa

        paper_trade_vincicasa()
        verifica_vincicasa()
    except Exception as e:
        log.error("VinciCasa: %s", e)


if __name__ == "__main__":
    log.info("=== Auto-update starting ===")
    update_diecielotto()
    update_lotto()
    update_vincicasa()
    log.info("=== Auto-update complete ===")
