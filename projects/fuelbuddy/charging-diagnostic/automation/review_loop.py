#!/usr/bin/env python3
"""Automated multi-AI review loop for the FuelBuddy charging diagnostic spec.

One round = CHATGPT review (Codex CLI) -> DEEPSEEK review (Claude Code on the
DeepSeek API) -> GROK review (Cursor agent, Grok 4.7) -> CLAUDE consolidation
(Claude Code on Anthropic, Sonnet).
The script commits and pushes after each step, then starts the next round,
until a round has no `blocking` or `major` finding (README stop rule) or
--max-rounds is reached.

State is the files in reviews/round-N/, as in the README: a step whose file
already exists is skipped, so the loop can be stopped and restarted at any time.

Run from anywhere:
    python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py --preflight
    python3 projects/fuelbuddy/charging-diagnostic/automation/review_loop.py
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
PROJECT = HERE.parent  # projects/fuelbuddy/charging-diagnostic
REL_PROJECT = "projects/fuelbuddy/charging-diagnostic"
README = PROJECT / "README.md"
SPEC = PROJECT / "spec.md"
LOG_DIR = HERE / "logs"  # gitignored

BRANCH = "agent/loop/fuelbuddy-review"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"
CLAUDE_MODEL = os.environ.get("CLAUDE_CONSOLIDATOR_MODEL", "claude-sonnet-5-5")
# Claude Code profile that talks to Anthropic. ~/.claude points at DeepSeek on
# the ZenBook, so the consolidator uses its own config dir (log in once there).
ANTHROPIC_CONFIG_DIR = Path(
    os.environ.get("ANTHROPIC_CLAUDE_CONFIG_DIR", str(Path.home() / ".claude-anthropic"))
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
pushes your files for you as "{agent}: FuelBuddy spec review round {n}".
- HUMAN is not answering during the loop. Items already listed as open HUMAN decisions in \
the previous CONSOLIDATION.md must not be raised again as blocking or major findings; \
comment on them only if you have new evidence, as a `question` of severity `minor`.
- Severity discipline: `blocking` and `major` keep the loop running, so use them only for \
problems that would make the spec unsafe, wrong or unimplementable. Use `minor` for the rest.
- Do not repeat findings that the previous consolidation already accepted and merged, \
unless the merged text is still wrong.
- End the review file with a line `Result: complete`. If you have no findings, write a line \
`Findings: none` before it. A file without `Result: complete` is treated as unfinished.
- When the file is written, stop."""


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
        # Flag settings take precedence over ~/.claude/settings.json.
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
    return ["codex", "exec", *mode, "--skip-git-repo-check", "-C", str(root), *out,
            *CODEX_EXTRA_ARGS, prompt]


def run_codex(prompt: str, root: Path, logfile: Path, timeout: int) -> None:
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


