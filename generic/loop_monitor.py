#!/usr/bin/env python3
"""Monitor and chain the spec review loops (generic/specs_review_loop.py).

State is read from the files the loop already writes; nothing in the loop changes:
  running   (green)  the loop holds automation/logs/.loop.lock
  preflight (amber)  the lock holder is a --preflight probe run, not a review round
  complete  (blue)   README has no '**Round N**' line and says "converged"
  failed    (red)    a step has a log but no complete review, the lock is free, or the last launch exited non-zero
  pending   (grey)   nothing started, or waiting for the loop it comes `after`

Loops are listed in generic/loops.json (see loops.example.json). A loop with "after": "<id>" and
"autostart": true is launched (generic/run_review_loop.sh <project> <name> <branch> full) by `tick`
when that loop is complete, nothing else is running and the git tree is clean. A failed loop is never
relaunched on its own: fix it, then `loop_monitor.py retry <id>`.

    loop_monitor.py status          # print the table
    loop_monitor.py tick            # refresh outputs, launch what is due (once)
    loop_monitor.py watch [secs]    # tick every N seconds (default 30)
    loop_monitor.py retry <id>      # clear a failed launch so the loop may start again

Outputs (all regenerated each tick): generic/.monitor/index.html (open it in a browser; no server,
no port) and Jarvis graph/log files in <workspace>/.jarvis/tracker/{memory,logs} for the shared
Jarvis tracker on 127.0.0.1:8777 (add those dirs to JARVIS_TRACKER_MEMORY_DIRS / _LOG_DIRS).
Jarvis draws in_progress blue and completed green; the HTML page uses green=running, blue=complete.
"""

from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
sys.path.insert(0, str(HERE))
import specs_review_loop as rl  # noqa: E402  (reuses ROUND_RE and validate_review; no globals used)

LOOPS_ROOT = Path(os.environ.get("LOOP_WORKTREES_DIR", str(WORKSPACE.parent / f"{WORKSPACE.name}.loops"))).expanduser()
MAX_PARALLEL = int(os.environ.get("LOOP_MAX_PARALLEL", "3"))
CONFIG = Path(os.environ.get("LOOP_MONITOR_CONFIG", HERE / "loops.json"))
OUT_DIR = HERE / ".monitor"
JARVIS_DIR = WORKSPACE / ".jarvis" / "tracker"
LAUNCHER = HERE / "run_review_loop.sh"
DEFAULT_REVIEWERS = "CHATGPT,DEEPSEEK,GROK"
COLORS = {"preflight": "#eab308", "running": "#22c55e", "failed": "#ef4444", "complete": "#3b82f6", "pending": "#94a3b8"}
JARVIS_STATUS = {"preflight": "pending", "running": "in_progress", "failed": "failed", "complete": "completed", "pending": "pending"}


def load_config(path: Path = CONFIG) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"no loop list: {path} (copy generic/loops.example.json)")
    loops = json.loads(path.read_text(encoding="utf-8"))["loops"]
    ids = [l["id"] for l in loops]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"duplicate loop id in {path}")
    for l in loops:
        if l.get("after") and l["after"] not in ids:
            raise SystemExit(f"loop {l['id']!r}: unknown 'after' {l['after']!r}")
        l.setdefault("name", l["id"])
        l.setdefault("branch", f"agent/loop/{rl.slug(l['name'])}-review")
        l.setdefault("reviewers", DEFAULT_REVIEWERS)
        l.setdefault("autostart", False)
    return loops


def loop_root(loop: dict) -> Path:
    """Where the loop's files live: its own git worktree, or (legacy) the main checkout."""
    return Path(loop["worktree"]).expanduser() if loop.get("worktree") else WORKSPACE


def project_dir(loop: dict) -> Path:
    return loop_root(loop) / loop["project"]


def logs_dir(loop: dict) -> Path:
    return project_dir(loop) / "automation" / "logs"


def checkout_lock(loop: dict) -> Path:
    """Held by generic/run_review_loop.sh while a loop or preflight uses this checkout/worktree (git-dir is per
    worktree, so loops in different worktrees run in parallel; two in the same one are refused)."""
    r = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=loop_root(loop), capture_output=True, text=True)
    return Path(r.stdout.strip() or loop_root(loop) / ".git") / "review-loop.lock"


