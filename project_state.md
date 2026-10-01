# project_state.md — faillissementen-wegvervoer

## Status: LIVE (2026-10-01)

Dashboard: https://faillissementen.laserraptorai.duckdns.org (HTTP 200, Let's Encrypt cert valid to 30-12-2026)
Repo: https://github.com/psvanzyl/faillissementen-wegvervoer (public, branch `main`)
Local: /root/projects/faillissementen-wegvervoer
Scratch: /root/.hermes/cache/scratch (index_template.html, index.html, dashboard_data.json, detail_sbi49.json)

## Coolify identifiers
- project_uuid: l8aqytzrcihnwxvdif4qtth5  (project "Faillissementen Wegvervoer")
- app_uuid:     zvqzr2d1vljeht4odkgznuw4  (app "faillissementen-wegvervoer")
- environment:  production
- server_uuid:  hff16ilrvechplni0w97qy2t  (localhost / CT310 @ 192.168.178.132:8000)
- deploy: POST /api/v1/deploy {"uuid": app_uuid}; token /root/.coolify_api_token
- Container name prefix: zvqzr2d1vljeht4odkgznuw4-*

## Data
- **866 faillietverklaringen** uit faillissementen.com (status=Faillissement, branche 49), 15-04-2005 → 01-10-2026,
  met detailvelden: rechtsvorm, postcode, 5-cijferige SBI, Rechtbank, plaats. `detail_sbi49.json`, 0 errors.
- **CBS 82244NED** SBI 383200 (= 49 Vervoer over land), maatstaf *Uitgesproken faillissementen* (M001327),
  jaar 2009–2025 + maand 2009-01 → 2026-08. Splitsing A028820 (eenmanszaak) / A047597 (bedrijven).
- **CBS 81567NED** dieselpompprijs: maatstaf D002209 + motorbrandstof A047219, maand 2006-01 → 2026-08.

## Excel-export
- Nextcloud: `nextcloud:projects/faillissementen-wegvervoer/faillissementen_sbi49_data.xlsx`
  (142.498 bytes, md5 `4945e86f5624ac10f21638224c143dd1`) — lokaal in `data/`.
- 11 sheets: Toelichting · Faillissementen (866 rijen, A1:P867, autofilter) · Site vs CBS ·
  CBS jaar · CBS maand · Dieselprijs · Dieselprijs jaar · Provincies · Top 30 plaatsen ·
  Rechtsvormen · Site per jaar. 4 grafieken, `full_calc_on_load`.
- Bouw: spec `~/.hermes/cache/scratch/workbook_spec.json`, script `skill xlsx/scripts/xlsx_create.py`,
  verificatie `verify2.py` (mojibake-scan, tellingen, formules).
- **`rv_bucket` is het betrouwbare rechtsvorm-veld**; `rv_clean` is rommelig (kapitalisatievarianten,
  afgekapte waarden). Gebruik altijd de bucket voor de MKB/groot-indeling, nooit rv_clean.
- Mojibake (30 curatornamen, enkele plaatsen) bij export hersteld via latin-1→utf-8.
- Let op: de opstart-kernel van execute_code heeft GÉÉN openpyxl — draai skill-scripts via `terminal`.

## Key findings
- **faillissementen.com is onvolledig (~40%)**: site 866 over 2005–2026 vs CBS 2009–2025 veelvoud.
  Voorbeelden: 2024 site 80 / CBS 185; 2012 site 79 / CBS 285. → CBS = aantallen, site = locatie/rechtsvorm.
- 2025: 142 faillissementen (2024: 185, −23%). 2026 t/m aug: 102.
- Pearson r ≈ −0,30 (CBS jaarbasis) — dieselprijs alleen verklaart het patroon NIET.
- Provincies: Zuid-Holland 185, Noord-Brabant 116, Limburg 95, Noord-Holland 92.

## Gotchas / lessons
- **CBS maandperioden** zijn `YYYYMMnn` — de maand staat op positie 6-7 (`p[6:8]`), NIET `p[4:6]` (dat is de letterlijke "MM").
- **`82244NED/Observations`** levert >100k rijen gepagineerd; filter met `$filter=BedrijfstakkenBranchesSBI2008 eq '383200'`.
  Resultaten altijd in `{"value":[...]}`.
- **Provincie-filter op faillissementen.com** (`/filter/provincie/<P>`) werkt NIET voor tellingen — geeft een venster van 10.
  Provincie daarom afgeleid uit postcode (4-cijferige reeksen); 16/866 zonder bruikbare postcode.
- **Site-datums staan als DD-MM-YYYY** — niet als string sorteren (gaf eerst 2023→2025 i.p.v. 2005→2026).
- Deenvoudig: dependency-vrij SVG-dashboard (geen CDN) — Chromium kon geen CDN-bestand downloaden.
- Reproductie/verificatie: `chromium --headless=new --virtual-time-budget=9000 --dump-dom <url>` en tel `<rect>`/`<polyline>`.

## Open / optioneel
- **Drift met Nextcloud (nog te doen):** `README.md` op Nextcloud is een oudere, hard-wrapped versie
  (3.608 vs 3.291 bytes) — inhoud identiek, alleen reflow. Opnieuw uploaden vereist goedkeuring.
- De xlsx staat lokaal in `data/` maar op Nextcloud in de projectroot; layout gelijk trekken loopt nog.
- KVK-koppeling ontbreekt (geen API-sleutel, geen vrije bulkdata).
- Provincie-heatmap is nu een geordende balkengrafiek; echte NL-kaart (GeoJSON) kan later.
- Detailpagina's van de site worden niet automatisch ververst — herhaal `data/harvest_details.py` voor updates.
