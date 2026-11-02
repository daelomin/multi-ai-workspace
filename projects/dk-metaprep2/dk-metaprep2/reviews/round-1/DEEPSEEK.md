# DEEPSEEK review — round 1

Scope: `spec.md` v0.1. No `decisions.md`, `docs/`, `evals/` or `assets/` exists yet, so the spec is the only declared input present. I checked the DistroKid-specific claims against DistroKid's help centre; those pages return HTTP 403 to direct fetches from this environment, so the figures below are taken from the search-indexed text of the same article URLs and corroborating pages, all checked 2026-11-02.

### DEEPSEEK-1 · UPC is not a DistroKid input: DistroKid generates it

- **Section:** §3.1, §4.1, §5.1, §6.1
- **Type:** error
- **Severity:** blocking
- **Finding:** The spec makes UPC a required, user-supplied 12-digit field with its own hard validation, UI control and manifest value. DistroKid does not accept a custom/outside UPC on any plan; it generates a unique UPC for every upload, so the field and its EAN-13 rule validate data the target form cannot consume, while the tool would still not capture the value DistroKid actually assigns.
- **Proposed change:** Remove UPC from the user-input schema and from hard validation. Replace the §3.1 row with: "UPC — assigned by DistroKid — read-only, recorded after upload — not exported as an input." Delete the §4.1 UPC rule, change §5.1 to a read-only "DistroKid will assign a UPC" note, and change the §6.1 `upc` value to `null`/omitted plus an optional `assigned_upc` field intended for post-upload capture. If a catalog key is needed, use an internal `release_id`, not a UPC.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013648913 and "Using Existing ISRCs or UPCs for New DistroKid Uploads" (updated 2026-08-03: no custom UPC on any plan), checked 2026-11-02.
- **Confidence:** high

### DEEPSEEK-2 · Plan-dependent form capabilities are not modelled

- **Section:** §3.1, §3.2, general
- **Type:** gap
- **Severity:** major
- **Finding:** The DistroKid form surface depends on the plan: own ISRCs can be entered only on Musician Plus/Ultimate, Record Label and custom future release dates are Plus/Ultimate-only, basic-plan releases go live on processing, and per-country territory exclusions are a post-upload request on Plus/Ultimate rather than an upload-time list. The spec marks label, release date, ISRC and territories as universal required fields, so it will demand and export values the user's form cannot accept and block valid basic-plan releases; the form's "already released before?" branch, which changes ISRC/date handling, is also absent.
- **Proposed change:** Add a "DistroKid plan capability" section and a project-level plan selector (Musician / Musician Plus / Ultimate) plus an `already_released` flag. Give each field a state — Available / Read-only-default / Unavailable — and make validation conditional on the plan. For unavailable fields do not emit a manifest value; show the DistroKid default instead (auto ISRC, label = artist name, immediate release, worldwide). Record the target plan in the manifest.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013648913 (ISRC via Plus/Ultimate), https://support.distrokid.com/hc/en-us/articles/360013648113 (worldwide by default; exclusions by request on Plus/Ultimate), https://support.distrokid.com/hc/en-us/articles/52677658186003 (upload flow, plan-gated date), checked 2026-11-02.
- **Confidence:** high

### DEEPSEEK-3 · Contributor and share model is contradictory and unimplementable

