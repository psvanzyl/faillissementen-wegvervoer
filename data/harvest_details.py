#!/usr/bin/env python3
"""Finish harvesting faillissementen.com detail pages for SBI 49 (Vervoer over land)."""
import json, re, os, sys, html as H
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

WS = "/root/.hermes/cache/scratch"
recs = json.load(open(f"{WS}/recs_listing.json", encoding="utf-8"))
OUT = f"{WS}/detail_sbi49.json"

done = {}
if os.path.exists(OUT):
    done = {d["url"]: d for d in json.load(open(OUT, encoding="utf-8"))}

HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
_tl = {}

def clean_rv(v):
    if not v:
        return None
    v = re.split(r'\s+en de hoofdactiviteit', v)[0]
    v = re.split(r'\s*,\s*', v)[0]
    return v.strip().rstrip('.')

def fetch(rec):
    url = "https://www.faillissementen.com" + rec["url"]
    s = _tl.get("s")
    if s is None:
        s = requests.Session(); s.headers.update(HDR); _tl["s"] = s
    for attempt in range(3):
        try:
            r = s.get(url, timeout=25)
            if r.status_code != 200:
                if attempt == 2:
                    return {**rec, "error": f"HTTP {r.status_code}"}
                continue
            t = r.text
            facts = dict(re.findall(
                r'detail-seo__fact-label">([^<]+)</span>\s*<span class="detail-seo__fact-value">([^<]*)</span>', t))
            facts = {k.strip(): H.unescape(v).strip() for k, v in facts.items()}
            mrv = re.search(r'De rechtsvorm betreft een\s+([^.]*)', t)
            mact = re.search(r'hoofdactiviteit van dit bedrijf was\s*(\d{3,6})\s*,\s*([^.]+)\.', t)
            mdate = re.search(r'Op\s+(\d{2}-\d{2}-\d{4})\s+heeft de rechtbank', t)
            return {**rec, **facts,
                    "rechtsvorm": clean_rv(mrv.group(1) if mrv else None),
                    "sbi5": mact.group(1) if mact else None,
                    "activiteit": mact.group(2).strip() if mact else None,
                    "detail_date": mdate.group(1) if mdate else None}
        except Exception as e:
            if attempt == 2:
                return {**rec, "error": str(e)[:120]}
    return {**rec, "error": "unknown"}

todo = [r for r in recs if r["url"] not in done]
print(f"resuming: {len(done)} done, {len(todo)} to fetch", flush=True)

results = dict(done)
errors = 0
n = 0
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch, r): r for r in todo}
    for f in as_completed(futs):
        d = f.result()
        results[d["url"]] = d
        n += 1
        if d.get("error"):
            errors += 1
        if n % 50 == 0:
            json.dump(list(results.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {n}/{len(todo)} errors={errors}", flush=True)

json.dump(list(results.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"DONE total={len(results)} errors={errors}", flush=True)