def lock_holder(lock: Path) -> int | None:
    """PID of the process holding a flock on `lock`, or None. Read from /proc/locks so the monitor
    never takes the lock itself (that could make a starting loop think another one runs)."""
    try:
        ino = lock.stat().st_ino
        table = Path("/proc/locks").read_text()
    except OSError:
        return None
    for line in table.splitlines():
        f = line.split()  # "1: FLOCK ADVISORY WRITE <pid> <maj>:<min>:<inode> <start> <end>"
        if len(f) > 5 and f[1] == "FLOCK" and f[5].rsplit(":", 1)[-1] == str(ino):
            return int(f[4])
    return None


def lock_held(lock: Path) -> bool:
    return lock_holder(lock) is not None


def is_preflight(pid: int | None) -> bool:
    """The engine takes the same lock for --preflight; that is a probe, not a review round."""
    try:
        return pid is not None and "--preflight" in Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
    except OSError:
        return False


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def step_info(logdir: Path, n: int, step: str) -> dict:
    """Model, effort, tier and served model of a step, from the engine's timing file."""
    t = read_json(logdir / f"r{n}-{step.lower()}.timing.json")
    return {k: t[k] for k in ("model", "effort", "tier", "reported", "cost_usd", "cost_basis") if t.get(k) is not None and t.get(k) != ""}


def describe(x: dict) -> str:
    """'deepseek-flash · effort default' (plus tier / served model when they differ)."""
    if not x.get("model"):
        return ""
    bits = [x["model"], f"effort {x.get('effort', 'default')}"]
    if x.get("tier"):
        bits.append(f"{x['tier']} tier")
    if x.get("reported") and x["reported"] != x["model"]:
        bits.append(f"served: {x['reported']}")
    if x.get("cost_usd") is not None:
        bits.append(f"${x['cost_usd']:.2f} ({x.get('cost_basis', '')})")
    elif x.get("cost_basis"):
        bits.append(f"cost: {x['cost_basis']}")
    return " · ".join(bits)


def round_cost(steps: list[dict]) -> dict:
    """Sum of the recorded step costs of a round; Grok (unreported) is flagged, not guessed."""
    known = [x["cost_usd"] for x in steps if x.get("cost_usd") is not None]
    return {"usd": round(sum(known), 2) if known else None,
            "missing": [x["name"] for x in steps if x.get("cost_usd") is None and x.get("seconds") is not None]}


def step_seconds(logdir: Path, n: int, step: str, state: str) -> float | None:
    """Time a step took (from the engine's timing file); a running step shows the time so far."""
    t = read_json(logdir / f"r{n}-{step.lower()}.timing.json")
    if "seconds" in t:
        return t["seconds"]
    if state == "running" and t.get("start"):
        try:
            return max(0.0, time.time() - time.mktime(time.strptime(t["start"], "%Y-%m-%dT%H:%M:%S")))
        except ValueError:
            return None
    return None


def label(name: str, seconds: float | None) -> str:
    return f"{name} {rl.fmt_duration(seconds)}" if seconds is not None else name


def step_state(rdir: Path, logdir: Path, n: int, step: str, running: bool, first_open: bool) -> tuple[str, str]:
    """(state, detail) of one step of round n; `first_open` marks the step the loop is working on."""
    if step == "CLAUDE":
        done = (rdir / "CONSOLIDATION.md").is_file()
        log = logdir / f"r{n}-claude.log"
    else:
        f = rdir / f"{step}.md"
        err = rl.validate_review(f.read_text(encoding="utf-8")) if f.is_file() else "missing"
        done = err is None
        log = logdir / f"r{n}-{step.lower()}.log"
    if done:
        return "complete", ""
    if running and first_open:
        return "running", ""
    if not running and (log.is_file() or (step != "CLAUDE" and (rdir / f"{step}.md").is_file())):
        return "failed", f"{step}: no complete review (see {log.name})"
    return "pending", ""


def round_numbers(project: Path) -> list[int]:
    """Round numbers that have a reviews/round-N folder ('round-2-pass1' and the like are skipped)."""
    return sorted(int(d.name[6:]) for d in (project / "reviews").glob("round-*") if d.name[6:].isdigit())


def past_steps(rdir: Path) -> list[dict]:
    """Steps of a finished round, from the files it holds: every review is complete, then the consolidation."""
    reviews = sorted(f.stem for f in rdir.glob("*.md") if f.stem != "CONSOLIDATION")
    steps = [{"name": r, "status": "complete", "detail": ""} for r in reviews]
    steps.append({"name": "CLAUDE", "status": "complete" if (rdir / "CONSOLIDATION.md").is_file() else "pending", "detail": ""})
    return steps


