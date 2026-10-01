#!/usr/bin/env python3
"""
Re-harvest faillissementen.com detail pages for authoritative field values.

Why: the first harvest stored truncated bedrijfsnamen (~24 chars) for a large
share of records, plus undecoded HTML entities, plus mojibake in curator names.
The detail pages carry authoritative values in JSON-LD (Organization.name,
WebPage.datePublished) and in the `detail-seo__fact` label/value block
(Status, KvK-nummer, Adres, Postcode, Plaats, Rechtbank, Insolventienummer, Curator).

Refreshes only fields the detail page actually provides; sbi5 / rechtsvorm /
provincie are preserved from the existing dataset because they are not on the page.

Usage:  python3 reharvest_names.py [--limit N] [--out FILE]
"""
import argparse, html, json, random, re, sys, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126 Safari/537.36"}
BASE = "https://www.faillissementen.com"
SRC = "/root/.hermes/cache/scratch/detail_sbi49.json"

FACT_RE = re.compile(
    r'detail-seo__fact-label">\s*(.*?)\s*</span>\s*'
    r'<span class="detail-seo__fact-value">\s*(.*?)\s*</span>', re.S)
LD_RE = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)


def repair_mojibake(s):
    if not isinstance(s, str):
        return s
    if any(m in s for m in ("\u00c3", "\u00e2\u20ac", "\u00c2")):
        try:
            return s.encode("latin-1").decode("utf-8")
        except Exception:
            return s
    return s


def clean(v):
    v = re.sub(r"<[^>]+>", " ", v or "")
    return repair_mojibake(html.unescape(re.sub(r"\s+", " ", v)).strip())


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}")
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1) + random.random())
    raise last


def parse(htmltext):
    # Fail loudly. Under rate limiting the source answers HTTP 200 with a stub body
    # ("Limit reached, contact info@faillissementen.com"). Treating that as a
    # successful empty parse produced a silent no-op "re-harvest" that looked clean.
    if "Limit reached" in htmltext or len(htmltext) < 2000:
        raise RuntimeError("source rate-limited or served a stub page")
    out = {}
    for k, v in FACT_RE.findall(htmltext):
        out[clean(k)] = clean(v)
    ld = LD_RE.search(htmltext)
    if ld:
        try:
            j = json.loads(ld.group(1))
            for node in j.get("@graph", j if isinstance(j, list) else [j]):
                if not isinstance(node, dict):
                    continue
                t = node.get("@type")
                if t == "Organization" and node.get("name"):
                    out["_name"] = clean(node["name"])
                elif t == "WebPage":
                    if node.get("name"):
                        out["_page_name"] = clean(node["name"])
                    if node.get("datePublished"):
                        out["_datePublished"] = node["datePublished"][:10]
        except Exception:
            pass
    if not out:
        raise RuntimeError("no structured fields parsed from page")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="/root/.hermes/cache/scratch/detail_sbi49_v2.json")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    recs = json.load(open(SRC, encoding="utf-8"))
    if args.limit:
        recs = recs[: args.limit]

    def work(r):
        u = r.get("url") or ""
        if not u.startswith("/"):
            return r, {"_err": "no url"}
        try:
            return r, parse(fetch(BASE + u))
        except Exception as e:
            return r, {"_err": f"{type(e).__name__}: {str(e)[:80]}"}

    done = 0
    errs = 0
    updated = {"name": 0, "curator": 0, "plaats": 0, "postcode": 0,
               "adres": 0, "rechtbank": 0, "insolventienummer": 0, "status": 0}
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for r, p in ex.map(work, recs):
            done += 1
            if "_err" in p:
                errs += 1
                results.append(r)
                continue
            nr = dict(r)
            mapping = [("_name", "name"), ("Curator", "Curator"), ("Plaats", "place"),
                       ("Postcode", "Postcode"), ("Adres", "Adres"),
                       ("Rechtbank", "Rechtbank"), ("Insolventienummer", "Insolventienummer"),
                       ("Status", "Status")]
            for src_k, dst_k in mapping:
                nv = p.get(src_k)
                if not nv or nv == "-":
                    continue
                if dst_k == "name" and "..." in nv:
                    # source itself truncates this name; keep whichever is longer
                    if len(nv) <= len(r.get("name") or ""):
                        continue
                if (r.get(dst_k) or "") != nv:
                    updated[dst_k] = updated.get(dst_k, 0) + 1
                nr[dst_k] = nv
            if p.get("_datePublished"):
                nr["date_iso"] = p["_datePublished"]
            results.append(nr)
            if done % 100 == 0:
                print(f"  ...{done}/{len(recs)} (errors={errs})", flush=True)

    print(f"fetched={done} errors={errs}")
    print("fields changed:", json.dumps(updated))
    json.dump(results, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
