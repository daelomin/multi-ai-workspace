# 12 — Security, deployment, operations and recovery runbooks

**Status:** draft v0.6 · **Normative:** `spec.md` §15, §17 · **Estimates and SLOs are proposals, not HUMAN-approved.**

Nothing in this document authorizes execution against real data. Runbooks are written to
be followed on a staging environment first; commands that delete anything are explicitly
excluded or guarded by AKIRA-D2.

---

## 1. Threat model (summary)

| Threat | Vector | Impact | Primary controls |
|---|---|---|---|
| Prompt injection | web page, email, attachment, connector output, MCP description, skill file | bot takes unintended action or leaks context | treat as data; provenance markers; approval for consequential actions; injection tests |
| Secret exfiltration | prompt, memory, artifact, export, log, sandbox | account takeover | secret store boundary; short-lived tokens; redaction; export excludes secrets; sandbox token rules |
| Tool/plugin supply chain | custom MCP, Composio app, skill script | arbitrary execution | pinned versions, review, least privilege, sandbox/allowlist, disable per connector |
| SSRF | WebFetch/fetch to internal services | internal network access | per-hop resolution and private-range rejection (Akeru's behaviour retained) |
| Cross-scope escape | room/bot/user boundary | unauthorized data access | server-side scopes; default-deny grants; tests |
| Channel spoofing | forged webhook, wrong sender | unauthorized work/response | signature verification, idempotency, sender policy |
| Runaway spend | loops, retries, paid media | cost blowout | per-task/bot caps, dedupe, approval for paid renders, kill switch |
| Destructive action | delete/purge/send/pay | data loss or harm | protected actions, explicit naming, backup-before-purge, audit |
| Host compromise | server/Linux account | full compromise | hardened host, minimal exposure, encrypted disk, separate service user |
| Data loss | disk failure, corruption, bad upgrade | lost team state | backups, snapshot-before-migrate, restore drills |

**Trust boundaries:** the host OS; the Akira server (single writer); the secret store;
provider APIs (untrusted responses); connector APIs; inbound webhooks (untrusted);
client devices (authenticated, scoped); bot output (untrusted content).

---

## 2. Service objectives (proposed, pending HUMAN)

| Objective | Proposal | Basis |
|---|---|---|
| Server availability during working hours (07:00–20:00 local) | 99% monthly | single-node, systemd restart, maintenance windows |
| Availability outside working hours | best effort | routines may run; no on-call promise |
| RPO (state) | ≤ 24 h, ≤ 1 h if continuous WAL shipping is adopted | daily verified backup + WAL optional |
| RTO | ≤ 2 h to a working server on a prepared host | restore runbook, warm spare optional |
| Max time to notice a failed channel | ≤ 15 min | health check + alert |
| Max age of unverified backup | 24 h | backup job alert |
| Restore drill cadence | quarterly | operational discipline |

These are proposals; HUMAN must approve or replace them. Until then, they are design
targets, not commitments.

---

## 3. Deployment

### 3.1 Host

- Linux x86_64, 4 vCPU, 8 GB RAM, 60–100 GB SSD (proposal; see §10 capacity).
- Dedicated non-root service user (`akira`), systemd user unit, lingering enabled.
- Disk encryption (LUKS) recommended; secrets depend on it.
- Only the reverse proxy port is public; the app port binds loopback or a private
  interface.
- Public HTTPS origin (reverse proxy) required for WhatsApp webhooks; TLS via the proxy.
- Outbound network allowed to provider/connector APIs; no inbound except the proxy.

### 3.2 Install (staging first)

```bash
# 1. Fetch the pinned Akira build (produced by CI from upstream.yaml)
# 2. Verify artifact hash and signature against the release manifest
# 3. Install to /opt/akira with a dedicated user
# 4. Create the state directory (default ~/.akira or configured base dir)
# 5. Start the systemd user unit, then check /healthz and logs
# 6. Pair the first client; complete provider logins in Settings
```

Exact commands depend on the packaging chosen in P10 (tarball + systemd unit vs container
image). The specification requires: reproducible artifact, hash verification, a
non-destructive upgrade path, and no secrets in the artifact.

### 3.3 Configuration

| Setting | Default | Notes |
|---|---|---|
| State base dir | `~/.akira` | must be on a backed-up volume |
| Server port | loopback only | proxy handles TLS |
| Public origin | unset | WhatsApp stays `not-live` until set |
| Provider accounts | none | per-bot/room route policy references them |
| Retention | keep | no automatic deletion |
| Analytics | off | opt-in only |
| Backup schedule | daily | verified weekly, drilled quarterly |
| Route policy | balanced | floors are configuration |

### 3.4 Upgrade and rollback

1. Snapshot the database and state dir (the service already snapshots before a remote
   candidate starts; retain and verify).
2. Stop the service; run forward migrations; start; check health and a scripted smoke
   turn.
3. If unhealthy: stop, restore the snapshot, restart the previous version in recovery
   quarantine (§5.3, AK-OPS-15); record the incident and the failing migration.
4. Never run a downgrade without the matching database snapshot; schema rollback is
   not assumed.

---

## 4. Secrets

| Secret | Storage | Permissions | Rotation |
|---|---|---|---|
| Provider OAuth/API credentials | `state/secrets/subscription-auth.json` | 0600 file, 0700 dir | re-login / replace key |
| Connector OAuth tokens | per-connection secret records | encrypted at rest if available | reconnect / revoke |
| Webhook signing secrets | secret store | 0600 | rotate with provider |
| Backup encryption key | separate, offline | not in the bundle | yearly or on staff change |
| Client pairing tokens | auth store, hashed | scoped, expiring | revoke device |

Rules: never in prompts/memory/artifacts/exports/logs; never in the repository; never in
environment files that are world-readable; a suspected leak is an incident (§7.6).

---

## 5. Backup

### 5.1 What must be backed up (complete restore set)

1. `state.sqlite` (events, projections, usage, actions, ratings, proposals) via
   `VACUUM INTO` or an offline copy — never a live `cp`.
2. `attachments/` and `artifacts/` (files + metadata).
3. `memory/` (bot and room Markdown, task memory).
4. `secrets/` (encrypted separately, or re-entered after restore).
5. Configuration (`settings.json`, routing policy, price tables, `upstream.yaml` + patch
   list, service unit).
6. Export bundles for templates/skills/procedures (content-addressed files).
7. Git checkpoint refs for active workspaces (`refs/t3/checkpoints`) — export the refs
   list and bundle the objects if the workspace repositories are not otherwise backed up.

Logs are optional and retained short; they are not part of restore correctness.

### 5.2 Procedure

The backup implementation follows these checked steps. This is a specification outline,
not a complete executable backup script; encryption and manifest generation are packaging
work in P10. Any command failure stops generation completion; preserve the incomplete
generation for diagnosis, never relabel a failed copy/export as an absent source.

1. Stop the service for the whole consistent snapshot; failure stops the run. Inventory
   the seven items, configured source paths and active workspace ids. Use a new generation
   (`mkdir "$GEN"`, no reuse); name its database snapshot with the same per-run timestamp.
   A timestamp collision fails, never overwrites. Record recovery point and source versions.
2. Snapshot the database with checked `VACUUM INTO` to a fresh path inside the generation.
   Copy attachments, artifacts and memory to distinct paths; settings/configuration and
   registry content likewise have their own explicit destinations. For a present tree,
   checked `rsync -a "$SOURCE/" "$DEST/"` copies into its dedicated destination, never
   a shared flattened tree. An absent tree gets a reason, not a failed rsync treated as
   success. A missing required source or unexpected missing mount makes the generation
   incomplete; it remains visible with its absent marker.
3. Encrypt secrets directly to `secrets.enc` with the separate backup key, checking success
   and decryptability in the authorized drill, or record `absent: re-enter after restore`.
   Never create plaintext secrets inside the generation.
4. Create the checkpoint destination **before** any workspace export:

   ```bash
   mkdir "$GEN/checkpoint-refs"   # checked; fresh generation only
   ```

   For each inventoried workspace id, create its own directory. Check success of
   `git -C "$W" for-each-ref refs/t3/checkpoints` writing its `.refs` list, then, if
   nonempty, `git -C "$W" bundle create "$BUNDLE" --glob='refs/t3/checkpoints/*'`.
   Verify the bundle and object/ref coverage before completion. If no refs exist, retain
   the successful empty list with `no checkpoint refs` and no bundle; a failure is never
   an empty-list result. Include the workspace repository/tree at the recovery point
   (or a verified backed-up repository reference) so the refs can be restored. With no
   active workspaces item 7 is `absent: no active workspaces`, explicitly.
5. Generate a structured `MANIFEST.json` with **exactly seven top-level item entries**,
   numbered as §5.1, even for an empty/absent source. Each entry is either
   `{item, paths, checksum}` or `{item, absent: reason}`. `paths` may list multiple
   destinations (e.g. attachments and artifacts); its checksum hashes a canonical,
   sorted inventory of relative paths, file hashes and empty-directory markers, so an
   empty present tree still has a checksum. Optional per-file `MANIFEST.sha256` detail
   does not replace these item entries and excludes manifest files from its own inventory.
   Include generation id, recovery point, secret handling, workspace export results and
   completeness status. Verify all checksums and the seven-item inventory before marking
   complete and copying/encrypting off-host. Completion is atomic; failed runs cannot
   produce a final complete manifest. Missing required items remain incomplete even
   though an absent marker records them; intentional secrets re-entry or no-workspace
   cases are valid only with the stated restore obligations.

A usable backup requires the complete manifest, verified checksums and a restore drill
within the last quarter. No deletion, prune or overwrite is part of generation completion.

**Append-only rule (AKIRA-D2, AK-OPS-11).** Each run writes a new generation; earlier
generations and dated database snapshots are preserved. Removing any generation is a
separate operation that requires a HUMAN message naming the items (same rule as purge,
§10). A source file that is absent in a later run (partial mount, interrupted restore,
named purge) does not remove its copy from earlier generations.

**Backup test (T-13).** On synthetic state: back up; remove a source file; back up again;
assert the file is still present in the earlier generation and the second generation does
not contain it. Also assert, on synthetic state holding a file with the same relative name
(`same/note.txt`) in `attachments/`, `artifacts/` and `memory/` with different contents,
that the generation holds three distinct paths and hashes; that two runs on the same day
produce two database snapshots; and that all seven items have manifest entries. T-13 also exercises a fresh
checkpoint destination, a workspace with refs, a workspace with no refs, no active
workspaces, an empty tree and a whole missing source tree (absent marker + incomplete
status for required sources); injected ref-list/bundle failures leave no complete manifest.

### 5.3 Restore

```bash
# Dedicated target; never restore over a live production state
systemctl --user stop akira-bot.service
# Place the database and files, fix ownership/permissions (0600/0700)
# Re-enter secrets, or decrypt the separately stored secret set
# Start in QUARANTINE (see below); verify health; run the restore checklist
# Release quarantine only after the recovery-interval reconciliation completes
```

**Recovery quarantine (AK-OPS-15).** A restored or rolled-back server (§3.4 step 3
included) starts with autonomous dispatch, routines, outbound channel delivery and all
external writes disabled. The original environment must be stopped or fenced (its
credentials/webhooks revoked or pointed away) before the restored one is enabled, so two
writers never act at once. Then:

1. Record the recovery point (snapshot time) and the uncertain interval (snapshot time →
   failure time).
2. For every task, routine and channel delivery that could have acted in the interval,
   **whatever its status at the recovery point** (including `paused`, `done`, `failed`
   and `cancelled` tasks, which can resume or reopen, and work created after the snapshot
   that exists only in preserved post-snapshot evidence or external state), reconcile
   against that evidence (original database/logs if recoverable) and external state
   (read-back, idempotency lookup, channel history). Preserved evidence narrows the set;
   absent evidence keeps the work quarantined. Absence from a snapshot status list is not
   a release.
3. A task whose prior effects cannot be established stays `blocked` for HUMAN
   reconciliation; it is never replayed. While quarantine is on, startup reconciliation
   (AK-TSK-14) may only mark or block: it must not dispatch, start a routine or send.
4. Only then are dispatch, routines and outbound delivery released, per task, with the
   release recorded using `quarantine.release` (docs/05 §1.5), with stored evidence for
   each task/routine/delivery. An unresolved effect prevents release.

A restore drill keeps dispatch, routines and outbound writes disabled for its whole
duration.

**Restore checklist (must all pass):** bots and personas; rooms and memberships; tasks,
attempts and checkpoints; memory files readable by the bot; skills present with support
levels; procedures/routines; usage ledger with parent links; unresolved actions still
unresolved; connector registrations present and marked for re-auth; audit trail intact;
a scripted smoke turn completes on a stub route.

**Never:** restore into the production state dir while the service runs; copy a live
SQLite file; restore a bundle without verifying its schema version; leave plaintext
secrets in a backup directory.

---

## 6. Monitoring and alerting

| Signal | Source | Alert |
|---|---|---|
| Server liveness | `/healthz`, systemd | down > 2 min |
| DB integrity | `PRAGMA integrity_check` daily | failure |
| Worker/queue backlog | orchestration metrics | backlog > threshold for 10 min |
| Provider auth health | provider probes | auth failure on the main account |
| Quota/credit | provider meters | stale > 1 h; exhausted with active tasks |
| Channel health | binding status/last success | failed/unknown delivery |
| Unresolved actions | action ledger | any `unknown` older than 15 min |
| Backup | manifest + age | missing or > 24 h |
| Disk | host metric | > 80% |
| Spend | ledger aggregation + optional caps | threshold breach (if configured) |
| Observer proposals | proposal queue | awaiting review > 7 days |

Alerts carry an owner and a runbook link; repeats update one incident. No alert for
"still working" or silence.

---

## 7. Incident runbooks (summary)

### 7.1 Provider outage

Classify the failure (network/5xx/rate limit/auth). Pause affected tasks; do not
auto-downgrade. Show the failure class and options. Resume when the provider recovers;
record the lost time and cost.

### 7.2 Credit exhaustion

Pause the task with `quota_exhausted`; list adequate routes and accounts. The operator
chooses wait, switch route, or switch account. Resume from checkpoint; record the switch
as a route decision, not an adequacy change.

### 7.3 Credential revocation

Reconnect in Settings; affected sessions stop; next turn starts a new session. No task
state is lost; attempts recorded as `failed_auth` (error class `auth_expired`).

### 7.4 Database corruption

Stop the service immediately. Do not run repair tools on the only copy. Restore the last
verified backup into a scratch directory; run integrity checks; compare recent events
from logs/exports; document what was lost (RPO). Never overwrite the corrupted file before
preserving it for forensics.

### 7.5 Duplicate or lost external action

For `unknown`: reconcile before retry; if the provider has no lookup, ask the human with
the evidence. For a confirmed duplicate: record the incident, notify the recipient if
appropriate, and add a dedupe rule. Never delete the ledger records.

### 7.6 Secret exposure

Rotate the credential at the provider, update the secret store, revoke sessions, audit
access, and check logs/exports for spread. Record the incident without reproducing the
secret in the record.

### 7.7 Runaway spend

Engage `dispatch.pause` (docs/05 §1.5), stop the offending task/bot, inspect the ledger,
add a guard, and record the incident. The kill switch preserves state. Use `dispatch.resume` only after inspection; it does
not clear quarantine or other pause scopes.

### 7.8 Disk full

Stop non-critical jobs; free space only by removing Akira-generated caches/temp files that
are explicitly safe and named (never user data or Docker images); restore from backup if
the database was damaged.

### 7.9 Deletion accident (attempted or actual)

AKIRA-D2 governs. If an accidental purge occurred: stop writes, restore from the
pre-purge backup (purge writes a backup first by design), audit the actor, and record the
incident. Do not attempt a partial manual reconstruction without the backup.

### 7.10 Unauthorized action

A bot or actor acted outside its grant, used a scope it should not have, or made an
external write that policy did not allow. Contain first: stop dispatch for the affected
bot or connector (engage the kill switch when the scope is unclear). Preserve the event,
action-ledger and audit records and the affected artifact hashes; do not edit or delete
them. Revoke the credential or grant that allowed it. Reconcile any `dispatched` or
`unknown` external effect before dispatch restarts (§7.5). Notify the operator, record
the incident (actor, grant, action ids, cause) and review the grant that was too wide
(AK-CON-08). Resume only by explicit operator release.

---

## 8. Migration runbook (existing team)

1. **Intake.** Export what exists: names, roles, room membership, routine schedule,
   shared page content if available. Everything else is marked unknown.
2. **Templates.** Map each name/role to a library template. No role → general assistant
   with a note.
3. **Personas.** Generate drafts from role + any supplied text; mark every gap
   `needs-human-review`; never present a draft as the original instructions.
4. **Rooms.** Recreate the four rooms with membership; set routing rules (lead/mention),
   topics and policies.
5. **Routines.** Recreate the Weekly bot scorecard as a procedure draft + schedule; require
   approval before enabling.
6. **Shared pages.** Import content if a bundle exists; otherwise create a board item
   linking the original source and a task to rebuild it. Do not fabricate page content.
7. **Providers/connectors.** List each required service; re-authenticate; mark
   `unverified` until the first successful real read.
8. **Dry run.** Import into staging; run the T-11 restore checklist; have a HUMAN review
   every draft persona and room rule.
9. **Cutover.** Keep the old workspace read-only until the new team passes a smoke week;
   no deletion of the old data (AKIRA-D2).
10. **Post-cutover.** Update the checklist; record what was not imported.

---

## 9. Capacity model (proposal)

| Dimension | Assumption | Single-node implication |
|---|---|---|
| Bots | 10–30 | fine |
| Humans | 2–10 | fine |
| Rooms | 4–20 | fine |
| Concurrent active tasks | 3–10 typical, 30 peak | provider rate limits dominate |
| Turns/day | 200–2,000 | SQLite writes fine; WAL + checkpoint tuning |
| Events/day | 10k–100k | event table growth; archival policy needed |
| Tokens/day | 2M–20M | provider cost, not host CPU |
| Connector calls/day | 100–2,000 | rate limits per service |
| Media jobs/month | 20–200 images, 5–50 videos | external cost/queue, not host |
| Storage/month | 5–50 GB artifacts | plan backup size accordingly |

Breaks at: >50 concurrent tasks, multi-host requirement, >100k events/day sustained, or
restore time above RTO. Those are ADR-10 migration triggers.

**Cost ranges (illustrative placeholders, not quotes; verify before budgeting).** Small
VPS: €10–40/month. Block storage/backups: €5–25/month. Domain/TLS: €0–20/year. Inference,
telephony, messaging and media are usage-based and must be taken from the ledger and
current vendor prices (`docs/09`), not from this table. No vendor quote was obtained for
this draft.

---

## 10. Retention and deletion policy (AKIRA-D2)

| Data | Default | Configurable |
|---|---|---|
| Bots (archived) | keep indefinitely | archive only; purge by explicit named request |
| Chats, tasks, artifacts | keep | archive/export; no auto-delete |
| Memory | keep | archive; no auto-delete |
| Usage/audit ledger | keep | export; no auto-delete |
| Logs | 30–90 days (proposal) | retention setting; logs excluded from restore correctness |
| Backups | 30–90 days (proposal) | rotation of backup files is a HUMAN-named operation |
| Temp/export scratch | 7 days | safe to clean, named by the system, never user data |

Purge procedure: `purge.request` with explicit ids → verify ids → write and verify a
backup → require `destructive` scope → execute → audit (actor, ids, backup id, time).
There is no timer, no wildcard, no "clean up all".

---

## 11. Testing and staging

- Staging uses the same artifacts and a synthetic fixture home; no production credentials.
- Test providers are stubs with recorded dialects; live tests use test accounts only.
- A restore drill runs quarterly into a fresh directory and is recorded in the operations
  log with the checklist results.
- CI runs: contract, decider, adapter, integration and E2E stub suites; lint and
  typecheck; packaging smoke.

---

## 12. Compliance and data handling notes

- Provider terms and data-retention policies are per vendor. Subscription routes are
  permitted for the operator's personal work (AKIRA-D5) and each route records its
  permission status; a route whose vendor terms forbid the use is disabled with the
  reason recorded. API keys remain the fallback.
- Recording phone calls and processing WhatsApp conversations carry consent and retention
  obligations; the telephony adapter requires a policy configuration and refuses to
  record when unset.
- Customer data in memory/artifacts follows the same no-delete policy; export and access
  are scoped and audited.
- Akira's own analytics are off by default and, when on, contain no content, ids beyond
  the fixed schema, or credentials.
