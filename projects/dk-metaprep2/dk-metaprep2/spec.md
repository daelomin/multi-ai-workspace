version = v0.3
date = 2026-11-02

> **Status of DistroKid rules (v0.3):** every DistroKid-specific rule in this spec is traceable through §11 and marked *Required*, *Recommended* or *App policy*. Items marked *unverified* come from reviewer reports of DistroKid help pages that could not be fetched directly and must be re-checked before release. Open HUMAN decisions are listed once, in §12.

Below is a detailed technical specification for a **Qt-based desktop application** designed to prepare, validate, and export a 100% DistroKid‑compliant metadata package. The tool does not attempt to bypass DistroKid’s lack of a public API; instead, it focuses on **eliminating metadata errors** by providing a single interface for all required and recommended fields, enforcing strict validation, and exporting a manifest that can be used with existing form‑filling bridges (e.g., DISTROPILOT, ReleaseBrief) or for manual entry with confidence.

---

## 1. Purpose & Scope

The application (“DK‑MetaPrep”) allows an artist, manager, or label to:

- Define a release (single, EP, album) with all DistroKid‑required fields.
- Define each track with its own metadata, including identifiers and contributor credits.
- Validate every field against DistroKid’s rules (formats, lengths, required‑ness).
- Export a **canonical manifest** in CSV and/or JSON whose fields are mapped to the DistroKid upload form fields (mapping table in `docs/`; the manifest is an internal format, see §6.1).
- Optionally push the manifest to a browser‑based form‑filling extension via a local bridge, or use an embedded WebEngine view to assist manual filling (with user supervision).

**Out of scope:** automated submission without user review, bypassing CAPTCHAs, or any action that violates DistroKid’s terms of service.

---

## 2. Architecture Overview

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| **UI** | Qt Widgets (or Qt Quick Controls 2) | Multi‑page wizard: Release → Tracks → Contributors → Review → Export |
| **Data Model** | Qt Core (`QAbstractItemModel` for tracks and contributors) + SQLite (via `QtSql`) | Persist projects locally, support undo/redo, session recovery |
| **Validation Engine** | Custom C++ classes + `QRegularExpression` | Field‑level and cross‑field validation |
| **Exporters** | `QJsonDocument`, `QTextStream` (CSV) | Generate the canonical JSON manifest (§6.1; DISTROPILOT via a future adapter, DKM2‑D8), generic CSV, and a human‑readable “upload sheet” |
| **Bridge (optional)** | `QtWebEngine` + `QWebChannel` or local HTTP server | Expose the validated manifest to a browser extension (e.g., via `localhost` endpoint) or inject data into the DistroKid page under user control |

---

## 3. Data Schema – Fields & Mapping to DistroKid

The schema is split into three levels: **Release**, **Track**, and **Contributor**. Each field is annotated with its DistroKid requirement status (Required, Strongly Recommended, Optional) and validation rules.

### 3.1 Release‑Level Fields

