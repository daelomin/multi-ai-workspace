#!/usr/bin/env python3
"""Local assistant for the review loops: serves generic/loop_wizard.html and RUNS the steps for you.

    generic/loop_wizard.py            # prints http://127.0.0.1:8795/?t=<token>

Safety: listens on 127.0.0.1 only; every request needs the token (kept in generic/.monitor/wizard.token, 0600; the URL is also in generic/.monitor/wizard.url) (and a 127.0.0.1 Host
header, against DNS rebinding); the page can only trigger the fixed actions below, with validated
arguments, never an arbitrary shell command. Paid-backend runs (`one`, `full`) are confirmed in the page.

Actions: state, loops, git_status, commit, create_loop, register, monitor_start/stop, job (preflight|one|full), retry.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
import uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
sys.path.insert(0, str(HERE))
import loop_monitor as lm  # noqa: E402
import specs_review_loop as rl  # noqa: E402

PORT = int(os.environ.get("LOOP_WIZARD_PORT", "8795"))
JOBS = lm.OUT_DIR / "jobs"
TOKEN_FILE = lm.OUT_DIR / "wizard.token"


def load_token() -> str:
    """Kept in a 0600 file so the URL survives restarts (delete the file to rotate it)."""
    try:
        tok = TOKEN_FILE.read_text().strip()
        if len(tok) >= 16:
            return tok
    except OSError:
        pass
    lm.OUT_DIR.mkdir(exist_ok=True)
    tok = secrets.token_urlsafe(16)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(tok)
    return tok


TOKEN = load_token()
WATCH_PID = lm.OUT_DIR / "watch.pid"
FOLDER_RE = re.compile(r"^projects/[\w.-]+/[\w.-]+$")
NAME_RE = re.compile(r"^[\w -]{2,30}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
BRANCH_RE = re.compile(r"^[\w./-]{1,80}$")


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd or WORKSPACE, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout + p.stderr).strip()


def loops() -> list[dict]:
    try:
        return lm.load_config()
    except SystemExit:
        return []


def save_loops(entries: list[dict]) -> None:
    lm.CONFIG.write_text(json.dumps({"loops": entries}, indent=2) + "\n", encoding="utf-8")


def raw_loops() -> list[dict]:
    if not lm.CONFIG.is_file():
        return []
    return json.loads(lm.CONFIG.read_text(encoding="utf-8"))["loops"]


def find(loop_id: str) -> dict:
    for l in loops():
        if l["id"] == loop_id:
            return l
    raise ValueError(f"unknown loop {loop_id!r}")


# --- actions -----------------------------------------------------------------

def a_state(_: dict) -> dict:
    return {"loops": lm.tick(loops(), do_launch=False), "monitor": monitor_alive()}


def a_loops(_: dict) -> dict:
    return {"loops": [{"id": l["id"], "name": l["name"], "project": l["project"], "branch": l["branch"]} for l in loops()]}


def a_git_status(_: dict) -> dict:
    _, branch = sh(["git", "branch", "--show-current"])
    out = subprocess.run(["git", "status", "--porcelain"], cwd=WORKSPACE, capture_output=True, text=True).stdout
    files = []
    for line in out.splitlines():  # "XY path" or "XY old -> new"; no strip: column 0 can be a space
        parts = [x.strip('"') for x in line[3:].split(" -> ")]
        files.append({"status": line[:2].strip() or "?", "path": parts[-1], "old": parts[0] if len(parts) > 1 else None})
    return {"branch": branch, "clean": not files, "files": files}


def a_commit(a: dict) -> dict:
    status = a_git_status({})["files"]
    allowed = {f["path"] for f in status}
    paths = a.get("paths") or []
    msg = (a.get("message") or "").strip()
    if not paths or not msg:
        raise ValueError("choose at least one file and write a message")
    bad = [p for p in paths if p not in allowed]
    if bad:
        raise ValueError(f"not changed files: {bad}")
    if not msg.upper().startswith(("HUMAN:", "CLAUDE:", "CHATGPT:", "GROK:", "DEEPSEEK:", "GEMINI:", "CURSOR:")):
        msg = "HUMAN: " + msg
    # A rename's old path is already gone from the index, so `git add` rejects it, but `git commit --only`
    # still needs it (it exists in HEAD) to commit the deletion together with the new file.
    olds = [f["old"] for f in status if f["path"] in paths and f["old"]]
    rc, out = sh(["git", "add", "--", *paths])
    if rc == 0:
        rc, out = sh(["git", "commit", "-m", msg, "--", *paths, *olds])
    return {"ok": rc == 0, "output": out}


README_TEMPLATE = """# {name} spec — multi-AI review

Review rounds for `spec.md`. General rules: `CONTRIBUTING.md`; loop rules: `generic/REVIEW_LOOP_GUIDELINE.md`.

## Current round

