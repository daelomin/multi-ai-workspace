# MASTER DOCUMENT

## Project
**Name:** Plateforme nationale de trafic routier

**One-line objective:** Ingérer, cartographier, expliquer et prévoir le trafic routier français (puis européen) à partir de flux DATEX II et d’un LRS national.

## Current state

### What exists
- Workspace multi-AI (protocoles, agents, templates)
- Spécification par phases v1.0 : `docs/SPEC_PHASES.md`
- Décisions D1–D11 enregistrées dans `DECISIONS.md` (2026-10-03)

### What is being built
- Phase 0 — Fondations & cadrage (données, stack, conventions, LRS pivots)

### Current blockers
- Accès / licences DATEX II non encore inventoriés
- Objectif et critères d’acceptation métier à figer (GO/NO-GO phase 0)

## Scope

### In scope
- Phases 0–7 telles que décrites dans `docs/SPEC_PHASES.md`
- Stack frozen for Phases 0–1 as of 2026-10-03; scope: A11 pilot only for Phases 0–1
- Axe pilote : A11 Nantes–Paris (~350 km)
- Stack phases 0–1 : Python 3.12, Postgres 16 + PostGIS + TimescaleDB, FastAPI, MapLibre, Redis, Martin, Docker Compose; tooling Python : `uv`

### Out of scope
- Kubernetes / Kafka avant phase 3
- Prédiction ML avant phase 6 (historique + baselines d’abord)
- Couverture européenne avant phase 7
- Extension géographique au-delà de l’A11 avant la fin des phases 0–1

## Architecture / approach

- Ingestion DATEX II (événements + mesures) → modèle interne → LRS / segments → API FastAPI + tuiles MVT (Martin) → frontend MapLibre
- Source de vérité projet : ce fichier ; détail livrable : `docs/SPEC_PHASES.md`
- Décisions durables : `DECISIONS.md` ; file d’attente : `TODO.md`

## Current priorities
1. Inventaire sources DATEX II + licences (`docs/data_sources.md`)
2. Conventions (IDs, unités, CRS, codes incident) alignées sur D1–D11
3. Environnement reproductible (bootstrap canonique) + smoke test DATEX factice → Postgres → MapLibre

## Constraints
- Docker Compose only en phases 0–1
- Timestamps UTC ISO 8601 ; géométrie EPSG:4326 (stockage), EPSG:2154 (métrique)
- Identifiants : `<network>_<road>_<pr>_<direction>_<seq>` (segments : `seg_<ulid>` per D9)
- Humains seuls pour GO/NO-GO de fin de phase
- Licence intent : internal use only until end of Phase 3 (D3)

## Open questions
- Quelle(s) source(s) DATEX réellement accessibles pour le pilote A11 ?
- Hébergement cible phase 3 (cloud / on-prem) avant estimation budget ?

## Latest status
**Last updated:** 2026-10-03
**Last editor:** CURSOR