| Field | DistroKid Status | Type | Validation / Notes | Maps to DistroKid Form |
|-------|------------------|------|-------------------|------------------------|
| **Artist / Band Name** | Required | String | No spammy text; consistent with track credits. | “Artist/Band Name” |
| **Release Title** | Required | String | Exact title, including version info if applicable. | “Album Title” |
| **Release Type** | Required | Enum (Single, EP, Album) | Checked against DistroKid’s track‑count and duration classification (§4.3); a contradiction is a warning. | “Release Type” |
| **Release Date** | Required (custom date plan‑gated, see §3.4) | Date (ISO, no time component) | No DistroKid hard minimum. Warnings only, see §4.2. “Today” = local date at validation time. | “Release Date” |
| **UPC** | **Not an input** | — | DistroKid generates the UPC for every upload; no custom UPC is accepted. The tool never asks for or validates one. An optional read‑only `assigned_upc` can be recorded after upload. Internal catalog key: `release_id`. | “UPC” (read‑only) |
| **Label Name** | Required; plan‑gated (see §3.4) | String | Defaults to the artist name where the plan does not allow a custom label. | “Record Label” |
| **Language** | Required | Enum (BCP‑47 tag) | Primary language of the release, from the bundled reference data (§3.5). | “Language” |
| **Primary Genre** | Required | Enum | From the bundled genre list (§3.5). | “Primary Genre” |
| **Secondary Genre** | Optional | Enum | Optional second genre. | “Secondary Genre” |
| **Cover Art File** | Required | File path | Square (1:1); JPEG; RGB/sRGB; minimum 1000×1000 px (error); 3000×3000 px recommended (warning). File must exist and decode. DistroKid publishes no maximum artwork file size (§11, unverified); the app applies none. | “Album Artwork” |
| **Explicit Flag (release‑level default)** | Required | Boolean | Can be overridden per track. | “Explicit Content” |
| **Excluded Territories** | Optional; default empty = worldwide; plan‑gated (see §3.4) | List of ISO 3166‑1 alpha‑2 codes | Per‑country exclusions are a post‑upload request on higher plans, not an upload‑time form value. The list is a record used to prepare that request (checklist in the upload sheet); it is exported as `excluded_territories` and never treated as a form field. Exact plan gating: DKM2‑D1. | none (post‑upload request) |
| **AI Disclosure** | Required (“no AI” is a valid answer) | `ai_used` boolean + set of `lyrics`, `music`, `all_audio`, `part_of_audio`; `artist_persona` answer when `all_audio` | Categories as reported for DistroKid’s AI Credits step (unverified, §11). `ai_used = false` means no categories; categories require `ai_used = true`. `artist_persona` (boolean) is asked only when `all_audio` is selected. | “AI Credits” |

**Required release‑level fields:** release title, release type, artist, language, primary genre, cover art, explicit default, AI disclosure answer (`ai_used`). Release date is required but defaults to “as soon as processed” on plans without custom dates. UPC is assigned by DistroKid and is not an input.

### 3.2 Track‑Level Fields

| Field | DistroKid Status | Type | Validation / Notes | Maps to DistroKid Form |
|-------|------------------|------|-------------------|------------------------|
| **Track Title** | Required | String | No version info or featured artists in title (use separate fields). | “Song Title” |
| **ISRC** | Optional (own ISRC only on plans that allow it, see §3.4; otherwise DistroKid assigns) | String (12 chars, normalised without hyphens) + `isrc_source` (`user` \| `distrokid`) | Supply if you have an existing catalog; auto‑assignment risks fragmented records. `isrc_source` is `distrokid` when no own ISRC is supplied or the plan does not allow one (§3.4), and `user` otherwise; with `already_released = true` and no ISRC, a warning asks for the existing ISRC. | “ISRC” |
| **Primary Artist** | Required (inherited from release, but can override) | String | Must match release artist unless it’s a collaboration. | “Primary Artist” |
| **Featured Artists** | Optional | List of strings | Comma‑separated in UI; exported as array. | “Featured Artists” |
| **Audio File** | Required | File path | Must exist and decode. DistroKid accepts WAV, MP3, FLAC, M4A, AIFF and WMA (unverified, §11); legacy formats such as CDDA are not accepted. File‑name, size and length limits are those in §11. 44.1 kHz / 16‑bit stereo is an **app policy** recommendation (warning), not a DistroKid rule. | “Audio File” |
| **Duration** | Derived | Seconds (read‑only) | Computed from decoded audio; shown in the Tracks table. | Implicit |
| **Explicit Flag** | Required | Boolean | Per‑track override of release default. | “Explicit” |
| **Version / Remix Info** | Optional | String | E.g., “Radio Edit”, “Remix”. | “Version” |
| **Producer(s)** | Strongly Recommended | List of contributor IDs | Links to contributor records. | “Producer” |
| **Remixer** | Optional (for remixes) | Contributor ID | Only if applicable. | “Remixer” |
| **Lyrics** | Optional | Text (multiline) | Can be pasted or loaded from file. | “Lyrics” |
| **Track Number** | Auto‑generated | Integer | Derived from order in UI. | Implicit |

