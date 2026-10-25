# 14 — Evidence log: what was inspected and how

**Status:** Final specification v0.7

**Purpose:** make every `V` claim reproducible by another engineer, and record what was
*not* done so nobody mistakes inspection for verification.

**Session date:** 2026-10-24 (Europe/Paris). **Author:** specification agent (no
deployment, build or provider login performed).

---

## 1. Pinned source

| Item | Value |
|---|---|
| Repository | `https://github.com/opencoredev/akeru-bot` |
| Revision | `524eb68a293c4b6a38acf722ab4232cfe5e22625` |
| Commit date | 2026-10-23T21:06:41Z |
| Commit subject | `feat(marketing): link to the other OpenCore sites from the footer (#470)` |
| Remote HEAD at inspection | same SHA (`git ls-remote … HEAD`) |
| Fetch method | `https://codeload.github.com/opencoredev/akeru-bot/tar.gz/<sha>` (tarball, no `.git`) |
| Local copy used | workspace scratch directory, not committed |
| Repo metadata | GitHub API: MIT, 106 stars, 10 forks, 70 open issues, created 2026-08-27, pushed 2026-10-23, latest release `v0.2.1` published 2026-10-01 |

**Checks.** The tarball was extracted and `README.md`, `LICENSE`, `package.json`,
`docs/**`, `plugins/entries/**`, `packages/contracts/**`, `apps/server/src/**` were read
directly. No dependency install, build, typecheck, test, lint or app launch was run.

A locally downloaded `Akeru-Bot-0.2.1-x64.AppImage` exists on the host (dated
2026-10-24 22:55, ~338 MB). It was **not** executed and is not evidence for any behaviour.

---

## 2. Files read (grouped by claim)

### Licensing and provenance
- `LICENSE` (MIT, T3 Tools Inc.)
- `THIRD_PARTY_NOTICES.md`, `legal/licenses/Mastra-Code.txt`
- `README.md` (including the "Do not push or publish this fork" line)

### Architecture and state
- `AGENTS.md`, `CLAUDE.md` (project rules; used only as documentation of intent)
- `docs/internals/overview.md`, `providers.md`, `memory.md`, `delegation.md`,
  `workspace-layout.md`, `usage-analytics.md`, `silence-watchdog.md`, `channels.md`,
  `observability.md`, `data-portability.md`, `subscription-auth.md`
- `apps/server/src/orchestration/**` (decider, projector, services, reactor layout)
- `apps/server/src/checkpointing/**` (`CheckpointStore`, `CHECKPOINT_REFS_PREFIX`)
- `apps/server/src/archivedBotRetention.ts`
- `packages/contracts/src/orchestration/roster.ts`, `rosterCommands.ts`, `events.ts`,
  `modelSelection.ts`
- `packages/contracts/src/usage.ts`, `akeruUsage.ts`
- `apps/server/src/persistence/Migrations/056_AkeruBotUsageLedger.ts`

### Providers and auth
- `apps/server/src/provider/builtInDrivers.ts`
- `apps/server/src/provider/Drivers/{Claude,Grok,Codex,CustomOpenai,Kimi,OpenCode,OpenCodeGo}Driver.ts`
- `apps/server/src/provider/Drivers/{ClaudeSkills,ClaudeSkillDispatch,GrokSkills}.ts`
- `apps/server/src/provider/Layers/codex/CodexCapabilitiesProbe.ts`
- `apps/server/src/provider/Layers/AgentController.ts`,
  `agentController/EngineRouting.ts`, `agentController/SessionLifecycle.ts`
- `apps/server/src/provider/mastra/AkeruMemory.ts`, `AkeruConversation.ts`,
  `AkeruRoutineSchemas.ts`
- `apps/server/src/provider/ReasoningOptions.ts`, `RecentConversation.ts`
- `docs/user/providers.md`, `docs/operations/provider-model-routing.md`,
  `docs/internals/subscription-auth.md`

### Skills
- `ClaudeSkills.ts` (roots/precedence/frontmatter), `ClaudeSkillDispatch.ts` (`$` → `/`),
  `GrokSkills.ts` (`grok inspect --json`, 4 s timeout)
- `packages/contracts/src/providerInstance.ts` (`ServerProviderSkill`)
- Grep: `skills: []` occurrences in `CustomOpenaiDriver.ts:211`, `KimiDriver.ts:89-91`,
  `OpenCodeGoDriver.ts:123`; `skills/list` in `CodexCapabilitiesProbe.ts`

### Collaboration, memory, usage
- `docs/user/bots.md`, `chats.md`, `usage.md`, `memory.md`, `channels.md`, `voice.md`,
  `image-generation.md`, `data-portability.md`, `permission-modes.md`
- `docs/internals/memory.md`, `delegation.md`, `channels.md`
- `apps/server/src/provider/AkeruAgentInstructions.ts`
- `apps/server/src/orchestration/SilenceWatchdog.ts` and its doc
- `apps/server/src/usage/{BotUsageLedger,BotUsageRows,UsageService}.ts`
- `apps/server/src/orchestration/decider/bots.ts` (`bot.delete` cascade)

### Connectors and plugins
- `plugins/entries/*/plugin.json` (54 entries) — tabulated id, category, transport, auth,
  connection type, catalog status
- `apps/server/src/provider/tools/AkeruPluginCatalog.ts` (`isInstallablePlugin`,
  install refusal for pending statuses)
