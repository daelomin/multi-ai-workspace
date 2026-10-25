# 02 — Akeru baseline: inspected source, reuse and gap matrix

**Status:** Final specification v0.7 · **Revision inspected:** `524eb68a293c4b6a38acf722ab4232cfe5e22625` (2026-10-23T21:06:41Z), which was also the remote `HEAD` on 2026-10-24.
**Method:** source tarball downloaded from `codeload.github.com/opencoredev/akeru-bot` at that SHA and inspected statically. No install, build, test, login, connector, archive, delete or paid call was performed. Every `V` claim below is a file/symbol read in that tree, not a reproduced behaviour.

---

## 1. Repository facts and provenance

| Fact | Value | Evidence |
|---|---|---|
| Project | Akeru Bot — "open-source, self-hosted alternative to Grok Bot", independent fork of T3 Code | `README.md` (D) |
| License | MIT, `Copyright (c) 2026 T3 Tools Inc.` | `LICENSE` (V) |
| Third-party | Mastra Code auth/provider code adapted under Apache-2.0 + Mastra Code terms; Claude Agent SDK terms; Pierre, Bluesky, Expo, Khroma, Beautiful UI notices | `THIRD_PARTY_NOTICES.md`, `legal/licenses/*` (V) |
| Mastra terms | Content outside `ee/` directories is Apache-2.0; `ee/` has separate terms | `legal/licenses/Mastra-Code.txt` (V) |
| Distribution request | "Do not push or publish this fork unless Leo asks." | `README.md` line 11 (V) |
| Activity at pin | 106 stars, 10 forks, 70 open issues, repo created 2026-08-27, pushed 2026-10-23; latest release v0.2.1 (2026-10-01) | GitHub API, 2026-10-24 (V) |
| Size | 428,638 lines of `.ts`/`.tsx` under `apps/` + `packages/` | `wc -l` on the pinned tree (V) |
| Node | Server install: `^22.16 \|\| ^23.11 \|\| >=24.10`; contributor setup Node `^24.13.1` | `docs/user/install.md`, `README.md` (D) |
| Runtime | `npx akeru-bot@latest`; systemd user unit `akeru-bot.service` on Linux | `docs/user/background-service.md` (D) |

**Assessment.** MIT is compatible with a private production spin-off. The parts Akira
must preserve are the MIT notice and the third-party notices; if Akira ever distributes
binaries, the Apache-2.0 and vendor terms for Mastra-derived code and the Claude Agent SDK
need a distribution review. The "do not publish" note is a maintainer request, not a
license term, but it is binding on the working relationship: Akira defaults to a private,
internal deployment (AKIRA-D6). The repository is young and active; the pinned
revision is a snapshot, and every Akira patch must be rebased deliberately.

**Naming/trademark.** Akira must not present itself as Akeru, T3 Code, Grok, xAI or
Cursor. It keeps upstream copyright notices and credits.

---

## 2. How the inspected system is built

| Layer | Mechanism | Source |
|---|---|---|
| Contract | Effect Schema types for commands, events, read model, RPC, settings | `packages/contracts/src/**` (V) |
| Orchestration | Clients send typed WebSocket requests → **commands** → a pure **decider** emits persisted **events** → a **projector** derives the read model | `apps/server/src/orchestration/{decider,projector}.ts`, `core` services (V); `AGENTS.md` §How it works (D) |
| Dispatch | `OrchestrationEngine` persists commands/events; reactors perform side effects; a receipt bus reports milestones | `orchestration/Services/OrchestrationEngine.ts`, `RuntimeReceiptBus.ts` (V) |
| Provider control | `ProviderCommandReactor` starts turns; `AgentController` is the single driver of provider runtimes; `ProviderRuntimeIngestion` normalizes runtime events | `orchestration/Services/ProviderCommandReactor.ts`, `provider/Layers/AgentController.ts`, `ProviderRuntimeIngestion.ts` (V) |
| Providers | Seven built-in drivers: Codex, Claude, Grok, Kimi, OpenCode, OpenCode Go, Custom OpenAI-compatible | `provider/builtInDrivers.ts`; `docs/internals/providers.md` §Built-in drivers (V/D) |
| Sessions | `ProviderSessionDirectory` + adapter registry; provider session ids are metadata, not the conversation record | `provider/Services/ProviderSessionDirectory.ts` (V) |
| Conversation truth | Event store + projection; Mastra observational memory stores provider-bound messages per thread for context; bot memory is Markdown | `orchestration`, `provider/mastra/AkeruMemory.ts`, `BotMemoryStore` (V) |
| Checkpoints | Hidden git refs (`refs/t3/checkpoints`) captured per turn; capture/restore/diff | `checkpointing/{CheckpointStore,Utils}.ts` (V) |
| Delegation | Child thread with `parentThreadId`/`parentDelegationId`; watch settles result; restart reconciliation marks running work failed | `docs/internals/delegation.md`; `AkeruDelegationRuntime.ts` (V/D) |
| Usage | Append-only ledger per bot/turn/category with reservations; projections and per-bot summary | `persistence/Migrations/056_AkeruBotUsageLedger.ts`, `usage/BotUsageLedger.ts` (V) |
| UI | React web, Electron desktop, React Native mobile, shared client runtime | `apps/{web,desktop,mobile}`, `packages/client-runtime` (V) |