**Required track‑level fields:** track title, primary artist name, and an audio file that exists and decodes. ISRC is required in the export only in the sense that `isrc_source` is recorded: the user’s own ISRC (`user`) or “DistroKid assigns” (`distrokid`, ISRC omitted).

### 3.3 Contributor‑Level Fields (Songwriters & Publishers)

DistroKid asks for the real (legal) name of each songwriter; IPI/PRO/publisher data are optional but their payment utility depends on accuracy. The model below is the single normative contributor model.

**Data model.**
- `contributors` — global identity keyed by an internal `contributor_id`: legal name, IPI, PRO. A Publisher is a `contributors` row (legal name = publisher name, IPI = publisher IPI) used with role Publisher. (legal name, IPI, PRO) is a match hint, not a unique constraint: auto‑link only on a non‑null IPI (or IPI + PRO); otherwise offer a merge suggestion the user confirms. Two contributors with the same name and no IPI stay separate until merged.
- `track_credits` — links a track to a `contributor_id` with one or more roles and, where applicable, `writer_share` (0–100, 2 dp) and `publisher_share` (0–100, 2 dp, publisher credits only).
- “Copy from another track” **copies** credit rows (not links); the contributor identity itself stays shared.

| Field | Status | Type | Validation / Notes |
|-------|--------|------|-------------------|
| **Legal Name** | Required for each Songwriter credit; Strongly Recommended otherwise | String | Real name, as registered with PRO. |
| **Role** | Required for each credit | Enum (Songwriter, Performer, Producer, Engineer, Publisher, Remixer) | Songwriter carries `writer_share`; Publisher carries `publisher_share`; Performer, Producer, Engineer and Remixer carry no share. |
| **IPI / CAE Number** | Strongly Recommended | String | 9‑digit IPI Name Number validated (error if malformed); 11‑digit forms accepted with a warning only, until HUMAN decides (§12, DKM2‑D6). |
| **PRO Affiliation** | Strongly Recommended | Enum (bundled list, §3.5) | Required if IPI is provided. |
| **Publisher name / IPI** | Strongly Recommended for Publisher credits | — | No separate fields: for a Publisher credit these are the contributor’s Legal Name and IPI. Nothing is stored on writer rows. |
| **writer_share** | Required on every Songwriter credit when the track has more than one Songwriter; a sole Songwriter defaults to 100.00 | Decimal (0–100, 2 dp) | Sum over Songwriter credits of a track = 100.00 ±0.01. |
| **publisher_share** | Optional | Decimal (0–100, 2 dp) | Separate layer; never enters the writer total. |
| **Signed Date** | Optional | Date | For split sheets. |
| **Contact Email** | Optional | Email | For internal records. |

**Credit groups for Apple Music.** Apple Music expects at least one Writer, one Performer and one Production & Engineering credit per track (unverified, §11). Whether this is enforced depends on HUMAN scope decision DKM2‑D5; until then it is a warning.

**Key guideline:** A track with no contributor rows skips the share‑sum check and raises a warning. Supplying names without IPIs creates noise: warn when a contributor has a name but no IPI, and when publisher fields are partially filled.

### 3.4 DistroKid Plan Capabilities

The DistroKid form depends on the plan (reported, unverified, §11): own ISRCs, custom Record Label and custom future release dates are available only on higher plans (Musician Plus / Ultimate); basic plans go live on processing and default the label to the artist name; per‑country territory exclusions are a post‑upload request. The project therefore carries:

- `target_plan` ∈ {Musician, Musician Plus, Ultimate} (selector on the Release screen, recorded in the manifest);
- `already_released` (boolean) — the form’s “released before?” branch, which changes ISRC and date handling.

Each field is in one of three states per plan: **Available**, **Read‑only default**, **Unavailable**. Validation is conditional on the state; Unavailable fields emit no manifest value and the UI shows the DistroKid default (auto ISRC, label = artist, immediate release, worldwide). The exact plan matrix is data (§3.5), not code, and must be confirmed by HUMAN (§12, DKM2‑D1).

### 3.5 Reference Data

