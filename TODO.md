# TODO — Multi-AI Workspace (Final structure — some fields pending)

**Version:** v2.5 — 2026-10-03
**Versioning rule:** content edits (wording, filled fields, ticked items) bump the minor version (v1.1, v1.2…); structural changes or newly resolved decisions bump the major version (v2.0). Every bump gets a change-log line.

**Sources:** Claude `[C]` · previous assistant `[G]` · Grok `[Grok]` · ChatGPT GPT-5.6 Luna `[GPT]` · DeepSeek `[DS]` · merge notes `[merge]`
**Structure finalized:** 2026-10-03. Merged from the consolidated multi-agent review (signed by Grok, 2026-10-03); decisions D1–D11 resolved by the human owner on the same date. "Final" refers to the structure and decisions, not to every field: owners, cost envelope and metric thresholds are still open (see below).

**Status legend:** `[ ]` todo · `[~]` in progress · `[x]` done. Nothing is ticked until verified by a human or agent. **CURSOR ticks its own tasks** in the same pull request that completes them; HUMAN may review afterwards and untick if needed. Sign-offs and HUMAN-owned parts are never ticked by an agent.

---

## Resolved decisions (owner sign-off 2026-10-03)

These are decided. Items that must record them in `DECISIONS.md` still do so as tasks below; the `D#` tags show where each decision applies.

| # | Decision | Applies to |
|---|---|---|
| **D1** | Freeze stack and A11 pilot axis now. The ADR states scope as *"A11 pilot only for Phases 0–1"*; `docs/scope.md` later records the expansion plan and must agree with it. | P0-1, P1-12 |
| **D2** | Python tooling: **`uv`**. | P0-2 |
| **D3** | Licence intent: **internal use only — re-evaluate openness at the end of Phase 3.** | P0-7 |
| **D4** | Minimal coordination rules in P0 (status only in CHANGELOG, single-writer list, human approval for irreversible decisions). Full task state machine and review SLA in P2. | P0-5, P2-4 |
| **D5** | P0 split into **P0-gate** (blocks Phase 1) and **P0-hygiene** (due by end of Phase 0). | P0 sections |
| **D6** | ADRs live in **`DECISIONS.md`** (single file). Revisit if the P2 output-format work shows a need or the ADR count exceeds ~40. | All ADR items, P2-9 |
| **D7** | Direction stored **relative to the road's linear reference (DATEX-style positive/negative)**; compass labels (`N/S/E/W`) are derived for display only. | P1-4 |
| **D8** | Raw measures keyed on the **measurement site**: `(site_id, source, source_ts)`. The derived per-segment table has its own key built on `segment_id` plus a time identity (e.g. `(segment_id, source, bucket_ts)`); the exact key is fixed in P1-2 once the full `traffic_measure` model is written. | P1-2 |
| **D9** | Segment IDs: **`seg_<ulid>`**. | P1-3 |
| **D10** | Template-vs-project split raised to **P1**. | P1-14 |
| **D11** | Source corrections: **append revisions** (option B, resolved 2026-10-03). Raw key becomes `(site_id, source, source_ts, source_version)`, where `source_version` is the publisher's record version/version time; a `traffic_measure_current` view (latest revision per key) feeds aggregates. Rejected: overwrite (loses the audit trail). Late-correction policy: corrections inside the continuous-aggregate refresh window are picked up automatically; older ones need an explicit refresh, logged in `docs/aggregates_history.md`. `[DS]` `[C]` | P1-2, P1-9, P2-6 |

**Still to fill in (owner):** the cost envelope (P1-10), and the metric thresholds in `docs/metrics.md` (P1-11).

---

## P0-gate — must be done before Phase 1 starts

- [ ] **P0-12 · Verify GitHub rendering — do first.** Check `CONTRIBUTING.md` and `CHANGELOG.md` from a logged-out browser (local glitch, or BOM / CRLF / bad Markdown). Moved from hygiene: P0-5 puts the coordination rules in `CONTRIBUTING.md`, so other agents must be able to read it. About 10 minutes. `[G]` `[Grok]` `[DS]`
  - *Owner:* HUMAN

- [x] **P0-1 · Freeze stack and pilot axis.** Align `MASTER.md` and `DECISIONS.md`; stop describing the stack as both "frozen" and "proposed". `[C]` `D1`
  - *ADR title:* `2026-10-03 — Stack and pilot axis frozen for Phases 0–1` `[Grok]`
  - *Definition of done:* one ADR line in `DECISIONS.md` stating *"Stack frozen for Phases 0–1 as of 2026-10-03; scope: A11 pilot only for Phases 0–1"*, and a matching sentence in `MASTER.md`, **in the same commit**. `[G]` `[Grok]`
  - *Owner:* CURSOR (Auto)
  - Done by CURSOR (`agent/cursor/p0-1-decisions`, 2026-10-03)

