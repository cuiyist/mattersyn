"""N display-only asset attribution; exactly two established public records."""
import copy
import hashlib
import html
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_dataset import render_record, structure_asset_reader_description


class AssetDescriptionBrandTests(unittest.TestCase):
    def test_only_leading_current_authored_brand_is_projected_without_mutation(self):
        asset = {'description': 'MatterSyn-authored diagram; no measured coordinates.',
                 'url': 'assets/mattersyn-identifier.svg', 'role': 'authored_illustration'}
        before = copy.deepcopy(asset)
        self.assertEqual(structure_asset_reader_description(asset),
                         'NanoXtalSyn-authored diagram; no measured coordinates.')
        self.assertEqual(asset, before)
        for description in ['Source text mentions MatterSyn-authored diagrams.',
                            '2026-09-16 historical MatterSyn attribution.',
                            'mattersyn-reference-schema/1', 'MatterSyn-authoredness is a different value.']:
            self.assertEqual(structure_asset_reader_description({'description': description}), description)

    def test_two_record_pages_project_all_fifteen_notes_and_preserve_Download_JSON(self):
        for rid, expected in [('chan2007-cdse-ag2se-microfluidic-jp073474u-route', 5),
                              ('naiki2013-ag-sio2-qd-jp305408p-route', 10)]:
            with self.subTest(record=rid):
                path = ROOT / 'data/records' / (rid + '.json')
                raw = path.read_bytes()
                record = json.loads(raw)
                before = copy.deepcopy(record)
                selected = [a for a in record['structure_assets'] if a['description'].startswith('MatterSyn-authored ')]
                self.assertEqual(len(selected), expected)
                meta = {'eligibility': {}, 'group_id': 'synthetic-display-test',
                        'split': 'development', 'record_sha256': hashlib.sha256(raw).hexdigest()}
                rendered = render_record(record, meta)
                self.assertEqual(rendered.count('NanoXtalSyn-authored '), expected)
                self.assertNotIn('MatterSyn-authored ', rendered)
                for asset in selected:
                    expected_note = 'NanoXtalSyn-authored ' + asset['description'][len('MatterSyn-authored '):]
                    self.assertIn(html.escape(expected_note, quote=True), rendered)
                self.assertIn('../data/records/' + rid + '.json', rendered)
                self.assertEqual(record, before)
                self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