- **Section:** §3.3, §4.1, §5.3, §7
- **Type:** inconsistency
- **Severity:** blocking
- **Finding:** Contributor data is declared "strongly recommended" (optional), yet §4.1 requires the writer shares on every track to sum to 100.00%: a track with no contributor rows sums to 0 and cannot export, and a single writer with a blank share (allowed by "required if multiple contributors") is undefined. Publisher is modelled twice — as a Role value and as Publisher Name/IPI attributes of a writer row — and the rule never says whether Publisher/Producer/Remixer rows participate in the 100% total, so a 100% writer row plus a 100% publisher row either double-counts or is silently excluded. The persistence model also contradicts the editor: §7 has global `contributors` plus a `track_contributors` many-to-many table, while §3.3/§5.3 define a per-track editor with "Copy from another track", and Producer/Remixer reference "contributor IDs" of unstated scope.
- **Proposed change:** Specify one model. Example: `contributors` is a global identity (legal name, IPI, PRO) deduplicated on (legal name, IPI, PRO); `track_credits` links `contributor_id` + role(s) + `writer_share` (0–100, 2 dp) + `publisher_share` (0–100, 2 dp, publisher rows only). Require `writer_share` to sum to 100.00 ±0.01 across rows that carry a writer share; define publisher shares as a separate layer that never enters that total; give Producer/Remixer rows no share and exclude them. If a track has no contributor rows, skip the sum check and emit a warning (or make contributors required and say so). Remove the duplicate Publisher role/attribute — either publisher rows own `publisher_share`, or publisher name/IPI are attributes of a writer row — and define whether "Copy from another track" links or copies.
- **Evidence:** reasoning only (internal contradictions); the writer-share/publisher-share distinction is standard PRO/split-sheet structure (DistroKid Publishing pages, checked 2026-11-02).
- **Confidence:** high

### DEEPSEEK-4 · Cover-art rules are wrong and contradict each other

- **Section:** §3.1, §4.1
- **Type:** error
- **Severity:** major
- **Finding:** §3.1 requires ≥3000×3000 px and JPEG/PNG, while the hard rule in §4.1 accepts ≥640×640 px; 640 is below DistroKid's 1000×1000 minimum, so the validator would pass artwork DistroKid rejects, and the two thresholds contradict each other. DistroKid specifies JPEG in RGB, minimum 1000×1000, 3000×3000 ideal; PNG is not listed, and the spec names sRGB without checking any colour profile or file-size limit.
- **Proposed change:** Replace both rows with one normative threshold: square 1:1; minimum 1000×1000; recommended 3000×3000 (warning); JPEG required; RGB/sRGB profile required; maximum file size per DistroKid's current limit. Add checks for file existence, decodability, format and colour profile, not only pixel dimensions, and make 3000×3000 an error only if HUMAN explicitly chooses to enforce the recommendation.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013534334 (minimum 1000×1000, ideal 3000×3000, JPEG, RGB), checked 2026-11-02.
- **Confidence:** high

### DEEPSEEK-5 · Release-date rule is stricter than DistroKid and internally inconsistent

- **Section:** §3.1, §4.1, §4.2
- **Type:** error
- **Severity:** major
- **Finding:** §4.1 makes "release date ≥ today + 7 days" a hard error "for playlist pitching", but Spotify's editorial pitch window is at least 3 weeks and DistroKid recommends roughly 4 weeks; a 7-day hard error therefore passes releases that cannot be pitched and blocks immediate releases that the basic plan allows. The document also says "≥ 3 weeks recommended" in §3.1 but warns only below 14 days in §4.1/§4.2, and "today" has no timezone or validation-time definition.
- **Proposed change:** State the DistroKid rule explicitly: no hard minimum from DistroKid, and custom dates require Musician Plus/Ultimate. Replace the error with warnings: < 21 days "outside Spotify editorial pitch window"; < 28 days "DistroKid recommends ~4 weeks". Define "today" as the local date at validation time and store `release_date` as a date with no time component. If the product intentionally enforces a 21-day policy, label it as an app policy, not a DistroKid rule, and make it a HUMAN decision.
- **Evidence:** internal inconsistency §3.1 vs §4.1; https://support.distrokid.com/hc/en-us/articles/52677658186003 and Spotify pitch guidance (3 weeks), checked 2026-11-02. Exact lead times vary by source; the finding that 7 days is not a DistroKid rule is high-confidence.
- **Confidence:** medium

### DEEPSEEK-6 · Audio rules misstate DistroKid and skip the checks that matter

