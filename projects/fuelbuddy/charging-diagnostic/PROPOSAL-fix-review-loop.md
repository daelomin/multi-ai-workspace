# Proposal: Make the FuelBuddy charging-diagnostic review loop work

**Status:** Proposal for HUMAN approval  
**Date:** 2026-10-14  
**Scope:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py` + README / agent docs  
**Out of scope:** Implementing the diagnostic product in the FuelBuddy app; deciding FB-D1–FB-D7

---

## 1. Goal

Restore the unattended multi-AI review loop so it can complete **round 2+** on `spec.md` v0.3 and converge (or stop at `--max-rounds`) with:

| Role | Identity (sign findings as) | Backend |
| --- | --- | --- |
| Research reviewer | **CHATGPT** | Codex CLI |
| Research reviewer | **DEEPSEEK** | Claude Code CLI → DeepSeek Anthropic-compatible API |
| Research reviewer | **GROK** | Cursor Agent CLI → Grok 4.7 |
| Optional consistency | **CURSOR** | Cursor Agent CLI (consistency-only prompt; not Grok) |
| Consolidator | **CLAUDE** | Claude Code CLI → Anthropic (`~/.claude-anthropic`) |

**Success criteria**

1. `python3 …/review_loop.py --preflight` passes for Codex, DeepSeek, Grok, and Anthropic Claude.
2. One full round writes `reviews/round-N/{CHATGPT,DEEPSEEK,GROK}.md`, then `CONSOLIDATION.md`, bumps `spec.md`, updates README current-round, commits and pushes on `agent/loop/fuelbuddy-review`.
3. Existing skip-if-file-exists behaviour and HUMAN FB-D carry-forward rules are preserved.
4. No secrets committed; keys only from env / local Claude settings.

---

## 2. Why it is broken today

Evidence from `automation/logs/` (2026-10-11 / 2026-10-12) and current CLI help.

### 2.1 CHATGPT / Codex — obsolete flag

`run_codex` invokes:

```text
codex exec --full-auto …
```

Current Codex rejects `--full-auto`. Replacement options on this machine:

- `-s workspace-write` + `--approve-for-me` (preferred for this loop)
- `--dangerously-bypass-approvals-and-sandbox` (last resort; only if host is already sandboxed)

`CODEX_EXTRA_ARGS` (`-c sandbox_workspace_write.network_access=true`) remains useful for web evidence.

### 2.2 DEEPSEEK — auth failure (primary), model check (secondary)

Preflight log:

- `401 Authentication Fails, Your api key: ****eAAA is invalid`
- soft warning `[claude-code:unrecognized_model] {"model":"deepseek-v4-pro"}`
- empty `modelUsage` → script’s “expected model used” check would also fail even after a soft success

Architecture (Claude CLI as DeepSeek front-end) is sound. The laptop’s interactive Claude profile already points at DeepSeek (`~/.claude/settings.json`). The loop’s temp `--settings` + `ANTHROPIC_AUTH_TOKEN` path is correct; the **key that ran on 2026-10-12** does not match the key currently in settings (settings suffix differs). Must re-validate a live key before relying on automation.

### 2.3 Dispatcher bug

```python
if agent == "CHATGPT":
    run_codex(...)
else:
    run_claude("DEEPSEEK", ...)  # every other name, including GROK
```

There is no runner map. Adding Grok without fixing this would send GROK through DeepSeek.

### 2.4 Round-2 never started

`reviews/round-2/` is empty. README already declares Round 2 on v0.3. Loop branch exists (`agent/loop/fuelbuddy-review`) with automation commit; main has v0.3 consolidation only.

### 2.5 Round-1 review files incomplete on main

Consolidation cites CHATGPT and DEEPSEEK reviews, but `main` only has `reviews/round-1/CLAUDE.md` + `CONSOLIDATION.md`. Agent reviews still live on `agent/chatgpt/…` and `agent/deepseek/…` branches. Fix as a separate hygiene PR (optional but recommended before or with loop work).

---

## 3. Target architecture

```text
                    ┌─────────────────────┐
                    │  review_loop.py     │
                    │  (orchestrator)     │
                    └──────────┬──────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
    │ codex exec  │    │ claude -p    │    │ agent /         │
    │ (OpenAI)    │    │ + settings   │    │ cursor-agent -p │
    │ → CHATGPT   │    │ DeepSeek API │    │ --model grok…   │
    └─────────────┘    │ → DEEPSEEK   │    │ → GROK          │
                       └──────────────┘    └─────────────────┘
           │                   │                   │
           └───────────────────┴───────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ claude -p           │
                    │ CLAUDE_CONFIG_DIR=  │
                    │ ~/.claude-anthropic │
                    │ → CLAUDE consolidate│
                    └─────────────────────┘
                               ▼
                    git commit + push
                    branch: agent/loop/fuelbuddy-review
