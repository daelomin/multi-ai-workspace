#!/usr/bin/env python3
"""Automated multi-AI review loop for the FuelBuddy charging diagnostic spec.

One round = CHATGPT review (Codex CLI) -> DEEPSEEK review (Claude Code on the
DeepSeek API) -> CLAUDE consolidation (Claude Code on Anthropic, Sonnet).
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
import json
import os
import re
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
STEP_TIMEOUT = int(os.environ.get("REVIEW_STEP_TIMEOUT", str(90 * 60)))
CODEX_EXTRA_ARGS = os.environ.get(
    "CODEX_EXTRA_ARGS", "-c sandbox_workspace_write.network_access=true"
).split()

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
- When the file is written, stop."""


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None,
        check: bool = True, capture: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, cwd=cwd, env=env, text=True, timeout=timeout,
                         capture_output=capture)
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


# --- git -----------------------------------------------------------------

def ensure_branch(root: Path) -> None:
    run(["git", "fetch", "origin"], cwd=root)
    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    if branch == BRANCH:
        return
    dirty = run(["git", "status", "--porcelain"], cwd=root).stdout.strip()
    if dirty:
        raise SystemExit(f"working tree not clean on {branch}; commit or stash first:\n{dirty}")
    exists = run(["git", "rev-parse", "--verify", "--quiet", f"origin/{BRANCH}"],
                 cwd=root, check=False).returncode == 0
    if exists:
        run(["git", "checkout", "-B", BRANCH, f"origin/{BRANCH}"], cwd=root)
    else:
        run(["git", "checkout", "-B", BRANCH, "origin/main"], cwd=root)
    log(f"on branch {BRANCH}")


def commit_and_push(root: Path, paths: list[str], message: str) -> None:
    run(["git", "add", "--", *paths], cwd=root)
    if run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode == 0:
        log("nothing to commit")
        return
    run(["git", "commit", "-m", message], cwd=root)
    for attempt in range(4):
        if run(["git", "push", "-u", "origin", BRANCH], cwd=root, check=False).returncode == 0:
            log(f"pushed: {message}")
            return
        time.sleep(2 ** (attempt + 1))
    raise SystemExit("git push failed 4 times")


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


def run_claude(profile: str, prompt: str, root: Path, logfile: Path, timeout: int) -> dict:
    """Run Claude Code headless with the DEEPSEEK or ANTHROPIC profile; return its JSON result."""
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
        # Flag settings take precedence over ~/.claude/settings.json.
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"env": {
            "ANTHROPIC_BASE_URL": DEEPSEEK_BASE_URL,
            "ANTHROPIC_AUTH_TOKEN": key,
            "ANTHROPIC_MODEL": DEEPSEEK_MODEL,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": os.environ.get("DEEPSEEK_SMALL_MODEL", "deepseek-flash"),
            "CLAUDE_CODE_SUBAGENT_MODEL": os.environ.get("DEEPSEEK_SMALL_MODEL", "deepseek-flash"),
        }}, tmp)
        tmp.close()
        os.chmod(tmp.name, 0o600)
        args += ["--settings", tmp.name, "--model", DEEPSEEK_MODEL]
    else:
        default_env = claude_settings(Path.home() / ".claude" / "settings.json").get("env", {})
        if "ANTHROPIC_BASE_URL" in default_env or os.environ.get("ANTHROPIC_CLAUDE_CONFIG_DIR"):
            env["CLAUDE_CONFIG_DIR"] = str(ANTHROPIC_CONFIG_DIR)
            alt_env = claude_settings(ANTHROPIC_CONFIG_DIR / "settings.json").get("env", {})
            if "ANTHROPIC_BASE_URL" in alt_env:
                raise SystemExit(f"{ANTHROPIC_CONFIG_DIR}/settings.json sets ANTHROPIC_BASE_URL; "
                                 "the consolidator must talk to Anthropic")
        args += ["--model", CLAUDE_MODEL]
    try:
        res = run(args, cwd=root, env=env, check=False, timeout=timeout)
    finally:
        if tmp:
            os.unlink(tmp.name)
    logfile.write_text(f"$ claude ({profile})\n--- stdout\n{res.stdout}\n--- stderr\n{res.stderr}\n",
                       encoding="utf-8")
    try:
        result = json.loads(res.stdout)
    except ValueError:
        raise SystemExit(f"claude ({profile}) gave no JSON result (exit {res.returncode}); see {logfile}")
    if result.get("is_error") or res.returncode != 0:
        raise SystemExit(f"claude ({profile}) failed: {str(result.get('result'))[:500]}; see {logfile}")
    expected = DEEPSEEK_MODEL if profile == "DEEPSEEK" else CLAUDE_MODEL
    used = models_used(result)
    if not any(expected in m for m in used):
        raise SystemExit(f"claude ({profile}) ran on {used}, expected {expected}; see {logfile}")
    log(f"claude ({profile}) ok on {used}, cost ${result.get('total_cost_usd', 0):.2f}")
    return result