def preflight_state(logdir: Path, n: int, running: bool) -> dict:
    """Status of the preflight of round n (running, complete, failed or pending) and of each probe."""
    pf = read_json(logdir / "preflight.json")
    if not running and (not pf or pf.get("round", n) != n):
        return {"status": "pending", "detail": "", "probes": []}
    probes = [{"name": k, "status": v.get("status", "pending"), "detail": v.get("detail", "")}
              for k, v in (pf.get("probes") or {}).items()] if pf and pf.get("round", n) == n else []
    if running:
        return {"status": "running", "detail": "probing the backends", "probes": probes}
    for x in probes:  # the engine died mid-probe (killed, crashed): do not leave a probe running forever
        if x["status"] == "running":
            x.update(status="failed", detail="interrupted")
    if pf.get("passed"):
        return {"status": "complete", "detail": pf.get("time", ""), "probes": probes}
    detail = "; ".join(f"{k}: {v}" for k, v in pf.get("failed", {}).items()) or "interrupted"
    return {"status": "failed", "detail": detail, "probes": probes}


def evaluate(loop: dict) -> dict:
    """Current state of one loop, from its files."""
    project = project_dir(loop)
    readme = project / "README.md"
    logdir = logs_dir(loop)
    out = {"id": loop["id"], "name": loop["name"], "after": loop.get("after"), "round": None,
           "branch": loop.get("branch", ""), "worktree": loop.get("worktree", ""),
           "steps": [], "rounds": [], "preflight": None, "cost": {"usd": None, "missing": []}, "status": "pending", "detail": "", "spec": ""}
    if loop.get("worktree") and not loop_root(loop).is_dir():
        out.update(status="failed", detail=f"worktree {loop['worktree']} is missing")
        return out
    if not (project / "spec.md").is_file() or not readme.is_file():
        out.update(status="failed", detail=f"{loop['project']} has no spec.md/README.md")
        return out
    text = readme.read_text(encoding="utf-8")
    m = rl.ROUND_RE.search(text)
    holder = lock_holder(logdir / ".loop.lock")
    pre_running = holder is not None and is_preflight(holder)
    running = holder is not None and not pre_running  # a review round, as opposed to a preflight probe
    launch = read_json(logdir / ".monitor.json")
    out["spec"] = rl.VERSION_RE.search((project / "spec.md").read_text(encoding="utf-8")[:500]).group(1) \
        if rl.VERSION_RE.search((project / "spec.md").read_text(encoding="utf-8")[:500]) else "?"
    # The engine leaves "**Round N** — the review converged at round N …" when the stop rule is met.
    converged = bool(m) and "converged" in text[m.start():m.start() + 200].lower()
    out["rounds"] = [{"n": k, "steps": past_steps(project / "reviews" / f"round-{k}")}
                     for k in round_numbers(project) if not m or converged or k < int(m.group(1))]
    if m:
        out["round"] = int(m.group(1))
    if not m or converged:
        out["status"] = "complete" if "converged" in text.lower() else "failed"
        out["detail"] = "converged" if out["status"] == "complete" else "README has no '**Round N**' line"
        return out
    n = int(m.group(1))
    out["round"] = n
    steps = [r.strip().upper() for r in loop["reviewers"].split(",") if r.strip()] + ["CLAUDE"]
    first_open = None
    rdir = project / "reviews" / f"round-{n}"
    for step in steps:
        state, detail = step_state(rdir, logdir, n, step, running, first_open is None)
        if state != "complete" and first_open is None:
            first_open = step
        out["steps"].append({"name": step, "status": state, "detail": detail,
                             "seconds": step_seconds(logdir, n, step, state), **step_info(logdir, n, step)})
    pf = preflight_state(logdir, n, pre_running)
    out["preflight"] = pf
    out["rounds"].append({"n": n, "steps": out["steps"], "preflight": pf})
    out["cost"] = round_cost(out["steps"])
    if not running:  # a failed preflight marks the still-pending steps of the backends that did not answer
        for name, why in read_json(logdir / "preflight.json").get("failed", {}).items():
            for x in out["steps"]:
                if x["name"] == ("CLAUDE" if name == "ANTHROPIC" else name) and x["status"] == "pending":
                    x.update(status="failed", detail=f"preflight: {why}")
    failed = [s for s in out["steps"] if s["status"] == "failed"]
    if pre_running:
        out.update(status="preflight", detail="preflight probes running (no review round started)")
    elif running:
        out["status"] = "running"
    elif failed:
        out.update(status="failed", detail=failed[0]["detail"])
    elif launch.get("exit") not in (None, 0):
        out.update(status="failed", detail=f"last launch exited {launch['exit']} (see automation/logs/monitor-launch.log)")
    return out


