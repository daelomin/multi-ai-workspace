# JarvisBot option debate — Round 2 decision brief for HUMAN

**Moderator:** CLAUDE · **Date:** 2026-10-24 · **Status:** awaiting HUMAN's choice. This is a decision brief, not an approved specification. `spec.md` v0.1 is untouched and remains the proposal under debate.

**Inputs read:** README.md, workflow.json, spec.md v0.1, assessment-context.md, and all nine round-2 files (three proposals, three challenges, three responses). There is no `decisions.md`, so no D-style decision IDs exist yet. I cite the project's finding IDs (CHATGPT-1…3, DEEPSEEK-1…10, GROK-1…7) and the four original options as **O1 shim, O2 reconstruction, O3 open-source alternative, O4 DIY primitives**.

**What I did and did not do:** I did not re-fetch sources, install anything, authenticate a connector, or run a test. Every external fact below was retrieved by a reviewer on 2026-10-24 and is labelled **[V]** (reviewer-retrieved primary source or inspected source file), **[M]** (maintainer-reported, not reproduced), **[R]** (reasoning), **[A]** (assumption) or **[U]** (unknown). Nobody in the debate ran any candidate. Every capability claim about Akeru, the shim, noid and the reconstruction is therefore documentation-level only.

**Summary in five lines**
1. All three reviewers independently ranked O3 > O4 > O1 > O2 and kept that order through challenge and response. I give that agreement no weight as evidence. They share one evidence base, and only Akeru was inspected in depth.
2. O1 and O2 are weak primaries for HUMAN's primary goal, on concrete evidence rather than prestige. O2 is weakest.
3. The O3-versus-O4 margin is **unmeasured**. The debate repeatedly removed assets that had been credited to O3 (delegation as resume, a one-layer skills projection, a "bounded" extension surface, the usage page as the requested ledger) and found no evidence that O4 reaches a usable product sooner.
4. My recommendation is O3, led by Akeru with noid as a second candidate, as a spike-first path with named reversal conditions. Confidence is low-to-moderate.
5. HUMAN may choose any option or ask for evidence first. My preference is not approval.

---

## Option comparison

### How to read this section

Criteria are those fixed in README.md: fit to HUMAN's goals, feasibility, effort, maintenance, local control, dependencies, operational risk and reversibility, extended with HUMAN's priorities. Judgments are qualitative. I assign no scores, weights, dollar figures or parity percentages because HUMAN supplied none and no workload, region, entitlement or inventory exists to compute them.

### Facts that decide the comparison

