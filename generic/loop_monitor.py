#!/usr/bin/env python3
"""Monitor and chain the spec review loops (generic/specs_review_loop.py).

State is read from the files the loop already writes; nothing in the loop changes:
  running   (green)  the loop holds automation/logs/.loop.lock
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

CONFIG = Path(os.environ.get("LOOP_MONITOR_CONFIG", HERE / "loops.json"))
OUT_DIR = HERE / ".monitor"
JARVIS_DIR = WORKSPACE / ".jarvis" / "tracker"
LAUNCHER = HERE / "run_review_loop.sh"
DEFAULT_REVIEWERS = "CHATGPT,DEEPSEEK,GROK"
COLORS = {"running": "#22c55e", "failed": "#ef4444", "complete": "#3b82f6", "pending": "#94a3b8"}
JARVIS_STATUS = {"running": "in_progress", "failed": "failed", "complete": "completed", "pending": "pending"}


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


def lock_held(lock: Path) -> bool:
    """True when some process holds a flock on `lock`. Read from /proc/locks so the monitor
    never takes the lock itself (that could make a starting loop think another one runs)."""
    try:
        ino = lock.stat().st_ino
        table = Path("/proc/locks").read_text()
    except OSError:
        return False
    for line in table.splitlines():
        f = line.split()  # "1: FLOCK ADVISORY WRITE <pid> <maj>:<min>:<inode> <start> <end>"
        if len(f) > 5 and f[1] == "FLOCK" and f[5].rsplit(":", 1)[-1] == str(ino):
            return True
    return False


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


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


def evaluate(loop: dict) -> dict:
    """Current state of one loop, from its files."""
    project = WORKSPACE / loop["project"]
    readme = project / "README.md"
    logdir = project / "automation" / "logs"
    out = {"id": loop["id"], "name": loop["name"], "after": loop.get("after"), "round": None,
           "steps": [], "rounds": [], "status": "pending", "detail": "", "spec": ""}
    if not (project / "spec.md").is_file() or not readme.is_file():
        out.update(status="failed", detail=f"{loop['project']} has no spec.md/README.md")
        return out
    text = readme.read_text(encoding="utf-8")
    m = rl.ROUND_RE.search(text)
    running = lock_held(logdir / ".loop.lock")
    launch = read_json(logdir / ".monitor.json")
    out["spec"] = rl.VERSION_RE.search((project / "spec.md").read_text(encoding="utf-8")[:500]).group(1) \
        if rl.VERSION_RE.search((project / "spec.md").read_text(encoding="utf-8")[:500]) else "?"
    out["rounds"] = [{"n": k, "steps": past_steps(project / "reviews" / f"round-{k}")}
                     for k in round_numbers(project) if not m or k < int(m.group(1))]
    if not m:
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
        out["steps"].append({"name": step, "status": state, "detail": detail})
    out["rounds"].append({"n": n, "steps": out["steps"]})
    failed = [s for s in out["steps"] if s["status"] == "failed"]
    if running:
        out["status"] = "running"
    elif failed:
        out.update(status="failed", detail=failed[0]["detail"])
    elif launch.get("exit") not in (None, 0):
        out.update(status="failed", detail=f"last launch exited {launch['exit']} (see automation/logs/monitor-launch.log)")
    return out


def git_clean() -> bool:
    return not subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=WORKSPACE,
                              capture_output=True, text=True).stdout.strip()


def due(loops: list[dict], states: dict[str, dict]) -> dict | None:
    """The next loop to launch, or None. One launch at a time: the loops share one checkout."""
    if any(s["status"] == "running" for s in states.values()):
        return None
    for l in loops:
        s = states[l["id"]]
        if l["autostart"] and l.get("after") and s["status"] == "pending" and states[l["after"]]["status"] == "complete":
            launch = read_json(WORKSPACE / l["project"] / "automation" / "logs" / ".monitor.json")
            if not launch:  # never launched by the monitor; a failed launch needs `retry`
                return l
    return None


def launch(loop: dict) -> None:
    logdir = WORKSPACE / loop["project"] / "automation" / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    mark = logdir / ".monitor.json"
    logf = open(logdir / "monitor-launch.log", "a")
    proc = subprocess.Popen([str(LAUNCHER), loop["project"], loop["name"], loop["branch"], "full"], cwd=WORKSPACE,
                            stdin=subprocess.DEVNULL, stdout=logf, stderr=logf, start_new_session=True)
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
        mark = WORKSPACE / l["project"] / "automation" / "logs" / ".monitor.json"
        data = read_json(mark)
        if data and data.get("exit") is None and not Path(f"/proc/{data.get('pid', 0)}").exists():
            data["exit"] = 0 if evaluate(l)["status"] in ("complete", "pending") else 1
            mark.write_text(json.dumps(data), encoding="utf-8")


# --- outputs ---------------------------------------------------------------

def write_html(states: list[dict]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    cards = []
    for s in states:
        chips = "".join(f'<span class="chip" style="background:{COLORS[x["status"]]}" title="{html.escape(x["detail"])}">'
                        f'{html.escape(x["name"])}</span>' for x in s["steps"]) or '<span class="muted">no steps</span>'
        after = f'<div class="muted">after {html.escape(s["after"])}</div>' if s["after"] else ""
        rnd = f'round {s["round"]}' if s["round"] else "—"
        cards.append(
            f'<section style="border-left:8px solid {COLORS[s["status"]]}"><h2>{html.escape(s["name"])} '
            f'<span class="badge" style="background:{COLORS[s["status"]]}">{s["status"]}</span></h2>'
            f'<div class="muted">{rnd} · spec v{html.escape(s["spec"])}</div>{after}<div>{chips}</div>'
            f'<div class="err">{html.escape(s["detail"])}</div></section>')
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
        meta = {"project": "spec-review-loop", "kind": "review", "node_type": "phase", "round": s["round"]}
        nodes, prev = {}, None
        for r in s["rounds"]:
            reviewers = [f"r{r['n']}-{x['name']}" for x in r["steps"] if x["name"] != "CLAUDE"]
            for x in r["steps"]:
                nid = f"r{r['n']}-{x['name']}"
                last = x["name"] == "CLAUDE"
                nodes[nid] = {"id": nid, "name": f"{s['name']} · round {r['n']} · {x['name']}",
                              "phase": "implement" if last else "validate", "description": nid,
                              "status": JARVIS_STATUS[x["status"]],
                              "depends_on": reviewers if last else ([prev] if prev else []),
                              "error": x["detail"] or None, "metadata": {**meta, "round": r["n"]}}
            prev = f"r{r['n']}-CLAUDE"
        (mem / f"graph_{run_id}.json").write_text(json.dumps({"run_id": run_id, "nodes": nodes}, indent=2), encoding="utf-8")
        entries = [{"timestamp": now, "run_id": run_id, "decision": "run_start", "message": s["name"]}]
        if s["status"] == "complete":
            entries.append({"timestamp": now, "run_id": run_id, "decision": "run_complete", "message": s["detail"]})
        elif s["status"] == "failed":
            entries.append({"timestamp": now, "run_id": run_id, "decision": "run_fail", "message": s["detail"]})
        (logs / f"run_{run_id}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")


def tick(loops: list[dict], do_launch: bool = True) -> list[dict]:
    reap_orphans(loops)
    states = {l["id"]: evaluate(l) for l in loops}
    nxt = due(loops, states) if do_launch else None
    if nxt:
        if git_clean():
            launch(nxt)
            states[nxt["id"]] = evaluate(nxt)
        else:
            states[nxt["id"]]["detail"] = "due, but the git tree is not clean"
    ordered = [states[l["id"]] for l in loops]
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
        (WORKSPACE / known[sys.argv[2]]["project"] / "automation" / "logs" / ".monitor.json").unlink(missing_ok=True)
        print("cleared; the next tick may launch it again (if autostart and its predecessor is complete)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