- **Section:** §3.2, §4.1
- **Type:** error
- **Severity:** major
- **Finding:** §4.1 calls "WAV or FLAC, ≥44.1 kHz, ≥16-bit" DistroKid format rules, but DistroKid accepts WAV, MP3, FLAC, M4A, AIFF, CDDA and WMA, with a 24-bit/96 kHz ceiling and 1 GB / 5-hour limits; the 16-bit/44.1 kHz floor is a quality policy, not a DistroKid requirement. The hard rule also omits the channel count that §3.2 states ("stereo"), never checks that the file exists or decodes, and the Tracks screen's Duration column has no field or rule that computes it.
- **Proposed change:** Separate "DistroKid accepts" from "we recommend": list all accepted formats and DistroKid limits, and mark 16-bit/44.1 kHz stereo as a recommendation or an explicit app policy. Add hard checks: file exists and decodes, duration > 0 and within DistroKid's per-track/album limits, channel count per policy, total album duration. Populate Duration from decoded audio metadata and define it as a derived, read-only field.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013647753 (accepted formats, 24-bit/96 kHz, 1 GB, track/album length), checked 2026-11-02.
- **Confidence:** high on accepted formats; medium on exact limits.

### DEEPSEEK-7 · The "canonical manifest" is an example, not a contract

- **Section:** §6.1, §6.2
- **Type:** gap
- **Severity:** major
- **Finding:** The JSON example is the only definition of the export, but it has no schema version, no defined wire values (the text enum is "Single/EP/Album" while `"type": "album"`; role is "Songwriter" while `"role": "songwriter"`), no rule for null/omitted auto-assigned values, no date/timezone or language-code rule, and no path policy (absolute `cover_art_path`/`audio_path` leak local directories and are meaningless to a browser bridge). The CSV format has no header/column list, quoting/encoding rule, or multi-line-lyrics rule, so "maps 1:1" and "DISTROPILOT-compatible" cannot be implemented or tested.
- **Proposed change:** Add a versioned JSON Schema (`manifest_version: 1`) with field names, lower-case enum wire values, required/optional/null semantics, `release_date` as an ISO date without time, BCP-47 language tags, and a path policy (relative paths or file names plus SHA-256, never absolute paths). Define CSV as RFC 4180 UTF-8 with a stated BOM policy, fixed column order, and JSON-encoded lyrics/contributors. Add golden fixtures for one single, one EP and one album. If DISTROPILOT's schema is a real target, cite its version and validate against it; otherwise rename the format as internal and add an adapter.
- **Evidence:** reasoning only (internal); DISTROPILOT/ReleaseBrief compatibility is asserted in §2, §6.1 and §6.2 without a link, version or schema.
- **Confidence:** high

### DEEPSEEK-8 · No source or date for any DistroKid rule

- **Section:** general
- **Type:** gap
- **Severity:** major
- **Finding:** The spec's premise is "100% DistroKid-compliant", yet it cites no DistroKid page, article version or checked date for any requirement, and names third-party bridges (DISTROPILOT, ReleaseBrief) as compatibility targets without links. Several rules are, as written, not DistroKid rules (see DEEPSEEK-1, -4, -5 and -6), so without provenance the compliance claim cannot be audited or maintained as DistroKid changes its form.
- **Proposed change:** Add §11 "Sources and provenance" with one row per rule: rule id, DistroKid help URL, article title, date checked, and status (Required / Recommended / App policy). Mark every unverified claim "assumption — verify before release", add a re-check trigger for each release, and put the same source metadata beside the bundled enum assets.
- **Evidence:** reasoning only; all external claims re-checked on 2026-11-02 show several spec rules diverging from DistroKid's help-centre text.
- **Confidence:** high

### DEEPSEEK-9 · Missing required credit roles and Apple Music credits

- **Section:** §3.3, §3.2
- **Type:** gap
- **Severity:** major
- **Finding:** DistroKid requires the real (legal) name of each songwriter, and Apple Music requires at least one Writer, one Performer and one Production & Engineering credit per track; the spec calls contributor data "strongly recommended", has no Performer or Engineer role, and has no Apple credits mapping. A tool exporting the current model cannot be "100% compliant" for Apple delivery, and its "no IPI" warning is the wrong primary check when the legal name itself is required.
- **Proposed change:** Make songwriter legal name required (not strongly recommended) for each writer row. Add credit groups Writer, Performer and Production & Engineering, with at least one row per group required when the release targets Apple Music, and add Performer and Engineer to the role enum. Map these to the DistroKid "Apple Music credits" step and record the target stores. Keep IPI/PRO/publisher strongly recommended with warnings as today.
- **Evidence:** https://support.distrokid.com/hc/en-us/articles/360013545554 (DistroKid asks for songwriters' real names) and https://help.apple.com/itc/musicstyleguide/en.lproj/itce0a71e240.html (Writer/Performer/Production credit groups), checked 2026-11-02.
- **Confidence:** high