- [x] **P0-2 · Record the `uv` ADR** in `DECISIONS.md`, with the migration note: *"All future Python tooling commands will use `uv` (run, sync, lock, add)."* `[C]` `[Grok]` `D2`
  - *Owner:* CURSOR (Auto)
  - Done by CURSOR (`agent/cursor/p0-1-decisions`, 2026-10-03)

- [x] **P0-3 · Create `docs/` and move `SPEC_PHASES.md`** → `docs/SPEC_PHASES.md`, leaving a short redirect stub at the root. Do this before P0-4 and before any P1 spec edit. `[C]` `[Grok]`
  - *Owner:* CURSOR (Auto)
  - Done by CURSOR (`agent/cursor/p0-3-docs-move`, 2026-10-03)

- [ ] **P0-4 · `docs/data_sources.md` — the critical path.** `[C]` `[G]` `[Grok]`
  - One sheet per source: URL, format, update frequency, coverage, licence (reuse / redistribution / derivation), contact, personal-data flag, fallback sources.
  - **Phase 0 sources (A11 pilot, per D1):** `[Grok]` `[merge]`
    1. Point d'Accès National (transport.data.gouv.fr / DATEX)
    2. Bison Futé
    3. Vinci Autoroutes (Cofiroute network), the A11 concessionaire. Verify during the review whether any non-concessioned A11 section falls under a DIR; if so, add that DIR as a row.
  - **Deferred to Phase 1+ (outside the A11 pilot):** APRR, SANEF and other DIRs. List them in a "Deferred" section of the file so the omission is visible and intentional. `[DS]`
  - **Licence terms:** record the per-source result in `DECISIONS.md`. It is a product decision, not a legal checkbox: it decides whether the platform can ever be open or public-facing. `[C]` `[Grok]`
  - **GDPR determination:** for each source, does it contain personal data? Floating-car data (FCD) is the main risk. If yes, record legal basis, retention limits and anonymisation requirements in `DECISIONS.md`; if no, record that determination and its basis. `[DS]` `[Grok]`
    - This is a documented compliance assessment, not an AI-only legal conclusion. Unresolved legal questions require human/legal review before the source is approved for production use. `[GPT]`
  - *Owner:* CLAUDE (Opus 5.5) — research and drafting · HUMAN — verifies licence and GDPR conclusions

