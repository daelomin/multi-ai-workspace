# Data sources — Phase 0 (A11 pilot)

**Task:** P0-4 · **Owner:** CLAUDE (research and drafting) · **Verification:** HUMAN (licence and GDPR conclusions)
**Status:** draft — all facts checked on **2026-10-03** against the sources listed at the end. Items marked **⚠ unverified** could not be confirmed and must not be relied on until checked.

Licence and GDPR conclusions below are **proposals**, not legal determinations. They are recorded in `DECISIONS.md` only after HUMAN review (see P0-4 in `TODO.md`).

---

## Key findings

1. **The A11 is a concessioned motorway, so its live data is not open data.** Open real-time datasets on the national access point (PAN) cover the **non-concessioned** national network run by the DIRs. Data from the motorway concession companies (SCA) is only available through Bison Futé's **restricted** portal, after registration and acceptance of a dedicated reuse licence. [S1][S2][S3][S4]
2. **For concession companies, only traffic volumes are currently offered** on that portal. Speed and travel-time data for SCAs is described as planned for a future, separate portal. If that is still true, the A11 pilot would get volumes but not speeds from official channels. [S3][S4] ⚠ Current status to confirm when requesting access.
3. **The A11 has two concessionaires, both in the VINCI Autoroutes group:** Cofiroute for most of the route, and **ASF for Le Mans–Angers**. `TODO.md` P0-4 row 3 named only Cofiroute. [S6][S7]
4. **All official feeds found are DATEX II version 2.2.2,** not version 3. The parser (P0-14, Phase 1 collectors) must target 2.2.2. [S1][S2]
5. **The reuse licence for live data (Bison Futé "action b", version 9) allows commercial use, derived products and redistribution,** with attribution, a visible last-update time, and the same terms passed on to third parties. This is compatible with D3 (internal use only). [S5]
6. **No personal data was found in any Phase 0 source;** they publish events and per-station aggregates. Floating-car data (FCD) only appears with commercial providers, which are deferred. [S1][S2][S3]

## Actions for HUMAN

These block the A11 pilot's real data. None of them blocks P0-13 (scaffold) or P0-14 (smoke test), which can use the open DIR feeds and synthetic files.

- [ ] **Request restricted access:** email `diffusion-numerique@info-routiere.gouv.fr`, accepting the action b reuse licence (v9) and, if needed, action c. Ask specifically for (a) A11 coverage from Cofiroute and ASF, (b) whether speed/travel time is available for SCAs, and (c) the feed URLs and update rates. [S3][S4]
- [ ] **Note the yearly duty:** licence holders file a compliance declaration every year before **13 July**. [S4]
- [ ] **Decide (if finding 2 is confirmed)** whether a volume-only A11 pilot still meets the project's goals, or whether a fallback is needed. This is a scope question for D1, not something CLAUDE should settle.
- [ ] **Verify** the licence and GDPR conclusions in this file before they are recorded in `DECISIONS.md`.

---

## A11 operators

| Section | Operator | Toll | Source |
|---|---|---|---|
| Paris area (Saint-Arnoult toll) – Le Mans (exit 8) | Cofiroute (VINCI Autoroutes) | yes | [S6] |
| Le Mans south (exit 9) – Angers (Gâtignolle) | ASF (VINCI Autoroutes) | yes, except exit 13 | [S6] |
| Angers – Nantes ring road | Cofiroute (VINCI Autoroutes) | yes, except the Angers and Nantes bypasses | [S6] |

⚠ **Unverified:** whether the toll-free Angers and Nantes bypasses are still operated by the concessionaire or by a DIR (likely DIR Ouest). If a DIR operates them, their data would be in the open DIR feeds. Check with the SCA access request or a road-authority map before adding a DIR row.

---

## Phase 0 sources

### S-1 · DIR road events (PAN / data.gouv.fr)