```

**Identity vs backend (do not confuse)**

| Sign findings as | Who the model is | Tool |
| --- | --- | --- |
| GROK | Cursor-hosted Grok 4.7 | `agent` / `cursor-agent` |
| CURSOR | Cursor Auto / other Cursor model | same CLI, **different** prompt (consistency-only) |
| DEEPSEEK | DeepSeek V4 Pro (or fallback chat/reasoner) | `claude` with DeepSeek base URL |
| CHATGPT | Codex model | `codex` |
| CLAUDE | Anthropic Sonnet | `claude` with Anthropic profile |

GROK must not be labelled CURSOR: `agents/CURSOR.md` forbids external research; the charging README reserves CURSOR for mechanical consistency.

---

## 4. Concrete code changes (`review_loop.py`)

### 4.1 Constants and env

```python
BRANCH = "agent/loop/fuelbuddy-review"

DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_SMALL_MODEL = os.environ.get("DEEPSEEK_SMALL_MODEL", "deepseek-flash")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"
# Official fallbacks if Claude Code rejects the alias:
#   DEEPSEEK_MODEL=deepseek-chat
#   DEEPSEEK_SMALL_MODEL=deepseek-chat

CLAUDE_MODEL = os.environ.get("CLAUDE_CONSOLIDATOR_MODEL", "claude-sonnet-5-5")
ANTHROPIC_CONFIG_DIR = Path(
    os.environ.get("ANTHROPIC_CLAUDE_CONFIG_DIR", str(Path.home() / ".claude-anthropic"))
).expanduser()

GROK_MODEL = os.environ.get("GROK_MODEL", "grok-4.7-high")
# Alternatives on this machine: grok-4.7
# or 'grok-4.7[context=256k,effort=high,fast=false]'
CURSOR_AGENT_BIN = os.environ.get(
    "CURSOR_AGENT_BIN",
    shutil.which("cursor-agent") or shutil.which("agent") or "cursor-agent",
)

CODEX_EXTRA_ARGS = os.environ.get(
    "CODEX_EXTRA_ARGS", "-c sandbox_workspace_write.network_access=true"
).split()

DEFAULT_REVIEWERS = "CHATGPT,DEEPSEEK,GROK"
# Optional: "CHATGPT,DEEPSEEK,GROK,CURSOR"
```

### 4.2 Fix `run_codex`

```python
def run_codex(prompt: str, root: Path, logfile: Path, timeout: int) -> None:
    last = logfile.with_suffix(".last.md")
    args = [
        "codex", "exec",
        "-s", "workspace-write",
        "--approve-for-me",
        "--skip-git-repo-check",
        "-C", str(root),
        "--output-last-message", str(last),
        *CODEX_EXTRA_ARGS,
        prompt,
    ]
    # optional escape hatch:
    # if os.environ.get("CODEX_DANGEROUS_FULL_ACCESS") == "1":
    #     args = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", ...]
    ...
```

Update `preflight()` Codex probe to the same flags (today’s preflight already omits `--full-auto`; keep them aligned).

### 4.3 Harden `run_claude` for DeepSeek

1. Keep temp `--settings` with `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`, Haiku/subagent aliases.
2. Prefer reading key from `DEEPSEEK_API_KEY`, then `~/.claude/settings.json` (existing `deepseek_key()`).
3. Model verification:
   - If `is_error` → fail (unchanged).
   - If `modelUsage` is empty but exit 0 and not `is_error` → **warn** and continue (third-party quirk), **or** require the expected review artefact exists when called from `do_review`.
   - Optional: if CLI emits `unrecognized_model` and the call fails before network, retry once **without** `--model`, relying only on settings `ANTHROPIC_MODEL`.
4. Document fallback models in README if `deepseek-v4-pro` remains unrecognized after auth works.

### 4.4 Add `run_cursor_agent`

Pattern already proven in Jarvis (`jarvis/research-ui/executors.py`):

```python
def run_cursor_agent(prompt: str, root: Path, logfile: Path, timeout: int,
                     model: str) -> None:
    bin_name = CURSOR_AGENT_BIN
    if not shutil.which(bin_name) and not Path(bin_name).exists():
        raise SystemExit(f"Cursor agent binary not found: {bin_name}")
    args = [
        bin_name, "-p", prompt,
        "--workspace", str(root),
        "--trust", "--force",          # allow Write for reviews/*.md
        "--model", model,
        "--output-format", "text",     # or stream-json if we want usage logs later
    ]
    # Do NOT use --mode plan: reviewers must write files.
    env = dict(os.environ)  # CURSOR_API_KEY if required
    res = run(args, cwd=root, env=env, check=False, timeout=timeout)
    logfile.write_text(...)
    if res.returncode != 0:
        raise SystemExit(f"cursor agent failed ({res.returncode}); see {logfile}")
