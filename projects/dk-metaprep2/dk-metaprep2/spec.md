version = v0.1 

Below is a detailed technical specification for a **Qt-based desktop application** designed to prepare, validate, and export a 100% DistroKid‑compliant metadata package. The tool does not attempt to bypass DistroKid’s lack of a public API; instead, it focuses on **eliminating metadata errors** by providing a single interface for all required and recommended fields, enforcing strict validation, and exporting a manifest that can be used with existing form‑filling bridges (e.g., DISTROPILOT, ReleaseBrief) or for manual entry with confidence.

---

## 1. Purpose & Scope

The application (“DK‑MetaPrep”) allows an artist, manager, or label to:

- Define a release (single, EP, album) with all DistroKid‑required fields.
- Define each track with its own metadata, including identifiers and contributor credits.
- Validate every field against DistroKid’s rules (formats, lengths, required‑ness).
- Export a **canonical manifest** in CSV and/or JSON that maps 1:1 to the DistroKid upload form fields.
- Optionally push the manifest to a browser‑based form‑filling extension via a local bridge, or use an embedded WebEngine view to assist manual filling (with user supervision).

**Out of scope:** automated submission without user review, bypassing CAPTCHAs, or any action that violates DistroKid’s terms of service.

---

## 2. Architecture Overview

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| **UI** | Qt Widgets (or Qt Quick Controls 2) | Multi‑page wizard: Release → Tracks → Contributors → Review → Export |
| **Data Model** | Qt Core (`QAbstractItemModel` for tracks and contributors) + SQLite (via `QtSql`) | Persist projects locally, support undo/redo, session recovery |
| **Validation Engine** | Custom C++ classes + `QRegularExpression` | Field‑level and cross‑field validation |
| **Exporters** | `QJsonDocument`, `QTextStream` (CSV) | Generate DISTROPILOT‑compatible JSON, generic CSV, and a human‑readable “upload sheet” |
| **Bridge (optional)** | `QtWebEngine` + `QWebChannel` or local HTTP server | Expose the validated manifest to a browser extension (e.g., via `localhost` endpoint) or inject data into the DistroKid page under user control |

---

## 3. Data Schema – Fields & Mapping to DistroKid

The schema is split into three levels: **Release**, **Track**, and **Contributor**. Each field is annotated with its DistroKid requirement status (Required, Strongly Recommended, Optional) and validation rules.

### 3.1 Release‑Level Fields

| Field | DistroKid Status | Type | Validation / Notes | Maps to DistroKid Form |
|-------|------------------|------|-------------------|------------------------|
| **Artist / Band Name** | Required | String | No spammy text; consistent with track credits. | “Artist/Band Name” |
| **Release Title** | Required | String | Exact title, including version info if applicable. | “Album Title” |
| **Release Type** | Required | Enum (Single, EP, Album) | Determines track‑count expectations. | “Release Type” |
| **Release Date** | Required | Date | At least 7 days in the future for playlist pitching; ≥ 3 weeks recommended. | “Release Date” |
| **UPC** | Required (or auto‑generated) | String (12 digits) | EAN‑13 compatible; must be unique if supplied. | “UPC” |
| **Label Name** | Required | String | Can be artist name if self‑released. | “Record Label” |
| **Language** | Required | Enum / String | Primary language of the release. | “Language” |
| **Primary Genre** | Required | Enum | From DistroKid’s genre list. | “Primary Genre” |
| **Secondary Genre** | Optional | Enum | Optional second genre. | “Secondary Genre” |
| **Cover Art File** | Required | File path | Square (1:1), ≥ 3000×3000 px, JPEG/PNG, sRGB. | “Album Artwork” |
| **Explicit Flag (release‑level default)** | Required | Boolean | Can be overridden per track. | “Explicit Content” |
| **Territories** | Required (default: worldwide) | List of country codes | Availability windows. | “Territories” |
| **AI Disclosure** | Optional (newer field) | Boolean / String | If AI‑generated content is involved. | “AI Disclosure” |

