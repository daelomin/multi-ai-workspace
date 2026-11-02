# DEEPSEEK review — round 4

Scope: `spec.md` v0.4 (2026-11-02), read against `reviews/round-3/DEEPSEEK.md` and `reviews/round-3/CONSOLIDATION.md`. `decisions.md`, `docs/`, `evals/` and `assets/` are still absent from the project folder; the round-3 consolidation deferred their creation to the implementation phase, so their absence is not re-raised here. I do not repeat the ten round-3 findings that were accepted and merged; the findings below are either new or concern v0.4 text that is still inconsistent. DistroKid help pages were not re-fetched this round; every finding below is internal to the spec, so evidence is reasoning only unless stated. Open HUMAN decisions DKM2-D1 to DKM2-D9 are not reopened; findings that touch them are minor.

### DEEPSEEK-40 · The previously-released ISRC request contradicts the plan-capability error

- **Section:** §3.2 (ISRC), §3.4, §4.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 says that when `already_released = true` and no ISRC is present, a warning asks the user for the existing ISRC, and §3.4 repeats that an existing ISRC is requested. §4.1, however, makes “own ISRC supplied while the plan does not allow it” a hard error, and §3.4 says own ISRCs are available only on higher plans. On a basic plan with `already_released = true` the user is therefore asked to supply a value that validation then blocks, so the previously-released workflow cannot be completed as written. This is the plan-capability interaction left open by DKM2-D1, not a request to decide that matrix; the spec can still state which behaviour applies in the meantime.
- **Proposed change:** Condition the §3.2/§3.4 ISRC request on the plan allowing own ISRC, or state that an existing ISRC for a previously-released upload is always accepted regardless of plan and exclude that case from the §4.1 error. Add the resulting warning to §4.2 (see DEEPSEEK-41).
- **Evidence:** reasoning only (internal inconsistency §3.2/§3.4 vs §4.1).
- **Confidence:** high

### DEEPSEEK-41 · §4.2 is presented as the warning list but omits three defined warnings

- **Section:** §4.2 (and §3.2, §3.3, §4.1)
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.2 is the spec’s “Warnings (Allow Export)” list, but it omits warnings that other sections define: the Apple Music Writer/Performer/Production credit-group warning (§3.3: “until then it is a warning”), the 11-digit CAE acceptance warning (§3.3 and the last row of §4.1), and the “`already_released = true` with no ISRC” request (§3.2/§3.4). An implementer who treats §4.2 as the warning catalogue will not implement them, and the Review screen will not show them.
- **Proposed change:** Add the three warnings to §4.2 with their exact conditions, or state explicitly that §4.2 is not exhaustive and that §3.2/§3.3 define additional warnings (less desirable, because §4.2 currently reads as the complete list).
- **Evidence:** reasoning only (internal inconsistency).
- **Confidence:** high

### DEEPSEEK-42 · No rule ties `release_date` to `already_released`

- **Section:** §3.1 (Release Date), §3.4, §4.1, §4.2
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.4 defines `release_date` as the original, past date when `already_released = true`, and §3.1 makes the date a user-set future date otherwise, but no validation rule checks either direction. `already_released = true` with a future date and `already_released = false` with a past date both pass: the lead-time warnings in §4.2 are scoped to “a user-set future date … and `already_released = false`”, so a past date on a new release triggers nothing, and a future date on a previously-released upload is not a lead-time case either. This is not a re-raise of DEEPSEEK-32, which scoped the lead-time warnings; the date/flag consistency check itself was never added.
- **Proposed change:** Add §4.1 errors (or at minimum §4.2 warnings): `already_released = true` requires `release_date <= today`; `already_released = false` on a plan that allows a custom date requires `release_date >= today`. State the comparison basis (“today” = local date at validation time, already defined in §3.1). If HUMAN prefers a warning for the past-date case, keep it out of §4.1.
- **Evidence:** reasoning only (internal gap §3.4/§3.1 vs §4.1/§4.2). The underlying DistroKid behaviour was not re-fetched; this finding does not rely on it.
- **Confidence:** high

### DEEPSEEK-43 · The Track Editor cannot collect the per-track primary artist that the manifest requires

- **Section:** §5.2 (and §3.2, §6.1)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 makes Primary Artist a required track field that may override the release artist, and §6.1 requires every track to carry `primary_artist` and requires a golden fixture with an override. The Track Editor in §5.2 lists Title, Version, ISRC, Audio File, Featured Artists, Explicit, Lyrics and Contributors, and the Tracks table columns are `#`, Title, ISRC, Duration and Status; neither screen has a Primary Artist control. The only way to produce the required override fixture is to bypass the specified UI, so the feature is not implementable from the screen description.
- **Proposed change:** Add Primary Artist to the Track Editor (defaulting to the release artist, editable for collaborations) and, if useful, to the Tracks table; state that clearing it restores the release-artist default.
- **Evidence:** reasoning only (internal inconsistency §3.2/§6.1 vs §5.2).
- **Confidence:** high

