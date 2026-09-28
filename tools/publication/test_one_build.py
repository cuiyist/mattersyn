"""Offline temporary-fixture tests; no production build or approval creation."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import one_build as p

SOURCE = Path(os.environ.get('MATTERSYN_SOURCE_ROOT',
    str(Path(__file__).resolve().parents[2])))


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else (json.dumps(value, indent=2) + '\n').encode())


class PrimitiveTests(unittest.TestCase):
    def test_hostile_paths_and_duplicate_rows(self):
        for name in ('../x', '/x', 'a//x', 'a/./x', 'a\\x', 'C:x', 'a.', 'con.txt', 'x\0y', 'e\u0301.txt'):
            with self.subTest(name=name), self.assertRaises(p.Rejected):
                p.path_name(name)
        r = {'path': 'X.json', 'sha256': 'a' * 64, 'bytes': 1}
        for rows in ([r, r], [r, {**r, 'path': 'x.json'}], [{**r, 'bytes': True}]):
            with self.assertRaises(p.Rejected):
                p.rows_map(rows)

    def test_duplicate_json_and_nonfinite_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(p.Rejected):
                p.loads(raw)

    def test_symlink_and_reparse_are_rejected_without_following(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'x'; target.write_text('a')
            original = Path.lstat
            def reparse(path):
                s = original(path)
                if path == target:
                    class Fake:
                        st_mode = s.st_mode
                        st_file_attributes = 0x400
                    return Fake()
                return s
            with patch.object(Path, 'lstat', reparse), self.assertRaisesRegex(p.Rejected, 'reparse'):
                p.stable_bytes(target)

    def test_same_length_race_rejected_even_with_restored_mtime(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'x'; file.write_bytes(b'one')
            original = Path.open
            class ChangedRead:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def fileno(self): return self.stream.fileno()
                def seek(self, *args): return self.stream.seek(*args)
                def read(self):
                    value = self.stream.read(); before = file.stat()
                    with original(file, 'wb') as out: out.write(b'two')
                    os.utime(file, ns=(before.st_atime_ns, before.st_mtime_ns))
                    return value
            with patch.object(Path, 'open', lambda path, *a, **k: ChangedRead(original(path, *a, **k))):
                with self.assertRaisesRegex(p.Rejected, 'changed_during_read'):
                    p.stable_bytes(file)

    def test_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            a = Path(temp) / 'a'; a.write_bytes(b'x'); b = Path(temp) / 'b'
            os.link(a, b)
            with self.assertRaisesRegex(p.Rejected, 'unique_regular'):
                p.stable_bytes(a)


class TransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.top = Path(cls.temp.name).resolve()
        cls.source = cls.top / 'source'; cls.source.mkdir()
        cls.candidate = cls.top / 'candidate'
        cls.snapshot = cls.top / 'snapshot.json'
        cls.contract = cls.top / 'contract.json'
        for name in p.CODE:
            raw = (SOURCE / name).read_bytes()
            if name == p.TRANSFORM:
                raw = b'# Synthetic fixture transformation is intentionally a no-op.\n'
            put(cls.source / name, raw)
        for scope in p.COPY_DIRS:
            (cls.source / scope).mkdir(parents=True, exist_ok=True)
        put(cls.source / 'recipe-atlas/templates/template.txt', b'Fixture')
        put(cls.source / 'README.md', b'Synthetic offline fixture\n')
        put(cls.source / '.gitignore', b'*.ignored\n')
        put(cls.source / 'recipe-atlas/static/index.html', b'<p>Offline fixture</p>\n')
        put(cls.source / 'recipe-atlas/data/release-baseline-manifest.json', {'records': []})
        for name in p.BUILDERS:
            put(cls.source / ('recipe-atlas/scripts/' + name), b'')
        put(cls.source / 'recipe-atlas/scripts/build_dataset.py',
            b"from pathlib import Path\np=Path('dist/data/dataset-manifest.json');p.parent.mkdir(exist_ok=True);p.write_text('{\"records\":[]}')\n")
        put(cls.source / 'recipe-atlas/scripts/generate_release_metadata.py',
            b"def generate(root,snapshot):\n return {'source_commit':snapshot['source_commit'],'release_id':snapshot['release_id']}\n")
        for name in ('check_site.py', 'check_atlas.py'):
            put(cls.source / ('recipe-atlas/scripts/' + name), b"print('passed fixture')\n")
        put(cls.source / 'recipe-atlas/scripts/check_quality.py',
            b"print('{\"passed\":true,\"counts\":{\"checks\":1},\"errors\":[],\"warnings\":[]}')\n")
        put(cls.source / 'recipe-atlas/tests/test_fixture.py',
            b'import unittest\nclass Fixture(unittest.TestCase):\n def test_one(self): self.assertEqual(1,1)\n')
        registry = {'schema_version': 'mattersyn-public-asset-rights/1', 'assets': [], 'snapshots': []}
        put(cls.source / p.REGISTRY, registry)
        policy = {'schema_version': 'mattersyn-public-projection-policy/1',
                  'approval_status': 'approved', 'approved_by': 'synthetic-fixture',
                  'asset_rights_registry_sha256': p.sha(cls.source / p.REGISTRY),
                  'allowed_content_classes': ['site_data'], 'exact_blob_approval_classes': [],
                  'path_rules': [{'rule_id': 'fixture', 'repo': 'mattersyn-site', 'path_glob': '*',
                                  'decision': 'allow', 'content_class': 'site_data',
                                  'review_status': 'approved', 'reviewer': 'synthetic-fixture', 'requires_source_refs': False}]}
        put(cls.source / p.POLICY, policy)
        subprocess.run(['git', 'init', '-q', str(cls.source)], check=True)
        for key, value in [('user.name', 'Fixture'), ('user.email', 'fixture@example.invalid'), ('core.autocrlf', 'false')]:
            p.git(cls.source, 'config', key, value)
        # Real complete source closure is always independently captured by wrapper.
        blueprint = {'schema': 'mattersyn-build-input-blueprint/1', 'release_id': 'synthetic-fixture',
                     'updated_at': '2026-01-01T00:00:00Z', 'input_files': p.inventory(cls.source / 'recipe-atlas/static')}
        blueprint['input_files'][0]['path'] = 'recipe-atlas/static/index.html'
        put(cls.source / 'publication/build-inputs.json', blueprint)
        p.git(cls.source, 'add', '.'); p.git(cls.source, 'commit', '-qm', 'Synthetic fixture')
        cls.head = p.git(cls.source, 'rev-parse', 'HEAD').decode().strip()
        snapshot = {k: v for k, v in blueprint.items() if k not in ('schema', 'note')}
        snapshot.update(schema='mattersyn-release-snapshot/1', source_commit=cls.head,
                        blueprint_sha256=p.sha(cls.source / 'publication/build-inputs.json'))
        put(cls.snapshot, snapshot)
        put(cls.contract, {'schema': 'mattersyn-one-build-contract/1', 'source_commit': cls.head,
                           'snapshot_sha256': p.sha(cls.snapshot), 'expected_tests': 1,
                           'code_sha256': {n: p.sha(cls.source / n) for n in p.CODE}})
        cls.seal_pin = p.build(cls.source, cls.snapshot, cls.candidate, cls.contract, p.sha(cls.contract))
        cls.manifest = p.read(cls.candidate / 'candidate-manifest.json')
        cls.review_path = cls.top / 'review.json'
        cls.review = cls.make_review()
        put(cls.review_path, cls.review)
        cls.originals = {file: file.read_bytes() for root in [cls.source, cls.candidate, cls.top]
                         for file in root.glob('*') if file.is_file()}
        for root in (cls.source, cls.candidate):
            cls.originals.update({file: file.read_bytes() for file in root.rglob('*')
                                  if file.is_file() and '.git' not in file.parts})

    @classmethod
    def make_review(cls):
        c = cls.candidate / 'candidate-manifest.json'
        for name in ('windows', 'ubuntu'):
            put(cls.top / (name + '.json'), c.read_bytes())
        put(cls.top / 'science.json', {'status': 'SYNTHETIC_TEST_ONLY'})
        put(cls.top / 'browser.json', {'status': 'SYNTHETIC_TEST_ONLY'})
        put(cls.top / 'ci.json', [{'repo': 'mattersyn', 'head_sha': cls.head, 'status': 'completed', 'conclusion': 'success',
                                 'jobs': [{'name': n, 'status': 'completed', 'conclusion': 'success', 'failed_steps': []}
                                          for n in ('validate (windows-latest)', 'validate (ubuntu-latest)', 'compare-artifacts')]}])
        put(cls.top / 'source-boundary.json', {'source_commit': cls.head, 'status': 'passed', 'file_count': 1,
              'policy_sha256': p.sha(cls.source / p.POLICY), 'asset_rights_registry_sha256': p.sha(cls.source / p.REGISTRY)})
        put(cls.top / 'source-report.json', {'schema_version': 'mattersyn-public-boundary-report/1', 'repo': 'mattersyn',
              'status': 'passed', 'checked_files': 1, 'passed_files': 1, 'failure_count': 0})
        entries = [{**r, 'repo': 'mattersyn-site', 'decision': 'allow', 'review_status': 'approved',
                    'reviewer': 'synthetic-fixture', 'reviewed_at': '2026-01-01T00:00:00Z',
                    'content_class': 'site_data', 'source_refs': []} for r in cls.manifest['files']]
        put(cls.top / 'allowlist.json', {'schema_version': 'mattersyn-public-release-allowlist/1', 'repo': 'mattersyn-site',
             'source_commit': cls.head, 'release_id': 'synthetic-fixture', 'policy_sha256': p.sha(cls.source / p.POLICY),
             'asset_rights_registry_sha256': p.sha(cls.source / p.REGISTRY), 'files': entries})
        return {'schema': 'mattersyn-one-build-promotion-review/1', 'status': 'REVIEWED_PENDING_FRESH_BOUNDARY',
                'source_commit': cls.head, 'candidate_manifest_sha256': p.sha(c), 'build_seal_sha256': cls.seal_pin['sha256'],
                'science_receipts': [p.pin(cls.top / 'science.json')], 'browser_receipts': [p.pin(cls.top / 'browser.json')],
                'browser_artifact_files': cls.manifest['files'], 'source_ci': p.pin(cls.top / 'ci.json'),
                'ci_manifests': {'windows-latest': p.pin(cls.top / 'windows.json'), 'ubuntu-latest': p.pin(cls.top / 'ubuntu.json')},
                'source_boundary_manifest': p.pin(cls.top / 'source-boundary.json'),
                'source_boundary_report': p.pin(cls.top / 'source-report.json'), 'allowlist': p.pin(cls.top / 'allowlist.json')}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def tearDown(self):
        for path, raw in self.originals.items():
            if not path.exists() or path.read_bytes() != raw:
                path.write_bytes(raw)

    def promote(self, review=None):
        if review is not None:
            put(self.review_path, review)
        out = self.top / self.id().split('.')[-1]
        return p.promote(self.source, self.candidate, self.seal_pin['sha256'], out, self.review_path, p.sha(self.review_path))

    def test_one_full_build_then_fresh_real_boundary_no_second_build(self):
        before = p.sha(self.candidate / 'candidate-manifest.json')
        real_execute = p.execute
        with patch.object(p, 'execute', wraps=real_execute) as run:
            result = self.promote()
        self.assertEqual(run.call_count, 1)
        self.assertIn('gate.py', run.call_args.args[0][1])
        receipt = p.read(result['path'])
        self.assertEqual(receipt['new_local_builds'], 0)
        self.assertFalse(receipt['published'])
        self.assertEqual(receipt['publication_credit'], 0)
        self.assertEqual(receipt['files'], self.manifest['files'])
        self.assertEqual(p.sha(self.candidate / 'candidate-manifest.json'), before)

    def test_input_drift_even_when_git_assume_unchanged(self):
        file = self.source / 'README.md'; p.git(self.source, 'update-index', '--assume-unchanged', 'README.md')
        try:
            file.write_bytes(b'new bytes')
            with self.assertRaisesRegex(p.Rejected, 'working_bytes'):
                self.promote()
        finally:
            p.git(self.source, 'update-index', '--no-assume-unchanged', 'README.md')

    def test_extra_ignored_input_rejected(self):
        file = self.source / 'recipe-atlas/static/new.ignored'; file.write_bytes(b'x')
        try:
            with self.assertRaisesRegex(p.Rejected, 'ignored_build_input'):
                self.promote()
        finally: file.unlink()

    def test_artifact_same_size_mtime_restored_rejected(self):
        file = self.candidate / 'project/recipe-atlas/dist/index.html'; st = file.stat()
        file.write_bytes(file.read_bytes().replace(b'Offline', b'Changed'))
        os.utime(file, ns=(st.st_atime_ns, st.st_mtime_ns))
        with self.assertRaisesRegex(p.Rejected, 'inventory_drift'): self.promote()

    def test_candidate_manifest_log_seal_and_contract_drift_rejected(self):
        for file in [self.candidate / 'candidate-manifest.json', self.candidate / 'build-log.json',
                     self.candidate / 'build-seal.private.json', self.contract]:
            original = file.read_bytes()
            try:
                file.write_bytes(original + b' ')
                with self.subTest(path=file.name), self.assertRaises(p.Rejected): self.promote()
            finally: file.write_bytes(original)

    def test_missing_extra_artifact_rejected(self):
        file = self.candidate / 'project/recipe-atlas/dist/index.html'; raw = file.read_bytes(); file.unlink()
        try:
            with self.assertRaises(p.Rejected): self.promote()
        finally: file.write_bytes(raw)
        extra = file.parent / 'extra.txt'; extra.write_bytes(b'x')
        try:
            with self.assertRaises(p.Rejected): self.promote()
        finally: extra.unlink()

    def test_science_browser_receipt_drift_rejected(self):
        for name in ('science.json', 'browser.json'):
            file = self.top / name; original = file.read_bytes(); file.write_bytes(original + b' ')
            try:
                with self.assertRaisesRegex(p.Rejected, 'pin_drift'): self.promote()
            finally: file.write_bytes(original)

    def test_rights_policy_and_runtime_drift_rejected(self):
        for name in (p.POLICY, p.REGISTRY):
            file = self.source / name; raw = file.read_bytes(); file.write_bytes(raw + b' ')
            try:
                with self.assertRaises(p.Rejected): self.promote()
            finally: file.write_bytes(raw)
        with patch.object(p, 'runtime_state', return_value={}), self.assertRaisesRegex(p.Rejected, 'runtime_drift'):
            self.promote()

    def test_wrong_head_and_dirty_index_rejected(self):
        with self.assertRaisesRegex(p.Rejected, 'head_drift'):
            p.source_state(self.source, '0' * 40)
        file = self.source / 'README.md'; file.write_bytes(b'changed'); p.git(self.source, 'add', 'README.md')
        try:
            with self.assertRaisesRegex(p.Rejected, 'dirty_source'): self.promote()
        finally: p.git(self.source, 'reset', '-q', 'HEAD', '--', 'README.md')

    def test_build_receipts_require_all_stages_full_discovery_and_quality(self):
        path = self.candidate / 'build-log.json'; original = p.read(path)
        variants = [original[:-1], [original[1], original[0], *original[2:]]]
        failed = copy.deepcopy(original); failed[3]['returncode'] = 1; variants.append(failed)
        tests = copy.deepcopy(original); tests[9]['stderr'] = 'Ran 0 tests in 0.001s\n\nOK\n'; variants.append(tests)
        skipped = copy.deepcopy(original); skipped[9]['stderr'] = 'Ran 1 test in 0.001s\n\nOK (skipped=1)\n'; variants.append(skipped)
        quality = copy.deepcopy(original); quality[-1]['stdout'] = '{"passed":false}'; variants.append(quality)
        for value in variants:
            put(path, value)
            with self.assertRaises(p.Rejected): p.check_log(self.source, self.candidate, 1)

    def test_incomplete_or_wrong_head_ci_and_mismatched_manifest_rejected(self):
        review = copy.deepcopy(self.review)
        ci = p.read(self.top / 'ci.json'); ci[0]['head_sha'] = '0' * 40; put(self.top / 'ci.json', ci)
        review['source_ci'] = p.pin(self.top / 'ci.json')
        with self.assertRaisesRegex(p.Rejected, 'exact_head_ci'): self.promote(review)
        ci[0]['head_sha'] = self.head; ci[0]['jobs'][0]['conclusion'] = 'failure'; put(self.top / 'ci.json', ci)
        review['source_ci'] = p.pin(self.top / 'ci.json')
        with self.assertRaisesRegex(p.Rejected, 'required_job'): self.promote(review)
        put(self.top / 'ci.json', self.originals[self.top / 'ci.json'])
        review = copy.deepcopy(self.review)
        remote = copy.deepcopy(self.manifest); remote['files'][0]['sha256'] = 'f' * 64
        put(self.top / 'windows.json', remote); review['ci_manifests']['windows-latest'] = p.pin(self.top / 'windows.json')
        with self.assertRaisesRegex(p.Rejected, 'ci_artifact_not_identical'): self.promote(review)

    def test_browser_file_binding_and_source_export_failure_rejected(self):
        review = copy.deepcopy(self.review); review['browser_artifact_files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(p.Rejected, 'browser_artifact_drift'): self.promote(review)
        report = p.read(self.top / 'source-report.json'); report['failure_count'] = 1
        put(self.top / 'source-report.json', report)
        review = copy.deepcopy(self.review); review['source_boundary_report'] = p.pin(self.top / 'source-report.json')
        with self.assertRaisesRegex(p.Rejected, 'boundary_failed'): self.promote(review)

    def test_actual_boundary_rejects_bad_allowlist_and_emits_no_promotion(self):
        allowlist = p.read(self.top / 'allowlist.json'); allowlist['files'][0]['sha256'] = '0' * 64
        put(self.top / 'allowlist.json', allowlist)
        review = copy.deepcopy(self.review); review['allowlist'] = p.pin(self.top / 'allowlist.json')
        with self.assertRaisesRegex(p.Rejected, 'fresh_boundary_command_failed'): self.promote(review)
        self.assertFalse((self.top / self.id().split('.')[-1] / 'promotion-receipt.private.json').exists())

    def test_race_after_real_boundary_rejected(self):
        original = p.execute
        def mutate(command, cwd):
            result = original(command, cwd)
            (Path(cwd) / 'dist/index.html').write_bytes(b'Changed after scan')
            return result
        with patch.object(p, 'execute', mutate), self.assertRaisesRegex(p.Rejected, 'post_boundary_artifact_drift'):
            self.promote()

    def test_output_must_be_disjoint_and_new(self):
        for out in (self.source / 'nested', self.candidate / 'nested', self.candidate):
            with self.assertRaises(p.Rejected):
                p.disjoint_new(out, [self.source, self.candidate])

    def test_snapshot_drift_rejected(self):
        self.snapshot.write_bytes(self.snapshot.read_bytes() + b' ')
        with self.assertRaisesRegex(p.Rejected, 'pin_drift'): self.promote()

    def test_simultaneous_manifest_and_artifact_rewrite_still_rejected(self):
        f = self.candidate / 'project/recipe-atlas/dist/index.html'; f.write_bytes(b'Edited')
        manifest = p.read(self.candidate / 'candidate-manifest.json')
        manifest['files'] = p.inventory(f.parent)
        put(self.candidate / 'candidate-manifest.json', manifest)
        with self.assertRaisesRegex(p.Rejected, 'pin_drift'): self.promote()

    def test_copy_source_changed_during_transfer_rejected(self):
        original = p.copy_exact
        def changed(origin, destination, rows):
            (Path(origin) / 'index.html').write_bytes(b'Changed before transfer')
            return original(origin, destination, rows)
        with patch.object(p, 'copy_exact', changed), self.assertRaisesRegex(p.Rejected, 'copy_input_drift'):
            self.promote()

    def test_review_receipt_changed_during_fresh_gate_rejected(self):
        original = p.execute
        def changed(command, cwd):
            result = original(command, cwd)
            self.review_path.write_bytes(self.review_path.read_bytes() + b' ')
            return result
        with patch.object(p, 'execute', changed), self.assertRaisesRegex(p.Rejected, 'pin_drift'):
            self.promote()

    def test_policy_changed_during_fresh_gate_rejected(self):
        original = p.execute
        def changed(command, cwd):
            result = original(command, cwd)
            path = self.source / p.POLICY; path.write_bytes(path.read_bytes() + b' ')
            return result
        with patch.object(p, 'execute', changed), self.assertRaises(p.Rejected): self.promote()

    def test_actual_privacy_guard_rejects_unpublished_source_text(self):
        # Independently invoke real gate on a synthetic exact-allowlisted secret
        # field; no fabricated seal can turn private source text into approval.
        stage = self.top / 'private-text-fixture'; stage.mkdir()
        raw = b'{"source_excerpt":"Synthetic private source quotation"}'
        put(stage / 'index.html', b'<p>Fixture</p>'); put(stage / 'data.json', raw)
        al = p.read(self.top / 'allowlist.json')
        template = al['files'][0]
        al['files'] = [{**template, **r} for r in p.inventory(stage)]
        ap = self.top / 'private-text-allowlist.json'; put(ap, al)
        run = p.execute([__import__('sys').executable, str(self.source / p.GATE), '--root', str(stage),
                         '--policy', str(self.source / p.POLICY), '--registry', str(self.source / p.REGISTRY),
                         '--allowlist', str(ap), '--repo', 'mattersyn-site',
                         '--manifest-out', str(self.top / 'private-text-manifest.json'),
                         '--report-out', str(self.top / 'private-text-report.json')], self.top)
        self.assertNotEqual(run['returncode'], 0)
        self.assertIn('staged_content_requires_sanitization',
                      [f['reason_code'] for f in p.read(self.top / 'private-text-report.json')['failures']])


if __name__ == '__main__':
    unittest.main()
