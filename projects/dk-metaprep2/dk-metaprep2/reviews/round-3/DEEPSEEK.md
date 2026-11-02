# DEEPSEEK review — round 3

Scope: `spec.md` v0.3 (2026-11-02), read against `reviews/round-2/DEEPSEEK.md` and `reviews/round-2/CONSOLIDATION.md`. `decisions.md`, `docs/`, `evals/` and `assets/` are still absent from the project folder; the round-2 consolidation deferred their creation to the implementation phase, so their absence is not re-raised here. I do not repeat the 14 round-2 findings except where the merged v0.3 text is still internally inconsistent. DistroKid help pages still return HTTP 403 to direct fetches from this environment, so external statements below are taken from the search-indexed text of the linked official articles, checked 2026-11-02. Open HUMAN decisions DKM2-D1 to DKM2-D9 are not reopened; findings that touch them are minor.

### DEEPSEEK-30 · The `artist_persona` answer has no place in the manifest

- **Section:** §3.1 (AI Disclosure), §5.1, §6.1
- **Type:** gap
- **Severity:** major
- **Finding:** §3.1 and §5.1 require an `artist_persona` answer when `all_audio` is selected, but §6.1's `ai_disclosure` object defines only `ai_used` and `categories`; the example has no `artist_persona` key, no wire semantics, and no statement of what the boolean means. The canonical manifest — which §6.1 says mirrors the data model — therefore cannot carry a required AI Credits answer for an all-audio release, so the browser bridge and the manual upload sheet lose it.
- **Proposed change:** Add `artist_persona` to `ai_disclosure` (boolean with true/false meaning stated, or an enum `human|ai_persona` if that matches the form); emit it only when `all_audio` is in `categories` and require it then; add it to the version-1 JSON Schema, the §6.1 example with an all-audio case, and a golden fixture. If the answer is intended to stay UI-only, say so explicitly and drop the “mirrors the data model” claim.
- **Evidence:** internal inconsistency §3.1/§5.1 vs §6.1; DistroKid “How to Fill Out AI Credits” (https://support.distrokid.com/hc/en-us/articles/50784709021971) reports the follow-up question after “All of the audio” (search-indexed text; direct fetch returned HTTP 403), checked 2026-11-02.
- **Confidence:** high

### DEEPSEEK-31 · AI-disclosure consistency rules are absent from the error list

- **Section:** §3.1 (AI Disclosure), §4.1, §6.1
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.1 states that `ai_used = false` means no categories and that categories require `ai_used = true`, and DistroKid requires selecting at least one category when AI was used, but §4.1 — the normative error list — has no rule for any of these conditions. A project can therefore export `ai_used: true` with `categories: []`, `ai_used: false` with categories, or an `artist_persona` answer outside `all_audio`, and validation reports no error; the spec also does not say whether `all_audio` and `part_of_audio` are mutually exclusive.
- **Proposed change:** Add §4.1 errors: `ai_used = true` requires at least one category; `ai_used = false` forbids categories; `artist_persona` is present and required if and only if `all_audio` is selected. State whether `all_audio` excludes `part_of_audio` (and whether the narrower `lyrics`/`music` categories may accompany it), and add an all-audio golden fixture.
- **Evidence:** internal inconsistency §3.1 vs §4.1; DistroKid “How to Fill Out AI Credits” (search-indexed text; direct fetch HTTP 403) says to select at least one category when AI was used, checked 2026-11-02. The mutual-exclusivity point is reasoning only: the article summary does not state it.
- **Confidence:** high on the missing rules; medium on mutual exclusivity

### DEEPSEEK-32 · `already_released` date handling is undefined and lead-time warnings misfire

- **Section:** §3.4, §4.2 (and §3.1 Release Date)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** `already_released` is introduced as changing “ISRC and date handling” (§3.4), but only the ISRC warning in §3.2 uses it; no date rule is defined. §4.2's lead-time warnings are “independent of the plan” and fire for any date less than 21/28 days away, so a previously released upload with a past original date triggers both warnings, and a basic-plan immediate release triggers warnings the user cannot act on; DistroKid's previously-released flow uses a past original release date, goes live on processing, and is not eligible for pre-order or editorial pitching.
- **Proposed change:** Define `already_released` date handling: when true, `release_date` is the original (past) release date and the lead-time warnings are suppressed; when false, the warnings apply only to a user-set future date on a plan that allows custom dates. State that the 21-day/28-day warnings do not apply to immediate or plan-default releases, and add the previously-released help article to §11.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360023454214-Specifying-Your-Upload-as-Previously-Released (past date, live immediately, no pre-order/pitching) and https://support.distrokid.com/hc/en-us/articles/52677658186003-How-to-Release-Music-on-DistroKid-Step-by-Step-for-New-Members (custom date on Plus/Ultimate; basic plan immediate) — search-indexed text, direct fetches returned HTTP 403, checked 2026-11-02.
- **Confidence:** high on the misapplication; medium on which warnings HUMAN wants (DKM2-D3 is not reopened)

### DEEPSEEK-33 · The “own ISRC on a plan that would assign anyway” warning contradicts the ISRC error

- **Section:** §4.2, §4.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.2 warns for “Own ISRC fields on a plan that would assign them anyway”, while §4.1 makes “Own ISRC supplied while the plan does not allow it” an error. On the plan that assigns ISRCs anyway (Musician) own ISRC is unavailable, so the warning condition is either unreachable or is the same condition that blocks export; an implementer cannot tell which outcome applies, and the UI could show a warning for data that is an error.
- **Proposed change:** Delete the warning, or redefine it as the exact state “own ISRC present while `isrc_source = distrokid`” (a chosen-source inconsistency) and keep it distinct from the §4.1 plan-capability error. Do not leave both the error and the warning covering the same plan state.
- **Evidence:** internal inconsistency §4.1 vs §4.2, with the plan states in §3.4.
- **Confidence:** high

### DEEPSEEK-34 · `track_credits` says “one or more roles” while every other model has one role per credit

- **Section:** §3.3, §5.3, §6.1, §7
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.3's data model says `track_credits` links a track to a contributor “with one or more roles”, but the §3.3 field table, the §5.3 editor and the §6.1 credit object all describe a single `role` per credit, and §7 says only “roles”. The two readings — one row per role versus one multi-role row carrying one `writer_share` — give different writer-share totals and different manifest serializations, so the model is not implementable without a choice.
- **Proposed change:** Pick one. Preferred: one role per `track_credits` row (a contributor credited twice has two rows; the contributor identity stays shared), with `writer_share` only on Songwriter rows and `publisher_share` only on Publisher rows. If multi-role rows are intended, define how they are split for the manifest and counted for the 100% sum, and align §5.3.
- **Evidence:** internal inconsistency §3.3 vs §5.3/§6.1/§7.
- **Confidence:** high

### DEEPSEEK-35 · Share bounds and precision are typed but never validated

- **Section:** §3.3, §4.1
- **Type:** gap
- **Severity:** minor
- **Finding:** `writer_share` and `publisher_share` are typed 0–100 with 2 dp in §3.3, but §4.1 only checks the sum over Songwriter credits. Two writers at 150.00 and -50.00 sum to 100.00 and pass; a publisher share of 250.00 or a three-decimal value has no rule at all, so values the type forbids can reach the manifest.
- **Proposed change:** Add §4.1 errors for each share: numeric, 0.00–100.00 inclusive, at most 2 decimal places; keep the Songwriter sum of 100.00 ±0.01. Add the `publisher_share` range check even though publisher shares are a separate layer outside the writer total.
- **Evidence:** internal inconsistency §3.3 field types vs §4.1 rule set.
- **Confidence:** high

### DEEPSEEK-36 · `target_plan` and Label are missing from the required-input definition, and `already_released` has no default

- **Section:** §3.1, §3.4, §4.1, §5.1
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.1 makes required-field validation conditional on the plan state, and §3.4 derives that state from `target_plan`, but `target_plan` is not in the §3.1 required list or the Release table; Label is marked “Required; plan-gated” in its table row and omitted from the required-fields paragraph; and `already_released` has no stated default. A new project can therefore reach validation with an undefined plan state and release branch, and an implementer cannot tell whether export is blocked.
- **Proposed change:** Add `target_plan` as a required release input with a defined initial value (or state that validation and export are blocked until it is chosen), add Label to the required list “when its plan state is Available”, and define `already_released` default `false`. Mention all three in the §3.1 required-fields paragraph and §5.1.
- **Evidence:** internal inconsistency §3.1/§3.4/§4.1.
- **Confidence:** high

### DEEPSEEK-37 · The manifest credit object is undefined and drops `publisher_share`

- **Section:** §6.1, §3.3
- **Type:** gap
- **Severity:** minor
- **Finding:** §6.1 says the JSON structure mirrors the data model, but it never defines the credit object's keys; the only example is a Songwriter credit. `publisher_share`, which §3.3 defines and §5.3 collects, has no manifest key, so a publisher split is silently lost in the canonical JSON and in the CSV's JSON-encoded credits.
- **Proposed change:** Add a normative credit object to §6.1: `role` (required), `legal_name` (required), `ipi`/`pro` (optional), `writer_share` (Songwriter rows only, required per §3.3), `publisher_share` (Publisher rows only, optional); keys absent for other roles. Add a Publisher golden fixture.
- **Evidence:** internal inconsistency §3.3/§5.3 vs §6.1 and the “mirrors the data model” sentence.
- **Confidence:** high

### DEEPSEEK-38 · `release_date` has no defined representation for immediate-release plans

- **Section:** §6.1, §3.4 (and §3.1 Release Date)
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.4 says plan-unavailable fields emit no manifest value and the basic-plan default is “immediate release”, but §6.1 presents `release_date` as an ISO 8601 date and its three-state rule covers only optional text; the example always includes a date. For a Musician-plan project the schema author cannot tell whether `release_date` is required, omitted, or set to today's date, and emitting today's date would turn the DistroKid default into a chosen release date.
- **Proposed change:** State that `release_date` is absent when the plan does not allow a custom date and that absence means “DistroKid immediate processing”; or add `release_date_mode: "date" | "immediate"`. Mark the field conditional/optional in the version-1 schema and add a golden fixture for an immediate-release project.
- **Evidence:** internal inconsistency §3.4 vs §6.1; DistroKid custom dates are Plus/Ultimate and the basic plan is immediate (https://support.distrokid.com/hc/en-us/articles/52677658186003, search-indexed text, direct fetch HTTP 403), checked 2026-11-02.
- **Confidence:** high on the gap; medium on the preferred representation

### DEEPSEEK-39 · A track with credits but no Songwriter is neither blocked nor warned

- **Section:** §4.2, §3.3
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.2 warns only when a track has no contributor rows, but a track with only a Performer or Producer credit has contributor rows and zero Songwriter credits: the share check is skipped (it applies “when the track has Songwriter credits”) and no warning fires. The exported track has no songwriter, although DistroKid's form requires the songwriter's real name, so the existing warning misses the case it is meant to catch.
- **Proposed change:** Add a warning (or an error if HUMAN chooses) when a track has contributor rows but no Songwriter credit, distinct from the existing “no contributor rows” warning; keep both visible in the Review screen. If missing songwriters are to block export, add it to §4.1.
- **Evidence:** internal gap §3.3/§4.2; the §11 songwriter row (https://support.distrokid.com/hc/en-us/articles/360013545554) and search-indexed DistroKid guidance that the songwriter field is mandatory, checked 2026-11-02 (direct fetch HTTP 403).
- **Confidence:** medium-high

## Top 3

1. **Put `artist_persona` in the manifest** (DEEPSEEK-30): the AI Credits answer is required for all-audio releases and currently disappears at export.
2. **Define `already_released` date handling and scope the lead-time warnings** (DEEPSEEK-32): back-catalogue and basic-plan releases currently get inapplicable pitch-window warnings, and the spec's own “changes date handling” promise is unspecified.
3. **Finish the credit model end to end** (DEEPSEEK-34, DEEPSEEK-35, DEEPSEEK-37): choose one role per credit, enforce the 0–100/2-dp bounds, and export `publisher_share` in a normative credit object.

Result: complete