- [x] **P0-5 · Minimal coordination rules** in `CONTRIBUTING.md`. `[C]` `[DS]` `[GPT]` `[Grok]` `D4`
  - **Status rule:** *"Status and progress updates go only in `CHANGELOG.md` (append-only). `MASTER.md` is updated only for structural or scope changes."*
  - **Single-writer protocol:** shared files — at least `MASTER.md`, `DECISIONS.md`, `TODO.md`, `CONTRIBUTING.md`, `docs/SPEC_PHASES.md`, `docs/data_sources.md` — may be edited by one agent at a time, with an explicit handoff note.
    - [x] *Identities:* add `CURSOR` and `GROK` to the identity list in `CONTRIBUTING.md`, so their commits have a valid `<AGENT>:` prefix. Done by HUMAN on 2026-10-03.
    - *Mechanism (minimal):* the agent claims the file or task by appending a line to `CHANGELOG.md` with `owner` + `started_at`, and releases it with a short handoff note in the same place. No locking tool unless concurrent editing proves problematic. `[GPT]`
  - **Human-approval rule:** AI agents research and propose; the final decision on licensing, architecture freezes, phase GO/NO-GO, external-data redistribution and major infrastructure changes is attributable to the human owner.
  - *Owner:* CURSOR (Auto) — review by HUMAN
  - Done by CURSOR (PR #3, 2026-10-03); ticked under the CURSOR self-tick rule, HUMAN review to follow.

- [ ] **P0-6 · Credential policy, then secret scanning.** `[C]` `[G]` `[Grok]`
  - Policy text for `CONTRIBUTING.md`:
    > All secrets live in `.env` (never committed).
    > `.env.example` must list every required variable with a dummy value.
    > GitHub Actions secrets are allowed only for CI.
    > No secrets in Markdown, code, or commit messages.
  - Then add `.env.example` and a secret-scanning check (DATEX credentials will exist).
  - *Owner:* CURSOR (Auto)

- [~] **P0-7 · Record licence intent, then add `LICENSE`.** `[G]` `[C]` `[Grok]` `D3`
  - [x] Record the intent ADR in `DECISIONS.md`: *internal use only, re-evaluate at end of Phase 3*.
    - Done by CURSOR (`agent/cursor/p0-1-decisions`, 2026-10-03)
  - [ ] Choose or draft the exact proprietary licence text and record its intended scope: code, configuration, documentation, derived data. "Internal use only" is an intent, not a complete licence. Scope over derived data is limited by the source licences found in P0-4. `[GPT]` `[merge]`
  - [ ] Commit the `LICENSE` file consistent with D3 (internal use, all rights reserved). Do not add MIT/Apache-2.0. `[DS]`
  - *Owner:* CURSOR (Auto) — intent ADR · CLAUDE (Opus 5.5) — LICENSE text and scope · HUMAN — sign-off

- [ ] **P0-8 · Phase 0 GO/NO-GO checklist.** Short enough for a human to sign off in about 10 minutes. Nothing in Phase 0 is marked "done" before it exists. `[G]` `[Grok]`
  - [ ] `docs/data_sources.md` complete, with licence status per source
  - [ ] GDPR determination recorded
  - [ ] Reproducible environment bootstrap (`make up` or the canonical `uv`/Docker command, as recorded in `CONTRIBUTING.md`). `make` is not adopted until an ADR says so. `[GPT]`
  - [ ] Smoke test passes: fake DATEX → Postgres → MapLibre
  - [ ] Conventions frozen
  - [ ] Every P0-gate item owned and closed
  - [ ] Human sign-off (name, date)
  - *Owner:* CURSOR (Auto) — writes the checklist · HUMAN — sign-off

- [ ] **P0-13 · Dev scaffold `dev/`:** docker-compose (Postgres + PostGIS + TimescaleDB, Redis, Martin), `.env.example` entries, and the canonical bootstrap command recorded in `CONTRIBUTING.md`. Needed by the P0-8 bootstrap line. Carried over from the phase work queue. `[merge]`
  - *Owner:* CLAUDE (Opus 5.5)

- [ ] **P0-14 · End-to-end smoke test:** a fake DATEX II XML sample → parser → Postgres → MapLibre map, reproducible from the P0-13 bootstrap. Needed by the P0-8 smoke-test line. Carried over from the phase work queue. `[merge]`
  - *Owner:* CLAUDE (Opus 5.5)

- [x] **P0-9 · Assign an owner to every P0 item** before Phase 1 starts; unowned P0 items are the main cause of Phase 0 stalls. `[G]` `[Grok]`
  - Done 2026-10-03 by HUMAN: CURSOR (Auto) for well-specified edits, CLAUDE (Opus 5.5) for research, legal drafting and the scaffold/smoke test, HUMAN for checks and sign-offs.

## P0-hygiene — due by end of Phase 0, does not block Phase 1 `D5`

- [ ] **P0-10 · `docs/README.md` navigation index**, once the first few docs exist. `[DS]` `[Grok]`
  - *Owner:* CURSOR (Auto)
- [ ] **P0-11 · Risk register `docs/RISKS.md`** — columns: Risk / Likelihood / Impact / Mitigation / Owner / Status. Move risks scattered through this TODO into it. `[DS]` `[Grok]`
  - *Owner:* CURSOR (Auto) — HUMAN reviews likelihood and impact

---

## P1 — Spec fixes (`docs/SPEC_PHASES.md` v1.1)

- [ ] **P1-1 · Add a `measurement_site` entity and a site-to-segment mapping.** DATEX measures come from point sensors, not segments. Before any collector code. `[C]` `[Grok]`

- [ ] **P1-2 · `traffic_measure` keys and timestamps.** `[C]` `[Grok]` `D8` `D11`
  - Unique key `(site_id, source, source_ts, source_version)` on raw measures (append revisions, per D11), plus the `traffic_measure_current` view (latest revision per key) that feeds aggregates.
  - Derived per-segment table: key includes `segment_id` plus a time identity (candidate: `(segment_id, source, bucket_ts)`). Verify against the complete `traffic_measure` model before the schema is validated; `segment_id` alone is not unique for time-series rows. `[GPT]`
  - Add `source_ts` / `ingest_ts` columns as required by the conventions.
  - Do not fix the compression `segmentby` columns until representative data has been benchmarked (P2-10). `[GPT]` `[DS]`

- [ ] **P1-3 · Opaque stable segment IDs `seg_<ulid>`**, replacing the position-based format; road, PR and direction become attributes. `[C]` `[Grok]` `D9`

- [ ] **P1-4 · Single direction vocabulary:** direction stored relative to the linear reference (positive/negative); compass label derived for display. Remove the `NORD_SUD…` forms from the spec. `[C]` `D7`
  - Define explicitly how each road's linear-reference orientation is obtained and persisted, and how each source's direction values are mapped to `positive` / `negative`; keep the per-source mapping in `docs/data_sources.md`. Otherwise two sources can silently use opposite conventions. `[GPT]`

- [ ] **P1-5 · Phase 4 routing:** replace "Contraction Hierarchies with NetworkX" with a live-weight approach (customizable CH, OSRM, Valhalla or GraphHopper). `[C]` `[Grok]`

- [ ] **P1-6 · Back the 50,000 events/min target with a source-based estimate.** Feeds P1-7. `[C]` `[Grok]`

- [ ] **P1-7 · Phase 3: defer Kafka/Redpanda.** Keep Redis Streams + workers until P1-6 gives a measured rate that justifies a broker; record the trigger threshold in the spec. `[C]` `[Grok]`

- [ ] **P1-8 · Phase 4 attribution ground truth:** who annotates the 100 test cases and what the ground truth is; label the "traffic density" residual (`OTHER`) as a catch-all, not a cause. `[C]` `[Grok]`

- [ ] **P1-9 · 90-day baselines with 30-day detailed retention** via continuous aggregates, with versioning: an `aggregate_version` column and `docs/aggregates_history.md` (what changed, when, whether history was rebuilt). `[C]` `[DS]` `[Grok]`
  - Aggregates read from `traffic_measure_current`. Late-correction policy (D11): corrections inside the refresh window are picked up automatically; older ones need an explicit refresh, logged in `docs/aggregates_history.md`.

- [ ] **P1-10 · Schedule assumptions and cost envelope** (phases 0–6 ≈ 53–68 weeks). `[C]` `[GPT]` `[DS]` `[Grok]`
  - State team size, separating human engineering effort from AI-agent activity (more agents ≠ more FTE or shorter calendar). Starting assumption to confirm: 1–2 human FTE + multi-AI support.
  - ```
    Human effort:               ______ FTE-months
    Dev infrastructure:         €______ / month
    Prod infrastructure (est.): €______ / month
    Data licences:              €______ / year
    ```

## P1 — Project definition

- [ ] **P1-11 · `docs/metrics.md` — project-level success metrics.** `[DS]` `[Grok]`
  - Thresholds stay blank until justified: define the need first, then measure. No agent fills them with "reasonable" numbers. `[GPT]`
  ```
  Product
    A11 corridor covered end-to-end
    route query P95 latency < ____ ms
    map refresh interval ≤ ____ s
  Data
    source freshness P95 < ____ min
    coverage of A11 sensors ≥ ____ %
    data completeness ≥ ____ %
  Quality
    attribution accuracy ≥ ____ % on the 100 test cases
    residual (OTHER) share ≤ ____ %
  ```

- [ ] **P1-12 · `docs/scope.md` — geographic boundary:** A11 pilot for Phases 0–1 (per D1), the phased expansion plan if any, and the boundary conditions that would change the architecture. `[DS]` `[Grok]` `D1`

- [ ] **P1-13 · `docs/runbooks/rollback.md`**, before Phase 1 ends: bad commit (`git revert` vs reset policy), bad data migration (schema + data), bad source configuration. `[DS]` `[Grok]`

- [ ] **P1-14 · Split the generic workspace template from the traffic-platform project:** decide one repo or two, and act on it. `[C]` `[DS]` `[Grok]` `D10`

---

## P2 — Later

- [ ] **P2-1 · Review `agents/` and `.github/`.** `[C]`
- [ ] **P2-2 · CI:** lint, tests, Markdown link check. `[C]`
- [ ] **P2-3 · PR template** enforcing the `CHANGELOG.md` entry and attribution. `[C]`

- [ ] **P2-4 · Full multi-AI task/handoff protocol** (extends P0-5). `[GPT]` `[DS]` `[Grok]` `D4`
  - Task record: id, status, owner, reviewer, created_by, priority, dependencies, created_at, `review_due_by`.
  - States: TODO, IN_PROGRESS, BLOCKED, REVIEW, CHANGES_REQUESTED, APPROVED, DONE.
  - No agent approves another agent's work silently, nor its own.
  - Review SLA: default `review_due_by = created_at + 72h`; overdue REVIEW tasks escalate to the human owner. The owner may override the deadline for tasks requiring external availability or scheduled review windows. `[GPT]`

- [ ] **P2-5 · Separate facts, assumptions, hypotheses and proposals** (`FACTS.md`, `ASSUMPTIONS.md`, `HYPOTHESES.md`, `PROPOSALS.md`), with a provenance block on every FACT: `[GPT]` `[DS]` `[Grok]`
  ```
  FACT
    statement:      ...
    source:         <URL or reference>
    verified_by:    ______
    verified_at:    YYYY-MM-DD
    re_verify_by:   YYYY-MM-DD
  ```

- [ ] **P2-6 · Provenance for derived data:** source → ingestion → normalisation → mapping → aggregation → output, recording source timestamp, ingestion timestamp, schema version and processing version (builds on P1-2, P1-9). `[GPT]`

- [ ] **P2-7 · Architectural-change proposal rule:** before any new database, queue, framework, cloud service or major dependency, a short proposal (problem, alternatives, operational impact, migration consequences); final call per the P0-5 human-approval rule. `[GPT]`

- [ ] **P2-8 · `docs/onboarding_agent.md`:** read order (MASTER → CONTRIBUTING → current tasks → DECISIONS) and a safe "first task" pattern; linked from `docs/README.md`. `[DS]` `[Grok]`

- [ ] **P2-9 · Agent output format conventions:** format per role (ADR, decision matrix, evidence table, review note) and location (`DECISIONS.md` for ADRs per D6, `reviews/`, `proposals/`). `[DS]` `[Grok]`

- [ ] **P2-10 · Benchmark hypertable compression settings** (`segmentby` / `orderby` candidates, including `source` and `site_id`) on representative A11 data before fixing them in the schema. `[GPT]` `[DS]`

---

## Top priorities

0. Verify GitHub rendering of `CONTRIBUTING.md` / `CHANGELOG.md` (P0-12) — 10 minutes, unblocks reading the rules.
1. Freeze stack + A11 pilot in `DECISIONS.md` this week (P0-1), with the `uv` and licence-intent ADRs in the same pass (P0-2, P0-7).
2. Start `docs/data_sources.md` immediately — the critical path (P0-4).
3. Write the GO/NO-GO checklist before more Phase 0 work is marked done (P0-8).
4. Put the minimal coordination rules in `CONTRIBUTING.md` before more shared files are edited (P0-5).
5. Assign owners to every P0 item (P0-9).

---

## Phase work queue (carried over unchanged from the previous `TODO.md`)

This is the Phase 0–2 task queue and agent-assignment table from the 2026-10-02 spec ingestion. It is kept verbatim per `CONTRIBUTING.md` ("do not delete another agent's work"). The review items above take priority for P0; reconcile overlaps (sources list, `make up`, GO/NO-GO) when P0-4 and P0-8 are executed.

### P0 — Critical (Phase 0)
- [ ] Inventaire sources DATEX II (DIR, Bison Futé, SANEF, APRR, Vinci, …) → `docs/data_sources.md`
- [ ] Vérifier licences (ouverture, rediffusion, dérivation) + contacts / conventions
- [ ] Valider axe pilote A11 Nantes–Paris (~350 km) et justification
- [ ] Écrire / revoir conventions (IDs, unités, timestamps, codes incident, CRS)
- [ ] Scaffold `dev/` : docker-compose (Postgres+PostGIS+TimescaleDB, Redis, Martin), `.env.example`, `Makefile` (`make up`)
- [ ] Smoke test bout-en-bout factice : XML DATEX → Postgres → MapLibre
- [ ] GO/NO-GO fin phase 0 → lancement phase 1

### P1 — Important (Phase 1 prep / early)
- [ ] Référentiels pivots LRS : `road`, `pr_point`, `pr_range` + dictionnaires routes / sens
- [ ] Collecteur DATEX événements (`parser` / `mapper` / `loader` / `scheduler`)
- [ ] Collecteur DATEX trafic (`MeasuredDataPublication`)
- [ ] Segments A11 (OSM Overpass → découpage → rattachement PR)
- [ ] Matcher DATEX → segment + table `incident_segment_link`
- [ ] Hypertable `traffic_measure` + API minimale + carte MapLibre

### P2 — Later (Phases 2+)
- [ ] Multi-sources `SourceAdapter` + déduplication incidents
- [ ] Extension 5–10 axes + observabilité Prometheus/Grafana
- [ ] LRS national + Kafka/Redpanda + compression TimescaleDB
- [ ] Attribution causale + itinéraires explicables
- [ ] Analytique / rapports / prédiction ML / API publique

### Agent assignments
| Task | Agent | Status | Notes |
|---|---|---|---|
| Populate SPEC_PHASES + MASTER/TODO | CLAUDE | done | Spec v1.0 ingested 2026-10-02 |
| Inventaire DATEX → data_sources.md | | todo | Phase 0.1 |
| Scaffold docker-compose / make up | | todo | Phase 0.3 |

---

## Change log for this file

- **v0.1 · 2026-10-03 — Merge.** Folded all accepted comments from `[C]`, `[G]`, `[Grok]`, `[GPT]`, `[DS]` into the items; adopted recommendations as items; opened decisions D1–D10.
- **v0.2 · 2026-10-03 — Finalized.** Human owner accepted all ten recommended resolutions. Decision table replaced by resolved decisions; P0 split into gate/hygiene; items updated to the chosen options (site-based key, `seg_<ulid>`, reference-relative direction, `uv`, internal licence intent, ADRs in `DECISIONS.md`, template split in P1).
- **v0.3 · 2026-10-03 — DeepSeek review applied.** Header reworded ("final structure — some fields pending"); D11 (source corrections) opened with recommendation; P0-4 source list scoped to the A11 pilot (Vinci/Cofiroute as concessionaire) with APRR, SANEF and other DIRs explicitly deferred; P0-12 moved to P0-gate as the first task; P0-7 split into ADR and LICENSE-text checkboxes; P1-2 `segmentby` choice deferred to a new benchmark task P2-10; D6 revisit threshold (~40 ADRs) added.
- **v0.4 · 2026-10-03 — ChatGPT review applied.** P0-7 adds licence-text and scope step; P0-4 GDPR marked as an assessment requiring human/legal review; P0-5 gets a minimal claim/release mechanism via `CHANGELOG.md`; P0-8 bootstrap line no longer implies `make`; D8/P1-2 derived-table key clarified (segment + time identity, to verify against the full model); P1-4 requires a defined linear-reference orientation and per-source direction mapping; P1-11 thresholds must not be invented; P2-4 SLA owner override. The reported end-of-file duplication was not present in this file (copy/paste artefact on the reviewer's side).
- **v1.0 · 2026-10-03 — Baseline.** Grok review: no changes requested. Version number and versioning rule added; this is the reference version for execution of P0.
- **v1.1 · 2026-10-03 — Committed to repo.** Previous `TODO.md` phase work queue and agent-assignment table carried over verbatim as a dedicated section, instead of being overwritten.
- **v2.0 · 2026-10-03 — D11 resolved.** HUMAN chose option B (append revisions). D11 moved to the resolved table; P1-2 raw key is now `(site_id, source, source_ts, source_version)` with a `traffic_measure_current` view; P1-9 carries the late-correction policy. No open decisions remain.
- **v2.1 · 2026-10-03 — Owners assigned (P0-9 done).** HUMAN assigned every P0 item to CURSOR (Auto), CLAUDE (Opus 5.5) or HUMAN. Dev scaffold and smoke test added as P0-13 and P0-14 so the GO/NO-GO checklist's prerequisites have owners. P0-5 now adds `CURSOR` and `GROK` identities to `CONTRIBUTING.md`.
- **v2.2 · 2026-10-03 — Sync with main.** v2.0 and v2.1 had missed the merge of PR #1 and are re-submitted together. P0-5 identities sub-task marked done (HUMAN added `CURSOR` and `GROK` to `CONTRIBUTING.md`).
- **v2.3 · 2026-10-03 — CURSOR self-tick rule.** HUMAN decided that CURSOR ticks its own tasks when it completes them, with HUMAN review afterwards; status legend updated. P0-5 ticked (done by CURSOR in PR #3).
- **v2.4 · 2026-10-03 — P0-1 / P0-2 / P0-7 intent ADR.** CURSOR recorded D1–D11 in `DECISIONS.md`, froze stack + A11 in `MASTER.md`, ticked P0-1 and P0-2; P0-7 intent ADR sub-item ticked (LICENSE text still CLAUDE).
- **v2.5 · 2026-10-03 — P0-3 docs move.** CURSOR moved `SPEC_PHASES.md` → `docs/SPEC_PHASES.md` with a root redirect stub; updated repo links.