**Required release‑level fields per DistroKid metadata guidelines:** UPC, release title, release type, and release date.

### 3.2 Track‑Level Fields

| Field | DistroKid Status | Type | Validation / Notes | Maps to DistroKid Form |
|-------|------------------|------|-------------------|------------------------|
| **Track Title** | Required | String | No version info or featured artists in title (use separate fields). | “Song Title” |
| **ISRC** | Required (or auto‑generated) | String (12 chars, format CC‑XXX‑YY‑NNNNN) | Strongly recommended to supply if you have an existing catalog; auto‑assignment risks fragmented records. | “ISRC” |
| **Primary Artist** | Required (inherited from release, but can override) | String | Must match release artist unless it’s a collaboration. | “Primary Artist” |
| **Featured Artists** | Optional | List of strings | Comma‑separated in UI; exported as array. | “Featured Artists” |
| **Audio File** | Required | File path | WAV or FLAC, 44.1 kHz / 16‑bit minimum, stereo. | “Audio File” |
| **Explicit Flag** | Required | Boolean | Per‑track override of release default. | “Explicit” |
| **Version / Remix Info** | Optional | String | E.g., “Radio Edit”, “Remix”. | “Version” |
| **Producer(s)** | Strongly Recommended | List of contributor IDs | Links to contributor records. | “Producer” |
| **Remixer** | Optional (for remixes) | Contributor ID | Only if applicable. | “Remixer” |
| **Lyrics** | Optional | Text (multiline) | Can be pasted or loaded from file. | “Lyrics” |
| **Track Number** | Auto‑generated | Integer | Derived from order in UI. | Implicit |

**Required track‑level fields:** track title, ISRC, primary artist name, and audio file meeting format rules.

### 3.3 Contributor‑Level Fields (Songwriters & Publishers)

DistroKid accepts detailed songwriter and publisher fields, but their payment utility depends on accurate identifiers. The tool should therefore treat contributor data as **strongly recommended** and validate it rigorously.

| Field | Status | Type | Validation / Notes |
|-------|--------|------|-------------------|
| **Legal Name** | Strongly Recommended | String | First and last name exactly as registered with PRO. |
| **Role** | Required for each contributor | Enum (Songwriter, Producer, Publisher, Remixer, etc.) | Determines which fields are relevant. |
| **IPI / CAE Number** | Strongly Recommended | String (9–11 digits) | If supplied, validate basic length. |
| **PRO Affiliation** | Strongly Recommended | Enum (ASCAP, BMI, PRS, GEMA, SACEM, etc.) | Required if IPI is provided. |
| **Publisher Name** | Strongly Recommended (for publishers) | String | If the writer is signed. |
| **Publisher IPI** | Strongly Recommended (for publishers) | String | Same format as writer IPI. |
| **Share Percentage** | Required if multiple contributors | Decimal (0–100, 2 decimal places) | Sum of all writer shares per track must equal 100.00%. |
| **Signed Date** | Optional | Date | For split sheets. |
| **Contact Email** | Optional | Email | For internal records. |

**Key guideline:** Supplying names without IPIs creates noise; the tool should warn when a contributor has a name but no IPI, and when publisher fields are partially filled. **Share percentages must sum to 100.00% per track** – this is a hard validation rule.

---

## 4. Validation Engine – Rules & Error Handling

The validation engine runs continuously (or on “Validate” button) and categorises issues into **Errors** (block export) and **Warnings** (allow export but flag).

### 4.1 Hard Validation Rules (Errors)

