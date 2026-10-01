# Faillissementen wegvervoer (SBI 49) vs. dieselprijs

Interactief dashboard dat het aantal **faillietverklaringen** in het wegvervoer
(SBI/branchecode 49 — *Vervoer over land*) afzet tegen de **gemiddelde dieselpompprijs**.

Live: https://faillissementen.laserraptorai.duckdns.org

## Bronnen

| Doel | Bron | Details |
|---|---|---|
| Faillissementen (officieel) | CBS dataset `82244NED` | maatstaf *Uitgesproken faillissementen*, SBI `383200` (= 49 Vervoer over land) |
| Faillissementen (locatie/rechtsvorm) | faillissementen.com | filter `status=Faillissement` + branchecode `49` |
| Dieselprijs | CBS dataset `81567NED` | maatstaf *Gemiddelde pompprijs*, motorbrandstof `A047219` (diesel), incl. accijns & btw |

## Methode

1. **Alleen faillietverklaringen.** Op faillissementen.com is gefilterd op de status
   `Faillissement`. Surséances van betaling, schuldsaneringen (WSNP) en wijzigingen zijn
   uitgesloten, zodat één onderneming niet dubbel meetelt.
2. **Twee reeksen.**
   - *CBS* — de volledige, officiële populatie (jaarlijks 2009–2025, maandelijks 2009-01 → 2026-08).
   - *faillissementen.com* — 866 zaken (15-04-2005 → 01-10-2026) met detailpagina's; gebruikt voor
     **provincie**, **vestigingsplaats**, **rechtsvorm** en **sub-branche**.
3. **Provincie** is afgeleid uit de 4-cijferige postcode. 16 van de 866 zaken hadden geen
   bruikbare postcode.
4. **MKB vs. groot** is een proxy op rechtsvorm (eenmanszaak/VOF/CV vs. BV/NV) en, voor de
   officiële reeks, CBS' eigen splitsing *natuurlijke personen met eenmanszaak* vs.
   *bedrijven en instellingen*.

## Belangrijkste bevindingen

- **Het openbare archief van faillissementen.com is niet compleet.** Het bevat 866 zaken voor
  branche 49 over 2005–2026, terwijl CBS voor 2009–2025 alleen al een veelvoud registreert
  (bijv. 2024: site 80 vs. CBS 185; 2012: site 79 vs. CBS 285). Gemiddeld dekt de site ~40%
  van het officiële aantal. **Gebruik de CBS-reeks voor aantallen.**
- Het aantal uitgesproken faillissementen in SBI 49 daalde in 2025 naar **142** (was 185 in 2024,
  −23%). In 2026 staan er t/m augustus **102** genoteerd.
- **Correlatie met de dieselprijs is zwak** (Pearson r ≈ −0,30 op jaarbasis). De zichtbare
  piek in 2013 (285) valt samen met een hoogste dieselprijs, maar de daling na 2021 zet door
  terwijl de dieselprijs juist steeg — olieprijs alleen verklaart het patroon niet.
- Regionaal concentreert het wegvervoer zich in **Zuid-Holland** (185), **Noord-Brabant** (116)
  en **Limburg** (95) — de logistieke as naar de havens en het achterland.

## Reproduceren

```bash
python3 data/harvest_details.py     # haalt de detailpagina's van faillissementen.com op
```
CBS-reeksen komen uit de OData-API: `https://datasets.cbs.nl/odata/v1/CBS/<dataset>/Observations`.

## Kanttekeningen

- **Correlatie is geen causaliteit.** Conjunctuur, rente, loonkosten, brandstofkosten en de
  coronasteun (2020–2021) spelen allemaal mee.
- **KVK-koppeling ontbreekt.** Er is geen KVK-API-sleutel beschikbaar en KVK levert geen vrije
  bulkdata. CBS levert wel de officiële splitsing eenmanszaak/bedrijven.
- De site-data is een **afgeleide dataset** (statistieken en rechtsvorm), geen herdruk van
  artikelen; bronvermelding staat in de footer van het dashboard.
