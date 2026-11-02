# DEEPSEEK review — round 2

Scope: `spec.md` v0.2, read against the round-1 review and `reviews/round-1/CONSOLIDATION.md`. `decisions.md`, `docs/`, `evals/` and `assets/` are still absent, so `spec.md` is the only declared input present; the consolidation deferred creating them, so their absence is not re-raised here. DistroKid help pages still return HTTP 403 to direct fetches from this environment, so external figures below are taken from the search-indexed text of the linked official articles, all checked 2026-11-02. Findings that touch an open HUMAN decision are marked minor and do not reopen the decision.

### DEEPSEEK-16 · Release-type boundaries contradict DistroKid's published classification

- **Section:** §4.3 (and §3.1, Release Type)
- **Type:** error
- **Severity:** major
- **Finding:** §4.3 says a Single should have 1 track, an EP 2–6 (with a 2-track EP warning) and an Album 7+, but DistroKid's own support article says Single = 1–3 songs, EP = 4–6 songs under 30 minutes, and Album = 7+ songs (or any release over 30 minutes); services also auto-classify by track count and runtime. A 2- or 3-track release is therefore a Single, not an EP, and the duration criteria (10-minute track, 30-minute total) are absent from the spec entirely.
- **Proposed change:** Replace the first §4.3 bullet with DistroKid's track-count and duration rules, make the classification a derived suggestion (advisory) or warn when the selected Release Type contradicts it, and add the source as a new §11 row. Keep it a warning until HUMAN decides otherwise.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/55115193705875-Singles-EPs-and-albums-which-format-should-you-release-on-DistroKid (English article; search-indexed Dutch version surfaced with the 1–3 / 4–6 / 7+ and 30-minute text), checked 2026-11-02; direct fetch returned HTTP 403. Corroborated by Spotify/Apple classification guidance.
- **Confidence:** high on 1–3 / 4–6 / 7+; medium on the 10-minute and 30-minute edge rules.

### DEEPSEEK-17 · AI disclosure categories do not match the DistroKid form

- **Section:** §3.1 (AI Disclosure), §6.1, §11
- **Type:** error
- **Severity:** major
- **Finding:** The spec models AI disclosure as `lyrics`, `vocals`, `instrumental`, `audio` or `none`. DistroKid's current AI Credits step asks whether AI was used and offers four categories — the lyrics, the music/composition, all of the audio, part of the audio — with an artist-persona follow-up when "all of the audio" is chosen; there is no `vocals`, `instrumental` or `none` category, and answering "no AI" is how none is recorded. An exported value from the current enum therefore cannot be mapped 1:1 to the form and may misstate the disclosure.
- **Proposed change:** Replace the set with `lyrics`, `music`, `all_audio`, `part_of_audio`; represent "no AI used" as an explicit `ai_used: false` (or an empty set) rather than a `none` category; record the `all_audio` artist-persona answer; mark the disclosure Required with "no AI" as a valid answer; update the §6.1 example and the §11 row.
- **Evidence:** https://support.distrokid.com/hc/da/articles/50784235803411 (AI Credits; English equivalent at `/hc/en-us/articles/50784235803411`) and https://support.distrokid.com/hc/vi/articles/50784709021971 (category-selection steps), checked 2026-11-02; direct fetch returned HTTP 403. Corroborated by https://www.rightsdocket.com/insights/ai-music-disclosure-distrokid-spotify-apple-music-2026 (2026).
- **Confidence:** high on the four categories; medium on exact requiredness.

### DEEPSEEK-18 · The 200 ms validation target conflicts with audio/artwork decoding

- **Section:** §8 (Performance), §4.1, §4
- **Type:** inconsistency
- **Severity:** major
- **Finding:** §4.1 makes audio and cover-art decoding hard validation rules, §4 says the validation engine runs continuously or on "Validate", and §8 then requires a 20-track album to validate in under 200 ms. Decoding twenty audio files (each up to 1 GB / 5 hours) plus artwork cannot meet that budget, so the NFR is unimplementable as written unless the spec explicitly separates and caches file checks.
- **Proposed change:** Split ingest-time file checks (existence, decode, duration, hash, format) from metadata validation; cache decoded facts keyed by path + size + mtime + SHA-256; define the <200 ms budget as rule evaluation over cached facts and state that file checks run on import or file change.
- **Evidence:** reasoning only (internal contradiction between §4.1/§4 and §8).
- **Confidence:** high.

### DEEPSEEK-19 · The manifest cannot export a per-track primary artist override

- **Section:** §6.1, §3.2 (Primary Artist)
- **Type:** gap
- **Severity:** major
- **Finding:** §3.2 makes Primary Artist a required track field that may override the release artist for collaborations, but the §6.1 track object has no `primary_artist` key and the contract never defines one. An override collected in the UI is therefore silently lost in every export, and the manifest will credit the release artist on tracks where the spec says it must not.
- **Proposed change:** Add `primary_artist` to the track object and the version-1 schema, state whether it is always emitted or omitted when equal to `release.artist` (prefer always emitting, since §6.1 only permits omission for unavailable/assigned values), and add a golden fixture with a per-track override.
- **Evidence:** reasoning only (internal inconsistency between §3.2 and §6.1).
- **Confidence:** high.

