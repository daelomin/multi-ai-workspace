"""Worktree-per-loop tests with real git in a throwaway repo (no provider calls)."""
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import loop_monitor as lm  # noqa: E402
import loop_wizard as lw  # noqa: E402

LAUNCHER = Path(__file__).resolve().parents[1] / "run_review_loop.sh"


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.main = Path(self.tmp.name) / "ws"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "base")
        git(self.main, "config", "user.email", "t@t")
        git(self.main, "config", "user.name", "t")
        (self.main / "f").write_text("x")
        git(self.main, "add", ".")
        git(self.main, "commit", "-qm", "init")
        self.cfg = Path(self.tmp.name) / "loops.json"
        self.cfg.write_text(json.dumps({"loops": []}))
        for mod in (lm, lw):
            p = mock.patch.object(mod, "WORKSPACE", self.main)
            p.start()
            self.addCleanup(p.stop)
        for target, val in ((lm, {"LOOPS_ROOT": Path(self.tmp.name) / "ws.loops", "CONFIG": self.cfg}),):
            for k, v in val.items():
                p = mock.patch.object(target, k, v)
                p.start()
                self.addCleanup(p.stop)

    def create(self, folder, name, **kw):
        return lw.a_create_loop({"folder": folder, "name": name, **kw})


class CreateInWorktree(Repo):
    def test_new_loop_gets_its_own_worktree_branch_and_registration(self):
        r = self.create("projects/acme/billing-spec", "Billing Spec")
        wt = Path(r["worktree"])
        self.assertTrue((wt / "projects/acme/billing-spec/spec.md").is_file())
        self.assertEqual(git(wt, "branch", "--show-current"), "agent/loop/billing-spec-review")
        self.assertEqual(git(self.main, "branch", "--show-current"), "base")  # main checkout untouched
        self.assertFalse((self.main / "projects").exists())
        self.assertIn("HUMAN: add Billing Spec", git(wt, "log", "-1", "--format=%s"))
        e = json.loads(self.cfg.read_text())["loops"][0]
        self.assertEqual((e["branch"], e["worktree"]), ("agent/loop/billing-spec-review", str(wt)))

    def test_option_debate_template_is_created_and_committed(self):
        r = self.create("projects/acme/options", "Option Debate", template="option-debate")
        project = Path(r["worktree"]) / "projects/acme/options"
        self.assertEqual(json.loads((project / "workflow.json").read_text())["phase"], "options")
        self.assertIn("Challenges", (project / "README.md").read_text())
        self.assertIn("awaiting_human_choice", (project / "README.md").read_text())
        self.assertEqual(git(r["worktree"], "status", "--porcelain"), "")

    def test_two_loops_have_independent_branches_and_commits(self):
        a = self.create("projects/p/a", "Alpha")
        b = self.create("projects/p/b", "Beta")
        for r, other in ((a, b), (b, a)):
            (Path(r["worktree"]) / "x.txt").write_text(r["id"])
            git(r["worktree"], "add", "x.txt")
            git(r["worktree"], "commit", "-qm", f"on {r['id']}")
        self.assertEqual(git(a["worktree"], "log", "-1", "--format=%s"), "on alpha")
        self.assertEqual(git(b["worktree"], "log", "-1", "--format=%s"), "on beta")
        self.assertNotEqual(git(a["worktree"], "rev-parse", "HEAD"), git(b["worktree"], "rev-parse", "HEAD"))

    def test_same_branch_cannot_be_checked_out_twice(self):
        r = self.create("projects/p/a", "Alpha")
        bad = subprocess.run(["git", "worktree", "add", str(Path(self.tmp.name) / "again"), r["branch"]],
                             cwd=self.main, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)

    def test_make_worktree_for_a_legacy_loop(self):
        git(self.main, "branch", "agent/loop/old-review")
        self.cfg.write_text(json.dumps({"loops": [{"id": "old", "project": "projects/o/o", "name": "Old",
                                                   "branch": "agent/loop/old-review"}]}))
        r = lw.a_make_worktree({"id": "old"})
        self.assertEqual(git(r["worktree"], "branch", "--show-current"), "agent/loop/old-review")
        self.assertEqual(json.loads(self.cfg.read_text())["loops"][0]["worktree"], r["worktree"])
        with self.assertRaises(ValueError):
            lw.a_make_worktree({"id": "old"})

    def test_make_worktree_refuses_a_branch_checked_out_in_main(self):
        self.cfg.write_text(json.dumps({"loops": [{"id": "m", "project": "projects/m/m", "name": "M", "branch": "base"}]}))
        with self.assertRaises(RuntimeError):
            lw.a_make_worktree({"id": "m"})