The app is offline‑first, so enums are bundled as versioned JSON assets in `assets/`: genre list, language tags (BCP‑47), territories (ISO 3166‑1 alpha‑2), PRO list, plan capability matrix. Each asset carries `source_url`, `date_checked` and `version`. The asset versions are written to the manifest, and the app warns when reference data is older than the configured age (default 180 days). The `assets/` content is not yet created; building it is an implementation task.

---

## 4. Validation Engine – Rules & Error Handling

The validation engine runs continuously (or on “Validate” button) and categorises issues into **Errors** (block export) and **Warnings** (allow export but flag).

**Two stages.** *File checks* (existence, decode, duration, format, size, SHA‑256, image dimensions and colour profile) run at import and when a file changes, off the UI thread. Their results (“file facts”) are cached keyed by path + size + mtime (+ SHA‑256 once computed). *Rule evaluation* runs over metadata and cached file facts only and never reads media files; this is the stage covered by the performance target in §8. A file with no cached facts yet is shown as “checking” and blocks export until its facts are available.

### 4.1 Hard Validation Rules (Errors)

| Rule | Applies To | Rationale |
|------|------------|-----------|
| All **Required** fields (taking the plan state of §3.4 into account) must be non‑empty. | Release, Track, Contributor | DistroKid will reject otherwise. |
| If an own ISRC is supplied: normalise to 12 characters; must match `^[A-Z]{2}[A-Z0-9]{3}[0-9]{2}[0-9]{5}$`. Display form is either all three hyphens or none; mixed hyphenation is an error. | Track | Prevents malformed identifiers. |
| Own ISRC supplied while the plan does not allow it. | Track | The form cannot accept it. |
| Sum of Songwriter `writer_share` per track = 100.00 (±0.01), when the track has Songwriter credits. Publisher, Performer, Producer, Engineer and Remixer credits are excluded. | Contributor (per track) | Prevents split disputes. |
| Audio file must exist, decode, have duration > 0, and be within DistroKid’s accepted formats and size/length limits (§11, unverified). | Track | DistroKid format rules. |
| Cover art must exist, decode, be JPEG, RGB/sRGB, square (width == height) and ≥ 1000×1000 px. | Release | DistroKid artwork rule. |
| Each Songwriter credit has a legal name. | Contributor | DistroKid asks for songwriters’ real names. |
| If IPI is provided, PRO must be selected. | Contributor | IPI alone is insufficient for matching. |
| A 9‑digit IPI Name Number that fails validation is an error. An 11‑digit CAE form is not an error: it is accepted with a warning until DKM2‑D6 is decided. | Contributor | Malformed identifiers. |

There is **no UPC rule** and **no release‑date minimum** among the errors: UPC is assigned by DistroKid, and DistroKid sets no hard minimum lead time.

### 4.2 Warnings (Allow Export)

- Contributor has a legal name but no IPI/CAE.
- Publisher credit has a name but no publisher IPI.
- Track has no contributor rows (share check skipped).
- Release date is less than 21 days away: “outside Spotify editorial pitch window”. Less than 28 days: “DistroKid recommends about 4 weeks”. Both are advisory and independent of the plan; whether the product enforces a 21‑day policy as an error is DKM2‑D3.
- Cover art smaller than 3000×3000 px (DKM2‑D2 decides whether this becomes an error).
- Audio below 44.1 kHz / 16‑bit stereo (app policy, DKM2‑D4).
- Track has featured artists but the release‑level artist name does not reflect a collaboration.
- Advisory title and artist checks: “feat.”, “remix” or version text in a track title, URLs, repeated characters.
- Own ISRC fields on a plan that would assign them anyway.
- Bundled reference data older than its configured age.

### 4.3 Cross‑Field Checks