def run_cursor_agent(prompt: str, root: Path, logfile: Path, timeout: int, model: str) -> None:
    """Run the Cursor agent CLI headless. Never --mode plan: reviewers must write files."""
    if not shutil.which(CURSOR_AGENT_BIN):
        raise SystemExit(f"Cursor agent binary not found: {CURSOR_AGENT_BIN} (set CURSOR_AGENT_BIN)")
    args = [CURSOR_AGENT_BIN, "-p", prompt, "--workspace", str(root), "--trust", "--force",
            "--model", model, "--output-format", "text"]
    try:
        res = run(args, cwd=root, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        logfile.write_text(f"$ cursor-agent --model {model}\nTIMEOUT after {timeout}s\n--- stdout\n"
                           f"{exc.stdout or ''}\n--- stderr\n{exc.stderr or ''}\n", encoding="utf-8")
        raise SystemExit(f"cursor agent ({model}) timed out after {timeout}s; see {logfile}")
    logfile.write_text(f"$ cursor-agent --model {model}\n--- stdout\n{res.stdout}\n--- stderr\n"
                       f"{res.stderr}\n", encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit(f"cursor agent ({model}) failed ({res.returncode}); see {logfile}")
    log(f"cursor agent ok on {model}")


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
            + REVIEW_RULES.format(review_path=review_path, agent=agent, n=n))


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
        f"You are CLAUDE, the consolidator of the FuelBuddy spec review. Read {REL_PROJECT}/README.md, "
        f"spec.md (v{spec_version()}), reviews/round-{n - 1}/CONSOLIDATION.md if it exists, and the "
        f"round-{n} reviews: {files}.\n\n"
        f"Consolidate round {n} the same way as reviews/round-1/CONSOLIDATION.md: write "
        f"reviews/round-{n}/CONSOLIDATION.md (accepted and merged, decisions for HUMAN, rejected or "
        f"deferred with reasons, traceability of every finding), and update spec.md to the next minor "
        f"version (bump the version line and date). Keep open HUMAN decisions in one carried-forward "
        f"list with their FB-D ids; HUMAN is not answering during the automated loop, so do not wait "
        f"for decisions and do not decide them yourself. {final}\n\n"
        "Also add a CHANGELOG.md entry at the top (Agent: CLAUDE). Do not run git: the loop commits "
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
            commit_and_push(root, [rel, "CHANGELOG.md"], f"{agent}: FuelBuddy spec review round {n}")
        return {"requested": "n/a", "reported": [], "verified": False, "note": "resumed, not rerun"}
    assert_clean(root)
    round_dir(n).mkdir(parents=True, exist_ok=True)
    log(f"round {n}: {agent} reviewing spec v{spec_version()}")
    logfile = LOG_DIR / f"r{n}-{agent.lower()}.log"
    prompt = review_prompt(agent, n)
    prov = {"requested": "default configuration", "reported": [], "verified": False,
            "note": "backend does not report the served model"}
    if agent == "CHATGPT":
        run_codex(prompt, root, logfile, STEP_TIMEOUT)
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
    commit_and_push(root, [rel, "CHANGELOG.md"], f"{agent}: FuelBuddy spec review round {n}")
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
            commit_and_push(root, rel_all, f"CLAUDE: consolidate FuelBuddy round {n} into spec v{spec_version()}")
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
    commit_and_push(root, rel, f"CLAUDE: consolidate FuelBuddy round {n} into spec v{spec_version()}")


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
    LOG_DIR.mkdir(exist_ok=True)
    probe = "Reply with the single word OK."
    if "DEEPSEEK" in reviewers:
        log(f"DeepSeek key: {'found' if deepseek_key() else 'MISSING'}")
        run_claude("DEEPSEEK", probe, root, LOG_DIR / "preflight-deepseek.log", 300)
    if with_consolidator:
        run_claude("ANTHROPIC", probe, root, LOG_DIR / "preflight-claude.log", 300)
    if "CHATGPT" in reviewers:
        probe_write(root, "CHATGPT", lambda p, lf: run_codex(p, root, lf, 300))
    if "GROK" in reviewers:
        probe_write(root, "GROK", lambda p, lf: run_cursor_agent(p, root, lf, 300, GROK_MODEL))
    if "CURSOR" in reviewers:
        probe_write(root, "CURSOR", lambda p, lf: run_cursor_agent(p, root, lf, 300, CURSOR_REVIEW_MODEL))
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
    ap.add_argument("--max-rounds", type=int, default=int(os.environ.get("REVIEW_MAX_ROUNDS", "5")),
                    help="stop after this many rounds in this run even without convergence (default 5)")
    ap.add_argument("--preflight", action="store_true",
                    help="probe the backends of the selected reviewers (plus the consolidator), then exit")
    ap.add_argument("--skip-consolidator", action="store_true",
                    help="with --preflight: do not probe the Anthropic consolidator profile")
    ap.add_argument("--reviewers", default=os.environ.get("REVIEWERS", "CHATGPT,DEEPSEEK,GROK"),
                    help="comma-separated, from CHATGPT,DEEPSEEK,GROK,CURSOR (default CHATGPT,DEEPSEEK,GROK)")
    opts = ap.parse_args()

    reviewers = parse_reviewers(opts.reviewers)
    root = repo_root()
    LOG_DIR.mkdir(exist_ok=True)
    lock = open(LOG_DIR / ".loop.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("another review loop is already running (automation/logs/.loop.lock)")
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
