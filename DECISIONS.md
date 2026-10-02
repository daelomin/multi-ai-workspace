# Decisions

Record durable decisions here. Do not use this file for temporary discussion.

## Template
### YYYY-MM-DD — Decision title
**Proposed by:**
**Reviewed by:**
**Status:** proposed / accepted / rejected / superseded

**Context**

**Options considered**

**Decision**

**Consequences**

---

### 2026-10-02 — Spécification par phases v1.0 comme feuille de route
**Proposed by:** HUMAN  
**Reviewed by:** CLAUDE  
**Status:** accepted

**Context**  
Le workspace multi-AI n’avait pas encore de projet métier. Une spécification détaillée (phases 0–7) a été fournie.

**Options considered**  
- Adopter `SPEC_PHASES.md` comme feuille de route canonique  
- Réécrire / simplifier avant engagement

**Decision**  
Adopter `SPEC_PHASES.md` v1.0 comme découpage livrable. `MASTER.md` reste l’état courant ; le détail des phases vit dans `SPEC_PHASES.md`.

**Consequences**  
Travail immédiat = Phase 0. Jalons GO/NO-GO humains en fin de chaque phase. Stack figée phases 0–1 (Compose, pas K8s/Kafka).

### 2026-10-02 — Stack technique phases 0–1
**Proposed by:** HUMAN (via SPEC)  
**Reviewed by:** CLAUDE  
**Status:** superseded

**Context**  
Besoin d’un environnement reproductible avant développement fonctionnel.

**Options considered**  
- Compose local (Postgres/PostGIS/TimescaleDB, Redis, Martin) + FastAPI + MapLibre  
- K8s dès le départ

**Decision**  
Stack initiale : Python 3.12, Postgres 16 + PostGIS 3.4 + TimescaleDB 2.15, FastAPI + Pydantic v2, MapLibre GL JS, Redis, Martin ; Docker Compose only. Packaging uv vs poetry encore ouvert.

**Consequences**  
Pas de Kafka/K8s avant phase 3. Choix uv/poetry à trancher en Phase 0.3.  
**Superseded by:** `2026-10-03 — Stack and pilot axis frozen for Phases 0–1` (D1) and `2026-10-03 — Python tooling: uv` (D2).

### 2026-10-02 — Axe pilote A11 Nantes–Paris
**Proposed by:** HUMAN (via SPEC)  
**Reviewed by:**  
**Status:** superseded

**Context**  
Phase 1 nécessite un seul axe pour valider la chaîne DATEX → LRS → carte.

**Options considered**  
- A11 Nantes–Paris (~350 km)  
- Autre axe (à proposer si licences/flux A11 insuffisants)

**Decision**  
Pilote proposé : A11 (trafic dense, mix DIR/concessionnaire, incidents fréquents). Validation formelle après inventaire sources.

**Consequences**  
LRS et collecteurs Phase 1 ciblent d’abord A11 ; bascule possible si accès DATEX bloqué.  
**Superseded by:** `2026-10-03 — Stack and pilot axis frozen for Phases 0–1` (D1).

### 2026-10-03 — Stack and pilot axis frozen for Phases 0–1
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D1 · P0-1

**Context**  
Phase 0 required a single frozen stack and pilot corridor so agents stop describing the stack as both frozen and proposed.

**Options considered**  
- Freeze now for Phases 0–1 (A11 pilot only)  
- Keep stack / axis as proposed until data-source inventory completes

**Decision**  
Stack frozen for Phases 0–1 as of 2026-10-03; scope: A11 pilot only for Phases 0–1. Stack components remain those recorded for phases 0–1: Python 3.12, Postgres 16 + PostGIS + TimescaleDB, FastAPI, MapLibre, Redis, Martin, Docker Compose only. Expansion beyond A11 is out of scope until later phases; `docs/scope.md` (P1-12) must agree with this ADR.

**Consequences**  
`MASTER.md` matches this freeze. No Kubernetes / Kafka before phase 3. Geographic expansion is deferred; LRS and collectors target A11 first.

### 2026-10-03 — Python tooling: uv
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D2 · P0-2

**Context**  
Packaging choice (uv vs poetry) was still open in earlier notes while the phase-0–1 stack was otherwise fixed.

**Options considered**  
- `uv`  
- poetry

**Decision**  
Python tooling is **`uv`**. All future Python tooling commands will use `uv` (run, sync, lock, add).

**Consequences**  
Bootstrap, CI and docs must use `uv`; poetry is not adopted.

### 2026-10-03 — Licence intent: internal use only
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D3 · P0-7

**Context**  
A licence posture was needed before drafting `LICENSE` text and before source-licence work in P0-4 constrains derived-data scope.

**Options considered**  
- Internal use only, re-evaluate openness at end of Phase 3  
- Open-source licence from the start

**Decision**  
Licence intent: **internal use only — re-evaluate openness at the end of Phase 3.** Exact proprietary licence text and scope (code, configuration, documentation, derived data) remain CLAUDE’s P0-7 work; do not add MIT/Apache-2.0.

**Consequences**  
No public redistribution posture until the Phase 3 re-evaluation. `LICENSE` file still to be written (not part of this ADR).

