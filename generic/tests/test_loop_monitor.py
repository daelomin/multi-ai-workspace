"""Tests for loop_monitor.py: no provider calls. Run: python3 -m unittest discover -s generic/tests"""
import fcntl
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import loop_monitor as lm  # noqa: E402

GOOD = "# r\n\n**Severity:** major\n\nResult: complete\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        patch = mock.patch.object(lm, "WORKSPACE", self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def project(self, pid, readme="## Current round\n\n**Round 2** — x\n", rounds=("round-1",)):
        p = self.root / "projects" / pid
        (p / "automation" / "logs").mkdir(parents=True)
        (p / "spec.md").write_text("version 0.4\n")
        (p / "README.md").write_text(readme)
        for r in rounds:
            (p / "reviews" / r).mkdir(parents=True)
            (p / "reviews" / r / "CHATGPT.md").write_text(GOOD)
            (p / "reviews" / r / "CONSOLIDATION.md").write_text("x")
        return p

    def loop(self, pid, **kw):
        return {"id": pid, "project": f"projects/{pid}", "name": pid, "reviewers": "CHATGPT,GROK",
                "branch": "b", "autostart": False, **kw}


class State(Base):
    def test_pending_then_running_then_failed(self):
        p = self.project("a")
        s = lm.evaluate(self.loop("a"))
        self.assertEqual((s["status"], s["round"]), ("pending", 2))
        (p / "reviews" / "round-2").mkdir()
        (p / "reviews" / "round-2" / "CHATGPT.md").write_text(GOOD)
        (p / "automation" / "logs" / "r2-grok.log").write_text("boom")
        s = lm.evaluate(self.loop("a"))
        self.assertEqual(s["status"], "failed")
        self.assertEqual([x["status"] for x in s["steps"]], ["complete", "failed", "pending"])
        with mock.patch.object(lm, "lock_holder", return_value=1), mock.patch.object(lm, "is_preflight", return_value=False):
            s = lm.evaluate(self.loop("a"))
        self.assertEqual(s["status"], "running")
        self.assertEqual([x["status"] for x in s["steps"]], ["complete", "running", "pending"])

    def test_preflight_lock_is_not_a_running_round(self):
        self.project("a")
        with mock.patch.object(lm, "lock_holder", return_value=123), mock.patch.object(lm, "is_preflight", return_value=True):
            s = lm.evaluate(self.loop("a"))
        self.assertEqual(s["status"], "preflight")
        self.assertTrue(all(x["status"] == "pending" for x in s["steps"]))
        with mock.patch.object(lm, "lock_holder", return_value=123), mock.patch.object(lm, "is_preflight", return_value=False):
            self.assertEqual(lm.evaluate(self.loop("a"))["status"], "running")

    def test_failed_preflight_marks_backend_step(self):
        p = self.project("a")
        (p / "automation" / "logs" / "preflight.json").write_text(json.dumps(
            {"passed": False, "failed": {"GROK": "Authentication required", "ANTHROPIC": "boom"}}))
        s = lm.evaluate(self.loop("a", reviewers="CHATGPT,GROK"))
        self.assertEqual(s["status"], "failed")
        self.assertEqual([x["status"] for x in s["steps"]], ["pending", "failed", "failed"])
        self.assertIn("Authentication required", s["steps"][1]["detail"])
        (p / "automation" / "logs" / "preflight.json").write_text(json.dumps({"passed": True, "failed": {}}))
        self.assertEqual(lm.evaluate(self.loop("a", reviewers="CHATGPT,GROK"))["status"], "pending")

    def test_preflight_node_in_jarvis_graph(self):
        p = self.project("a")
        logs = p / "automation" / "logs"
        def graph():
            s = lm.evaluate(self.loop("a", reviewers="CHATGPT,GROK"))
            with mock.patch.object(lm, "JARVIS_DIR", self.root / "j"):
                lm.write_jarvis([s])
            return json.loads((self.root / "j/memory/graph_review-loop-a.json").read_text())["nodes"]
        n = graph()
        self.assertEqual(n["r2-PREFLIGHT"]["status"], "pending")
        self.assertEqual(n["r2-CHATGPT"]["depends_on"], ["r2-PREFLIGHT"])
        self.assertEqual(n["r2-PREFLIGHT"]["depends_on"], ["r1-CLAUDE"])
        with mock.patch.object(lm, "lock_holder", return_value=9), mock.patch.object(lm, "is_preflight", return_value=True):
            self.assertEqual(graph()["r2-PREFLIGHT"]["status"], "in_progress")
        (logs / "preflight.json").write_text(json.dumps({"round": 2, "passed": False, "failed": {"GROK": "auth"}}))
        self.assertEqual(graph()["r2-PREFLIGHT"]["status"], "failed")
        (logs / "preflight.json").write_text(json.dumps({"round": 2, "passed": True, "failed": {}}))
        self.assertEqual(graph()["r2-PREFLIGHT"]["status"], "completed")
        (logs / "preflight.json").write_text(json.dumps({"round": 1, "passed": True, "failed": {}}))
        self.assertEqual(graph()["r2-PREFLIGHT"]["status"], "pending")  # a pass for another round does not count

    def test_probe_nodes_in_jarvis_graph(self):
        p = self.project("a")
        logs = p / "automation" / "logs"
        (logs / "preflight.json").write_text(json.dumps({"round": 2, "done": False, "probes": {
            "DEEPSEEK": {"status": "complete", "detail": ""}, "GROK": {"status": "running", "detail": ""},
            "CHATGPT": {"status": "pending", "detail": ""}}}))
        def nodes(pre_running):
            with mock.patch.object(lm, "lock_holder", return_value=9 if pre_running else None), \
                    mock.patch.object(lm, "is_preflight", return_value=True), \
                    mock.patch.object(lm, "JARVIS_DIR", self.root / "j"):
                lm.write_jarvis([lm.evaluate(self.loop("a", reviewers="DEEPSEEK,GROK,CHATGPT"))])
            return json.loads((self.root / "j/memory/graph_review-loop-a.json").read_text())["nodes"]
        n = nodes(True)
        self.assertEqual([n[f"r2-PREFLIGHT-{k}"]["status"] for k in ("DEEPSEEK", "GROK", "CHATGPT")],
                         ["completed", "in_progress", "pending"])
        self.assertEqual(n["r2-PREFLIGHT"]["status"], "in_progress")
        self.assertEqual(set(n["r2-PREFLIGHT"]["depends_on"]), {f"r2-PREFLIGHT-{k}" for k in ("DEEPSEEK", "GROK", "CHATGPT")})
        self.assertEqual(n["r2-DEEPSEEK"]["depends_on"], ["r2-PREFLIGHT"])
        n = nodes(False)  # engine died mid-probe: the running probe is shown as failed, not running forever
        self.assertEqual(n["r2-PREFLIGHT-GROK"]["status"], "failed")
        self.assertEqual(n["r2-PREFLIGHT"]["status"], "failed")

    def test_is_preflight_reads_cmdline(self):
        import subprocess
        p = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)", "--preflight"])
        self.addCleanup(p.kill)
        for _ in range(40):  # /proc/<pid>/cmdline can read empty for a moment right after the exec
            if lm.is_preflight(p.pid):
                break
            time.sleep(0.05)
        self.assertTrue(lm.is_preflight(p.pid))
        q = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)"])
        self.addCleanup(q.kill)
        self.assertFalse(lm.is_preflight(q.pid))

    def test_complete_when_converged(self):
        self.project("a", readme="Review has converged at round 2.\n", rounds=("round-1", "round-2"))
        s = lm.evaluate(self.loop("a"))
        self.assertEqual(s["status"], "complete")
        self.assertEqual([r["n"] for r in s["rounds"]], [1, 2])

    def test_rounds_append_as_readme_advances(self):
        p = self.project("a")
        self.assertEqual([r["n"] for r in lm.evaluate(self.loop("a"))["rounds"]], [1, 2])
        (p / "README.md").write_text("**Round 3**\n")
        (p / "reviews" / "round-2").mkdir()
        (p / "reviews" / "round-2" / "CONSOLIDATION.md").write_text("x")
        self.assertEqual([r["n"] for r in lm.evaluate(self.loop("a"))["rounds"]], [1, 2, 3])

    def test_failed_launch_exit(self):
        p = self.project("a")
        (p / "automation" / "logs" / ".monitor.json").write_text(json.dumps({"pid": 1, "exit": 3}))
        self.assertEqual(lm.evaluate(self.loop("a"))["status"], "failed")

    def test_lock_held_by_flock(self):
        f = self.root / "x.lock"
        with open(f, "w") as fh:
            self.assertFalse(lm.lock_held(f))
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertTrue(lm.lock_held(f))
        self.assertFalse(lm.lock_held(f))


