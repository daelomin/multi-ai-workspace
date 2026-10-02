# Spécification détaillée par phases — Plateforme nationale de trafic routier

**Version:** 1.0  
**Découpage:** 7 phases livrables, chacune autonome et validable.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble-des-phases)
2. [Phase 0 — Fondations & cadrage](#phase-0--fondations--cadrage)
3. [Phase 1 — MVP mono-axe mono-source](#phase-1--mvp-mono-axe-mono-source)
4. [Phase 2 — Multi-axes / multi-sources](#phase-2--multi-axes--multi-sources)
5. [Phase 3 — Échelle nationale](#phase-3--échelle-nationale)
6. [Phase 4 — Explicabilité & itinéraires](#phase-4--explicabilité--itinéraires)
7. [Phase 5 — Historisation & analytique](#phase-5--historisation--analytique)
8. [Phase 6 — Prédiction & ML](#phase-6--prédiction--ml)
9. [Phase 7 — Extensions & écosystème](#phase-7--extensions--écosystème)
10. [Annexes transverses](#annexes-transverses)

---

## Vue d'ensemble des phases

| Phase | Nom | Durée | Livrable principal |
|------:|-----|------:|--------------------|
| 0 | Fondations & cadrage | 3–4 sem | Environnement, référentiels, conventions |
| 1 | MVP mono-axe mono-source | 6–8 sem | Carte temps réel A11 + 1 source DATEX |
| 2 | Multi-axes / multi-sources | 8–10 sem | 5–10 axes, 3+ sources, incidents |
| 3 | Échelle nationale | 10–12 sem | Réseau complet, tuiles vectorielles |
| 4 | Explicabilité & itinéraires | 8–10 sem | Route explicable, attribution causale |
| 5 | Historisation & analytique | 6–8 sem | TimescaleDB, dashboards, rapports |
| 6 | Prédiction & ML | 12–16 sem | Prévisions +15/30/60 min |
| 7 | Extensions & écosystème | continu | Europe, alertes, API publique |

---

## Phase 0 — Fondations & cadrage

### Objectifs

Poser les bases techniques, juridiques et méthodologiques avant tout développement fonctionnel.

### Périmètre

#### 0.1 Cadre juridique et données

- Inventaire des sources DATEX II accessibles (DIR, Bison Futé, SANEF, APRR, Vinci, etc.)
- Vérification des licences : ouverture, rediffusion, dérivation
- Rédaction d'une fiche par source : URL, format, fréquence, couverture, licence, contact
- Inscription aux flux (certains nécessitent une convention)

**Livrable :** `data_sources.md` avec 1 fiche par source.

#### 0.2 Choix du périmètre pilote

- Sélection de 1 axe majeur (ex. : A11 Nantes–Paris, ~350 km)
- Justification : trafic dense, mix DIR/concessionnaire, incidents fréquents

#### 0.3 Environnement technique

```text
dev/
  docker-compose.yml   # Postgres+PostGIS+TimescaleDB, Redis, tile server
  .env.example
  Makefile
infra/
  terraform/           # ou k8s/ si cloud
  ansible/
ci/
  .gitlab-ci.yml       # ou github actions
  lint, test, build, deploy
```

**Stack initiale figée :**

- Python 3.12, uv ou poetry
- Postgres 16 + PostGIS 3.4 + TimescaleDB 2.15
- FastAPI + Pydantic v2
- MapLibre GL JS
- Redis (cache + streams)
- Martin (tuile vectorielle)
- Docker Compose uniquement (pas de K8s en phase 0–1)

#### 0.4 Conventions

- **Identifiants :** `<network>_<road>_<pr>_<direction>_<seq>` (ex. : `NAT_A11_102_N_0001`)
- **Unités :** SI, km/h, m, s, veh/h
- **Timestamps :** UTC ISO 8601 ; colonnes `source_ts`, `ingest_ts`, `valid_from`, `valid_to`
- **Codes incident :** mapping DATEX II `IncidentType` → énumération interne (`accident`, `roadworks`, `closure`, `obstruction`, `weather`, `breakdown`, `other`)
- **Convention géométrique :** EPSG:4326 stockage, EPSG:2154 calculs métriques

#### 0.5 Référentiels pivots

- **LRS** (Linear Referencing System) : tables `road`, `pr_point`, `pr_range`
- **Dictionnaire de routes :** A1..A999, N1..N999, D…
- **Dictionnaire de sens :** `N`, `S`, `E`, `W`, `NORD_SUD`, `SUD_NORD`, `EST_OUEST`, `OUEST_EST`, `BIDIR`

### Critères d'acceptation phase 0

- [ ] Toutes les sources identifiées avec licence documentée
- [ ] Environnement reproductible en 1 commande (`make up`)
- [ ] 1 test bout-en-bout factice : XML DATEX → insertion Postgres → affichage MapLibre
- [ ] Conventions écrites et revues par l'équipe

### Risques

- Refus d'accès à certains flux → prévoir source de repli (Open Data SNCF Réseau, data.gouv.fr)
- Incohérences de format entre opérateurs → parser tolérant dès le départ

---

## Phase 1 — MVP mono-axe mono-source

### Objectifs

Démontrer la chaîne complète sur 1 axe, 1 source événementielle, 1 source trafic, en conditions réelles.

### Périmètre

#### 1.1 Ingestion

**Collecteur DATEX II Événements**

```text
collector_datex_events/
  parser.py       # lxml, XSD DATEX II v3
  mapper.py       # XML → modèle interne
  loader.py       # upsert Postgres
  scheduler.py    # APScheduler, 60s
```

- Parse XML DATEX II : `SituationPublication`, `Situation`, `SituationRecord`
- Extraction : type, sévérité, localisation linéaire, période, description
- Idempotence : clé = `source_id` + `version_time`
- Gestion des suppressions / mises à jour (`cancel`, `update`)

**Collecteur DATEX II Trafic (mesures capteurs)**

- Parse `MeasuredDataPublication`
- Extraction : PR, sens, vitesse, débit, taux d'occupation, timestamp
- Insertion en staging puis agrégation

#### 1.2 Référentiel segments (LRS)

Construit manuellement sur l'axe pilote :

- Extraction OSM via Overpass API sur la bbox A11
- Fusion des way en itinéraire continu
- Découpage : 500 m ou entre échangeurs
- Rattachement PR DATEX ↔ PR OSM via points connus (échangeurs)

**Tables :**

```sql
CREATE TABLE road_segment (
  segment_id      TEXT PRIMARY KEY,
  road            TEXT NOT NULL,
  direction       TEXT NOT NULL,
  pr_start        NUMERIC,
  pr_end          NUMERIC,
  length_m        NUMERIC,
  speed_limit     SMALLINT,
  geom            GEOMETRY(LINESTRING, 4326),
  valid_from      TIMESTAMPTZ,
  valid_to        TIMESTAMPTZ,
  UNIQUE (road, direction, pr_start, valid_from)
);
CREATE INDEX ON road_segment USING GIST (geom);
```

#### 1.3 Matching DATEX → Segment

Module `matcher.py` :

1. Résolution route : nom DATEX → route interne (dictionnaire + fuzzy)
2. Résolution PR : `pr_value` → `ST_LineLocatePoint`
3. Résolution sens
4. Fenêtre : segment couvrant `[pr_start, pr_end]`
5. Cas ambigus : log + revue manuelle hebdo (objectif &lt;5% d'ambiguïté)

**Résultat :** table `incident_segment_link(incident_id, segment_id, overlap_ratio)`.

#### 1.4 Modèle trafic

Table `traffic_measure` (hypertable TimescaleDB) :

```sql
CREATE TABLE traffic_measure (
  segment_id   TEXT NOT NULL,
  ts           TIMESTAMPTZ NOT NULL,
  source       TEXT NOT NULL,
  avg_speed    REAL,
  flow         REAL,
  occupancy    REAL,
  travel_time  REAL,
  confidence   SMALLINT
);
SELECT create_hypertable('traffic_measure', 'ts');
```

Classification état (voir spec §7) calculée à la volée.

#### 1.5 API FastAPI (minimale)

```http
GET /health
GET /segments?bbox=...
GET /segments/{id}
GET /segments/{id}/traffic?from&to
GET /incidents?bbox=...
GET /tiles/{z}/{x}/{y}.mvt   # via Martin
```

#### 1.6 Frontend MapLibre

- Carte plein écran centrée sur l'axe
- Couche segments colorés (MVT, source segments)
- Popup au clic : vitesse, débit, état, incidents actifs
- Rafraîchissement : polling 30s (SSE plus tard)

### Livrables phase 1

- 1 axe affiché en temps réel
- Incidents DATEX positionnés
- Code documenté, tests unitaires (&gt;70% sur parsers et matcher)
- Documentation utilisateur (README + tuto déploiement)

### Critères d'acceptation

- [ ] ≥ 95% des incidents DATEX correctement rattachés à un segment
- [ ] Latence bout-en-bout ingestion → affichage &lt; 3 min
- [ ] API p95 &lt; 200 ms sur `/segments` (bbox axe complet)
- [ ] Carte à 60 FPS sur 5 000 segments
- [ ] Aucune perte de mesure sur 7 jours consécutifs (comptage source vs DB)

### Risques

- Parsing DATEX complexe → prévoir 2 semaines tampon
- Ambiguïté LRS → gel partiel acceptable avec marquage `confidence=low`

---

## Phase 2 — Multi-axes / multi-sources

### Objectifs

Passer de 1 à 5–10 axes, intégrer 3+ sources hétérogènes, gérer les conflits.

### Périmètre

#### 2.1 Multi-sources

- Ajouter 2–3 sources DIR / concessionnaires
- Abstraction `SourceAdapter` :

```python
class SourceAdapter(Protocol):
    def fetch(self) -> list[RawEvent]: ...
    def parse(self, raw) -> list[InternalEvent]: ...
    def reference(self) -> SourceMeta: ...
```

- Registre de sources configurable (YAML)
- Politique de conflit : priorité source + fraîcheur + déduplication sémantique

#### 2.2 Déduplication d'incidents

Deux sources peuvent décrire le même accident :

- Clé de dédup : `(road, pr_center ± 500m, type, time_window ± 15min)`
- Fusion : garder l'événement le plus complet, tracer `merged_from`
- Résolution manuelle possible (back-office)

#### 2.3 Multi-axes

- Extension LRS à 5–10 axes (A11, A71, A85, A10, A6…)
- Automatisation partielle du rattachement PR ↔ OSM
- Script de contrôle qualité : détection de trous, doublons, incohérences de sens

#### 2.4 UI multi-axes

- Filtre par axe
- Recherche par PR ou par nom de ville
- Vue liste des incidents actifs (tri par sévérité, axe, ancienneté)

#### 2.5 Observabilité

- Prometheus : métriques par source (événements/min, erreurs, latence)
- Grafana : dashboard ingestion + API
- Alerting : source muette &gt; 15 min, taux d'erreur &gt; 5%

### Critères d'acceptation

- [ ] 5 axes complets, &lt;10% segments manquants
- [ ] 3 sources actives, dédup fonctionnelle (&gt;90% des doublons détectés)
- [ ] Métriques exposées sur `/metrics`
- [ ] Back-office dédup opérationnel

### Risques

- Complexité opérationnelle × sources → fort besoin d'abstraction
- Conflits non résolubles automatiquement → charge manuelle

---

## Phase 3 — Échelle nationale

### Objectifs

Couvrir l'intégralité du réseau routier national (autoroutes + nationales), soit ~200 000 segments.

### Périmètre

#### 3.1 LRS national

- Construction automatique complète depuis OSM
- Pipeline batch :
  1. Extraction OSM France (Geofabrik dump)
  2. Filtre `highway=motorway|trunk|primary`
  3. Découpage et rattachement PR (source IGN Route 500)
  4. Contrôle qualité (couverture, continuité)
- Versionnage obligatoire : `road_segment_version`
- Processus de mise à jour hebdo sans casser l'historique

#### 3.2 Ingestion à l'échelle

- 50 000 événements/min en pic
- Passage à Kafka justifié ici (ou Redpanda, plus léger)
- Topics : `raw.datex.events`, `raw.datex.traffic`, `normalized.events`, `normalized.traffic`, `enriched.incidents`
- Consumers scalables horizontalement

#### 3.3 Stockage

- TimescaleDB compression native :

```sql
ALTER TABLE traffic_measure SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'segment_id,source',
  timescaledb.compress_orderby = 'ts DESC'
);
SELECT add_compression_policy('traffic_measure', INTERVAL '7 days');
```

- Rétention : 30 j détaillé, 2 ans agrégé 5 min
- Continuous aggregates :
  - `traffic_measure_5min`
  - `traffic_measure_1h`
  - `traffic_daily_stats`

#### 3.4 Tuiles vectorielles nationales

- Martin en production, cache CDN
- Génération MVT à la volée + cache Redis (TTL 30s)
- Zoom min/max par couche, simplification géométrique
- Pré-génération des zooms bas (0–8) en statique

#### 3.5 Frontend national

- Vue France entière
- Zoom progressif : agrégation par axe aux zooms bas, segment aux zooms hauts
- Heatmap nationale (densité de congestion)
- Performance cible : 60 FPS sur 200k segments

#### 3.6 API public-ready

- Rate limiting (Redis)
- Clés API
- Cache HTTP (ETag, Cache-Control)
- Pagination sur toutes les listes
- Versionnement `/v1/`

### Critères d'acceptation

- [ ] ≥ 95% du réseau national couvert
- [ ] Ingestion à 50k evt/min tenue 1h sans perte
- [ ] Carte nationale fluide (60 FPS) sur machine standard
- [ ] API p95 &lt; 200 ms sur toutes routes
- [ ] Compression TimescaleDB active, gain &gt;8× vérifié
- [ ] 0 perte de données sur 30 jours

### Risques

- Coût infra → dimensionner (estimation : 3–5 nœuds K8s, 500 Go–1 To SSD)
- Mises à jour OSM cassant des IDs → mitigé par versionnage phase 0

---

## Phase 4 — Explicabilité & itinéraires

### Objectifs

Livrer la valeur différenciante : expliquer les ralentissements et calculer des itinéraires explicables.

### Périmètre

#### 4.1 Baseline historique

Pour chaque segment, profil de vitesse attendue :

- Par heure × jour de semaine × mois
- Calculé sur 90 j glissants
- Stocké dans `segment_baseline(segment_id, hour_dow, mean_speed, p10, p90)`

Anomalie = `observed_speed - baseline_speed` (bornée).

#### 4.2 Attribution causale

Modèle v1 (règles + statistiques) :

1. Si incident actif sur segment → candidat principal
2. Contribution estimée = `(baseline - observed) / (baseline - min_observed_segment)`
3. Si plusieurs incidents → répartition proportionnelle à sévérité × recouvrement
4. Résidu (non expliqué par incidents) → attribué à « densité de trafic »
5. Contrainte : somme des `impact_pct` = 100%

**Sortie :**

```json
{
  "segment_id": "NAT_A11_102_N_0001",
  "ts": "2026-09-24T17:30:00Z",
  "delay_s": 720,
  "causes": [
    {"type": "roadworks", "incident_id": "INC123", "impact_pct": 40, "delay_s": 288},
    {"type": "traffic_density", "impact_pct": 60, "delay_s": 432}
  ],
  "confidence": "medium"
}
```

Note explicite : c'est une inférence, pas une vérité terrain. L'UI doit le refléter (badge « estimation »).

#### 4.3 Calcul d'itinéraire

- Graphe routier national en mémoire (NetworkX ou igraph) ou pgRouting
- Algo : Contraction Hierarchies pour requêtes &lt; 500 ms
- Poids : temps de parcours temps réel (pas distance)
- Alternatives : k-shortest paths (Yen)

#### 4.4 Itinéraire explicable

Pour un trajet `(from, to)` :

1. Calcul meilleur chemin
2. Pour chaque segment du chemin : anomalie + causes
3. Agrégation par cause :

```json
{
  "distance_km": 710,
  "duration_min": 420,
  "delay_min": 37,
  "causes": [
    {"road": "A71", "reason": "accident", "delay_min": 12, "incident_id": "INC_a"},
    {"road": "A85", "reason": "roadworks", "delay_min": 8, "incident_id": "INC_b"},
    {"road": "A10", "reason": "traffic_density", "delay_min": 17}
  ],
  "segments": []
}
```

#### 4.5 UI explicable

- Panneau « Pourquoi ce retard ? »
- Chronologie des causes avec icônes
- Comparaison avec temps théorique (baseline)
- Lien vers incident DATEX source

### Critères d'acceptation

- [ ] Attribution causale validée manuellement sur 100 cas annotés (accord ≥ 70%)
- [ ] Itinéraire Nantes → Lyon calculé en &lt; 500 ms
- [ ] Décomposition retard cohérente (somme segments = total ± 5%)
- [ ] Documentation des limites de l'inférence

### Risques

- Sur-interprétation → communiquer les incertitudes
- Validation coûteuse → prévoir jeu de test annoté dès phase 3

---

## Phase 5 — Historisation & analytique

### Objectifs

Exploiter les données accumulées : statistiques, rapports, détection d'anomalies.

### Périmètre

#### 5.1 Historisation consolidée

- Toutes hypertables configurées
- Politiques de rétention appliquées
- Snapshots mensuels exportables (Parquet) pour archivage froid (S3)

#### 5.2 Requêtes analytiques

Continuous aggregates TimescaleDB :

- `stats_road_hourly(road, hour, avg_speed, delay_min, incidents_count)`
- `stats_segment_daily(segment_id, date, congestion_min, max_delay)`
- `stats_zone_congestion` (clustering PostGIS sur segments saturés)

#### 5.3 Rapports

- Journalier : top 10 zones congestionnées, retards cumulés par axe
- Hebdomadaire : comparaison semaine N-1, tendances
- Mensuel : évolution long terme, cartes de chaleur
- Format : PDF (WeasyPrint) + API JSON
- Envoi programmable (email/Slack)

#### 5.4 Détection d'anomalies

- Sur séries temporelles : STL decomposition + seuil
- Sur incidents : détection d'événements inhabituels
- Alertes configurables par axe / zone

#### 5.5 Back-office analytique

- Interface web de consultation des rapports
- Filtres : période, axe, type d'incident
- Export CSV/Parquet

### Critères d'acceptation

- [ ] 2 ans de données conservées (détaillé 30 j + agrégé)
- [ ] Rapports PDF générés &lt; 30 s
- [ ] Détection anomalies : &lt; 5% faux positifs sur 3 mois test
- [ ] Requêtes analytiques &lt; 5 s sur fenêtre 30 j

---

## Phase 6 — Prédiction & ML

### Objectifs

Prévoir l'état du trafic à +15 / +30 / +60 min.

### Périmètre

#### 6.1 Features

- Historique segment (baseline, 7 j glissants)
- Calendrier : jour, heure, vacances scolaires (zone A/B/C), jours fériés
- Météo (Météo-France API ou OpenWeather)
- Incidents actifs
- Amont/aval du segment (features spatiales)
- Vitesse limite, classe de route

#### 6.2 Modèles

**v1 — XGBoost** par segment ou par cluster de segments similaires

- Cible : vitesse à t+15, t+30, t+60
- Métrique : MAE, MAPE
- Réentraînement hebdomadaire

**v2 — LSTM / TFT** (Temporal Fusion Transformer)

- Si v1 insuffisant
- Justification : dépendances temporelles longues, features multi-échelles

#### 6.3 Évaluation

- Split temporel strict (pas de fuite)
- Baseline naïve (vitesse t = vitesse t+15) comme référence
- Objectif : &gt; 15% de réduction MAE vs baseline naïve
- Monitoring de dérive (drift) mensuel

#### 6.4 API & UI

- `GET /forecast/segment/{id}?horizons=15,30,60`
- `POST /forecast/route` (prévision sur itinéraire)
- UI : courbe de prévision, bande de confiance
- Indicateur de fiabilité par horizon

#### 6.5 MLOps

- Versionnage modèles (MLflow)
- Registre de features (Feast ou simple Postgres)
- Réentraînement automatisé + validation avant mise en prod
- Shadow mode au démarrage

### Critères d'acceptation

- [ ] MAE &lt; baseline naïve − 15% sur +15 et +30 min
- [ ] MAE &lt; baseline naïve − 8% sur +60 min
- [ ] Latence prédiction &lt; 100 ms
- [ ] Pipeline MLOps documenté et reproductible

### Risques

- Qualité de données insuffisante → phase 5 obligatoire avant
- Overfitting → validation croisée temporelle stricte
- Communication : les prévisions sont probabilistes → UI honnête

---

## Phase 7 — Extensions & écosystème

### Objectifs

Ouvrir la plateforme, enrichir les données, s'étendre.

### Périmètre

#### 7.1 Données supplémentaires

- Péages (flux, tarifs)
- Bornes de recharge électrique (open data)
- Stations-service, aires de repos
- Météo temps réel (intégration fine)
- Parkings poids lourds

#### 7.2 Couverture européenne

- Flux DATEX II européens (Allemagne, Espagne, Italie, Benelux)
- Standardisation : modèle interne déjà DATEX-compatible
- Frontière : continuité du réseau, matching PR ↔ PR étrangers

#### 7.3 API publique

- Portail développeur
- Documentation OpenAPI interactive
- Tiers : gratuit (rate-limited), pro (SLA), entreprise (temps réel garanti)
- Webhooks pour incidents

#### 7.4 Alertes personnalisées

- Utilisateur : trajet récurrent + seuil de retard
- Notification : push, email, SMS
- Pertinence : ne notifier que si retard &gt; seuil ET cause identifiée

#### 7.5 Extensions produit

- Comparaison avec Waze / Google (mesure d'écart)
- Détection automatique d'anomalies en temps réel
- Rapports automatiques par collectivité
- Dashboard pour gestionnaires routiers

### Critères d'acceptation

- [ ] API publique versionnée, documentée, sous SLA
- [ ] Couverture ≥ 3 pays européens
- [ ] Alertes avec précision &gt; 80% (validation utilisateur)

---

## Annexes transverses

### A. Sécurité

- Secrets : Vault ou SOPS
- TLS partout
- Authentification API : clé + JWT (utilisateurs)
- Audit log des accès

### B. Performance cible

| Indicateur | Cible |
|------------|-------|
| Ingestion | 50 000 evt/min |
| API p95 | &lt; 200 ms |
| Carte | 60 FPS |
| Itinéraire | &lt; 500 ms |
| Disponibilité | 99,9 % |
| Fraîcheur données | &lt; 3 min |

### C. Tests

- Unitaires : parsers, matcher, algorithme causal
- Intégration : ingestion → API → MVT
- Bout-en-bout : scénario ville à ville
- Charge : Locust (API), k6 (ingestion)
- Qualité données : contrôles quotidiens automatiques

### D. Documentation obligatoire à chaque phase

- README technique
- Schéma base à jour (dbdocs ou SchemaSpy)
- Journal des décisions (ADR)
- Runbook exploitation

### E. Budget indicatif infra (phase 3)

| Poste | Coût mensuel estimé |
|-------|---------------------|
| Kubernetes (3 nœuds) | 300–600 € |
| Postgres managé + stockage | 200–400 € |
| Redis | 50–100 € |
| Kafka managé | 200–400 € |
| CDN + stockage objet | 50–150 € |
| Observabilité | 100–200 € |
| **Total** | **900–1 850 €/mois** |

---

## Récapitulatif jalons de décision

| Fin phase | Décision |
|-----------|----------|
| 0 | GO/NO-GO lancement phase 1 |
| 1 | GO/NO-GO extension multi-axes |
| 2 | GO/NO-GO national |
| 3 | GO/NO-GO investissement explicabilité |
| 4 | GO/NO-GO phase ML |
| 5 | GO/NO-GO prédiction |
| 6 | GO/NO-GO ouverture publique |

---

*Fin du document — `SPEC_PHASES.md` v1.0*