| Rule | Applies To | Rationale |
|------|------------|-----------|
| All **Required** fields must be non‑empty. | Release, Track, Contributor | DistroKid will reject otherwise. |
| ISRC must match `^[A-Z]{2}-?[A-Z0-9]{3}-?[0-9]{2}-?[0-9]{5}$` (hyphens optional). | Track | Prevents malformed identifiers. |
| UPC must be 12 digits (EAN‑13 compatible). | Release | Retailer systems require valid product codes. |
| Release Date must be ≥ today + 7 days (warning if < 14 days). | Release | Playlist pitching window. |
| Sum of writer shares per track = 100.00% (±0.01). | Contributor (per track) | Prevents split disputes. |
| Audio file must be WAV or FLAC, sample rate ≥ 44.1 kHz, bit depth ≥ 16. | Track | DistroKid format rules. |
| Cover art must be square (width == height) and ≥ 640×640 px. | Release | Platform requirement. |
| If IPI is provided, PRO must be selected. | Contributor | IPI alone is insufficient for matching. |
| If Publisher Name is provided, Publisher IPI should be provided (warning if missing). | Contributor | Incomplete publisher data causes payment delays. |

### 4.2 Warnings (Allow Export)

- Contributor has a legal name but no IPI/CAE.
- Contributor has a publisher name but no publisher IPI.
- Release date is between 7 and 13 days away (still possible but tight for playlist pitching).
- Track has featured artists but the release‑level artist name does not reflect a collaboration.
- Explicit flag is set to “true” but no lyrics are provided (optional but helpful).

### 4.3 Cross‑Field Checks

- **Release type vs. track count**: A “Single” should have 1 track; an “EP” typically 3–6; an “Album” 7+. Warn if inconsistent.
- **Artist name consistency**: The primary artist on each track should match the release artist unless a featured artist is explicitly listed.
- **ISRC uniqueness**: No duplicate ISRCs within a release (and optionally against a local catalog database).

---

## 5. UI Design – Workflow & Screens

The UI is a **wizard‑style** interface with a persistent navigation sidebar.

### 5.1 Release Screen
- Fields: Artist/Band Name, Release Title, Release Type (dropdown), Release Date (calendar picker), UPC (with “auto‑generate” checkbox that leaves field blank for DistroKid to assign), Label, Language, Primary/Secondary Genre, Territories (multi‑select).
- Cover Art: drag‑and‑drop area with preview and dimension check.
- Explicit default toggle and AI disclosure checkbox.

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
  - Role (Songwriter / Producer / Publisher / Remixer)
  - Legal Name
  - IPI/CAE
  - PRO (dropdown)
  - Publisher Name / Publisher IPI (enabled only for publisher rows)
  - Share % (numeric spinbox with 2 decimals)
- A live **Share Total** indicator shows `X.XX% / 100.00%` and turns red if ≠ 100.
- “Add Contributor” button; “Copy from another track” option to reuse credits.

### 5.4 Review & Validation Screen
- Summary of all data with **inline error/warning badges**.
- A “Validate All” button that runs the full rule set.
- Export buttons are disabled until all **Errors** are resolved.
- A checklist of DistroKid‑specific reminders (e.g., “Register with your PRO and The MLC separately – this tool does not do that for you”).

### 5.5 Export Screen
- Choose format: **JSON (DISTROPILOT‑compatible)** or **CSV (human‑readable / importable)**.
- Preview the generated manifest (read‑only text view).
- “Save to file” and “Copy to clipboard” buttons.
- Optional: “Send to browser bridge” button (see Section 6.2).

---

## 6. Export Formats & Interoperability

### 6.1 Canonical JSON Manifest (Recommended)

The JSON structure should mirror the data model and be directly importable by **DISTROPILOT**, which already supports JSON manifests for DistroKid form filling.

