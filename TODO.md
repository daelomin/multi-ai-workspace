# TODO

## P0 — Critical (Phase 0)
- [ ] Inventaire sources DATEX II (DIR, Bison Futé, SANEF, APRR, Vinci, …) → `docs/data_sources.md`
- [ ] Vérifier licences (ouverture, rediffusion, dérivation) + contacts / conventions
- [ ] Valider axe pilote A11 Nantes–Paris (~350 km) et justification
- [ ] Écrire / revoir conventions (IDs, unités, timestamps, codes incident, CRS)
- [ ] Scaffold `dev/` : docker-compose (Postgres+PostGIS+TimescaleDB, Redis, Martin), `.env.example`, `Makefile` (`make up`)
- [ ] Smoke test bout-en-bout factice : XML DATEX → Postgres → MapLibre
- [ ] GO/NO-GO fin phase 0 → lancement phase 1

## P1 — Important (Phase 1 prep / early)
- [ ] Référentiels pivots LRS : `road`, `pr_point`, `pr_range` + dictionnaires routes / sens
- [ ] Collecteur DATEX événements (`parser` / `mapper` / `loader` / `scheduler`)
- [ ] Collecteur DATEX trafic (`MeasuredDataPublication`)
- [ ] Segments A11 (OSM Overpass → découpage → rattachement PR)
- [ ] Matcher DATEX → segment + table `incident_segment_link`
- [ ] Hypertable `traffic_measure` + API minimale + carte MapLibre

## P2 — Later (Phases 2+)
- [ ] Multi-sources `SourceAdapter` + déduplication incidents
- [ ] Extension 5–10 axes + observabilité Prometheus/Grafana
- [ ] LRS national + Kafka/Redpanda + compression TimescaleDB
- [ ] Attribution causale + itinéraires explicables
- [ ] Analytique / rapports / prédiction ML / API publique

## Agent assignments
| Task | Agent | Status | Notes |
|---|---|---|---|
| Populate SPEC_PHASES + MASTER/TODO | CLAUDE | done | Spec v1.0 ingested 2026-10-02 |
| Inventaire DATEX → data_sources.md | | todo | Phase 0.1 |
| Scaffold docker-compose / make up | | todo | Phase 0.3 |
