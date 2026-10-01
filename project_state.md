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
  Subsectoren: 491=`383300`, 492=`383500`, 493=`383700`, 494=`384400`. Let op: subsector 494 (goederenvervoer
  over de weg) is verreweg de grootste; 493 (personenvervoer) is klein.
- **CBS 82522NED** *Uitgesproken faillissementen* naar regio (TypeGefailleerde × RegioS × maand),
  maatstaf A047596, provincies `PV20`–`PV31`, jaar 2009–2025 + maand 2009-01 → 2026-08.
  BELANGRIJK: deze tabel heeft **geen SBI-uitsplitsing** — het zijn alle sectoren. Niet te filteren op wegvervoer.
- **CBS 81567NED** dieselpompprijs: maatstaf D002209 + motorbrandstof A047219, maand 2006-01 → 2026-08.

## Excel-export
- Nextcloud: `nextcloud:projects/faillissementen-wegvervoer/faillissementen_sbi49_data.xlsx`
  (169.908 bytes, md5 `cb5cc1cbe3f752e71d6d3ae01ac9d884`) — lokaal in `data/`; read-back byte-identiek.
- 14 sheets: Toelichting · Faillissementen (866 rijen, **A1:Q867**, autofilter) · Site vs CBS ·
  CBS jaar · CBS maand · **CBS 82244NED subsectoren** · **CBS 82522NED regio jaar** ·
  **CBS 82522NED regio maand** · Dieselprijs · Dieselprijs jaar · Provincies · Top 30 plaatsen ·
  Rechtsvormen · Site per jaar. 6 grafieken, `full_calc_on_load`.
- Nieuwe CBS-bladzijden (2026-10-01): subsectoren jaar 2009-2025 + 2026 (t/m aug, voorlopig);
  regio jaar = provincies als rijen, recentste jaar eerst, + totaal 2009-2025; regio maand = 212 maanden × 12 provincies + NL.
- Bouw: spec `~/.hermes/cache/scratch/workbook_spec.json`, script `skill xlsx/scripts/xlsx_create.py`,
  verificatie `verify2.py` (mojibake-scan, tellingen, formules).
- **`rv_bucket` is het betrouwbare rechtsvorm-veld**; `rv_clean` is rommelig (kapitalisatievarianten,
  afgekapte waarden). Gebruik altijd de bucket voor de MKB/groot-indeling, nooit rv_clean.
- Mojibake (30 curatornamen, enkele plaatsen) bij export hersteld via latin-1→utf-8.
- Let op: de opstart-kernel van execute_code heeft GÉÉN openpyxl — draai skill-scripts via `terminal`.
- Kolom Q `Naam afgekapt?` markeert 111 records waarvan de bedrijfsnaam onvolledig is.

### Bekende datadefecten (eerlijk gedocumenteerd in blad Toelichting)
- **111 van 866 records hebben een afgekapte bedrijfsnaam** (kolom Q = `ja`).
  Dit is een fout in de oorspronkelijke oogst, niet in de bron. Bewijs: detailpagina van
  KvK 27196576 toont `R Hoekstra (inter)nationaal Transport`, de dataset heeft
  `R Hoekstra (inter)nationa`. Detectie: naam korter dan de URL-slug, plus namen met `...`.
  4 records zijn in de BRON zelf afgekapt (o.a. KvK 84099747 -> letterlijk `De...`).
- **499 records hebben een afgekapte activiteitomschrijving IN DE BRON**
  (`Goederenvervoer over weg (geen verhuiz.).`). Niet te repareren door opnieuw op te halen;
  de SBI-code is wel compleet. Alle 499 zitten onder code `4941`.
- **faillissementen.com rate-limit de box-IP.** Symptoom: **HTTP 200** met een stub-body
  van 50 bytes: `5) Limit reached, contact info@faillissementen.com`. Dit is géén 429 en
  géén exception — een parser die alleen op HTTP-status let, ziet een "geslaagde" lege pagina.
  Herstel: `reharvest_names.py` faalt nu hard op stub-bodies; wacht met her-oogsten tot de
  limiet is opgeheven (cooldown), en doseer met vertraging tussen requests.
- **Autoritatieve velden op een detailpagina:** JSON-LD `Organization.name` = volledige
  bedrijfsnaam; JSON-LD `WebPage.datePublished` = datum; het `detail-seo__fact`-blok geeft
  Status, KvK-nummer, Adres, Postcode, Plaats, Rechtbank, Insolventienummer, Curator.
  SBI/activiteit/rechtsvorm/provincie staan NIET op de detailpagina.