```json
{
  "release": {
    "artist": "Example Artist",
    "title": "Example Album",
    "type": "album",
    "release_date": "2026-12-01",
    "upc": "012345678905",
    "label": "Example Records",
    "language": "en",
    "primary_genre": "Pop",
    "secondary_genre": "Rock",
    "cover_art_path": "/path/to/cover.jpg",
    "explicit": false,
    "territories": ["US", "GB", "DE", "FR"],
    "ai_disclosure": false
  },
  "tracks": [
    {
      "track_number": 1,
      "title": "First Song",
      "isrc": "USABC1234567",
      "audio_path": "/path/to/track1.wav",
      "explicit": false,
      "featured_artists": ["Featured Artist"],
      "version": "",
      "lyrics": "...",
      "contributors": [
        {
          "role": "songwriter",
          "legal_name": "Jane Doe",
          "ipi": "123456789",
          "pro": "ASCAP",
          "share": 100.00
        }
      ]
    }
  ]
}
```

**Why JSON?** It preserves nested contributor objects and is easier to validate programmatically than CSV.

### 6.2 CSV Export (Universal)

A flat CSV with one row per track. Contributor data is either denormalised (one row per contributor per track) or serialised as a JSON string in a single column, depending on user preference. A “human‑readable” CSV can also be generated for manual entry: it mimics the order of the DistroKid form fields so the user can copy‑paste value by value.

### 6.3 Browser Bridge (Optional)

If the user has a form‑filling extension installed, the Qt app can expose the validated manifest via a **local HTTP endpoint** (`http://127.0.0.1:PORT/manifest`) or via `QWebChannel`. The extension polls or receives the manifest and fills the DistroKid form fields automatically. The user must still review and submit manually – no auto‑submission.

### 6.4 Direct WebEngine Filling (Advanced, with Caution)

Using `QtWebEngine`, the app can open `https://distrokid.com/new` in an embedded browser and inject JavaScript to set form values. This is technically feasible but **fragile** (DistroKid’s UI changes) and may violate terms if used to automate submission. It should be offered only as a **“Guided Fill”** mode where the user watches the fields populate and clicks “Submit” themselves. The spec recommends the browser‑bridge approach as the primary integration path.

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

**Data Persistence:** Projects are stored as SQLite databases with a `.dkmeta` extension. The schema includes tables `release`, `tracks`, `contributors`, and `track_contributors` (many‑to‑many). This allows undo/redo and session recovery.

**Undo/Redo:** Implemented via `QUndoStack` for field edits and list operations.

---

## 8. Non‑Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Cross‑platform** | Windows 10+, macOS 12+, Linux (AppImage/Flatpak). |
| **Offline‑first** | All validation and export functions work without internet. Browser bridge is optional. |
| **Performance** | Validation of a 20‑track album with 10 contributors per track completes in < 200 ms. |
| **Accessibility** | Keyboard navigation, screen‑reader labels for all form controls. |
| **Security** | No credentials stored; browser bridge uses a random token and binds only to `127.0.0.1`. |
| **Localisation** | UI strings externalised in `.ts` files; initial release in English. |

---

## 9. Future Extensions (Out of Scope for v1.0)

- **DDEX ERN export** for label‑level distribution.
- **ISRC/UPC generator** with prefix management (if the user owns a registrant code).
- **PRO/MLC registration checklist** with deep links.
- **Catalog‑wide duplicate detection** across multiple `.dkmeta` projects.
- **Direct integration with unofficial DistroKid APIs** (via bearer token) – only if terms permit; currently discouraged because no official API exists.

---

## 10. Summary

DK‑MetaPrep is a **Qt desktop application** that acts as a metadata pre‑flight system for DistroKid. By centralising all release‑, track‑, and contributor‑level fields in one interface, enforcing hard validation rules (ISRC format, UPC length, share totals, file specs), and exporting a clean JSON/CSV manifest, it eliminates the most common causes of DistroKid upload errors and royalty‑matching failures. The tool does **not** attempt to automate submission; instead, it prepares a perfect payload that can be consumed by existing form‑filling bridges or used for confident manual entry. The architecture is modular, offline‑capable, and built entirely with Qt’s standard modules, making it maintainable and cross‑platform.