The architecture is the main reusable asset. It already separates *the conversation*
from *the provider session*, which is the structural condition for provider-independent
bots. Akira's design adds aggregates and dimensions; it does not need a second
orchestrator.

---

## 3. Capability inventory: reuse, configure, extend, replace, build

Legend — **Reuse**: keep behaviour unchanged. **Configure**: existing switch/setting.
**Extend**: same component, new fields/commands/events. **Replace**: incompatible or
insufficient, bounded replacement. **Build**: no equivalent exists.

| # | Capability | Evidence (pinned tree) | Decision | Akira component / note | Requirement |
|---|---|---|---|---|---|
| B-01 | Event-sourced orchestration, decider/projector/reactors, receipts | `orchestration/Layers/OrchestrationEngine.ts`, `decider.ts`, `projector.ts`, `Services/RuntimeReceiptBus.ts` (V) | **Reuse + Extend** | Add Task, Goal, Rating, RouteDecision, Action, ObserverProposal aggregates as new commands/events/projections in the same engine | AK-GOV-01/04 |
| B-02 | Bot roster and profile persistence | `roster.ts` `OrchestrationBot`, `rosterCommands.ts` `BotUpdateCommand` (V) | **Extend** | Add template ref, persona revision, policy, goal/procedure refs, grant refs; keep name/title/label/description/avatar/engine/runtime mode | AK-IDE-02 |
| B-03 | Persona/identity | `AkeruAgentInstructions.ts` `createAkeruAgentInstructions` builds instructions from name, date, `personalityTone`; no free-text persona field (V) | **Replace** | Versioned PersonaRevision document + template defaults; tone slider demoted to a field | AK-IDE-03 |
| B-04 | Agent library / templates | No template commands; copying persona is manual (`docs/user/bots.md` D) | **Build** | BotTemplate + PersonaRevision + instantiate/upgrade/clone commands | AK-IDE-07..10 |
| B-05 | Per-bot memory (Markdown) | `BotMemoryStore`: `USER.md`, `MEMORY.md`, `groups/<id>/GROUP.md`, 0600/0700, locks, sanitization, budgets (`docs/internals/memory.md` D) | **Reuse + Extend** | Add task-scope memory documents and room-scope policy; keep file boundary and sanitization | AK-IDE-02, AK-TSK-06 |
| B-06 | Observational memory / context assembly | `memory.md` §Context assembly: instructions → USER → MEMORY → GROUP → entity packet → observations → recent 30 turns/≈64k tokens (D); `RecentConversation.ts` constants (V) | **Reuse** | Provider-neutral message store is what makes switching tolerable; keep budgets and ordering | AK-GOV-07 |
| B-07 | Provider drivers and registry | `builtInDrivers.ts`; `ProviderInstanceRegistry`, `ProviderAdapterRegistry`; `docs/internals/providers.md` (V/D) | **Reuse + Extend** | Add first-class DeepSeek route metadata (API-key, dialect), capability probes, account references on attempts | AK-RTE-01/02/07 |
| B-08 | Subscription auth + secret store | `docs/internals/subscription-auth.md`: `secrets/subscription-auth.json` 0600, device/PKCE flows, refresh, health (D); `subscription-auth/credentialStore.ts` (V) | **Reuse** | Keep boundary; add transport-permission metadata and per-instance account labels | AK-RTE-04/05 |
| B-09 | Fail-closed model routing | `AgentController.resolveEngine`; `docs/operations/provider-model-routing.md` (V/D) | **Reuse + Extend** | Keep fail-closed; insert route decision + capability check *before* dispatch, not a fallback inside the adapter | AK-RTE-12/16 |
| B-10 | Per-provider session lifecycle | `SessionLifecycle.ts` model switch; provider change starts new session; conversation rehydrated from memory/projection (V/D) | **Reuse** | Declare provider-native state disposable; task checkpoint carries continuity | AK-GOV-07, AK-TSK-09 |
| B-11 | Skills discovery (Claude) | `ClaudeSkills.ts` scans `<config>/skills`, `<cwd>/.agents/skills`, `<cwd>/.claude/skills`, `SKILL.md` + YAML frontmatter; `ClaudeSkillDispatch.ts` converts `$name` to `/name` (V) | **Extend** | Canonical registry projects into these roots; verify the Mastra-routed Claude transport, not only the composer path | AK-SKL-01/04/08 |
| B-12 | Skills discovery (Grok) | `GrokSkills.ts` runs `grok inspect --json` (4 s timeout), decodes `skills[]` with source path; probe failure typed (V) | **Extend** | Add support-level record; missing CLI becomes "unsupported on this host", not empty success | AK-SKL-05/08 |
| B-13 | Skills discovery (Codex) | `Layers/CodexProvider.ts` reads `snapshot.skills`; `codex/CodexCapabilitiesProbe.ts` parses `skills/list`; composer uses `$name` (V) | **Extend** | E2E verify invocation and resource access; record support level per model | AK-SKL-05/07 |
| B-14 | Skills discovery (Custom API, Kimi, OpenCode Go) | `CustomOpenaiDriver.ts:211` `skills: []`; `KimiDriver.ts:89-91` `skills: []`; `OpenCodeGoDriver.ts:123` `skills: []` (V) | **Replace (route level)** | Prompt-inject canonical skill instructions + Akira tool runtime; label `prompt-injected` | AK-SKL-06 |
| B-15 | Delegation / child threads | `docs/internals/delegation.md`; `AkeruDelegationRuntime.ts`; `PendingWaiters.ts` (V/D) | **Reuse + Extend** | Link delegations to Tasks, attempts and usage parent ids; keep exactly-once result ack and restart reconciliation | AK-TSK-10/17, AK-ACC-02 |
| B-16 | Temporary workers (Task/CheckSubagent/StopSubagent) | `docs/internals/delegation.md` §Temporary workers; `AkeruWorkerRuntime.ts` (V/D) | **Reuse + Extend** | Record as child work units with own usage, not hidden in the parent turn | AK-TSK-18, AK-ACC-05 |
| B-17 | File checkpoints | `checkpointing/CheckpointStore.ts` capture/restore/diff; `CHECKPOINT_REFS_PREFIX = "refs/t3/checkpoints"` (V) | **Reuse + Extend** | Add TaskCheckpoint record referencing the file checkpoint; snapshot before external effects | AK-TSK-06/08 |
| B-18 | Routines and scheduling | `AkeruRoutineSchemas.ts` (daily/weekdays/weekly, skill/connector names, lifecycle draft→approved→enabled…); routine approval flow (V/D) | **Reuse + Extend** | Bind routines to versioned procedures; re-approval on procedure change; schedule + delegation to another bot retained | AK-IDE-06, AK-SKL-10 |
| B-19 | Groups (boss/specialist, mentions) | `roster.ts` groups; `docs/user/chats.md` §Group chats (V/D) | **Extend** | Rooms with topics, roles, board items, explicit routing rule; boss default becomes a configurable rule | AK-COL-01/02 |
| B-20 | Silence handling | `SilenceWatchdog.ts` + `docs/internals/silence-watchdog.md`: 90 s stall detector, inbox item, never interrupts (V/D) | **Reuse + Build** | Keep as liveness; add publish gate and `TurnOutcome=silent` with reason (not the same feature) | AK-COL-04..06 |
| B-21 | Approval / permission modes | `docs/user/permission-modes.md`; `AkeruToolRuntime.approvals`; protected action list (D/V) | **Reuse + Extend** | Keep four modes and protected actions; add per-connector grant scopes and spend gates | AK-SEC-02/03/09 |
| B-22 | Usage ledger | Migration 056/068; `AkeruUsageEntry` categories turn/tool/observer/reflector/extraction/recall/routine/delegated; `UNIQUE(bot_id, source_key)`; states reserved/reported/unavailable/released (V) | **Extend** | Add task/attempt/room/account/parent columns, cost provenance, non-token units, correction records | AK-ACC-01..04 |
| B-23 | Usage presentation | `docs/user/usage.md`: per-bot input/output/Observer/Reflector, estimates "not money spent", plan meters, `Unavailable` (D) | **Extend** | Exclusive/inclusive task and room views; label measured/estimated/subscription/unknown | AK-ACC-12/13 |
| B-24 | Channels (Slack/Discord/Telegram/WhatsApp/iMessage/Photon) | `channels/ChannelRuntime.ts`; `docs/internals/channels.md`: delivery states pending/sent/failed/unknown, idempotent inbound, reply ownership, WhatsApp public HTTPS + DM only (V/D) | **Reuse + Extend** | Keep delivery-state honesty; add WhatsApp template/media/admin capability; add PSTN adapter separately | AK-SPC-02/03/04, AK-CON-07 |
| B-25 | Voice | `docs/user/voice.md`: in-client calls (ChatGPT realtime / OpenAI API / transcribe-reply-speak); no PSTN (D) | **Reuse** | Keep as in-client capability, explicitly not telephony | AK-SPC-02 |
| B-26 | Image generation | `docs/user/image-generation.md`: ChatGPT/Grok subscription providers, per-bot provider, fallback order, stills (D) | **Reuse + Extend** | Add provider-agnostic image tool interface and local/API providers | AK-SPC-05 |
| B-27 | Video | No video capability in docs or catalog (V/D) | **Build** | Async video workflow with render approval gate | AK-SPC-06 |
| B-28 | Plugins / MCP / Composio | `plugins/entries/*` 54 entries, all `verification-pending` or `approval-pending`; `isInstallablePlugin` refuses both; Composio own-key path (V/D) | **Reuse substrate + Build connectors** | Custom MCP and own Composio work now; catalog is preview only; first-party connectors where needed | AK-CON-02/04 |
| B-29 | Workspace, sandboxes, computer, browser | `docs/user/sandboxes.md`, `computer.md`, `provider/computer*`, `botBrowser.ts` (D/V) | **Reuse + Configure** | Keep local/E2B/Daytona/Vercel/Upstash; browser automation is a labelled fallback, not connector parity | AK-CON-10 |
| B-30 | Remote access, pairing, SSH/tailnet | `docs/user/remote-access.md`; `packages/ssh`, `packages/tailscale` (D/V) | **Reuse** | Keep private-by-default posture; add explicit admin scopes audit | AK-SEC-07 |
| B-31 | Export/import | `docs/user/data-portability.md`: `akeru.archive` excludes secrets, bot memory, routines, skill assignments, usage, files, repos, attachments, checkpoints; 20 MiB (D) | **Replace (export scope)** | Full-team bundle with memory, routines, skills, usage, checkpoints, ratings; async, verified, versioned | AK-OPS-04/05 |
| B-32 | Archived-bot deletion | `ARCHIVED_BOT_RETENTION_DAYS = 7` (`roster.ts:358`); `archivedBotRetention.ts` hourly sweep dispatches `bot.delete` with `archivedAt` (V) | **Replace (disable)** | Retention off by default; archive-first UI; purge only on explicit named HUMAN request | AKIRA-D2, AK-OPS-11 |
| B-33 | Delete semantics | `decider/bots.ts` `bot.delete` deletes routine assignments/skill assignments and emits `bot.deleted`; chats stay (V/D) | **Extend** | Remove hard delete from UI; add explicit purge with audit and backup verification; the decider rejects a direct `bot.delete` unless it carries the `purge.request` guards | AK-OPS-11, AK-OPS-17, AK-SEC-08 |
| B-34 | Observability | `docs/internals/observability.md`, `server.trace.ndjson`, per-thread provider event logs (D) | **Reuse + Extend** | Keep NDJSON traces; add task/attempt/route spans and metrics/alerting | AK-OPS-07 |
| B-35 | Analytics | Fixed 18-counter payload, no user content, local buffering (`docs/internals/usage-analytics.md`, D) | **Configure** | Off by default for Akira unless operator opts in; keep the fixed schema | AK-SEC-12 |
| B-36 | Tests / CI | Vitest-style focused tests, integration harnesses, `vp test`, lint gates (V/D) | **Reuse** | Akira adds its own suite; both must pass on every patch | AK-TST-01 |