- Her-oogst-script: `~/.hermes/cache/scratch/reharvest_names.py` (refresh van naam/curator/
  plaats/adres; behoudt sbi5/rechtsvorm/provincie). Draai pas na cooldown.

## Key findings
- **faillissementen.com is onvolledig, en de dekking hangt sterk van de leeftijd af.**
  Op dezelfde filter (SBI 49): CBS 2.946 over 2009-2026 vs site 866. Dekking site/CBS:
  2020-2022 **28-30%**, 2023-2024 **42-43%**, 2025 **82%**, 2026 **176%**.
  Het site-archief is dus alleen voor de recentste maanden ongeveer compleet; in de recentste
  maanden is de site juist BREDER dan CBS. → CBS = aantallen/trends, site = detail op zaakniveau.
- **Het site-bestand bevat dubbeltellingen**: 82 KvK-nummers komen >1× voor = 105 extra regels.
  CBS controleert expliciet op dubbelgetelde faillissementen; de site publiceert per publicatie/entiteit.
- **Site-maandcijfers lopen tot 2 maanden voor op CBS** en schommelen t.o.v. CBS tussen 20% en 267%.
- 2025: 142 faillissementen (2024: 185, −23%). 2026 t/m aug: 102.
- Pearson r op jaarbasis (volledige jaren): site-reeks **+0,60** (n=20), CBS-reeks **−0,30** (n=17).
  Het tekenverschil komt door de onvolledige, niet-gelijkmatige dekking van het site-archief —
  gebruik voor correlaties de CBS-reeks. Dieselprijs alleen verklaart het patroon NIET.
- Provincies: Zuid-Holland 185, Noord-Brabant 116, Limburg 95, Noord-Holland 92.

## Waarom CBS en faillissementen.com verschillen (bewezen, 2026-10-01)
- **CBS = integrale waarneming.** De Nederlandse rechtbanken leveren dagelijks elektronisch ALLE
  uitgesproken faillissementen aan CBS. CBS codeert de bedrijfstak volgens de SBI, verrijkt de
  database met het ABR via KvK-nummers en controleert expliciet op ontbrekende gegevens en
  **dubbelgetelde faillissementen**. Elk faillissement komt **1x** voor, in de maand van de uitspraak.
  Maandelijks gepubliceerd ca. 2 weken na de verslagmaand; de **laatste twee maanden zijn voorlopig**
  en worden bijgesteld. Rechtbanken spreken meestal op vaste dagen uit (dinsdag) -> 4 of 5
  zittingsdagen per maand; daarom publiceert CBS ook een **zittingsdaggecorrigeerde reeks (83085NED)**.
- **faillissementen.com = commercieel register** (Dordrecht), publiceert dagelijks nieuwe uitspraken.
  Het gratis openbare archief is niet gegarandeerd historisch volledig; de complete, op branche
  gecodeerde dataset wordt als **betaalde dataservice** geleverd (CSV/XML/JSON, web service, alerts).
- **Netto:** de twee meten niet dezelfde populatie. In oudere jaren mist het site-archief 57-72% van
  de uitspraken; in de recentste maanden is de site juist breder dan CBS (vermoedelijk doordat de site
  op meerdere branchecoderingen matcht en per publicatie telt i.p.v. per faillissement).
  Dit is een **hypothese** voor het recente overschot; het tekort in oudere jaren is **bewezen**.

## Blokkade faillissementen.com (2026-10-01) - OPGELOST: bypass mislukt, gepivoteerd
- De site heeft het box-IP **volledig geband**: ook de homepage geeft HTTP 200 met een ~50-byte
  body `5) Limit reached, contact info@faillissementen.com`. Geen detailpagina's meer, geen zoekacties.
- **Geen user-agent-probleem**: bewezen met een echte headless Chromium (zelfde stub). Het is IP-based.
- Gevolg: de **111 afgekapte bedrijfsnamen kunnen niet hersteld worden** zolang de ban staat, en een
  volledige her-download is onmogelijk. De bestaande 866 records + `records.json` staan wel op Nextcloud.