- **Release type vs. track count and duration**: per DistroKid (unverified, §11) a Single is 1–3 tracks, an EP 4–6 tracks under 30 minutes in total, an Album 7+ tracks or any release over 30 minutes. The app derives a suggested type from track count and total duration and warns when the selected Release Type differs. Warning only until HUMAN decides otherwise. The single‑track length edge (reported as 10 minutes) is low confidence and not enforced.
- **Artist name consistency**: The primary artist on each track should match the release artist unless a featured artist is explicitly listed.
- **ISRC uniqueness**: No duplicate ISRCs within a project; an optional catalog check is a future extension (§9).
- **Total album duration** within DistroKid’s limit (§11, unverified).

---

## 5. UI Design – Workflow & Screens

The UI is a **wizard‑style** interface with a persistent navigation sidebar.

### 5.1 Release Screen
- Fields: Artist/Band Name, Release Title, Release Type (dropdown), Release Date (calendar picker; disabled with the DistroKid default shown when the plan does not allow custom dates), a read‑only note “DistroKid will assign a UPC”, Label, Language, Primary/Secondary Genre, Excluded territories (optional multi‑select recording the post‑upload exclusion request, §3.1; default worldwide), target plan selector and “already released” checkbox.
- Cover Art: drag‑and‑drop area with preview and dimension, format and colour‑profile check.
- Explicit default toggle; “AI used?” yes/no, with category checkboxes (lyrics, music, all audio, part of audio) and the artist‑persona question when “all audio” is checked.

### 5.2 Tracks Screen
- A table/list of tracks with columns: `#`, Title, ISRC, Duration, Status (Valid / Errors).
- “Add Track” button opens a **Track Editor** drawer:
  - Title, Version, ISRC (with “auto‑assign” option), Audio File picker.
  - Featured Artists (chips input).
  - Explicit override.
  - Lyrics (multiline text area).
  - **Contributors sub‑table** (see 5.3).
- Drag‑to‑reorder tracks.

### 5.3 Contributor Editor (per track)
- A table where each row is a contributor:
  - Role (Songwriter / Performer / Producer / Engineer / Publisher / Remixer)
  - Legal Name
  - IPI/CAE
  - PRO (dropdown)
  - (For Publisher rows, Legal Name and IPI/CAE are the publisher’s name and IPI.)
  - Writer share % (Songwriter rows) or publisher share % (Publisher rows), numeric spinbox with 2 decimals; disabled for other roles.
- A live **Writer Share Total** indicator shows `X.XX% / 100.00%` (Songwriter rows only) and turns red if ≠ 100.
- “Add Contributor” button; “Copy from another track” option to reuse credits.

### 5.4 Review & Validation Screen
- Summary of all data with **inline error/warning badges**.
- A “Validate All” button that runs the full rule set.
- Export buttons are disabled until all **Errors** are resolved.
- A checklist of DistroKid‑specific reminders (e.g., “Register with your PRO and The MLC separately – this tool does not do that for you”).

### 5.5 Export Screen
- Choose format: **JSON (canonical manifest, §6.1)** or **CSV (human‑readable / importable)**.
- Preview the generated manifest (read‑only text view).
- “Save to file” and “Copy to clipboard” buttons.
- Optional: “Send to browser bridge” button (see Section 6.2).

---

## 6. Export Formats & Interoperability

### 6.1 Canonical JSON Manifest (Recommended)

The JSON structure mirrors the data model. The manifest is an **internal, versioned format**. Compatibility with DISTROPILOT or ReleaseBrief is *unverified* (no link, version or schema is known); until a target schema is cited and validated against, such tools are reached through an adapter (DKM2‑D8).

Contract rules (normative):
- `manifest_version` (integer, currently 1) at the top level; a JSON Schema file for each version is shipped in `docs/` and used by golden fixtures (one single, one EP, one album) in `evals/`.
- Enum wire values are lower‑case: `type` ∈ `single|ep|album`; `role` ∈ `songwriter|performer|producer|engineer|publisher|remixer`; `target_plan` ∈ `musician|musician_plus|ultimate`; `isrc_source` ∈ `user|distrokid`; `ai_disclosure.categories` ⊆ `lyrics|music|all_audio|part_of_audio`.
- `release_date` is an ISO 8601 date (`YYYY-MM-DD`), no time component. `language` is a BCP‑47 tag. `excluded_territories` are ISO 3166‑1 alpha‑2.
- Optional text has three states: key **absent** = not applicable, unavailable on the plan, or DistroKid‑assigned; `null` = user explicitly left blank; otherwise a non‑empty string. Empty strings are never emitted.
- Every track carries `primary_artist`, always emitted (equal to `release.artist` unless overridden), so the per‑track override of §3.2 is never lost. Goldens must include a track with an override.
- A track carries `isrc_source`; `isrc` is present only when `isrc_source` is `user`.
- Paths are file names relative to the project’s `media/` folder (§7) plus a SHA‑256, never absolute paths.
- `target_plan`, `already_released`, and the reference‑data asset versions are recorded.

