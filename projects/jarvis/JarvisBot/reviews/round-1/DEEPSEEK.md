# DEEPSEEK review — round 1

Reviewed the local `spec.md`, version 0.1, for round 1. No previous-round consolidation and no project `decisions.md` exist. The CHATGPT round-1 review was present in the folder and was also read; DEEPSEEK-1 and DEEPSEEK-4 overlap it in subject, and the proposed changes below were derived from the spec text. No external candidate, URL, licence or capability claim was verified.

### DEEPSEEK-1 · The document is truncated inside §6 and has no requirements beyond the architecture

- **Section:** §6 / general
- **Type:** error
- **Severity:** major
- **Finding:** `spec.md` v0.1 ends at line 110 inside the Mermaid block opened in §6 (`flowchart LR` at line 97), with no closing fence and no sections after the architecture. Nothing in the file defines functional or non-functional requirements, acceptance criteria, a security model, a licensing deliverable, risks or a rollout; §1–§6 are context and goals only. As supplied, the document cannot be implemented or checked for completeness, and a reviewer cannot tell whether the missing content was omitted deliberately or by a copy/paste error.
- **Proposed change:** Close the Mermaid fence. Then either add the missing sections in this revision or mark the file explicitly as `Status: partial draft` and state which review questions it can and cannot answer. At minimum, before the next round, add: a numbered requirements section (functional, non-functional, platform), a Phase 0 section (see DEEPSEEK-2), a security/threat-model section (DEEPSEEK-4), a licensing/compliance section (DEEPSEEK-3), and acceptance criteria for the MVP.
- **Evidence:** reasoning only; `projects/jarvis/JarvisBot/spec.md` v0.1, line 97 (```` ```mermaid ````) and line 110 (last line, inside the block).
- **Confidence:** high

### DEEPSEEK-2 · Phase 0 and the requested path selection have no scope, evidence or exit criteria

- **Section:** Decision requested; §1; §6
- **Type:** gap
- **Severity:** major
- **Finding:** The “Decision requested” asks HUMAN to approve a Phase 0 feasibility spike and select a primary implementation path, but Phase 0 is never defined and §1 recommends parallel tracks rather than one path. There are no deliverables, test cases, selection criteria or GO/NO-GO evidence, so neither HUMAN nor an implementer can tell what the spike must prove or what “selected” means; the recommendation itself is not phrased as a decision option.
- **Proposed change:** Add a Phase 0 section with: (a) objective and non-goals; (b) a test matrix run against each candidate path — start/stop, chat round trip with streaming, tool call round trip (shell + file), approval allow/deny, cancellation, persistence across restart, offline operation, upgrade/rollback; (c) recorded environment (host OS, Docker version, model, endpoint, client/runtime versions, source revisions); (d) selection criteria with an explicit weighting (locality, UI parity, licence/ToS status, maintainability, setup time, resource use); (e) decision options for HUMAN, for example “approve Phase 0 only”, “approve Phase 0 and fund path X conditionally”, “stop”; (f) an exit gate requiring a signed comparison report, not an MVP. State that the §1 recommendation is an input to the decision, not the decision itself.
- **Evidence:** reasoning only; “Decision requested” line 7, §1 lines 15–22.
- **Confidence:** high

### DEEPSEEK-3 · The recommended paths conflict with the §4 non-goals and have no legal gate

- **Section:** §1; §2; §3 (licensing goal); §4
- **Type:** inconsistency
- **Severity:** major
- **Finding:** §4 excludes “Redistributing proprietary Grokbot binaries or bypassing licensing” and “Bypassing vendor terms of service or authentication requirements”, yet §1 recommends the two paths most exposed to those constraints: the “official-client shim” that keeps the proprietary client and translates its inference protocol, and a runtime built from “community reconstructions of the Grokbot codebase”. The spec never explains how either path stays inside the non-goals, and although §3 says licensing constraints must be documented before distribution, the file contains no licensing section, checklist or gate. Deciding path 1 or 2 without that determination could direct development into a ToS or copyright problem, which is a HUMAN decision with legal consequences.
- **Proposed change:** Add a compliance gate before any path work: for each path, record the artefacts used, their licence or lack of one, the vendor ToS clauses on client modification, protocol interception and account use, and whether local-only personal use is permitted; mark paths 1 and 2 “conditional — not approved until HUMAN records this determination”. State explicitly that no proprietary binary or code is redistributed and that the project does not facilitate authentication bypass; define what counts as “distribution” (source, container images, binaries, documentation). Make the gate a Phase 0 deliverable and a stop condition for the MVP, not a later task.
- **Evidence:** reasoning only; §1 lines 15–22, §3 line 61, §4 lines 63–70. I am not a lawyer and did not verify any licence or ToS text; the finding is that the document is internally inconsistent and lacks a gate, not that a particular path is unlawful.
- **Confidence:** high for the inconsistency; medium for the legal characterisation.

### DEEPSEEK-4 · No security baseline for shell execution, untrusted content, network egress or remote approval

- **Section:** §3; §5; §6
- **Type:** risk
- **Severity:** major
- **Finding:** The architecture gives the runtime shell, file and GUI tools plus a container, and §5 use cases 2–4 and 7 let the agent execute commands, take over the desktop and approve actions from a remote client, but the document states no threat model. In particular it does not address prompt injection from web pages, files, tool output or model endpoints; network egress from the sandbox (an agent with shell and unrestricted network can exfiltrate memory and credentials or reach internal services); host access through mounts, the Docker socket or credentials; or authentication of the mobile approval channel. “Secure” in §3 is therefore unenforceable.
- **Proposed change:** Add a security requirements section for HUMAN review: default-deny egress from the agent sandbox with an explicit allowlist; no Docker socket, host home directory or host credentials inside the sandbox; per-action approval bound to the exact command, arguments and paths, invalidated if they change; an authenticated, authorised approval channel (loopback by default, no unauthenticated remote bind); untrusted content (web, files, tool output, model text) treated as data, never as permission to widen scope; an append-only audit log of commands, approvals and denials; documented sandbox-escape and resource-limit behaviour; and a Phase 0 test for denied/expired approval and sandbox/egress failure.
- **Evidence:** reasoning only; §3 line 60, §5 use cases 2–4 and 7 (lines 86–91), §6 lines 97–110. Complements the enforcement-boundary finding in the CHATGPT review; this finding focuses on untrusted content, egress and the approval channel.
- **Confidence:** high

### DEEPSEEK-5 · “Local-first” has no enforceable offline or locality contract

- **Section:** §1; §3; §5
- **Type:** gap
- **Severity:** major
- **Finding:** The summary promises a “local or user-controlled” environment and §3 says “Work offline or with minimal cloud dependency where possible”, but “where possible” makes the goal untestable, and §5 use case 1 only says “with a local model endpoint”. The spec does not say whether the vendor client’s login, licence check, telemetry, update check or model-provider traffic is acceptable, so a shim-based implementation could pass every stated goal while remaining unusable offline. The primary property of the project is therefore not specified.
- **Proposed change:** Add a locality contract with a must/may split, for example: with all non-loopback network access blocked (except the configured local model endpoint), the tool must start, complete a chat round trip, execute an approved tool, persist memory across a restart, and run a scheduled routine; features that may require the internet (model download, vendor login, update check, web tools) must fail with an explicit message and be listed. Add a Phase 0 test that runs the matrix with external egress denied and records every external connection attempt.
- **Evidence:** reasoning only; §1 lines 11–22, §3 lines 51–61, §5 line 85.
- **Confidence:** high

### DEEPSEEK-6 · “OpenAI-compatible” is not defined; tool calling and streaming are assumed

- **Section:** §3; §6
- **Type:** gap
- **Severity:** minor
- **Finding:** The model provider adapter is required to talk to “any OpenAI-compatible endpoint”, but that label covers servers that implement only basic chat completions and not streaming or `tool_calls`, while the runtime in §6 depends on tool execution and §5 use case 1 assumes a chat loop. Without a minimum adapter contract, a local model can satisfy the wording and still fail the agent loop, and Phase 0 has no way to record which endpoints actually work.
- **Proposed change:** Define the adapter minimum: a chat-completions endpoint with streaming and native tool/function calls; endpoints without native tool calling are unsupported, or supported only through a documented emulation whose failure modes are stated. Add timeout, retry, cancellation, context-limit and error-mapping requirements, and require a per-model/per-endpoint capability row (streaming, tools, parallel tool calls, vision, context size) in the Phase 0 report.
- **Evidence:** reasoning only; §3 line 54, §6 lines 101–110. No endpoint was tested.
- **Confidence:** medium

### DEEPSEEK-7 · Multi-agent isolation and delegated permissions are undefined

- **Section:** §2; §3; §5; §6
- **Type:** risk
- **Severity:** minor
- **Finding:** §5 use case 5 promises per-agent memory, instructions and tool permissions and use case 7 delegates work to a local worker agent, but the architecture has one sandbox and does not say whether agents get a container each or share one. If several agents share a container or credential store, per-agent permissions and memory are not enforceable, and the cited `noid-bot` model (“persistent bots share a Docker container as their computer”) makes that design plausible rather than hypothetical.
- **Proposed change:** Define the trust and isolation model: one sandbox per agent or per task, with a read-only shared workspace where collaboration is needed; per-agent secrets and memory; cross-agent file access denied by default; a delegated agent receives an explicit capability set and cannot widen it or approve its own actions; and a test that one agent cannot read another’s memory or credentials. If a shared container is chosen, state the resulting limitation explicitly instead of promising per-agent permissions.
- **Evidence:** reasoning only; §2 line 45, §5 use cases 5 and 7 (lines 89, 91), §6.
- **Confidence:** medium

### DEEPSEEK-8 · Memory and log data have no privacy, retention or deletion rules

- **Section:** §3; §5
- **Type:** gap
- **Severity:** minor
- **Finding:** Persistent memory is a goal and a named target user is “privacy-sensitive”, but the spec defines no memory data model, storage location, retention period, encryption, export/deletion path, or rule for what context is sent to a model endpoint. Logs of shell commands and model traffic can contain credentials or personal data, and the approval workflow may store sensitive arguments; without rules, “local” does not by itself deliver the privacy the document promises.
- **Proposed change:** Add memory and log requirements: per-agent storage in a documented location; encryption at rest or an explicit decision that it is not provided; retention and deletion (user-triggered and on agent removal); redaction of secrets and configurable redaction of file contents in logs; export; and a statement that memory/context is sent only to the configured endpoint. Record where any telemetry goes.
- **Evidence:** reasoning only; §3 line 58, §5 lines 79 and 89.
- **Confidence:** high

**Top 3**

1. DEEPSEEK-1: complete the document — close the Mermaid fence and supply the missing requirements sections.
2. DEEPSEEK-2: define Phase 0’s evidence, exit criteria and the decision options HUMAN is being asked to choose.
3. DEEPSEEK-3 and DEEPSEEK-4: settle the legal/ToS gate and the security baseline before any path is approved or agent execution is enabled.

Result: complete