### DEEPSEEK-20 · Manifest optional-value and enum wire semantics are undefined or contradictory

- **Section:** §6.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The contract says unavailable/assigned values are omitted and "never emitted as empty strings", but the example emits `"version": ""`, and the spec never says whether an optional text left blank is omitted or `null`. The contract also defines wire values for `type` and `role` but not `target_plan` (the example uses `"musician_plus"` while §3.4 says "Musician Plus") or `ai_disclosure`.
- **Proposed change:** State the three-state rule for optional text (absent = not applicable/unavailable, `null` = explicitly blank, no empty strings) and fix the example; add `target_plan` wire values (`musician|musician_plus|ultimate`) and the `ai_disclosure` values to the contract and example.
- **Evidence:** reasoning only (internal inconsistency).
- **Confidence:** high.

### DEEPSEEK-21 · Cover-art maximum file size is a limit DistroKid does not publish

- **Section:** §3.1 (Cover Art File), §11
- **Type:** error
- **Severity:** minor
- **Finding:** §3.1 requires a maximum cover-art file size "per DistroKid's current limit (§11, unverified)", but DistroKid's artwork help article states format, colour mode and minimum/ideal dimensions and no maximum file size, and §11 has no corresponding row. The rule therefore invents a limit and points at a source that does not support it, so an implementer may reject valid artwork or choose an arbitrary cap.
- **Proposed change:** Remove the DistroKid max-size requirement; if the app wants a cap, state it as an app policy with an explicit number and add it to §11 as App policy. Keep the verified JPEG/RGB/1000×1000/3000×3000 rules.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013534334 (search-indexed; format, RGB, min/ideal size, no max size), checked 2026-11-02; direct fetch returned HTTP 403.
- **Confidence:** medium-high.

### DEEPSEEK-22 · Accepted-audio list keeps the legacy CDDA format

- **Section:** §3.2 (Audio File), §11
- **Type:** error
- **Severity:** minor
- **Finding:** The accepted-format list includes CDDA, but DistroKid's current audio help article lists WAV, MP3, M4A, FLAC, AIFF and WMA; CDDA appears only in older or third-party legacy listings. Accepting a non-current format can let a file pass the validator that DistroKid rejects, and the spec's "unverified" marker does not identify the stale item.
- **Proposed change:** Replace the list with the current official formats; drop CDDA or label it "legacy — verify before accepting". State the file-name, 1 GB and 5-hour/10-hour limits in the rule or explicitly defer them with a source, and update §11.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013647753 (search-indexed; current list WAV/MP3/M4A/FLAC/AIFF/WMA; CDDA only in legacy quotes), checked 2026-11-02; direct fetch returned HTTP 403.
- **Confidence:** medium.

### DEEPSEEK-23 · Territories are simultaneously post-upload-only and an upload-time multi-select