### Patch-burden notes

- The event/command/projection layer is additive by design (new event types + decider
  branches + projections). Risk is medium: the decider is central and heavily tested;
  every new aggregate needs invariants and tests.
- Persona/instructions replacement touches `AkeruAgentInstructions.ts` and every
  provider's context assembly path. Risk is medium-high: it is on the critical path of
  every turn and must remain provider-identical.
- Usage ledger extension is additive (columns + migration + write paths). Risk is medium:
  accounting must not double count, and the unique constraints must be preserved.
- Disabling retention is small but must be proven by test; it is a contracts constant plus
  the startup sweep. Risk is low code-wise, high consequence-wise.
- Skills projections per route are the highest-variance area: four different discovery
  mechanisms, each with its own failure mode. Budget for per-route E2E tests, not just
  unit tests.

---

## 4. Behaviour incompatible with Akira requirements (find before depending on it)

| # | Akeru behaviour | Why it conflicts | Akira response |
|---|---|---|---|
| X-01 | Archived bots deleted after 7 days, hourly sweep | Violates AKIRA-D2 | Disable sweep; archive-first; test that no delete command is emitted |
| X-02 | Bot "delete" removes roster entry, routines and skill assignments | Destructive without naming items; irreversible in UI | Remove from normal flow; explicit purge only, with backup + audit |
| X-03 | Persona is generated from a tone number; no authored instructions | Cannot carry the named team's outlook/attitude/procedures | PersonaRevision + templates; tone remains optional |
| X-04 | Boss answers every group message by default; no silence outcome | Produces chatter and duplicate answers | Room routing rules + publish gate + silence reason codes |
| X-05 | Fail-closed routing with no per-task routing, no fallback policy | Cannot meet "good enough per task" or credit exhaustion handling | RouteDecision before dispatch; conservative fallback policy; task pause on quota |
| X-06 | Skills catalogs empty on Custom API/Kimi/OpenCode Go | A DeepSeek bot appears to have skills but they are not dispatched | Prompt-injected skill path, labelled; E2E per route |
| X-07 | Export excludes memory, routines, skills, usage, checkpoints; 20 MiB cap | Cannot restore a working team | Full-team export with verified restore |
| X-08 | Delegation restart marks running work failed (no resume) | Loses in-flight task progress | Task checkpoint + resume; delegation failure remains a signal, not the recovery mechanism |
| X-09 | Usage lacks task/attempt/account/room/parent dimensions | Cannot bill a task or prevent double counting | Ledger extension; exclusive/inclusive model |
| X-10 | No ratings, no effectiveness observer; Observer/Reflector are memory stages | Requirements explicitly ask for both | New aggregates; memory stages renamed to avoid confusion |
| X-11 | No shared result pages; rich replies and attachments only | The existing team's "pages" have no home | Board/artifact items with stable links |
| X-12 | Plugin catalog not installable; connector parity cannot be claimed | Migration and specialist requirements would silently fail | Honest inventory; MCP + Composio + first-party connectors |
| X-13 | In-client voice presented near "calls"; no PSTN | HUMAN asked for phone calls | Separate PSTN capability; in-client voice labelled |
| X-14 | Provider session state is not portable; Mastra trace lacks provider/model attributes | Switch provenance would be guessed | Record route at attempt level; extend spans; never infer effective model |

