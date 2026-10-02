import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from prepare_source_release import (BLUEPRINT, MANIFEST, PreparationError, apply_transaction,
                                    canonical, encoded, git, load_module, payload_binding, prepare, sha)
from check_project_manifest import ManifestError, check
from bind_source_allowlist import bind


def guard_module():
    candidate = os.environ.get('MATTERSYN_GUARD_MODULE')
    path = Path(candidate) if candidate else Path(__file__).resolve().parents[1] / 'mattersyn-release/public_release_guard.py'
    return load_module(path, 'source_release_test_guard')


class PrepareReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard = guard_module()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.name', 'Fixture')
        git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        git(self.root, 'config', 'core.autocrlf', 'false')
        self.write('README.md', b'Reviewed notes\n')
        self.write('recipe-atlas/data/record.json', b'{"amount": 1}\n')
        self.write('recipe-atlas/data/release-baseline-manifest.json', encoded({
            'schema_version': '1.0.0', 'dataset_version': 'fixture', 'record_count': 0,
            'group_count': 0, 'families': [], 'split_policy': 'fixture', 'records': []}))
        self.write('publication/public-release-policy.json', b'{}\n')
        self.write('publication/asset-rights-registry.json', b'{"assets": []}\n')
        self.write(BLUEPRINT, encoded({'schema': 'mattersyn-build-input-blueprint/1', 'input_files': []}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'Initial payload')
        rows = [self.row(n) for n in self.names()]
        self.write(MANIFEST, encoded({'schema_version': 'mattersyn-public-release-allowlist/1',
                                     'repo': 'mattersyn', 'source_commit': self.head(), 'files': rows}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'Initial closure')
        self.base = self.head()
        self.receipt = {'schema': 'mattersyn-reviewed-source-changes/1', 'base_commit': self.base, 'files': []}

    def names(self):
        return [n.decode() for n in git(self.root, 'ls-files', '-z').split(b'\0') if n]

    def head(self):
        return git(self.root, 'rev-parse', 'HEAD').decode().strip()

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def row(self, name):
        raw = (self.root / name).read_bytes()
        return {'path': name, 'sha256': sha(raw), 'bytes': len(raw), 'git_mode': '100644',
                'decision': 'allow', 'review_status': 'approved', 'reviewer': 'independent-fixture',
                'reviewed_at': '2026-09-26T00:00:00Z', 'content_class': 'authored_docs', 'source_refs': []}

    def config(self):
        return {'approval_status': 'approved', 'approved_by': 'fixture',
                'policy_sha256': sha((self.root / 'publication/public-release-policy.json').read_bytes()),
                'asset_rights_registry_sha256': sha((self.root / 'publication/asset-rights-registry.json').read_bytes()),
                'allowed_content_classes': ['authored_docs'],
                'path_rules': [{'rule_id': 'fixture-' + str(i), 'repo': 'mattersyn', 'path_glob': n,
                                'decision': 'allow', 'content_class': 'authored_docs', 'review_status': 'approved',
                                'reviewer': 'fixture', 'requires_source_refs': False} for i, n in enumerate(self.names())],
                'blob_approvals': [], 'exact_blob_approval_classes': [],
                'asset_rights_registry': {'schema_version': 'mattersyn-public-asset-rights/1', 'assets': [], 'snapshots': []}}

    def reviewed_edit(self, name='README.md', raw=b'New reviewed notes\n'):
        previous = json.loads(git(self.root, 'show', 'HEAD:' + MANIFEST))
        old = next((r for r in previous['files'] if r['path'] == name), None)
        self.write(name, raw)
        git(self.root, 'add', '--', name)
        self.receipt['files'].append({**self.row(name), 'before_sha256': old['sha256'] if old else None})

    def plan(self):
        return prepare(self.root, self.receipt, 'fixture-release', self.guard, self.config(), now='2026-09-26T01:00:00Z')

    def test_single_commit_and_clean_checker_and_runtime_export_binding(self):
        self.reviewed_edit()
        before_count = int(git(self.root, 'rev-list', '--count', 'HEAD'))
        controls, plan = self.plan()
        result = apply_transaction(self.root, controls, plan)
        self.assertTrue(result['commit_ready'])
        self.assertEqual(self.head(), self.base)  # preparer does not commit
        git(self.root, 'commit', '-qm', 'One reviewed release commit')
        self.assertEqual(int(git(self.root, 'rev-list', '--count', 'HEAD')), before_count + 1)
        self.assertEqual(check(self.root, pre_push=True)['status'], 'passed')
        output = Path(self.temp.name) / 'runtime.json'
        result = bind(self.root, output)
        self.assertEqual(result['source_commit'], self.head())
        self.assertEqual(result['prepared_from'], self.base)
        self.assertEqual(json.loads(output.read_bytes())['source_commit_role'], 'verified_runtime_release_commit')
        self.assertEqual(git(self.root, 'status', '--porcelain'), b'')
        manifest, report = self.guard.export_public_release(
            self.root, Path(self.temp.name) / 'public-stage', output, self.config(), 'mattersyn',
            Path(self.temp.name) / 'boundary-manifest.json', Path(self.temp.name) / 'boundary-report.json')
        self.assertEqual(manifest['source_commit'], self.head())
        self.assertEqual(report['status'], 'passed')

    def test_unreviewed_change_is_not_implicitly_approved(self):
        self.write('README.md', b'Unreviewed content\n')
        git(self.root, 'add', '.')
        with self.assertRaisesRegex(PreparationError, 'Missing exact changed-file review'):
            self.plan()

    def test_exact_review_hash_and_bytes_and_base_required(self):
        for field, value in [('sha256', '0' * 64), ('bytes', 123456), ('before_sha256', '0' * 64)]:
            self.receipt['files'] = []
            self.reviewed_edit()
            self.receipt['files'][0][field] = value
            with self.subTest(field=field), self.assertRaises(PreparationError):
                self.plan()

    def test_new_file_requires_exact_review_and_is_blueprint_bound(self):
        self.reviewed_edit('recipe-atlas/data/new.json', b'{"material": "CdSe"}\n')
        controls, _ = self.plan()
        inputs = json.loads(controls[BLUEPRINT])['input_files']
        self.assertIn('recipe-atlas/data/new.json', {r['path'] for r in inputs})

    def test_baseline_and_record_count_are_one_derived_transaction(self):
        self.reviewed_edit('recipe-atlas/data/records/example.json', b'{"record_id":"example"}\n')
        row = {'record_id': 'example', 'record_sha256': 'a' * 64,
               'eligibility': {'partial_protocol': {'eligible': False}}}
        generated = {'schema_version': '1.0.0', 'dataset_version': 'fixture',
                     'record_count': 1, 'group_count': 1, 'families': [],
                     'split_policy': 'fixture', 'records': [row]}
        with patch('prepare_source_release.generate_baseline', return_value=generated):
            controls, plan = self.plan()
        blueprint = json.loads(controls[BLUEPRINT])
        self.assertEqual(blueprint['record_count'], 1)
        self.assertEqual(json.loads(controls['recipe-atlas/data/release-baseline-manifest.json']), generated)
        baseline_input = next(x for x in blueprint['input_files']
                              if x['path'] == 'recipe-atlas/data/release-baseline-manifest.json')
        self.assertEqual(baseline_input['sha256'], sha(controls[baseline_input['path']]))
        self.assertEqual({x['path'] for x in plan['controls']},
                         {BLUEPRINT, MANIFEST, baseline_input['path']})

    def test_manual_baseline_edit_is_rejected(self):
        baseline = 'recipe-atlas/data/release-baseline-manifest.json'
        self.write(baseline, encoded({'record_count': 999, 'records': []}))
        git(self.root, 'add', '--', baseline)
        with self.assertRaisesRegex(PreparationError, 'Dataset baseline is generated'):
            self.plan()

    def test_unstaged_edit_and_untracked_draft_rejected(self):
        self.write('README.md', b'Unstaged\n')
        with self.assertRaisesRegex(PreparationError, 'unstaged'):
            self.plan()
        git(self.root, 'restore', '--worktree', 'README.md')
        self.write('draft.md', b'private candidate\n')
        with self.assertRaisesRegex(PreparationError, 'Untracked'):
            self.plan()

    def test_blocked_file_cannot_be_approved_by_review_receipt(self):
        self.reviewed_edit('paper.pdf', b'Synthetic document')
        with self.assertRaisesRegex(PreparationError, 'Boundary rejected'):
            self.plan()

    def test_secret_fails_even_with_exact_review(self):
        # Synthetic shape only; not a real credential.
        self.reviewed_edit('README.md', ('token ' + 'ghp_' + 'A' * 40).encode())
        with self.assertRaisesRegex(PreparationError, 'Boundary rejected'):
            self.plan()

    def test_deleted_file_needs_review(self):
        name = 'recipe-atlas/data/record.json'
        old = self.row(name)
        git(self.root, 'rm', '--', name)
        with self.assertRaisesRegex(PreparationError, 'deletion review'):
            self.plan()
        self.receipt['files'].append({**old, 'decision': 'delete', 'before_sha256': old['sha256']})
        controls, _ = self.plan()
        self.assertNotIn(name, {r['path'] for r in json.loads(controls[MANIFEST])['files']})

    def test_plan_is_deterministic_and_read_only(self):
        self.reviewed_edit()
        before = git(self.root, 'write-tree')
        a, plan_a = self.plan()
        b, plan_b = self.plan()
        self.assertEqual(a, b)
        self.assertEqual(plan_a, plan_b)
        self.assertEqual(before, git(self.root, 'write-tree'))

    def test_raced_index_rejects_without_control_mutation(self):
        controls, plan = self.plan()
        originals = {n: (self.root / n).read_bytes() for n in controls}
        self.reviewed_edit()
        with self.assertRaisesRegex(PreparationError, 'HEAD or index changed'):
            apply_transaction(self.root, controls, plan)
        self.assertEqual(originals, {n: (self.root / n).read_bytes() for n in controls})

    def test_existing_index_lock_is_not_removed(self):
        controls, plan = self.plan()
        lock = self.root / '.git/index.lock'
        lock.write_bytes(b'other writer')
        with self.assertRaises(FileExistsError):
            apply_transaction(self.root, controls, plan)
        self.assertEqual(lock.read_bytes(), b'other writer')

    def test_tampered_binding_is_rejected(self):
        controls, plan = self.plan()
        apply_transaction(self.root, controls, plan)
        data = json.loads((self.root / MANIFEST).read_bytes())
        data['source_payload_binding']['sha256'] = '0' * 64
        self.write(MANIFEST, encoded(data))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'Bad binding')
        with self.assertRaisesRegex(ManifestError, 'content binding mismatch'):
            check(self.root, pre_push=True)

    def test_manifest_binding_includes_mode_and_identity(self):
        rows = [self.row('README.md')]
        original = payload_binding(rows)
        changed = copy.deepcopy(rows)
        changed[0]['git_mode'] = '100755'
        self.assertNotEqual(original, payload_binding(changed))

    def test_tampered_generated_controls_rejected_before_mutation(self):
        controls, plan = self.plan()
        controls[BLUEPRINT] = b'{}\n'
        before = git(self.root, 'write-tree')
        with self.assertRaisesRegex(PreparationError, 'control identities changed'):
            apply_transaction(self.root, controls, plan)
        self.assertEqual(before, git(self.root, 'write-tree'))

    def test_failed_second_replace_rolls_back_controls_and_index(self):
        controls, plan = self.plan()
        originals = {n: (self.root / n).read_bytes() for n in controls}
        index_before = (self.root / '.git/index').read_bytes()
        replace = os.replace
        calls = []
        def fail_second(src, dst):
            calls.append(dst)
            if len(calls) == 2:
                raise OSError('Synthetic interrupted transaction')
            return replace(src, dst)
        with patch('prepare_source_release.os.replace', side_effect=fail_second), self.assertRaises(OSError):
            apply_transaction(self.root, controls, plan)
        self.assertEqual(originals, {n: (self.root / n).read_bytes() for n in controls})
        self.assertEqual(index_before, (self.root / '.git/index').read_bytes())
        self.assertFalse((self.root / '.git/index.lock').exists())
        self.assertFalse(list((self.root / 'publication').glob('.mattersyn-control-*')))

    def test_blueprint_authorization_fields_are_not_blanket_approved(self):
        before = json.loads((self.root / BLUEPRINT).read_bytes())
        after = {**before, 'withheld_input_count': 1}
        self.write(BLUEPRINT, encoded(after))
        git(self.root, 'add', '--', BLUEPRINT)
        with self.assertRaisesRegex(PreparationError, 'authorization metadata requires exact'):
            self.plan()
        meta = lambda d: {k: v for k, v in d.items() if k not in {'input_files', 'release_id', 'updated_at'}}
        self.receipt['blueprint_metadata_review'] = {
            'before_sha256': sha(canonical(meta(before))), 'sha256': sha(canonical(meta(after))),
            'decision': 'allow', 'review_status': 'approved',
            'reviewer': 'fixture-independent-release-reviewer', 'reviewed_at': '2026-09-26T01:00:00Z'}
        controls, _ = self.plan()
        self.assertEqual(json.loads(controls[BLUEPRINT])['withheld_input_count'], 1)


if __name__ == '__main__':
    unittest.main()