| # | Fact | Label | Source (reviewer-retrieved 2026-10-24) |
|---|---|---|---|
| F1 | Grok Bot connected apps are account-wide; OAuth tokens sit on Cursor's connector backend, not the Bot computer. | V | [computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps) |
| F2 | Grok Bot runs only on Cursor-hosted computers; Cursor manages model selection; there is no customer model picker; usage is recorded as Grok Bot usage, not per model. The connector table names WhatsApp Business and a broad productivity set without action lists. | V | [security](https://docs.x.ai/grok-bot/security) |
| F3 | Official templates package instructions, selected memories/skills and first-party plugins. Custom MCP, scripts and code are excluded; recipients re-authenticate. | V | [templates guide](https://x.ai/bot/guides/templates-for-grok-bot) |
| F4 | Shim: ISC, active (push 2026-10-19), Linux, needs the installed Grok Bot app, Node 22.12+, Docker. Routes: `codex-oauth`, `openai-compatible`, `canned`; fallback only on Codex auth/quota rejection; **isolated `appdata/` profile**; undocumented integration points; user-visible text requires the `SendMessage` tool. No Claude, DeepSeek or Grok-subscription route, and no connected apps, are documented. | V/M | [shim README](https://github.com/luckeyfaraday/grokbot-shim/blob/main/README.md) |
| F5 | Reconstruction: archived, no SPDX licence (`NOTICE.md` asserts no upstream source licence), macOS Apple Silicon, Node 26.5, Xcode CLT, Git LFS, a 0.18.0 snapshot while the product is at 0.75.x. Routes: Cursor, Claude Code, Codex, OpenRouter; DeepSeek not named. Archive date differs between reviewers (Aug 23 vs Aug 28), which is immaterial to the ranking. | V/M | [README](https://github.com/b-nnett/grok-bot-0.18-reconstructed/blob/main/README.md) |
| F6 | Akeru: MIT, T3 Code fork, v0.2.1 (2026-10-01), pushed 2026-10-23, 70 open issues; desktop/web/mobile; README says "Do not push or publish this fork unless Leo asks". Source inspected at `524eb68a293c`. | V/M | [repo](https://github.com/opencoredev/akeru-bot) |
| F7 | Akeru bots: per-bot name, avatar, model, tools; memory files (`USER.md` 1,375, `MEMORY.md` 2,200, `GROUP.md` 2,200 chars) under Akeru home. Saved model is resolved per thread; routing "must fail, not fall back"; "Akeru never switches it for you"; a provider change starts a **fresh provider session**; same-provider backup accounts serve the *next* request. No template/clone library is described. | V | Akeru [bots](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/bots.md), [providers](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/providers.md), [routing runbook](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/operations/provider-model-routing.md) |
| F8 | Akeru **deletes an archived bot automatically 7 days after archiving**; no disable is documented. This conflicts with HUMAN's standing rule that nothing is deleted without an explicit message naming the items. Not exercised. | V | bots doc (CHATGPT-2, DEEPSEEK-7, GROK) |
| F9 | Akeru delegation: work runs in the other bot's chat; result delivered to the requester once; a restart stops running delegated work; **Try again** starts a new card. Exactly-once covers chat delivery, not external side effects. | V | [chats](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/chats.md) (GROK-6) |
| F10 | Akeru skills are per driver. Claude: `ClaudeDriver.ts` calls a `SKILL.md` scanner; selection is sent as `/name` for Claude Code. Grok: shells out to `grok inspect --json`; empty list if the command is missing. Custom API (the DeepSeek preset): `skills: []`. Codex: no skill code in `CodexDriver.ts`; the composer says Codex reads `$name`. The "no CLI needed" sentence is scoped to creating a bot, chatting and titles. | V (source files) | GROK-7 R1–R6, DEEPSEEK-8 |
| F11 | Akeru export excludes secrets, bot memory (separate export), routines, skill assignments, usage history, files, attachments and checkpoints. | V | [data-portability](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/data-portability.md) |
| F12 | Akeru usage: per-bot input/output plus Observer/Reflector tokens, estimates that "are not money spent", plan meters, "Unavailable" for missing data. Observer/Reflector are **memory-curation stages, not an effectiveness observer**. No per-task, per-room or exclusive parent/child view is documented. | V | [usage](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/usage.md) |
| F13 | Akeru channels: WhatsApp **Business Cloud API, direct messages only**, one bot per account, public HTTPS, credentials on the server. No profile/template/registration administration. Voice is in-client, not PSTN. Images: ChatGPT/Grok subscription, stills only. No video. Gmail Connect is verification-pending; custom MCP and own-key Composio are supported. | V | channels, voice, image-generation, plugins docs |
| F14 | DeepSeek tool calls are documented (OpenAI-SDK `tools` round trip). Chat Completions cannot insert tool calls mid-conversation; Anthropic `/messages` and Responses can. DeepSeek's Claude Code and Codex integrations are **API-key** routes, not subscription entitlements. Akeru's DeepSeek preset is an API key plus base URL; its API family is unverified. | V | [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls) (DEEPSEEK's earlier "undocumented" claim was a wrong URL) |
| F15 | noid-one/noid-bot exists: MIT, created 2026-10-20, pushed 2026-10-24, 2 stars; named bots with faces; agent files imported from `~/.agents/agents/`, `~/.pi/agent/agents/`, `~/.claude/agents/`; one shared Docker computer (shared browser logins); per-session model choice and retry on another model; durable tool log that reruns a cut-off call "only if that is safe"; Pi Durable experimental; Linux/macOS. WhatsApp, PSTN, video not documented. | V/M | [README](https://raw.githubusercontent.com/noid-one/noid-bot/main/README.md) (GROK G8, CHATGPT C8) |
| F16 | Skill file convention is a directory with singular `SKILL.md` (Agent Skills spec). Codex scans `.agents/skills`; Claude Code scans `.claude/skills`; Cursor scans several. No candidate is verified to discover a file literally named `SKILLS.md`. | V | [agentskills.io](https://agentskills.io/specification), [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills) |
| F17 | Original-product video and Pages are advertised in changelog v0.75.2 (2026-10-22). Retrieved by CHATGPT and GROK; DEEPSEEK's re-fetch returned HTTP 403. | V (two reviewers) | [changelog](https://x.ai/changelog/bot) |

### Assumptions and unknowns that bound every conclusion

- **[A]** "Phone calls" means PSTN, not in-app voice. "WhatsApp Business account management" means more than direct messages.
- **[A]** An always-on host is acceptable for routines and for WhatsApp's public HTTPS origin. No new spending, hardware or subscription is presumed authorised.
- **[A]** The daily host is Linux (this workspace). That is the main reason O2 loses. If HUMAN has an Apple Silicon Mac, O2's feasibility changes but its archive and licence problems do not.
- **[U]** HUMAN's installed Grokbot connector set and action scope; exported persona text, memories and provider assignments for the named team; whether the shim's isolated profile restores the team, rooms, the Fuel Atlas page and the Weekly bot scorecard routine.
- **[U]** Whether subscription credentials (ChatGPT, Claude, Grok) may be used through a third-party runtime such as Akeru. No reviewer verified vendor terms. If not permitted, O3's cost advantage shrinks to API-key routing.
- **[U]** Live behaviour of everything: tool-call reliability on any backend, skill execution per driver, resume after restart, Akeru's DeepSeek wire format, whether the deletion timer can be disabled, adaptation effort, rebase burden, vendor rates for telephony/WhatsApp/media.

### Fixed-criteria comparison

| Criterion | O1 Official-client shim | O2 Reconstructed build | O3 Open-source alternative (Akeru lead; noid second) | O4 DIY primitives |
|---|---|---|---|---|
| **Fit to the primary goal** (same persistent bots across Codex/Claude/DeepSeek/Grok) | Weak-to-conditional. Bot records live in the vendor app; Cursor chooses models and does not attribute usage per model [V F2]. Documented routes are Codex OAuth plus an OpenAI-compatible endpoint [V F4]. A stable app could in principle hold one identity while inference changes (conceded by DEEPSEEK), so this is an evidence gap, not a logical impossibility. | Partial, stale. Routes include Claude Code, Codex, OpenRouter, Cursor [M F5]; DeepSeek absent; 0.18 snapshot. | Best existing structure: a bot is a local profile with model, tools and memory, independent of provider [V F7]. But provider change starts a fresh session, skills are per driver, and no cross-provider task resume is documented. A structure, not a demonstrated outcome. | Can meet it by design; nothing exists. |
| **Feasibility** | Documented Linux loop [M]; depends on undocumented hooks and the installed app. | Poor on Linux (macOS, Apple Silicon) [V F5]. | Documented, active, cross-platform [M]; not reproduced. | Plausible from public APIs and harnesses; longest build. |
| **Effort** | Low initial integration if the team is present in the isolated profile; otherwise recreate the team. Ongoing repair. | High: port or provenance work first. | Medium to uncertain: install, recreate ten bots and four rooms, re-authenticate connectors, then adapter/controller work for routing, skills, resume, accounting. | Highest: clients, profiles, groups, provider sessions, plugin lifecycle, approvals, accounting, UI. |
| **Maintenance** | Tracks a proprietary app and protocol that can break it. | Frozen archived fork; no upstream. | Pre-1.0 fork of a fast-moving upstream; custom patches; unknown rebase cost. | All owned; no upstream chase. |
| **Local control** | Computer local; connector custody and model selection vendor-side. | Source local; licence ambiguity. | Local state under `~/.akeru`; MIT; provider calls remain remote. | Highest, if designed for export. |
| **Dependencies** | Official app, Node, Docker, Codex login or API key, possibly hosted connectors. | Apple toolchain, pinned artifacts, provider CLIs. | Node, provider accounts; optional Composio/sandboxes; public HTTPS for WhatsApp. | Chosen harnesses/APIs, storage, scheduler. |
| **Operational risk** | Fallback may change models mid-task without proving safe writes; weak tool-callers fail the `SendMessage` loop; profile drift. | Old tool schemas; no licence; archived. | Fresh-session resume; Try-again resubmits work; 7-day auto-delete; over-broad plugin defaults; unknown transport terms. | Custom recovery/permission bugs. |
| **Reversibility** | Stop the shim; original profile preserved; return path for local state unknown. | Separate bundle id; no import/export documented. | Local files, but the main archive omits memory, routines, skills, usage, checkpoints [V F11]. | Open formats if designed; bespoke lock-in possible. |

### HUMAN priorities, assessed for every option

Cell values describe documented or reasoned status. "—" means no evidence and not inferred.

| HUMAN priority | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **Primary goal and route types** (API vs CLI harness vs subscription) | Codex = subscription OAuth via `codex login`; compatible endpoint = API key. Claude/Grok subscriptions not documented. | Mixed CLI logins plus one API key; DeepSeek absent. | Built-in drivers for ChatGPT/Claude/Grok/Kimi/OpenCode Go [M]; DeepSeek = API-key preset. Transport authorisation unverified. DeepSeek's Claude Code/Codex configs are separate API-key harness routes. | Wrap official harnesses or public APIs per backend; no universal subscription credential. |
| **Declaring bots (usability)** | Official create flow and templates, conditional on the shim profile; install and model-file editing first. | Old UI creation; template behaviour undocumented. | Intent sentence → proposed plan → name → first message → profile editor. No template catalog; copying a persona is manual. noid imports agent files as bots (unproven for fidelity). | Best possible flow, after it is built. |
| **Minimise cost** | Setup and repair-heavy; inference via entitled Codex or API; see the cost table below. | Hardware and legal exposure; see the cost table below. | No licence fee; cost is adaptation, fork upkeep and services; see the cost table below. | Highest build cost; no platform subscription; see the cost table below. |
| **SKILLS.md** | In-app skill objects; no file bridge. | Undocumented. | Per-driver: Claude scans `SKILL.md`; Grok via CLI probe; Custom API empty; Codex unverified [V F10]. | Canonical tree projected per harness; each harness still needs an adapter. |
| **Agent library** (templates vs instances) | Official templates (recipes), re-auth required, custom MCP excluded. | Undocumented. | Profiles and isolated per-bot memory exist; reusable named-template library does not [V F7]. | Can separate template defaults from instance state by design. |
| **Autonomy** | Official routines/host loop; routed behaviour unproven. | Unverified. | Routines (procedure approval first), delegation, groups; helpers skip approval steps. | Build. |
| **Deliberation and silence** | `SendMessage` is a publication gate, not judgment. | Unverified. | Boss answers every message by default; watchdog is a stall detector, not deliberate silence. | Build a publish gate. |
| **Collaborative excellence** | Rooms exist; no challenge protocol. | Unverified. | Groups, @mention, delegation cards; no peer-critique feature. | Build. |
| **Observer** | None; new work. | None. | None. Akeru's Observer/Reflector is memory curation [V F12]. | Build; own usage line. |
| **Good-enough routing** | Cursor-managed in the official product; shim has only an auth/quota fallback. | Router for new turns; no quality gate. | Per-bot saved model, fail-closed; no per-task hook; variant dispatch is a second bot (rejected as a solution by all reviewers). | Task field with acceptance criteria and a visible reason, if built. |
| **Safe switching/resume** | Undocumented. | Undocumented. | Chat delivery once; external-write resume custom; fresh session on provider change. | Ledger and checkpoints, if built. |
| **Specialists** (phone, WhatsApp Business, images, video) | Original advertises video and names a WhatsApp Business connector; retention under the shim unverified. | Unverified in the 0.18 snapshot. | WhatsApp DM channel and still images exist; phone, video, Business administration custom. | All custom or API reuse. |
| **Grokbot connector replication** | Hosted tokens stay on Cursor; local routing does not grant them. | Bridge claimed, not verified. | Plugin/MCP/Composio substrate; no hosted tokens; re-authentication required. | Own OAuth or a broker. |
| **Team baseline** (named bots, rooms, pages, routines) | Strongest *if* the isolated profile shows the team; otherwise recreate. | No importer. | Manual recreation of names, groups, routines; no shared-page equivalent. | Build and import by hand. |
| **Lean UI** | Closest visual match when the official window is the workspace. | Old renderer. | Roster, conversation, collapsible panel; separate usage page; "no separate dashboard". Can host compact summaries with drill-down. | Designed against the screenshot. |
| **Task ratings** | Not documented. | Unverified. | Delegation cards are evidence objects, not ratings. | Custom record. |
| **Usage transparency** | Official aggregate; shim attribution unverified. | Local counters, "not an invoice". | Best available: estimates vs bills separated, "Unavailable" labelled; no task/room/parent-child roll-up. | Define the ledger; cannot invent withheld telemetry. |
| **Early triage** | No documented gate. | None. | Question cards and routine approval stop some work; no complexity estimate or readiness check. | Can refuse dispatch until readiness passes, once dispatch exists. |

### Costs, by category (no totals)

| Category | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| One-time setup | Runtime extraction, TLS, multi-GB image pull; legal review of extraction is HUMAN's call; possible team recreation. | Apple Silicon machine, Git LFS, toolchain, bootstrap. | Install, provider logins, recreate bots; WhatsApp adds a Meta app, phone-number id and HTTPS origin; possible deletion-timer and driver patches. | Product build dominates. |
| Hosting | Local Docker; official connectors stay on Cursor if retained. | Local Mac. | Local or controlled host; optional sandboxes/Composio; HTTPS for WhatsApp. | Chosen host; callbacks for phone/WhatsApp. |
| Inference and subscriptions | Entitled Codex route or API; residual Grok Bot plan usage unknown. | Four separate bills. | Subscriptions where a supported transport works, else API keys; DeepSeek always API key; observer/retry/helper turns add usage. | Same provider bills; no platform subscription. |
| Operations/maintenance | Repair after each Grok Bot update. | Frozen; provider CLI breakage. | Fork upkeep, provider drivers, plugin repair, backups. | Everything in-house. |
| Cost uncertainty | Hosted retention; billing split. | Hardware; legal exposure. | Patch and rebase size; transport terms; broker fees. | Build duration and ongoing repair. |

No dollar figure is defensible without workload, region, minutes/messages/media volume and entitlements. The statement "O3 is cheaper than O4" is a reuse hypothesis, not a measurement.

### Grokbot connector capability matrix, every option

**Boundary.** Public sources do not reveal HUMAN's installed connector set, so original capability is stated only where a primary source supports it, and everything else is [U]. "Hosted-U" means retention of the original hosted connector under that option is unproven. Preserving a UI or an MCP tool bridge is not possession of hosted OAuth registrations or tokens (F1). Statuses: **native** (documented, untested), **reuse** (a public API/MCP exists; HUMAN supplies credentials; wiring untested), **custom**, **not supported** (no documented support for the stated operation, not proof of impossibility), **unverified**. No parity percentage is claimed. Evidence is reviewer-retrieved 2026-10-24; Twilio, Google, Notion, Slack, GitHub and X API rows were retrieved by CHATGPT and carried, not re-fetched by the others.

**Shared service catalog** (candidate, actions, auth/hosting, cost basis; identical across options because the vendor, not the client, sets them):

| ID | Original capability (evidence) | Candidate and actions covered | Authentication and hosting | Setup / ongoing cost basis | Evidence |
|---|---|---|---|---|---|
| S1 | Phone/PSTN: not documented in fetched original docs [U]; voice chat is talk-to-the-bot | Twilio Programmable Voice: read call status, dial/control. A conversational agent also needs audio, speech/model loop and callbacks. | Twilio account, number, public callback | Number onboarding, audio adapter; number rental, per-minute, speech/inference, hosting. Rates unverified. | [Twilio Calls](https://www.twilio.com/docs/voice/api/call-resource) |
| S2 | WhatsApp Business connector named (F2); actions [U] | Twilio WhatsApp or Meta Cloud API: send/receive messages, media, templates where implemented | Meta app/token/phone ID or BSP; public HTTPS | Sender registration, webhook upkeep; messaging/template fees. Unverified. | [Twilio WhatsApp](https://www.twilio.com/docs/whatsapp); Akeru channels doc |
| S3 | WhatsApp Business **administration**: action set [U] | Twilio Senders API (sender onboarding/status); Meta Business Management API candidate for profile, templates, verification. Full administration not established. | Meta business permissions and verification; provider control plane | Admin onboarding, manual approvals; fees unknown. | [Senders API](https://www.twilio.com/docs/whatsapp/api/senders); Meta page failed to load for two reviewers |
| S4 | Images: advertised in changelog (F17) | xAI Imagine image API (generate/edit); Akeru ChatGPT/Grok subscription tool | API key, or subscription transport (entitlement unverified); cloud | Adapter and output storage; allowance or API charges. | [xAI images](https://docs.x.ai/developers/model-capabilities/images/generation); Akeru image doc |
| S5 | Short movies: advertised in changelog (F17) | xAI video API: submit/status/result. A finished movie may need scripting, audio and editing. | API key; async jobs; durable storage | Job-tracking adapter; per-second charges and retries. Unverified. | [xAI video](https://docs.x.ai/developers/model-capabilities/video/generation) |
| S6 | Gmail: named (F1, F2); actions [U] | Gmail API read/search; draft/send/modify under scopes | Google OAuth registration and refresh, or authorised broker | Scopes/adapter; broker or Workspace costs. | [Gmail API](https://developers.google.com/workspace/gmail/api/guides); Akeru Gmail Connect verification-pending |
| S7 | Google Calendar: named (F2); actions [U] | Events list/get/insert/update; recurrence and timezone need tests | Google OAuth | OAuth, recurrence testing | [Events](https://developers.google.com/workspace/calendar/api/v3/reference/events) |
| S8 | Drive/Docs/Sheets/Slides: named (F2); actions [U] | Drive list/download/upload/permissions; Docs/Sheets/Slides editing needs their own APIs | Google OAuth, per-file rights | OAuth, file handling | [Drive](https://developers.google.com/workspace/drive/api/guides/about-sdk) |
| S9 | Notion: category documented (F1) | Official Notion MCP: search/read/create/update | Notion OAuth; vendor-hosted MCP | Authorise and validate tools | [Notion MCP](https://developers.notion.com/guides/mcp/mcp-supported-tools) |
| S10 | Slack: category documented (F1) | Slack Web API history/post/update; Events API or Socket Mode for incoming events | Slack app and scopes | App, scopes, event setup | [Slack Web API](https://docs.slack.dev/apis/web-api/) |
| S11 | GitHub: named (F2); actions [U] | GitHub REST Issues: read/create/update; PR/code separate | Fine-grained token, App or OAuth | Least-privilege setup | [Issues API](https://docs.github.com/en/rest/issues) |
| S12 | X: public read verified; authenticated actions [U] (F1) | X API scoped reads/writes | Developer app, bearer/user OAuth; not inherited from app login | Developer access, usage costs [U] | [X platform](https://docs.x.com/overview) |
| S13 | Other named hosted connectors: Origin, Google Ads, Outlook mail/calendar, OneDrive, Teams, Stripe Link, Tailscale, QuickBooks Online, Workday, Zoho CRM/Books/Desk (F2) | Candidate vendor APIs exist for many (Microsoft Graph, Stripe, QuickBooks, Zoho, Tailscale); contracts not fetched | Each vendor's OAuth/tenant | All [U] | Names and hosts from the security page only |

**Per-option status** (each cell is what that option adds on top of the catalog row):

| ID | O1 Shim | O2 Reconstruction | O3 Akeru (noid: unverified on every row) | O4 DIY |
|---|---|---|---|---|
| S1 Phone | Custom adapter and audio bridge; hosted: not supported documented | Custom | Custom MCP/API. In-client voice is not PSTN. | Reuse Twilio API; custom conversation loop |
| S2 WhatsApp messaging | Hosted-U; custom if rebuilt | Hosted-U; custom | **Native** (Cloud API, DMs only, one bot per account) [M]; media/templates [U] | Reuse API; custom webhook/channel |
| S3 WhatsApp administration | Custom subset; **not supported** as full administration | Custom subset; not supported | Custom subset; DM channel is not administration; **not supported** | Reuse/custom subset; full [U] |
| S4 Images | Hosted-U; custom API otherwise | Unverified in 0.18; custom API | **Native** ChatGPT/Grok stills [M]; xAI API custom | Reuse API; custom tool |
| S5 Movies | Hosted-U; custom job workflow | Unverified in 0.18; custom | **Not supported** natively; custom job adapter | Reuse API; custom job store |
| S6 Gmail | Hosted-U; custom independent API | Hosted-U; custom | Verification-pending plugin; custom API or Composio | Custom OAuth |
| S7 Calendar | Hosted-U; custom | Hosted-U; custom | Reuse/unverified via broker; custom API | Custom |
| S8 Drive and Docs | Hosted-U; custom | Hosted-U; custom | Reuse/unverified via broker; custom API | Custom |
| S9 Notion | Hosted-U; reuse own MCP if the host accepts it | Hosted-U; reuse via the claimed bridge | Reuse (custom MCP lifecycle) | Reuse MCP; custom client |
| S10 Slack | Hosted-U; custom | Hosted-U; custom | Native messaging channel; broader tools reuse/unverified | Custom |
| S11 GitHub | Hosted-U; custom | Hosted-U; custom | Reuse via broker or custom | Custom |
| S12 X | Public read retention unverified; custom API | Unverified; custom | Custom | Custom |
| S13 Others | Hosted-U | Hosted-U | Custom/unverified | Custom/unverified |

**Reading the matrix.** No option natively covers phone, Business administration or movies. O3 has the only documented native WhatsApp messaging and still-image paths. O1 has the only possible route to *retained* hosted connectors (S2, S4, S5, S6–S13), and that possibility is unverified. Every other cell is a custom integration with HUMAN's own credentials. The O3 and O4 columns share the same Twilio, Meta, Google and xAI dependencies; the client changes the wiring burden, not the vendor's cost or onboarding.

---

## Debate assessment

### Process notes

- The three independent proposals converged on O3 first and O4 second. They then shared sources through challenge and response, so their later agreement is not independent confirmation.
- The reviewers were generous with concessions. Almost every material challenge landed. That is a good sign for the debate's honesty and a warning that the evidence base shrank rather than grew: the net effect of the debate was to **remove** claimed O3 assets and **lower confidence**, not to produce a measured O3 advantage.
- Nobody ran a spike. Every "unresolved" item below is an untested claim, not a negative result.

### Challenge trace

Legend: **Conceded** = the challenged party accepted it. **Holds** = the objection stands on evidence. **Rebutted** = answered with evidence. **Partly** = partly accepted. **Open** = unresolved, a test is named.

#### Findings raised in proposals and challenges

| ID | Raised by | Claim | Outcome | My judgement |
|---|---|---|---|---|
| CHATGPT-1 | CHATGPT | Spec's "Windows-first" description of the reconstruction is unsupported; the identifiable repo is macOS and archived | Accepted by all three. GROK-3 and DEEPSEEK-2 independently made the same point. | **Holds.** Verified in F5. |
| CHATGPT-2 | CHATGPT (proposal; filed in challenge) | Akeru's 7-day automatic deletion conflicts with the no-deletion rule | Accepted by all. DEEPSEEK-7 adds that no disable is documented, so the patch is part of O3's cost. CHATGPT concedes the point and accepts that a fixture or static review, not a real archive, must test it. | **Holds. A hard adoption condition for Akeru**, though not for O3 as a class. |
| CHATGPT-3 | CHATGPT | DEEPSEEK's "O1 needs no migration" is unsupported because the shim uses an isolated profile | Conceded by DEEPSEEK; GROK agreed. | **Holds.** O1's usability advantage is conditional on a test. |
| DEEPSEEK-1 | DEEPSEEK | Shim-first cannot meet provider independence | CHATGPT: overstated; a stable app could hold identity while inference changes. DEEPSEEK conceded and narrowed to documented routes, Cursor-managed model/usage, hosted connector custody and the isolated profile. GROK agreed. | **Partly holds.** The narrow grounds suffice to rank O1 below O3; the "structurally impossible" wording does not. |
| DEEPSEEK-2 | DEEPSEEK | Reconstruction is archived, unlicensed, macOS | Accepted by all. | **Holds.** |
| DEEPSEEK-3 | DEEPSEEK | O3 bundles two candidates of very different maturity | CHATGPT: partly right, but age/stars are wrong weights; noid is real and relevant. DEEPSEEK conceded the weights. | **Partly holds.** Candidate-level evidence is needed; maturity alone does not decide. noid belongs in the trial. |
| DEEPSEEK-4 | DEEPSEEK | API / harness / subscription conflated | Accepted by all; GROK-4 makes the same point. CHATGPT corrected one detail: Akeru's Claude route is described as a built-in runtime, not an installed CLI. | **Holds.** Every route must be named by driver and auth class. |
| DEEPSEEK-5 | DEEPSEEK | The proposal has no connector, usage, skills or observer assessment | Accepted. The reviewers' matrices are now the input. | **Holds.** Addressed in this brief; the installed connector inventory is still missing. |
| DEEPSEEK-6 | DEEPSEEK (challenge) | DeepSeek tool calling is undocumented | **Rebutted by GROK-5** and conceded by DEEPSEEK: the cited URL was a redirect; `tool_calls` is documented. The *resume* risk survives: Chat Completions cannot insert tool calls mid-conversation, and Akeru's preset API family is unknown. CHATGPT adds that the restriction is about client-inserted calls, not all replay. | **Partly holds.** Tool use is documented, not demonstrated. Wire format and live reliability are open. |
| DEEPSEEK-7 | DEEPSEEK | Auto-deletion has no documented disable | Conceded by all. | **Holds** (same as CHATGPT-2). |
| DEEPSEEK-8 | DEEPSEEK | "No CLI needed" conflicts with the Claude Code skill dispatch | GROK-7 resolved part of it from source: it is a *mix*. Claude scans files, Grok shells out, Custom API is empty, Codex is unverified. CHATGPT had not found a `discoverClaudeSkills` reference in `AgentController.ts`/`AkeruMastraHarness.ts` (not a whole-tree audit); GROK found it in `ClaudeDriver.ts`. | **Holds.** Unresolved: whether `ClaudeDriver.ts` is the path used by the no-CLI built-in runtime. |
| DEEPSEEK-9 | DEEPSEEK | GROK marked O2 media "not supported" from README silence | Accepted by GROK. | **Holds**; ranking unaffected. |
| DEEPSEEK-10 | DEEPSEEK (response) | GROK's 2,000-character excerpt is not on the chats page | GROK showed it is on the bots page as a card display rule, not prompt truncation. | **Resolved.** The structural point (delegation is another bot) stands independently. |
| GROK-1 | GROK | Spec is truncated and recommends a three-track hybrid | CHATGPT: the truncation is real, but missing low-level specs are not independent majors in an options phase and reviewers cannot withdraw the hybrid for HUMAN. GROK conceded. | **Partly holds.** The input is incomplete, and the §1 hybrid is not one of the four options. Reviewers recommend against it. It is not withdrawn. |
| GROK-2 | GROK | Three named tools could not be found | **Rebutted** by CHATGPT C8: noid exists. GROK withdrew it as evidence of absence. `grokbot-local-agent` and `grok-bot-analysis` remain unverified. | **Does not hold** for noid. |
| GROK-3 | GROK | Reconstruction platform and archive | Accepted by all. | **Holds.** |
| GROK-4 | GROK | "OpenAI-compatible" confuses provider, harness and subscription | Accepted; DEEPSEEK-6's route detail refines it. | **Holds.** |
| GROK-5 | GROK | DeepSeek tool-calling citation and resume rule | Accepted by DEEPSEEK; CHATGPT limited the inference to client-inserted calls. | **Holds** with CHATGPT's qualification. |
| GROK-6 | GROK | Delegated-result delivery is not safe resume of external work | Conceded by all three. | **Holds. This materially lowers O3's resume score.** |
| GROK-7 | GROK | A projected `SKILL.md` does not reach Akeru's Grok probe or Custom API catalog | New in the response pass; no peer has answered it. It rests on inspected source. | **Holds on its evidence; unrebutted, not yet challenged.** The live menu test is still required, and Codex is unverified. |

#### Strategic challenges (not finding IDs)

| Challenge | Direction | Outcome |
|---|---|---|
| "Bounded extension" is premature; per-task routing, skills, resume and accounting are interconnected runtime work | DEEPSEEK/GROK → CHATGPT, DEEPSEEK | **Conceded by all.** Evidence: no per-task hook in the routing runbook; fail-closed by design; fixes belong at the adapter boundary (F7). |
| "Beside core versus fork" is the wrong test; compare retained behaviour and who owns retries | CHATGPT → GROK, DEEPSEEK | **Partly conceded.** DEEPSEEK keeps a "no second state store / no second retry authority" threshold; CHATGPT calls "no core edits" too rigid. The disagreement is only about how to state the threshold. |
| Variant dispatch ("stronger Natalia") is a second bot, not the same persistent bot | GROK → DEEPSEEK | **Conceded and withdrawn** by DEEPSEEK; CHATGPT agreed. All reviewers reject variant dispatch as a way to meet the primary goal. |
| Exactly-once delegated delivery was counted as resume | GROK → DEEPSEEK/CHATGPT | **Conceded.** CHATGPT notes its proposal had not claimed it. |
| Specialists are not a tie: official video and a named WhatsApp Business connector are advertised | CHATGPT → DEEPSEEK, GROK | **Conceded.** The advertisement is verified for WhatsApp (F2); video rests on the changelog (F17). Retention under the shim is unverified. |
| Shim is third on "documented routes" rather than "identity is vendor-held" | CHATGPT → DEEPSEEK | **Conceded.** |
| One-year cost horizon is not HUMAN's | CHATGPT → DEEPSEEK | **Conceded and withdrawn.** |
| Usage page is "best visibility" but not the requested ledger | DEEPSEEK → GROK | **Conceded.** |
| Option 2 would only be reopened by a maintained, licensed fork on the right host | CHATGPT | **Accepted as a condition** by the others; it is not on the table today. |
| Option 1 can rise without a priority waiver if a trial shows team restoration plus supported switching with state preserved | CHATGPT → GROK | **Conceded** by GROK. |

### Who conceded what, in short

- **DEEPSEEK** conceded the most: bounded extension, variant dispatch, shim "structural" failure and "no migration", the "not advertised" wording, DeepSeek "undocumented", exactly-once delivery as resume, age/stars weighting, the one-year horizon. DEEPSEEK did not concede that O3 ranks below O4, and it added a precise threshold for that reversal.
- **GROK** conceded noid, the hybrid's "withdrawn" status, a single skills projection layer, the usage page as the ledger, option 2 media wording, the "specialists are a tie" claim, the "beside core vs fork" test, and the "2,000-character" detail. GROK made the decisive source-level skills finding (GROK-7).
- **CHATGPT** conceded identification of noid, unbounded confidence in Akeru's cost advantage, and that the original product advertises WhatsApp/video. It corrected others on shim migration, DeepSeek's insertion rule, rigid "no core edits" thresholds, and not mapping a stronger-model delegation to the same bot.

### Objections that hold

1. **The central O3 assumption is untested.** A neutral skill layer, per-task routing on one bot, external-write resume, parent/child accounting, deletion suppression and a readiness gate are runtime changes. At best they are adapter-level patches. At worst they are two retry authorities.
2. **Akeru's deletion timer** conflicts with a standing HUMAN rule, and no disable is documented.
3. **Delegation is not resume.** A restart stops delegated work and Try again resubmits it as a new card.
4. **Skills are per driver.** The Custom API (DeepSeek) catalog is empty; Grok depends on its CLI; Codex is unverified.
5. **O1 and O2 fail on documented routes and platform**, not on a general dislike of proprietary UIs.
6. **No candidate has a template library, shared result pages, a task-rating record, an effectiveness observer, or a complexity/readiness gate.**
7. **Subscription-transport permission is unverified for every subscription route**, which bears on the cost case for O3.

### Objections rebutted or withdrawn

- "DeepSeek tool calling is undocumented" (wrong URL).
- "O1 needs no migration" (shim uses an isolated profile).
- "Original product does not advertise WhatsApp/video."
- "noid cannot be found."
- "Shim structurally cannot hold identity."
- "Variant dispatch meets the primary goal."
- "2,000-character excerpt on the chats page."
- "Missing low-level specs are an independent major defect before a path is chosen."
- "The hybrid is withdrawn" (reviewers cannot withdraw it for HUMAN).

### Unresolved

| Item | Why it matters | Test that resolves it |
|---|---|---|
| Size of the Akeru adapter/controller patch for routing, skills, resume, accounting, deletion | It is the whole O3-over-O4 margin | Continuity and restart spike (see Preferred choice) |
| Whether `ClaudeDriver.ts` skill scanning is used by the built-in no-CLI runtime; Codex skill source | Decides how much skills work is per driver | Menu and execution test per driver |
| Akeru's DeepSeek preset API family and live tool reliability | Decides whether DeepSeek is tool-capable in O3 | Tool transcript test on preset vs Anthropic/Responses route |
| Whether the shim's isolated profile restores the team and connectors | Decides O1's bridge value | Shim bridge test on a copy, preserving both profiles |
| noid's continuity, safe rerun and skills, on the four backends | A second O3 candidate with a possibly better durability story | noid trial on Linux |
| Subscription transport permission for third-party runtimes | Bears on cost for O3 | Vendor-term review by HUMAN |
| HUMAN's actual connector inventory and persona/memory exports | Needed for any parity or migration claim | HUMAN supplies |
| Reconstruction archive date (Aug 23 vs 28) | None for the ranking | None needed |

---

## Preferred choice

### Primary recommendation: **O3 — Open-source alternative**, with **Akeru as the lead candidate** and **noid as a second candidate inside the same option**, adopted **spike-first**.

This is one primary path. I do not recommend running the shim or the reconstruction in parallel, and I do not combine O3 and O4 silently. If a candidate fails the gates below, the fallback is a separately chosen O4, not a quiet blend.

**Compelling reasons**

1. **It is the only option whose structure already matches the primary goal.** A bot is a local profile (name, avatar, model, tools, per-bot memory) separate from the provider connection, with built-in drivers for ChatGPT/Codex, Claude and Grok plus a DeepSeek API preset (F7). That storage separation is what "bot identity must not be tied to a provider" needs. O1 keeps identity in a vendor app with Cursor-managed models; O2 is an archived macOS snapshot.
2. **It supplies the undifferentiated, expensive layer under MIT on Linux.** Clients, profiles, groups, routines, delegation cards, plugin/MCP lifecycle with honest health status, memory files, still images, a WhatsApp DM channel and a usage page that separates estimates from bills are all documented. They map directly to HUMAN's usability, lean-UI and usage-visibility priorities, and O4 would have to build every one of them before reaching any differentiator.
3. **The gaps are known and named.** The debate converted vague worries into specific, testable ones: per-driver skills (F10), fail-closed routing (F7), restart behaviour (F9), export exclusions (F11), deletion timer (F8), DeepSeek wire format (F14). A path whose weaknesses are enumerated is easier to decide on than one whose weaknesses are unknown.
4. **It keeps the failure path cheap.** If the spike shows Akeru needs a second retry authority, HUMAN can move to O4 having spent a bounded effort, with a clear definition of what O4 must provide.

**What O3 does not do.** Stock Akeru does not meet the primary goal. It has no neutral skills, no per-task routing on one bot, no safe external-write resume, no effectiveness observer, no task-rating record, no triage gate, no shared pages, no PSTN calling, no video, and no Business administration. Choosing O3 is choosing a base to test and extend.

**Strongest counterargument.** If per-task routing, neutral skills, external-write resume and parent/child accounting each require edits to Akeru's controller and accounting paths, then what O3 retains is a client, profiles, groups, MCP switches, images and DMs. A thin DIY composition around the official Codex and Claude Code harnesses plus MCP libraries, with one file-based bot record and an action ledger, could then be the smaller long-term burden, and it would avoid inheriting a pre-1.0 fork with a "do not publish" README note and an automatic-deletion behaviour. Nobody measured where that threshold lies. GROK and DEEPSEEK stated the reversal condition as "a second authority over retries, dispatch and accounting"; CHATGPT stated it as retained behaviour versus ownership. I treat these as the same concern worded differently.

**Why the closest alternative (O4) loses, narrowly.** O4 is the only path that can implement every priority exactly: a canonical `SKILL.md` library, a task route record with acceptance criteria, an external-write ledger, exclusive parent/child usage, reviewable observer proposals, and a clean template/instance split. It loses on current evidence only because (a) it must first build the platform surface above, (b) the debate found no evidence that a thin composition reaches a usable, friendly declaration-to-result experience sooner, and (c) HUMAN's usability and cost priorities favour reuse when reuse is real. That is an effort hypothesis, not a measured cost comparison. The debate narrowed the gap, because O3 supplies few differentiators for free.

**Why O1 and O2 lose.** O1 offers the familiar UI and a possible retained connector path, but Cursor chooses the models and does not attribute usage per model, the shim's documented routes are narrower than the primary goal, and its profile is isolated. It remains valuable as a **bridge test** and UI reference. O2 is archived, unlicensed, macOS-only and a 0.18 snapshot. Nothing in the debate changes that on this Linux host.

**Confidence: low-to-moderate** that O3 beats O4 on total delivery for HUMAN's full priority set. **Moderate-to-high** that O1 and O2 are the wrong primaries today. **Low** that any candidate, unmodified, meets neutral skills, quality routing, safe resume, phone, video, shared pages, task ratings and the triage gate together.

### What would change this recommendation

Each test is bounded, uses stubs or test accounts, and requires no real archive, delete, phone call or customer message. None has been run.

| # | Test | Result that moves the ranking |
|---|---|---|
| 1 | **Continuity and restart.** One named bot, one private memory fact, one procedure, one goal, one `SKILL.md`, one partly completed task moves Codex → Claude → DeepSeek → Grok and back. A stub service accepts a write before acknowledgement; restart; retry. Record driver, auth class, preserved state, ledger count. | O4 first if Try again repeats the write and a short harness wrapper with a ledger passes, or if the fix needs a second orchestrator beside Akeru's controller. |
| 2 | **Per-task stronger model on one bot**, without a second bot and without hand-editing the profile. Record files changed. | O4 gains if only controller edits work. O3 holds if a supported mechanism shares memory and ledger. |
| 3 | **Skills per driver.** Unique bundle in each root; check menu and execution on Claude, Codex, Grok, DeepSeek; repeat after a provider switch. | O4 gains if each driver needs a standing patch that will not rebase. |
| 4 | **DeepSeek tool transcript** with a prior assistant tool call on Akeru's preset vs Claude Code at DeepSeek's Anthropic base URL. | Label the preset text/single-shot if only the harness route works; O4 gains if the adapter exceeds a thin harness wrapper. |
| 5 | **Deletion safety.** Find a documented setting or bounded patch (static review or synthetic clock only). | Akeru is out if the timer needs a standing fork HUMAN will not carry; another O3 candidate or O4 replaces it. |
| 6 | **Full export and restore** including memory, routines, skill assignments, usage, checkpoints, on a second environment. | Reversibility is weaker than "local files" if it fails; moves toward O4. |
| 7 | **noid trial** on Linux: agent-file import, per-session model change, one stub write surviving. | noid replaces Akeru as lead if it reproduces; O3 remains the option. |
| 8 | **Shim bridge test** on a copy: does the isolated profile show the ten named bots, four rooms, Fuel Atlas page, scorecard routine, and do hosted connectors work? | A positive result makes O1 a credible short-term bridge; it becomes primary only if supported switching preserves bot, skills and one external write. |
| 9 | **Template-to-two-instances usability trial** with a non-developer. | A competing path that does this with less setup can rise. |
| 10 | **Triage trial.** One complex, ambiguous integration task run three ways (advanced model; advanced spec plus simpler implementer after the readiness check; simpler only if ready), counting planning, tools, validation, rework. | Failure to attach the gate to every dispatch path weakens O3. |
| 11 | **Subscription terms** for third-party runtimes (HUMAN review). | If forbidden, O3's cost advantage shrinks to API keys; recheck against a thin CLI wrapper. |

HUMAN-side changes that would also move the ranking: a connector inventory showing deep dependence on hosted connectors (raises O1 as a bridge); a decision that exact UI and team continuity outranks provider independence (that makes O1 a legitimate choice, but it should be recorded as a deliberate trade, not inferred); an Apple Silicon host and a licence decision (reopens O2, though not its archive status).

---

## Decision for HUMAN

**HUMAN, please choose one of the following. I have not decided for you.**

1. **Select O1** (official-client shim).
2. **Select O2** (reconstructed local-first build).
3. **Select O3** (open-source alternative). My preference, with Akeru as the lead candidate and noid as second, spike-first.
4. **Select O4** (DIY primitives).
5. **Request more evidence** before choosing. The cheapest evidence is tests 1, 3, 5 and 8 above, plus your inputs below. This may be the better choice if the O3-versus-O4 margin matters to you.
6. Amend an option or ask for another debate round.

**An AI preference is not HUMAN approval.** The three reviewers and I agree on a ranking, and none of us has authority to select an implementation path. Nothing proceeds to full specs until you record a choice. If you select the proposal's §1 hybrid (shim MVP plus reconstruction plus open-source fallback), that is your decision to make, and I would flag it as two state stores rather than a fifth option.

**Information from you that would reduce the biggest unknowns** (all optional):
- Your installed Grokbot connector list and which actions the team really uses.
- Whether persona text and memories for the ten named bots can be exported or retyped.
- Your target host (Linux, macOS Apple Silicon, always-on or laptop).
- Whether you accept using subscription logins through a third-party runtime, or want API keys only.
- Whether you will accept a standing patch to disable Akeru's 7-day auto-delete, given your no-deletion rule.
- Which WhatsApp Business administration operations you actually need beyond messaging.

---

## After HUMAN chooses

If HUMAN selects **O3**, these are the topics for the full implementation specs. Other selections get their own topic list; I do not write any of these specs now, and `spec.md` stays unchanged until then. Record the choice and constraints in `decisions.md`, set `workflow.json` to `template: spec-review`, `phase: specification`, with `human_choice`, as README.md describes.

1. **Candidate selection and gating.** The comparison spike (tests 1–7 and 9–10), pinned revisions of Akeru and noid, pass/fail criteria, and the O4 fallback trigger.
2. **Canonical bot model.** Persona, goals, procedures, skills, memory and task state stored independently of any provider session; template defaults versus per-instance state; deletion-safety and export/restore, including items outside the main archive.
3. **Agent library.** Named templates, instance creation, appearance, attitude, dependency declaration, isolation checks, import of the ten named bots without inventing unseen personas.
4. **Backend routes.** Per backend: API, harness or subscription; auth class; tool-call behaviour; transport-permission evidence; DeepSeek wire format.
5. **Skills.** Canonical `SKILL.md` library, per-driver discovery and registration, configuration, dependencies, and the literal-`SKILLS.md` question.
6. **Task routing and triage.** Acceptance criteria per task class, readiness check, route and reason fields, escalation, separate handling of credit exhaustion, rate limits, authentication failure and poor capability, re-triage rules. No invented thresholds.
7. **Switching and safe resume.** Checkpoints, action ledger and idempotency, tool/schema/context compatibility, user-initiated versus automatic switching, credit visibility limits.
8. **Collaboration, silence and observer.** Publish gate and silence policy, peer-challenge procedures, observer scope, proposal-review flow that never silently edits goals or personas, and observer cost visibility.
9. **Task ratings.** Rating record, reviewer identity, criteria, evidence links, disagreement and correction, task versus bot reputation.
10. **Usage accounting.** Attribution by bot, model, provider, room, task, parent and child; exclusive versus rolled-up totals; measured, estimated, subscription and unavailable labels.
11. **Specialists.** Phone, WhatsApp messaging versus named administration operations, images, short movies: adapters, credentials, hosting and callbacks, idempotency for side effects.
12. **Connector inventory and replication.** The user-supplied inventory, per-service read/write coverage and authentication, with no parity percentage without a defined inventory.
13. **UI.** Screenshot-based lean workspace, compact summaries with drill-down for usage, ratings and triage, shared result pages.
14. **Migration and operations.** Team and room recreation, routine recreation, backups, update and rebase policy, security and approvals, and acceptance tests.

Result: complete