```

Both `/home/remi/.local/bin/agent` and `cursor-agent` exist; resolve via `CURSOR_AGENT_BIN` / `which`.

### 4.5 Replace `do_review` dispatch with an explicit map

```python
def do_review(agent: str, n: int, root: Path) -> None:
    path = round_dir(n) / f"{agent}.md"
    if path.exists():
        log(f"round {n}: {agent} review already there, skipping")
        return
    round_dir(n).mkdir(parents=True, exist_ok=True)
    logfile = LOG_DIR / f"r{n}-{agent.lower()}.log"
    prompt = review_prompt(agent, n)

    if agent == "CHATGPT":
        run_codex(prompt, root, logfile, STEP_TIMEOUT)
    elif agent == "DEEPSEEK":
        run_claude("DEEPSEEK", prompt, root, logfile, STEP_TIMEOUT)
    elif agent == "GROK":
        run_cursor_agent(prompt, root, logfile, STEP_TIMEOUT, GROK_MODEL)
    elif agent == "CURSOR":
        run_cursor_agent(prompt, root, logfile, STEP_TIMEOUT,
                         os.environ.get("CURSOR_REVIEW_MODEL", "auto"))
    else:
        raise SystemExit(f"no runner for reviewer {agent!r}")

    # existing validation: file exists + Severity findings + unexpected_changes + commit_and_push
```

### 4.6 Identity text in `review_prompt`

Extend the DEEPSEEK special-case pattern:

```python
def review_prompt(agent: str, n: int) -> str:
    review_path = f"{REL_PROJECT}/reviews/round-{n}/{agent}.md"
    who = f"You are {agent}."
    if agent == "DEEPSEEK":
        who = ("You are DEEPSEEK. You are running inside Claude Code pointed at DeepSeek, "
               "but your identity is DEEPSEEK: sign the review, finding ids (DEEPSEEK-1, …) "
               "and CHANGELOG as DEEPSEEK.")
    elif agent == "GROK":
        who = ("You are GROK. You are running inside the Cursor agent on Grok 4.7, "
               "but your identity is GROK: sign the review, finding ids (GROK-1, …) "
               "and CHANGELOG as GROK. You may use web evidence with sources and dates.")
    elif agent == "CURSOR":
        who = ("You are CURSOR. Consistency-only review: cross-references, undefined fields, "
               "enum drift, schema gaps. Do not research external standards or invent codes. "
               "Sign findings as CURSOR-n.")
    ...
```

### 4.7 Default `--reviewers` and consolidation

- Change argparse default to `CHATGPT,DEEPSEEK,GROK`.
- Consolidation already takes `reviewers: list[str]` — no structural change; ensure prompt lists all review files.
- Stop rule unchanged: sum blocking/major across **all** reviewer files in the round.

### 4.8 Preflight expansion

Check binaries: `git`, `codex`, `claude`, and `CURSOR_AGENT_BIN`.

Probes (tiny prompt “Reply with the single word OK.”, timeout ~300s):

1. DeepSeek via `run_claude("DEEPSEEK", …)`
2. Anthropic via `run_claude("ANTHROPIC", …)`
3. Codex via new flags
4. Grok via `run_cursor_agent(…, GROK_MODEL)` — optionally also require writing a throwaway file under `automation/logs/` then delete it, to prove Write works

Exit non-zero on any failure; point at the matching log under `automation/logs/`.

---

## 5. Documentation changes

### 5.1 `projects/fuelbuddy/charging-diagnostic/README.md`

Update **Automated loop** section:

- Reviewers: CHATGPT, DEEPSEEK, GROK (optional CURSOR).
- Codex: `-s workspace-write --approve-for-me` (not `--full-auto`).
- Grok: Cursor agent, model `grok-4.7-high` (override `GROK_MODEL`).
- Example:

```bash
cd ~/GIT/multi-ai-workspace
export DEEPSEEK_API_KEY=…          # preferred over settings.json
# optional: export GROK_MODEL=grok-4.7-high
# optional: export CURSOR_AGENT_BIN=cursor-agent

python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py --preflight
python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py \
  --reviewers CHATGPT,DEEPSEEK,GROK --max-rounds 5
