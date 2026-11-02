# Round 3 consolidation — dk-metaprep2

Reviewed `spec.md` v0.3 → now **v0.4** (2026-11-02). Inputs: `reviews/round-3/DEEPSEEK.md` (10 findings, DEEPSEEK-30 to -39: 1 major, 9 minor, 0 blocking) and `reviews/round-2/CONSOLIDATION.md`. `decisions.md`, `docs/`, `evals/` and `assets/` still do not exist; their creation stays deferred to the implementation phase.

## Reviewer provenance

- DEEPSEEK: requested `deepseek-flash`, served `deepseek-flash` (verified).
- No reviewer was unverified. Only one reviewer took part, so there is no cross-reviewer agreement to rely on.
- DEEPSEEK could not fetch DistroKid help pages (HTTP 403) and used search-indexed text. CLAUDE did not re-verify any external claim; new rules are marked *unverified* in §11.

## Accepted and merged

| Finding | Severity | Spec change (v0.4) |
|---|---|---|
| DEEPSEEK-30 artist_persona | major | §3.1 and §6.1: `ai_disclosure.artist_persona` (boolean) emitted and required only when `all_audio` is selected; goldens must include an all-audio case. Meaning of true/false follows the form wording and is unverified. |
| DEEPSEEK-31 AI consistency | minor | §4.1 new error: `ai_used` ⇔ at least one category; `artist_persona` iff `all_audio`. Mutual exclusivity of categories is not stated by any known source, so no rule is added; recorded in §3.1 and §11 as unknown. |
| DEEPSEEK-32 already_released | minor | §3.4 defines the behaviour (original past date, lead-time warnings suppressed); §4.2 lead-time warnings apply only to a user-set future date on a plan allowing custom dates; §3.1 Release Date row; §11 row for the previously-released article. |
| DEEPSEEK-33 ISRC warning | minor | §4.2 warning redefined as "own ISRC value present while `isrc_source = distrokid`", distinct from the §4.1 plan-capability error. |
| DEEPSEEK-34 roles per credit | minor | One role per `track_credits` row (preferred option) in §3.3 and §7; shares exist only on the matching role. |
| DEEPSEEK-35 share bounds | minor | §4.1 new error: each share numeric, 0.00–100.00, at most 2 dp, in addition to the Songwriter sum. |
| DEEPSEEK-36 required inputs | minor | §3.1: `target_plan` (no default; export blocked until chosen) and `already_released` (default `false`) added as rows; Label required when its plan state is Available; §3.4, §4.1, §5.1 aligned. |
| DEEPSEEK-37 credit object | minor | §6.1 normative credit object including `publisher_share`; Publisher golden fixture required; CSV uses the same object. |
| DEEPSEEK-38 release_date immediate | minor | §6.1: `release_date` absent when the plan has no custom date and `already_released` is false; absence = DistroKid immediate processing; first alternative (absence) chosen over a mode field; immediate-release golden required. |
| DEEPSEEK-39 no Songwriter | minor | §4.2 new warning for contributor rows without a Songwriter credit, kept separate from "no contributor rows"; error status not decided. |

## Decisions for HUMAN

No new decision IDs. The carried-forward list in spec §12 (DKM2-D1 to DKM2-D9) is unchanged and was not touched. Not decided here, not waited on. Conservative readings stay in force: warnings rather than errors (including the new no-Songwriter warning, which HUMAN may later raise to an error), §6.4 not to be implemented, manifest treated as internal. Whether `already_released` with a past original date is allowed on every plan is part of the unverified plan matrix (DKM2-D1).

## Rejected or deferred

- Nothing rejected.
- Not adopted: a mutual-exclusivity rule for `all_audio` / `part_of_audio` (DEEPSEEK-31, medium confidence, reasoning only); left unknown until verified.
- Not adopted: `release_date_mode` field (DEEPSEEK-38 alternative); absence is used.
- Deferred: JSON Schema, golden fixtures, field-mapping table and `assets/` data (implementation phase); the spec states their required contents.

## Traceability

| Finding | Disposition |
|---|---|
| DEEPSEEK-30 | Accepted |
| DEEPSEEK-31 | Accepted; exclusivity rule not adopted |
| DEEPSEEK-32 | Accepted |
| DEEPSEEK-33 | Accepted |
| DEEPSEEK-34 | Accepted (one role per row) |
| DEEPSEEK-35 | Accepted |
| DEEPSEEK-36 | Accepted |
| DEEPSEEK-37 | Accepted |
| DEEPSEEK-38 | Accepted (absence option) |
| DEEPSEEK-39 | Accepted as warning |