def git_clean(loop: dict | None = None) -> bool:
    return not subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                              cwd=loop_root(loop) if loop else WORKSPACE,
                              capture_output=True, text=True).stdout.strip()


def due(loops: list[dict], states: dict[str, dict]) -> dict | None:
    """The next loop to launch, or None. Loops in different worktrees run in parallel up to MAX_PARALLEL;
    a loop never starts while its own worktree is in use."""
    busy = sum(1 for s in states.values() if s["status"] in ("running", "preflight"))
    if busy >= MAX_PARALLEL:
        return None
    for l in loops:
        s = states[l["id"]]
        if l["autostart"] and l.get("after") and s["status"] == "pending" and states[l["after"]]["status"] == "complete":
            if lock_held(checkout_lock(l)):
                continue
            if not read_json(logs_dir(l) / ".monitor.json"):  # never launched by the monitor; a failed launch needs `retry`
                return l
    return None


def launcher_env(loop: dict) -> dict:
    """Environment for generic/run_review_loop.sh: LOOP_WORKTREE makes it work in the loop's own worktree."""
    env = dict(os.environ)
    env.pop("LOOP_WORKTREE", None)
    if loop.get("worktree"):
        env["LOOP_WORKTREE"] = str(loop_root(loop))
    return env


def launch(loop: dict) -> None:
    logdir = logs_dir(loop)
    logdir.mkdir(parents=True, exist_ok=True)
    mark = logdir / ".monitor.json"
    logf = open(logdir / "monitor-launch.log", "a")
    proc = subprocess.Popen([str(LAUNCHER), loop["project"], loop["name"], loop["branch"], "full"], cwd=loop_root(loop),
                            env=launcher_env(loop), stdin=subprocess.DEVNULL, stdout=logf, stderr=logf, start_new_session=True)
    mark.write_text(json.dumps({"pid": proc.pid, "started": time.strftime("%FT%T"), "exit": None}), encoding="utf-8")
    print(f"[{time.strftime('%T')}] launched {loop['id']} (pid {proc.pid})", flush=True)
    _watch_exit(proc, mark)


def _watch_exit(proc: subprocess.Popen, mark: Path) -> None:
    import threading

    def wait() -> None:
        code = proc.wait()
        data = read_json(mark)
        data.update(exit=code, finished=time.strftime("%FT%T"))
        mark.write_text(json.dumps(data), encoding="utf-8")

    threading.Thread(target=wait, daemon=True).start()


def reap_orphans(loops: list[dict]) -> None:
    """A monitor restart loses the exit watcher: a mark whose pid is gone and whose exit is unknown
    is resolved from the loop's own state (complete => 0, otherwise 1)."""
    for l in loops:
        mark = logs_dir(l) / ".monitor.json"
        data = read_json(mark)
        if data and data.get("exit") is None and not Path(f"/proc/{data.get('pid', 0)}").exists():
            data["exit"] = 0 if evaluate(l)["status"] in ("complete", "pending") else 1
            mark.write_text(json.dumps(data), encoding="utf-8")


# --- outputs ---------------------------------------------------------------

