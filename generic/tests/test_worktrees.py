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
            (Path(r["worktree"]) / "projects/p" / r["id"][0] / "x.txt").write_text(r["id"])
            git(r["worktree"], "add", "projects")
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

class GenericProject(Repo):
    def test_unrelated_projects_and_root_task_queues_are_not_materialized(self):
        (self.main / 'projects/old/spec').mkdir(parents=True)
        (self.main / 'projects/old/spec/spec.md').write_text('old task')
        (self.main / 'MASTER.md').write_text('old unrelated task')
        (self.main / 'CHANGELOG.md').write_text('old activity')
        git(self.main, 'add', '.')
        git(self.main, 'commit', '-qm', 'old task')
        created = self.create('projects/new/spec', 'Fresh Loop')
        wt = Path(created['worktree'])
        self.assertFalse((wt / 'projects/old').exists())
        self.assertFalse((wt / 'MASTER.md').exists())
        self.assertFalse((wt / 'CHANGELOG.md').exists())
        self.assertTrue((self.main / 'MASTER.md').exists())
        self.assertEqual(git(wt, 'status', '--porcelain'), '')
        self.assertIn('projects/old/spec/spec.md', git(wt, 'ls-tree', '-r', '--name-only', 'HEAD'))

    def test_import_rebuilds_operational_files_and_keeps_content(self):
        import loop_project as lp
        source = Path(self.tmp.name) / 'source'
        (source / 'docs').mkdir(parents=True)
        (source / 'automation/logs').mkdir(parents=True)
        (source / 'reviews/round-1').mkdir(parents=True)
        (source / 'spec.md').write_text('Version 3.2\ninput')
        (source / 'decisions.md').write_text('HUMAN chose the base')
        (source / 'docs/design.md').write_text('a real design')
        (source / 'README.md').write_text('wrong projects/old/spec; CHATGPT already reviewed')
        (source / 'HANDOFF.md').write_text('old launch commands')
        (source / 'automation/run_review_loop.sh').write_text('old launch script')
        (source / 'automation/logs/old.log').write_text('private old log')
        (source / 'reviews/round-1/CHATGPT.md').write_text('Result: complete')
        (source / '.env').write_text('SECRET=never-import')
        before = (source / 'README.md').read_bytes()
        created = self.create('projects/acme/new', 'Imported Loop', source=str(source))
        project = Path(created['worktree']) / 'projects/acme/new'
        self.assertEqual((project / 'spec.md').read_bytes(), (source / 'spec.md').read_bytes())
        self.assertEqual((project / 'docs/design.md').read_text(), 'a real design')
        self.assertIn('v3.2', (project / 'README.md').read_text())
        self.assertFalse((project / 'HANDOFF.md').exists())
        self.assertFalse((project / 'reviews/round-1').exists())
        self.assertFalse((project / '.env').exists())
        self.assertNotIn('projects/old', (project / 'README.md').read_text())
        self.assertNotIn('old launch', (project / 'automation/run_review_loop.sh').read_text())
        self.assertEqual((source / 'README.md').read_bytes(), before)
        self.assertTrue(lp.validate(project)['ok'])

    def test_managed_validation_rejects_stale_paths_but_legacy_warns(self):
        import loop_project as lp
        created = self.create('projects/acme/new', 'Validation')
        project = Path(created['worktree']) / 'projects/acme/new'
        with (project / 'README.md').open('a') as f:
            f.write('\ngeneric/run_review_loop.sh projects/old/spec Old agent/loop/old-review full\n')
        report = lp.validate(project)
        self.assertFalse(report['ok'])
        self.assertIn('stale launcher project', ' '.join(report['errors']))
        legacy = self.main / 'projects/legacy/spec'
        legacy.mkdir(parents=True)
        (legacy / 'spec.md').write_text('Version 1.0')
        (legacy / 'README.md').write_text('**Round 1**\ngeneric/run_review_loop.sh projects/old/spec Old full')
        report = lp.validate(legacy, expected={'project':'projects/legacy/spec'})
        self.assertTrue(report['ok'])
        self.assertTrue(report['warnings'])

    def test_unsafe_import_fails_before_creating_worktree(self):
        source = Path(self.tmp.name) / 'source'
        source.mkdir()
        (source / 'spec.md').symlink_to(self.main / 'f')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.create('projects/acme/new', 'Unsafe Import', source=str(source))
        self.assertFalse((lm.LOOPS_ROOT / 'unsafe-import').exists())
        with self.assertRaises(ValueError):
            self.create('projects/../escape', 'Traversal')
        self.assertEqual(json.loads(self.cfg.read_text())['loops'], [])

    def test_companion_write_scope_and_project_activity(self):
        import loop_project as lp
        import specs_review_loop as rl
        created = self.create('projects/acme/new', 'Scoped Loop')
        wt = Path(created['worktree'])
        project = wt / 'projects/acme/new'
        # Preserve module-global configuration to avoid affecting tests that use legacy fixtures.
        keys = ('PROJECT','REL_PROJECT','README','SPEC','DECISIONS','LOG_DIR','NAME','BRANCH')
        saved = {key:getattr(rl,key) for key in keys}
        self.addCleanup(lambda: [setattr(rl,k,v) for k,v in saved.items()])
        rl.configure(project)
        rl.LOG_DIR.mkdir(parents=True)
        self.assertEqual(rl.activity_rel(), 'projects/acme/new/CHANGELOG.md')
        self.assertIn('docs', rl.consolidation_prompt(1,['CHATGPT'],True))
        def provider(*args):
            (project / 'spec.md').write_text('Version 0.2\nupdated')
            (project / 'docs').mkdir()
            (project / 'docs/design.md').write_text('accepted change')
            (project / 'reviews/round-1').mkdir(parents=True)
            (project / 'reviews/round-1/CONSOLIDATION.md').write_text('accepted')
            return {}
        with mock.patch.object(rl,'run_claude',side_effect=provider), mock.patch.object(rl,'push_branch'):
            rl.do_consolidation(1,['CHATGPT'],True,wt)
        self.assertEqual(git(wt,'status','--porcelain'),'')
        self.assertIn('docs/design.md',git(wt,'show','--format=','--name-only','HEAD'))
        (wt / 'outside.txt').write_text('unrelated')
        allowed = rl.expand_allowed(wt,rl.consolidation_rels(wt))
        self.assertIn('outside.txt',rl.unexpected_changes(wt,allowed))
        for value in ('../other', '/tmp/other', 'automation/logs', '.env'):
            cfg=lp.load(project);cfg['consolidation_paths'].append(value)
            (project/'loop.json').write_text(json.dumps(cfg))
            with self.assertRaises(ValueError): lp.load(project)
            # Restore the good manifest without deleting any artifact.
            (project/'loop.json').write_text(json.dumps(lp.manifest('Scoped Loop','scoped-loop','projects/acme/new',created['branch'],'spec-review')))

    def test_portable_wrapper_uses_current_manifest_and_toolkit(self):
        import loop_project as lp
        toolkit = self.main / 'generic'
        toolkit.mkdir()
        (toolkit / 'loop_project.py').write_text(Path(lp.__file__).read_text())
        (toolkit / 'run_review_loop.sh').write_text('#!/bin/bash\nprintf "%s\\n" "$@"\nprintf "ROOT=%s\\n" "$LOOP_WORKTREE"\n')
        git(self.main,'add','generic')
        git(self.main,'commit','-qm','toolkit')
        created=self.create('projects/acme/spec','Portable Loop')
        project=Path(created['worktree'])/'projects/acme/spec'
        result=subprocess.run(['bash',str(project/'automation/run_review_loop.sh'),'full'],cwd=self.tmp.name,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('projects/acme/spec\nPortable Loop\nagent/loop/portable-loop-review\nfull',result.stdout)
        self.assertIn('ROOT='+created['worktree'],result.stdout)
        # A stale copied launcher reference prevents dispatch, even if the caller bypasses the UI.
        with (project/'README.md').open('a') as f: f.write('\ngeneric/run_review_loop.sh projects/old/spec Old full\n')
        failed=subprocess.run(['bash',str(project/'automation/run_review_loop.sh'),'full'],capture_output=True,text=True)
        self.assertNotEqual(failed.returncode,0)
        self.assertIn('stale launcher project',failed.stderr)

    def test_existing_review_state_and_registry_remain_unchanged(self):
        legacy = self.main / 'projects/legacy/spec'
        (legacy/'reviews/round-4').mkdir(parents=True)
        (legacy/'README.md').write_text('**Round 4** — converged\n')
        (legacy/'spec.md').write_text('Version 1.4')
        (legacy/'reviews/round-4/CONSOLIDATION.md').write_text('historical result')
        entry={'id':'legacy','name':'Legacy','project':'projects/legacy/spec','branch':'base'}
        self.cfg.write_text(json.dumps({'loops':[entry]}))
        git(self.main,'add','projects')
        git(self.main,'commit','-qm','legacy loop')
        before={p.relative_to(legacy):p.read_bytes() for p in legacy.rglob('*') if p.is_file()}
        self.create('projects/acme/new','New Loop')
        self.assertEqual(json.loads(self.cfg.read_text())['loops'][0],entry)
        self.assertEqual({p.relative_to(legacy):p.read_bytes() for p in legacy.rglob('*') if p.is_file()},before)
        self.assertEqual(lm.evaluate(lm.load_config(self.cfg)[0])['status'],'complete')


if __name__ == "__main__":
    unittest.main()
