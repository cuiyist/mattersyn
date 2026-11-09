"""Synthetic N6 publisher integration and inert workflow syntax checks only."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_site_publish as publisher
from repository_names import LEGACY_SITE_PUBLISH_WORKFLOW_NAME, SITE_PUBLISH_WORKFLOW_NAME
ROOT = Path(__file__).resolve().parents[2]


class PublishedBrandHookTests(unittest.TestCase):
    def fixture(self, root, historical=False):
        source, work = root/'source', root/'work'
        (source/'.github/workflows').mkdir(parents=True)
        (source/'tools/ci').mkdir(parents=True)
        (source/'publication').mkdir()
        (work/'receipts').mkdir(parents=True)
        (source/'.github/workflows/site-publish.yml').write_text('name: '+(
            LEGACY_SITE_PUBLISH_WORKFLOW_NAME if historical else SITE_PUBLISH_WORKFLOW_NAME)+'\n', encoding='utf-8')
        rows = []
        for relative, raw in [('tools/ci/brand_name_scan.py', b'# synthetic scanner, never executed\n'),
                              ('tools/ci/brand-name-identifiers.json', b'{"synthetic":true}\n')]:
            (source/relative).write_bytes(raw)
            rows.append({'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        (source/'publication/build-inputs.json').write_text(json.dumps({'input_files': rows}), encoding='utf-8')
        (work/'build.json').write_text(json.dumps({'source_commit': 'a'*40}), encoding='utf-8')
        args = SimpleNamespace(source=source, site_repo=publisher.SITE_REPO, site_url=publisher.SITE_URL)
        stage = {'source_commit': 'a'*40}
        push = {'source_commit': 'a'*40, 'site_commit': 'b'*40}
        return args, work, stage, push

    def report(self):
        return {'schema': 'NanoXtalSyn-N6-full-published-text-scan/1', 'phase': 'published',
                'source_commit': 'a'*40, 'site_commit': 'b'*40, 'passed': True,
                'all_selected_HTTP_verified': True, 'selected_text_file_count': 2,
                'anonymous_HTTP_verified_files': 2}

    def fake_git(self, source, *args):
        return 'a'*40 if args == ('rev-parse', 'HEAD') else ''

    def test_exact_publication_receipts_complete_preview_and_approved_Source_inputs_are_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, work, stage, push = self.fixture(Path(tmp))
            def step(name, command, cwd=None):
                self.assertEqual(cwd, args.source)
                self.assertIn('--scan', command)
                for flag, value in [('--root', work/'site-preview'), ('--manifest', work/'site-allowlist.json'),
                                    ('--source-blueprint', args.source/'publication/build-inputs.json'),
                                    ('--identifiers', args.source/'tools/ci/brand-name-identifiers.json'),
                                    ('--build-receipt', work/'build.json'), ('--stage-receipt', work/'stage.json'),
                                    ('--push-receipt', work/'push.json'), ('--live-receipt', work/'receipts/live-verification.json')]:
                    self.assertEqual(command[command.index(flag)+1], value)
                self.assertEqual(command[command.index('--site-commit')+1], 'b'*40)
                self.assertEqual(command[command.index('--source-commit')+1], 'a'*40)
                self.assertEqual(command[command.index('--phase')+1], 'published')
                Path(command[command.index('--out')+1]).write_text(json.dumps(self.report()), encoding='utf-8')
            with patch.object(publisher.rb, 'git', side_effect=self.fake_git), patch.object(publisher, 'step', side_effect=step) as run:
                self.assertTrue(publisher.scan_published_brand(args, work, stage, push)['passed'])
            self.assertEqual(run.call_count, 1)

    def test_changed_Source_commit_or_input_or_live_namespace_fails_before_scanner(self):
        for failure in ('head', 'dirty', 'stage', 'push', 'input', 'repo', 'url'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                args, work, stage, push = self.fixture(Path(tmp))
                if failure == 'stage': stage['source_commit'] = 'c'*40
                if failure == 'push': push['source_commit'] = 'c'*40
                if failure == 'input': (args.source/'tools/ci/brand_name_scan.py').write_bytes(b'changed')
                if failure == 'repo': args.site_repo = 'other/nanoxtalsyn-site'
                if failure == 'url': args.site_url = 'https://example.invalid/nanoxtalsyn-site/'
                def git(source, *command):
                    if command == ('rev-parse', 'HEAD'): return ('c' if failure == 'head' else 'a')*40
                    return ' M tracked.py' if failure == 'dirty' else ''
                with patch.object(publisher.rb, 'git', side_effect=git), patch.object(publisher, 'step') as run, contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                    publisher.scan_published_brand(args, work, stage, push)
                run.assert_not_called()

    def test_historical_Source_never_imports_or_runs_new_scanner(self):
        with tempfile.TemporaryDirectory() as tmp:
            args, work, stage, push = self.fixture(Path(tmp), historical=True)
            (args.source/'tools/ci/brand_name_scan.py').unlink()
            (args.source/'tools/ci/brand-name-identifiers.json').unlink()
            with patch.object(publisher.rb, 'git', side_effect=self.fake_git), patch.object(publisher, 'step') as run:
                result = publisher.scan_published_brand(args, work, stage, push)
            self.assertEqual(result['status'], 'not_applicable_historical_Source')
            run.assert_not_called()

    def test_incomplete_failed_wrong_commit_or_zero_file_report_fails_closed(self):
        mutations = [{'passed': False}, {'all_selected_HTTP_verified': False}, {'source_commit': 'c'*40},
                     {'site_commit': 'c'*40}, {'anonymous_HTTP_verified_files': 1},
                     {'selected_text_file_count': 0, 'anonymous_HTTP_verified_files': 0}]
        for changed in mutations:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                args, work, stage, push = self.fixture(Path(tmp))
                def step(name, command, cwd=None):
                    Path(command[command.index('--out')+1]).write_text(json.dumps(self.report() | changed), encoding='utf-8')
                with patch.object(publisher.rb, 'git', side_effect=self.fake_git), patch.object(publisher, 'step', side_effect=step), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                    publisher.scan_published_brand(args, work, stage, push)

    def test_verify_command_requires_explicit_Source_before_any_action(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            publisher.main(['verify', '--work', 'unused'])
        self.assertEqual(error.exception.code, 2)


class WorkflowSyntaxTests(unittest.TestCase):
    def test_multiline_run_blocks_are_valid_bash_and_missing_Publish_arm_is_rejected(self):
        candidates = [Path('C:/Program Files/Git/bin/bash.exe'), Path(shutil.which('bash') or 'missing')]
        bash = next((p for p in candidates if p.is_file()), None)
        if bash is None: self.skipTest('Bash unavailable for static -n check')
        env = {**os.environ, 'BASH_ENV': '', 'ENV': ''}
        blocks = []
        for name in ('site-publish.yml', 'validate-project.yml'):
            lines = (ROOT/'.github/workflows'/name).read_text(encoding='utf-8').splitlines()
            for index, line in enumerate(lines):
                if line.strip() != 'run: |': continue
                indent = len(line)-len(line.lstrip())
                body = []
                for following in lines[index+1:]:
                    if following.strip() and len(following)-len(following.lstrip()) <= indent: break
                    body.append(following[indent+2:])
                script = re.sub(r'\$\{\{.*?\}\}', 'SYNTHETIC_GITHUB_EXPRESSION', '\n'.join(body)+'\n')
                result = subprocess.run([str(bash), '--noprofile', '--norc', '-n'], input=script, text=True,
                                        capture_output=True, env=env)
                self.assertEqual(result.returncode, 0, name+': '+result.stderr)
                blocks.append(script)
        choose = next(block for block in blocks if 'case "$message" in' in block)
        self.assertIn('Publish*) built=', choose)
        broken = choose.replace('Publish*) built=', 'built=', 1)
        self.assertNotEqual(subprocess.run([str(bash), '--noprofile', '--norc', '-n'], input=broken,
                                          text=True, capture_output=True, env=env).returncode, 0)


if __name__ == '__main__':
    unittest.main()