def write_html(states: list[dict]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    cards = []
    for s in states:
        pf = s.get("preflight")
        pchips = "".join(f'<span class="chip" style="background:{COLORS[x["status"]]}" title="{html.escape(x["detail"])}">'
                         f'probe {html.escape(x["name"])}</span>' for x in (pf or {}).get("probes", []))
        chips = (f'<span class="chip" style="background:{COLORS[pf["status"]]}" title="{html.escape(pf["detail"])}">PREFLIGHT</span>'
                 + pchips if pf else "") + "".join(f'<span class="chip" style="background:{COLORS[x["status"]]}" title="{html.escape(x["detail"] or describe(x))}">'
                        f'{html.escape(label(x["name"], x.get("seconds")))}</span>' for x in s["steps"]) or '<span class="muted">no steps</span>'
        after = (f'<div class="muted">after {html.escape(s["after"])}</div>' if s["after"] else "") + \
            (f'<div class="muted">branch {html.escape(s["branch"])}' + (f' · {html.escape(s["worktree"])}' if s.get("worktree") else " · main checkout") + "</div>"
             if s.get("branch") else "")
        rnd = f'round {s["round"]}' if s["round"] else "—"
        c = s.get("cost") or {}
        if c.get("usd") is not None:
            rnd += f' · round cost ≈ ${c["usd"]:.2f}' + (f' (+ {", ".join(c["missing"])} not reported)' if c.get("missing") else "")
        cards.append(
            f'<section style="border-left:8px solid {COLORS[s["status"]]}"><h2>{html.escape(s["name"])} '
            f'<span class="badge" style="background:{COLORS[s["status"]]}">{s["status"]}</span></h2>'
            f'<div class="muted">{rnd} · spec v{html.escape(s["spec"])}</div>{after}<div>{chips}</div>'
            f'<div class="err">{html.escape(s["detail"])}</div>'
            f'<a href="http://127.0.0.1:8777/?run_id=review-loop-{html.escape(s["id"])}" target="_blank">Open in Jarvis ↗</a></section>')
    page = f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=10><title>Review loops</title>
<style>body{{font:15px system-ui;background:#0f172a;color:#e2e8f0;margin:2rem}}section{{background:#1e293b;padding:1rem 1.2rem;
margin:0 0 1rem;border-radius:6px}}h2{{margin:0 0 .3rem}}.badge,.chip{{color:#fff;border-radius:4px;padding:.15rem .5rem;font-size:.8rem;
margin-right:.3rem}}.muted{{color:#94a3b8;font-size:.85rem}}.err{{color:#fca5a5;font-size:.85rem;margin-top:.3rem}}</style>
<h1>Review loops</h1><div class="muted">green running · blue complete · red failed · grey pending — updated {time.strftime('%F %T')}</div><br>
{''.join(cards)}"""
    path = OUT_DIR / "index.html"
    path.write_text(page, encoding="utf-8")
    return path


def write_jarvis(states: list[dict]) -> None:
    mem, logs = JARVIS_DIR / "memory", JARVIS_DIR / "logs"
    mem.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%FT%T")
    for s in states:
        run_id = f"review-loop-{s['id']}"
        meta = {"project": "spec-review-loop", "kind": "review", "node_type": "phase", "round": s["round"],
                "branch": s.get("branch", ""), "worktree": s.get("worktree", "")}
        nodes, prev = {}, None
        for r in s["rounds"]:
            reviewers = [f"r{r['n']}-{x['name']}" for x in r["steps"] if x["name"] != "CLAUDE"]
            gate = prev
            if r.get("preflight"):  # only the current round has one
                pf = r["preflight"]
                gate = f"r{r['n']}-PREFLIGHT"
                probe_ids = []
                for x in pf.get("probes", []):
                    pid = f"{gate}-{x['name']}"
                    probe_ids.append(pid)
                    nodes[pid] = {"id": pid, "name": f"{s['name']} · round {r['n']} · probe {x['name']}", "phase": "design",
                                  "description": f"{x['name']} backend probe", "status": JARVIS_STATUS[x["status"]],
                                  "depends_on": [prev] if prev else [], "error": x["detail"] or None,
                                  "metadata": {**meta, "round": r["n"]}}
                nodes[gate] = {"id": gate, "name": f"{s['name']} · round {r['n']} · PREFLIGHT", "phase": "design",
                               "description": "backend probes", "status": JARVIS_STATUS[pf["status"]],
                               "depends_on": probe_ids or ([prev] if prev else []), "error": pf["detail"] or None,
                               "metadata": {**meta, "round": r["n"]}}
            for x in r["steps"]:
                nid = f"r{r['n']}-{x['name']}"
                last = x["name"] == "CLAUDE"
                nodes[nid] = {"id": nid, "name": " · ".join(filter(None, [f"{s['name']} · round {r['n']} · {label(x['name'], x.get('seconds'))}", describe(x)])),
                              "phase": "implement" if last else "validate", "description": nid,
                              "status": JARVIS_STATUS[x["status"]],
                              "depends_on": reviewers if last else ([gate] if gate else []),
                              "error": x["detail"] or None,
                              "metadata": {**meta, "round": r["n"], "duration_seconds": x.get("seconds"),
                                           **{k: x[k] for k in ("model", "effort", "tier", "reported", "cost_usd", "cost_basis")
                                              if x.get(k) is not None}}}
            prev = f"r{r['n']}-CLAUDE"
        (mem / f"graph_{run_id}.json").write_text(json.dumps({"run_id": run_id, "nodes": nodes}, indent=2), encoding="utf-8")
        entries = [{"timestamp": now, "run_id": run_id, "decision": "run_start", "message": s["name"]}]
        if s["status"] == "complete":
            entries.append({"timestamp": now, "run_id": run_id, "decision": "run_complete", "message": s["detail"]})
        elif s["status"] == "failed":
            entries.append({"timestamp": now, "run_id": run_id, "decision": "run_fail", "message": s["detail"]})
        (logs / f"run_{run_id}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")


SOUND_FILE = Path(os.environ.get("LOOP_MONITOR_SOUND_FILE", "/usr/share/sounds/freedesktop/stereo/complete.oga"))


def consolidated_round(loop: dict) -> int:
    """Highest round whose CONSOLIDATION.md exists (0 when none)."""
    reviews = project_dir(loop) / "reviews"
    return max((n for n in round_numbers(project_dir(loop)) if (reviews / f"round-{n}" / "CONSOLIDATION.md").is_file()), default=0)


def play_sound(message: str) -> None:
    """Sound + desktop notification on this machine; silent failure when there is no audio/desktop."""
    if os.environ.get("LOOP_MONITOR_SOUND", "1") == "0":
        return
    for cmd in (["paplay", str(SOUND_FILE)], ["canberra-gtk-play", "-i", "complete"]):
        try:
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except OSError:
            continue
    try:
        subprocess.Popen(["notify-send", "Review loop", message], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def notify_consolidations(loops: list[dict]) -> list[str]:
    """Play the sound when a loop's consolidation finishes (a round gets its CONSOLIDATION.md).
    The first look at a loop only records the current state, so old rounds never ring."""
    notified = OUT_DIR / "notified.json"
    seen = read_json(notified)
    fired = []
    for l in loops:
        now = consolidated_round(l)
        if l["id"] in seen and now > seen[l["id"]] and l.get("sound", True):
            msg = f"{l['name']}: round {now} consolidation finished"
            play_sound(msg)
            fired.append(msg)
        seen[l["id"]] = now
    OUT_DIR.mkdir(exist_ok=True)
    notified.write_text(json.dumps(seen), encoding="utf-8")
    return fired


def tick(loops: list[dict], do_launch: bool = True) -> list[dict]:
    reap_orphans(loops)
    states = {l["id"]: evaluate(l) for l in loops}
    nxt = due(loops, states) if do_launch else None
    if nxt:
        if git_clean(nxt):
            launch(nxt)
            states[nxt["id"]] = evaluate(nxt)
        else:
            states[nxt["id"]]["detail"] = "due, but the git tree is not clean"
    ordered = [states[l["id"]] for l in loops]
    if do_launch:  # only the watcher rings; `status` is read-only
        notify_consolidations(loops)
    write_html(ordered)
    write_jarvis(ordered)
    return ordered


def show(states: list[dict]) -> None:
    for s in states:
        steps = " ".join(f"{x['name']}:{x['status']}" for x in s["steps"])
        print(f"{s['id']:<16} {s['status']:<9} round {s['round'] or '-'}  {steps}  {s['detail']}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    loops = load_config()
    if cmd == "status":
        show(tick(loops, do_launch=False))
    elif cmd == "tick":
        show(tick(loops))
    elif cmd == "watch":
        every = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        print(f"watching {len(loops)} loop(s) every {every}s; page: {OUT_DIR / 'index.html'}", flush=True)
        while True:
            tick(loops)
            time.sleep(every)
    elif cmd == "retry" and len(sys.argv) > 2:
        known = {l["id"]: l for l in loops}
        if sys.argv[2] not in known:
            raise SystemExit(f"unknown loop {sys.argv[2]!r}")
        (logs_dir(known[sys.argv[2]]) / ".monitor.json").unlink(missing_ok=True)
        print("cleared; the next tick may launch it again (if autostart and its predecessor is complete)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
