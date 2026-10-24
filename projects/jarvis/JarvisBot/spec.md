# Spec Proposal: Local Grokbot Tool

**Document ID:** SPEC-LOCAL-GROKBOT-001  
**Status:** Draft for review  
**Version:** 0.1  
**Date:** 2026-10-24  
**Decision requested:** Approve Phase 0 feasibility spike and select a primary implementation path.

---

## 1. Summary

This proposal defines options and requirements for re-creating **Grokbot as a local tool**: a self-hosted or local-first agent environment that preserves as much of the original Grokbot experience as practical while running inference, tools, memory, and the “computer” environment on local or user-controlled infrastructure.

Four implementation paths are considered:

1. **Official-client shim** — keep the Grokbot desktop UI and connect it to a local runtime.
2. **Reconstructed local-first build** — use community reconstructions of the Grokbot codebase.
3. **Open-source alternative** — adopt a self-hosted agent platform with similar capabilities.
4. **DIY primitives** — assemble a custom local tool from containers, schedulers, memory files, and model APIs.

**Recommendation:** Use a phased approach. Start with a **shim-based MVP** for UI parity, validate a **local-first reconstructed runtime** in parallel, and keep an **open-source alternative** as a fallback if proprietary or licensing constraints block the reconstruction path.

---

## 2. Background and Context

Grokbot-style tools combine:

- A desktop or web chat interface.
- An agent runtime that can call tools, run commands, and process files.
- A persistent “computer” environment, often a container with a display.
- Memory and routine/event scheduling.
- Model inference through a cloud or OpenAI-compatible API.
- Approval workflows for risky actions.

Community tooling and guides already exist for several local variants:

| Path | Representative Tooling | Notes |
|---|---|---|
| Official-client shim | `grokbot-shim` | Connects installed Grokbot desktop app to a local host runtime. Translates inference protocol to local models or OpenAI-compatible APIs. Runs a local “Computer” via noVNC. Linux, Node.js 22.12+, Docker. |
| Local agent delegation | `grokbot-local-agent` | Delegates work from a Grokbot Linux instance to a local Pi agent using shell access and webhooks. |
| Reconstructed build | `grok-bot-0.18-reconstructed` | Unofficial reconstruction of Grok Bot 0.18.0. Windows-first, local-first runtime, works without a Cursor account, routes inference to OpenAI-compatible endpoints. |
| Reverse-engineering reference | `grok-bot-analysis` | Analysis of Grok Bot 0.70.2 covering client, API, agent architecture, and memory design. Reference only, not a runnable tool. |
| Open-source alternative | `noid-bot` | Durable, mobile-first web app for Pi agents. Persistent bots share a Docker container as their computer. Phone-based approval for risky actions. |
| Open-source alternative | `akeru-bot` | Local-first desktop/web/mobile clients. Named AI teammates with per-bot tools, instructions, and memory. Supports Claude, Codex, OpenCode, and other providers. |
| DIY | “Build your own Grok Bot” guides | Maps features to primitives: Docker container as computer, cron/event loops for routines, per-agent files for memory. |

---

## 3. Goals

- Provide a **local or user-controlled Grokbot-like environment**.
- Support **local inference** or routing to any OpenAI-compatible endpoint.
- Preserve the original **Grokbot UI** where feasible.
- Provide a **sandboxed computer environment** with Docker and optional noVNC.
- Support **persistent memory**, routines, and multi-agent workflows.
- Enable **approval workflows** for risky actions.
- Work **offline or with minimal cloud dependency** where possible.
- Keep the design **auditable, reproducible, and secure**.
- Document licensing and compliance constraints before distribution.

## 4. Non-Goals

- Redistributing proprietary Grokbot binaries or bypassing licensing.
- Bypassing vendor terms of service or authentication requirements.
- Building a production-grade hosted multi-tenant SaaS.
- Guaranteeing feature parity with every Grokbot release.
- Supporting every operating system in the first release.
- Replacing the user’s preferred model provider.

---

## 5. Target Users and Use Cases

**Primary users:**

- Developers who want a local coding/automation agent.
- Privacy-sensitive users who want local inference and local file processing.
- Power users who want persistent agents, routines, and approval gates.
- Researchers evaluating agent architectures.

**Primary use cases:**

1. Run a Grokbot-like assistant on a local machine with a local model endpoint.
2. Let an agent execute shell commands and file operations inside a container.
3. Watch or take over the agent’s desktop through noVNC.
4. Approve or deny risky actions from a desktop or mobile client.
5. Maintain per-agent memory, instructions, and tool permissions.
6. Schedule recurring routines and event-driven tasks.
7. Delegate work from a primary agent to a local worker agent.

---

## 6. Proposed Architecture

```mermaid
flowchart LR
    UI[Grokbot UI or Alternative Client] --> GW[Protocol / API Gateway]
    GW --> RT[Agent Runtime]
    RT --> MP[Model Provider Adapter]
    RT --> MEM[Memory Store]
    RT --> SCH[Event Scheduler / Routines]
    RT --> APP[Approval Service]
    RT --> SBX[Computer Sandbox]
    SBX --> DOCKER[Docker Container]
    SBX --> VNC[noVNC / Display]
    RT --> TOOLS[Tool / Shell / File APIs]
    MP --> LOCAL[Local Model Server]
    MP --> OAI[OpenAI-Compatible Endpoint]