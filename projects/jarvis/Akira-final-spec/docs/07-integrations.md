# 07 — Integration matrices: routes, skills, connectors, specialists

**Status:** Final specification v0.7 · **Normative:** `spec.md` §6, §9, §13, §14.
**Evidence date:** 2026-10-24 unless stated. Nothing below was executed. `V` = inspected file/source, `D` = upstream documentation, `M` = maintainer-reported, `R` = reasoning, `U` = unknown.

---

## 1. Route model and what must be verified per route

A route is a tuple, not a product name:

```
route = { harness, driver, api provider, model, account/instance, auth class, options }
```

| Dimension | Examples | Why it must be separate |
|---|---|---|
| Harness | Akeru Mastra controller; standard OpenCode legacy bridge; Codex CLI app-server | Determines tool loop, approvals, skills wiring, resume semantics |
| Driver | `codex`, `claudeAgent`, `grok`, `kimi`, `opencodeGo`, `customOpenai` | Determines protocol translation and capability probing |
| API provider | OpenAI, Anthropic, xAI, Moonshot, DeepSeek, local | Determines quota, pricing, data handling, tool dialect |
| Model | `gpt-5.1-codex`, `sonnet-4.7`, `deepseek-chat`, `grok-4.7` | Determines context, reasoning controls, quality, cost |
| Account | subscription plan or API key; main/backup | Determines credits, rate limits, terms, which bill |
| Auth class | OAuth subscription / API key / local | Determines terms, refresh, failure modes |

**Verification rule:** each route gets a capability record from `probe()` plus an
end-to-end transcript (tool call → result → final answer) before it may be used for a
task class whose floor requires tools. A route is `unknown` until then.

---

## 2. Provider routes: inspected facts and support level

### 2.1 Built-in drivers (V: `provider/builtInDrivers.ts`; D: `docs/internals/providers.md`)

| Driver | Runtime | Auth routes known to Akeru | Tool calling evidence | Skills | Notes |
|---|---|---|---|---|---|
| `codex` | Mastra controller | ChatGPT subscription via device flow; API key uses OpenAI Responses API (D) | Mastra catalog; Codex app-server for sessions | app-server `skills/list` | Reroute event exists; effective-model reporting incomplete in traces |
| `claudeAgent` | Mastra controller | Claude Pro/Max via paste-code PKCE; API key | Mastra catalog | filesystem scan + `$name`→`/name` dispatch | Whether the Mastra-routed transport uses the scanner is unverified |
| `grok` | Mastra controller | xAI device flow; API key at default endpoint; custom base URL rejected (D) | Mastra catalog | `grok inspect --json` | CLI absent → empty catalog (typed failure) |
| `kimi` | Mastra controller | Moonshot device flow; API key | Mastra catalog | declared `skills: []` (V) | U: real skill path |
| `opencodeGo` | Mastra controller | API key | Mastra catalog | declared `skills: []` (V) | U: real skill path |
| `opencode` (standard) | legacy bridge | CLI install + login/API | native adapter; child sessions | `debug skill` inventory | Cannot delegate (V) |
| `customOpenai` | Mastra controller | base URL + optional key | OpenAI-compatible `tools` | declared `skills: []` (V) | DeepSeek preset lives here |

### 2.2 DeepSeek specifically

