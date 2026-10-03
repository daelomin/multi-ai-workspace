# Changelog

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `docs/data_sources.md`, `docs/README.md`, `docs/RISKS.md`, `.env.example`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-4 draft — `docs/data_sources.md` with the A11 operator map, four Phase 0 source sheets (DIR events, DIR traffic state, Bison Futé restricted action b and action c), VINCI Autoroutes direct status, deferred sources, Alert-C direction conventions and a GDPR proposal. Key findings: the A11 is fully concessioned (Cofiroute + ASF), so its live data needs the Bison Futé restricted portal; SCAs may offer volumes only; feeds are DATEX II 2.2.2. Added restricted-portal credential names to `.env.example`, the file to `docs/README.md`, and one new risk to `docs/RISKS.md`. TODO → v2.10, P0-4 `[~]`. Claimed `docs/README.md`, `docs/RISKS.md`, `.env.example`, `TODO.md` (`owner=CLAUDE`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN: request restricted access (email in the file), verify licence and GDPR conclusions, then record them in `DECISIONS.md`. Open checks marked ⚠ in the file (bypass operator, SCA speed availability, exact open-directory paths, 2.2.2 element names).  
**Verification:** Every fact cites a source checked on 2026-10-03; unverified items marked ⚠. Not ticked: needs HUMAN review.
**Files:** `agents/CLAUDE.md`, `CHANGELOG.md`  
**Change:** Added CLAUDE's role, working rules and ordered P0 task queue to `agents/CLAUDE.md` (P0-4 → P0-7 LICENSE text → P0-13 → P0-14), keeping the existing instructions. CLAUDE does not self-tick: its tasks need HUMAN review. Replaces PR #7, which predated CURSOR's completed queue.  
**Remaining:** CLAUDE starts P0-4.  
**Verification:** Queue matches the CLAUDE owner fields in `TODO.md` v2.9.
**Files:** `.github/workflows/gitleaks.yml`, `CHANGELOG.md`  
**Change:** P0-6 leftover — added the gitleaks GitHub Actions workflow CURSOR could not push (no `workflow` scope): runs on pull requests and on pushes to `main`, full history checkout, `gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`. Matches CURSOR's intended content; adds the push-to-`main` trigger.  
**Remaining:** HUMAN to confirm the first run passes, then tick P0-6.  
**Verification:** YAML written; not yet run on GitHub.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/RISKS.md`, `docs/README.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-11 — created `docs/RISKS.md` with required columns; filled only from risks already in `TODO.md`/`DECISIONS.md` (cited); Likelihood/Impact = `?`. Updated `docs/README.md` index. Ticked P0-11; TODO → v2.9. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN reviews Likelihood/Impact. **CURSOR queue empty** — no further tasks in `agents/CURSOR.md` until HUMAN assigns new work in `TODO.md`. Open leftover: P0-6 Actions workflow (needs `workflow` scope).  
**Verification:** No invented risks; no Likelihood/Impact values guessed.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/README.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-10 — added `docs/README.md` index (one line per existing file: `SPEC_PHASES.md`, `phase0_go_no_go.md`). Ticked P0-10; TODO → v2.8. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** Next CURSOR queue item after merge: P0-11 (`docs/RISKS.md`).  
**Verification:** Only existing `docs/` files listed; no invented doc paths as present.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `CONTRIBUTING.md`, `.env.example`, `.pre-commit-config.yaml`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-6 (partial) — credential policy in `CONTRIBUTING.md`; `.env.example` header only; gitleaks `.pre-commit-config.yaml` (rev v8.24.2); confirmed `.env` in `.gitignore`. TODO → v2.7; P0-6 left `[~]`. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN must add `.github/workflows/gitleaks.yml` (push blocked: OAuth App lacks `workflow` scope) — intended content: `on: pull_request`, `actions/checkout@v4` with `fetch-depth: 0`, `gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`. Then tick P0-6. P0-4/P0-13 add `.env.example` variables later. Next queue items P0-10/P0-11 wait on whether HUMAN treats this partial as enough to proceed.  
**Verification:** Policy text matches TODO; `.env` ignored; workflow file intentionally omitted from the push.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/phase0_go_no_go.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-8 — wrote `docs/phase0_go_no_go.md` with the TODO checklist items (unticked) plus empty HUMAN sign-off line. Ticked P0-8 write step only; TODO → v2.6. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN fills/signs checklist when gate criteria exist. Next CURSOR queue item after merge: P0-6.  
**Verification:** Checklist wording matches P0-8; no sub-boxes ticked.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/SPEC_PHASES.md`, `SPEC_PHASES.md`, `MASTER.md`, `README.md`, `DECISIONS.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-3 — `git mv` `SPEC_PHASES.md` → `docs/SPEC_PHASES.md`; root stub redirect; updated links in `MASTER.md`, `README.md`, `DECISIONS.md`. Ticked P0-3; TODO → v2.5. Claimed shared docs (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** Next CURSOR queue item after merge: P0-8 (GO/NO-GO checklist).  
**Verification:** Spec content at `docs/SPEC_PHASES.md`; root stub points there; older CHANGELOG entries left unchanged.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `DECISIONS.md`, `MASTER.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-1 + P0-2 + P0-7 intent ADR — recorded D1–D11 as accepted ADRs in `DECISIONS.md` (D1 title and freeze sentence; D2 `uv` migration note; D3 licence intent). Marked prior 2026-10-02 stack/A11 ADRs superseded. Aligned `MASTER.md` (freeze sentence; removed proposed stack/axis and open uv/poetry question). Ticked P0-1, P0-2; P0-7 left `[~]` with intent ADR sub-item done. TODO → v2.4. Claimed `DECISIONS.md`/`MASTER.md`/`TODO.md` (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** CLAUDE for P0-7 LICENSE text/scope; HUMAN sign-off on P0-7. Next CURSOR queue item after merge: P0-3 (`docs/` move).  
**Verification:** Freeze sentence present in both files; no `LICENSE` file created; CURSOR-owned boxes only ticked.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `agents/CURSOR.md`, `CHANGELOG.md`  
**Change:** HUMAN decision: CURSOR ticks its own tasks in `TODO.md` when it completes them; HUMAN reviews afterwards. Status legend in `TODO.md` (v2.3) and `agents/CURSOR.md` updated accordingly (owner-only ticks, version bump per tick, never sign-offs). P0-5 ticked.  
**Remaining:** HUMAN review of P0-5 when convenient.  
**Verification:** Rule text consistent across `TODO.md` and `agents/CURSOR.md`.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `agents/CURSOR.md`, `CHANGELOG.md`  
**Change:** Added instruction file for CURSOR (Cursor Auto): role limits, git and changelog rules, files reserved for other owners, and its ordered P0 task queue (P0-1/P0-2/P0-7 intent ADR → P0-3 → P0-8 checklist → P0-6 → P0-10 → P0-11). Task content stays in `TODO.md`.  
**Remaining:** HUMAN to review P0-5 (PR #3). No instruction file exists yet for GROK.  
**Verification:** Queue matches the CURSOR owner fields in `TODO.md` v2.2.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `CONTRIBUTING.md`, `CHANGELOG.md`  
**Change:** P0-5 — added status rule, single-writer protocol (claim/release via `CHANGELOG.md` with `owner` + `started_at`), and human-approval rule to `CONTRIBUTING.md`. Identities CURSOR and GROK were already present. Claimed `CONTRIBUTING.md` (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN review of P0-5 (do not tick until verified). Next: P0-12 GitHub rendering check; other P0-gate items.  
**Verification:** Wording matches TODO.md P0-5; TODO.md left unticked for HUMAN.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.2. The v2.0 (D11) and v2.1 (P0 owners) commits were pushed after PR #1 was merged, so they were missing from `main`; rebased onto `main` and re-submitted. P0-5 identities sub-task marked done (HUMAN added `CURSOR` and `GROK` to `CONTRIBUTING.md` in 3af0482).  
**Remaining:** Rest of P0-5 (status rule, single-writer protocol, human-approval rule) for CURSOR.  
**Verification:** `TODO.md` on this branch reads v2.2; identity list checked in `CONTRIBUTING.md`.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.1 — HUMAN assigned owners to every P0 item (P0-9 done): CURSOR (Auto) for well-specified edits (P0-1, P0-2, P0-3, P0-5, P0-6, P0-7 ADR, P0-8 checklist, P0-10, P0-11); CLAUDE (Opus 5.5) for P0-4 research, P0-7 LICENSE text, and new items P0-13 (dev scaffold) and P0-14 (smoke test); HUMAN for P0-12 and all sign-offs.  
**Remaining:** CURSOR identity is not yet in `CONTRIBUTING.md` (added by P0-5). HUMAN still to fill cost envelope and metric thresholds. Next: P0-12 (HUMAN), then CLAUDE starts P0-4.  
**Verification:** Document only.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.0 — HUMAN resolved D11: source corrections are appended as revisions (key `(site_id, source, source_ts, source_version)`, `traffic_measure_current` view feeds aggregates). No open decisions remain in the TODO.  
**Remaining:** HUMAN to assign P0 owners (P0-9), fill cost envelope and metric thresholds. D11 to be recorded in `DECISIONS.md` alongside the other ADRs.  
**Verification:** Document only.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** Replaced the task list with the consolidated multi-agent review TODO v1.1 (Claude, Gemini/previous assistant, Grok, ChatGPT, DeepSeek). Decisions D1–D10 resolved by HUMAN on 2026-10-03; D11 (source corrections) open. P0 split into gate/hygiene. Previous phase work queue and agent-assignment table preserved verbatim in a dedicated section.  
**Remaining:** HUMAN to decide D11, assign owners to P0 items (P0-9), fill cost envelope and metric thresholds. Next execution step: P0-12 (check GitHub rendering of `CONTRIBUTING.md` / `CHANGELOG.md`).  
**Verification:** Document only; no decision recorded in `DECISIONS.md` yet (that is P0-1/P0-2/P0-7).

## 2026-10-02
**Agent:** CLAUDE  
**Files:** `SPEC_PHASES.md`, `MASTER.md`, `TODO.md`, `CHANGELOG.md`, `README.md`, `DECISIONS.md`  
**Change:** Ingested plateforme nationale de trafic routier spec v1.0 (phases 0–7). Canonical brief and Phase 0 task queue populated.  
**Remaining:** Fill `docs/data_sources.md`; scaffold `dev/`; smoke test DATEX factice; human GO/NO-GO phase 0.  
**Verification:** Documents written; no runtime/env verified yet.

## YYYY-MM-DD
**Agent:** HUMAN  
**Files:**  
**Change:** Workspace initialized.  
**Remaining:** Define project.  
**Verification:** Not applicable.
