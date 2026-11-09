"""Normal GitHub full-candidate test; do not run this all-record loop locally.

It measures reader visibility, not scientific validity or new admission status.
"""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from reader_background import attach_background, load_library, select_background
from reader_presentation_registry import load_reviewed_reader, source_paths


class EveryRecordBackground(unittest.TestCase):
    def test_all_Reader_records_have_neutral_background_without_changing_source_inputs(self):
        paths = sorted((ROOT/'data/records').glob('*.json'))
        self.assertTrue(paths)
        source = ROOT/'data/reader-presentation-reviewed.json'
        input_paths = paths+list(source_paths(source))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
        records = {p.stem: json.loads(p.read_bytes()) for p in paths}
        view = load_reviewed_reader(source)
        library = load_library(ROOT)
        original = copy.deepcopy(view)
        projected, coverage = attach_background(view, records, library)
        self.assertEqual(view, original)
        self.assertEqual(set(projected['records']), set(records), 'Every canonical record must have a Reader projection')
        for rid, entry in view['records'].items():
            with self.subTest(record=rid):
                background = projected['records'][rid]['general_background']
                self.assertGreaterEqual(len(background), 1)
                self.assertLessEqual(len(background), 3)
                self.assertEqual({k: v for k, v in projected['records'][rid].items() if k != 'general_background'}, entry)
                reviewed = copy.deepcopy(records[rid])
                extracted = copy.deepcopy(records[rid])
                reviewed.setdefault('quality', {})['review_status'] = 'reviewed'
                extracted.setdefault('quality', {})['review_status'] = 'source_extracted'
                self.assertEqual(select_background(reviewed, entry, library), select_background(extracted, entry, library))
        self.assertEqual(coverage['after_sections_visible'], len(records))
        self.assertEqual(coverage['neither'], 0)
        self.assertEqual(sum(coverage['background_card_distribution'].values()), len(records))
        self.assertEqual({p: hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}, before)
        # Small quote-free counts are also emitted by build_reader_metadata and
        # become dist/data/reader-background-coverage.json in the actual build.
        print('M_CHEMICAL_INTUITION_COVERAGE '+json.dumps(coverage, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