class MonitorWithWorktrees(Repo):
    def test_state_is_read_from_the_worktree_and_locks_are_per_worktree(self):
        a = self.create("projects/p/a", "Alpha")
        b = self.create("projects/p/b", "Beta")
        loops = lm.load_config(self.cfg)
        la, lb = loops
        self.assertNotEqual(lm.checkout_lock(la), lm.checkout_lock(lb))
        self.assertEqual(lm.evaluate(la)["round"], 1)
        self.assertEqual(lm.evaluate(la)["worktree"], a["worktree"])
        with open(lm.checkout_lock(la), "w") as fh:  # alpha busy, beta free
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertTrue(lm.lock_held(lm.checkout_lock(la)))
            self.assertFalse(lm.lock_held(lm.checkout_lock(lb)))

    def test_cap_on_parallel_loops(self):
        self.create("projects/p/a", "Alpha")
        self.create("projects/p/b", "Beta", after="alpha", autostart=True)
        la, lb = lm.load_config(self.cfg)
        states = {"alpha": {"status": "complete"}, "beta": {"status": "pending"}}
        self.assertEqual(lm.due([la, lb], states)["id"], "beta")
        with mock.patch.object(lm, "MAX_PARALLEL", 1):
            busy = dict(states, alpha={"status": "running"}, beta={"status": "pending"})
            busy["alpha"]["status"] = "running"
            self.assertIsNone(lm.due([la, lb], dict(busy, alpha={"status": "running"})))

    def test_launcher_env_points_at_the_worktree(self):
        self.create("projects/p/a", "Alpha")
        (la,) = lm.load_config(self.cfg)
        self.assertEqual(lm.launcher_env(la)["LOOP_WORKTREE"], la["worktree"])
        self.assertNotIn("LOOP_WORKTREE", lm.launcher_env({"project": "x", "name": "x", "branch": "b"}))


class LauncherLock(Repo):
    def test_launcher_refuses_a_busy_worktree_but_not_another_one(self):
        a = self.create("projects/p/a", "Alpha")
        b = self.create("projects/p/b", "Beta")
        env = {**os.environ, "REPO": str(self.main), "DEEPSEEK_API_KEY": "x", "HOME": self.tmp.name}
        Path(self.tmp.name, ".credentials").write_text("")
        # the launcher itself needs the real backends to get past its sanity checks, so only test the lock
        # mechanics it uses: flock on <git-dir>/review-loop.lock, per worktree
        lock_a = lm.checkout_lock({"worktree": a["worktree"], "project": "x"})
        lock_b = lm.checkout_lock({"worktree": b["worktree"], "project": "x"})
        holder = subprocess.Popen(["bash", "-c", f'exec 9>"{lock_a}"; flock -n 9 && sleep 5'])
        self.addCleanup(lambda: (holder.kill(), holder.wait()))
        import time
        time.sleep(0.5)
        busy = subprocess.run(["bash", "-c", f'exec 9>"{lock_a}"; flock -n 9 || echo BLOCKED'], capture_output=True, text=True)
        free = subprocess.run(["bash", "-c", f'exec 9>"{lock_b}"; flock -n 9 && echo FREE'], capture_output=True, text=True)
        self.assertIn("BLOCKED", busy.stdout)
        self.assertIn("FREE", free.stdout)

    def test_launcher_source_uses_per_gitdir_lock_and_worktree_root(self):
        src = LAUNCHER.read_text()
        self.assertIn("rev-parse --absolute-git-dir", src)
        self.assertIn('ROOT="${LOOP_WORKTREE:-$REPO}"', src)
        self.assertIn('--project "$ROOT/$PROJECT"', src)


if __name__ == "__main__":
    unittest.main()
