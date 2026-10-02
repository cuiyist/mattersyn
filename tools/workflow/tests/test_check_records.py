"""The advisory checker reads only exact frozen-package records."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_records


class FrozenPackageCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'records').mkdir()
        self.record = {'record_id': 'sample-1', 'lineage': {'source_group': 'paper-a'},
                       'materials': [], 'material_states': [], 'stocks': [],
                       'operations': [], 'products': [], 'measurements': [],
                       'structure_assets': [], 'material': {'formula': 'CdSe'}}
        raw = json.dumps(self.record).encode()
        (self.root / 'records/sample-1.json').write_bytes(raw)
        self.package = {'records': [{'record_id': 'sample-1',
                                     'path': 'records/sample-1.json',
                                     'sha256': hashlib.sha256(raw).hexdigest()}]}
        self.manifest = self.root / 'package.json'
        self.manifest.write_text(json.dumps(self.package), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_only_manifest_declared_records(self):
        (self.root / 'records/unreviewed-draft.json').write_text('{}')
        self.assertEqual(list(check_records.declared_package_records(self.manifest)),
                         [self.record])

    def test_rejects_stale_record_hash(self):
        (self.root / 'records/sample-1.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            list(check_records.declared_package_records(self.manifest))

    def test_rejects_path_traversal(self):
        self.package['records'][0]['path'] = '../outside.json'
        self.manifest.write_text(json.dumps(self.package), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            list(check_records.declared_package_records(self.manifest))

    def test_flags_are_advisory_questions(self):
        self.record['materials'] = [{'id': 'cd-salt', 'name': 'Cadmium chloride',
                                     'formula': 'CdCl2', 'role': 'precursor'}]
        flags = check_records.check_record(self.record)
        self.assertEqual(flags[0]['kind'], 'unused_material')
        self.assertEqual(flags[0]['severity'], 'check')

    def test_shell_layer_numeral_is_flagged_even_before_another_slash(self):
        for formula in ('CdSe/CdS4', 'CdSe/CdS2/ZnS2', 'CdSe/CdS3/ZnS',
                        'CdSe/ZnS/CdS3', 'CdSe/ZnS4', 'CdSe/CdS2/ZnS/CdS'):
            with self.subTest(formula=formula):
                self.record['material']['formula'] = formula
                self.assertIn('formula_layer_notation',
                              {f['kind'] for f in check_records.check_record(self.record)})


if __name__ == '__main__':
    unittest.main()
