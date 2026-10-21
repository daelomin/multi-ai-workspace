"""Mocked tests for specs_review_loop.py: no provider calls. Run: python3 -m unittest discover -s generic/tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import specs_review_loop as rl  # noqa: E402

GOOD = "# X review — round 2\n\n**Severity:** major\n\nResult: complete\n"
CLEAN = "# X review — round 2\n\nFindings: none\nResult: complete\n"


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout


class ValidateReview(unittest.TestCase):
    def test_accepts_findings_and_clean(self):
        self.assertIsNone(rl.validate_review(GOOD))
        self.assertIsNone(rl.validate_review(CLEAN))

    def test_rejects_partial_and_contradictory(self):
        self.assertIn("Result: complete", rl.validate_review("**Severity:** major\n"))
        self.assertIn("no Severity", rl.validate_review("Result: complete\n"))
        self.assertIn("contradictory", rl.validate_review(GOOD + "Findings: none\n"))


class SymlinkedSpec(unittest.TestCase):
    def test_spec_rels_includes_the_symlink_target(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            proj = root / "projects/p/s"
            proj.mkdir(parents=True)
            (proj / "Real_Spec.md").write_text("Version 1.1")
            (proj / "spec.md").symlink_to("Real_Spec.md")
            with mock.patch.object(rl, "SPEC", proj / "spec.md"):
                self.assertEqual(rl.spec_rels(root), ["projects/p/s/spec.md", "projects/p/s/Real_Spec.md"])
            (proj / "plain.md").write_text("x")
            with mock.patch.object(rl, "SPEC", proj / "plain.md"):
                self.assertEqual(rl.spec_rels(root), ["projects/p/s/plain.md"])

    def test_symlink_target_edit_is_not_flagged_as_unexpected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            git(root, "init", "-q")
            proj = root / "projects/p/s"
            proj.mkdir(parents=True)
            (proj / "Real_Spec.md").write_text("Version 1.1\n")
            (proj / "spec.md").symlink_to("Real_Spec.md")
            git(root, "add", ".")
            git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i")
            (proj / "spec.md").write_text("Version 1.2\n")  # writes through the link
            with mock.patch.object(rl, "SPEC", proj / "spec.md"), mock.patch.object(rl, "REL_PROJECT", "projects/p/s"):
                self.assertEqual(rl.unexpected_changes(root, set(rl.spec_rels(root))), [])
                self.assertEqual(rl.unexpected_changes(root, {"projects/p/s/spec.md"}), ["projects/p/s/Real_Spec.md"])


class Cost(unittest.TestCase):
    USAGE = {"modelUsage": {"deepseek-flash": {"inputTokens": 1_000_000, "cacheReadInputTokens": 1_000_000, "outputTokens": 1_000_000}}}

    def test_peak_window_is_beijing_weekday_9_12_and_14_18(self):
        import calendar
        wed = lambda h, m=0: calendar.timegm((2026, 10, 21, h - 8, m, 0))  # Wed, Beijing hour h
        sat = calendar.timegm((2026, 10, 24, 10 - 8, 0, 0))
        self.assertTrue(rl.deepseek_peak(wed(9)) and rl.deepseek_peak(wed(11, 59)) and rl.deepseek_peak(wed(17, 59)))
        self.assertFalse(rl.deepseek_peak(wed(12)) or rl.deepseek_peak(wed(13, 59)) or rl.deepseek_peak(wed(18)) or rl.deepseek_peak(sat))

    def test_deepseek_cost_from_tokens_at_list_prices(self):
        import calendar
        with mock.patch.object(rl, "CNY_USD", 0.14):
            peak = rl.deepseek_cost(self.USAGE, calendar.timegm((2026, 10, 21, 2, 0, 0)))   # 10:00 Beijing
            off = rl.deepseek_cost(self.USAGE, calendar.timegm((2026, 10, 21, 12, 0, 0)))   # 20:00 Beijing
        self.assertAlmostEqual(peak[0], (0.04 + 2.0 + 8.0) * 0.14, places=3)   # 1M hit + 1M miss + 1M out
        self.assertAlmostEqual(off[0], (0.02 + 1.0 + 4.0) * 0.14, places=3)
        self.assertIn("peak", peak[1])

    def test_unknown_model_is_priced_as_flash_and_flagged(self):
        usd, basis = rl.deepseek_cost({"modelUsage": {"mystery": {"outputTokens": 1_000_000}}}, 0)
        self.assertGreater(usd, 0)
        self.assertIn("flash", basis)

    def test_note_keeps_a_zero_cost(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "LOG_DIR", Path(d)):
            with rl.timed(1, "GROK") as t:
                t.note(cost_usd=0.0, cost_basis="x")
            self.assertEqual(json.loads((Path(d) / "r1-grok.timing.json").read_text())["cost_usd"], 0.0)


class VersionLine(unittest.TestCase):
    def test_common_spellings(self):
        for head, want in (("# X\n\nVersion 0.4 (draft)", "0.4"), ("**Version:** 1.1 (proposal)  \n**Date:**", "1.1"),
                           ("version: 2.10", "2.10"), ("Version v3.0", "3.0")):
            self.assertEqual(rl.VERSION_RE.search(head).group(1), want, head)
        self.assertIsNone(rl.VERSION_RE.search("Versions of the thing 1.2; conversion 3.4"))

    def test_bump_is_detected_in_bold_style(self):
        self.assertNotEqual(rl.VERSION_RE.search("**Version:** 1.1").group(1), rl.VERSION_RE.search("**Version:** 1.2").group(1))


class Timing(unittest.TestCase):
    def test_fmt_duration(self):
        self.assertEqual([rl.fmt_duration(x) for x in (4, 91, 477, 3725)], ["4s", "1m31s", "7m57s", "1h02m05s"])

    def test_timed_writes_start_then_end_and_marks_failure(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "LOG_DIR", Path(d)):
            with rl.timed(3, "GROK"):
                self.assertNotIn("end", json.loads((Path(d) / "r3-grok.timing.json").read_text()))
            t = json.loads((Path(d) / "r3-grok.timing.json").read_text())
            self.assertTrue(t["ok"] and "seconds" in t and "end" in t)
            with self.assertRaises(RuntimeError), rl.timed(3, "CLAUDE"):
                raise RuntimeError("boom")
            self.assertFalse(json.loads((Path(d) / "r3-claude.timing.json").read_text())["ok"])


class StepConfig(unittest.TestCase):
    def test_models_efforts_tiers(self):
        with mock.patch.object(rl, "GROK_MODEL", "grok-4.7-high-fast"), mock.patch.object(rl, "DEEPSEEK_MODEL", "deepseek-flash"), \
                mock.patch.object(rl, "DEEPSEEK_EFFORT", ""), mock.patch.object(rl, "CONSOLIDATOR_EFFORT", "high"), \
                mock.patch.object(rl, "CODEX_SERVICE_TIER", "fast"), \
                mock.patch.object(rl, "CODEX_EXTRA_ARGS", ["-c", 'model_reasoning_effort="high"']):
            self.assertEqual(rl.step_config("GROK"), {"model": "grok-4.7-high-fast", "effort": "high", "tier": "fast"})
            self.assertEqual(rl.step_config("DEEPSEEK"), {"model": "deepseek-flash", "effort": "default", "tier": ""})
            self.assertEqual(rl.step_config("CLAUDE")["effort"], "high")
            c = rl.step_config("CHATGPT")
            self.assertEqual((c["effort"], c["tier"]), ("high", "fast"))

    def test_all_defaults_are_medium(self):
        for agent in ("CHATGPT", "DEEPSEEK", "GROK", "CLAUDE"):
            self.assertEqual(rl.step_config(agent)["effort"], "medium", agent)
        self.assertIn('model_reasoning_effort="medium"', rl.CODEX_EXTRA_ARGS)

    def test_codex_banner_is_what_actually_ran(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "l.log"
            f.write_text("$ codex exec\n--- stderr\nOpenAI Codex v1\n--------\nmodel: gpt-6.1-sol\nprovider: openai\n"
                         "reasoning effort: medium\nsession id: x\n")
            self.assertEqual(rl.codex_banner(f), {"model": "gpt-6.1-sol", "effort": "medium"})
            self.assertEqual(rl.codex_banner(Path(d) / "missing"), {})

    def test_timing_file_carries_config_and_reported_model(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "LOG_DIR", Path(d)):
            with rl.timed(3, "DEEPSEEK") as t:
                self.assertIn("model", json.loads((Path(d) / "r3-deepseek.timing.json").read_text()))
                t.note(reported="deepseek-flash")
            j = json.loads((Path(d) / "r3-deepseek.timing.json").read_text())
            self.assertEqual((j["reported"], j["effort"]), ("deepseek-flash", rl.DEEPSEEK_EFFORT or "default"))

    def test_effort_flag_passed_to_claude_code_only_when_set(self):
        seen = []
        def fake_run(args, **kw):
            seen.append(args)
            return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "run", fake_run), \
                mock.patch.object(rl, "ANTHROPIC_CONFIG_DIR", Path(d)):
            with mock.patch.object(rl, "CONSOLIDATOR_EFFORT", "xhigh"):
                rl._claude_once("ANTHROPIC", "p", Path(d), Path(d) / "l", 5, "m")
            with mock.patch.object(rl, "CONSOLIDATOR_EFFORT", ""):
                rl._claude_once("ANTHROPIC", "p", Path(d), Path(d) / "l", 5, "m")
        self.assertEqual(seen[0][seen[0].index("--effort") + 1], "xhigh")
        self.assertNotIn("--effort", seen[1])


class DeepSeekProfile(unittest.TestCase):
    def test_deepseek_never_uses_the_default_claude_profile(self):
        seen = {}

        def fake_run(args, cwd=None, env=None, **kw):
            seen["env"] = env
            return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")

        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "run", fake_run), \
                mock.patch.object(rl, "deepseek_key", return_value="k"), \
                mock.patch.object(rl, "DEEPSEEK_CONFIG_DIR", Path(d) / "ds"), \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/home/x/.claude"}):
            rl._claude_once("DEEPSEEK", "p", Path(d), Path(d) / "l.log", 5, "deepseek-chat")
            self.assertEqual(seen["env"]["CLAUDE_CONFIG_DIR"], str(Path(d) / "ds"))


class Reviewers(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(rl.parse_reviewers("chatgpt, Deepseek,GROK"), ["CHATGPT", "DEEPSEEK", "GROK"])

    def test_rejects_unknown_empty_duplicate(self):
        for bad in ("FOO", "GROK,,CHATGPT", "", "GROK,GROK"):
            with self.assertRaises(SystemExit):
                rl.parse_reviewers(bad)


class CodexArgs(unittest.TestCase):
    def test_no_obsolete_flag_and_shared_builder(self):
        a = rl.codex_args("p", Path("/r"), Path("/r/l.md"))
        self.assertNotIn("--full-auto", a)
        self.assertIn("--approve-for-me", a)
        self.assertNotIn("-s", a)
        self.assertEqual(a[-1], "p")

    def test_dangerous_is_opt_in(self):
        with mock.patch.dict(os.environ, {"CODEX_DANGEROUS_FULL_ACCESS": "1"}):
            self.assertIn("--dangerously-bypass-approvals-and-sandbox", rl.codex_args("p", Path("/r")))
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", rl.codex_args("p", Path("/r")))

    def test_timeout_is_logged(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(rl, "run", side_effect=subprocess.TimeoutExpired("codex", 1)):
            log = Path(d) / "l.log"
            with self.assertRaises(SystemExit):
                rl.run_codex("p", Path(d), log, 1)
            self.assertIn("TIMEOUT", log.read_text())


class CodexUsage(unittest.TestCase):
    def session(self, d, events):
        f = Path(d) / "2026/10/14/rollout-x-abc123.jsonl"
        f.parent.mkdir(parents=True)
        f.write_text("\n".join(json.dumps({"payload": {"type": "token_count", "info": e}}) for e in events))

    def ev(self, tin, cached, out, last_in, window=475000):
        return {"total_token_usage": {"input_tokens": tin, "cached_input_tokens": cached,
                                      "cache_write_input_tokens": 0, "output_tokens": out,
                                      "reasoning_output_tokens": 0, "total_tokens": tin + out},
                "last_token_usage": {"input_tokens": last_in}, "model_context_window": window}

    LOG = "model: gpt-6.1-sol\nsession id: abc123\n"

    def test_sums_requests_dedupes_and_prices(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "CODEX_SESSIONS", Path(d)):
            self.session(d, [self.ev(1000, 0, 100, 1000), self.ev(1000, 0, 100, 1000),
                             self.ev(3000, 1000, 300, 2000)])
            u = rl.codex_usage(self.LOG)
        self.assertEqual((u["requests"], u["input_tokens"], u["cached_input_tokens"], u["output_tokens"]),
                         (2, 3000, 1000, 300))
        self.assertEqual(u["max_request_context_tokens"], 2000)
        self.assertEqual(u["context_window"], 475000)
        # fresh 2000*2 + cached 1000*0.1 + out 300*10 = 4000+100+3000 per 1e6
        self.assertAlmostEqual(u["cost_usd"], 0.0071, places=4)
        self.assertGreater(u["cost_usd_upper_bound"], u["cost_usd"])

    def test_long_context_threshold_selects_tier(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "CODEX_SESSIONS", Path(d)), \
                mock.patch.object(rl, "CODEX_LONG_CONTEXT_TOKENS", 1500):
            self.session(d, [self.ev(2000, 0, 0, 2000)])
            u = rl.codex_usage(self.LOG)
        self.assertEqual(u["cost_usd"], u["cost_usd_upper_bound"])
        self.assertAlmostEqual(u["cost_usd"], 0.008, places=4)  # 2000 * $4/M

    def test_fast_tier_doubles_cost_and_is_passed_to_codex(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "CODEX_SESSIONS", Path(d)):
            self.session(d, [self.ev(1000, 0, 100, 1000)])
            std = rl.codex_usage(self.LOG)
            with mock.patch.object(rl, "CODEX_SERVICE_TIER", "fast"):
                fast = rl.codex_usage(self.LOG)
                self.assertIn('service_tier="fast"', rl.codex_args("p", Path("/r")))
        self.assertEqual(fast["service_tier"], "fast")
        self.assertAlmostEqual(fast["cost_usd"], 2 * std["cost_usd"], places=4)
        self.assertNotIn('service_tier="fast"', rl.codex_args("p", Path("/r")))

    def test_unknown_model_and_missing_session(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "CODEX_SESSIONS", Path(d)):
            self.session(d, [self.ev(1000, 0, 100, 1000)])
            self.assertIsNone(rl.codex_usage(self.LOG.replace("gpt-6.1-sol", "other"))["cost_usd"])
            self.assertIsNone(rl.codex_usage("model: x\nsession id: nope\n"))
            self.assertIsNone(rl.codex_usage("no session line"))


class Provenance(unittest.TestCase):
    def fake(self, usage, out_extra=""):
        res = subprocess.CompletedProcess([], 0, stdout="", stderr=out_extra)
        return ({"is_error": False, "modelUsage": usage, "result": "OK"}, res)

    def run_ds(self, usage, accept):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(rl, "_claude_once", return_value=self.fake(usage)), \
                mock.patch.object(rl, "DEEPSEEK_ACCEPT_UNVERIFIED", accept):
            return rl.run_claude("DEEPSEEK", "p", Path(d), Path(d) / "l.log", 1)

    def test_verified(self):
        r = self.run_ds({rl.DEEPSEEK_MODEL: {}}, False)
        self.assertTrue(r["_provenance"]["verified"])

    def test_empty_telemetry_needs_opt_in(self):
        with self.assertRaises(SystemExit):
            self.run_ds({}, False)
        r = self.run_ds({}, True)
        self.assertFalse(r["_provenance"]["verified"])

    def test_contradictory_model_fails_even_with_opt_in(self):
        with self.assertRaises(SystemExit):
            self.run_ds({"claude-sonnet-5-5": {}}, True)

    def test_unrecognized_model_retries_once_but_not_on_401(self):
        bad = ({"is_error": True, "result": "x"}, subprocess.CompletedProcess([], 1, stdout="", stderr="unrecognized_model"))
        ok = self.fake({"deepseek-chat": {}})
        calls = []

        def once(profile, prompt, root, logfile, timeout, model):
            calls.append(model)
            return bad if len(calls) == 1 else ok
        with tempfile.TemporaryDirectory() as d, mock.patch.object(rl, "_claude_once", side_effect=once):
            r = rl.run_claude("DEEPSEEK", "p", Path(d), Path(d) / "l.log", 1)
        self.assertEqual(calls, [rl.DEEPSEEK_MODEL, "deepseek-chat"])
        self.assertEqual(r["_provenance"]["requested"], "deepseek-chat")
        auth = ({"is_error": True, "result": "401"}, subprocess.CompletedProcess(
            [], 1, stdout='"api_error_status":401', stderr="unrecognized_model"))
        calls.clear()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(rl, "_claude_once", side_effect=lambda *a: (calls.append(1), auth)[1]):
            with self.assertRaises(SystemExit):
                rl.run_claude("DEEPSEEK", "p", Path(d), Path(d) / "l.log", 1)
        self.assertEqual(len(calls), 1)


BRANCH = "agent/loop/fuelbuddy-review"


class GitFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.origin, self.root = t / "origin.git", t / "work"
        git(t, "init", "-q", "--bare", "-b", BRANCH, str(self.origin))
        git(t, "clone", "-q", str(self.origin), str(self.root))
        git(self.root, "config", "user.email", "t@t")
        git(self.root, "config", "user.name", "t")
        self.proj = self.root / "projects/fuelbuddy/charging-diagnostic"
        (self.proj / "reviews/round-2").mkdir(parents=True)
        (self.proj / "automation/logs").mkdir(parents=True)
        (self.proj / "spec.md").write_text("# S\n\n**Technical specification — version 0.3**\n")
        (self.root / "CHANGELOG.md").write_text("# c\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")
        git(self.root, "push", "-q", "-u", "origin", BRANCH)
        rl.configure(self.proj, name="FuelBuddy")
        self.patches = [mock.patch("time.sleep")]
        for p in self.patches:
            p.start()
        self.rel = "projects/fuelbuddy/charging-diagnostic/reviews/round-2/GROK.md"

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_configure_defaults(self):
        self.assertEqual(rl.BRANCH, BRANCH)
        self.assertEqual(rl.REL_PROJECT, "projects/fuelbuddy/charging-diagnostic")
        self.assertEqual(rl.LOG_DIR, (self.proj / "automation/logs").resolve())
        rl.configure(self.proj)
        self.assertEqual((rl.NAME, rl.BRANCH), ("fuelbuddy", BRANCH))
        other = self.root / "specs" / "My Thing"
        other.mkdir(parents=True)
        rl.configure(other, branch="agent/loop/custom")
        self.assertEqual((rl.NAME, rl.BRANCH, rl.REL_PROJECT), ("My Thing", "agent/loop/custom", "specs/My Thing"))
        rl.configure(other)
        self.assertEqual(rl.BRANCH, "agent/loop/my-thing-review")
        with self.assertRaises(SystemExit):
            rl.configure(self.root / "missing")

    def test_decisions_rule_only_when_file_exists(self):
        self.assertNotIn("decisions.md", rl.review_prompt("GROK", 2))
        self.assertIn("FuelBuddy spec review round 2", rl.review_prompt("GROK", 2))
        (self.proj / "decisions.md").write_text("# d\n")
        self.assertIn("charging-diagnostic/decisions.md", rl.review_prompt("GROK", 2))
        self.assertIn("decisions.md", rl.consolidation_prompt(2, ["GROK"], False))

    def test_pre_staged_unrelated_change_is_refused(self):
        (self.root / "other.txt").write_text("x")
        git(self.root, "add", "other.txt")
        with self.assertRaises(SystemExit):
            rl.assert_clean(self.root)
        (self.root / self.rel).write_text(GOOD)
        with self.assertRaises(SystemExit):
            rl.commit_and_push(self.root, [self.rel, "CHANGELOG.md"], "m")
        self.assertNotIn(self.rel, git(self.root, "log", "--name-only"))

    def test_resume_pushes_complete_but_unpushed_review(self):
        (self.root / self.rel).write_text(GOOD)
        self.assertFalse(rl.is_pushed(self.root, self.rel))
        rl.do_review("GROK", 2, self.root)  # file exists and validates: resume at commit/push
        git(self.root, "fetch", "-q")
        self.assertTrue(rl.is_pushed(self.root, self.rel))

    def test_unfinished_existing_file_is_not_skipped(self):
        (self.root / self.rel).write_text("**Severity:** major\n")  # no Result: complete
        with self.assertRaises(SystemExit):
            rl.do_review("GROK", 2, self.root)

    def test_clean_review_accepted_and_pushed(self):
        (self.root / self.rel).write_text(CLEAN)
        rl.do_review("GROK", 2, self.root)
        self.assertTrue(rl.is_pushed(self.root, self.rel))

    def test_forbidden_edit_by_reviewer_is_detected(self):
        (self.root / "spec-extra.md").write_text("x")
        self.assertEqual(rl.unexpected_changes(self.root, {self.rel}), ["spec-extra.md"])

    def test_failed_push_then_resume(self):
        (self.root / self.rel).write_text(GOOD)
        real = rl.run

        def flaky(cmd, *a, **k):
            if cmd[:2] == ["git", "push"]:
                return subprocess.CompletedProcess(cmd, 1, "", "denied")
            return real(cmd, *a, **k)
        with mock.patch.object(rl, "run", side_effect=flaky):
            with self.assertRaises(SystemExit):
                rl.commit_and_push(self.root, [self.rel, "CHANGELOG.md"], "m")
        self.assertEqual(git(self.root, "rev-list", "--count", f"origin/{BRANCH}..HEAD").strip(), "1")
        rl.ensure_branch(self.root)  # pushes pending commits
        self.assertEqual(git(self.root, "rev-list", "--count", f"origin/{BRANCH}..HEAD").strip(), "0")


if __name__ == "__main__":
    unittest.main()
