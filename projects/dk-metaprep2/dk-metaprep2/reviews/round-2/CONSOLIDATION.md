# Round 2 consolidation — dk-metaprep2

Reviewed `spec.md` v0.2 → now **v0.3** (2026-11-02). Inputs: `reviews/round-2/DEEPSEEK.md` (14 findings, DEEPSEEK-16 to -29: 4 major, 10 minor, 0 blocking) and `reviews/round-1/CONSOLIDATION.md`. `decisions.md`, `docs/`, `evals/` and `assets/` still do not exist; their creation stays deferred to the implementation phase (see round 1).

## Reviewer provenance

- DEEPSEEK: requested `deepseek-flash`, served `deepseek-flash` (verified).
- No reviewer was unverified. Only one reviewer took part, so there is no cross-reviewer agreement to rely on.
- DEEPSEEK could not fetch DistroKid help pages (HTTP 403) and used search-indexed text. CLAUDE did not re-verify any external claim; new and changed rules are marked *unverified* in §11.

## Accepted and merged

| Finding | Severity | Spec change (v0.3) |
|---|---|---|
| DEEPSEEK-16 release types | major | §4.3 now uses Single 1–3, EP 4–6 under 30 min, Album 7+ or over 30 min; derived suggestion, warning only; §3.1 note; §11 row. The 10-minute single-track edge is low confidence and explicitly not enforced. |
| DEEPSEEK-17 AI disclosure | major | §3.1 replaced the enum with `ai_used` + `lyrics`/`music`/`all_audio`/`part_of_audio` + `artist_persona`; "no AI" is a valid required answer; §5.1, §6.1 example and §11 updated. Requiredness is medium confidence, so it stays unverified. |
| DEEPSEEK-18 performance | major | §4 split into file checks (at import/change, cached "file facts") and rule evaluation; §8 budget applies to rule evaluation only; §7 adds `file_facts`. |
| DEEPSEEK-19 primary artist | major | `primary_artist` always emitted per track (§6.1); golden fixtures must include an override. |
| DEEPSEEK-20 wire semantics | minor | Three-state optional-text rule; `target_plan`, `isrc_source` and AI wire values defined; example `"version": ""` → `null`. |
| DEEPSEEK-21 cover-art size | minor | DistroKid max file size removed; no app cap; §11 row records the absence. |
| DEEPSEEK-22 CDDA | minor | CDDA dropped; list is WAV, MP3, M4A, FLAC, AIFF, WMA; limits referenced to §11. |
| DEEPSEEK-23 territories | minor | Option (a): field renamed `excluded_territories`, a record for the post-upload request, not a form value; §3.1, §5.1, §6.1, §11. Exact plan gating folded into DKM2-D1. |
| DEEPSEEK-24 ISRC source | minor | `isrc_source` (`user`\|`distrokid`) in §3.2 and §6.1; `isrc` present only for `user`. |
| DEEPSEEK-25 project container | minor | §7: project folder with `<name>.dkmeta` and `media/`; files copied on import; manifest paths relative to `media/`. |
| DEEPSEEK-26 IPI wording | minor | §3.3 and §4.1 now state the same outcome. DKM2-D6 untouched. |
| DEEPSEEK-27 residual claims | minor | §1, §2, §5.5 no longer claim DISTROPILOT compatibility or 1:1 mapping. |
| DEEPSEEK-28 publisher storage | minor | A Publisher is a `contributors` row (name = publisher name, IPI = publisher IPI); duplicate fields removed from §3.3 and §5.3. |
| DEEPSEEK-29 dedup | minor | Internal `contributor_id` identity; (name, IPI, PRO) is a match hint, auto-link only on non-null IPI, otherwise user-confirmed merge. |

## Decisions for HUMAN

No new decision IDs. The carried-forward list in spec §12 (DKM2-D1 to DKM2-D9) is unchanged except that DKM2-D1 now also covers territory-exclusion gating (DEEPSEEK-23). Not decided here, not waited on. Conservative readings stay in force: warnings rather than errors, §6.4 not to be implemented, manifest treated as internal.

## Rejected or deferred

- Nothing rejected outright.
- Deferred: JSON Schema, golden fixtures, field-mapping table and `assets/` data (companion files, implementation phase); the spec states their required contents.
- Deferred: DistroKid size/length figures; the unverified numbers stay as references to §11, not restated.
- Not adopted as proposed: DEEPSEEK-16's 10-minute and 30-minute edge rules are only partly adopted (30-minute total used, 10-minute edge recorded but not enforced) given medium/low confidence.
- Not adopted as proposed: DEEPSEEK-18's cache key includes SHA-256; the spec keys on path + size + mtime and adds SHA-256 once computed, since hashing large files is itself a file check.

## Traceability

| Finding | Disposition |
|---|---|
| DEEPSEEK-16 | Accepted; edge rules in part |
| DEEPSEEK-17 | Accepted |
| DEEPSEEK-18 | Accepted; cache key adjusted |
| DEEPSEEK-19 | Accepted |
| DEEPSEEK-20 | Accepted |
| DEEPSEEK-21 | Accepted |
| DEEPSEEK-22 | Accepted |
| DEEPSEEK-23 | Accepted (option a); plan gating → DKM2-D1 |
| DEEPSEEK-24 | Accepted |
| DEEPSEEK-25 | Accepted |
| DEEPSEEK-26 | Accepted; DKM2-D6 not reopened |
| DEEPSEEK-27 | Accepted; target → DKM2-D8 |
| DEEPSEEK-28 | Accepted |
| DEEPSEEK-29 | Accepted |
