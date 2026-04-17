"""Parse millionday.cloud archive HTML into JSON.

Expected row:
<tr>
    <td><span class="testo_arancione">Giovedì 16 Aprile 2026</span>  ore 20:30</td>
    <td>3</td><td>4</td><td>11</td><td>34</td><td>55</td>
    <td><span style="color:#088796">25</span></td> ... (5 extra)
</tr>
"""

import json
import re
from pathlib import Path

MESI = {
    "Gennaio": "01", "Febbraio": "02", "Marzo": "03", "Aprile": "04",
    "Maggio": "05", "Giugno": "06", "Luglio": "07", "Agosto": "08",
    "Settembre": "09", "Ottobre": "10", "Novembre": "11", "Dicembre": "12",
}

HTML_PATH = Path(__file__).parent / "data" / "archivio_estrazioni.html"
html = HTML_PATH.read_text() if HTML_PATH.exists() else Path("/tmp/mdcloud.html").read_text()  # noqa: S108

# Pattern: cattura un <tr>...</tr> che contiene testo_arancione
row_pattern = re.compile(
    r'<tr>\s*<td><span class="testo_arancione">([^<]+)</span>\s*ore\s*(\d{2}:\d{2})</td>'
    r'(.*?)</tr>',
    re.DOTALL,
)

# Pattern numeri: <td>NN</td>  e <td><span style="color:#088796">NN</span></td>
num_base = re.compile(r"<td>\s*(\d{1,2})\s*</td>")
num_extra = re.compile(r'<td><span style="color:#088796">\s*(\d{1,2})\s*</span></td>')

data_date = re.compile(
    r"(?:Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)\s+(\d{1,2})\s+(\w+)\s+(\d{4})"
)

estrazioni = []
for m in row_pattern.finditer(html):
    data_str = m.group(1).strip()
    ora = m.group(2).strip()
    body = m.group(3)

    d = data_date.search(data_str)
    if not d:
        continue
    day, mese_nome, year = d.group(1), d.group(2), d.group(3)
    mese = MESI.get(mese_nome)
    if not mese:
        continue
    iso_date = f"{year}-{mese}-{int(day):02d}"

    bases = [int(x) for x in num_base.findall(body)]
    extras = [int(x) for x in num_extra.findall(body)]

    if len(bases) != 5 or len(extras) != 5:
        continue
    if not all(1 <= n <= 55 for n in bases):
        continue
    if not all(1 <= n <= 55 for n in extras):
        continue

    estrazioni.append({"data": iso_date, "ora": ora, "numeri": bases, "extra": extras})

# Ordina cronologicamente (oldest first)
estrazioni.sort(key=lambda e: (e["data"], e["ora"]))

# Dedup
seen = set()
uniq = []
for e in estrazioni:
    key = (e["data"], e["ora"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(e)

print(f"Estrazioni totali: {len(uniq)}")
print(f"Dal: {uniq[0]['data']} {uniq[0]['ora']}")
print(f"Al:  {uniq[-1]['data']} {uniq[-1]['ora']}")

# Stats per anno
by_year = {}
for e in uniq:
    y = e["data"][:4]
    by_year[y] = by_year.get(y, 0) + 1
print("\nPer anno:")
for y in sorted(by_year):
    print(f"  {y}: {by_year[y]}")

# Salva
OUT = Path(__file__).parent / "data" / "archive_2022_2026.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(uniq, indent=2))
print(f"\nSalvato: {OUT} ({len(uniq)} estrazioni)")

# Prime 3 e ultime 3
print("\nPrime 3:")
for e in uniq[:3]:
    print(f"  {e['data']} {e['ora']} base={e['numeri']} extra={e['extra']}")
print("\nUltime 3:")
for e in uniq[-3:]:
    print(f"  {e['data']} {e['ora']} base={e['numeri']} extra={e['extra']}")
