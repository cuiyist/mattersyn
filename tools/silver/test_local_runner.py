"""Offline independent checks of the bounded runner; no model or network calls."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request

import local_runner as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pages = self.root / 'pages.json'
        self.validator = self.root / 'validator.py'
        self.validator.write_text('# synthetic validator fixture\n', encoding='utf-8')
        self.source = {'documents': {'main': {'source_id': 'paper-a', 'pages': {
            '1': 'Method A uses 10 mL of water.', '2': 'No additional preparation facts.'}}}}
        self.pages.write_text(json.dumps(self.source), encoding='utf-8')
        self.output = self.root / 'draft.json'
        self.args = SimpleNamespace(pages=str(self.pages), validator=str(self.validator), output=str(self.output),
                                    source_id='paper-a', family_id='CdSe', model='qwen3.5:9b', pass_id='A', page=None)
        self.tags = {'models': [{'name': name, 'digest': digest, 'details': {'format': 'gguf'}}
                                for name, digest in runner.MODELS.items()]}
        self.response = {'done': True, 'done_reason': 'stop', 'message': {'content': '{"claims":[]}'},
                         'prompt_eval_count': 30, 'eval_count': 4, 'load_duration': 1000}

    def invoke(self, side_effect=None):
        with patch.object(runner, 'call', side_effect=side_effect or [self.tags, self.response]) as call:
            with contextlib.redirect_stdout(io.StringIO()):
                runner.run(self.args)
            return call

    def preflight_rejects_without_call(self, message=None):
        with patch.object(runner, 'call') as call:
            with self.assertRaises((ValueError, FileNotFoundError)) as exc:
                runner.run(self.args)
            if message:
                self.assertIn(message, str(exc.exception))
            call.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_success_writes_draft_and_hash_bound_receipt_locally(self):
        call = self.invoke()
        self.assertEqual(call.call_count, 2)
        draft = runner.read(self.output)
        receipt = runner.read(str(self.output) + '.receipt.json')
        self.assertEqual(draft['model_sha256'], runner.MODELS[self.args.model])
        self.assertEqual(draft['pass_id'], 'A')
        self.assertFalse(draft['saw_other_draft'])
        self.assertEqual(receipt['draft_sha256'], runner.digest_bytes(self.output.read_bytes()))
        self.assertEqual(receipt['page_map_sha256'], runner.digest_bytes(self.pages.read_bytes()))
        self.assertFalse(receipt['published'])
        self.assertFalse(receipt['external_document_transfer'])
        self.assertTrue(receipt['not_accuracy_calibration'])

    def test_existing_draft_preserved_without_call(self):
        original = b'existing draft must survive'
        self.output.write_bytes(original)
        with patch.object(runner, 'call') as call, self.assertRaisesRegex(ValueError, 'already exists'):
            runner.run(self.args)
        self.assertEqual(self.output.read_bytes(), original)
        call.assert_not_called()

    def test_existing_receipt_preserved_before_model_call(self):
        receipt = Path(str(self.output) + '.receipt.json')
        receipt.write_bytes(b'prior receipt')
        self.preflight_rejects_without_call('already exists')
        self.assertEqual(receipt.read_bytes(), b'prior receipt')

    def test_empty_page_selection_blocks_before_model_call(self):
        self.args.page = [999]
        self.preflight_rejects_without_call('no source text')

    def test_blank_or_nontext_page_blocks_before_model_call(self):
        for text in (' ', None, 123):
            self.source['documents']['main']['pages'] = {'1': text}
            self.pages.write_text(json.dumps(self.source), encoding='utf-8')
            with self.subTest(text=text):
                self.preflight_rejects_without_call('empty or not text')

    def test_wrong_source_map_is_not_sent_to_model(self):
        self.args.source_id = 'another-paper'
        self.preflight_rejects_without_call('another source')

    def test_large_context_is_not_silently_truncated(self):
        self.source['documents']['main']['pages'] = {'1': 'x' * 40001}
        self.pages.write_text(json.dumps(self.source), encoding='utf-8')
        self.preflight_rejects_without_call('split explicitly')

    def test_unsupported_model_and_pass_rejected_before_call(self):
        self.args.model = 'remote-model'
        self.preflight_rejects_without_call('not locally pinned')
        self.args.model = 'qwen3.5:9b'
        self.args.pass_id = 'C'
        self.preflight_rejects_without_call('A or B')

    def test_unavailable_validator_rejected_before_call(self):
        self.validator.unlink()
        self.preflight_rejects_without_call()

    def test_git_checkout_output_rejected_before_call(self):
        (self.root / '.git').mkdir()
        self.preflight_rejects_without_call('inside a Git checkout')

    def test_git_worktree_marker_file_also_blocks(self):
        (self.root / '.git').write_text('gitdir: synthetic-worktree')
        self.preflight_rejects_without_call('inside a Git checkout')

    def test_installed_model_digest_mismatch_prevents_chat(self):
        self.tags['models'][0]['digest'] = '0' * 64
        with patch.object(runner, 'call', return_value=self.tags) as call, self.assertRaisesRegex(ValueError, 'digest differs'):
            runner.run(self.args)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[0], '/api/tags')
        self.assertFalse(self.output.exists())

    def test_absent_model_does_not_trigger_pull_or_chat(self):
        with patch.object(runner, 'call', return_value={'models': []}) as call, self.assertRaises(ValueError):
            runner.run(self.args)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[0], '/api/tags')

    def test_non_gguf_runtime_model_prevents_chat(self):
        self.tags['models'][0]['details']['format'] = 'remote'
        with patch.object(runner, 'call', return_value=self.tags) as call, self.assertRaisesRegex(ValueError, 'GGUF'):
            runner.run(self.args)
        self.assertEqual(call.call_count, 1)

    def test_incomplete_or_truncated_response_never_written(self):
        for done, reason in ((False, 'stop'), (True, 'length')):
            with self.subTest(done=done, reason=reason):
                response = {**self.response, 'done': done, 'done_reason': reason}
                with patch.object(runner, 'call', side_effect=[self.tags, response]), self.assertRaisesRegex(ValueError, 'Incomplete'):
                    runner.run(self.args)
                self.assertFalse(self.output.exists())

    def test_malformed_or_oversized_claims_schema_not_written(self):
        for claims in ({'other': []}, {'claims': {}}, {'claims': [{}] * 25}):
            response = {**self.response, 'message': {'content': json.dumps(claims)}}
            with self.subTest(claims=claims), patch.object(runner, 'call', side_effect=[self.tags, response]), self.assertRaises(ValueError):
                runner.run(self.args)
            self.assertFalse(self.output.exists())

    def test_second_pass_does_not_receive_first_output(self):
        (self.root / 'first-pass.json').write_text('UNIQUE_FIRST_PASS_CLAIM')
        self.args.pass_id = 'B'
        self.args.model = 'qwen3.5:27b'
        self.args.page = [1]
        call = self.invoke()
        payload = call.call_args_list[1].args[1]
        self.assertNotIn('UNIQUE_FIRST_PASS_CLAIM', json.dumps(payload))
        self.assertNotIn('No additional preparation facts.', json.dumps(payload))
        self.assertEqual([m['role'] for m in payload['messages']], ['system', 'user'])
        self.assertEqual(payload['model'], 'qwen3.5:27b')
        self.assertEqual(payload['keep_alive'], 0)
        self.assertFalse(payload['stream'])
        self.assertNotIn('tools', payload)

    def test_validator_change_changes_pipeline_identity(self):
        before = runner.make_config(self.validator)
        self.validator.write_text('# modified synthetic validator')
        after = runner.make_config(self.validator)
        self.assertNotEqual(before['validator_sha256'], after['validator_sha256'])

    def test_output_race_never_overwrites_prior_content(self):
        def fake(path, *args, **kwargs):
            if path == '/api/tags':
                return self.tags
            self.output.write_bytes(b'another completed run')
            return self.response
        with patch.object(runner, 'call', side_effect=fake), self.assertRaises(FileExistsError):
            runner.run(self.args)
        self.assertEqual(self.output.read_bytes(), b'another completed run')
        self.assertFalse(Path(str(self.output) + '.receipt.json').exists())


class LocalTransportTests(unittest.TestCase):
    def test_only_fixed_loopback_paths_and_explicit_proxy_disable(self):
        opener = SimpleNamespace(open=lambda request, timeout: io.StringIO('{"ok":true}'))
        requests = []
        def capture(request, timeout):
            requests.append((request, timeout))
            return io.StringIO('{"ok":true}')
        opener.open = capture
        with patch.object(runner.urllib.request, 'build_opener', return_value=opener) as build:
            self.assertEqual(runner.call('/api/tags', timeout=10), {'ok': True})
        handlers = build.call_args.args
        self.assertIsInstance(handlers[0], urllib.request.ProxyHandler)
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsInstance(handlers[1], runner.NoRedirect)
        self.assertEqual(requests[0][0].full_url, 'http://127.0.0.1:11434/api/tags')
        self.assertEqual(requests[0][0].method, 'GET')

    def test_post_is_json_to_same_loopback_host(self):
        captured = []
        def opened(request, timeout):
            captured.append(request)
            return io.StringIO('{}')
        with patch.object(runner.urllib.request, 'build_opener', return_value=SimpleNamespace(open=opened)):
            runner.call('/api/chat', {'model': 'fixture', 'messages': []})
        self.assertEqual(captured[0].full_url, 'http://127.0.0.1:11434/api/chat')
        self.assertEqual(captured[0].method, 'POST')
        self.assertEqual(json.loads(captured[0].data), {'model': 'fixture', 'messages': []})

    def test_unknown_or_remote_endpoint_never_opens(self):
        for path in ('https://example.test/api/chat', '//example.test/api/chat', '/api/pull', '/api/chat?remote=1'):
            with self.subTest(path=path), patch.object(runner.urllib.request, 'build_opener') as build, self.assertRaises(ValueError):
                runner.call(path)
            build.assert_not_called()

    def test_redirect_rejected_even_to_loopback(self):
        with self.assertRaisesRegex(ValueError, 'redirect rejected'):
            runner.NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'http://127.0.0.1:11434/api/chat')


if __name__ == '__main__':
    unittest.main()
