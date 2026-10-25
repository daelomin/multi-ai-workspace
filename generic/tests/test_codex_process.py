"""Verify probe timeout handling without calling providers."""
import json
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import specs_review_loop as r

class CodexProcess(unittest.TestCase):
    def test_timeout_stops_process_group_and_keeps_partial_text(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/'live.log'
            proc=mock.Mock(pid=4321)
            proc.wait.side_effect=[subprocess.TimeoutExpired('codex',1),0,0]
            def launch(*args,**kw):
                kw['stdout'].write('model: gpt-6.1-sol\n');kw['stdout'].flush()
                self.assertTrue(kw['start_new_session'])
                self.assertEqual(kw['stdin'],subprocess.DEVNULL)
                return proc
            with mock.patch.object(r.subprocess,'Popen',side_effect=launch),mock.patch.object(r.os,'killpg') as kill:
                with self.assertRaises(subprocess.TimeoutExpired) as exc:
                    r.run(['codex','exec'],timeout=1,output_log=log)
                self.assertEqual(kill.call_args_list,[mock.call(4321,signal.SIGTERM),mock.call(4321,signal.SIGKILL)])
                self.assertIn('model: gpt-6.1-sol',exc.exception.output)
                self.assertIsInstance(exc.exception.output,str)
            self.assertIn('model: gpt-6.1-sol',log.read_text())

    def test_live_output_remains_available_on_success(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/'live.log'
            out=r.run([sys.executable,'-c','print("MODEL_READY", flush=True)'],timeout=5,output_log=log)
            self.assertEqual(out.returncode,0)
            self.assertIn('MODEL_READY',out.stdout)
            self.assertIn('MODEL_READY',log.read_text())

    def test_preflight_uses_codex_specific_timeout(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(r.lp,'load',return_value={}), \
             mock.patch.object(r,'LOG_DIR',Path(d)),mock.patch.object(r,'current_round',return_value=4), \
             mock.patch.object(r,'spec_version',return_value='0.6'),mock.patch.object(r.shutil,'which',return_value='/bin/tool'), \
             mock.patch.object(r,'CODEX_PREFLIGHT_TIMEOUT',901),mock.patch.object(r,'run_codex') as codex:
            def probe(root,name,runner): runner('p',Path(d)/'probe.log')
            with mock.patch.object(r,'probe_write',side_effect=probe):r.preflight(Path(d),['CHATGPT'],False)
            self.assertEqual(codex.call_args.args[3],901)

    def test_probe_keeps_written_evidence(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(r,'LOG_DIR',Path(d)/'logs'), \
             mock.patch.object(r.time,'time',return_value=1),mock.patch.object(r.os,'getpid',return_value=2):
            target=Path(d)/'logs/probe-CHATGPT-1-2/probe.txt'
            def runner(prompt,log): target.write_text('CHATGPT-1-2')
            r.probe_write(Path(d),'CHATGPT',runner)
            self.assertTrue(target.exists())