---

## 5. Gap matrix: HUMAN requirement → current Akeru → gap → Akira requirement

| HUMAN requirement | Current Akeru (evidence) | Gap | Akira requirement |
|---|---|---|---|
| Same persistent bots across Codex/Claude/DeepSeek/Grok, switching when credits run out | Bot record holds one engine; provider change starts a fresh session; conversation/memory rehydrated (V/D) | No per-task route, no fallback policy, no credit handling, no attempt provenance | AK-RTE-01..16, AK-TSK-04 |
| Identity/persona independent of provider | Name/description/tone only; memory files provider-neutral (V) | No authored persona, goals, procedures | AK-IDE-01..12 |
| Easy bot declaration | Setup asks one question, proposes plan, names bot, first message (D) | No library, no dependency map, no policy choice | AK-UX-01..03, AK-IDE-07..09 |
| Low total cost | No platform fee; subscriptions/API; usage page (D) | No task cost, no total delivery cost, no rework accounting | AK-ACC-01..16, AK-TRG-14 |
| SKILLS.md / skills support | `SKILL.md` per driver; SKILLS.md absent (V) | Canonical package, per-route execution, index | AK-SKL-01..12 |
| Agent library with named specialists | None | Templates, instances, upgrade, clone | AK-IDE-07..10 |
| Autonomy within intent | Approvals, protected actions, auto-review (D) | No task-level autonomy boundaries or spend guards | AK-SEC-01..11 |
| Deliberate silence | Stall watchdog only; boss answers every message (V/D) | Publish gate, silence reasons, anti-ping-pong | AK-COL-03..07 |
| Constructive peer challenge | No challenge protocol | Structured challenge, dissent record | AK-COL-08..10 |
| Observer bot | None (memory stages only) | Proposal + evaluation + approval + cost | AK-OBS-01..08 |
| Credit/rate/auth/capability distinction | Typed unavailability categories and fail-closed (V) | Classification into attempt outcome + route policy | AK-RTE-12/13, AK-UX-11 |
| Task-specific good-enough routing | Saved model per bot; no triage | Task classes, floors, readiness, escalation | AK-TRG-01..16 |
| Safe switching and resume | Chat delivery once; restart fails running delegation; checkpoint per turn (V/D) | Task checkpoint, action ledger, reconciliation, resume across routes | AK-TSK-01..18 |
| Phone, WhatsApp Business, images, movies | WhatsApp DM channel; subscription images; in-client voice; no video/PSTN (V/D) | Capability contracts + adapters | AK-SPC-01..12 |
| Grokbot connector replication | Custom MCP + own Composio; catalog preview only (V/D) | Inventory, custody, re-auth, fallbacks | AK-CON-01..12 |
| Team/room migration | Export excludes memory/routines/skills/usage; no pages (D) | Full bundle; drafted personas; room/board recreation | AK-IDE-13/14, AK-OPS-12 |
| Lean UI with compact indicators | Roster/groups/conversation; separate usage page (D) | Task/route/quality/usage indicators with drill-down | AK-UX-04, AK-UX-17..22 |
| Task ratings | None | Rating record, disputes, reputation separation | AK-RAT-01..08 |
| Usage transparency | Per-bot tokens + plan meters; estimates labelled; `Unavailable` (D) | Task/attempt/room/account/parent attribution, exclusive/inclusive | AK-ACC-01..16 |
| Early complexity triage | Question cards and routine approvals only (D) | Triage, discovery budget, readiness rubric, re-triage | AK-TRG-01..16 |
| No deletion without explicit naming | 7-day auto-delete; delete button (V) | Retention off, archive-first, explicit purge | AKIRA-D2, AK-OPS-11 |
| Production operations | systemd service, snapshot-before-update, traces (D) | Full backup/restore, alerts, incident runbooks, capacity | AK-OPS-01..14 |

