# Round 1 consolidation — dk-metaprep2

Reviewed `spec.md` v0.1 → now **v0.2** (2026-11-02). Inputs: `reviews/round-1/DEEPSEEK.md` (15 findings: 2 blocking, 9 major, 4 minor). No round-0 consolidation, `decisions.md`, `docs/`, `evals/` or `assets/` exists.

## Reviewer provenance

- DEEPSEEK: requested `deepseek-flash`, served `deepseek-flash` (verified).
- No reviewer was unverified. Only one reviewer took part, so there is no cross-reviewer agreement to rely on.
- DEEPSEEK could not fetch DistroKid help pages (HTTP 403) and used search-indexed text. CLAUDE did not re-verify any external claim; the spec marks them *unverified* in §11.

## Accepted and merged

| Finding | Severity | Spec change (v0.2) |
|---|---|---|
| DEEPSEEK-1 UPC | blocking | UPC removed as input and rule; read-only note, `release_id`, optional `assigned_upc` (§3.1, §4.1, §5.1, §6.1). |
| DEEPSEEK-2 plans | major | New §3.4 (`target_plan`, `already_released`, field states); plan-conditional validation. Matrix scope left to DKM2-D1. |
| DEEPSEEK-3 contributors | blocking | One model in §3.3 (`contributors` + `track_credits`, writer vs publisher share, copy semantics, no-contributor warning); §5.3 and §7 aligned. |
| DEEPSEEK-4 cover art | major | One rule: JPEG, RGB, ≥1000×1000 error, 3000×3000 warning, decode check (§3.1, §4.1). |
| DEEPSEEK-5 release date | major | 7-day error removed; 21/28-day warnings; date semantics defined (§3.1, §4.2). |
| DEEPSEEK-6 audio | major | Accepted formats vs app policy separated; existence/decode/duration checks; Duration derived (§3.2, §4.1). |
| DEEPSEEK-7 manifest | major | Versioned contract, wire values, path policy, CSV rules (§6.1, §6.2). JSON Schema and golden fixtures are to be created in `docs/` and `evals/` (not yet written). |
| DEEPSEEK-8 provenance | major | New §11 with per-rule source, status and "unverified" marking. |
| DEEPSEEK-9 credits | major | Legal name required for songwriters; Performer and Engineer roles; Apple credit groups as warning pending DKM2-D5. |
| DEEPSEEK-10 baseline | major | New §7.1 as a proposal pending DKM2-D9. |
| DEEPSEEK-11 security | major | Off-the-record profile, absolute "no credentials" claim reworded, bridge hardening list (§6.3, §6.4, §8). |
| DEEPSEEK-12 identifiers | minor | ISRC normalisation/hyphen rule, IPI 9-digit check; UPC part moot (see DEEPSEEK-1). |
| DEEPSEEK-13 undefined rules | minor | Advisory title/artist checks, 2-track release, Duration; explicit/lyrics warning dropped. |
| DEEPSEEK-14 reference data | minor | New §3.5 versioned assets; AI disclosure as category set. Asset files not yet created. |

## Decisions for HUMAN

Carried forward in one list in spec §12 (IDs DKM2-D1 to DKM2-D9). Not decided here, not waited on:

- DKM2-D1 plan matrix/scope (DEEPSEEK-2)
- DKM2-D2 3000×3000 cover art as error (DEEPSEEK-4)
- DKM2-D3 21-day lead-time policy (DEEPSEEK-5)
- DKM2-D4 audio quality policy (DEEPSEEK-6)
- DKM2-D5 Apple credit enforcement (DEEPSEEK-9)
- DKM2-D6 11-digit CAE/IPI (DEEPSEEK-12)
- DKM2-D7 bridge and Guided Fill vs ToS scope (DEEPSEEK-11, DEEPSEEK-15)
- DKM2-D8 DISTROPILOT as real target (DEEPSEEK-7)
- DKM2-D9 technical baseline (DEEPSEEK-10)

In the meantime the spec takes the conservative reading: warnings rather than errors, and §6.4 Guided Fill is not to be implemented.

## Rejected or deferred

- Nothing rejected outright.
- Deferred: creating the JSON Schema, golden fixtures and `assets/` data (DEEPSEEK-7, -14). They are companion files for the implementation phase; the spec states their required contents.
- Deferred: exact DistroKid size/length limits and the 2-track/EP boundary; unverified, so left as references to §11 rather than numbers.
- Not accepted as written: DEEPSEEK-9's "required when the release targets Apple Music" is kept as a warning until DKM2-D5.

## Traceability

| Finding | Disposition |
|---|---|
| DEEPSEEK-1 | Accepted |
| DEEPSEEK-2 | Accepted; scope → DKM2-D1 |
| DEEPSEEK-3 | Accepted |
| DEEPSEEK-4 | Accepted; strictness → DKM2-D2 |
| DEEPSEEK-5 | Accepted; policy → DKM2-D3 |
| DEEPSEEK-6 | Accepted; policy → DKM2-D4 |
| DEEPSEEK-7 | Accepted; target → DKM2-D8; artefacts deferred |
| DEEPSEEK-8 | Accepted |
| DEEPSEEK-9 | Accepted in part; enforcement → DKM2-D5 |
| DEEPSEEK-10 | Accepted as proposal → DKM2-D9 |
| DEEPSEEK-11 | Accepted; scope → DKM2-D7 |
| DEEPSEEK-12 | Accepted; CAE → DKM2-D6 |
| DEEPSEEK-13 | Accepted |
| DEEPSEEK-14 | Accepted; asset files deferred |
| DEEPSEEK-15 | Escalated → DKM2-D7 |