| Field | Value |
|---|---|
| Publisher | Point d'Accès National transport.data.gouv.fr; produced by the DIRs |
| URL | https://www.data.gouv.fr/datasets/62558686864eeafd3af07eac · open directory `http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/grt/RRN/` |
| Content | Diversions, current and planned roadworks, congestion, unexpected and dangerous events |
| Format | DATEX II **2.2.2** XML (+ HTML summaries) |
| Update frequency | Real time for the main XML file; hourly aggregations also published |
| Coverage | **Non-concessioned** national network only |
| A11 coverage | **No** (A11 is concessioned), except possibly the toll-free bypasses ⚠ |
| Licence | Licence Ouverte / Open Licence 2.0 |
| Contact | via the PAN dataset page |
| Personal data | None identified (event records) |
| Use in Phase 0 | Real DATEX II 2.2.2 samples for the parser and the P0-14 smoke test |

### S-2 · DIR traffic state (PAN / data.gouv.fr, "QTV-DIR")

| Field | Value |
|---|---|
| Publisher | Point d'Accès National transport.data.gouv.fr; produced by the DIRs |
| URL | https://www.data.gouv.fr/datasets/626113a9e7a3010e25422e7f · open directory `http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/QTV-DIR/` |
| Content | Average speed, flow (vehicles/hour) and traffic state ("Traficolor": fluid, dense, congested, impossible, unknown) from counting stations |
| Format | DATEX II **2.2.2** XML and CSV |
| Update frequency | Every 6 minutes (aggregated files) |
| Coverage | **Non-concessioned** national network; around 20 major cities named |
| A11 coverage | **No** (concessioned), except possibly the bypasses ⚠ |
| Licence | Licence Ouverte 2.0 per data.gouv.fr [S2]; ⚠ Bison Futé's page lists the same DIR traffic data under the action b licence v9 [S4]. The stricter of the two (v9's attribution and timestamp duties) is the safe assumption until clarified. |
| Personal data | None identified (station aggregates) |
| Use in Phase 0 | Real `MeasuredDataPublication` samples for the parser and the smoke test |

⚠ The open `tipi` directories could not be listed from the research environment on 2026-10-03 (one returned 404). Check the exact file paths from a browser before coding against them.

### S-3 · Bison Futé restricted portal — "action b" (DIR + SCA live data)

| Field | Value |
|---|---|
| Publisher | Bison Futé (French ministry for transport), national access point under EU Regulation 2015/962 |
| URL | Restricted: `http://tipi.bison-fute.gouv.fr/bison-fute-restreint/publications-restreintes/grt/ACTION-B/` |
| Content | Dynamic data (closures, accidents, weather, speed restrictions…) and traffic data (volume, congestion, travel times) |
| SCA coverage | **Traffic volumes only** for concession companies; SCA speed and travel time described as planned for a separate portal ⚠ |
| Format | DATEX II (version to confirm on access; the open DIR equivalents are 2.2.2) |
| A11 coverage | **Expected yes**, via Cofiroute and ASF as SCAs ⚠ to confirm on access |
| Access | Registration by email to `diffusion-numerique@info-routiere.gouv.fr`, accepting the reuse licence |
| Licence | "Licence de réutilisation des données numérisées d'informations en temps réel sur la circulation", action b, **v9** (page updated 8 April 2026) |
| Licence terms (summary) | Attribution "Information provided by [producer]" with the Bison Futé logo and link where feasible; last-update time shown to end users; redistribution allowed on the same terms; derived products and commercial use allowed; no alteration or misrepresentation; respect traffic-management plans; 3 years, renewable automatically; access can be revoked after repeated breaches |
| Obligations | Yearly compliance declaration before 13 July |
| Credentials | Yes → `.env.example` (`BISON_FUTE_RESTRICTED_USER`, `BISON_FUTE_RESTRICTED_PASSWORD`) |
| Personal data | None identified (events and aggregates) |

### S-4 · Bison Futé restricted portal — "action c" (safety-related traffic information)

| Field | Value |
|---|---|
| URL | Restricted: `tipi.bison-fute.gouv.fr/bison-fute-restreint/publications-restreintes/grt/ACTION-C/` |
| Content | Road-safety-related traffic information (EU "SRTI" data) |
| Licence | Separate action c reuse licence (latest version found: "vdef-3-3") ⚠ terms not reviewed |
| Relevance | Optional for Phase 0; useful for incident attribution later. Request together with action b to avoid a second application. |

### S-5 · VINCI Autoroutes (Cofiroute and ASF) — direct