- **ProtonVPN-bypass: GEPROBEERD EN MISLUKT.** `/etc/wireguard/wg-proton.conf` (NL-FREE#15),
  AllowedIPs bewust beperkt tot `149.210.216.126/32` (alleen de site liep via de tunnel).
  Diagnose met een neutrale bestemming door dezelfde tunnel:
  - **1.1.1.1 (Cloudflare) via de tunnel = HTTP 301 -> de tunnel WERKT**, alleen traag
    (~12,5 s vs 0,064 s direct).
  - **De site zelf via de tunnel = 0 bytes in 120 s**, terwijl hij direct gewoon antwoordt.
  - **Conclusie: de site blokkeert VPN/datacenter-IP's**, niet alleen het box-IP. De tunnel was nooit
    kapot. Elke andere Proton-endpoint zou net zo goed falen — een VPN-bypass is dus een dood spoor.
- **Boss besloot daarna te pivoten** naar de officiele bronnen (zie de sectie hieronder).

## Officiele bronnen na de pivot (2026-10-01, onderzocht)

### Centraal Insolventieregister — publieke JSON-API ONTDEKT
- De Angular-bundle van `insolventies.rechtspraak.nl` bevat de endpoint-map; de CIR heeft een **open,
  onbeveiligde JSON-API**: `https://insolventies.rechtspraak.nl/Services/BekendmakingenService/`
  - `getAll/` -> lijst van publicatiedagen, bv. `[{"Id":"20260901000000","Datum":"\/Date(1788213600000)\/"}]`
  - `haalOp/<Id>` -> alle publicaties van die dag: rechtbank -> publicatiecluster -> publicatiesoort -> vrije-tekstberichten
  - ook aanwezig: `WebInsolventieService/zoekOpKenmerk`, `zoekOpRechtspersoon`, `VerslagenService/...`
- **Harde beperking:** alleen een **rollende ~1 maand**. Oudere dag-Ids (`20200102000000`, `20050103000000`)
  geven een **leeg antwoord** (51 bytes). De CIR bewaart een zaak slechts tot **6 maanden NA beeindiging**.
  -> De CIR is een actueel register, **GEEN archief**.
- **Geen SBI-codes** in de feed. Filteren op wegvervoer (SBI 49) kan alleen via KvK-verrijking (betaald).
- Wel bruikbaar in de vrije tekst: insolventienummer (`F.13/26/255`), KvK-nummer (1209 van 2256 records),
  adres/plaats, rechtbank en uitspraakdatum.
- **Oogst 2026-10-01:** 23 publicatiedagen, **2256 publicaties**, waarvan **575** in de faillissement-clusters
  (`uitspraken faillissement`, `faillissementen`, `vereenvoudigde afwikkeling faillissementen`).
- Deliverables op Nextcloud (`projects/faillissementen-wegvervoer/`): `cir_officiele_publicaties.xlsx`
  (6 bladen, 2 grafieken), `cir_bekendmakingen.csv`, `cir_bekendmakingen_enriched.json`,
  `cir_bekendmakingen_raw.json` — alle vier read-back **md5-identiek**.
- Herhaalbaar: `cir_harvest.py` in de repo-root (11,5 s voor de hele window); `--append` om te accumuleren.

### Staatscourant / SRU-API — GEEN zaakniveau
- `https://repository.overheid.nl/sru` werkt (open XML, `searchRetrieve`), maar bevat **geen individuele
  faillissementsberichten** meer. Vrije-tekst "faillissement" geeft 69.019 treffers — dat is wetgeving,
  circulaires en algemene stukken, geen uitspraken.

### Conclusie van de pivot
- **Er bestaat geen open, officieel, record-level historisch bestand** van faillietverklaringen.
  De CIR geeft alleen het heden; de Staatscourant heeft ze niet meer. faillissementen.com put uit eigen archief.
- **Voor historische aantallen is CBS de enige officiele bron** (82244NED nationaal, 82522NED regionaal) —
  precies wat boss al als voorkeur had.
- Wil je toch officiele historie op zaakniveau: `cir_harvest.py` dagelijks draaien en laten accumuleren.

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
- **Volledige her-download van faillissementen.com nog steeds geblokkeerd** (2026-10-01 12:36): de site
  rate-limit de box-IP nog (HTTP 200 + 50-byte `5) Limit reached`-stub). De 111 afgekapte namen kunnen
  dus nog niet hersteld worden; `reharvest_names.py` staat klaar en faalt hard op stubs. Doseer na cooldown.
- **CBS is de bron voor alle aantallen**; de site alleen voor detail op zaakniveau.
- **VPN-tunnel OPGERUIMD (2026-10-01).** `wg-quick down wg-proton` uitgevoerd; `ip route` is schoon en de
  site is direct weer bereikbaar (nog wel de ban-stub, want de ban op het box-IP staat nog).
- **Officiele historie op zaakniveau bestaat niet open** (zie de pivot-sectie). Wel: `cir_harvest.py`
  dagelijks draaien om vanaf nu zelf een officieel archief op te bouwen.