def run_codex(prompt: str, root: Path, logfile: Path, timeout: int) -> None:
    last = logfile.with_suffix(".last.md")
    args = ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-C", str(root),
            "--output-last-message", str(last), *CODEX_EXTRA_ARGS, prompt]
    res = run(args, cwd=root, check=False, timeout=timeout)
    logfile.write_text(f"$ codex exec\n--- stdout\n{res.stdout}\n--- stderr\n{res.stderr}\n", encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit(f"codex exec failed ({res.returncode}); see {logfile}")
    log("codex ok")


# --- steps ---------------------------------------------------------------

def review_prompt(agent: str, n: int) -> str:
    review_path = f"{REL_PROJECT}/reviews/round-{n}/{agent}.md"
    who = f"You are {agent}."
    if agent == "DEEPSEEK":
        who = ("You are DEEPSEEK. You are running inside the Claude Code tool, but your identity for "
               "this task is DEEPSEEK, not CLAUDE: sign the review, the finding ids (DEEPSEEK-1, …) "
               "and the CHANGELOG entry as DEEPSEEK.")
    return (f"{who}\n\nRead {REL_PROJECT}/README.md and follow its 'Instructions for the reviewing AI' "
            f"for round {n}: read spec.md (the local file, current version v{spec_version()}), and from "
            f"round 2 read reviews/round-{n - 1}/ first. Write your review to {review_path}, starting "
            f"with '# {agent} review — round {n}'.\n\n"
            + REVIEW_RULES.format(review_path=review_path, agent=agent, n=n))


def consolidation_prompt(n: int, reviewers: list[str], converged: bool) -> str:
    nxt = n + 1
    files = ", ".join(f"reviews/round-{n}/{a}.md" for a in reviewers)
    final = ("This round has no blocking or major finding, so it is the LAST round: apply the accepted "
             "minor findings, and in README.md replace the Current round text with a line saying the "
             f"review converged at round {n} on the new spec version." if converged else
             f"Then set README.md 'Current round' to **Round {nxt}**, reviewing the new spec version, "
             f"with reviews in `reviews/round-{nxt}/`.")
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
    )


def do_review(agent: str, n: int, root: Path) -> None:
    path = round_dir(n) / f"{agent}.md"
    if path.exists():
        log(f"round {n}: {agent} review already there, skipping")
        return
    round_dir(n).mkdir(parents=True, exist_ok=True)
    log(f"round {n}: {agent} reviewing spec v{spec_version()}")
    logfile = LOG_DIR / f"r{n}-{agent.lower()}.log"
    if agent == "CHATGPT":
        run_codex(review_prompt(agent, n), root, logfile, STEP_TIMEOUT)
    else:
        run_claude("DEEPSEEK", review_prompt(agent, n), root, logfile, STEP_TIMEOUT)
    if not path.exists() or not SEVERITY_RE.search(path.read_text(encoding="utf-8")):
        raise SystemExit(f"{agent} did not write a review with findings at {path}; see {logfile}")
    rel = str(path.relative_to(root))
    extra = unexpected_changes(root, {rel, "CHANGELOG.md"})
    if extra:
        raise SystemExit(f"{agent} changed files outside its review: {extra}")
    commit_and_push(root, [rel, "CHANGELOG.md"], f"{agent}: FuelBuddy spec review round {n}")


def do_consolidation(n: int, reviewers: list[str], converged: bool, root: Path) -> None:
    path = round_dir(n) / "CONSOLIDATION.md"
    if path.exists():
        log(f"round {n}: consolidation already there, skipping")
        return
    before = spec_version()
    log(f"round {n}: CLAUDE consolidating (spec v{before})")
    logfile = LOG_DIR / f"r{n}-claude.log"
    run_claude("ANTHROPIC", consolidation_prompt(n, reviewers, converged), root, logfile, STEP_TIMEOUT)
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


def preflight(root: Path) -> None:
    ok = True
    for tool in ("git", "codex", "claude"):
        found = shutil.which(tool)
        log(f"{tool}: {found or 'MISSING'}")
        ok &= bool(found)
    if not ok:
        raise SystemExit("missing tools")
    log(run(["codex", "--version"], check=False).stdout.strip())
    log(run(["claude", "--version"], check=False).stdout.strip())
    log(f"round {current_round()}, spec v{spec_version()}")
    log(f"DeepSeek key: {'found' if deepseek_key() else 'MISSING'}")
    LOG_DIR.mkdir(exist_ok=True)
    probe = "Reply with the single word OK."
    run_claude("DEEPSEEK", probe, root, LOG_DIR / "preflight-deepseek.log", 300)
    run_claude("ANTHROPIC", probe, root, LOG_DIR / "preflight-claude.log", 300)
    res = run(["codex", "exec", "--skip-git-repo-check", "-C", str(root), *CODEX_EXTRA_ARGS, probe],
              check=False, timeout=300)
    (LOG_DIR / "preflight-codex.log").write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit("codex exec probe failed; see automation/logs/preflight-codex.log")
    log("codex ok")
    log("preflight passed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-rounds", type=int, default=int(os.environ.get("REVIEW_MAX_ROUNDS", "5")),
                    help="stop after this many rounds in this run even without convergence (default 5)")
    ap.add_argument("--preflight", action="store_true",
                    help="check codex, claude and both model profiles with a tiny prompt, then exit")
    ap.add_argument("--reviewers", default="CHATGPT,DEEPSEEK")
    opts = ap.parse_args()

    root = repo_root()
    LOG_DIR.mkdir(exist_ok=True)
    if opts.preflight:
        preflight(root)
        return

    reviewers = [r.strip().upper() for r in opts.reviewers.split(",") if r.strip()]
    ensure_branch(root)
    for _ in range(opts.max_rounds):
        n = current_round()
        for agent in reviewers:
            do_review(agent, n, root)
        totals = {"blocking": 0, "major": 0, "minor": 0}
        for agent in reviewers:
            for k, v in severity_counts(round_dir(n) / f"{agent}.md").items():
                totals[k] += v
        converged = totals["blocking"] == 0 and totals["major"] == 0
        log(f"round {n}: {totals['blocking']} blocking, {totals['major']} major, {totals['minor']} minor")
        do_consolidation(n, reviewers, converged, root)
        if converged:
            log(f"converged at round {n}: spec v{spec_version()}")
            return
    log(f"stopped after {opts.max_rounds} rounds without convergence; rerun to continue")
    sys.exit(2)


if __name__ == "__main__":
    main()