```json
{
  "manifest_version": 1,
  "target_plan": "musician_plus",
  "already_released": false,
  "reference_data": { "genres": "1", "languages": "1", "territories": "1", "pros": "1", "plans": "1" },
  "release": {
    "release_id": "local-0001",
    "artist": "Example Artist",
    "title": "Example Album",
    "type": "album",
    "release_date": "2026-12-01",
    "label": "Example Records",
    "language": "en",
    "primary_genre": "Pop",
    "secondary_genre": "Rock",
    "cover_art": { "file": "cover.jpg", "sha256": "…" },
    "explicit": false,
    "excluded_territories": [],
    "ai_disclosure": { "ai_used": false, "categories": [] }
  },
  "tracks": [
    {
      "track_number": 1,
      "title": "First Song",
      "primary_artist": "Example Artist",
      "isrc_source": "user",
      "isrc": "USABC1234567",
      "audio": { "file": "track1.wav", "sha256": "…", "duration_seconds": 215.4 },
      "explicit": false,
      "featured_artists": ["Featured Artist"],
      "version": null,
      "lyrics": "...",
      "credits": [
        {
          "role": "songwriter",
          "legal_name": "Jane Doe",
          "ipi": "123456789",
          "pro": "ASCAP",
          "writer_share": 100.00
        }
      ]
    }
  ]
}
```

`upc` is intentionally absent (assigned by DistroKid); an optional `assigned_upc` may be added after upload.

**Why JSON?** It preserves nested credit objects and is easier to validate programmatically than CSV.

### 6.2 CSV Export (Universal)

RFC 4180, UTF‑8 (BOM policy: no BOM by default, optional for Excel), fixed column order defined in `docs/` alongside the JSON Schema, one row per track. Contributor credits and lyrics are JSON‑encoded in single columns (multi‑line lyrics are therefore quoted). A one‑row‑per‑credit variant may be generated on user preference. A “human‑readable” CSV can also be generated for manual entry: it mimics the order of the DistroKid form fields so the user can copy‑paste value by value.

### 6.3 Browser Bridge (Optional)

If the user has a form‑filling extension installed, the Qt app can expose the validated manifest via a **local HTTP endpoint** (`http://127.0.0.1:PORT/manifest`) or via `QWebChannel`. The user must still review and submit manually – no auto‑submission. The bridge is **disabled by default** and is subject to HUMAN scope decision DKM2‑D7 (§12), which also covers §6.4.

Bridge security requirements:
- ephemeral port on `127.0.0.1` only; `GET` only;
- 256‑bit per‑session random token, sent in an `Authorization` header (never in a query string); requests without it are rejected;
- no wildcard `Access-Control-Allow-Origin`; `Origin` validated against the configured extension ID;
- threat note: any local process can reach loopback, so the token is the only barrier; the manifest contains no credentials.

### 6.4 Direct WebEngine Filling (Advanced, with Caution)

Using `QtWebEngine`, the app can open `https://distrokid.com/new` in an embedded browser and inject JavaScript to set form values. This is technically feasible but **fragile** (DistroKid’s UI changes) and its ToS status is unresolved. **Whether this mode ships at all is DKM2‑D7**; until decided it is treated as out of scope per §1 and must not be implemented. If it ships, it is named “assisted entry — user submits”, requires per‑session consent, never clicks Submit, and uses an off‑the‑record `QWebEngineProfile` (no persistent cookies, cache or localStorage; cleared on close). The spec recommends the browser‑bridge approach as the primary integration path.