### DEEPSEEK-44 · “Read-only default” has no defined validation or export semantics

- **Section:** §3.4 (and §3.1 Label/Release Date, §6.1)
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.4 introduces three plan states — Available, Read-only default, Unavailable — but only defines Unavailable (“emit no manifest value; UI shows the DistroKid default”). “Read-only default” appears once, for Release Date, where it also means “no value is emitted”; for Label, §3.1 says it “defaults to the artist name where the plan does not allow a custom label”, which could mean the manifest emits the artist name or omits `label`. Because §6.1 says an absent key means “unavailable on the plan”, an implementer cannot tell whether a basic-plan Label is `"label": "<artist>"` or no `label` key, nor whether a Read-only default field counts as Required under §4.1. The same ambiguity leaves `already_released = true` on a plan without custom dates contradictory: §3.1 says no value is emitted when the plan does not allow a custom date, while §6.1 says `release_date` is present whenever `already_released` is true.
- **Proposed change:** Define each state once: Available (validated as Required, emitted), Read-only default (not user-editable, value is the stated default, and state whether it is emitted), Unavailable (not validated, not emitted, UI shows the DistroKid default). Then state Label’s state and manifest representation on plans without a custom label, and say whether the release-date state is evaluated per `already_released` branch.
- **Evidence:** reasoning only (internal gap §3.4 vs §3.1/§6.1).
- **Confidence:** high

### DEEPSEEK-45 · §5.5 points the browser-bridge button at the CSV section

- **Section:** §5.5
- **Type:** error
- **Severity:** minor
- **Finding:** §5.5 says the optional “Send to browser bridge” button is “see Section 6.2”, but §6.2 is “CSV Export (Universal)”; the browser bridge is §6.3. An implementer following the reference will land on the wrong contract.
- **Proposed change:** Change the reference to §6.3.
- **Evidence:** reasoning only (internal cross-reference).
- **Confidence:** high

### DEEPSEEK-46 · Two §4.3 cross-field checks have no stated severity

- **Section:** §4.3 (and §4.1, §4.2)
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.3 lists “ISRC uniqueness: No duplicate ISRCs within a project” and “Total album duration within DistroKid’s limit” without saying whether they are errors, warnings or advisory. Neither rule appears in §4.1’s error table or §4.2’s warning list, while the same section explicitly calls release-type classification a warning. An implementer therefore cannot tell whether duplicate ISRCs or an over-limit album blocks export; duplicate ISRCs in particular are a hard identifier conflict, not a style warning.
- **Proposed change:** Classify each rule. Prefer moving same-project ISRC uniqueness to §4.1 as an error and stating the album-duration check’s severity; if the duration limit is still unverified, keep the rule but say “warning until §11 is verified”.
- **Evidence:** reasoning only (internal gap §4.3 vs §4.1/§4.2).
- **Confidence:** high

### DEEPSEEK-47 · The normative credit object marks `pro` optional although it is conditionally required

- **Section:** §6.1 (and §3.3, §4.1)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §6.1’s normative credit object says “`ipi` and `pro` (optional)”, but §3.3 makes PRO Affiliation “Required if IPI is provided” and §4.1 enforces it as an error. A valid manifest therefore cannot have `ipi` without `pro`, and the version-1 schema needs that conditional if goldens are to match the validation rules; the contract as written lets a schema author mark both unconditionally optional.
- **Proposed change:** Change the contract to “`ipi` (optional); `pro` (required when `ipi` is present, otherwise absent)” and state that the version-1 schema encodes that conditional.
- **Evidence:** reasoning only (internal inconsistency §6.1 vs §3.3/§4.1).
- **Confidence:** high

## Top 3

1. **Resolve the previously-released ISRC contradiction** (DEEPSEEK-40): on a basic plan the spec asks for an ISRC that its own error rule rejects.
2. **Add a Primary Artist control to the Track Editor** (DEEPSEEK-43): the manifest requires a per-track override that the specified UI cannot collect.
3. **Complete the warning and date rules** (DEEPSEEK-41, DEEPSEEK-42, DEEPSEEK-46): warnings defined outside §4.2 are missing from the catalogue, and no rule ties `release_date` to `already_released`.

Result: complete
