#!/usr/bin/env python3
"""Harvest the Centraal Insolventieregister (CIR) 'bekendmakingen' feed.

WHY THIS EXISTS
---------------
Rechtspraak publishes every insolvency publication as an open JSON API at
https://insolventies.rechtspraak.nl/Services/BekendmakingenService/
(discoverable in the Angular bundle's slug map: /frontend/main.js).

CRITICAL LIMITATION -- READ BEFORE RELYING ON THIS
--------------------------------------------------
The CIR exposes ONLY a rolling window of roughly one month of publication
days.  `getAll/` returns the available day-ids; addressing any older day
(e.g. haalOp/20200102000000) returns an EMPTY payload.  The register keeps
a case only until 6 months AFTER the insolvency ends, so the CIR is a
current-register, not an archive.

=> There is NO open, official, record-level historical bankruptcy dataset.
   To build history you must run this script repeatedly (e.g. daily via
   cron) and accumulate the results.  Each run appends/supersedes days.

The CIR carries NO SBI industry codes, so this cannot be filtered to road
transport (SBI 49) without paid KvK enrichment.  For historical *counts*
use CBS (82244NED / 82522NED) instead.

USAGE
-----
    python3 cir_harvest.py [--out DIR] [--append]

    --out DIR    output directory (default ./cir_data)
    --append     merge with an existing cir_bekendmakingen_enriched.json
                 instead of overwriting, so repeated runs accumulate
                 whatever the rolling window still exposes.

OUTPUT
------
    cir_bekendmakingen_enriched.json   flattened notices (+ regex fields)
    cir_bekendmakingen_raw.json        raw per-day API payloads
    cir_bekendmakingen.csv             ;-delimited, utf-8-sig for Excel
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://insolventies.rechtspraak.nl/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE,
}
DAYS_URL = "Services/BekendmakingenService/getAll/"
DAY_URL = "Services/BekendmakingenService/haalOp/{pid}"

MONTHS = {"januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5,
          "juni": 6, "juli": 7, "augustus": 8, "september": 9, "oktober": 10,
          "november": 11, "december": 12}

FIELDS = ["Datum", "Rechtbank", "Cluster", "Publicatiesoort", "Locatiecode",
          "Insolventienummer", "KvK", "Plaats", "Uitspraakdatum", "Tekst"]


def fetch(path: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ms_from_dotnet(x: str) -> int:
    """'\\/Date(1788213600000)\\/' -> 1788213600000"""
    return int(re.search(r"\((\d+)", x).group(1))


def insol_nr(t: str) -> str:
    m = re.search(r"\(([A-Z]\.\d{2}/\d{2}/\d+)", t or "")
    return m.group(1) if m else ""


def kvk(t: str) -> str:
    m = re.search(r"KvK[:\s]*(\d{6,10})", t or "")
    return m.group(1) if m else ""


def plaats(t: str) -> str:
    m = re.search(r"\d{4}\s?[A-Z]{2}\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-'\. ]{1,38}?)"
                  r"(?=[,.]| geb\.|$)", t or "")
    return m.group(1).strip() if m else ""


def uitspraakdatum(t: str) -> str:
    """'Uitspraak faillissement op 29 september 2026' -> 2026-09-29"""
    m = re.search(r"\b(\d{1,2})\s+([a-z]+)\s+(\d{4})", (t or "").lower())
    if m and m.group(2) in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return ""


def flatten(pid: str, date: dt.date, payload: dict) -> list[dict]:
    out = []
    for inst in payload.get("Instanties", []) or []:
        court = inst.get("PublicerendeInstantieOmschrijving")
        for cl in inst.get("Publicatieclusters", []) or []:
            cluster = cl.get("PublicatieclusterOmschrijving")
            for so in cl.get("Publicatiesoorten", []) or []:
                caption = so.get("PublicatiesoortCaption")
                for loc in so.get("PublicatiesNaarLocatie", []) or []:
                    for txt in loc.get("Publicaties", []) or []:
                        out.append({
                            "Datum": date.strftime("%Y-%m-%d"),
                            "PublicatieId": pid,
                            "Rechtbank": court,
                            "Cluster": cluster,
                            "Publicatiesoort": caption,
                            "Locatiecode": loc.get("LocatiecodeBekendmaking"),
                            "Insolventienummer": insol_nr(txt),
                            "KvK": kvk(txt),
                            "Plaats": plaats(txt),
                            "Uitspraakdatum": uitspraakdatum(txt),
                            "Tekst": txt,
                        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="cir_data")
    ap.add_argument("--append", action="store_true",
                    help="merge with existing enriched JSON instead of overwriting")
    ap.add_argument("--delay", type=float, default=0.4)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    days = json.loads(fetch(DAYS_URL))
    if not days:
        print("ERROR: getAll/ returned no publication days", file=sys.stderr)
        return 1
    print(f"rolling window: {len(days)} publication days "
          f"({days[0]['Id']} .. {days[-1]['Id']})")

    records, raw = [], {}
    for d in days:
        pid = d["Id"]
        date = dt.datetime.fromtimestamp(ms_from_dotnet(d["Datum"]) / 1000).date()
        try:
            payload = json.loads(fetch(DAY_URL.format(pid=pid)))
        except Exception as e:                                  # noqa: BLE001
            print(f"  ! {pid} failed: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        raw[pid] = payload
        got = flatten(pid, date, payload)
        records.extend(got)
        print(f"  {date}  {pid}  {len(got):4d} notices")
        time.sleep(a.delay)

    if not records:
        print("ERROR: no notices parsed -- layout may have changed", file=sys.stderr)
        return 1

    enr = os.path.join(a.out, "cir_bekendmakingen_enriched.json")
    if a.append and os.path.exists(enr):
        old = json.load(open(enr, encoding="utf-8"))
        by = {(r["PublicatieId"], r["Tekst"]): r for r in old}
        for r in records:
            by[(r["PublicatieId"], r["Tekst"])] = r
        records = list(by.values())
        print(f"appended: {len(records)} unique notices total")

    records.sort(key=lambda r: (r["Datum"], str(r["Rechtbank"]), r["Tekst"] or ""))
    json.dump(records, open(enr, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(raw, open(os.path.join(a.out, "cir_bekendmakingen_raw.json"), "w",
                        encoding="utf-8"), ensure_ascii=False)

    cols = ["Datum", "Rechtbank", "Cluster", "Publicatiesoort", "Insolventienummer",
            "KvK", "Plaats", "Uitspraakdatum", "Tekst"]
    with open(os.path.join(a.out, "cir_bekendmakingen.csv"), "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for r in records:
            w.writerow([r.get(c, "") for c in cols])

    print(f"\nparsed {len(records)} notices -> {a.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