---

## 7. Technical Implementation Details (Qt‑Specific)

| Module | Usage |
|--------|-------|
| **Qt Core** | Data models (`QAbstractItemModel` for tracks/contributors), signals/slots for validation feedback, `QRegularExpression` for format checks. |
| **Qt Widgets** | Main window, wizard pages, tables (`QTableView` with custom delegates for share percentage), dialogs. |
| **Qt SQL** | SQLite backend for project persistence (save/load `.dkmeta` files), versioned schema migrations. |
| **Qt Gui** | `QPixmap` for cover‑art preview and dimension validation, `QFileDialog` for audio/art selection. |
| **Qt WebEngine** | (Optional) Embedded browser for guided form filling. |
| **Qt Network** | Local HTTP server (via `QTcpServer`) for browser‑extension bridge. |
| **Qt Json** | Serialisation/deserialisation of the manifest. |

**Project container.** A project is a folder containing `<name>.dkmeta` (the SQLite database) and a `media/` subfolder. Audio and cover files are copied into `media/` on import (the original is left untouched), so manifest paths are relative to `media/` and SHA‑256 values are reproducible across machines. The browser bridge serves the manifest only, never media files.

**Data Persistence:** The project database is a SQLite file with a `.dkmeta` extension. The schema includes tables `release`, `tracks`, `contributors` (global identities with internal `contributor_id`, publishers included, §3.3), `file_facts` (cached results of §4 file checks) and `track_credits` (track ↔ contributor, roles, `writer_share`, `publisher_share`). This allows undo/redo and session recovery.

**Undo/Redo:** Implemented via `QUndoStack` for field edits and list operations.

### 7.1 Technical Baseline

Proposed baseline (pending DKM2‑D9, §12): Qt 6.x LTS, C++17 or later, CMake; modules Core, Gui, Widgets, Sql (SQLite driver), Network, optional WebEngine; dynamic linking under LGPLv3 with licence texts shipped and relinkability preserved for AppImage/Flatpak; code signing and notarization for Windows/macOS; no crash reporting or telemetry; CI pins the exact Qt and compiler versions; per‑OS minimum versions as in §8. Until HUMAN confirms, implementers must not choose a toolchain beyond this proposal.

---

## 8. Non‑Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Cross‑platform** | Windows 10+, macOS 12+, Linux (AppImage/Flatpak). |
| **Offline‑first** | All validation and export functions work without internet. Browser bridge is optional. |
| **Performance** | Rule evaluation (§4, stage 2) of a 20‑track album with 10 contributors per track, over cached file facts, completes in < 200 ms. File checks run at import or file change, asynchronously, and have no fixed budget. |
| **Accessibility** | Keyboard navigation, screen‑reader labels for all form controls. |
| **Security** | The app itself stores no credentials. If assisted entry ships (DKM2‑D7), its embedded browser is off‑the‑record so no DistroKid session persists. Browser bridge requirements: §6.3. |
| **Localisation** | UI strings externalised in `.ts` files; initial release in English. |

---

## 9. Future Extensions (Out of Scope for v1.0)

- **DDEX ERN export** for label‑level distribution.
- **ISRC generator** with prefix management (if the user owns a registrant code). UPC generation is not applicable: DistroKid assigns UPCs.
- **PRO/MLC registration checklist** with deep links.
- **Catalog‑wide duplicate detection** across multiple `.dkmeta` projects.
- **Direct integration with unofficial DistroKid APIs** (via bearer token) – only if terms permit; currently discouraged because no official API exists.

---

## 10. Summary

DK‑MetaPrep is a **Qt desktop application** that acts as a metadata pre‑flight system for DistroKid. By centralising all release‑, track‑, and contributor‑level fields in one interface, enforcing hard validation rules (ISRC format, share totals, file specs), and exporting a clean JSON/CSV manifest, it eliminates the most common causes of DistroKid upload errors and royalty‑matching failures. The tool does **not** attempt to automate submission; instead, it prepares a perfect payload that can be consumed by existing form‑filling bridges or used for confident manual entry. The architecture is modular, offline‑capable, and built entirely with Qt’s standard modules, making it maintainable and cross‑platform.

