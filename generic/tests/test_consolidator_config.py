"""Consolidator routing must not change reviewers or legacy loops. No provider calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import specs_review_loop as rl
import loop_project as lp

CFG = {'backend': 'CHATGPT', 'model': 'gpt-6.1-sol', 'effort': 'medium'}

class ConsolidatorConfig(unittest.TestCase):
    def test_legacy_defaults_remain_claude(self):
        with mock.patch.object(lp, 'load', return_value={}):
            self.assertEqual(rl.consolidator_config(), {'backend': 'CLAUDE'})
            self.assertEqual(rl.step_config('CLAUDE')['model'], rl.CLAUDE_MODEL)

    def test_project_override_is_consolidator_only(self):
        with mock.patch.object(lp, 'load', return_value={'consolidator': CFG}), mock.patch.object(rl, 'run_codex') as runner:
            self.assertEqual(rl.step_config('CLAUDE')['actor'], 'CHATGPT')
            self.assertEqual(rl.step_config('CLAUDE')['effort'], 'medium')
            rl.run_consolidator_codex('p', Path('/tmp'), Path('/tmp/log'), 60)
            self.assertEqual(runner.call_args.kwargs, {'model': 'gpt-6.1-sol', 'effort': 'medium'})
            self.assertEqual(rl.step_config('DEEPSEEK')['model'], rl.DEEPSEEK_MODEL)

    def test_codex_override_takes_precedence_without_mutating_reviewer_args(self):
        with mock.patch.object(rl, 'CODEX_EXTRA_ARGS', ['-c', 'model_reasoning_effort="high"']):
            args=rl.codex_args('p', Path('/tmp'), model=CFG['model'], effort=CFG['effort'])
            self.assertIn('gpt-6.1-sol', args)
            self.assertGreater(args.index('model_reasoning_effort="medium"'), args.index('model_reasoning_effort="high"'))
            self.assertNotIn('--model', rl.codex_args('p', Path('/tmp')))

    def test_chatgpt_preflight_does_not_probe_anthropic(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(lp, 'load', return_value={'consolidator': CFG}), \
             mock.patch.object(rl, 'LOG_DIR', Path(d)), mock.patch.object(rl, 'current_round', return_value=4), \
             mock.patch.object(rl, 'spec_version', return_value='0.6'), mock.patch.object(rl.shutil, 'which', return_value='/bin/tool'), \
             mock.patch.object(rl, 'run_claude') as claude, mock.patch.object(rl, 'probe_write') as probe:
            rl.preflight(Path(d), [], True)
            claude.assert_not_called()
            self.assertEqual(probe.call_args.args[1], 'CHATGPT-CONSOLIDATOR')

    def test_manifest_rejects_incomplete_config(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d)
            cfg=lp.manifest('test','test','projects/p/test','agent/loop/test-review','spec-review')
            for bad in ({'backend':'other'}, {'backend':'CHATGPT','model':'gpt-6.1-sol'}, {'backend':'CHATGPT','model':'bad name','effort':'medium'}):
                cfg['consolidator']=bad
                (project/'loop.json').write_text(json.dumps(cfg))
                with self.assertRaises(ValueError): lp.load(project)
            cfg['consolidator']=CFG
            (project/'loop.json').write_text(json.dumps(cfg))
            self.assertEqual(lp.load(project)['consolidator'], CFG)

    def test_consolidation_calls_only_codex_and_attributes_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = root/'spec.md'; spec.write_text('Version 0.6')
            readme = root/'README.md'; readme.write_text('**Round 4**')
            rdir = root/'reviews/round-4'; rdir.mkdir(parents=True)
            def finish(*args, **kwargs):
                self.assertIn('You are CHATGPT', args[0])
                spec.write_text('Version 0.7')
                readme.write_text('**Round 5**')
                (rdir/'CONSOLIDATION.md').write_text('Done')
                return {'cost_usd': 0.1}
            with mock.patch.multiple(rl, PROJECT=root, SPEC=spec, README=readme, LOG_DIR=root/'logs'), \
                 mock.patch.object(lp, 'load', return_value={'consolidator': CFG}), \
                 mock.patch.object(lp, 'validate', return_value={'ok':True}), \
                 mock.patch.object(rl, 'workflow', return_value={'phase':'specification'}), \
                 mock.patch.object(rl, 'consolidation_rels', return_value=['spec.md','README.md']), \
                 mock.patch.object(rl, 'assert_clean'), mock.patch.object(rl, 'expand_allowed', return_value=set()), \
                 mock.patch.object(rl, 'unexpected_changes', return_value=[]), \
                 mock.patch.object(rl, 'consolidation_prompt', return_value='You are CLAUDE'), \
                 mock.patch.object(rl, 'run_codex', side_effect=finish) as codex, \
                 mock.patch.object(rl, 'run_claude') as claude, \
                 mock.patch.object(rl, 'codex_banner', return_value={'model':CFG['model']}), \
                 mock.patch.object(rl, 'commit_and_push') as commit:
                rl.do_consolidation(4, ['CHATGPT'], False, root)
                claude.assert_not_called()
                self.assertEqual(codex.call_args.kwargs, {'model':CFG['model'], 'effort':'medium'})
                self.assertTrue(commit.call_args.args[2].startswith('CHATGPT:'))
                timing=json.loads((root/'logs/r4-claude.timing.json').read_text())
                self.assertEqual(timing['actor'], 'CHATGPT')
                self.assertEqual(timing['model'], CFG['model'])

    def test_disabled_consolidator_probe_keeps_reviewer_probe(self):
        cfg={**CFG, 'preflight':False}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(lp, 'load', return_value={'consolidator':cfg}), \
             mock.patch.object(rl, 'LOG_DIR', Path(d)), mock.patch.object(rl, 'current_round', return_value=4), \
             mock.patch.object(rl, 'spec_version', return_value='0.6'), mock.patch.object(rl.shutil, 'which', return_value='/bin/tool'), \
             mock.patch.object(rl, 'run_claude') as claude, mock.patch.object(rl, 'probe_write') as probe:
            rl.preflight(Path(d), ['CHATGPT'], True)
            claude.assert_not_called()
            self.assertEqual([call.args[1] for call in probe.call_args_list], ['CHATGPT'])
            state=json.loads((Path(d)/'preflight.json').read_text())
            self.assertEqual(list(state['probes']), ['CHATGPT'])
            self.assertTrue(state['passed'])
