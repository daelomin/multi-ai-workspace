"""Tests for loop_monitor.py: no provider calls. Run: python3 -m unittest discover -s generic/tests"""
import fcntl
import json
import sys
import tempfile
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
        with mock.patch.object(lm, "lock_held", return_value=True):
            s = lm.evaluate(self.loop("a"))
        self.assertEqual(s["status"], "running")
        self.assertEqual([x["status"] for x in s["steps"]], ["complete", "running", "pending"])

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
        with mock.patch.object(lm, "lock_held", side_effect=lambda p: "projects/b" in str(p)):
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
