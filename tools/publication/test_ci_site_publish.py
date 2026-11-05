"""Staging, commit and push mechanics of the GitHub site publisher, on local Git repositories."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_site_publish as publisher  # noqa: E402


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class SitePublisherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name)
        seed = root / 'seed'
        (seed / 'data/records').mkdir(parents=True)
        (seed / '.github/workflows').mkdir(parents=True)
        for i in range(5):
            (seed / f'data/records/r{i}.json').write_bytes((json.dumps({'record_id': f'r{i}'})).encode('utf-8'))
        (seed / 'index.html').write_bytes(('<p>old</p>').encode('utf-8'))
        (seed / 'gone.txt').write_bytes(('remove me').encode('utf-8'))
        (seed / '.github/workflows/pages.yml').write_bytes(('name: pages\n').encode('utf-8'))
        sh('git', 'init', '-q', '-b', 'main', cwd=seed)
        sh('git', 'config', 'core.autocrlf', 'false', cwd=seed)  # exact bytes, as the site's '* -text'
        sh('git', 'add', '-A', cwd=seed)
        sh('git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-qm', 'Publish 1 papers', cwd=seed)
        self.remote = root / 'remote.git'
        sh('git', 'clone', '-q', '--bare', str(seed), str(self.remote))
        sh('git', '-C', str(self.remote), 'config', 'uploadpack.allowFilter', 'true')
        sh('git', '-C', str(self.remote), 'config', 'uploadpack.allowAnySHA1InWant', 'true')
        self.site = root / 'site'
        sh('git', 'clone', '-q', '--filter=blob:none', '--no-checkout', '--depth', '1', self.remote.as_uri(), str(self.site))
        self.base = sh('git', '-C', str(self.site), 'rev-parse', 'HEAD')
        self.work = root / 'work'
        preview = self.work / 'site-preview'
        (preview / 'data/records').mkdir(parents=True)
        (preview / '.github/workflows').mkdir(parents=True)
        for i in range(5):
            (preview / f'data/records/r{i}.json').write_bytes((json.dumps({'record_id': f'r{i}'})).encode('utf-8'))
        (preview / 'data/records/r5.json').write_bytes((json.dumps({'record_id': 'r5'})).encode('utf-8'))
        (preview / 'index.html').write_bytes(('<p>new</p>').encode('utf-8'))
        (preview / '.github/workflows/pages.yml').write_bytes(('name: pages\n').encode('utf-8'))
        self.preview = preview

    def tearDown(self):
        self.tmp.cleanup()

    def stage(self):
        rows, added, changed, removed = publisher.diff_trees(self.preview, self.site)
        stage = {'source_commit': 'a' * 40, 'site_base_commit': self.base,
                 'preview_tree_sha256': publisher.rb.tree_digest(self.preview), 'new_papers': {},
                 'files_added': added, 'files_changed': changed, 'files_removed': removed,
                 'entries': {p: rows[p] for p in added + changed}}
        publisher.rb.write_json(self.work / 'stage.json', stage)
        return stage

    def push(self, token='secret-token'):
        os.environ['TEST_SITE_TOKEN'] = token
        try:
            with redirect_stdout(io.StringIO()):
                return publisher.main(['push', '--work', str(self.work), '--site', str(self.site),
                                       '--token-env', 'TEST_SITE_TOKEN'])
        finally:
            del os.environ['TEST_SITE_TOKEN']

    def test_diff_uses_blob_ids_without_downloading_site_files(self):
        stage = self.stage()
        self.assertEqual(stage['files_added'], ['data/records/r5.json'])
        self.assertEqual(stage['files_changed'], ['index.html'])
        self.assertEqual(stage['files_removed'], ['gone.txt'])
        self.assertEqual(sh('git', '-C', str(self.site), 'count-objects', '-v').count('count: 0'), 1)

    def test_live_check_names_only_built_files(self):
        (self.preview / '.github/workflows/pages.yml').write_bytes(('name: pages v2\n').encode('utf-8'))
        (self.preview / '.release-control').mkdir()
        (self.preview / '.release-control/site-allowlist.json').write_bytes(b'{}')
        stage = self.stage()
        self.assertIn('.github/workflows/pages.yml', stage['files_changed'])
        self.assertIn('.release-control/site-allowlist.json', stage['files_added'])
        self.assertEqual(publisher.built_changed_paths(stage), ['data/records/r5.json', 'index.html'])

    def test_one_ordinary_commit_is_pushed_on_top_of_site_main(self):
        self.stage()
        self.assertEqual(self.push(), 0)
        log = sh('git', '-C', str(self.remote), 'log', '--format=%P %s', 'main').splitlines()
        self.assertEqual(log[0], f'{self.base} Publish site from source aaaaaaa')
        self.assertEqual(sh('git', '-C', str(self.remote), 'show', 'main:index.html'), '<p>new</p>')
        names = sh('git', '-C', str(self.remote), 'ls-tree', '-r', '--name-only', 'main').splitlines()
        self.assertIn('data/records/r5.json', names)
        self.assertNotIn('gone.txt', names)
        receipt = json.loads((self.work / 'push.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['pushed'])

    def test_moved_site_main_fails_without_force(self):
        self.stage()
        other = Path(self.tmp.name) / 'other'
        sh('git', '-c', 'core.autocrlf=false', 'clone', '-q', str(self.remote), str(other))
        (other / 'index.html').write_bytes(('<p>someone else</p>').encode('utf-8'))
        sh('git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-qam', 'other', cwd=other)
        sh('git', 'push', '-q', 'origin', 'main', cwd=other)
        moved = sh('git', '-C', str(self.remote), 'rev-parse', 'main')
        with self.assertRaises(SystemExit):
            self.push()
        self.assertEqual(sh('git', '-C', str(self.remote), 'rev-parse', 'main'), moved)

    def test_missing_token_builds_but_pushes_nothing(self):
        self.stage()
        self.assertEqual(self.push(token=''), 0)
        receipt = json.loads((self.work / 'push.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['pushed'])
        self.assertIn('not set', receipt['reason'])
        self.assertEqual(sh('git', '-C', str(self.remote), 'rev-parse', 'main'), self.base)

    def test_unchanged_site_pushes_nothing(self):
        (self.preview / 'index.html').write_bytes(('<p>old</p>').encode('utf-8'))
        (self.preview / 'data/records/r5.json').unlink()
        (self.preview / 'gone.txt').write_bytes(('remove me').encode('utf-8'))
        stage = self.stage()
        self.assertFalse(stage['files_added'] or stage['files_changed'] or stage['files_removed'])
        self.assertEqual(self.push(), 0)
        self.assertEqual(json.loads((self.work / 'push.json').read_text(encoding='utf-8'))['reason'], 'unchanged')

    def test_difference_classes_never_carry_values(self):
        old = json.dumps({'updated_at': '2026-11-01T15:46:24+00:00', 'n': 1}).encode()
        new = json.dumps({'updated_at': '2026-11-04T01:02:03+00:00', 'n': 1}).encode()
        self.assertEqual(publisher.classify('data/x.json', old, new)['class'], 'timestamp-only')
        changed = publisher.classify('data/x.json', old, json.dumps({'updated_at': 'x', 'n': 2}).encode())
        self.assertEqual(changed['class'], 'content')
        self.assertEqual(changed['json_pointers'], ['/n', '/updated_at'])
        allow = {'release_id': 'r', 'files': [{'path': 'a', 'sha256': 'x', 'bytes': 1, 'reviewer': 'one',
                                               'reviewed_at': '2026-11-01T00:00:00+00:00'}]}
        later = {'release_id': 'r', 'files': [{'path': 'a', 'sha256': 'x', 'bytes': 1, 'reviewer': 'two',
                                               'reviewed_at': '2026-11-04T00:00:00+00:00'}]}
        result = publisher.classify('.release-control/site-allowlist.json', json.dumps(allow).encode(), json.dumps(later).encode())
        self.assertEqual(result['class'], 'allowlist review stamps only')


if __name__ == '__main__':
    unittest.main()
