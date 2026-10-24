"""Option debate contracts and human-choice gate; no providers or network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import specs_review_loop as rl
import loop_monitor as lm


class Debate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'projects/demo'
        self.project.mkdir(parents=True)
        (self.project / 'spec.md').write_text('Version 0.1\nproposal')
        (self.project / 'README.md').write_text('**Round 2**\n')
        self.workflow = self.project / 'workflow.json'
        self.workflow.write_text(json.dumps({'template': 'option-debate', 'phase': 'options', 'priorities': ['minimise costs']}))
        for key, value in dict(PROJECT=self.project, README=self.project/'README.md', SPEC=self.project/'spec.md',
                               DECISIONS=self.project/'decisions.md', LOG_DIR=self.project/'automation/logs',
                               REL_PROJECT='projects/demo', NAME='Demo').items():
            p = mock.patch.object(rl, key, value); p.start(); self.addCleanup(p.stop)
        self.reviewers = ['CHATGPT', 'DEEPSEEK', 'GROK']

    def test_templates_and_barriers(self):
        steps = rl.debate_steps(self.reviewers, 'options')
        self.assertEqual(steps, self.reviewers + [a+'-CHALLENGE' for a in self.reviewers] + [a+'-RESPONSE' for a in self.reviewers])
        for stage in ('review', 'challenge', 'response'):
            text = rl.option_prompt('CHATGPT', 2, stage, self.reviewers)
            self.assertIn('minimise costs', text)
            self.assertIn('HUMAN chooses', text)
        challenge = rl.option_prompt('CHATGPT', 2, 'challenge', self.reviewers)
        self.assertIn('DEEPSEEK, GROK', challenge)
        self.assertIn('ALL independent', challenge)
        response = rl.option_prompt('CHATGPT', 2, 'response', self.reviewers)
        self.assertIn('all *-CHALLENGE.md', response)
        consolidation = rl.consolidation_prompt(2, self.reviewers, False)
        for step in steps:
            self.assertIn(step+'.md', consolidation)
        self.assertIn('DO NOT edit or bump spec.md', consolidation)
        self.assertIn('minimise costs', consolidation)

    def test_no_human_choice_no_specification(self):
        self.workflow.write_text('{"phase":"specification", "template":"spec-review"}')
        with self.assertRaisesRegex(SystemExit, "HUMAN's explicit choice"):
            rl.workflow()
        self.workflow.write_text('{"phase":"specification", "template":"spec-review", "human_choice":"HUMAN: option B"}')
        self.assertEqual(rl.workflow()['phase'], 'specification')
        self.workflow.write_text('{"phase":"options", "template":"spec-review"}')
        with self.assertRaisesRegex(SystemExit, 'match its phase'):
            rl.workflow()

    def test_old_reviews_do_not_satisfy_debate_contract(self):
        self.assertIn('Option comparison', rl.validate_option_output('Findings: none\nResult: complete', 'review', 'CHATGPT', self.reviewers))
        challenge = '## Challenges to peers\nDEEPSEEK: agreed\n## Preferred choice\nB\nFindings: none\nResult: complete'
        self.assertIn('GROK', rl.validate_option_output(challenge, 'challenge', 'CHATGPT', self.reviewers))

    def test_options_finish_after_one_debate_even_with_major_findings(self):
        (self.project/'reviews/round-2').mkdir(parents=True)
        for agent in self.reviewers:
            (self.project/f'reviews/round-2/{agent}.md').write_text('**Severity:** major\nResult: complete')
        argv = ['loop', '--project', str(self.project), '--max-rounds', '5']
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(rl, 'configure'), \
             mock.patch.object(rl, 'repo_root', return_value=self.root), mock.patch.object(rl, 'ensure_branch'), \
             mock.patch.object(rl, 'do_review', return_value={}) as review, mock.patch.object(rl, 'do_consolidation') as consolidate:
            rl.main()
        self.assertEqual(review.call_count, 9)
        self.assertEqual([c.args[0] + ('' if c.args[3]=='review' else '-'+c.args[3].upper()) for c in review.call_args_list], rl.debate_steps(self.reviewers, 'options'))
        consolidate.assert_called_once()

    def test_restart_while_waiting_never_dispatches_reviewers(self):
        (self.project/'README.md').write_text('**Round 2**\n**Workflow status:** awaiting_human_choice')
        with mock.patch.object(sys, 'argv', ['loop', '--project', str(self.project)]), mock.patch.object(rl, 'configure'), \
             mock.patch.object(rl, 'repo_root', return_value=self.root), mock.patch.object(rl, 'do_review') as review, \
             mock.patch.object(rl, 'do_consolidation') as consolidate, mock.patch.object(rl, 'ensure_branch'):
            rl.main()
        review.assert_not_called()
        consolidate.assert_called_once()

    def test_option_consolidation_cannot_modify_proposal(self):
        rdir=self.project/'reviews/round-2'; rdir.mkdir(parents=True)
        def provider(*args):
            (rdir/'CONSOLIDATION.md').write_text('incomplete')
            rl.SPEC.write_text('Version 0.2\nchanged')
            return {}
        with mock.patch.object(rl, 'assert_clean'), mock.patch.object(rl, 'run_claude', side_effect=provider), \
             mock.patch.object(rl, 'commit_and_push') as commit:
            rl.LOG_DIR.mkdir(parents=True)
            with self.assertRaisesRegex(SystemExit, 'changed the proposal'):
                rl.do_consolidation(2, self.reviewers, False, self.root)
        commit.assert_not_called()

    def test_monitor_waits_and_blocks_chaining(self):
        (self.project/'README.md').write_text('**Round 2**\n**Workflow status:** awaiting_human_choice')
        loop = {'id':'demo','name':'Demo','project':'projects/demo','reviewers':','.join(self.reviewers)}
        with mock.patch.object(lm, 'WORKSPACE', self.root), mock.patch.object(lm, 'lock_holder', return_value=None):
            state = lm.evaluate(loop)
        self.assertEqual(state['status'], 'awaiting_choice')
        self.assertEqual(len(state['steps']), 10)
        next_loop={'id':'next','after':'demo','autostart':True}
        self.assertIsNone(lm.due([next_loop], {'demo':state, 'next':{'status':'pending'}}))

    def test_legacy_default_and_model_metadata(self):
        # Point at a project with no workflow without deleting the fixture.
        with mock.patch.object(rl, 'PROJECT', self.root):
            self.assertEqual(rl.workflow()['phase'], 'specification')
        self.assertEqual(rl.debate_steps(self.reviewers, 'specification'), self.reviewers)
        self.assertEqual(rl.step_config('DEEPSEEK-CHALLENGE')['model'], rl.DEEPSEEK_MODEL)
