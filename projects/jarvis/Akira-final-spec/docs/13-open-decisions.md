# 13 — Unresolved decisions register

**Status:** draft v0.3. Every item is a question this specification does not answer, or
one that HUMAN has now answered and that is kept for traceability. Resolved items state
the decision.

A reversible default is not an approval. When HUMAN answers, the answer is recorded in
`decisions.md` and the default is removed.

---

## 1. Register

| ID | Question | Options | Default taken (reversible) | Blocking? | What resolves it / what changes |
|---|---|---|---|---|---|
| U1 | What host runs Akira, and is it always on? | Linux VPS; home server; macOS; laptop-only | **Resolved 2026-10-25: AKIRA-D4** — Linux, single node, always on | No | A later host change is a deployment decision; it changes WhatsApp/webhook and availability design |
| U2 | May subscription logins (ChatGPT/Claude/Grok/Kimi) be used through Akira's runtime? | Personal-use acceptance; API keys only; per-vendor review | **Resolved 2026-10-25: AKIRA-D5** — yes, for the operator's personal work; route-level permission recorded | No | A vendor prohibition disables that route (recorded) and reverts it to API keys; no architecture change |
| U3 | Is Akira private/internal or to be published? | Private fork; internal distribution; public release | **Resolved 2026-10-25: AKIRA-D6** — private, internal only | No | Publication would be a new HUMAN decision with license/trademark/distribution review |
| U4 | What budgets, spend caps, concurrency caps and approval thresholds apply? | No cap; per-task cap; monthly cap; per-route cap | No caps; proposed defaults are labelled and configurable (AK-TRG-15) | No (spec proceeds) | Values set guardrails; low caps force stricter routing/triage and may change the cheapest adequate route |
| U5 | Which WhatsApp Business administration operations are actually needed? | Messaging only; profile+numbers+templates; full account ops | Messaging now; admin adapter scoped to profile/numbers/templates | No | Drives Meta app permissions, onboarding time and cost; full account review is not automatable |
| U6 | How should ratings aggregate into reputation? | Evidence-weighted mean; median+confidence; task-class normalised | Derived view, model configurable, no weights fixed | No | The chosen model changes reputation displays, not task data; needed before ratings inform routing |
| U7 | Which vendors for telephony, WhatsApp BSP vs direct, images, video? | Twilio/Meta direct; BSP; xAI/OpenAI/local; video providers | Contracts defined; first adapters candidates only | No (stub-first) | Vendor onboarding time and cost; contract stays stable |
| U8 | Which existing team exports exist (persona text, memory, pages, routines)? | Full export; partial; none | Drafts + `needs-human-review`; no invented content | No | A full export removes drafting work and improves migration fidelity |
| U9 | Who may approve observer activation and template upgrades? | HUMAN only; designated bot-admin; any room owner | HUMAN (or explicit bot-admin role) only | No | Delegation of authority changes approval UX, not the proposal lifecycle |
| U10 | Retention for logs and backups? | 30/90 days; longer; forever | Logs 30–90 days (proposal); backups 30–90; user data kept (AKIRA-D2) | No | Affects disk/backup sizing and forensics; never deletes user data |
| U11 | Is desktop/mobile in the first release? | Web first; +desktop; +mobile read/reply | Web first; desktop/mobile later | No | Scope and test surface; server contract unchanged |
| U12 | Is multi-team / hosted tenancy ever needed? | Single team only; multiple teams; hosted SaaS | Single environment per team (A3) | No | Would trigger Postgres, tenancy isolation, secret-per-tenant and compliance work (ADR-10) |
| U13 | What does "phone calls" need: outbound only, inbound, recording, transcription? | Outbound scripted; +inbound; +recording | Outbound first; recording requires policy config | No | Telephony adapter scope, cost, consent obligations |
| U14 | How long may a task run before it needs a human checkpoint? | No limit; per-class deadline; spend-based | Deadlines optional per task; defaults proposed | No | Affects triage estimates, supervision and cost guards |
| U15 | Should Akira adopt Akeru's analytics? | Off; anonymous counters on | Off | No | Privacy posture; no functional impact |
| U16 | May route selection rank candidates across auth classes (API vs subscription) using a labelled API-equivalent comparison unit? (added v0.4, from review round 1) | Within one auth class only; cross-class ranking via the comparison unit; operator chooses | Off: rank within an auth class, cross-class choice is the operator's (`docs/09` §1.7) | No | Enabling it changes automatic route choice only; accounting and records are unchanged |

---

## 2. Blocking questions — resolved

There are **no blocking questions left** for specification review. HUMAN answered the
three that were blocking on 2026-10-25:

1. **U1 host** → AKIRA-D4: Linux, single node, always on.
2. **U2 subscription transport** → AKIRA-D5: permitted for the operator's personal work.
3. **U3 distribution** → AKIRA-D6: private, internal only.

The remaining register items are configuration or policy choices with labelled defaults.
They do not block review or the first implementation slice, and changing them does not
require a schema migration (except U12, which is a future architecture decision).

---

## 3. Decisions that would change architecture (not just configuration)

| Decision | Architecture impact |
|---|---|
| Host is not Linux or not always-on | Deployment (§12), channel design, availability objectives; possibly remove WhatsApp |
| Subscription transport forbidden | Route matrix and cost model; no orchestrator change |
| Multi-team/hosted | Tenancy, Postgres, secret isolation, per-tenant quotas (ADR-10 rewritten) |
| Real-time duplex PSTN required | Add a streaming media service; concurrency and cost model change |
| Public plugin marketplace | Trust/review pipeline, distribution, sandboxing; significant scope |
| Publish Akira publicly | License/trademark review; support/docs; possibly replace Mastra-derived auth components |

---

## 4. Decisions that would change estimates (not architecture)

| Measurement | Effect |
|---|---|
| Spike shows the Mastra Claude transport bypasses the skill scanner | +1–2 ew skills work, or a route-specific limitation |
| DeepSeek fails the tool transcript | Drop DeepSeek from tool tasks; routing and cost case change |
| Retention disable requires a larger patch than one constant | +0.5–1 ew; review whether upstream offers a setting |
| Export cannot include checkpoints without a new bundle format | +1–2 ew; restore fidelity risk |
| Vendor onboarding for WhatsApp takes >4 weeks | Specialist phase slips; outbound-only fallback |
| Actual provider usage is not reported per turn on a route | More `unknown` coverage; routing calibration weaker; cost-per-task less precise |
| Persona replacement touches more provider paths than expected | +1–3 ew; risk of drift between routes |
| Single-node load exceeds assumptions in the first month | Trigger ADR-10 earlier; significant replan |

---

## 5. Questions this specification deliberately does not ask

- Which AI vendor is "best": the spec defines evidence and routing, not a winner.
- Whether Akeru was the right base: AKIRA-D1 settled it; the fallback trigger is in
  `docs/11-backlog.md` §16, not a daily debate.
- Specific numeric weights for reputation or routing: without HUMAN values, the spec
  fixes the data and the policy surface, not the numbers.
- The exact visual design: the screenshot is the reference; the spec fixes structure and
  behaviour, not pixels.

---

## 6. How answers are recorded

1. HUMAN states the decision in chat or in `decisions.md`.
2. The answer gets an `AKIRA-D<n>` id with the date and the exact instruction.
3. The corresponding register row is marked resolved (kept, not deleted), the default is
   removed from the code/config, and affected requirements are re-statused.
4. If the answer changes architecture, an ADR is added or superseded; if it changes
   estimates, `docs/11-backlog.md` is updated with the reason.