- **Section:** §3.1 (Territories), §5.1, §6.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.1 says per-country exclusions are a post-upload request on higher plans, "not an upload-time list", yet §5.1 offers a territories multi-select and §6.1 exports a `territories` array. The spec does not say whether that array is an upload value, a post-upload request list, or a read-only record, so bridge and manual-entry semantics are ambiguous.
- **Proposed change:** Pick one: (a) remove the upload-time multi-select and exported array, record the worldwide default and keep a separate post-upload exclusion request; or (b) if the form does accept a territory list, correct §3.1 and state exactly what the array means and which plan states expose it.
- **Evidence:** internal inconsistency; DistroKid defaults to worldwide and its help articles cover store selection rather than a documented country list (https://support.distrokid.com/hc/en-us/articles/360013648113 and https://support.distrokid.com/hc/en-us/articles/360013647693), checked 2026-11-02.
- **Confidence:** medium.

### DEEPSEEK-24 · "DistroKid assigns" ISRC is required to be recorded but has no manifest field

- **Section:** §3.2, §6.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 says a track's ISRC disposition is recorded as either the user's own ISRC or "DistroKid assigns", but §6.1 says DistroKid-assigned values are omitted and provides no field to distinguish "assigned" from "user left blank" or "not applicable". The manifest therefore cannot represent the §3.2 requirement.
- **Proposed change:** Add an explicit `isrc_source` (`user` | `distrokid`) or a boolean `isrc_auto_assigned` to the track object, define how it interacts with `already_released` and the plan states, or change §3.2 to say the disposition is a UI-only state.
- **Evidence:** reasoning only (internal inconsistency).
- **Confidence:** high.

### DEEPSEEK-25 · "Project folder" paths do not fit a `.dkmeta` SQLite file

- **Section:** §6.1, §7
- **Type:** gap
- **Severity:** minor
- **Finding:** §7 stores a project as a single SQLite file with a `.dkmeta` extension, while §6.1 defines manifest paths as "file names relative to the project folder". A file has no folder, and the spec never says whether audio and cover files are copied into a project package, referenced in place, or embedded, so paths and SHA-256s are not reproducible across machines.
- **Proposed change:** Define the project container — either a folder containing `<name>.dkmeta` and an asset directory, or a single file with embedded assets — and state how relative paths resolve, whether files are copied on import, and how the browser bridge consumes them.
- **Evidence:** reasoning only (internal inconsistency between §6.1 and §7).
- **Confidence:** high.

### DEEPSEEK-26 · IPI 9-digit rule still reads as an error for 11-digit values (DKM2-D6)

- **Section:** §3.3 (IPI), §4.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.3 says 11-digit CAE forms are "accepted with a warning only" pending DKM2-D6, while §4.1 says "IPI must be a valid 9-digit IPI Name Number; 11-digit values produce a warning". The §4.1 wording can be read as a hard 9-digit requirement with a warning bolted on, so an implementer cannot tell whether 11-digit input blocks export. This is a wording alignment only and does not ask to reopen DKM2-D6.
- **Proposed change:** Reword §4.1 to match §3.3: "9-digit IPI Name Numbers are validated as an error; 11-digit CAE forms are accepted with a warning until DKM2-D6 is decided", or state the single normative outcome with a reference to the decision.
- **Evidence:** reasoning only (internal inconsistency in the v0.2 text).
- **Confidence:** high.

### DEEPSEEK-27 · Residual "DISTROPILOT-compatible" and "maps 1:1" claims survive the §6.1 caveat

- **Section:** §1, §2, §3.1, §6.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §6.1 now says the manifest is internal and DISTROPILOT/ReleaseBrief compatibility is unverified until a schema is cited, but §2 still says the exporters generate "DISTROPILOT-compatible JSON" and §1 says the manifest "maps 1:1 to the DistroKid upload form fields". The residual claims contradict the merged caveat and may lead implementers to target an unvalidated schema.
- **Proposed change:** Qualify or remove the §1/§2 claims; point them to §6.1 and DKM2-D8 and the adapter, or state that DISTROPILOT compatibility is a future adapter, not a v1 contract.
- **Evidence:** reasoning only (internal inconsistency with the merged §6.1 text).
- **Confidence:** high.

### DEEPSEEK-28 · Publisher name/IPI still has no defined storage location

- **Section:** §3.3 (Publisher), §7
- **Type:** gap
- **Severity:** minor
- **Finding:** The table describes "Publisher Name / IPI" as attributes of a Publisher credit with no duplicate on writer rows, but §7 gives `contributors` only legal name/IPI/PRO and `track_credits` only roles and shares; there is no stated home for a publisher name/IPI distinct from the contributor identity. An implementer cannot tell whether a Publisher is a separate `contributors` row (legal name = publisher name, IPI = publisher IPI) or a pair of extra `track_credits` columns.
- **Proposed change:** State that a Publisher credit is a `contributors` row with role Publisher, whose legal name and IPI are the publisher name/IPI (and remove the duplicate table field), or add explicit `publisher_name` and `publisher_ipi` columns to `track_credits` and update §3.3/§7.
- **Evidence:** reasoning only (internal ambiguity).
- **Confidence:** high.

### DEEPSEEK-29 · Contributor deduplication on nullable (legal name, IPI, PRO) can merge or fail to merge identities

- **Section:** §3.3
- **Type:** risk
- **Severity:** minor
- **Finding:** Identities are deduplicated on (legal name, IPI, PRO), but IPI and PRO are optional. A SQL UNIQUE constraint over nullable columns permits multiple rows with NULLs, so contributors without an IPI will not deduplicate, while two different writers with the same legal name and no IPI would collide and could have their credits or shares conflated.
- **Proposed change:** Make an internal `contributor_id` the identity. Treat (legal name, IPI, PRO) as a match hint: auto-link only on a non-null IPI (or IPI + PRO), otherwise present a merge suggestion for user confirmation; do not enforce a unique constraint over nullable fields.
- **Evidence:** reasoning only (SQL/identity semantics).
- **Confidence:** medium-high.

## Top 3

1. **Correct the release-type classification** (DEEPSEEK-16): the current 1 / 2–6 / 7+ boundaries misclassify every 2- and 3-track single and omit DistroKid's duration rules.
2. **Replace the AI disclosure enum** (DEEPSEEK-17): the current categories do not exist on DistroKid's AI Credits step, so the exported disclosure cannot map to the form.
3. **Close the manifest and validation gaps** (DEEPSEEK-19, DEEPSEEK-18): export the per-track primary artist, and define where file decoding lives so the 200 ms target is achievable.

Result: complete