| Question | Current evidence | Status |
|---|---|---|
| How does Akeru reach DeepSeek? | Custom API preset: base URL + API key; `createOpenAICompatible` (D/V) | Confirmed in docs; preset URL not verified |
| Does DeepSeek support tool calling? | Yes, OpenAI-SDK `tools` round trip (D, DeepSeek API docs; the debate's earlier "undocumented" claim was a wrong URL) | Documented, not executed |
| Can tool calls be inserted mid-conversation? | Chat Completions cannot insert assistant tool calls mid-history; Anthropic `/messages` and Responses can (D) | Relevant to resume design: replay is not portable |
| Is a DeepSeek "Claude Code" or "Codex" integration a subscription? | No — they are API-key harness routes (D) | Confirmed |
| Which API family does Akeru's preset use? | Not established | U — verify with a transcript test |
| Skills on this route? | `skills: []` in the driver (V) | Unsupported natively → prompt injection |

**Akira requirement:** DeepSeek is a first-class, supported route for tasks whose floor
is text plus tools, but it is not assumed interchangeable. It must pass the transcript
test, declare its dialect and context, and use prompt-injected skills (labelled).

### 2.3 Transport permission (terms)

| Route class | Permission status | Consequence |
|---|---|---|
| API keys (DeepSeek, OpenRouter, Groq, local, provider API keys) | Standard API use; terms accepted by the operator | Included in cost case |
| ChatGPT/Claude/Grok/Kimi subscription OAuth through Akeru's own runtime | `assumed-for-personal-use` under AKIRA-D5; per-route `verified` after a terms check | Included as `subscription-equivalent`; a route with `forbidden` terms is disabled with the reason recorded |
| Subscription CLIs invoked by a third-party runtime | `assumed-for-personal-use` (same decision) | Same; the operator owns vendor compliance |

The route record carries `transportPermission` and the UI shows the status. This is
not a legal opinion; it is a traceability requirement, and the operator remains
responsible for vendor terms.

---

## 3. Tool and feature support per route

| Feature | Codex | Claude | Grok | Kimi | OpenCode Go | Custom API (DeepSeek) | Standard OpenCode |
|---|---|---|---|---|---|---|---|
| Tool calling (Mastra catalog) | yes (D) | yes (D) | yes (D) | yes (D) | yes (D) | OpenAI-compatible `tools` (D) | native (D) |
| Parallel tool calls | U | U | U | U | U | model-dependent U | U |
| Native skills | app-server list | scan + slash dispatch | CLI probe | empty (V) | empty (V) | empty (V) | CLI inventory |
| Delegation (`SendToAgent`) | yes (D) | yes (D) | yes (D) | yes (D) | yes (D) | yes (D) | **no** (V) |
| Temporary workers | yes | yes | yes | yes | yes | yes | no |
| Image generation | via Akeru image runtime (separate provider) | same | same | same | same | same | same |
| In-client voice | ChatGPT/OpenAI API | ChatGPT/OpenAI API | ChatGPT/OpenAI API | same | same | same | same |
| Usage reporting | per-turn/aggregate (varies) | provider usage | provider usage | provider usage | API usage | API usage if returned | provider CLI |
| Effective model reported | partial (`model.rerouted`) | U | U | U | U | U | legacy span only |
| Resume across restart | task checkpoint (Akira) | task checkpoint | task checkpoint | task checkpoint | task checkpoint | task checkpoint | task checkpoint |

"yes" here means the inspected code advertises the capability through the shared
controller; it is not an executed claim (see `docs/10-tests-and-acceptance.md` T-02).

---

## 4. Skills: canonical package, per-route support levels

### 4.1 Discovery facts

| Route | Mechanism | Source | Status for Akira |
|---|---|---|---|
| Claude | Scan `<config>/skills`, `<cwd>/.agents/skills`, `<cwd>/.claude/skills`; YAML frontmatter; precedence user → `.agents` → `.claude`; `$name` converted to `/name` before the message is sent | `ClaudeSkills.ts`, `ClaudeSkillDispatch.ts` (V) | Project canonical bundles here; verify execution on the Mastra route |
| Codex | App-server `skills/list`; composer inserts `$name`; Codex parses natively | `CodexCapabilitiesProbe.ts`, `codexLaunchArgs` (V) | Verify invocation + resource access E2E |
| Grok | `grok inspect --json`, 4 s timeout, decodes `skills[]` with absolute `SKILL.md` path and `userInvocable` | `GrokSkills.ts` (V) | Keep; missing CLI is "unsupported on host", not empty success |
| Kimi | Declared empty | `KimiDriver.ts:89-91` (V) | Prompt-injected path |
| OpenCode Go | Declared empty | `OpenCodeGoDriver.ts:123` (V) | Prompt-injected path |
| Custom API (DeepSeek) | Declared empty | `CustomOpenaiDriver.ts:211` (V) | Prompt-injected path |
| Standard OpenCode | CLI inventory (`debug skill`), serialized probe | `opencodeRuntime.ts` (V) | Keep as legacy; not a first-class route |

### 4.2 Support-level matrix (target state, after verification)

| Route | `native-verified` | `prompt-injected` | Notes |
|---|---|---|---|
| Codex | required for skills with resources | fallback if a skill cannot be projected | `$name` invocation must be proven |
| Claude | required | fallback | Prove the Mastra transport path, not only the composer |
| Grok | required when CLI present | if CLI absent | Host-level capability |
| Kimi / OpenCode Go / Custom API | none | required | No native discovery; instructions injected |
| Standard OpenCode | legacy best-effort | optional | Not required for v1 |

### 4.3 Naming: `SKILL.md` vs `SKILLS.md`

No inspected mechanism reads a literal `SKILLS.md` (V across all four routes plus
Codex/Claude/Grok ecosystem docs). Akira therefore:

1. uses `SKILL.md` directories as the canonical executable format;
2. generates `SKILLS.md` as a human-readable index (names, versions, support levels,
   dependencies) from the registry;
3. states this substitution in the skill settings screen.

This satisfies the HUMAN request for "SKILLS.md support" without pretending a file name
is a runtime contract. The concrete v1 packages, statuses and fixtures are in
`docs/15-skills-v1.md`.

---

## 5. Specialist capability contracts

Each contract is independent of vendor. A vendor adapter fills it in; the spec does not
select a vendor without current primary-source evidence (`docs/13-open-decisions.md` U7).

### 5.1 Telephony (PSTN)

| Operation | Direction | Async | Semantics | Verification |
|---|---|---|---|---|
| `call.place` | write | yes | returns call id; may fail after acceptance | stub + test number only |
| `call.status` / callback | read | webhook | queued/ringing/in-progress/completed/failed/busy/no-answer | replay-safe, idempotent by call id |
| `call.dtmf` | write | yes | digits during a live call | stub |
| `call.hangup` | write | yes | idempotent by call id | stub |
| `recording.get` / `transcript.get` | read | delayed | may be absent; consent policy | stub + policy review |
| `voicemail.detect` | read | derived | provider-dependent | U |

Candidate: Twilio Programmable Voice (documented Call resource, status callbacks). Whether
Twilio supports a client idempotency key for call creation is **U** (the docs page is
JS-rendered and was not parsed for that field); the adapter must not assume it. Consent
and recording rules are mandatory configuration.

### 5.2 WhatsApp messaging

| Operation | Direction | Notes |
|---|---|---|
| `message.send-text` | write | may be accepted then fail in UI; `unknown` state required |
| `message.send-media` | write | media upload + message; size/type limits |
| `message.send-template` | write | template must be approved; parameters |
| `message.receive` | webhook | idempotent by message id; ignore bot-authored/empty |
| `message.status` | webhook | sent/delivered/read/failed; delayed |
| `conversation.window` | read | customer-service window rules; template needed outside it |

Base: Akeru's Cloud API channel — direct messages only, one bot per account, public HTTPS
webhook, delivery states including `unknown` (V/D). Akira keeps those constraints visible
and adds media/templates only after verification.

### 5.3 WhatsApp Business administration (separate capability)

| Operation | Supported by Cloud API? | Akira status |
|---|---|---|
| Business profile read/update | yes (Graph) | planned adapter |
| Phone number registration/verification | yes (Graph onboarding) | planned, onboarding-heavy |
| Message template create/list/update/delete | yes | planned |
| Quality rating / messaging limits | yes (read) | planned |
| Business verification / account review | Meta-controlled, not fully API-driven | **not supported** as automation; manual checklist |
| Sender/account deletion or migration | provider-controlled | explicit manual runbook only |

Akira MUST NOT claim "WhatsApp Business management" from messaging support. The
administration capability has its own permissions, verification and cost basis.

### 5.4 Image generation

| Operation | Notes |
|---|---|
| `image.generate` | prompt, size/aspect, count, seed; returns artifact + cost |
| `image.edit` / reference | provider-dependent; label if unsupported |
| `image.describe` | optional metadata/provenance |
| moderation/safety | required; provider or local policy |
| storage/licensing | artifact with provenance and license field |

Provider candidates: Akeru's ChatGPT/Grok subscription tools (existing), xAI image API,
OpenAI Images API, local SDXL pipeline (operator already runs one). Selection is a
configuration decision with per-image cost basis and a quality comparison on fixtures.

### 5.5 Short movies

Stages: brief → script → storyboard → shots → audio/voice → assembly → review →
deliverable. Each stage is an artifact; each render is a paid job with an approval gate
(default: any paid render requires approval until HUMAN sets a cap). Candidate providers
must be checked for async job APIs, duration/resolution limits, audio support and
licensing. Akeru has no video capability (V); this is a build, not an extension.

### 5.6 What is explicitly not a specialist

- In-client voice calls (Akeru) are not PSTN.
- A WhatsApp DM channel is not account administration.
- Image generation is not a video workflow.
- A browser automation script is not a connector.

---

## 6. Connector inventory

### 6.1 Substrate status (V/D)

| Path | Status | Notes |
|---|---|---|
| Custom MCP servers | supported | add/edit/disable/remove; per-bot enablement; guidance field |
| Composio (bring your own key) | supported | Akeru holds no vendor OAuth; account connect via Composio |
| Bundled plugin catalog | **not installable** | 54 entries: 0 installable; all `verification-pending` or `approval-pending` |
| Gmail | brokered + verification-pending | Connect stays unavailable |
| Hosted Grokbot connectors | not transferable | tokens stay on the vendor backend |

### 6.2 Required service matrix

Effort is an engineering estimate (person-days, 1 senior engineer, ±50%) for a
first-party adapter with tests, not a vendor onboarding time. It is the **adapter-only
subset** of the connector effort in `docs/11` §10, which adds 1–2 ew per service for auth
custody, per-bot grants, health check, ledger integration, docs and workflow
verification. Cost basis is stated only
where a primary source was read; otherwise U.

| Service | Read actions | Write actions | Concrete path | Auth / custody | Effort | Cost basis | Status |
|---|---|---|---|---|---|---|---|
| Gmail | list/search/get message, threads, labels | send, draft, modify labels | Gmail API (scopes verified: `gmail.readonly`, `gmail.modify`, `gmail.send`, `gmail.compose`, `gmail.labels`) | Google OAuth, refresh token in secret store; per-user consent | 4–7 d | Google API free; Workspace plan U | adapter build |
| Google Calendar | list/get events, free/busy | create/update/delete event, invites | Calendar API v3 | Google OAuth, same custody | 3–5 d | free API | adapter build |
| Drive / Docs / Sheets | list/download/export; read cells | upload, create, update, share (scoped) | Drive + Docs + Sheets APIs | Google OAuth, per-file rights | 6–10 d | free API | adapter build |
| Slack | history, search, channels | post message, update, reactions | Slack Web API + Events/Socket Mode | Slack app scopes; bot token | 3–5 d | plan-dependent U | MCP candidate (catalog pending) |
| Notion | search, read pages/db | create/update pages, append blocks | Notion API or Notion MCP | Notion OAuth/integration token | 2–4 d | free/plan U | MCP candidate (catalog pending) |
| GitHub | issues/PR read, checks | create/comment/update issues, PR review | GitHub REST/GraphQL or MCP | fine-grained PAT or GitHub App | 2–4 d | free/paid plan U | MCP candidate (catalog pending) |
| WhatsApp | inbound messages, statuses | text/media/template send | Meta Cloud API (Graph) | Meta app + phone number id; token in secret store | 5–8 d (base exists) | per-conversation/template fees U | Akeru channel + Akira extension |
| Telephony | call status, recordings | place/hangup/DTMF | Twilio Programmable Voice | account SID + auth token; public callback | 5–8 d | per-minute + number rental U | build |
| Outlook / Teams | mail/calendar read; send | send, invite | Microsoft Graph | Entra app + OAuth | 4–8 d | M365 plan U | build if required |
| Stripe (if used) | charges/customers read | refunds (approval-gated) | Stripe API | restricted key | 2–4 d | per-transaction fees U | build if required |
| Web research (search/fetch) | search, fetch | — | Exa/Context/Firecrawl/Tavily or Akeru WebFetch | API key | 1–3 d | per-query U | Akeru WebFetch exists; WebSearch unavailable |

**Reading the matrix.** None of these is "supported" today as a first-party Akira
connector. The honest status is: substrate exists, actions are designed, adapters are
work. Effort excludes vendor onboarding (WhatsApp/Meta approval can dominate).

### 6.3 Token custody and migration

- Tokens are per-connection, encrypted at rest where available, never in exports.
- A hosted connector's token cannot be reused locally; migration lists
  "re-authenticate" as a required step per service.
- Per-bot grants are default-deny for writes; read scopes can be granted more freely.
- Revocation and rotation are first-class operations with audit.

### 6.4 Browser automation

A labelled fallback only: separate permission, visible "unverified" state, no default for
send/pay/delete, and a human-visible record that a browser (not an API) performed the
action. It is not evidence of connector parity.

---

## 7. Vendor decision checklist (for each integration)

1. Primary docs read today (URL + date) for the exact operations, not the product page.
2. Auth model, scopes, token lifetime, revocation, whether tokens can be held locally.
3. Async/acknowledgement semantics and whether an idempotency key exists.
4. Limits, pricing basis, onboarding/approval time, regional availability.
5. Data handling: retention, training use, PII, recording consent.
6. Failure modes and how to reconcile an unknown outcome.
7. Sandbox/test-account availability.

Until all seven are answered, the integration is `unverified` and may not be presented as
available. This is deliberate: the previous debate's most expensive error was treating a
directory listing as capability.