### DEEPSEEK-10 · No technical baseline for implementing the Qt app

- **Section:** §2, §7, §8
- **Type:** gap
- **Severity:** major
- **Finding:** The spec names Qt modules but not the Qt major version, C++ standard, build system, dependency policy, packaging/signing/notarization, or licensing. Qt 5 vs Qt 6 changes APIs and QtWebEngine availability, and distributing a Qt app under LGPLv3 with QtWebEngine has compliance obligations that the AppImage/Flatpak targets make concrete, so an implementer cannot choose a toolchain from this document.
- **Proposed change:** Add §7.1 "Technical baseline": Qt 6.x LTS (or state 5.15), C++17/20, CMake, supported compilers per OS, exact Qt modules (Core, Widgets, Sql with SQLite driver, Network, optional WebEngine), static vs dynamic linking, LGPLv3 compliance plan (dynamic linking, licence texts, relinkability for AppImage), code signing/notarization, crash reporting (off), and minimum OS versions. Pin the versions used by CI.
- **Evidence:** reasoning only; no technical baseline appears in the spec.
- **Confidence:** high for the gap; medium for the specific version recommendation.

### DEEPSEEK-11 · "No credentials stored" is contradicted by WebEngine login; bridge security is underspecified

- **Section:** §6.3, §6.4, §8
- **Type:** risk
- **Severity:** major
- **Finding:** §8 promises "No credentials stored", but §6.4 logs the user in to `https://distrokid.com/new` in an embedded QWebEngineView; a default QWebEngineProfile persists cookies, cache and localStorage on disk, which includes the DistroKid session. The §6.3 bridge is protected only by "a random token" and a loopback bind; it does not specify token transport/entropy/lifetime, an Origin/CORS policy, allowed methods, or whether any local process can read the manifest.
- **Proposed change:** Use an off-the-record QWebEngineProfile for the DistroKid view (no persistent cookies/cache, cleared on close) or explicitly document that the session is stored and where, and drop the absolute "no credentials stored" claim. For the bridge specify: 256-bit per-session token required in an `Authorization` header (not a query string), reject requests without it, no wildcard `Access-Control-Allow-Origin`, validate `Origin` against the extension ID, `GET` only, ephemeral port on `127.0.0.1`, and disabled by default. Add a threat note that any local process can reach loopback.
- **Evidence:** reasoning only; Qt WebEngine default-profile persistence is standard behaviour, and §8's claim is absolute.
- **Confidence:** high

### DEEPSEEK-12 · Identifier validation is too weak for a compliance tool

- **Section:** §3.1, §3.3, §4.1
- **Type:** gap
- **Severity:** minor
- **Finding:** If UPC is retained at all, the rule checks only 12 digits and calls it "EAN-13 compatible", conflating UPC-A (12 digits) with EAN-13 (13 digits) and never verifying the GS1 check digit, so invalid barcodes pass. The ISRC regex allows mixed hyphenation (e.g. `US-ABC1234567`), and IPI is "9–11 digits" with no check-digit rule, so malformed identifiers pass the hard rules.
- **Proposed change:** If UPC remains, validate UPC-A (12 digits) or EAN-13 (13 digits) with the GS1 mod-10 check digit and state which is accepted. Normalise ISRC to 12 characters and require either all three hyphens or none. Validate the 9-digit IPI Name Number and, if 11-digit CAE forms are accepted, document the extra check digits; otherwise keep the looser rule as a warning. State the uniqueness scope: within the project, plus optional catalog check.
- **Evidence:** reasoning only for the spec mismatch; GS1 check-digit and ISRC structure rules are standard (IFPI/GS1).
- **Confidence:** high