class Chaining(Base):
    def setUp(self):
        super().setUp()
        self.project("a", readme="converged\n", rounds=("round-1",))
        self.project("b")
        self.loops = [self.loop("a"), self.loop("b", after="a", autostart=True)]

    def states(self):
        return {l["id"]: lm.evaluate(l) for l in self.loops}

    def test_launches_after_complete(self):
        self.assertEqual(lm.due(self.loops, self.states())["id"], "b")

    def test_not_without_autostart_or_when_running_or_after_launch(self):
        self.loops[1]["autostart"] = False
        self.assertIsNone(lm.due(self.loops, self.states()))
        self.loops[1]["autostart"] = True
        with mock.patch.object(lm, "lock_holder", side_effect=lambda p: 1 if "projects/b" in str(p) else None), mock.patch.object(lm, "is_preflight", return_value=False):
            self.assertIsNone(lm.due(self.loops, self.states()))
        (self.root / "projects/b/automation/logs/.monitor.json").write_text(json.dumps({"pid": 1, "exit": 1}))
        self.assertIsNone(lm.due(self.loops, self.states()))

    def test_not_when_predecessor_incomplete(self):
        (self.root / "projects/a/README.md").write_text("**Round 2**\n")
        self.assertIsNone(lm.due(self.loops, self.states()))

    def test_tick_launches_only_with_clean_tree(self):
        with mock.patch.object(lm, "git_clean", return_value=False), mock.patch.object(lm, "launch") as la, \
                mock.patch.object(lm, "OUT_DIR", self.root / "out"), mock.patch.object(lm, "JARVIS_DIR", self.root / "j"):
            lm.tick(self.loops)
            la.assert_not_called()
        with mock.patch.object(lm, "git_clean", return_value=True), mock.patch.object(lm, "launch") as la, \
                mock.patch.object(lm, "OUT_DIR", self.root / "out"), mock.patch.object(lm, "JARVIS_DIR", self.root / "j"):
            lm.tick(self.loops)
            la.assert_called_once()
            g = json.loads((self.root / "j/memory/graph_review-loop-b.json").read_text())
            self.assertIn("r2-CHATGPT", g["nodes"])


if __name__ == "__main__":
    unittest.main()