---

## 11. Sources and Provenance

All rows were reported by reviewer DEEPSEEK on 2026-11-02 from search‑indexed text; the DistroKid help pages returned HTTP 403 to direct fetches. CLAUDE did not re-verify them. Every row is **unverified — re-check before release** and again at each release.

| Rule | Source (reported) | Status |
|------|-------------------|--------|
| UPC assigned by DistroKid, no custom UPC | support.distrokid.com/hc/en-us/articles/360013648913 | Required (unverified) |
| Own ISRC / custom label / custom date plan‑gated; worldwide default | …/360013648913, …/360013648113, …/52677658186003 | Required (unverified) |
| Cover art: JPEG, RGB, min 1000×1000, ideal 3000×3000 | …/360013534334 | Required / Recommended (unverified) |
| Audio formats (WAV, MP3, M4A, FLAC, AIFF, WMA; CDDA is legacy and not accepted), 24‑bit/96 kHz ceiling, 1 GB and length limits | …/360013647753 | Required (unverified) |
| No published maximum cover‑art file size | …/360013534334 | Absence of a rule (unverified); no app cap |
| Release type: Single 1–3, EP 4–6 under 30 min, Album 7+ or over 30 min | support.distrokid.com/hc/en-us/articles/55115193705875 | Recommended (unverified; 10‑minute edge low confidence) |
| Songwriter real names | …/360013545554 | Required (unverified) |
| Apple Music Writer / Performer / Production credits | help.apple.com/itc/musicstyleguide/en.lproj/itce0a71e240.html | Required by Apple (unverified) |
| Release lead time 3 weeks (Spotify) / ~4 weeks (DistroKid) | Spotify pitch guidance; …/52677658186003 | Recommended (unverified; sources vary) |
| 44.1 kHz / 16‑bit stereo audio | none | App policy |
| AI Credits step: lyrics / music / all audio / part of audio, artist‑persona follow‑up, “no AI” answer | support.distrokid.com/hc/en-us/articles/50784235803411 | Required answer (unverified, may change) |
| Excluded territories as post‑upload request | …/360013648113 | Required (unverified; DKM2‑D1) |
| DISTROPILOT / ReleaseBrief compatibility | none | Assumption — verify before release |

---

## 12. Open HUMAN Decisions (carried forward)

| ID | Decision | Origin |
|----|----------|--------|
| DKM2‑D1 | Confirm the supported plan matrix (including territory-exclusion gating, §3.1) and whether plan modelling (§3.4) is in v1 scope. | DEEPSEEK‑2, DEEPSEEK‑23 |
| DKM2‑D2 | Make 3000×3000 cover art an error rather than a warning? | DEEPSEEK‑4 |
| DKM2‑D3 | Enforce a 21‑day release lead time as an app policy (error) or keep warnings only? | DEEPSEEK‑5 |
| DKM2‑D4 | Keep 44.1 kHz / 16‑bit stereo as an app policy (warning) or an error? | DEEPSEEK‑6 |
| DKM2‑D5 | Enforce Apple Music credit groups (Writer, Performer, Production & Engineering) as errors when Apple is a target store? | DEEPSEEK‑9 |
| DKM2‑D6 | Accept 11‑digit CAE forms of IPI, and with what check rule? | DEEPSEEK‑12 |
| DKM2‑D7 | Ship the bridge (§6.3) and “Guided Fill” (§6.4) at all, given the ToS scope in §1? Record in `decisions.md`. | DEEPSEEK‑11, DEEPSEEK‑15 |
| DKM2‑D8 | Is DISTROPILOT a real target (cite version/schema) or is the manifest internal with an adapter? | DEEPSEEK‑7 |
| DKM2‑D9 | Approve the technical baseline in §7.1 (Qt 6 LTS, LGPLv3 dynamic linking, signing). | DEEPSEEK‑10 |