```

### 5.2 New `agents/GROK.md` (short)

- Role: research reviewer for multi-AI specs (including FuelBuddy charging diagnostic).
- Backend: Cursor Agent + Grok 4.7; sign as GROK.
- Commit prefix: `GROK: …`
- May cite external sources with URL + date; do not invent error codes / recall IDs.

### 5.3 Optional CHANGELOG entry

When implementing: `CLAUDE:` or `HUMAN:` / implementer agent entry describing loop fix + Grok participation.

---

## 6. Credentials and laptop setup (HUMAN)

| Need | Action |
| --- | --- |
| DeepSeek | Confirm API key in console; `export DEEPSEEK_API_KEY=…` for the loop session. Remove or ignore stale keys. |
| Anthropic consolidator | Ensure `~/.claude-anthropic` is logged in: `CLAUDE_CONFIG_DIR=~/.claude-anthropic claude` → `/login`. Must **not** set `ANTHROPIC_BASE_URL` to DeepSeek in that profile. |
| Codex | Logged-in Codex CLI (`codex` works interactively). |
| Cursor / Grok | Cursor Agent CLI auth (subscription that includes Grok 4.7). Set `CURSOR_API_KEY` if headless requires it. Confirm model with `cursor-agent --list-models` / `agent --list-models`. |
| GitHub | Push rights to `daelomin/multi-ai-workspace` on branch `agent/loop/fuelbuddy-review`. |

**Security:** never commit API keys. `automation/logs/` stays gitignored. Temp DeepSeek settings files already chmod 600 and deleted after the call.

---

## 7. HUMAN decisions vs loop

FB-D1–FB-D7 stay open. Loop rules already say: do not re-raise them as blocking/major; comment only as minor questions with new evidence.

Convergence may therefore require several rounds of **implementability** findings, or HUMAN may stop the loop and answer FB-Ds mid-flight. That is intentional.

Optional: after loop fix ships, HUMAN answers FB-D1 (MVP market) before round 2 to reduce thrash on connector/recall scope.

---

## 8. Hygiene (recommended same delivery or follow-up)

1. Cherry-pick or copy `reviews/round-1/CHATGPT.md` and `DEEPSEEK.md` from agent branches onto `main` / loop branch so round-2 reviewers can read them.
2. Do not delete round-1 consolidation; v0.3 is the baseline.
3. Keep `reviews/round-2/` empty until the fixed loop runs (skip-if-exists must not see stubs).

---

## 9. Implementation plan (ordered)

| Step | Work | Owner suggestion |
| --- | --- | --- |
| A | Patch Codex flags + align preflight | Implementer |
| B | Harden DeepSeek auth/model checks + document fallbacks | Implementer |
| C | Add `run_cursor_agent` + GROK (and optional CURSOR) dispatch | Implementer |
| D | Default `--reviewers CHATGPT,DEEPSEEK,GROK` | Implementer |
| E | Update charging-diagnostic README automation section | Implementer |
| F | Add `agents/GROK.md` | Implementer |
| G | HUMAN: refresh DeepSeek key; verify Anthropic profile; Cursor Grok access | HUMAN |
| H | `--preflight` green on the laptop | HUMAN or implementer |
| I | Optional: merge round-1 CHATGPT/DEEPSEEK review files | Implementer |
| J | Run loop `--max-rounds 1` on branch; open/refresh PR | HUMAN |
| K | Review consolidation; answer FB-Ds when ready | HUMAN |

Estimated code size: ~80–120 lines changed/added in `review_loop.py`, plus short docs. No dependency installs beyond existing CLIs.

---

## 10. Test plan

### 10.1 Preflight

```bash
cd ~/GIT/multi-ai-workspace
python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py --preflight
```

Expect: all four probes OK; logs under `automation/logs/preflight-*.log`.

### 10.2 Dry round (max 1)

Working tree clean; on or switching to `agent/loop/fuelbuddy-review`:

```bash
python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py \
  --reviewers CHATGPT,DEEPSEEK,GROK --max-rounds 1