### 2026-10-03 — Minimal coordination rules in P0
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D4 · P0-5 · P2-4

**Context**  
Multiple agents edit shared docs; irreversible product calls need a clear owner.

**Options considered**  
- Minimal P0 rules now; full task state machine later (P2)  
- Full multi-AI protocol immediately

**Decision**  
Minimal coordination rules in P0: status only in `CHANGELOG.md`, single-writer list for shared files, human approval for irreversible decisions. Full task state machine and review SLA in P2 (P2-4).

**Consequences**  
Rules live in `CONTRIBUTING.md` (P0-5). Agents must not silently approve each other’s work under the fuller P2 protocol later.

### 2026-10-03 — P0 split into gate and hygiene
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D5

**Context**  
Not every Phase 0 task must block Phase 1 equally.

**Options considered**  
- Single flat P0 list  
- Split into P0-gate (blocks Phase 1) and P0-hygiene (due by end of Phase 0)

**Decision**  
P0 is split into **P0-gate** (blocks Phase 1) and **P0-hygiene** (due by end of Phase 0).

**Consequences**  
Gate items must be owned and closed before Phase 1; hygiene items (e.g. docs index, risk register) may finish later in Phase 0.

### 2026-10-03 — ADRs live in DECISIONS.md
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D6 · P2-9

**Context**  
Need a single place for durable architecture / product decisions.

**Options considered**  
- Single `DECISIONS.md`  
- One file per ADR from the start

**Decision**  
ADRs live in **`DECISIONS.md`** (single file). Revisit if the P2 output-format work shows a need or the ADR count exceeds ~40.

**Consequences**  
No `docs/adrs/` tree for now; P2-9 may revisit format/location.

### 2026-10-03 — Direction relative to linear reference
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D7 · P1-4

**Context**  
Direction encoding must be consistent across DATEX sources and display labels.

**Options considered**  
- Store compass labels (`N/S/E/W`) as the canonical direction  
- Store direction relative to the road’s linear reference (DATEX-style positive/negative); derive compass for display

**Decision**  
Direction is stored **relative to the road's linear reference (DATEX-style positive/negative)**; compass labels (`N/S/E/W`) are derived for display only.

**Consequences**  
Spec and mappers must define linear-reference orientation per road and per-source mapping to `positive` / `negative` (P1-4); remove compass forms as stored identity.

### 2026-10-03 — Raw measures keyed on measurement site
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D8 · P1-2

**Context**  
DATEX measures come from point sensors; segment-level keys alone are the wrong grain for raw storage.

**Options considered**  
- Key raw measures on segment  
- Key raw measures on measurement site; derive per-segment tables separately

**Decision**  
Raw measures are keyed on the **measurement site**: `(site_id, source, source_ts)` as the base identity. The derived per-segment table has its own key built on `segment_id` plus a time identity (e.g. `(segment_id, source, bucket_ts)`); the exact derived key is fixed in P1-2 once the full `traffic_measure` model is written. D11 extends the raw key with `source_version`.

**Consequences**  
P1-1 must add `measurement_site` and site-to-segment mapping before collectors. Aggregates read from the current-revision view once D11 is applied.

### 2026-10-03 — Segment IDs: seg_<ulid>
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D9 · P1-3

**Context**  
Stable segment identifiers are required before LRS and matcher work.

**Options considered**  
- Human-readable composite IDs only  
- Opaque `seg_<ulid>` identifiers

**Decision**  
Segment IDs: **`seg_<ulid>`**.

**Consequences**  
P1-3 updates the spec; display/human labels remain separate from the primary key.

### 2026-10-03 — Template-vs-project split in P1
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D10 · P1-14

**Context**  
The repo currently mixes generic multi-AI workspace template material with the traffic-platform project.

**Options considered**  
- Split in P0  
- Raise the split to P1

**Decision**  
Template-vs-project split is raised to **P1** (P1-14): decide one repo or two, and act on it.

**Consequences**  
No template extraction work blocks Phase 0 gate items.

### 2026-10-03 — Source corrections: append revisions
**Proposed by:** HUMAN  
**Reviewed by:**  
**Status:** accepted  
**Refs:** D11 · P1-2 · P1-9 · P2-6

**Context**  
DATEX publishers can reissue a record for the same `(site_id, source, source_ts)`. Overwrite vs append affects provenance and aggregate rebuilds.

**Options considered**  
- **A · Overwrite** — upsert on `(site_id, source, source_ts)`; keep only the latest value  
- **B · Append revisions** — key becomes `(site_id, source, source_ts, source_version)` with a `traffic_measure_current` view

**Decision**  
Source corrections: **append revisions** (option B). Raw key becomes `(site_id, source, source_ts, source_version)`, where `source_version` is the publisher's record version/version time; a `traffic_measure_current` view (latest revision per key) feeds aggregates. Rejected: overwrite (loses the audit trail). Late-correction policy: corrections inside the continuous-aggregate refresh window are picked up automatically; older ones need an explicit refresh, logged in `docs/aggregates_history.md`.

**Consequences**  
P1-2 and P1-9 implement the key, view and late-correction logging; P2-6 provenance builds on this choice.
