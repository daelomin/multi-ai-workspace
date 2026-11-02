"""Tests for loop_wizard.py agent selection: no server, no provider calls."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import loop_monitor as lm  # noqa: E402

with tempfile.TemporaryDirectory() as _d, mock.patch.object(lm, "OUT_DIR", Path(_d)):
    import loop_wizard as lw  # noqa: E402  (writes its token under OUT_DIR at import)


class AgentFields(unittest.TestCase):
    def test_maps_ticks_to_reviewers_and_consolidator(self):
        self.assertEqual(lw.agent_fields({"agents": ["claude", "DEEPSEEK"]}),
                         {"reviewers": "DEEPSEEK", "consolidator": True})
        self.assertEqual(lw.agent_fields({"agents": ["GROK", "CHATGPT", "DEEPSEEK"]}),
                         {"reviewers": "CHATGPT,DEEPSEEK,GROK", "consolidator": False})
        self.assertEqual(lw.agent_fields({}), {})  # page sent nothing: monitor defaults (all agents)

    def test_needs_a_reviewer_and_known_names(self):
        for bad in (["CLAUDE"], [], ["DEEPSEEK", "GEMINI"]):
            with self.assertRaises(ValueError):
                lw.agent_fields({"agents": bad})


class SetAgents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cfg = Path(self.tmp.name) / "loops.json"
        cfg.write_text(json.dumps({"loops": [{"id": "dk-metaprep", "project": "projects/dk/x", "name": "DK"}]}))
        p = mock.patch.object(lm, "CONFIG", cfg)
        p.start()
        self.addCleanup(p.stop)
        self.cfg = cfg

    def test_existing_loop_drops_chatgpt_and_grok(self):
        r = lw.a_set_agents({"id": "dk-metaprep", "agents": ["DEEPSEEK", "CLAUDE"]})
        self.assertTrue(r["ok"])
        (e,) = json.loads(self.cfg.read_text())["loops"]
        self.assertEqual((e["reviewers"], e["consolidator"]), ("DEEPSEEK", True))
        (l,) = lw.a_loops({})["loops"]
        self.assertEqual(l["agents"], ["DEEPSEEK", "CLAUDE"])

    def test_unknown_loop(self):
        with self.assertRaises(ValueError):
            lw.a_set_agents({"id": "nope", "agents": ["DEEPSEEK"]})
