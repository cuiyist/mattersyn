"""Staging, commit and push mechanics of the GitHub site publisher, on local Git repositories."""
import io
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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


class LiveReverificationScopeTests(unittest.TestCase):
    def scope(self):
        return {'schema':'MatterSyn-live-reverification-scope/1', 'prior_source_commit':'a'*40,
                'prior_site_commit':'b'*40, 'prior_publisher_run':123,
                'prior_receipt_sha256':'c'*64, 'required_paths':['old.html'],
                'provenance':{'original_probe_count':8284, 'historical_cause':'unknown'}}

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw=json.dumps(value,indent=2).encode();path.write_bytes(raw);return raw

    def stage_fixture(self, root):
        source=root/'source';work=root/'work';dist=work/publisher.DIST
        for rel in ('old.html','new.css'):
            p=dist/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(rel.encode())
        scope=self.scope();raw=self.put(source/publisher.LIVE_REVERIFICATION_INPUT,scope)
        binding=publisher.carry_live_reverification_scope(source,work,{'old.html','new.css'},'b'*40)
        stage={'source_commit':'d'*40,'site_base_commit':'b'*40,'paper_routes':{},'material_routes':{},
               'files_added':[], 'files_changed':['new.css','.release-control/site-policy.json'],
               'live_reverification_scope':binding}
        self.put(work/'stage.json',stage);self.put(work/'push.json',{'pushed':True,'site_commit':'e'*40})
        return source,work,dist,stage,raw

    def test_optional_absent_input_preserves_normal_path(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);work=root/'work'
            self.assertIsNone(publisher.carry_live_reverification_scope(root/'source',work,{'new.css'},'b'*40))
            self.assertEqual(publisher.read_live_reverification_scope({'site_base_commit':'b'*40},work,{'new.css'}),([],None))
            self.assertFalse(work.exists())

    def test_carried_receipt_cannot_lose_its_stage_binding(self):
        with tempfile.TemporaryDirectory() as t:
            _,work,_,stage,_=self.stage_fixture(Path(t))
            del stage['live_reverification_scope']
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.read_live_reverification_scope(stage,work,{'old.html','new.css'})

    def test_exact_raw_scope_provenance_and_pin_are_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            source,work,dist,stage,raw=self.stage_fixture(Path(t))
            self.assertEqual((work/publisher.LIVE_REVERIFICATION_RECEIPT).read_bytes(),raw)
            paths,metadata=publisher.read_live_reverification_scope(stage,work,{'old.html','new.css'})
            self.assertEqual(paths,['old.html']);self.assertEqual(metadata['prior_publisher_run'],123)
            self.assertEqual(metadata['receipt_sha256'],publisher.hashlib.sha256(raw).hexdigest())
            self.assertEqual(json.loads(raw)['provenance']['historical_cause'],'unknown')

    def test_missing_duplicate_control_and_unbuilt_paths_fail_closed(self):
        for paths in [[],['old.html','old.html'],['../old.html'],['missing.html'],['.release-control/site-policy.json'],[None]]:
            scope=self.scope();scope['required_paths']=paths
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.validate_live_reverification_scope(scope,{'old.html','.release-control/site-policy.json'},'b'*40)

    def test_prior_identity_digest_schema_and_site_base_are_checked(self):
        for key,value in [('schema','wrong'),('prior_source_commit','bad'),('prior_site_commit','0'*40),
                          ('prior_publisher_run',True),('prior_receipt_sha256','bad')]:
            scope=self.scope();scope[key]=value
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.validate_live_reverification_scope(scope,{'old.html'},'b'*40)

    def test_carried_bytes_or_receipt_binding_cannot_change(self):
        with tempfile.TemporaryDirectory() as t:
            _,work,_,stage,_=self.stage_fixture(Path(t))
            receipt=work/publisher.LIVE_REVERIFICATION_RECEIPT;receipt.write_bytes(receipt.read_bytes()+b' ')
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.read_live_reverification_scope(stage,work,{'old.html','new.css'})
            altered=copy.deepcopy(stage);altered['live_reverification_scope']['receipt']='../other.json'
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.read_live_reverification_scope(altered,work,{'old.html','new.css'})

    def test_current_build_membership_is_rechecked_before_normal_verification(self):
        with tempfile.TemporaryDirectory() as t:
            _,work,_,stage,_=self.stage_fixture(Path(t))
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.read_live_reverification_scope(stage,work,{'new.css'})

    def test_verify_unions_prior_mandatory_and_current_changed_paths_once(self):
        with tempfile.TemporaryDirectory() as t:
            _,work,_,stage,_=self.stage_fixture(Path(t))
            result={'passed':True,'checked_files':2,'checked_changed_files':['new.css','old.html'],
                    'checked_paper_routes':[],'checked_material_routes':[],'mismatched_files':[]}
            args=SimpleNamespace(work=work,site_repo='o/r',site_url='https://example.test/site/',pages_minutes=1)
            with mock.patch.object(publisher,'wait_for_pages',return_value=(True,[(1,'success')])),mock.patch.object(publisher.rb,'verify_live',return_value=result)as verify,redirect_stdout(io.StringIO()):
                self.assertEqual(publisher.cmd_verify(args),0)
            self.assertEqual(verify.call_count,1)
            self.assertEqual(verify.call_args.kwargs['changed_paths'],['new.css','old.html'])
            self.assertEqual(verify.call_args.args[3:5],({},{}),'Existing binding scopes stay unchanged, including empty scopes')
            saved=json.loads((work/'receipts/live-verification.json').read_bytes())
            self.assertEqual(saved['reverification_scope']['required_files'],1)
            self.assertEqual(saved['reverification_scope']['checked_required_files'],1)
            self.assertEqual(saved['reverification_scope']['failed_required_paths'],[])

    def test_failed_prior_path_still_fails_and_keeps_receipt_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            _,work,_,_,_=self.stage_fixture(Path(t))
            result={'passed':False,'checked_files':1,'checked_changed_files':['new.css'],
                    'checked_paper_routes':[],'checked_material_routes':[],'mismatched_files':['old.html']}
            args=SimpleNamespace(work=work,site_repo='o/r',site_url='https://example.test/site/',pages_minutes=1)
            with mock.patch.object(publisher,'wait_for_pages',return_value=(True,[(1,'success')])),mock.patch.object(publisher.rb,'verify_live',return_value=result),redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                publisher.cmd_verify(args)
            saved=json.loads((work/'receipts/live-verification.json').read_bytes())
            self.assertFalse(saved['passed']);self.assertEqual(saved['reverification_scope']['checked_required_files'],0)
            self.assertEqual(saved['reverification_scope']['failed_required_paths'],['old.html'])
            self.assertEqual(saved['reverification_scope']['prior_receipt_sha256'],'c'*64)


if __name__ == '__main__':
    unittest.main()