- `plugins/catalog.test.ts` (status semantics)
- `docs/user/plugins.md`, `docs/internals/connector-gap-matrix.md`
- `docs/internals/channels.md` (WhatsApp public origin, delivery states)

### Deployment and operations
- `docs/user/install.md`, `background-service.md`, `remote-access.md`
- `apps/server/src/config.ts` (`deriveServerPaths`: `state.sqlite`, `secrets`, `logs`,
  `attachments`, `worktrees`)
- `docs/internals/observability.md`

### Tests
- File listing and selected tests under `apps/server/src/**` (unit/integration pattern),
  `plugins/catalog.test.ts`, `PluginLifecycleMatrix.test.ts` (name only)

---

## 3. Commands used (no mutations)

```bash
git ls-remote https://github.com/opencoredev/akeru-bot HEAD refs/heads/main
curl -sSL https://codeload.github.com/opencoredev/akeru-bot/tar.gz/<sha> -o akeru.tar.gz
tar -xzf akeru.tar.gz
curl -s https://api.github.com/repos/opencoredev/akeru-bot
curl -s https://api.github.com/repos/opencoredev/akeru-bot/commits/<sha>
curl -s https://api.github.com/repos/opencoredev/akeru-bot/releases/latest
wc -l $(find apps packages -name '*.ts' -o -name '*.tsx')
jq -r … plugins/entries/*/plugin.json        # read-only tabulation
grep -rn … (source/doc searches)
```

Vendor pages: Gmail scopes page fetched (HTTP 200; scopes listed), Twilio Call resource
and Meta WhatsApp send page fetched (HTTP 200; Meta `wamid` confirmed; Twilio idempotency
field **not** established because the page is JS-rendered). No pricing was fetched for
this specification; cost bases are marked unknown where not read.

---

## 4. What was not done (and why it matters)

| Not done | Consequence |
|---|---|
| Install/build/launch Akeru | All runtime claims are documentation/source-level, not reproduced |
| Any provider login or live turn | Route matrices are "advertised/implemented", not "works" |
| Tool-call transcript on any route | DeepSeek and per-route tool reliability remain unverified |
| Skill execution on any route | Support levels are target states, not measured |
| Connector authentication | Connector matrix is design + effort, not tested capability |
| Vendor onboarding or pricing | Specialist costs are unknown/stated as such |
| Retention sweep exercise | Deletion behaviour is code-inspected only; test is specified, not run |
| Export/import exercise | Data-portability limitations are documentation-level |
| Load/capacity benchmark | Capacity model is assumptions + reasoning |
| Desktop/mobile run | UI claims are structural, from docs/source |

---

## 5. Contradictions found with the debate record

| Debate statement | Pinned-source finding | Handling |
|---|---|---|
| "Usage page shows per-bot input/output plus Observer/Reflector; no per-task view" | A durable ledger exists with categories turn/tool/observer/reflector/extraction/recall/routine/delegated and reservation states (V). It lacks task/attempt/room/account/parent dimensions and cost provenance, and the UI docs show per-bot only | Corrected: Akira extends a real ledger, rather than inventing accounting |
| "Skills are per driver: Claude scans, Grok CLI, Custom API empty" | Also empty on Kimi and OpenCode Go; Codex uses app-server `skills/list`; Claude dispatch converts `$name` to `/name` | Extended matrix; more routes need prompt injection |
| "Delegation is not resume" | Restart marks running delegations failed; retry is a new record; result delivery is acknowledged in the same persisted step as the next turn | Confirmed; Akira adds task checkpoints and keeps exactly-once chat acknowledgement |
| "No template library" | No template commands/records; persona is generated from name/tone/description | Confirmed; library is a build |
| "Observer/Reflector are memory curation" | `AkeruMemory.ts` maps observation/reflection callbacks; usage categories observer/reflector | Confirmed; no effectiveness observer |
| "Plugin catalog may provide connectors" | 54 entries, 0 installable; install refuses pending statuses | Stronger: catalog is a preview, not capability |
| "WhatsApp Business connector" | DM channel via Cloud API; administration not implemented | Confirmed; split messaging vs admin |
| "Voice calls" | In-client only; no PSTN | Confirmed; separate telephony contract |

---

## 6. Confidence

| Claim class | Confidence | Basis |
|---|---|---|
| Source paths/symbols and pinned revision | High | Direct reads, tarball at SHA |
| Behaviour described by upstream docs | Medium-high | Documentation at the same revision; not executed |
| Runtime behaviour (tool calls, skills, resume) | Low | Not reproduced |
| Vendor capability/pricing | Low | Partial fetches, no pricing |
| Effort estimates | Low-medium | Code size and complexity inspection, no history |

---

## 7. Reproduce this inspection

```bash
SHA=524eb68a293c4b6a38acf722ab4232cfe5e22625
curl -sSL "https://codeload.github.com/opencoredev/akeru-bot/tar.gz/$SHA" -o /tmp/akeru.tgz
mkdir -p /tmp/akeru && tar -xzf /tmp/akeru.tgz -C /tmp/akeru --strip-components=1
cd /tmp/akeru
sed -n '350,370p' packages/contracts/src/orchestration/roster.ts        # retention constant
sed -n '1,60p' apps/server/src/archivedBotRetention.ts                  # hourly sweep
grep -n "skills: \[\]" apps/server/src/provider/Drivers/*.ts            # empty catalogs
sed -n '1,60p' docs/internals/delegation.md                             # child threads/restart
```

Anything this log marks U must be treated as unknown by an implementing agent until a
test produces evidence.
