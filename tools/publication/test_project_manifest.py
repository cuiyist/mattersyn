"""Regression tests for stale manifests and final source closure checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_project_manifest import ManifestError, check


class SourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.write('README.md', 'Reviewed source\n')
        self.write('recipe-atlas/data/record.json', '{"value": 1}\n')
        self.write('MEMORY.md', 'Reviewed checkpoint\n')
        self.freeze_blueprint()
        self.close()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE)

    def write(self, path, value):
        out = self.root / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(value, encoding='utf-8', newline='\n')

    def dump(self, path, value):
        self.write(path, json.dumps(value, indent=2) + '\n')

    def row(self, path):
        raw = (self.root / path).read_bytes()
        return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def freeze_blueprint(self):
        paths = ['README.md', 'MEMORY.md', 'recipe-atlas/data/record.json']
        self.dump('publication/build-inputs.json', {'schema': 'mattersyn-build-input-blueprint/1', 'input_files': [self.row(p) for p in paths]})

    def close(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Reviewed payload', '--allow-empty')
        source_commit = self.git('rev-parse', 'HEAD').decode().strip()
        paths = self.git('ls-files', '-z').decode().split('\0')
        rows = [self.row(path) for path in paths if path and path != 'publication/project-allowlist.json']
        self.dump('publication/project-allowlist.json', {'schema_version': 'mattersyn-public-release-allowlist/1', 'repo': 'mattersyn', 'source_commit': source_commit, 'files': rows})
        self.git('add', '.')
        self.git('commit', '-qm', 'Approve exact source manifest', '--allow-empty')

    def edit_manifest(self, operation):
        path = 'publication/project-allowlist.json'
        data = json.loads((self.root / path).read_bytes())
        operation(data)
        self.dump(path, data)
        self.git('add', path)
        self.git('commit', '-qm', 'Fixture manifest edit')

    def test_clean_closure_passes_read_only(self):
        before = self.git('rev-parse', 'HEAD')
        result = check(self.root, pre_push=True)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['blueprint_input_count'], 3)
        self.assertEqual(before, self.git('rev-parse', 'HEAD'))
        self.assertEqual(self.git('status', '--porcelain'), b'')

    def test_unlisted_new_file_reports_path(self):
        self.write('research-assets/checkpoint.json', '{}\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'Stale manifest checkpoint')
        with self.assertRaisesRegex(ManifestError, 'unlisted tracked files: research-assets/checkpoint.json'):
            check(self.root)

    def test_stale_source_commit_reports_changed_memory(self):
        self.write('MEMORY.md', 'Changed after approval\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'Late memory update')
        with self.assertRaisesRegex(ManifestError, 'Source changed.*MEMORY.md'):
            check(self.root)

    def test_listed_but_untracked_file_rejected(self):
        self.edit_manifest(lambda data: data['files'].append({'path': 'missing.json', 'sha256': '0' * 64, 'bytes': 0}))
        with self.assertRaisesRegex(ManifestError, 'listed but untracked files: missing.json'):
            check(self.root)

    def test_duplicate_paths_rejected(self):
        self.edit_manifest(lambda data: data['files'].append(data['files'][0].copy()))
        with self.assertRaisesRegex(ManifestError, 'Duplicate source manifest paths'):
            check(self.root)

    def test_wrong_manifest_hash_rejected(self):
        self.edit_manifest(lambda data: data['files'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ManifestError, 'Source manifest hash/size mismatch'):
            check(self.root)

    def test_wrong_manifest_byte_count_rejected(self):
        self.edit_manifest(lambda data: data['files'][0].update(bytes=-1))
        with self.assertRaisesRegex(ManifestError, 'Source manifest hash/size mismatch'):
            check(self.root)

    def test_uncommitted_payload_change_rejected(self):
        self.write('MEMORY.md', 'Uncommitted update\n')
        with self.assertRaisesRegex(ManifestError, 'Source manifest hash/size mismatch.*MEMORY.md'):
            check(self.root, pre_push=True)

    def test_untracked_draft_blocks_pre_push(self):
        self.write('draft.txt', 'Not reviewed\n')
        with self.assertRaisesRegex(ManifestError, 'Pre-push requires a clean'):
            check(self.root, pre_push=True)

    def test_stale_blueprint_rejected_even_with_fresh_source_manifest(self):
        self.write('recipe-atlas/data/record.json', '{"value": 2}\n')
        self.close()
        with self.assertRaisesRegex(ManifestError, 'Build blueprint hash/size mismatch.*record.json'):
            check(self.root, pre_push=True)

    def test_unbound_build_input_rejected(self):
        self.write('recipe-atlas/data/new.json', '{}\n')
        self.close()
        with self.assertRaisesRegex(ManifestError, 'Build blueprint omits build inputs.*new.json'):
            check(self.root, pre_push=True)

    def test_blueprint_traversal_rejected(self):
        self.dump('publication/build-inputs.json', {'schema': 'mattersyn-build-input-blueprint/1', 'input_files': [{'path': '../escape.json', 'sha256': '0' * 64}]})
        self.close()
        with self.assertRaisesRegex(ManifestError, 'canonical and repository-relative'):
            check(self.root, pre_push=True)


if __name__ == '__main__':
    unittest.main()