| Field | Value |
|---|---|
| Open data | Only one dataset on data.gouv.fr: carpool car parks. **No real-time traffic or DATEX dataset published directly.** [S8] |
| Route to A11 data | Through S-3 (Bison Futé restricted portal, as SCAs) |
| Direct feed | ⚠ Unknown. Ask VINCI Autoroutes only if S-3 turns out not to cover the A11 or lacks speeds. |

---

## Deferred to Phase 1+ (outside the A11 pilot)

| Source | Reason |
|---|---|
| APRR, SANEF, other concessionaires | Not on the A11; reached through S-3 later if needed |
| Other DIRs | Not on the A11 (pending the bypass check above) |
| Michelin Travel Partner, TomTom | Commercial; FCD-based, so a GDPR assessment is required before use. Contacts listed by Bison Futé: `realtime@tp.michelin.com`, `carto-france@tomtom.com` [S3] |

---

## Direction conventions (for P1-4 / D7)

DATEX II location referencing with Alert-C expresses direction relative to a **location table**, not compass points. [S9] documents DATEX II v3.3; the Alert-C model is the same idea in 2.2.2, but ⚠ confirm the exact element names against the 2.2.2 schema used by the feeds.

- `alertCDirectionCoded` says whether the event is located by navigating the table with **positive** or **negative** offsets. The positive direction follows the order of the table's points ("Alert-C chaining").
- `alertCAffectedDirection` says which traffic is affected: **aligned**, **opposite** or **both**.

This matches D7 (store direction relative to the road's linear reference; derive compass labels for display). Two things remain for P1-4:

- ⚠ Identify the French Alert-C location table version used by each feed, and whether SCA feeds use Alert-C, the French PR system, or both.
- Map each source's `positive`/`negative` to our linear reference once real files are available; keep that mapping in this file, per source.

---

## GDPR assessment (proposal — HUMAN/legal review required)

| Source | Personal data? | Basis |
|---|---|---|
| S-1 DIR events | No | Event records describing road conditions |
| S-2 DIR traffic state | No | Aggregates per counting station (flow, mean speed, state) |
| S-3 action b (DIR + SCA) | No | Same kinds of events and aggregates |
| S-4 action c | No (to confirm when terms are reviewed) | Safety events |
| Commercial FCD (deferred) | **Likely yes** | Derived from vehicle traces; needs legal basis, retention and anonymisation review before any use |

Proposed conclusion: Phase 0 sources contain no personal data, so no GDPR legal basis is needed for them. This stays a proposal until HUMAN confirms it.

---

## Sources (checked 2026-10-03)

- [S1] data.gouv.fr — [Événements routiers sur le réseau routier national non concédé](https://www.data.gouv.fr/datasets/62558686864eeafd3af07eac)
- [S2] data.gouv.fr — [État de circulation en temps réel sur le réseau national routier non concédé](https://www.data.gouv.fr/datasets/626113a9e7a3010e25422e7f)
- [S3] Bison Futé — [Informations en temps réel sur la circulation (action b)](https://www.bison-fute.gouv.fr/action-b.html)
- [S4] Bison Futé — [Directive STI, data access and licences](https://www.bison-fute.gouv.fr/directive-sti,id_sous_rubrique10402.html) and [Données sur le RRN](https://www.bison-fute.gouv.fr/donnees-sur-le-rrn,langes.html)
- [S5] Bison Futé — [Reuse licence, action b, v9 (PDF)](https://www.bison-fute.gouv.fr/IMG/pdf/Licence_reutilisation_donnees_action_b_-_v9.pdf)
- [S6] Wikipedia (FR) — [Autoroute A11 (France)](https://fr.wikipedia.org/wiki/Autoroute_A11_(France)) — secondary source; confirm section boundaries with the operators
- [S7] data.gouv.fr — [VINCI Autoroutes organisation page](https://www.data.gouv.fr/fr/organizations/vinci-autoroutes/) (lists Cofiroute and ASF among its concession companies)
- [S8] Same page as [S7] (published datasets)
- [S9] DATEX II documentation — [Alert-C location referencing](https://docs.datex2.eu/v3.3/location/2_Alert-C.html)
