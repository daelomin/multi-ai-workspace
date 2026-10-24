# DEEPSEEK — round 2 independent option proposal

This is the independent proposal pass. I read `README.md`, `workflow.json`, `spec.md` v0.1, `assessment-context.md`, the round-1 DEEPSEEK and CHATGPT reviews, and `CHANGELOG.md`. I did **not** read any round-2 peer file. No candidate was installed, no connector was authenticated and no paid call or media job was made. All URLs below were fetched on **2026-10-24**.

`spec.md` v0.1 still ends at line 110 inside the unclosed Mermaid fence in §6; there is no `decisions.md`. I therefore treat the proposal as a list of four alternatives, not an implementation baseline. The proposal's initial shim-first recommendation is provisional.

## Method and evidence labels

- **V** — fetched primary source; the claim is quoted or directly paraphrased from it.
- **M** — repository metadata from the GitHub API (licence, archive state, dates, counts).
- **R** — reasoning from the evidence.
- **A** — assumption I am making; not verified.
- **U** — unknown or unverified; confidence is limited accordingly.

Vendor documentation is maintainer-reported until reproduced. I did not reproduce any candidate claim. I assign no numeric scores and no dollar figures; cost statements describe structure and what remains unknown.

## Verified facts

| ID | Claim | Source | Label |
|---|---|---|---|
| V1 | Grok Bot connected apps are account-wide; OAuth tokens are held on **Cursor's connector backend**, not on the Bot computer; app logins stay off the computer. | [docs.x.ai computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps) | V |
| V2 | A Grok Bot template packages instructions, relevant memories, skills and first-party plugins. Custom MCP servers, scripts and custom code are excluded; recipients reinstall/authenticate included plugins. Guide dated **8 Sep 2026**. | [x.ai templates guide](https://x.ai/bot/guides/templates-for-grok-bot) | V |
| V3 | Grok Bot skills are reusable task instructions shared across bots and may need connected-app access. Routines schedule or event-trigger one bot; event triggers use Cursor account integrations separate from Slack/GitHub apps. Limits: 50 routines/bot, 20 run records, schedules ≥5 minutes. | [docs.x.ai skills-routines](https://docs.x.ai/grok-bot/skills-routines-and-automations) | V |
| V4 | `grokbot-shim` is **ISC**, active (last push 2026-10-19), Linux only, requires the installed Grok Bot desktop application, Node 22.12+, Docker, and either `codex login` or an OpenAI-compatible API key. It translates the app's inference protocol. User-visible replies require the `SendMessage` tool; assistant text is private working text. It relies on "undocumented integration points"; the README documents an optional fallback for Codex auth/quota rejection. | [shim README](https://github.com/luckeyfaraday/grokbot-shim/blob/main/README.md); GitHub API | V/M |
| V5 | `grok-bot-0.18-reconstructed` is **archived**, has **no licence** (`spdx_id: null`), was created and last pushed on **2026-08-23**, and requires macOS Apple Silicon, Node 26.5.x, Xcode CLT and Git LFS. It routes Cursor, Claude Code, Codex and OpenRouter and claims MCP/plugin tool execution. | [reconstruction README](https://github.com/b-nnett/grok-bot-0.18-reconstructed/blob/main/README.md); GitHub API | V/M |
| V6 | **Akeru** is **MIT** (copyright T3 Tools Inc), a fork of T3 Code, **v0.2.1 released 2026-10-01**, active (last push 2026-10-23), 106 stars, 70 open issues. Desktop macOS/Windows/Linux; CLI Node `^22.16 || ^23.11 || >=24.10`; background service Linux/macOS. | [repo](https://github.com/opencoredev/akeru-bot); [install](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/install.md); GitHub API | V/M |
| V7 | Akeru has a built-in runtime for ChatGPT, Claude, Grok, Kimi For Coding and OpenCode Go (subscription/account login), plus **Custom API** presets including **DeepSeek**, OpenRouter, Groq, Together, Mistral, Fireworks, LM Studio, Ollama and vLLM (API key and/or base URL). It supports same-provider **backup account failover**; it does **not** switch a bot's model/provider automatically. | [providers](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/providers.md); [bots](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/bots.md); [routing internals](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/operations/provider-model-routing.md) | V |
| V8 | Akeru bots have per-bot avatar, name, label, description, model, voice and enabled tools; the model lives in the bot's settings. Changing provider starts a fresh provider session with the **same enabled tool set**. "A bot keeps its model when that model stops working. Akeru never switches it for you." | [bots doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/bots.md) | V |
| V9 | Akeru **groups** are chats with two or more bots, a Boss who answers by default, `@BotName` routing, and delegation cards showing state, elapsed time, tokens, retries and deadlines. Delegated work is child-thread linked, delivered exactly once, retried as a new record; group results are posted. Groups are bot-only; max three concurrent delegated tasks per chat. | [chats doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/chats.md); [delegation internals](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/internals/delegation.md) | V |
| V10 | Akeru memory is per bot: Markdown `USER.md` (1,375 chars), `MEMORY.md` (2,200), `GROUP.md` (2,200), plus durable facts scoped chat/bot/project/workspace. It lives on the environment server under Akeru home; export/import uses a versioned JSON archive with checksums. The docs do not state whether memory survives a provider switch, but the storage is provider-agnostic. | [memory doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/memory.md) | V |
| V11 | Akeru **skills are provider-scoped**: "The list shows the skills of the provider the chat is using." Sources are App, Repo, Project, Personal, System or Provider. Claude selection is sent as a trailing `/name`; Codex reads `$name` natively. | [composer doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/composer.md) | V |
| V12 | Akeru plugins support public/local plugins, OAuth/keys, Composio, and **custom MCP servers**; tools are enabled per bot; provider change preserves the tool set. "Health stays Not checked until a real request succeeds"; an enabled plugin is not proof it works. Mobile cannot manage plugins. | [plugins doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/plugins.md) | V |
| V13 | Akeru usage shows plan meters, provider totals, an activity chart, **per-bot input/output/Observer/Reflector/reserved tokens**, and an **estimated cost** that "is not money spent". No standalone cached-token or reasoning-token figure, no conversation-level view. Missing data reads "Unavailable", not zero. | [usage doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/usage.md) | V |
| V14 | Akeru channels are per-bot external messaging. Slack/Discord support DMs and mentions; Telegram, iMessage and WhatsApp support **DMs only**; a messaging account answers for only one bot; delegated bots do not send separate external replies. | [channels doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/channels.md) | V |
| V15 | Akeru voice is in-client realtime conversation (ChatGPT subscription or API), with no PSTN numbers or outbound telephony. Image generation is native for **ChatGPT and Grok, still images only, no video**. Computer use is **Daytona sandboxes with Codex or Kimi only**; Claude, Grok and OpenCode engines are "Not available yet"; a local workspace has no separate desktop. | [voice](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/voice.md); [image](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/image-generation.md); [computer](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/computer.md) | V |
| V16 | Akeru's main export includes bots, groups, projects, chats, settings and MCP recipes; it **excludes** secrets, bot memory (separate archive), **routines, skill assignments**, usage history, files, Git repositories, attachments and checkpoints. | [portability doc](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/user/data-portability.md) | V |
| V17 | `noid-one/noid-bot` is MIT, created **2026-10-20**, 2 stars, "built on pi-durable"; Pi Durable is "experimental"; it has bots, groups, bot mail, a shared Docker computer, mobile-first approvals and skills; it does not mention WhatsApp; Linux/macOS only. | [README](https://raw.githubusercontent.com/noid-one/noid-bot/main/README.md); GitHub API | V/M |
| V18 | There is no universal `SKILLS.md`. Claude Code discovers `.claude/skills/<name>/SKILL.md` with YAML frontmatter; Codex discovers `.agents/skills` / `~/.agents/skills` with `SKILL.md` plus `AGENTS.md` (`~/.codex/AGENTS.md`). | [Claude skills](https://code.claude.com/docs/en/skills); [Codex customization](https://learn.chatgpt.com/docs/customization/overview) | V |
| V19 | Akeru's **Observer** and **Reflector** are memory-curation components in the observational-memory path ("condenses older messages for one thread") and use the same usage ledger hooks; they are not documented as bot-effectiveness observers. | [memory internals](https://raw.githubusercontent.com/opencoredev/akeru-bot/main/docs/internals/memory.md) | V |

## Assumptions

- **A1.** An always-on Linux or macOS host is acceptable for routines and remote use. A laptop that sleeps cannot run unattended routines.
- **A2.** HUMAN will accept a pre-1.0 base if it is actively maintained and the gaps have bounded fixes. Akeru is v0.2.1 with 70 open issues, so this is a real assumption.
- **A3.** "Phone calls" means PSTN/telephony, not in-app voice chat; "WhatsApp Business account management" means Business Platform profile, sender registration, templates, verification and analytics, not only DMs.
- **A4.** Grok Bot's hosted connectors cannot be exported or reused without a Cursor/xAI account and a supported backend. The proposal's options must therefore re-authenticate connectors.
- **A5.** "Minimise total costs" means total cost over roughly a year (setup, hosting, inference, operations, maintenance), not the lowest licence fee. I do not assign weights.
- **A6.** The screenshot team is the migration baseline for names, roles, rooms/pages and routines; unseen persona text, memories and provider assignments are not inferable.

## Unknowns

- **U1.** Akeru's real tool-call reliability and cross-provider quality; its docs are maintainer-reported.
- **U2.** Whether provider-neutral skills can be layered onto Akeru without forking its core, given V11.
- **U3.** Whether Akeru has any other bot-effectiveness observer. Its Observer and Reflector are memory-curation components (V19), not an effectiveness evaluator.
- **U4.** Whether Akeru's WhatsApp channel uses the WhatsApp Business Platform, Cloud API or a linked personal account. The internals doc confirms a webhook-based Meta integration and DM-only behavior, but not the account type (V14).
- **U5.** Whether the Akeru fork is intended for external adoption. Its README says "Do not push or publish this fork unless Leo asks", yet it is public, MIT and has releases. That is a governance ambiguity, not a licence restriction.
- **U6.** Provider terms for using subscription credentials through a third-party harness.
- **U7.** Exact Twilio, Meta/WhatsApp, xAI media and sandbox rates; none were verified.
- **U8.** T3 Code upstream's long-term roadmap and how easily Akeru can rebase.
- **U9.** Whether Akeru groups can grow into rooms with shared result pages, peer ratings and an observer without deep changes.
- **U10.** The user's actual installed Grok Bot connector set, persona exports, memories and provider assignments; the screenshot roster is context only (`assessment-context.md`).

## Option comparison

Symbols: **●** documented/strong, **◐** partial or conditional, **○** absent/not documented, **?** unverified. These are qualitative, not scores.

### Mandated criteria

| Criterion | 1 Official-client shim | 2 Reconstructed build | 3 Open-source alternative | 4 DIY primitives |
|---|---|---|---|---|
| **Fit to HUMAN's goals** | Low–medium. Preserves the exact UI, but only inference moves; bot identity, skills, connectors and state stay in the proprietary app. Cannot add the required accountability/usage/observer UI. | Low–medium. Source access and four inference routes, but a 0.18 snapshot on macOS, archived and unlicensed; team/skills/memory not documented. | **High.** Per-bot model/tools/memory/avatar, four named backends including DeepSeek, groups, delegation, plugins/MCP, image and voice. Gaps are bounded extensions. | Highest in principle; everything must be built. |
| **Feasibility** | Medium: active ISC project, but only with the installed app and undocumented hooks. | Low–medium: the code exists, but it is archived, macOS-only and unlicensed. | **High:** MIT, releases, cross-platform, active. | Medium technically; long build. |
| **Effort** | Low initial integration; high ongoing repair. | High: port, revive and legally clear a dead fork. | Medium: integrate the missing skills/routing/observer/usage/specialist modules. | Highest. |
| **Maintenance** | Very high: every app change can break the shim. | Certain decay: archived; no upstream fixes. | Medium–high: pre-1.0 fork plus T3 upstream churn. | High but owned and predictable. |
| **Local control** | Medium: proprietary app holds state and connector auth. | Medium–high: source and data local, but macOS and no licence. | **High:** MIT, local-first, data in `~/.akeru`; export is partial. | Highest. |
| **Dependencies** | Grok Bot desktop app, Codex login or API key, Docker, Node 22.12+. | macOS Apple Silicon, Node 26.5, Xcode CLT, Git LFS. | Node 22+, provider CLIs/accounts, optional Docker/Daytona, T3 upstream. | Chosen per component. |
| **Operational risk** | High: undocumented protocol, app updates, vendor ToS, Linux-only. | High: no licence, archived, platform lock. | Medium: pre-1.0, fork governance, subscription ToS unknown. | Medium: custom bugs, but controlled. |
| **Reversibility** | Low: state/connectors in the vendor store; UI proprietary. | Medium: source/data local, but macOS and legal ambiguity. | **High:** MIT, local data; export omits routines/skills/usage. | High: your code and data. |

### Priority-by-priority assessment

Columns are the four original options. Every option is assessed against every HUMAN priority; an absent row would silently drop a requirement.

| HUMAN priority | 1 Shim | 2 Reconstruction | 3 OSS platform (Akeru) | 4 DIY |
|---|---|---|---|---|
| Primary goal: same persistent bots across Codex/Claude/DeepSeek/Grok | ◐ UI/state persist, but only inference switches; connectors vendor-bound | ◐ Four routes, but macOS/stale/no licence | ● Four backends + per-bot state; manual cross-provider switch; same-provider failover | ● in principle; must build |
| User-friendly bot declaration | ● existing Grok Bot flow; no new template UX | ◐ old UI, macOS build | ● connect account, one setup question, edit profile/tools/model; no template library | ○ later |
| Minimise total cost | ◐ low licence, high upkeep; needs vendor app | ◐ no licence fee, high effort/macOS hardware | ● MIT/no licence fee, local hosting; subscriptions/API + optional sandbox | ○ highest build cost |
| SKILLS.md support | ◐ in-app skills, no file convention | ? unverified | ◐ provider-scoped `SKILL.md`; neutral file not native | ● can define exactly |
| Agent library: named templates, appearance, procedures, goals, attitude, skills | ● Grok Bot templates, but recipients reinstall and custom MCP is excluded | ? | ◐ per-bot avatar/name/label/description/tools/memory; no documented template/clone library | ● build |
| Autonomy within intent | ◐ app routines; not extensible | ? | ● routines, delegation, background service; routine docs thin | ● build |
| Deliberate speech / selective silence | ? app behavior; `SendMessage` is a communication gate but not configurable | ? | ○ no selective-silence feature; watchdog is provider inactivity | ● build |
| Collaborative excellence | ◐ app rooms; no ratings/challenge protocol | ? | ◐ groups, Boss, @mentions, delegation; no peer ratings | ● build |
| Smart observer bot | ○ proprietary | ○/? | ○ no effectiveness observer; Observer/Reflector are memory curation (V19) | ● build |
| Task-specific good-enough routing | ○ manual | ◐ manual routes | ◐ per-bot model; no capability routing; fail-closed | ● build |
| Safe switching / resume | ◐ app state persists; no checkpoint or duplicate-side-effect controls | ? | ◐ exactly-once delegation, retries, startup reconciliation; provider change starts a fresh session; no cross-provider task transfer | ● build best |
| Phone / WhatsApp Business / image / video | ? Grok Bot plugins; cannot add | ◐ custom MCP; macOS | ◐ native image; no video/PSTN; WhatsApp DMs only; MCP/Composio for the rest | ● build |
| Grok Bot connector replication | ◐ best chance while the Cursor account exists; unverified and vendor-bound | ◐ MCP/plugin claimed; unverified | ◐ plugin/MCP substrate; no hosted tokens; re-auth required | ◐ build |
| Migration baseline: names, roles, rooms, pages, routines | ● strongest UI/team continuity; state in vendor store | ◐ 0.18 UI; macOS | ◐ names/roles/groups/routines/memory recreate; shared pages absent | ◐ build |
| Lean UI matching the screenshot | ● reference UI | ● old reference UI | ◐ different lean UI; not the screenshot | ○ build |
| Task accountability (peer task ratings) | ○ proprietary | ○/? | ◐ delegation cards show state/time/tokens/retry; no peer ratings | ● build |
| Usage transparency | ○ no per-bot/room attribution | ? | ◐ per-bot/Observer/Reflector tokens, estimated cost, plan meters; no cached/reasoning/conversation/child roll-up | ● build |
| Review/coordination overhead visible | ○ | ○/? | ○ Observer/Reflector are memory curation, so a separate effectiveness observer's cost is not visible (V19) | ● build |

### Option 1 — Official-client shim

**What it is.** Keep the installed Grok Bot desktop UI and run `grokbot-shim` as a local host that translates the app's Connect/protobuf inference stream to Codex OAuth or an OpenAI-compatible endpoint, with a local noVNC Computer (V4).

**Usability walkthrough.** Install the Grok Bot desktop app and log in; install the shim; put provider keys in `.env` and models in `models.json`; start the host; pick a model; create or open a bot in the app. Customisation is limited to what the app exposes (name, instructions, memories, plugins), plus model choice in the shim. There is no new template library, appearance editor or per-instance isolation beyond the app's own.

**Strengths.** It is the only path that preserves the exact reference UI, rooms, pages, routines and the existing team workflow without a migration. It is ISC-licensed and actively maintained (V4). The `SendMessage` protocol gate is a genuine architectural advantage for deliberate speech: assistant text is private working text unless the bot calls the tool (V4). The hosted connector backend may keep working while the Cursor/xAI account remains (V1), which is the best short-term connector continuity of any option.

**Decisive weaknesses.** The primary goal is provider-independent bot identity, memory, skills, procedures and task progress. The shim moves *inference* only. The app still owns the bot state, the UI is proprietary, and connector OAuth tokens stay on Cursor's backend (V1). There is no supported way to add the required usage drill-down, peer task ratings, observer or automatic routing to that UI. The integration points are undocumented and may break on any app update (V4). It is Linux-only and needs the proprietary app plus Docker. Claude subscription access is not a documented route; Codex OAuth and OpenAI-compatible APIs are. So the model coverage is narrower than the proposal implies, and it is structurally impossible for the shim to satisfy the "not tied to a single provider" requirement for connectors and skills.

**Verdict.** Valuable as a UI/connector *reference* and a short-term fallback while the Cursor account exists. Not a credible primary path for the full priority set, and not the MVP I would choose.

### Option 2 — Reconstructed local-first build

**What it is.** Adopt or fork `grok-bot-0.18-reconstructed`, an unofficial source-oriented reconstruction of Grok Bot 0.18.0 for macOS Apple Silicon, with Cursor, Claude Code, Codex and OpenRouter inference routes and claimed MCP/plugin tool execution (V5).

**Usability walkthrough.** Build on macOS Apple Silicon with Node 26.5, Xcode CLT and Git LFS; launch the reconstructed app; connect Cursor, Claude Code, Codex or OpenRouter; create bots in the 0.18 UI. Customisation is whatever 0.18 exposes, which the README does not document for templates, memory or skills. There is no Linux/Windows path.

**Strengths.** It has the most UI parity of any *modifiable* option: the source is available, so in principle one could add usage displays, ratings or an observer. It supports Claude Code and Codex harness routes plus Cursor and OpenRouter, which is closer to the primary goal than the shim. It has significant public interest (3,536 stars).

**Decisive weaknesses.** The repository is **archived**, was created and last pushed on the same day (2026-08-23), and has **no licence** (V5). It is a snapshot of 0.18.0 while the public analysis referenced Grok Bot 0.70.2. It requires macOS Apple Silicon, Node 26.5, Xcode CLT and Git LFS. Adopting it means owning a dead, legally uncleared fork of an old proprietary-derived app; any security or provider change is yours to fix. Its README does not document memory, rooms, templates or skills, so the migration-baseline claims are unverified. Building a distribution or sharing derived code without a licence is a legal exposure, not a technical detail, and it conflicts with the proposal's own §4 non-goal against redistributing proprietary material or bypassing licensing.

**Verdict.** Reference material for understanding Grok Bot internals; not a maintainable base. I rank it last.

### Option 3 — Open-source alternative (Akeru as the concrete candidate)

**What it is.** Adopt a self-hosted platform with named bots and multi-provider routes. For this assessment the concrete candidate is **Akeru**: MIT, local-first, desktop/web/mobile, a T3 Code fork, v0.2.1 (2026-10-01), active on 2026-10-23. `noid-bot` is the other named candidate; it is MIT but four days old, 2 stars, and built on an explicitly experimental Pi Durable (V17), so it is not mature enough to lead.

**Usability walkthrough.** Download Akeru or run `npx akeru-bot@latest`; connect one or more providers in Settings; create a bot, answer the single setup question, and edit the proposed plan and opening message; then edit avatar, name, label, description, model, voice and enabled tools; add a routine with procedure, schedule, timezone, required skills and connectors; create a group with a Boss and at least one other bot. Memory is editable as Markdown. There is no documented template/clone library, so a pre-declared agent library is a custom pack.

**Why it fits the primary goal better than anything else.** Akeru already has the hard commodity layer:
- a per-bot record with name, avatar, label, description, model, voice, tools and memory (V8, V10);
- first-class routes to **ChatGPT/Codex, Claude, Grok and DeepSeek** — the last through the Custom API preset with an API key/base URL (V7);
- same-provider backup-account failover and visible plan meters (V7, V13);
- provider change starting a fresh provider session while keeping the same enabled tools (V8);
- groups with a Boss, `@BotName` routing, delegation cards with tokens/retries/deadlines and exactly-once result delivery (V9);
- a plugin catalog, Composio and **custom MCP servers** with per-bot enablement and honest "Not checked" health (V12);
- native ChatGPT/Grok image generation, in-client voice, a Linux/macOS background service, and desktop/web/mobile clients (V6, V15).

That is a large fraction of the platform HUMAN would otherwise commission. The remaining work is the differentiators, not the plumbing.

**Documented gaps that matter.**
- **Skills are provider-scoped**, not unified (V11). A canonical `SKILLS.md` is not native. This is the sharpest conflict with "skills must not be tied to a single provider".
- **No cross-provider automatic fallback.** Akeru fails closed and never silently substitutes a model; only same-provider backup accounts fail over (V7, V8). This is good for quality honesty but means credit exhaustion needs a user or custom-router action.
- **Task-level routing is not native.** The model is saved per bot and resolved per thread; capability-based routing would need a router layer, multiple bot variants or a fork.
- **No effectiveness observer or peer task ratings.** The usage page exposes Observer/Reflector token categories, but the internals place them in the observational-memory path, not in bot-effectiveness evaluation (V19).
- **Usage is partial.** Per-bot input/output/Observer/Reflector/reserved tokens and estimated cost are present; cached/reasoning tokens, conversation-level attribution, child-roll-up and double-counting rules are not documented (V13).
- **Specialists are incomplete.** No PSTN, no video, WhatsApp DMs only and one bot per messaging account, and computer use only on Daytona with Codex/Kimi (V14, V15).
- **No shared result pages.** Groups post results and work cards; there is no page/artifact object equivalent to the screenshot's shared pages (V9, U9).
- **Export is incomplete.** Routines, skill assignments, usage history and checkpoints are excluded; memory uses a separate archive (V16).
- **Governance is ambiguous.** The README's "Do not push or publish this fork unless Leo asks" conflicts with the public MIT repo and releases (U5). That is not a licence problem, but it is a maintenance-intent risk.

**Verdict.** The strongest base. It should be adopted as a platform to extend, not as a finished solution.

### Option 4 — DIY primitives

**What it is.** Assemble the system from containers, schedulers, memory files, model APIs/CLIs and MCP servers, with no platform base.

**Usability walkthrough.** You design the flow. It can be the best (one template picker, named instance, appearance, persona fields, procedure/goal/attitude, skills and connector dependencies), but it does not exist until built.

**Strengths.** It can implement every priority exactly: a canonical provider-neutral `SKILLS.md`, a capability-aware router with acceptance criteria and escalation, a deliberate-speech/selective-silence policy, an observer with measurable proposals, peer task ratings linked to deliverables, and usage attribution down to parent/child turns. It has no fork governance, no upstream churn and the highest local control and reversibility. If the platform's extension points turn out to be closed, this is the clean fallback.

**Decisive weaknesses.** It must rebuild the commodity layer that Akeru already provides under MIT: provider adapters and session handling, bot profiles and memory, group/delegation semantics, plugin/MCP lifecycle, clients, approvals, background service and checkpoints. That work is large, non-differentiating and delays the features HUMAN actually asked for. The risk is not that DIY is impossible; it is that it spends the first phase on plumbing and reaches the differentiators later, with all maintenance owned. For a small team, that is usually the more expensive path even when the licence fee is zero.

**Verdict.** Runner-up and fallback. It wins only if Option 3's extension points fail the bounded tests below.

### Agent library, skills and per-instance isolation

| Requirement | 1 Shim | 2 Reconstruction | 3 Akeru | 4 DIY |
|---|---|---|---|---|
| Named, reusable template | Grok Bot templates (instructions, memories, skills, first-party plugins); recipients reinstall; custom MCP excluded (V2) | Undocumented | Bot profiles; no documented template/clone library; export omits routines and skill assignments (V8, V16) | Define a template schema and instantiate |
| Named instances | App bots | 0.18 bots | Per-bot name, label, description, avatar | Any |
| Appearance/outlook | App avatar | 0.18 avatar | Per-bot avatar (styled/animated); no dedicated persona/tone editor (V8) | Any |
| Procedures, goals, attitude | App instructions | Undocumented | Setup plan, description and routines; no explicit goals/attitude fields | Explicit fields |
| Skills discovery | In-app, provider-bound | Undocumented | Provider-scoped menu; `$name`/`/name`; no canonical `SKILLS.md` (V11, V18) | Canonical library rendered per harness |
| Per-instance isolation | Vendor app store | Undocumented | Separate workspace identity and browser profile by default; per-bot memory; optional shared files/cookies (V8, V10) | Design |

**Implication.** Akeru is the only option that already separates template-like defaults from named instance state in a local data model, but it has neither the template library nor the neutral skill file. The agent library is therefore a custom template pack plus a skill-sync layer on Option 3; on Option 4 it is native but must be built. Options 1 and 2 inherit the app's template and isolation behavior, which is neither exportable nor auditable.

### Migration continuity against the supplied team baseline

The screenshot roster (Natalia; CodeBot Rajiv; Stefano The QA; DeepSeek Batch'it crazee; Sarah The Critic; Godzilla the Dataminer; MarketingBot Kristin; SeniorEngineer Arns; Counsel Helmut; Grok Bot Optimus), the rooms (Technical Board; Bringing In Deepseek; GETTING TO PRODUCTION; Administration board), the shared page and the weekly scorecard routine are context, not verified persona/memory exports or provider assignments (U10). No option has a documented Grok Bot export/import.

- **Option 1** preserves the live app, so names, rooms, pages, routines and memories continue as long as the app and account work. Nothing needs importing, but nothing can be audited or exported either.
- **Option 2** may preserve 0.18-era equivalents if old app data is compatible; unverified, and the repo does not document migration from a current account.
- **Option 3** can recreate names, avatars, labels/descriptions, memory seeds, groups (Boss plus members), routines and delegation. It cannot import Grok Bot persona text, memories or connector tokens automatically; expect manual transcription, `USER.md`/`MEMORY.md` seeding, group creation, routine recreation and connector re-authentication. Shared result pages have no direct equivalent; groups and work cards are the substitute.
- **Option 4** can model the baseline, but the migration path is yours to build.

**Migration implication.** Do not treat the screenshot as an export. A Phase 0 migration checklist should state what HUMAN must retype or re-authorise, and the agent library should be built from the recreated personas rather than pretending to restore unseen data. I will revisit this evidence in the challenge and response passes.

### Switching, credit visibility and safe resume

- **User-initiated switching.** Option 1 selects a model in the shim/app; the app keeps its state, but in-flight turns and tool side effects are not documented as resumable. Option 2 switches route in the reconstructed app; unverified. Option 3 changes the bot's model/provider in settings; a fresh provider session starts with the same enabled tools and per-bot memory stays local, but there is no documented cross-provider transfer of an in-flight turn. Option 4 can define checkpoints and idempotency keys.
- **Automatic fallback.** Option 1 has a documented optional fallback for Codex auth/quota rejection (V4), but the README does not specify the fallback target or state behavior. Option 2 is unverified. Option 3 has same-provider backup-account failover; the request that hit the limit still fails and the next request uses the backup, and it never silently changes model/provider (V7, V8). Option 4 can implement explicit capability-aware escalation.
- **Credit and account visibility.** Option 1 relies on the Grok Bot/Cursor UI and provider dashboards; no unified attribution. Option 2 is unverified. Option 3 shows provider-reported plan meters and an estimated cost, hides disconnected/unreported limits, and separates subscription meters from API billing; it cannot present a common cross-provider credit balance (V13). Option 4 can unify only what provider APIs expose, with the same subscription-versus-API distinction.
- **Safe resume.** Option 1 relies on the app's own persistence; duplicate-side-effect controls are undocumented. Option 2 is unverified. Option 3 has exactly-once delegated-result delivery, retries as new records, and startup reconciliation for queued/running work, but provider change starts a fresh session and does not checkpoint external tool side effects (V9). Option 4 can design the checkpoint/idempotency contract.

### Service-by-service capability matrix

Status: **N** native, **R** reuse an existing MCP/API connector, **C** custom adapter, **X** not supported, **◐** partial/conditional, **?** unverified. The original Grok Bot capability is stated only where public documentation supports it; the user's installed connector inventory is unknown (U10). Each cell's candidate implies the status; the notes below give the actions covered, authentication and hosting dependency, setup/ongoing cost basis and evidence for each service across the four options.

| Service | Original Grok Bot (public evidence) | 1 Shim | 2 Reconstruction | 3 Akeru | 4 DIY |
|---|---|---|---|---|---|
| **Phone calls (PSTN)** | Not advertised; unknown | C: Twilio Programmable Voice via custom MCP/API | C: Twilio via MCP | C: Twilio via custom MCP; Akeru voice is in-client only | C/R: Twilio/Telnyx |
| **WhatsApp messaging** | Not advertised; unknown | C: Meta Cloud API/Twilio via MCP | C: Meta/Twilio via MCP | ◐: Channels WhatsApp **DMs only**, one bot/account, no group messages; Business Platform unverified | C/R: Meta Cloud API/Twilio |
| **WhatsApp Business administration** | Unknown | X/C: Meta Business Management API | X/C | X/C: no profile/template/verification/analytics admin | C |
| **Image generation** | Unknown; Grok apps unverified | ?: xAI image API through the tool bridge | C: xAI/OpenAI image API | **N: ChatGPT/Grok still images, per-bot provider, fallback order** | R: xAI/OpenAI/others |
| **Short movie / video** | Not advertised | C: xAI video API | C: xAI video API | X/C: no native video; custom MCP | C/R |
| **Email / calendar** | Gmail, Notion, Slack apps documented as account-wide, Cursor backend (V1) | ◐/?: may work while the Cursor account exists; not portable | ?: claimed MCP/plugin tools | R/C: plugin catalog/Composio/MCP; **no first-party email connector; no calendar/booking connector; browser fallback** | R/C |
| **Chat/docs (Slack/Notion/Drive)** | Slack/Notion apps documented | ◐/? | ? | R/C: plugins/Composio/MCP; Slack/Discord channels are messaging, not workspace admin | R/C |
| **Browser/desktop computer** | Grok Bot Computer documented | **N: local Computer via noVNC, Linux** | ◐: optional local Docker sandbox | ◐: **Daytona + Codex/Kimi only**; Claude/Grok/OpenCode not yet; local workspace has no desktop | C |
| **MCP/custom tool bridge** | Plugins/apps | ◐: tool-schema translation; plugins via the app | R/?: MCP/plugin execution claimed | **N: custom MCP servers, per-bot enablement, guidance, health** | R |

**Auth, hosting and cost notes for the matrix.**

- **Phone.** Actions: outbound/inbound PSTN calls, call control and webhooks. Every option needs a PSTN vendor; Twilio's Call resource is the documented example, not a selected vendor. Authentication is a vendor account/key and a provisioned number; hosting is the option's environment plus a public webhook. Inbound calls need a public webhook, so a purely local host needs a tunnel or a hosted relay. That is an operational dependency in all four options. Exact per-minute and number costs were not verified (U7).
- **WhatsApp messaging.** Actions: send/receive messages, templates and media. WhatsApp Business Platform messaging is not the same as Business account administration. It requires a Meta business account, sender registration, templates and a BSP or direct Cloud API; Twilio is one BSP. Authentication is the Meta/BSP account and token on the environment; inbound needs a webhook. Akeru's channels doc says WhatsApp DMs only and one bot per account (V14); it does not say whether that is Business Platform. Do not claim parity. Conversation/template/BSP costs are unverified (U7).
- **WhatsApp administration.** Actions: profile, template management, verification, analytics and account health. No option has it; all four need the Meta Business Management API as a custom adapter, with a Meta business account that has management permissions. Costs are Meta/BSP fees, unverified.
- **Image.** Actions: generate and edit still images (Akeru: up to four per request, per-bot provider, fallback order, no silent cross-provider send) (V15). Akeru is the only option with documented first-party image generation: ChatGPT/Grok. Authentication is the connected subscription on the environment server; the docs say it uses the subscription, with API billing separate if an API key is used. Other options need an xAI/OpenAI image API adapter and a vendor key; the xAI image API is documented as a route, not as a bundled tool.
- **Video.** Actions: submit asynchronous generation jobs, poll, store and attach output. No option is native. The xAI video API is a candidate, with a vendor key and output storage; async job handling and cost are custom work and unverified.
- **Email/calendar and chat/docs.** Actions: read/send email; calendar/booking where the connector exposes it; read/write Slack, Notion or Drive content. This is the one place the original Grok Bot path has a real advantage: its apps are account-wide on Cursor's backend, so the shim/reconstruction may retain access while that account is used. But the tokens are not portable and the local-routing behavior is unverified (V1). Akeru's own connector-gap matrix says it has no first-party email connector and no calendar/booking connector, and falls back to a temporary browser session. Akeru's plugin catalog/Composio/MCP is the reusable route, with per-app OAuth or a Composio key stored on the environment server, and honest health status. Costs are the vendor subscription/API; Composio has its own account terms, unverified.
- **Computer.** Actions: screenshot, mouse/keyboard input and takeover. Grok Bot's Computer is a documented baseline; the shim preserves it on Linux. Akeru's is narrower: Daytona with Codex or Kimi only, with exclusive control capped at one minute. Authentication is a Daytona account; hosting is the Daytona sandbox, not the local machine. If desktop takeover is required for every model backend, Akeru needs custom work.
- **MCP.** Actions: invoke MCP tools with per-bot enablement and server guidance. Akeru has the strongest substrate: add a custom MCP server, enable it per bot, store guidance, and show health only after a real request (V12). The shim translates the app's tool schema but does not provide a general MCP registry; the reconstruction claims MCP/plugin execution but is archived and unverified.

**Bottom line on specialists.** None of the four options has native PSTN calling, native WhatsApp Business administration or native video. Akeru alone has native still-image generation. Every option therefore needs the same class of custom MCP/API adapters for phone, WhatsApp and video; the differences are the substrate (Akeru's per-bot plugin/MCP lifecycle and auth storage versus a shim that can only use the app's plugins versus a DIY build) and the operational burden (public webhooks, Meta verification, media storage). Connector work does not favour the shim or reconstruction: neither gives a reusable connector registry, and the hosted Grok Bot apps are not portable.

### Cost structure (no invented figures)

| Cost | 1 Shim | 2 Reconstruction | 3 Akeru | 4 DIY |
|---|---|---|---|---|
| **One-time setup** | Install app, shim, Docker; low | macOS build chain; high | Download/npx, connect providers; low–medium | Build the platform; highest |
| **Hosting** | Local Linux + Docker image (multi-GB) | macOS Apple Silicon machine | Local Linux/macOS/Windows or server; optional Daytona | Your choice |
| **Inference/subscriptions** | Existing Grok Bot/Cursor account + Codex login or API key | Cursor, Claude Code, Codex or OpenRouter account | Existing ChatGPT/Claude/Grok/Kimi/OpenCode Go subscriptions, or API keys (DeepSeek etc.) | Your choice |
| **Ongoing operations** | App-update repair, undocumented hooks | Dead fork; no upstream fixes | Pre-1.0 upgrades, fork rebase, provider changes | All yours |
| **Maintenance** | Very high | Certain decay | Medium–high | High but owned |
| **Cost unknowns** | App subscription, ToS, whether local routing is permitted | Licence/legal exposure, macOS hardware | Subscription-reuse ToS, API rates, sandbox costs | Build labour |

## Preferred choice

**Option 3 — the open-source alternative, with Akeru as the concrete platform to spike and extend.** This is a primary path, not a hybrid: do not run a parallel DIY build or a shim MVP. Option 3 is the only alternative that already satisfies the primary goal's hardest structural requirement — a bot whose name, avatar, model, tools and memory are a first-class local record, with documented routes to ChatGPT/Codex, Claude, Grok and DeepSeek (V7, V8, V10). It also supplies the collaboration substrate (groups, Boss routing, delegation, exactly-once results), the connector substrate (plugins, Composio, custom MCP), a background service, and cross-platform clients under MIT. Those are the parts that are expensive to build and do not differentiate the product.

The proposal's shim-first plan optimises UI parity and connector continuity while leaving the primary goal unmet: the shim moves inference, not the bot's identity, memory, skills, connectors or state (V1, V4). The reconstruction is archived, unlicensed and macOS-only (V5), so it cannot be the maintainable multi-platform base the project needs. If UI parity is the top priority, the shim is the right *reference*; it is not the right foundation for provider independence.

**What I would build on Option 3, in order.** (1) A provider-neutral skill layer: keep a canonical skill library and materialise it into the active provider's native discovery path (`.claude/skills/...`, `.agents/skills/...`), because Akeru's native skill list is provider-scoped (V11, V18). (2) A router/acceptance module: task class, acceptance criteria, model capability record, explicit escalation, and a visible reason for every model choice; Akeru's saved-model-per-bot model must not silently substitute (V7, V8). (3) An observer/ratings module using delegation events and work cards as evidence, with the observer's own tokens visible and its strategy proposals reviewable, never auto-applied. (4) A usage roll-up that labels measured/estimated/unavailable, separates parent and delegated child usage, and never presents a dollar estimate as a bill (V13). (5) Specialist MCP adapters for Twilio voice, WhatsApp Business Platform and an image/video provider; add WhatsApp Business *administration* as a separate adapter, not as a messaging claim. (6) A template pack for the agent library, because Akeru has profiles but no documented template/clone library and its export omits routines and skill assignments (V16).

**Why the closest runner-up (Option 4) loses.** DIY is the only option that can implement every priority natively, and it wins on provider-neutral skills, task routing, observer design, ratings and usage attribution. But it must first rebuild the provider adapters, bot profiles, groups, delegation, plugin lifecycle, clients, approvals and background service that Akeru already provides under MIT. That is the largest effort and the slowest time-to-value, and it defers the differentiators. The right comparison is not "Akeru as-is vs. a perfect DIY build"; it is "a custom layer on Akeru vs. the same layer plus the whole platform". DIY becomes the better choice only if Akeru's extension points are closed — which is exactly what the tests below decide.

**Strongest case against Option 3.** Akeru is a pre-1.0 fork of a fast-moving upstream, with 70 open issues and a README that says not to publish the fork (V6, U5). The custom layer is not small: provider-neutral skills, per-task routing, an observer, peer ratings, usage roll-up and three specialist adapters. If each of those needs a core fork, the savings evaporate and the maintenance burden becomes Akeru's plus yours. There is also a quality-honesty tension: Akeru's "never silently substitute" policy is good, but it means credit exhaustion does not switch providers automatically; a router that does so must be explicit, auditable and tested for duplicate side effects.

**Confidence.** Medium overall. High that Options 1 and 2 are not viable primaries for the full priority set. Medium-high that Option 3 is the best base. Medium that Akeru specifically beats both `noid-bot` and Option 4 after a bounded spike. The recommendation is conditional on the tests in the next section, not on the maintainer documentation alone.

## What would change my mind

1. **Continuity test fails.** Create a named bot with a persona, one skill, one memory and one routine; run a task on Codex, then switch to Claude, DeepSeek and Grok. If Akeru loses the skill, memory, routine, task state or tool set on switch and cannot be extended without forking core, Option 3's primary-goal advantage collapses. Option 4 becomes preferred.
2. **Task-routing test fails.** If Akeru cannot select a model per task (rather than per bot/thread) through a supported extension point, the "critical feature" of good-enough routing would require either multiple bot variants with delegation overhead or a core fork. If the overhead is large, Option 4 wins.
3. **Skills test fails.** If a canonical skill library cannot be materialised into each provider's native discovery path without provider-specific forks, the provider-neutral `SKILLS.md` requirement is not met and Option 4's clean design becomes more attractive.
4. **Governance/upstream test fails.** If Akeru's releases stop, the fork cannot be rebased onto T3 Code without heavy conflicts, or the "do not publish" note reflects an intent not to support external adopters, maintenance risk rises. A different Option 3 candidate or Option 4 would be safer.
5. **Provider terms forbid subscription reuse.** If ChatGPT/Claude/Grok subscription credentials cannot lawfully be used through a third-party harness, Akeru's cost and usability advantage shrinks to API-key routing. It remains viable, but the ranking versus a thin DIY/CLI wrapper changes.
6. **Grok Bot connectors prove non-replicable.** If the existing team depends on hosted connectors that cannot be reproduced with MCP/Composio/APIs at acceptable effort, Option 1's short-term continuity becomes more valuable. It still fails identity, extensibility and provider independence, so I would treat it as a migration bridge, not the primary.
7. **HUMAN prioritises exact UI/team parity above provider independence.** Then Option 1 (or Option 2 on macOS) could be the pragmatic short-term choice. That would be a deliberate trade of the primary goal for continuity, and I would want it recorded as such.
8. **`noid-bot` matures or Akeru is abandoned.** If noid-bot gains stability (it is currently four days old, 2 stars and experimental) or Akeru stops, the Option 3 candidate changes; the option itself may still be the right shape.

**Bounded comparison tests I would run before committing** (cheap, reproducible, no full spec): (a) the continuity test in item 1; (b) a skills-discovery test using the same skill in `.claude/skills/`, `.agents/skills/` and Akeru's provider-scoped menu; (c) a simulated 401/quota failure to distinguish authentication, rate-limit and credit-exhaustion behavior and measure manual switch steps; (d) a custom MCP spike for Twilio voice and WhatsApp messaging, with WhatsApp Business administration tested separately; (e) an observer/usage spike to confirm that a separate effectiveness observer can be attributed in the usage page without double counting and that delegated child usage rolls up correctly; (f) a one-week rebase test against upstream T3 Code.

## Findings

### DEEPSEEK-1 · The shim-first recommendation cannot meet the primary provider-independence goal

- **Section:** §1 Recommendation; §2 table; §3 goals
- **Type:** inconsistency
- **Severity:** major
- **Finding:** The proposal recommends a shim-based MVP "for UI parity". The shim keeps the proprietary Grok Bot app and translates its inference protocol (V4). Bot identity, memories, skills, routines and task state remain in the vendor app, and connected-app OAuth tokens remain on Cursor's connector backend (V1). Local inference therefore does not move the bot or its connectors, and the proprietary UI cannot be extended with the required usage drill-down, peer task ratings or observer. The recommendation optimises the one priority the shim can satisfy (UI continuity) at the expense of the stated primary goal.
- **Proposed change:** Demote the shim to a UI/connector reference and short-term migration bridge, not the MVP. Require any primary path to pass a continuity test in which a named bot's persona, memory, skill and task state survive a backend switch without the vendor app, and to expose where state and connector tokens live.
- **Evidence:** V1, V4; `assessment-context.md` finding 1; no candidate installed or tested.
- **Confidence:** high for the architectural limitation; medium for the exact connector behavior after local routing, which is undocumented.

### DEEPSEEK-2 · The reconstruction path is an archived, unlicensed, macOS-only snapshot

- **Section:** §1 Recommendation; §2 table
- **Type:** risk
- **Severity:** major
- **Finding:** The proposal recommends validating "a local-first reconstructed runtime" in parallel, naming `grok-bot-0.18-reconstructed`. GitHub metadata shows the repository is **archived**, has **no licence**, and was created and last pushed on 2026-08-23. Its documented requirements are macOS Apple Silicon, Node 26.5.x, Xcode CLT and Git LFS, targeting Grok Bot 0.18.0 (V5). It is not a maintainable multi-platform base; adopting it creates legal exposure and a guaranteed maintenance dead end, and its memory/rooms/templates/skills support is undocumented.
- **Proposed change:** Remove it from the primary/parallel recommendation or mark it "reference only". Require a licence and a maintenance/port plan before any code reuse. If UI parity is needed, use it to understand the original design, not as the product base.
- **Evidence:** V5; GitHub API (`archived: true`, `license: null`, created/pushed 2026-08-23); README requirements.
- **Confidence:** high.

### DEEPSEEK-3 · Option 3 conflates two candidates with very different maturity

- **Section:** §2 table; §1
- **Type:** gap
- **Severity:** major
- **Finding:** The proposal lists `noid-bot` and `akeru-bot` under one "open-source alternative" option without URLs, revisions, licences or a candidate-level comparison. They are not comparable: Akeru is MIT, v0.2.1 (2026-10-01), 106 stars, active, with desktop/web/mobile, groups, delegation, plugins/MCP and extensive docs (V6–V16); noid-bot is MIT but four days old, 2 stars, built on experimental Pi Durable, Linux/macOS only, with no WhatsApp (V17). Treating them as one option hides a large maturity difference and makes the option untestable; it could also cause HUMAN to dismiss the strongest base.
- **Proposed change:** Keep the Option 3 identity but add a candidate sub-table with pinned URLs, release/commit, licence, maturity and feature evidence; recommend Akeru as the candidate to spike and noid-bot as an experimental alternative, not a co-equal.
- **Evidence:** V6–V17; GitHub API for both repositories; fetched 2026-10-24.
- **Confidence:** high.

### DEEPSEEK-4 · Model APIs, CLI harnesses and subscription authentication are conflated

- **Section:** §2 table; §3
- **Type:** gap
- **Severity:** major
- **Finding:** The table mixes `grokbot-shim` (inference-protocol translation; Codex OAuth/OpenAI-compatible), `grok-bot-0.18-reconstructed` (Cursor/Claude Code/Codex/OpenRouter routes) and Akeru (subscription/account logins plus Custom API) without distinguishing model APIs, CLI/agent harnesses and subscription authentication. HUMAN explicitly requires this distinction. As written, the options look more interchangeable than they are: Claude subscription access depends on a Claude Code harness, DeepSeek is an API route, and skill discovery and tool-call behavior differ by harness (V11, V18). This can produce a false parity claim.
- **Proposed change:** Add a per-option route matrix: backend | route type (API / CLI harness / subscription) | authentication | tool-call support | skill discovery | state location | evidence/date. Do not call routes interchangeable until tested.
- **Evidence:** V4, V5, V7, V11, V18; HUMAN primary-goal wording.
- **Confidence:** high.

### DEEPSEEK-5 · No connector, usage, skills or observer assessment, so the requested choice cannot be made from the proposal

- **Section:** §2; §3; general
- **Type:** gap
- **Severity:** major
- **Finding:** The proposal names candidate tools but provides no service-by-service connector matrix, no authentication/hosting/cost analysis per service, no usage-accounting design, no verification of skill-file conventions and no observer/ratings assessment. HUMAN's priorities require all of these for every option, and the proposal's parity language is unsupported. (The file is also truncated at §6, already a round-1 finding; here the defect is the missing option-comparison evidence, not only the missing later sections.)
- **Proposed change:** Add the required matrices, or adopt the matrices in this review as the debate input. Mark every cell native/reuse/custom/not supported/unverified with evidence and date. Do not claim a parity percentage without a defined inventory. Separate WhatsApp messaging from Business account administration, and phone from in-app voice.
- **Evidence:** Proposal §2–§3; `assessment-context.md` "Required audit and decision tests"; this review's service matrix.
- **Confidence:** high.

Result: complete