### DEEPSEEK-13 · Several stated rules are not in the validation engine; undefined terms

- **Section:** §3.1, §3.2, §4.2, §4.3, §5.2
- **Type:** gap
- **Severity:** minor
- **Finding:** The schema tables state rules that §4 never enforces: artist name "no spammy text" (undefined), track title "no version info or featured artists" (no rule), and §4.3's release-type counts leave a 2-track release undefined ("Single 1; EP 3–6; Album 7+"). §5.2 shows a Duration column but no field or derivation exists, and the §4.2 warning "explicit but no lyrics" mixes content rating with an optional field.
- **Proposed change:** Add explicit rules for the title/artist checks (e.g. advisory warnings for "feat.", "remix", URLs, repeated characters) or move them to "advisory, not validated". Define a 2-track release as an EP-with-warning or state the correct DistroKid boundary. Remove or reword the explicit/lyrics warning, and define Duration as derived from the audio file (see DEEPSEEK-6).
- **Evidence:** reasoning only; DistroKid upload guidance confirms titles should not contain version/featured-artist info (search summary, checked 2026-11-02).
- **Confidence:** high

### DEEPSEEK-14 · Reference data and enums are not specified, bundled or versioned

- **Section:** §3.1, §3.3, §8, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The app is offline-first and claims to enforce enums, but the genre list, language values, territory codes and PRO list are not enumerated, and the declared `assets/` input does not exist. AI disclosure is typed "Boolean / String" even though DistroKid's disclosure covers separate categories (lyrics, vocals, instrumental performance, audio), so the field cannot be validated or exported consistently.
- **Proposed change:** Add versioned JSON assets (genre list, language tags, ISO 3166-1 alpha-2 territories, PRO list) with source URL and date checked, and validate against them offline. Replace AI disclosure with an enum/flag set (`none`, `lyrics`, `vocals`, `instrumental`, `audio`, multiple allowed) plus the exemptions DistroKid states. Record the asset version in the manifest and surface "reference data outdated" warnings.
- **Evidence:** DistroKid AI disclosure categories and Apple/Spotify DDEX reporting (2026 sources, checked 2026-11-02); `assets/` is absent from the project tree.
- **Confidence:** medium (AI categories are newly reported and may change)

### DEEPSEEK-15 · Guided Fill conflicts with the stated ToS scope

- **Section:** §1, §6.4
- **Type:** question
- **Severity:** minor
- **Finding:** §1 puts "any action that violates DistroKid's terms of service" out of scope, while §6.4 includes a Guided Fill mode that the same paragraph says "may violate terms if used to automate submission". Even with manual Submit, injecting values into the DistroKid page and the browser bridge touch the ToS, so the document cannot both exclude and ship it without a HUMAN scope decision.
- **Proposed change:** HUMAN to decide: (a) drop §6.4 and keep only the manifest export plus an optional read-only bridge, or (b) keep Guided Fill behind explicit per-session consent, document the ToS risk, never auto-click Submit, and name the feature "assisted entry — user submits". Record the decision in `decisions.md` and reference it from §1 and §6.4.
- **Evidence:** internal contradiction §1 vs §6.4; DistroKid terms are legal scope, so this is a HUMAN decision, not a reviewer choice.
- **Confidence:** high

## Top 3

1. **Remove the fake UPC input and model plan capabilities** (DEEPSEEK-1, DEEPSEEK-2): the form does not accept a supplied UPC, and several other "required" fields are plan-gated.
2. **Rework the contributor and share model** (DEEPSEEK-3, DEEPSEEK-9): the 100% rule cannot pass an optional-contributor track, publisher is double-modelled, and Apple-required credit roles are missing.
3. **Correct and source the artwork/date/audio rules** (DEEPSEEK-4, DEEPSEEK-5, DEEPSEEK-6, DEEPSEEK-8): three hard rules diverge from DistroKid's published requirements and the spec cites no provenance.

Result: complete
