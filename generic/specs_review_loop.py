#!/usr/bin/env python3
"""Automated multi-AI review loop for a project spec (spec.md + README.md).

One round = CHATGPT review (Codex CLI) -> DEEPSEEK review (Claude Code on the
DeepSeek API) -> GROK review (Cursor agent, Grok 4.7) -> CLAUDE consolidation
(Claude Code on Anthropic, Sonnet).
The script commits and pushes after each step, then starts the next round,
until a round has no `blocking` or `major` finding (README stop rule) or
--max-rounds is reached.

State is the files in reviews/round-N/, as in the README: a step whose file
already exists is skipped, so the loop can be stopped and restarted at any time.

The project folder must hold spec.md and a README.md with a '**Round N**' line;
an optional decisions.md lists decisions HUMAN has settled.

Run from anywhere:
    python3 generic/specs_review_loop.py --project projects/fuelbuddy/charging-diagnostic \
        --name FuelBuddy --preflight
    python3 generic/specs_review_loop.py --project projects/fuelbuddy/charging-diagnostic --name FuelBuddy
The branch defaults to agent/loop/<name>-review; override it with --branch.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent

# Project settings, filled in by configure() from --project / --name / --branch.
PROJECT: Path = Path()
REL_PROJECT = ""
README: Path = Path()
SPEC: Path = Path()
DECISIONS: Path = Path()
LOG_DIR: Path = Path()
NAME = ""
BRANCH = ""
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"
CLAUDE_MODEL = os.environ.get("CLAUDE_CONSOLIDATOR_MODEL", "claude-sonnet-5-5")
# Claude Code profile that talks to Anthropic. ~/.claude points at DeepSeek on
# the ZenBook, so the consolidator uses its own config dir (log in once there).
ANTHROPIC_CONFIG_DIR = Path(
    os.environ.get("ANTHROPIC_CLAUDE_CONFIG_DIR", str(Path.home() / ".claude-anthropic"))
).expanduser()
# Claude Code profile for the DeepSeek reviewer. It must not be ~/.claude: a claude.ai login there
# (OAuth) takes precedence and its token would be sent to DeepSeek, which answers 401.
DEEPSEEK_CONFIG_DIR = Path(
    os.environ.get("DEEPSEEK_CLAUDE_CONFIG_DIR", str(Path.home() / ".claude-deepseek"))
).expanduser()
GROK_MODEL = os.environ.get("GROK_MODEL", "grok-4.7-high")
CURSOR_REVIEW_MODEL = os.environ.get("CURSOR_REVIEW_MODEL", "auto")
CURSOR_AGENT_BIN = os.environ.get(
    "CURSOR_AGENT_BIN", shutil.which("cursor-agent") or shutil.which("agent") or "cursor-agent"
)
STEP_TIMEOUT = int(os.environ.get("REVIEW_STEP_TIMEOUT", str(90 * 60)))
CODEX_EXTRA_ARGS = shlex.split(
    os.environ.get("CODEX_EXTRA_ARGS", "-c sandbox_workspace_write.network_access=true")
)
CODEX_SESSIONS = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions"
# USD per 1M tokens: (fresh input, cached input, cache write, output). Source:
# https://developers.openai.com/api/docs/pricing (read 2026-10-14). Override with CODEX_PRICING_JSON,
# e.g. '{"m": {"standard": {"short": [2, 0.1, 2.5, 10], "long": [4, 0.2, 5, 15]}, "fast": {...}}}'.
CODEX_PRICES = {"gpt-6.1-sol": {
    "standard": {"short": (2.00, 0.10, 2.50, 10.00), "long": (4.00, 0.20, 5.00, 15.00)},
    "fast": {"short": (4.00, 0.20, 5.00, 20.00), "long": (8.00, 0.40, 10.00, 30.00)}}}
if os.environ.get("CODEX_PRICING_JSON"):
    CODEX_PRICES.update(json.loads(os.environ["CODEX_PRICING_JSON"]))
# Codex Fast service tier (about 2x speed at 2x price on gpt-6.1-sol). Empty = standard tier.
CODEX_SERVICE_TIER = os.environ.get("CODEX_SERVICE_TIER", "").strip()
# Per-request input size above which the long-context tier applies. Unknown by default: the
# cost is then reported for both tiers (short = estimate, long = upper bound).
CODEX_LONG_CONTEXT_TOKENS = int(os.environ.get("CODEX_LONG_CONTEXT_TOKENS", "0")) or None
DEEPSEEK_FALLBACK_MODEL = "deepseek-chat"
# Without served-model telemetry (empty modelUsage) a DeepSeek review is "unverified";
# unattended runs must opt in to that explicitly.
DEEPSEEK_ACCEPT_UNVERIFIED = os.environ.get("DEEPSEEK_ACCEPT_UNVERIFIED") == "1"

KNOWN_REVIEWERS = {"CHATGPT", "DEEPSEEK", "GROK", "CURSOR"}
SEVERITY_RE = re.compile(r"\*\*Severity:\*\*\s*\**\s*(blocking|major|minor)", re.I)
ROUND_RE = re.compile(r"\*\*Round (\d+)\*\*")
VERSION_RE = re.compile(r"version (\d+\.\d+)", re.I)

REVIEW_RULES = """\
Automated loop rules (they override anything in the README about git or pull requests):
- Write ONLY {review_path} and a new entry at the top of CHANGELOG.md (repository root, \
same format as the existing entries, Agent: {agent}). Do not edit spec.md or any other file.
- Do not run git, do not create branches, do not open pull requests: the loop commits and \
pushes your files for you as "{agent}: {name} spec review round {n}".
{decisions_rule}- HUMAN is not answering during the loop. Items already listed as open HUMAN decisions in \
the previous CONSOLIDATION.md must not be raised again as blocking or major findings; \
comment on them only if you have new evidence, as a `question` of severity `minor`.
- Severity discipline: `blocking` and `major` keep the loop running, so use them only for \
problems that would make the spec unsafe, wrong or unimplementable. Use `minor` for the rest.
- Do not repeat findings that the previous consolidation already accepted and merged, \
unless the merged text is still wrong.
- End the review file with a line `Result: complete`. If you have no findings, write a line \
`Findings: none` before it. A file without `Result: complete` is treated as unfinished.
- When the file is written, stop."""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def configure(project: str | Path, name: str | None = None, branch: str | None = None) -> None:
    """Point the loop at one project folder. A relative path is taken from the workspace root.

    name labels commits and prompts (default: the folder under projects/, else the folder's own
    name); branch defaults to agent/loop/<name>-review.
    """
    global PROJECT, REL_PROJECT, README, SPEC, DECISIONS, LOG_DIR, NAME, BRANCH
    path = Path(project).expanduser()
    PROJECT = (path if path.is_absolute() else WORKSPACE / path).resolve()
    if not PROJECT.is_dir():
        raise SystemExit(f"project folder not found: {PROJECT}")
    top = Path(run(["git", "rev-parse", "--show-toplevel"], cwd=PROJECT).stdout.strip()).resolve()
    REL_PROJECT = PROJECT.relative_to(top).as_posix()
    README = PROJECT / "README.md"
    SPEC = PROJECT / "spec.md"
    DECISIONS = PROJECT / "decisions.md"
    LOG_DIR = PROJECT / "automation" / "logs"  # stays with the project; keep it gitignored
    parts = Path(REL_PROJECT).parts
    NAME = name or (parts[1] if len(parts) > 1 and parts[0] == "projects" else PROJECT.name)
    BRANCH = branch or f"agent/loop/{slug(NAME)}-review"


def decisions_note(rule: str) -> str:
    return rule if DECISIONS.is_file() else ""


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None,
        check: bool = True, capture: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    # stdin=DEVNULL: `codex exec` waits for piped stdin to EOF, which hangs an unattended run.
    res = subprocess.run(cmd, cwd=cwd, env=env, text=True, timeout=timeout,
                         capture_output=capture, stdin=subprocess.DEVNULL)
    if check and res.returncode != 0:
        raise SystemExit(f"command failed ({res.returncode}): {' '.join(cmd)}\n"
                         f"{res.stdout or ''}\n{res.stderr or ''}")
    return res


def repo_root() -> Path:
    return Path(run(["git", "rev-parse", "--show-toplevel"], cwd=PROJECT).stdout.strip())


# --- state ---------------------------------------------------------------

def current_round() -> int:
    text = README.read_text(encoding="utf-8")
    m = ROUND_RE.search(text)
    if not m and "converged" in text.lower():
        log("README says the review has converged; nothing to do")
        sys.exit(0)
    if not m:
        raise SystemExit("README.md has no '**Round N**' line under 'Current round'")
    return int(m.group(1))


def spec_version() -> str:
    m = VERSION_RE.search(SPEC.read_text(encoding="utf-8")[:500])
    return m.group(1) if m else "?"


def round_dir(n: int) -> Path:
    return PROJECT / "reviews" / f"round-{n}"


def severity_counts(path: Path) -> dict[str, int]:
    counts = {"blocking": 0, "major": 0, "minor": 0}
    for sev in SEVERITY_RE.findall(path.read_text(encoding="utf-8")):
        counts[sev.lower()] += 1
    return counts


COMPLETE_RE = re.compile(r"^\s*Result:\s*complete\s*$", re.I | re.M)
NONE_RE = re.compile(r"^\s*Findings:\s*none\s*$", re.I | re.M)


def validate_review(text: str) -> str | None:
    """Return an error string, or None when the review is complete and well formed."""
    has_findings = bool(SEVERITY_RE.search(text))
    if not COMPLETE_RE.search(text):
        return "missing the 'Result: complete' line"
    if has_findings and NONE_RE.search(text):
        return "contradictory: has findings and 'Findings: none'"
    if not has_findings and not NONE_RE.search(text):
        return "no Severity findings and no 'Findings: none' line"
    return None


# --- git -----------------------------------------------------------------

def ensure_branch(root: Path) -> None:
    run(["git", "fetch", "origin"], cwd=root)
    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    if branch != BRANCH:
        dirty = run(["git", "status", "--porcelain"], cwd=root).stdout.strip()
        if dirty:
            raise SystemExit(f"working tree not clean on {branch}; commit or stash first:\n{dirty}")
        local = run(["git", "rev-parse", "--verify", "--quiet", BRANCH], cwd=root, check=False).returncode == 0
        remote = run(["git", "rev-parse", "--verify", "--quiet", f"origin/{BRANCH}"],
                     cwd=root, check=False).returncode == 0
        if local:
            run(["git", "checkout", BRANCH], cwd=root)
        else:
            run(["git", "checkout", "-b", BRANCH, f"origin/{BRANCH}" if remote else "origin/main"], cwd=root)
    # Never reset a local branch: it may hold commits that are not pushed yet.
    if run(["git", "rev-parse", "--verify", "--quiet", f"origin/{BRANCH}"], cwd=root, check=False).returncode == 0:
        if run(["git", "merge", "--ff-only", f"origin/{BRANCH}"], cwd=root, check=False).returncode != 0:
            log(f"WARNING: local {BRANCH} has diverged from origin; left untouched")
    ahead = run(["git", "rev-list", "--count", f"origin/{BRANCH}..HEAD"], cwd=root, check=False).stdout.strip()
    if ahead and ahead != "0":
        log(f"{ahead} local commit(s) not pushed; pushing before continuing")
        push_branch(root, "pending commits")
    log(f"on branch {BRANCH}")


def staged_paths(root: Path) -> list[str]:
    return run(["git", "diff", "--cached", "--name-only"], cwd=root).stdout.split()


def assert_clean(root: Path, allow: set[str] = frozenset()) -> None:
    """Refuse to start a step on a dirty tree or a non-empty index (except allowed paths)."""
    extra = unexpected_changes(root, set(allow))
    pre = [p for p in staged_paths(root) if p not in allow]
    if extra or pre:
        raise SystemExit(f"working tree or index not clean before the step: changed={extra} staged={pre}")


def commit_and_push(root: Path, paths: list[str], message: str) -> None:
    pre = [p for p in staged_paths(root) if p not in set(paths)]
    if pre:
        raise SystemExit(f"unrelated paths already staged, refusing to commit them: {pre}")
    run(["git", "add", "--", *paths], cwd=root)
    staged = staged_paths(root)
    stray = [p for p in staged if p not in set(paths)]
    if stray:
        raise SystemExit(f"unexpected staged paths: {stray}")
    if staged:
        run(["git", "commit", "-m", message], cwd=root)
    else:
        log("nothing new to commit")
    push_branch(root, message)


def push_branch(root: Path, label: str) -> None:
    for attempt in range(4):
        if run(["git", "push", "-u", "origin", BRANCH], cwd=root, check=False).returncode == 0:
            log(f"pushed: {label}")
            return
        time.sleep(2 ** (attempt + 1))
    raise SystemExit("git push failed 4 times; rerun to resume at the push")


def is_pushed(root: Path, rel: str) -> bool:
    """True when origin/BRANCH has this file with identical content."""
    if not run(["git", "ls-tree", f"origin/{BRANCH}", "--", rel], cwd=root, check=False).stdout.strip():
        return False
    return run(["git", "diff", "--quiet", f"origin/{BRANCH}", "--", rel], cwd=root, check=False).returncode == 0


def unexpected_changes(root: Path, allowed: set[str]) -> list[str]:
    out = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root).stdout
    changed = [line[3:].strip() for line in out.splitlines() if line.strip()]
    return [p for p in changed if p not in allowed and not p.startswith(f"{REL_PROJECT}/automation/logs/")]


# --- model runners -------------------------------------------------------

def claude_settings(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def deepseek_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key
    env = claude_settings(Path.home() / ".claude" / "settings.json").get("env", {})
    if "deepseek" in env.get("ANTHROPIC_BASE_URL", ""):
        return env.get("ANTHROPIC_AUTH_TOKEN", "")
    return ""


def clean_env(keep_api_key: bool) -> dict:
    """Drop inherited model/endpoint variables so each profile sets its own."""
    env = dict(os.environ)
    for k in list(env):
        if k == "ANTHROPIC_API_KEY" and keep_api_key:
            continue
        if k.startswith("ANTHROPIC_") or k in ("CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CONFIG_DIR"):
            env.pop(k)
    return env


def models_used(result: dict) -> list[str]:
    return sorted((result.get("modelUsage") or {}).keys())


def _claude_once(profile: str, prompt: str, root: Path, logfile: Path, timeout: int,
                 model: str) -> tuple[dict | None, subprocess.CompletedProcess]:
    env = clean_env(keep_api_key=profile != "DEEPSEEK")
    args = ["claude", "-p", prompt, "--output-format", "json",
            "--permission-mode", "acceptEdits",
            "--allowedTools", "Read,Write,Edit,Glob,Grep,WebFetch,WebSearch",
            "--disallowedTools", "Bash"]
    tmp = None
    if profile == "DEEPSEEK":
        key = deepseek_key()
        if not key:
            raise SystemExit("no DeepSeek key: set DEEPSEEK_API_KEY or keep it in ~/.claude/settings.json")
        small = os.environ.get("DEEPSEEK_SMALL_MODEL", "deepseek-flash")
        if model == DEEPSEEK_FALLBACK_MODEL:
            small = DEEPSEEK_FALLBACK_MODEL
        DEEPSEEK_CONFIG_DIR.mkdir(mode=0o700, exist_ok=True)
        env["CLAUDE_CONFIG_DIR"] = str(DEEPSEEK_CONFIG_DIR)  # no OAuth login in here, only the DeepSeek key below
        # Flag settings take precedence over the profile's settings.json.
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"env": {
            "ANTHROPIC_BASE_URL": DEEPSEEK_BASE_URL,
            "ANTHROPIC_AUTH_TOKEN": key,
            "ANTHROPIC_MODEL": model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": small,
            "CLAUDE_CODE_SUBAGENT_MODEL": small,
        }}, tmp)
        tmp.close()
        os.chmod(tmp.name, 0o600)
        args += ["--settings", tmp.name, "--model", model]
    else:
        # Always the isolated Anthropic profile: never inherit a default profile that
        # may point at another provider.
        env["CLAUDE_CONFIG_DIR"] = str(ANTHROPIC_CONFIG_DIR)
        alt_env = claude_settings(ANTHROPIC_CONFIG_DIR / "settings.json").get("env", {})
        if "ANTHROPIC_BASE_URL" in alt_env:
            raise SystemExit(f"{ANTHROPIC_CONFIG_DIR}/settings.json sets ANTHROPIC_BASE_URL; "
                             "the consolidator must talk to Anthropic")
        args += ["--model", model]
    try:
        res = run(args, cwd=root, env=env, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        logfile.write_text(f"$ claude ({profile}) {model}\nTIMEOUT after {timeout}s\n--- stdout\n"
                           f"{exc.stdout or ''}\n--- stderr\n{exc.stderr or ''}\n", encoding="utf-8")
        raise SystemExit(f"claude ({profile}) timed out after {timeout}s; see {logfile}")
    finally:
        if tmp:
            os.unlink(tmp.name)
    with logfile.open("a" if logfile.exists() and model == DEEPSEEK_FALLBACK_MODEL else "w",
                      encoding="utf-8") as fh:
        fh.write(f"$ claude ({profile}) requested={model}\n--- stdout\n{res.stdout}\n"
                 f"--- stderr\n{res.stderr}\n")
    try:
        return json.loads(res.stdout), res
    except ValueError:
        return None, res


def run_claude(profile: str, prompt: str, root: Path, logfile: Path, timeout: int) -> dict:
    """Run Claude Code headless with the DEEPSEEK or ANTHROPIC profile; return its JSON result.

    The result carries `_provenance`: requested model, reported model(s), and whether the
    served model was verified by provider telemetry.
    """
    requested = DEEPSEEK_MODEL if profile == "DEEPSEEK" else CLAUDE_MODEL
    result, res = _claude_once(profile, prompt, root, logfile, timeout, requested)
    failed = result is None or result.get("is_error") or res.returncode != 0
    if (failed and profile == "DEEPSEEK" and requested != DEEPSEEK_FALLBACK_MODEL
            and "unrecognized_model" in (res.stdout + res.stderr)
            and "Authentication Fails" not in res.stdout and '"api_error_status":401' not in res.stdout):
        log(f"DeepSeek rejected model {requested!r}; retrying once with {DEEPSEEK_FALLBACK_MODEL!r}")
        requested = DEEPSEEK_FALLBACK_MODEL
        result, res = _claude_once(profile, prompt, root, logfile, timeout, requested)
        failed = result is None or result.get("is_error") or res.returncode != 0
    if result is None:
        raise SystemExit(f"claude ({profile}) gave no JSON result (exit {res.returncode}); see {logfile}")
    if failed:
        raise SystemExit(f"claude ({profile}) failed: {str(result.get('result'))[:500]}; see {logfile}")
    reported = models_used(result)
    if reported and not any(requested in m for m in reported):
        raise SystemExit(f"claude ({profile}) ran on {reported}, requested {requested}; see {logfile}")
    verified = bool(reported)
    if not verified:
        if profile == "DEEPSEEK" and not DEEPSEEK_ACCEPT_UNVERIFIED:
            raise SystemExit(
                f"claude ({profile}) returned no served-model telemetry (empty modelUsage), so "
                f"{requested!r} cannot be verified. If the DeepSeek routing is trusted, accept it "
                f"explicitly with DEEPSEEK_ACCEPT_UNVERIFIED=1; see {logfile}")
        log(f"WARNING claude ({profile}): served model UNVERIFIED (requested {requested})")
    result["_provenance"] = {"profile": profile, "requested": requested,
                             "reported": reported, "verified": verified}
    log(f"claude ({profile}) ok requested={requested} reported={reported or 'unverified'}, "
        f"cost ${result.get('total_cost_usd', 0):.2f}")
    return result


def codex_args(prompt: str, root: Path, last: Path | None = None) -> list[str]:
    """One command builder for preflight and review steps."""
    if os.environ.get("CODEX_DANGEROUS_FULL_ACCESS") == "1":
        log("WARNING: CODEX_DANGEROUS_FULL_ACCESS=1, Codex runs without sandbox or approvals")
        mode = ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        mode = ["--approve-for-me"]  # selects the workspace-write sandbox itself
    out = ["--output-last-message", str(last)] if last else []
    if CODEX_SERVICE_TIER:
        out += ["-c", f'service_tier="{CODEX_SERVICE_TIER}"']
    return ["codex", "exec", *mode, "--skip-git-repo-check", "-C", str(root), *out,
            *CODEX_EXTRA_ARGS, prompt]


def codex_usage(log_text: str) -> dict | None:
    """Total tokens, context size and estimated cost of one `codex exec`, from its session file.

    Cost integrates every request: fresh input, cached input, cache writes and output (reasoning
    tokens are part of output). Returns None when the session file cannot be found.
    """
    sid = re.search(r"session id:\s*(\S+)", log_text)
    model = re.search(r"^model:\s*(\S+)", log_text, re.M)
    if not sid:
        return None
    files = list(CODEX_SESSIONS.rglob(f"*{sid.group(1)}*.jsonl"))
    if not files:
        return None
    keys = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens",
            "reasoning_output_tokens")
    prev = dict.fromkeys(keys, 0)
    tot = dict.fromkeys(keys, 0)
    window = max_req = requests = 0
    short = long_ = 0.0
    prices = CODEX_PRICES.get(model.group(1) if model else "", {}).get(
        "fast" if CODEX_SERVICE_TIER else "standard")
    for line in files[0].read_text(encoding="utf-8").splitlines():
        try:
            pl = json.loads(line).get("payload", {})
        except ValueError:
            continue
        info = pl.get("info") if pl.get("type") == "token_count" else None
        if not info or not info.get("total_token_usage"):
            continue
        window = info.get("model_context_window") or window
        now = {k: info["total_token_usage"].get(k, 0) for k in keys}
        delta = {k: now[k] - prev[k] for k in keys}
        if delta["input_tokens"] <= 0 and delta["output_tokens"] <= 0:
            continue  # repeated event, nothing new
        prev = now
        requests += 1
        ctx = (info.get("last_token_usage") or {}).get("input_tokens", delta["input_tokens"])
        max_req = max(max_req, ctx)
        for k in keys:
            tot[k] += delta[k]
        if prices:
            fresh = delta["input_tokens"] - delta["cached_input_tokens"] - delta["cache_write_input_tokens"]
            vol = (fresh, delta["cached_input_tokens"], delta["cache_write_input_tokens"], delta["output_tokens"])
            c_short = sum(v * r for v, r in zip(vol, prices["short"])) / 1e6
            c_long = sum(v * r for v, r in zip(vol, prices["long"])) / 1e6
            if CODEX_LONG_CONTEXT_TOKENS:
                c_short = c_long if ctx > CODEX_LONG_CONTEXT_TOKENS else c_short
                c_long = c_short
            short += c_short
            long_ += c_long
    usage = {"model": model.group(1) if model else None,
             "service_tier": CODEX_SERVICE_TIER or "standard", "requests": requests, **tot,
             "total_tokens": tot["input_tokens"] + tot["output_tokens"],
             "fresh_input_tokens": tot["input_tokens"] - tot["cached_input_tokens"] - tot["cache_write_input_tokens"],
             "context_window": window, "max_request_context_tokens": max_req,
             "max_request_context_pct": round(100 * max_req / window, 1) if window else None,
             "cost_usd": round(short, 4) if prices else None,
             "cost_usd_upper_bound": round(long_, 4) if prices else None}
    return usage


def log_codex_usage(usage: dict | None) -> None:
    if not usage:
        log("codex usage: session file not found, tokens/cost unavailable")
        return
    cost = ("no price known for this model (set CODEX_PRICING_JSON)" if usage["cost_usd"] is None else
            f"est. cost ${usage['cost_usd']:.3f}" + (
                f" (${usage['cost_usd_upper_bound']:.3f} if the long-context tier applied)"
                if usage["cost_usd_upper_bound"] != usage["cost_usd"] else ""))
    log(f"codex {usage['model']} ({usage['service_tier']} tier): {usage['requests']} requests, input {usage['input_tokens']:,} "
        f"(cached {usage['cached_input_tokens']:,}, fresh {usage['fresh_input_tokens']:,}), "
        f"output {usage['output_tokens']:,} (reasoning {usage['reasoning_output_tokens']:,}); "
        f"largest request {usage['max_request_context_tokens']:,} of {usage['context_window']:,} "
        f"window tokens ({usage['max_request_context_pct']}%); {cost}")


def run_codex(prompt: str, root: Path, logfile: Path, timeout: int) -> dict | None:
    args = codex_args(prompt, root, logfile.with_suffix(".last.md"))
    try:
        res = run(args, cwd=root, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        logfile.write_text(f"$ codex exec\nTIMEOUT after {timeout}s\n--- stdout\n{exc.stdout or ''}\n"
                           f"--- stderr\n{exc.stderr or ''}\n", encoding="utf-8")
        raise SystemExit(f"codex exec timed out after {timeout}s; see {logfile}")
    logfile.write_text(f"$ codex exec\n--- stdout\n{res.stdout}\n--- stderr\n{res.stderr}\n", encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit(f"codex exec failed ({res.returncode}); see {logfile}")
    log("codex ok")
    usage = codex_usage(res.stdout + "\n" + res.stderr)
    log_codex_usage(usage)
    if usage:
        logfile.with_suffix(".usage.json").write_text(json.dumps(usage, indent=2), encoding="utf-8")
    return usage


def run_cursor_agent(prompt: str, root: Path, logfile: Path, timeout: int, model: str) -> None:
    """Run the Cursor agent CLI headless. Never --mode plan: reviewers must write files.

    Output goes straight to the log file, so `tail -f` shows progress while it runs.
    """
    if not shutil.which(CURSOR_AGENT_BIN):
        raise SystemExit(f"Cursor agent binary not found: {CURSOR_AGENT_BIN} (set CURSOR_AGENT_BIN)")
    args = [CURSOR_AGENT_BIN, "-p", prompt, "--workspace", str(root), "--trust", "--force",
            "--model", model, "--output-format", "text"]
    started = time.time()
    with logfile.open("w", encoding="utf-8") as fh:
        fh.write(f"$ cursor-agent --model {model}\n--- output (live)\n")
        fh.flush()
        proc = subprocess.Popen(args, cwd=root, text=True, stdin=subprocess.DEVNULL,
                                stdout=fh, stderr=subprocess.STDOUT)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            fh.write(f"\nTIMEOUT after {timeout}s\n")
            raise SystemExit(f"cursor agent ({model}) timed out after {timeout}s; see {logfile}")
    if code != 0:
        raise SystemExit(f"cursor agent ({model}) failed ({code}); see {logfile}")
    log(f"cursor agent ok on {model} in {time.time() - started:.0f}s")


# --- steps ---------------------------------------------------------------

def review_prompt(agent: str, n: int) -> str:
    review_path = f"{REL_PROJECT}/reviews/round-{n}/{agent}.md"
    who = f"You are {agent}."
    if agent == "DEEPSEEK":
        who = ("You are DEEPSEEK. You are running inside the Claude Code tool, but your identity for "
               "this task is DEEPSEEK, not CLAUDE: sign the review, the finding ids (DEEPSEEK-1, …) "
               "and the CHANGELOG entry as DEEPSEEK.")
    elif agent == "GROK":
        who = ("You are GROK. You are running inside the Cursor agent on Grok 4.7, but your identity "
               "for this task is GROK, not CURSOR: sign the review, the finding ids (GROK-1, …) and the "
               "CHANGELOG entry as GROK. You may use web evidence; cite source and date, and do not "
               "invent error codes, campaign numbers or standard clauses.")
    elif agent == "CURSOR":
        who = ("You are CURSOR. Consistency-only review: cross-references, undefined fields, enum "
               "drift, schema gaps. Do not research external standards. Sign the review, the finding "
               "ids (CURSOR-1, …) and the CHANGELOG entry as CURSOR.")
    return (f"{who}\n\nRead {REL_PROJECT}/README.md and follow its 'Instructions for the reviewing AI' "
            f"for round {n}: read spec.md (the local file, current version v{spec_version()}), and from "
            f"round 2 read reviews/round-{n - 1}/ first. Write your review to {review_path}, starting "
            f"with '# {agent} review — round {n}'.\n\n"
            + REVIEW_RULES.format(review_path=review_path, agent=agent, n=n, name=NAME,
                                  decisions_rule=decisions_note(
                                      f"- Read {REL_PROJECT}/decisions.md: decisions listed there are SETTLED "
                                      "by HUMAN. Treat them as fixed; do not re-open them and do not review the "
                                      "spec's remaining 'Pending HUMAN decision' text for them.\n")))


def consolidation_prompt(n: int, reviewers: list[str], converged: bool, provenance: dict | None = None) -> str:
    nxt = n + 1
    files = ", ".join(f"reviews/round-{n}/{a}.md" for a in reviewers)
    final = ("This round has no blocking or major finding, so it is the LAST round: apply the accepted "
             "minor findings, and in README.md replace the Current round text with a line saying the "
             f"review converged at round {n} on the new spec version." if converged else
             f"Then set README.md 'Current round' to **Round {nxt}**, reviewing the new spec version, "
             f"with reviews in `reviews/round-{nxt}/`.")
    prov_lines = ""
    if provenance:
        rows = "; ".join(
            f"{a}: requested={p.get('requested')}, "
            f"served={','.join(p.get('reported') or []) or 'unverified'}"
            for a, p in provenance.items())
        prov_lines = (f"\n\nReviewer provenance (requested vs served model; 'unverified' means the "
                      f"provider reported no served model): {rows}. Add a short 'Reviewer provenance' "
                      f"section to CONSOLIDATION.md stating which reviewers were unverified.")
    return (
        f"You are CLAUDE, the consolidator of the {NAME} spec review. Read {REL_PROJECT}/README.md, "
        f"spec.md (v{spec_version()}), reviews/round-{n - 1}/CONSOLIDATION.md if it exists, and the "
        f"round-{n} reviews: {files}.\n\n"
        f"Consolidate round {n} the same way as reviews/round-1/CONSOLIDATION.md: write "
        f"reviews/round-{n}/CONSOLIDATION.md (accepted and merged, decisions for HUMAN, rejected or "
        f"deferred with reasons, traceability of every finding), and update spec.md to the next minor "
        f"version (bump the version line and date). Keep open HUMAN decisions in one carried-forward "
        f"list with their FB-D ids; HUMAN is not answering during the automated loop, so do not wait "
        f"for decisions and do not decide them yourself. {final}\n\n"
        + decisions_note(
            f"Read {REL_PROJECT}/decisions.md: every decision listed there is settled by HUMAN. Apply it to spec.md "
            "(replace the matching 'Pending HUMAN decision' passage, adjust the affected sections) and remove it from "
            "the carried-forward open list; follow its notes and do not invent detail HUMAN did not give. ")
        + "Also add a CHANGELOG.md entry at the top (Agent: CLAUDE). Do not run git: the loop commits "
        "and pushes for you. Only edit spec.md, README.md, CHANGELOG.md and the CONSOLIDATION.md file."
        + prov_lines
    )


def do_review(agent: str, n: int, root: Path) -> dict:
    """Run or resume one review; return its provenance record."""
    path = round_dir(n) / f"{agent}.md"
    rel = str(path.relative_to(root))
    if path.exists():
        err = validate_review(path.read_text(encoding="utf-8"))
        if err:
            raise SystemExit(f"{rel} exists but is unfinished ({err}); inspect it, delete it to rerun")
        assert_clean(root, {rel, "CHANGELOG.md"})
        if is_pushed(root, rel):
            log(f"round {n}: {agent} review complete and pushed, skipping")
        else:
            log(f"round {n}: {agent} review complete but not pushed, resuming at commit/push")
            commit_and_push(root, [rel, "CHANGELOG.md"], f"{agent}: {NAME} spec review round {n}")
        return {"requested": "n/a", "reported": [], "verified": False, "note": "resumed, not rerun"}
    assert_clean(root)
    round_dir(n).mkdir(parents=True, exist_ok=True)
    log(f"round {n}: {agent} reviewing spec v{spec_version()}")
    logfile = LOG_DIR / f"r{n}-{agent.lower()}.log"
    prompt = review_prompt(agent, n)
    prov = {"requested": "default configuration", "reported": [], "verified": False,
            "note": "backend does not report the served model"}
    if agent == "CHATGPT":
        usage = run_codex(prompt, root, logfile, STEP_TIMEOUT)
        if usage:
            prov = {"requested": usage["model"], "reported": [usage["model"]] if usage["model"] else [],
                    "verified": False, "note": "model from the Codex banner", "usage": usage}
    elif agent == "DEEPSEEK":
        prov = run_claude("DEEPSEEK", prompt, root, logfile, STEP_TIMEOUT)["_provenance"]
    elif agent == "GROK":
        run_cursor_agent(prompt, root, logfile, STEP_TIMEOUT, GROK_MODEL)
        prov["requested"] = GROK_MODEL
    elif agent == "CURSOR":
        run_cursor_agent(prompt, root, logfile, STEP_TIMEOUT, CURSOR_REVIEW_MODEL)
        prov["requested"] = CURSOR_REVIEW_MODEL
    else:
        raise SystemExit(f"no runner for reviewer {agent!r}")
    if not path.exists():
        raise SystemExit(f"{agent} did not write {path}; see {logfile}")
    err = validate_review(path.read_text(encoding="utf-8"))
    if err:
        raise SystemExit(f"{agent} review is unfinished ({err}); see {logfile}")
    extra = unexpected_changes(root, {rel, "CHANGELOG.md"})
    if extra:
        raise SystemExit(f"{agent} changed files outside its review: {extra}")
    (LOG_DIR / f"r{n}-{agent.lower()}.provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    commit_and_push(root, [rel, "CHANGELOG.md"], f"{agent}: {NAME} spec review round {n}")
    return prov


def do_consolidation(n: int, reviewers: list[str], converged: bool, root: Path,
                     provenance: dict | None = None) -> None:
    path = round_dir(n) / "CONSOLIDATION.md"
    rel_all = [str(p.relative_to(root)) for p in (path, SPEC, README)] + ["CHANGELOG.md"]
    if path.exists():
        if is_pushed(root, rel_all[0]):
            log(f"round {n}: consolidation complete and pushed, skipping")
        else:
            log(f"round {n}: consolidation written but not pushed, resuming at commit/push")
            assert_clean(root, set(rel_all))
            commit_and_push(root, rel_all, f"CLAUDE: consolidate {NAME} round {n} into spec v{spec_version()}")
        return
    assert_clean(root)
    before = spec_version()
    log(f"round {n}: CLAUDE consolidating (spec v{before})")
    logfile = LOG_DIR / f"r{n}-claude.log"
    run_claude("ANTHROPIC", consolidation_prompt(n, reviewers, converged, provenance), root, logfile, STEP_TIMEOUT)
    if not path.exists():
        raise SystemExit(f"CLAUDE did not write {path}; see {logfile}")
    if spec_version() == before:
        raise SystemExit(f"CLAUDE did not bump the spec version (still v{before}); see {logfile}")
    if not converged and current_round() != n + 1:
        raise SystemExit(f"CLAUDE did not move README to round {n + 1}; see {logfile}")
    rel = [str(p.relative_to(root)) for p in (path, SPEC, README)] + ["CHANGELOG.md"]
    extra = unexpected_changes(root, set(rel))
    if extra:
        raise SystemExit(f"CLAUDE changed files outside the consolidation: {extra}")
    commit_and_push(root, rel, f"CLAUDE: consolidate {NAME} round {n} into spec v{spec_version()}")


def probe_write(root: Path, name: str, runner) -> None:
    """Prove a backend can *write* a file headless, not just answer. The orchestrator checks
    the content and cleans up; the model never deletes its own evidence."""
    nonce = f"{name}-{int(time.time())}-{os.getpid()}"
    pdir = LOG_DIR / f"probe-{nonce}"
    pdir.mkdir(parents=True)
    target = pdir / "probe.txt"
    logfile = LOG_DIR / f"preflight-{name.lower()}.log"
    try:
        rel = target.relative_to(root)
        runner(f"Create the file {rel} containing exactly the text {nonce} and nothing else. "
               f"Do not touch any other file. Then stop.", logfile)
        if not target.exists() or target.read_text(encoding="utf-8").strip() != nonce:
            raise SystemExit(f"{name} probe did not write the expected file; see {logfile}")
    finally:
        shutil.rmtree(pdir, ignore_errors=True)
    log(f"{name} write probe ok")


def preflight(root: Path, reviewers: list[str], with_consolidator: bool) -> None:
    tools = ["git"]
    if "CHATGPT" in reviewers:
        tools.append("codex")
    if "DEEPSEEK" in reviewers or with_consolidator:
        tools.append("claude")
    if {"GROK", "CURSOR"} & set(reviewers):
        tools.append(CURSOR_AGENT_BIN)
    ok = True
    for tool in tools:
        found = shutil.which(tool)
        log(f"{tool}: {found or 'MISSING'}")
        ok &= bool(found)
    if not ok:
        raise SystemExit("missing tools")
    log(f"round {current_round()}, spec v{spec_version()}, reviewers {','.join(reviewers)}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    probe = "Reply with the single word OK."
    # Run every probe, so one preflight shows everything that needs fixing.
    probes = []
    if "DEEPSEEK" in reviewers:
        log(f"DeepSeek key: {'found' if deepseek_key() else 'MISSING'}")
        probes.append(("DEEPSEEK", lambda: run_claude("DEEPSEEK", probe, root, LOG_DIR / "preflight-deepseek.log", 300)))
    if with_consolidator:
        probes.append(("ANTHROPIC", lambda: run_claude("ANTHROPIC", probe, root, LOG_DIR / "preflight-claude.log", 300)))
    if "CHATGPT" in reviewers:
        probes.append(("CHATGPT", lambda: probe_write(root, "CHATGPT", lambda p, lf: run_codex(p, root, lf, 300))))
    if "GROK" in reviewers:
        probes.append(("GROK", lambda: probe_write(root, "GROK", lambda p, lf: run_cursor_agent(p, root, lf, 300, GROK_MODEL))))
    if "CURSOR" in reviewers:
        probes.append(("CURSOR", lambda: probe_write(root, "CURSOR", lambda p, lf: run_cursor_agent(p, root, lf, 300, CURSOR_REVIEW_MODEL))))
    failures = []
    reasons = {}
    rnd = current_round()
    state = {name: {"status": "pending", "detail": ""} for name, _ in probes}

    def record(done: bool = False) -> None:
        # Machine-readable progress for generic/loop_monitor.py (one Jarvis node per probe);
        # a later preflight overwrites it.
        (LOG_DIR / "preflight.json").write_text(json.dumps(
            {"time": time.strftime("%FT%T"), "round": rnd, "done": done, "passed": done and not failures,
             "failed": reasons, "probes": state}, indent=2), encoding="utf-8")

    record()
    for name, fn in probes:
        state[name]["status"] = "running"
        record()
        try:
            fn()
            state[name]["status"] = "complete"
        except SystemExit as exc:
            failures.append(name)
            reasons[name] = str(exc).splitlines()[0][:300] if str(exc) else "failed"
            state[name].update(status="failed", detail=reasons[name])
            log(f"FAILED {name}: {exc}")
        record()
    record(done=True)
    if failures:
        raise SystemExit(f"preflight failed ({len(failures)} of {len(probes)} probes): {', '.join(failures)}")
    log("preflight passed")


def parse_reviewers(raw: str) -> list[str]:
    names = [r.strip().upper() for r in raw.split(",")]
    if not names or any(not r for r in names):
        raise SystemExit(f"empty reviewer name in --reviewers {raw!r}")
    if len(set(names)) != len(names):
        raise SystemExit(f"duplicate reviewer in --reviewers {raw!r}")
    unknown = [r for r in names if r not in KNOWN_REVIEWERS]
    if unknown:
        raise SystemExit(f"no runner for reviewer(s) {unknown}; known: {sorted(KNOWN_REVIEWERS)}")
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=os.environ.get("REVIEW_PROJECT"),
                    help="project folder holding spec.md and README.md, relative to the workspace root "
                         "or absolute (env REVIEW_PROJECT)")
    ap.add_argument("--name", default=os.environ.get("REVIEW_NAME"),
                    help="label for commits and prompts (default: the folder under projects/)")
    ap.add_argument("--branch", default=os.environ.get("REVIEW_BRANCH"),
                    help="branch the loop commits to (default: agent/loop/<name>-review)")
    ap.add_argument("--max-rounds", type=int, default=int(os.environ.get("REVIEW_MAX_ROUNDS", "5")),
                    help="stop after this many rounds in this run even without convergence (default 5)")
    ap.add_argument("--preflight", action="store_true",
                    help="probe the backends of the selected reviewers (plus the consolidator), then exit")
    ap.add_argument("--skip-consolidator", action="store_true",
                    help="with --preflight: do not probe the Anthropic consolidator profile")
    ap.add_argument("--reviewers", default=os.environ.get("REVIEWERS", "CHATGPT,DEEPSEEK,GROK"),
                    help="comma-separated, from CHATGPT,DEEPSEEK,GROK,CURSOR (default CHATGPT,DEEPSEEK,GROK)")
    opts = ap.parse_args()

    if not opts.project:
        ap.error("--project is required (or set REVIEW_PROJECT)")
    reviewers = parse_reviewers(opts.reviewers)
    configure(opts.project, opts.name, opts.branch)
    missing = [p.name for p in (SPEC, README) if not p.is_file()]
    if missing:
        raise SystemExit(f"{REL_PROJECT} has no {' or '.join(missing)}")
    root = repo_root()
    log(f"project {REL_PROJECT} ({NAME}), branch {BRANCH}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(LOG_DIR / ".loop.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit(f"another review loop is already running ({LOG_DIR / '.loop.lock'})")
    if opts.preflight:
        preflight(root, reviewers, not opts.skip_consolidator)
        return

    ensure_branch(root)
    for _ in range(opts.max_rounds):
        n = current_round()
        provenance = {}
        for agent in reviewers:
            provenance[agent] = do_review(agent, n, root)
        totals = {"blocking": 0, "major": 0, "minor": 0}
        for agent in reviewers:
            for k, v in severity_counts(round_dir(n) / f"{agent}.md").items():
                totals[k] += v
        converged = totals["blocking"] == 0 and totals["major"] == 0
        log(f"round {n}: {totals['blocking']} blocking, {totals['major']} major, {totals['minor']} minor")
        do_consolidation(n, reviewers, converged, root, provenance)
        if converged:
            log(f"converged at round {n}: spec v{spec_version()}")
            return
    log(f"stopped after {opts.max_rounds} rounds without convergence; rerun to continue")
    sys.exit(2)


if __name__ == "__main__":
    main()
