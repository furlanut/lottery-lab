"""Lottery Lab auto-updater.

Runs periodically to scrape, predict, and verify all games.
Designed to run via cron or as a periodic task.
"""

from __future__ import annotations

import logging
from datetime import date, time, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("auto-update")


def update_diecielotto():
    """Scrape latest 10eLotto extractions from lottologia API."""
    try:
        import httpx
        from diecielotto.ingestor.service import inserisci_estrazioni
        from lotto_predictor.models.database import get_session

        api_url = "https://lottologia.com/api/metalotto/data/lottery/10elotto5minuti/draw/bydate"
        session = get_session()
        total = 0
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
                    stats = inserisci_estrazioni(session, records)
                    total += stats["inseriti"]
            except Exception as e:
                log.error("10eLotto %s: %s", d, e)
        session.close()
        log.info("10eLotto: +%d new extractions", total)
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


def generate_and_verify():
    """Generate predictions and verify active ones."""
    try:
        from paper_trading.service import (
            paper_trade_diecielotto,
            paper_trade_lotto,
            paper_trade_vincicasa,
            verifica_diecielotto,
            verifica_lotto,
            verifica_vincicasa,
        )

        paper_trade_diecielotto()
        paper_trade_vincicasa()
        paper_trade_lotto()
        log.info("Predictions generated")

        r1 = verifica_diecielotto()
        r2 = verifica_vincicasa()
        r3 = verifica_lotto()
        log.info("Verified: 10eL=%d VC=%d Lotto=%d", len(r1), len(r2), len(r3))
    except Exception as e:
        log.error("Predict/verify failed: %s", e)


if __name__ == "__main__":
    log.info("=== Auto-update starting ===")
    update_diecielotto()
    update_lotto()
    generate_and_verify()
    log.info("=== Auto-update complete ===")
