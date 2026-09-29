"""Synthetic byte-placement tests; these do not establish scientific validity."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest

HERE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('evidence_test_merger', HERE / 'merger.py')
merger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merger)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class EvidenceCSVTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'checkout'
        self.payload = self.root / 'payload'
        self.output = self.root / 'output'
        self.checkout.mkdir()
        self.payload.mkdir()
        self.base = self.checkout / 'base.json'
        self.base.write_bytes(b'{}\n')
        self.csv = b'Sample,Size (nm)\r\nsynthetic-a,5\r\n'
        self.data = 'recipe-atlas/data/paper-evidence/synthetic-paper/table-1.csv'
        self.static = 'recipe-atlas/static/data/paper-evidence/synthetic-paper/table-1.csv'
        self.review_path = 'recipe-atlas/data/paper-reviews/synthetic-paper.json'
        self.review = {'paper_id': 'synthetic-paper', 'tables': [{
            'source_data_path': self.data.removeprefix('recipe-atlas/'),
            'source_data_sha256': digest(self.csv),
        }]}

    def mapping(self, **options):
        result = {self.review_path: json.dumps(self.review).encode()}
        if options.get('static', True):
            result[self.static] = self.csv
        if options.get('data', False):
            result[self.data] = self.csv
        return result

    def merge(self, created):
        entries = []
        for target, raw in created.items():
            source = target.removeprefix('recipe-atlas/')
            path = self.payload / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            entries.append({'source': source, 'target': target,
                            'sha256': digest(raw), 'bytes': len(raw)})
        contract = {'schema_version': 'mattersyn-declarative-additive-merge/1',
                    'base_commit': None, 'base_files': {'base.json': digest(self.base.read_bytes())},
                    'create_files': entries, 'json_operations': []}
        importer = Path(os.environ.get('MATTERSYN_IMPORTER_PATH', HERE / 'importer.py'))
        return merger.merge_plan(self.checkout, self.payload, contract, self.output, importer)

    def reject(self, created):
        with self.assertRaises(merger.MergeRejected):
            merger.place_declared_evidence_csvs(created)

    def test_static_bytes_become_explicit_source_create_only_without_input_mutation(self):
        created = self.mapping()
        before = copy.deepcopy(created)
        result = self.merge(created)
        self.assertEqual(created, before)
        self.assertEqual(self.base.read_bytes(), b'{}\n')
        for relative in (self.static, self.data):
            self.assertEqual((self.output / 'overlay' / relative).read_bytes(), self.csv)
            row = next(row for row in result['package_files'] if row['path'] == relative)
            self.assertEqual(row['mode'], 'create_only')
            self.assertEqual((row['sha256'], row['bytes']), (digest(self.csv), len(self.csv)))
            self.assertFalse((self.checkout / relative).exists())
        self.assertEqual(result['evidence_csv_placements'], [{
            'declaration': self.review_path, 'source': self.static, 'target': self.data,
            'sha256': digest(self.csv), 'bytes': len(self.csv)}])

    def test_already_declared_source_csv_is_not_duplicated(self):
        original = self.mapping(data=True)
        result, placements = merger.place_declared_evidence_csvs(original)
        self.assertEqual(result, original)
        self.assertEqual(placements, [])

    def test_source_only_declaration_is_valid_without_inventing_static_delivery(self):
        original = self.mapping(static=False, data=True)
        result, placements = merger.place_declared_evidence_csvs(original)
        self.assertEqual(result, original)
        self.assertEqual(placements, [])

    def test_duplicate_table_references_share_one_copy(self):
        self.review['tables'].append(copy.deepcopy(self.review['tables'][0]))
        result, placements = merger.place_declared_evidence_csvs(self.mapping())
        self.assertEqual(len(placements), 1)
        self.assertEqual(result[self.data], self.csv)

    def test_unrelated_payload_has_no_effect(self):
        original = {'recipe-atlas/static/assets/card.svg': b'<svg/>'}
        self.assertEqual(merger.place_declared_evidence_csvs(original), (original, []))

    def test_paths_reject_foreign_traversal_nested_absolute_non_csv_and_suffixes(self):
        for relative in [
            'data/paper-evidence/other-paper/table-1.csv',
            'data/paper-evidence/synthetic-paper/../table-1.csv',
            'data/paper-evidence/synthetic-paper/subdir/table-1.csv',
            '/data/paper-evidence/synthetic-paper/table-1.csv',
            'data/paper-evidence/synthetic-paper/table-1.json',
            'data/paper-evidence/synthetic-paper/table-1.csv?query',
            'data/paper-evidence/synthetic-paper/table-1.csv#fragment',
            'data/paper-evidence/synthetic-paper/table-1.csv:stream',
            'data/paper-evidence/synthetic-paper/.csv',
            'data/paper-evidence/synthetic-paper/table-1.CSV',
        ]:
            with self.subTest(relative=relative):
                self.review['tables'][0]['source_data_path'] = relative
                self.reject(self.mapping())
        self.review['tables'][0]['source_data_path'] = self.data.replace('/', chr(92))
        self.reject(self.mapping())

    def test_paper_identity_must_match_review_filename(self):
        self.review['paper_id'] = 'another-paper'
        self.reject(self.mapping())

    def test_missing_or_wrong_hash_is_rejected(self):
        for bad in [None, '', 'a' * 64, digest(self.csv).upper()]:
            with self.subTest(hash=bad):
                self.review['tables'][0]['source_data_sha256'] = bad
                self.reject(self.mapping())
        del self.review['tables'][0]['source_data_sha256']
        self.reject(self.mapping())

    def test_missing_csv_is_rejected(self):
        self.reject(self.mapping(static=False))

    def test_conflicting_static_and_source_bytes_are_rejected(self):
        created = self.mapping(data=True)
        created[self.data] = b'different\n'
        self.reject(created)
        created = self.mapping(data=True)
        created[self.static] = b'different\n'
        self.reject(created)

    def test_case_collision_is_rejected(self):
        for path in (self.data, self.static):
            with self.subTest(path=path):
                created = self.mapping()
                created[path.replace('table-1', 'TABLE-1')] = self.csv
                self.reject(created)

    def test_conflicting_repeated_declaration_is_rejected(self):
        self.review['tables'].append({**self.review['tables'][0], 'source_data_sha256': 'b' * 64})
        self.reject(self.mapping())

    def test_existing_source_target_rejected_before_any_output(self):
        existing = self.checkout / self.data
        existing.parent.mkdir(parents=True)
        existing.write_bytes(self.csv)
        with self.assertRaisesRegex(merger.MergeRejected, 'Create-only target already exists'):
            self.merge(self.mapping())
        self.assertEqual(existing.read_bytes(), self.csv)
        self.assertFalse(self.output.exists())

    def test_unlisted_static_file_cannot_be_used(self):
        path = self.payload / self.static.removeprefix('recipe-atlas/')
        path.parent.mkdir(parents=True)
        path.write_bytes(self.csv)
        with self.assertRaisesRegex(merger.MergeRejected, 'Payload file set differs'):
            self.merge(self.mapping(static=False))
        self.assertFalse(self.output.exists())

    def test_bad_declaration_leaves_no_output(self):
        self.review['tables'][0]['source_data_sha256'] = 'b' * 64
        with self.assertRaises(merger.MergeRejected):
            self.merge(self.mapping())
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