**Round 1** — reviewing `spec.md` **v0.1**. Reviews go in `reviews/round-1/`.
*(Updated by CLAUDE at each consolidation.)*

| File | What it is |
|---|---|
| `spec.md` | The specification. Only CLAUDE edits it, when consolidating a round. |
| `reviews/round-N/<AGENT>.md` | One review per AI per round. Each AI writes only its own file. |
| `decisions.md` | Decisions HUMAN has settled (optional). Reviewers treat them as fixed. |
| `reviews/round-N/CONSOLIDATION.md` | CLAUDE's merge of round N. |

**Stop rule:** iteration ends when a round produces no `blocking` or `major` findings, or when HUMAN stops it.

## Review format

```markdown
### <AGENT>-<n> · <short title>

- **Section:** §x.y (or "general")
- **Type:** error | gap | risk | inconsistency | suggestion | question
- **Severity:** blocking | major | minor
- **Finding:** what is wrong or missing, in two or three sentences.
- **Proposed change:** the exact text or rule to add, change or delete.
- **Evidence:** source URL + date checked, or "reasoning only".
- **Confidence:** high | medium | low
```

Rules: facts need sources; don't invent identifiers; propose, don't decide (safety, legal and scope are HUMAN decisions);
don't edit `spec.md` or another review. End with a short **Top 3**. A review ends with `Result: complete`, and has
findings or `Findings: none`.
"""


def a_create_loop(a: dict) -> dict:
    folder, name = a.get("folder", ""), a.get("name", "").strip()
    if not FOLDER_RE.match(folder) or not NAME_RE.match(name):
        raise ValueError("folder must look like projects/<project>/<spec>; name 2-30 letters/digits/spaces")
    lid = rl.slug(name)
    branch = a.get("branch") or f"agent/loop/{lid}-review"
    base = a.get("base") or sh(["git", "branch", "--show-current"])[1]
    if not ID_RE.match(lid) or not BRANCH_RE.match(branch) or not BRANCH_RE.match(base):
        raise ValueError("invalid name/branch")
    if any(l["id"] == lid for l in raw_loops()):
        raise ValueError(f"loop id {lid!r} is already registered")
    proj = WORKSPACE / folder
    if proj.exists():
        raise ValueError(f"{folder} already exists")
    log: list[str] = []

    def step(label: str, rc_out: tuple[int, str]) -> None:
        log.append(f"$ {label}\n{rc_out[1]}".rstrip())
        if rc_out[0] != 0:
            raise RuntimeError("\n".join(log))

    step(f"git checkout -b {branch} {base}", sh(["git", "checkout", "-b", branch, base]))
    (proj / "automation").mkdir(parents=True)
    (proj / "reviews").mkdir()
    (proj / "reviews" / ".gitkeep").write_text("")
    (proj / "automation" / ".gitignore").write_text("logs/\n")
    (proj / "spec.md").write_text(f"# {name} specification\n\nVersion 0.1\n\n(write the spec here)\n", encoding="utf-8")
    (proj / "README.md").write_text(README_TEMPLATE.format(name=name), encoding="utf-8")
    log.append(f"wrote {folder}/spec.md, README.md, automation/.gitignore")
    step("git add + commit", sh(["git", "add", "--", folder]))
    step("git commit", sh(["git", "commit", "-m", f"HUMAN: add {name} spec for the review loop", "--", folder]))
    entry = {"id": lid, "project": folder, "name": name, "branch": branch}
    for k in ("after", "autostart"):
        if a.get(k):
            entry[k] = a[k]
    save_loops(raw_loops() + [entry])
    log.append(f"registered loop {lid!r} in generic/loops.json")
    return {"ok": True, "id": lid, "branch": branch, "output": "\n".join(log),
            "note": "Write the real content into spec.md, commit it, then run the loop."}


def a_register(a: dict) -> dict:
    """Register an existing spec folder (already committed on its own branch)."""
    folder, name = a.get("folder", ""), a.get("name", "").strip()
    if not FOLDER_RE.match(folder) or not NAME_RE.match(name) or not (WORKSPACE / folder / "spec.md").is_file():
        raise ValueError("folder must be an existing projects/<project>/<spec> with spec.md; name 2-30 chars")
    lid = rl.slug(name)
    if any(l["id"] == lid for l in raw_loops()):
        raise ValueError(f"loop id {lid!r} is already registered")
    entry = {"id": lid, "project": folder, "name": name}
    for k in ("after", "autostart", "branch"):
        if a.get(k):
            entry[k] = a[k]
    save_loops(raw_loops() + [entry])
    return {"ok": True, "id": lid}


def monitor_alive() -> bool:
    try:
        pid = int(WATCH_PID.read_text())
        os.kill(pid, 0)
        return "loop_monitor" in Path(f"/proc/{pid}/cmdline").read_text()
    except (OSError, ValueError):
        return False


def a_monitor_start(_: dict) -> dict:
    if monitor_alive():
        return {"ok": True, "output": "monitor already running"}
    lm.OUT_DIR.mkdir(exist_ok=True)
    p = subprocess.Popen([sys.executable, str(HERE / "loop_monitor.py"), "watch", "30"], cwd=WORKSPACE,
                         stdin=subprocess.DEVNULL, stdout=open(lm.OUT_DIR / "watch.log", "a"),
                         stderr=subprocess.STDOUT, start_new_session=True)
    WATCH_PID.write_text(str(p.pid))
    return {"ok": True, "output": f"monitor started (pid {p.pid}), ticking every 30 s"}


def a_monitor_stop(_: dict) -> dict:
    if not monitor_alive():
        return {"ok": True, "output": "monitor is not running"}
    os.kill(int(WATCH_PID.read_text()), signal.SIGTERM)
    return {"ok": True, "output": "monitor stopped"}


def a_job(a: dict) -> dict:
    mode = a.get("mode")
    if mode not in ("preflight", "one", "full"):
        raise ValueError("mode must be preflight, one or full")
    l = find(a.get("id", ""))
    if lm.lock_held(WORKSPACE / l["project"] / "automation" / "logs" / ".loop.lock"):
        raise ValueError(f"{l['name']} already has a loop or preflight running; wait for it to finish (watch the colour card)")
    JOBS.mkdir(parents=True, exist_ok=True)
    jid = uuid.uuid4().hex[:8]
    logf = open(JOBS / f"{jid}.log", "w")
    p = subprocess.Popen([str(lm.LAUNCHER), l["project"], l["name"], l["branch"], mode], cwd=WORKSPACE,
                         stdin=subprocess.DEVNULL, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    (JOBS / f"{jid}.json").write_text(json.dumps({"pid": p.pid, "mode": mode, "loop": l["id"], "exit": None}))
    import threading

    def wait() -> None:
        code = p.wait()
        (JOBS / f"{jid}.json").write_text(json.dumps({"pid": p.pid, "mode": mode, "loop": l["id"], "exit": code}))

    threading.Thread(target=wait, daemon=True).start()
    return {"ok": True, "job": jid}


def a_retry(a: dict) -> dict:
    l = find(a.get("id", ""))
    (WORKSPACE / l["project"] / "automation" / "logs" / ".monitor.json").unlink(missing_ok=True)
    return {"ok": True, "output": f"cleared failed launch of {l['id']}"}


ACTIONS = {"state": a_state, "loops": a_loops, "git_status": a_git_status, "commit": a_commit,
           "create_loop": a_create_loop, "register": a_register, "monitor_start": a_monitor_start,
           "monitor_stop": a_monitor_stop, "job": a_job, "retry": a_retry}


def job_info(jid: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{8}", jid):
        raise ValueError("bad job id")
    meta = json.loads((JOBS / f"{jid}.json").read_text())
    text = (JOBS / f"{jid}.log").read_text(errors="replace")
    return {"mode": meta["mode"], "loop": meta["loop"], "running": meta["exit"] is None, "exit": meta["exit"], "output": text[-20000:]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass

    def _authorized(self) -> bool:
        host_ok = self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")
        token = self.headers.get("X-Token") or parse_qs(urlparse(self.path).query).get("t", [""])[0]
        if not token and urlparse(self.path).path == "/":  # the page itself may load with the cookie set by a first visit
            token = SimpleCookie(self.headers.get("Cookie", "")).get("wizard_token", None)
            token = token.value if token else ""
        return host_ok and secrets.compare_digest(token, TOKEN)

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        if ctype.startswith("text/html"):  # Strict: other sites cannot make the browser send it
            self.send_header("Set-Cookie", f"wizard_token={TOKEN}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj).encode())

    def do_GET(self) -> None:
        if not self._authorized():
            return self._json(403, {"error": "forbidden: open the full link once (cat generic/.monitor/wizard.url); after that plain http://127.0.0.1:8795/ works"})
        path = urlparse(self.path).path
        try:
            if path == "/":
                page = (HERE / "loop_wizard.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
                return self._send(200, page.encode(), "text/html; charset=utf-8")
            if path.startswith("/api/job/"):
                return self._json(200, job_info(path.rsplit("/", 1)[1]))
            if path.startswith("/api/") and path[5:] in ("state", "loops", "git_status"):
                return self._json(200, ACTIONS[path[5:]]({}))
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"error": str(exc)})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self._authorized():
            return self._json(403, {"error": "forbidden"})
        name = urlparse(self.path).path.removeprefix("/api/")
        fn = ACTIONS.get(name)
        if not fn:
            return self._json(404, {"error": "unknown action"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            args = json.loads(self.rfile.read(n) or b"{}")
            self._json(200, fn(args))
        except (ValueError, RuntimeError) as exc:
            self._json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/?t={TOKEN}"
    (lm.OUT_DIR / "wizard.url").write_text(url + "\n")
    print(f"Review loop assistant: {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