---

## 6. What was not inspected (honest unknowns)

| Area | Status | What resolves it |
|---|---|---|
| Live behaviour of any provider route (tool calls, streaming, resume) | U — nothing executed | Route verification suite with test accounts |
| DeepSeek wire format through the Custom API driver | U — source shows OpenAI-compatible path, no live transcript | E2E tool-call transcript test |
| Whether the Mastra-routed Claude transport uses `ClaudeSkills.ts`/`ClaudeSkillDispatch.ts` or a different path | U — the composer-path source is inspected; runtime use is not proven | Instrumented skill execution test on the Mastra route |
| Whether `ClaudeDriver`/`CodexDriver` report skills for models without a CLI | Partially D, not executed | Provider snapshot test with fixture homes |
| Web/desktop/mobile visual details beyond docs | U — no app run | UI fixtures and screenshots during the vertical slice |
| Akeru's real memory file sizes/budgets at runtime | D only (documented budgets) | Runtime probe |
| Connector behaviours behind the catalog | U — none installable | Per-service E2E with test accounts |
| Vendor pricing and terms (Twilio/Meta/Google/xAI/OpenAI/Anthropic) | U — not fetched for pricing in this session | Primary-source fetch at integration decision time, dated |
| Load/capacity behaviour (SQLite, event volume, attachments) | U — no benchmark | Capacity test in Phase 0/10 |

---

## 7. Baseline conclusion

Akeru supplies the right skeleton and a surprising amount of the hard work (durable
events, provider adapters, delegation plumbing, memory boundaries, usage reservations,
channel delivery states). It does not supply Akira's product concepts. The correct
strategy is therefore **additive extension around a single authority**, with four bounded
replacements: persona/instructions, export scope, retention/deletion policy, and the
empty skills catalogs on non-native routes. Everything else is extension or build.

Any implementation that finds itself adding a second orchestrator, a second retry loop or
a second task store has left the approved design (`docs/03-architecture.md`, ADR-01) and
must stop and raise it.
