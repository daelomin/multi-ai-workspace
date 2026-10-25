# HUMAN decisions — Akira

Only HUMAN-settled decisions belong in this file. Architecture choices, budget
thresholds and policy defaults are proposals: they live in `docs/03-architecture.md`
(ADR records) and `docs/13-open-decisions.md`, never here.

---

## AKIRA-D1 — Akeru is the selected primary base; the spin-off is named Akira

**Decided by:** HUMAN, 2026-10-24.
**Recorded in:** `projects/jarvis/JarvisBot/decisions.md` (same decision, original context).

**User instruction:** "ok agreed with Akeru as prime option. specify a prompt for another
Agent to specify the Akeru spin-off, which we'll call Akira. Encompass all the features and
required developments to add to Akeru to rich Akira-grade professional production".

**Decision:** Akeru (`https://github.com/opencoredev/akeru-bot`) is the foundation. The
product is **Akira**, a professional production spin-off. The authorized deliverable is a
complete, implementable specification and phased development plan, including bounded
component replacement where the inspected code justifies it.

**Consequences:**

- The option debate (O1 shim / O2 reconstruction / O3 open-source / O4 DIY) is closed.
  Akira must not re-litigate the base choice, and must not review the historical
  `projects/jarvis/JarvisBot/spec.md` as if it were the Akira specification.
- Akeru behaviour is retained wherever it is compatible with the requirements; every
  replacement is recorded with its evidence and its rebase cost.
- The round-2 consolidation remains an evidence inventory. It is not proof that any
  capability works, and it is superseded on specifics wherever this specification cites
  the pinned source directly.

---

## AKIRA-D2 — Standing no-deletion rule applies to Akira

**Decided by:** HUMAN, standing rule restated in the Akira specification handoff, 2026-10-24.

**Decision:** Never delete, trash or prune user data, bots, chats, artifacts, memories,
backups, reviews or Docker images without an explicit HUMAN message naming the items.
Deleting a Docker image always requires separate, specific approval.

**Consequences:**

- Akeru's automatic deletion of archived bots after seven days
  (`ARCHIVED_BOT_RETENTION_DAYS = 7` in `packages/contracts/src/orchestration/roster.ts`
  line 358, swept by `apps/server/src/archivedBotRetention.ts`) is disabled in the Akira
  build before any real data is imported. Verification uses static inspection or
  synthetic fixtures only.
- Akira's own lifecycle is archive-first. "Delete" in the UI means "remove from roster
  and keep restorable state" unless a HUMAN explicitly requests permanent purge of named
  items, which is a separate, audited operation (`docs/03-architecture.md` ADR-08).
- Test and cleanup instructions in this specification must never run destructive
  commands against real state. The specification's runbooks use copies and synthetic
  fixtures.

---

## AKIRA-D3 — Authorization boundary of this work

**Decided by:** HUMAN, specification handoff, 2026-10-24.

**Decision:** This work produces a specification and plan. It does not authorize
deployment, production onboarding, paid service purchase, real customer communication,
real phone calls, real WhatsApp messages or paid media jobs. Verification uses stubs,
synthetic fixtures or separately authorized test accounts.

**Consequences:** every integration in this specification is marked with its evidence
level and its verification status. Nothing here is a claim that a live vendor
integration was exercised.

---

---

## AKIRA-D4 — Target host: Linux, single node, always on

**Decided by:** HUMAN, 2026-10-25, answering the blocking host question with "yes for
default".

**Decision:** Akira targets a Linux x86_64 host running the server as a systemd user
service, single node, SQLite, available continuously enough for routines and inbound
WhatsApp webhooks. The deployment, backup, availability and capacity sections of
`docs/12-operations.md` are written for that host.

**Consequences:**

- The proposed service objectives and the single-node capacity model apply (they remain
  proposals until HUMAN sets targets).
- WhatsApp's public HTTPS origin is viable; without a public origin the channel stays
  outbound-only (`not-live`), which is a configuration state, not a redesign.
- A later move to macOS, Windows or a laptop-only host is a deployment change with
  explicit consequences (webhooks, routines, availability), not an architecture change.

---

## AKIRA-D5 — Subscription logins may be used through Akira

**Decided by:** HUMAN, 2026-10-25, answering "subscription logins yes".

**Decision:** The operator's own ChatGPT/Codex, Claude, Grok and Kimi subscription
logins **may** be connected to Akira and used for the operator's personal work. This
includes subscription routes running through Akira's own runtime. API keys remain
supported and are the fallback where a vendor forbids or does not offer subscription
use.

**Consequences:**

- Subscription routes are included in routing and cost accounting as
  `subscription-equivalent` usage, never as cash spent.
- Each route still records `transportPermission`; the default for an accepted
  subscription route is `assumed-for-personal-use`. A vendor whose terms prohibit the
  use disables that route (recorded, with the reason), not the whole class.
- It remains the operator's responsibility to comply with each vendor's terms and plan
  limits; Akira surfaces the permission status and does not represent it as a legal
  opinion.
- Consent for using these accounts is per environment; credentials stay in the secret
  store and are never exported.

---

## AKIRA-D6 — Private, internal deployment

**Decided by:** HUMAN, 2026-10-25, answering "private".

**Decision:** Akira v1 is a private, internal deployment. Builds, repositories and the
specification are not published or redistributed. Upstream MIT and third-party notices
are preserved; the upstream request not to push or publish the Akeru fork is respected.

**Consequences:**

- No public distribution or licensing/trademark review is required for v1; if that
  changes, it is a new HUMAN decision with a distribution review.
- Documentation and runbooks assume a trusted operator and a private host.
- The codebase still keeps provenance and notices clean so a later publication decision
  is not blocked by avoidable ambiguity.

---

## Not decided here

The following are **not** HUMAN decisions and must not be treated as settled by a
reviewer or an implementation agent:

- Any budget, spend cap, quality threshold, concurrency cap or approval rule.
- The exact WhatsApp Business administration scope, or the telephony/video providers.
- Whether the first production release includes desktop and mobile clients.
- The rating aggregation model, retention windows, or the identity of a delegated
  bot-admin.

These are tracked, with reversible defaults, in `docs/13-open-decisions.md`.