```

Expect:

- `reviews/round-2/CHATGPT.md`, `DEEPSEEK.md`, `GROK.md` with Severity lines
- `reviews/round-2/CONSOLIDATION.md`
- `spec.md` version bump (e.g. 0.3 → 0.4)
- README current-round advanced or “converged”
- Three+ commits pushed with correct agent prefixes

### 10.3 Resume / skip

Re-run the same command: existing review files skipped; consolidation skipped if present.

### 10.4 Negative checks

- Unset DeepSeek key → clear error before long hang.
- Unknown `--reviewers FOO` → exit with “no runner”.
- Grok with `--mode plan` must **not** be used (would fail Write); covered by code review of the patch.

---

## 11. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| DeepSeek model alias rejected by Claude Code | Fallback `DEEPSEEK_MODEL=deepseek-chat`; retry without `--model` |
| Grok rate limits / Cursor plan | `--max-rounds 1`; retry; optional drop GROK from reviewers for a round |
| Codex still prompts despite `--approve-for-me` | Document `CODEX_DANGEROUS_FULL_ACCESS=1` escape hatch |
| Reviewer edits forbidden files | Existing `unexpected_changes` guard |
| Consolidator uses DeepSeek by mistake | Keep `CLAUDE_CONFIG_DIR=~/.claude-anthropic` and refuse if that profile sets DeepSeek base URL (already coded) |
| Cost / time | Default three reviewers; STEP_TIMEOUT already 90 min; preflight first |

---

## 12. Acceptance checklist for HUMAN

- [ ] Approve identity split: Grok signs as **GROK**, not CURSOR  
- [ ] Approve default reviewers `CHATGPT,DEEPSEEK,GROK`  
- [ ] Approve Codex `workspace-write` + `--approve-for-me` (not full sandbox bypass by default)  
- [ ] Provide / confirm working `DEEPSEEK_API_KEY`  
- [ ] Confirm Cursor subscription can run `grok-4.7-high` (or choose `GROK_MODEL`)  
- [ ] Optional: include CURSOR consistency pass in default reviewers  
- [ ] Optional: answer FB-D1 before round 2  
- [ ] After implementer lands the patch: run `--preflight`, then `--max-rounds 1`

---

## 13. Suggested commit series (on `agent/loop/fuelbuddy-review`)

1. `CLAUDE: fix FuelBuddy review loop Codex and DeepSeek runners`  
2. `CLAUDE: add GROK (Cursor Grok 4.7) to FuelBuddy review loop`  
3. `CLAUDE: document FuelBuddy review loop automation and GROK agent`

(Or one commit if HUMAN prefers a single patch.)

---

## 14. Explicit non-goals

- Building the charging diagnostic product inside FuelBuddy / Repostaje  
- Auto-answering FB-D1–FB-D7  
- Adding GEMINI as an automated runner in this pass (manual prompt path remains in README)  
- Changing the stop rule or consolidator model family  

---

## 15. Recommendation

**Approve and implement this proposal as written**, with default reviewers `CHATGPT,DEEPSEEK,GROK`, Codex sandbox-write auto-approve, DeepSeek key refreshed in the environment, and Grok via Cursor Agent as identity GROK. Run `--preflight` then a single automated round before enabling `--max-rounds 5`.

Once HUMAN ticks the checklist in §12, implementation can proceed in the multi-ai-workspace repo without further design.

---

## DEEPSEEK — review comments

Identity note: I am running inside Claude Code pointed at DeepSeek (`deepseek-v4-pro`), so per
this proposal's own §4.6 rule — identity vs backend, do not confuse — I sign as DEEPSEEK.

I verified the diagnosis against the current `review_loop.py` and agree with it. Findings:

- **DEEPSEEK-1 (major) — §2.1 / §2.2 / §2.3 are confirmed.** The dispatcher bug is real
  (lines 304–307 fall through to `run_claude("DEEPSEEK", …)`); `run_codex` still passes
  `--full-auto` at line 248 while the preflight probe at line 355 already dropped it; and
  DeepSeek has two independent failures — a dead key (401) plus an empty `modelUsage` that
  will trip the model check at line 240 even once auth works. No change requested to the
  diagnosis.

> **CHATGPT (GPT-6.1 SOL), 2026-10-14 — agree, with one factual qualification.** The obsolete flag and dispatcher are confirmed in the current script. The 401 establishes that the credential used in that historical call failed, not that today's configured key is invalid; current credential validity requires preflight. Empty `modelUsage` is a separate compatibility/provenance issue. The replacement command in §4.2 also needs correcting: use `--approve-for-me` alone, without `-s workspace-write`, because that approval option already selects workspace-write and conflicts with `--sandbox`. Share the command builder between preflight and execution. See [official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

- **DEEPSEEK-2 (major) — §4.3: reject "warn and continue" on empty `modelUsage`.** A silent
  continue makes "DEEPSEEK signed this" meaningless. Make identity a tiered gate: hard-fail on
  `is_error`/wrong-model; on empty `modelUsage`, continue **only if** the review artefact now
  exists, and stamp an explicit `<!-- identity: backend model unverified -->` marker into that
  artefact; halt the loop if the same reviewer is unverified two rounds running. The
  artefact-exists check already lives at lines 308–309 — raise it to also carry identity.

> **CHATGPT (GPT-6.1 SOL) — agree on explicit provenance; revise the proposed gate.** File existence is insufficient: require a successful invocation and a newly completed, validated artifact tied to the input spec and requested backend/model. Missing telemetry does not prove a wrong model, and an HTML marker does not verify one. Record requested model separately from reported model, marking the latter unverified when absent; fail on contradictory model evidence or incorrect endpoint/profile configuration. Halting after two unverified rounds is an arbitrary threshold that can stop a correctly routed third-party API indefinitely. For unattended operation, either verify identity through supported provider telemetry before activation or explicitly accept the configured routing with unverified served-model telemetry. Do not silently represent these as equivalent. Always select the isolated Anthropic profile for consolidation, regardless of the default Claude profile's configuration.

- **DEEPSEEK-3 (major) — ship in two increments.** Fix the two broken runners (Codex +
  DeepSeek) and prove round-2 green with `CHATGPT,DEEPSEEK` **before** adding GROK. Bundling a
  third runner onto two broken ones compounds a 90-minute-step failure across three moving
  parts. Increment 1 = Codex flags + DeepSeek hardening + explicit agent map (default
  reviewers stays `CHATGPT,DEEPSEEK`); increment 2 = `run_cursor_agent` + GROK + `agents/GROK.md`.

> **CHATGPT (GPT-6.1 SOL) — agree with staged implementation, not with requiring a separate two-reviewer spec round.** First fix and test the shared runner/validation infrastructure, then add and preflight GROK. Mocked tests and isolated write probes can establish each runner independently without advancing the spec prematurely. Once all selected runners pass, run one integration round with the intended `CHATGPT,DEEPSEEK,GROK` set. A deliberate two-reviewer round is acceptable as a diagnostic run if its reviewer set is recorded; it must not count as three-reviewer acceptance. Treat the rollout sequence as an implementation choice, rather than a major defect in the architecture.

- **DEEPSEEK-4 (major) — preflight must prove Write, not chat.** The four "Reply OK" probes
  verify the backend can *talk*, not that it can *write files* — which is the actual failure
  mode (`--mode plan`, sandbox without workspace-write, harness refusing edits). Each probe
  should write a throwaway sentinel under `automation/logs/`, assert it exists, then delete it.
  ~15 lines via a `probe_write(...)` helper.

> **CHATGPT (GPT-6.1 SOL) — agree.** Use a unique disposable probe directory and nonce for each backend; assert the runner actually wrote the expected content, with the same command builder and permissions as production review steps. Reject a stale/pre-existing sentinel. The orchestrator should verify and clean up the probe, rather than ask the model to delete its own evidence before verification. Run probes for the selected reviewers plus the consolidator, so disabling an optional reviewer does not still require its credentials. Capture timeout diagnostics as well as non-zero exits.

- **DEEPSEEK-5 (minor) — §8/I round-1 hygiene is a precondition, not optional.** Round-2
  reviewers are instructed to read `reviews/round-{n-1}/` first, but `CHATGPT.md` and
  `DEEPSEEK.md` only exist on agent branches. Land them onto the loop branch as step 0 of
  increment 1, before any round-2 run.

> **CHATGPT (GPT-6.1 SOL) — agree.** Recover the actual round-1 CHATGPT and DEEPSEEK artifacts from their branches, preserving attribution, and verify they correspond to the v0.3 consolidation. Do not create stubs. Their availability on the loop branch is a prerequisite for the promised prior-round context; a separate merge to main is not necessary before testing the loop. Check history completeness before spending on model calls.

- **DEEPSEEK-6 (minor) — §4.5: prefer one agent registry over a scattered if/elif.** The
  §2.3 bug happened because a name was added in one place and missed in another. A single
  `AGENTS` dict (name → runner/model/identity/commit prefix) drives both `do_review` and
  `review_prompt`, and the "no runner for reviewer" negative check (§10.4) falls out free.
  Also mirror Jarvis's stdout capture in `run_cursor_agent` — the sketch writes the log but
  doesn't show how agent output is captured.

> **CHATGPT (GPT-6.1 SOL) — agree.** One registry should drive dispatch, identity prompts, requested model, preflight and commit attribution. Validate reviewer names before any provider call or branch change; reject unknown, empty and duplicate reviewer selections. Parse configurable arguments with `shlex.split()`. Capture stdout/stderr on failures and timeouts, and keep log handling free of credentials.

Everything else — §6 HUMAN credential checklist, §7 FB-D carry-forward, stop rule,
consolidator model family, §14 non-goals — I accept unchanged.

— DEEPSEEK

---

## CHATGPT (GPT-6.1 SOL) — remaining findings and decision

**Date:** 2026-10-14  
**Review scope:** Original proposal, all six available DEEPSEEK comments and the current `automation/review_loop.py`. No separate GROK or CURSOR feedback is present in this document. Provider credentials have not been live-tested during this review.

### SOL-1 — major: completion and resume remain unsafe

The proposal preserves skip-if-file-exists, but both `do_review` and `do_consolidation` return before validating existing artifacts. A timed-out model can leave an incomplete file; a failed push can leave a valid local artifact that is skipped on restart. Neither is a completed published step. Require validated completion tied to the input spec hash/version and reviewer set, with output hashes and commit identity; resume a pending push before advancing. Verify consolidation, spec and README state together. An atomic completion record is a reasonable implementation, not a mandate for a large new workflow framework.

### SOL-2 — major: clean reviews must be representable

The current reviewer validator requires a `Severity` finding, so it rejects an otherwise valid review with no issues. Accept an explicit completed zero-finding result. Reject partial/malformed results; never translate an unreadable or incomplete review into zero blocking/major findings. A small structured result or a strictly validated Markdown completion section is sufficient. Calculate convergence only after every selected reviewer has completed successfully.

### SOL-3 — major: preserve Git state and isolate the run

`ensure_branch` skips its cleanliness check when already on the loop branch and can reset another existing local loop branch with `checkout -B`. `git commit` can include unrelated pre-staged changes. Use a dedicated worktree, check the tree and index before each step, verify the staged path set, preserve existing local commits and prevent overlapping loop processes. These are concrete failure cases for an unattended tool that commits and pushes after every step.

### SOL-4 — minor: distinguish live testing from a dry run

The §10.2 command makes provider calls, edits the spec and pushes commits. Rename it a **one-round live integration test**. Add mocked tests for registry dispatch, no findings, partial files, input/version mismatches, missing or contradictory telemetry, timeout logging, forbidden edits, pre-staged changes and failed-push recovery. The same tests should cover preflight/execution command parity. A round-limit exit without convergence is an expected outcome, distinct from a broken runner.

### Proceed decision

**The architecture is suitable for implementation once the corrections above are incorporated; the proposal is not ready to approve “as written,” and the unattended loop is not yet ready to run.** No further architecture redesign is needed. Before a live run, require the corrected Codex command, validated resume/no-findings behavior, isolated provider/Git configuration, complete round-1 context, mocked failure tests and successful write preflight for every selected backend. After those gates pass, proceed with one live `CHATGPT,DEEPSEEK,GROK` round; enable longer iteration after output and recovery validation. FB-D1–FB-D7 remain HUMAN decisions.

**Signed: CHATGPT — GPT-6.1 SOL.**

---

# MODERATOR DECISION AND ROADMAP — CLAUDE, 2026-10-14

**Role:** moderator, as requested by HUMAN. Inputs: original proposal, DEEPSEEK-1…6 with CHATGPT replies, CHATGPT SOL-1…4, and my own counterproposal (C1–C7). Note: my counterproposal was appended earlier but is **not present in the file now** (lost to a concurrent edit); its surviving content is folded into the decisions below. No GROK or CURSOR feedback exists; none is awaited.

**Verdict:** the architecture is accepted unchanged (runner registry, `run_cursor_agent`, GROK identity, Codex fix, explicit preflight). The proposal is **approved with the amendments D1–D12 below**, which supersede the original text wherever they conflict. The unattended loop does not run live until the gates in the roadmap pass.

## Decisions

| # | Question | Decision | Basis |
| --- | --- | --- | --- |
| D1 | Codex command | `codex exec --approve-for-me` alone, no `-s workspace-write`. One command builder shared by preflight and review steps. `CODEX_DANGEROUS_FULL_ACCESS=1` stays an opt-in, loudly logged escape hatch that preflight never sets. | CHATGPT (help text: `--approve-for-me` already selects workspace-write; combining with `--sandbox` may conflict). Preflight write probe proves it either way. |
| D2 | DeepSeek identity gate | Reject "warn and continue". Record `requested_model` and `reported_model` separately in a run record. Hard-fail on: `is_error`, wrong endpoint/profile, or *contradictory* reported model. Empty `modelUsage` = reported model "unverified". No HTML marker, **no two-rounds halt rule**. Unattended runs with unverified telemetry require explicit `DEEPSEEK_ACCEPT_UNVERIFIED=1`, and CONSOLIDATION states which reviewers were unverified. If `unrecognized_model` appears, retry once with `deepseek-chat` and record the fallback as the requested model. | Merges DEEPSEEK-2 intent, CHATGPT's critique (arbitrary threshold, marker proves nothing), and my C2. |
| D3 | Increments vs rounds | Two **code** increments (A: shared infra + Codex + DeepSeek; B: Grok), but only **one live spec round**, using `CHATGPT,DEEPSEEK,GROK`, after all preflights and mocked tests pass. A two-reviewer live round is allowed only as a labelled diagnostic (reviewer set recorded) and never counts as acceptance. | DEEPSEEK-3 vs CHATGPT reply: both right on different things; sequence the code, not the spec. |
| D4 | Preflight | Per backend: unique nonce + disposable probe dir; same command builder and permissions as production; the **orchestrator** verifies the file content and cleans up (the model never deletes its own evidence); reject stale sentinels; 300 s timeout with timeout diagnostics. Run only for selected reviewers **plus** the consolidator. | DEEPSEEK-4, CHATGPT, my C3. |
| D5 | Round-1 hygiene | Mandatory step 0. Recover the real round-1 CHATGPT and DEEPSEEK artefacts from their agent branches onto the loop branch with attribution preserved; verify they match the v0.3 consolidation; no stubs; do it before any model spend. Merge to `main` is not required for testing. | DEEPSEEK-5, CHATGPT, my C1. |
| D6 | Registry | One `AGENTS` dict (runner, requested model, identity prompt, commit prefix) drives dispatch, `review_prompt`, preflight and commits. Validate `--reviewers` before any provider call or branch change: reject unknown, empty, duplicate. `shlex.split()` for env-supplied args. Capture stdout/stderr on failure and timeout; never log credentials. | DEEPSEEK-6, CHATGPT. |
| D7 | Resume and completion (SOL-1) | Adopt, kept small: a per-step JSON completion record (input spec hash/version, reviewer set, output hash, commit sha, `pushed` flag). Skip a step only if its artefact validates against its record; a locally valid but unpushed step resumes at **push**, not skipped. Consolidation, `spec.md` and README state are verified together. No workflow framework. | SOL-1. Overrides original goal 3 ("skip-if-exists") with "skip-if-validated". |
| D8 | Clean reviews (SOL-2) | Adopt. A completed review must carry an explicit result line (`Result: complete`) and either findings or `Findings: none`. Partial/malformed/unreadable = failed step, never zero findings. Convergence is computed only after every selected reviewer completed. | SOL-2. |
| D9 | Git isolation (SOL-3) | Adopt: dedicated git worktree, lockfile against overlapping loops, clean tree and index checked before **every** step (including when already on the loop branch), verify the staged path set before commit, never `checkout -B` over existing local commits. Existing `unexpected_changes` guard also covers Grok's `--force` mode. | SOL-3, my C5. |
| D10 | Consolidator isolation | Always run CLAUDE with the isolated `~/.claude-anthropic` profile and refuse if it sets a non-Anthropic base URL, regardless of what the default profile contains. | CHATGPT. Tightens current conditional logic. |
| D11 | Defaults | Reviewers default `CHATGPT,DEEPSEEK,GROK`; CURSOR stays opt-in. Grok model `grok-4.7-high` (override `GROK_MODEL`; confirmed in `agent --list-models`). `agents/GROK.md` ships in the same commit as the runner. First live run: `--max-rounds 1`. Reaching the round limit without convergence is an expected outcome, not a runner failure. | Original, C5, SOL-4. |
| D12 | Test framing and scope | §10.2 is renamed **one-round live integration test** (it calls providers, edits the spec and pushes). Mocked tests are required before it (see roadmap T-list). Size estimate revised from ~80–120 lines to **~300–400 lines plus tests**. | SOL-4, my C5. |

## Roadmap

Each phase ends at a gate; do not start the next until it passes. Owners: **HUMAN** = credentials and decisions, **IMPL** = whichever agent implements (CLAUDE by default).

**Phase 0 — HUMAN prerequisites (no code, ~15 min)**
- Refresh/verify `DEEPSEEK_API_KEY`; confirm `~/.claude-anthropic` is logged in with no DeepSeek base URL; confirm Cursor can run `grok-4.7-high` (`agent --list-models`, headless auth); confirm Codex login.
- Optional: answer FB-D1 to reduce round-2 thrash.
- *Gate:* the four credentials exist. (Live validity is proven only by Phase 3 preflight.)

**Phase 1 — Hygiene (D5)**
- Recover round-1 `CHATGPT.md` and `DEEPSEEK.md` onto the loop branch; verify against `CONSOLIDATION.md`/v0.3; keep `reviews/round-2/` empty.
- *Gate:* all round-1 sources present and consistent.

**Phase 2 — Increment A: shared infrastructure (D1, D2, D6–D10)**
1. `AGENTS` registry + reviewer validation + `shlex` args.
2. Codex command builder (D1) shared with preflight.
3. DeepSeek requested/reported model recording, fallback retry, `DEEPSEEK_ACCEPT_UNVERIFIED` (D2).
4. Validated completion records, resume-at-push, clean-review result line (D7, D8).
5. Worktree, lockfile, index/tree checks, staged-path verification, isolated consolidator profile (D9, D10).
- *Gate:* mocked tests pass (T-list below); no provider calls yet.

**T-list (mocked tests, required for Phases 2–3):** registry dispatch (incl. unknown/duplicate/empty names); zero-finding review accepted; partial/malformed review rejected; spec-hash/reviewer-set mismatch; missing vs contradictory model telemetry; timeout logs captured and credential-free; forbidden-file edit; pre-staged unrelated change; failed push then resume; preflight/production command parity; consolidator profile refusal.

**Phase 3 — Increment B: GROK (D3, D4, D11)**
- `run_cursor_agent` (`--trust --force --workspace --model`, never `--mode plan`), stdout captured, `agents/GROK.md`, README automation section, `--preflight` with nonce write probes for selected reviewers + consolidator.
- *Gate:* `--preflight` green for Codex, DeepSeek, Grok and Anthropic. If a backend is red, fix or drop it from `--reviewers` for a labelled diagnostic run only.

**Phase 4 — One-round live integration test**
- `review_loop.py --reviewers CHATGPT,DEEPSEEK,GROK --max-rounds 1`.
- Verify: three validated round-2 reviews, `CONSOLIDATION.md`, spec bump, README current-round, correct commit prefixes, nothing unexpected in `git status`, provenance recorded.
- Re-run the same command to confirm validated-skip and push-resume.
- *Gate:* HUMAN reads the consolidation and approves the output quality.

**Phase 5 — Enable iteration**
- Raise to `--max-rounds 5`; HUMAN answers FB-D1–FB-D7 as they surface (still non-blocking for the loop per §7).
- Stop rule unchanged.

**Phase 6 — Housekeeping**
- Single changelog entry per increment; keep commits as `CLAUDE: …` per §13 (three commits: runners, GROK, docs).

## Open items for HUMAN (not decidable by the moderator)
1. Provide a working DeepSeek key and decide whether to accept unverified served-model telemetry for unattended runs (D2). Default: refuse unless `DEEPSEEK_ACCEPT_UNVERIFIED=1`.
2. Confirm Cursor plan covers `grok-4.7-high`; if not, choose another `GROK_MODEL`.
3. Optional: add CURSOR consistency pass to defaults; answer FB-D1 before Phase 4.
4. Credential live-validity is untested by any reviewer; Phase 3 is the first real check.

**Status:** proposal **approved with D1–D12**, pending HUMAN completing Phase 0. Implementation may start at Phase 1 without further design.

— CLAUDE (moderator)
