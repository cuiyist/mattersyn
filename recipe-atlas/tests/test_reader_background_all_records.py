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
from reader_background import attach_background, load_library, select_background, render_record_background
from build_dataset import render_record
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
        reader_ids = set(view['records'])
        self.assertTrue(reader_ids)
        self.assertLessEqual(reader_ids, set(records), 'Every live Reader projection must name a canonical record')
        original = copy.deepcopy(view)
        projected, coverage = attach_background(view, records, library)
        self.assertEqual(view, original)
        self.assertEqual(set(projected['records']), reader_ids, 'Every live Reader record must retain its projection')
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
        self.assertEqual(coverage['canonical_records'], len(records))
        self.assertEqual(coverage['reader_records'], len(reader_ids))
        self.assertEqual(coverage['after_sections_visible'], len(reader_ids))
        self.assertEqual(coverage['neither'], 0)
        self.assertEqual(sum(coverage['background_card_distribution'].values()), len(reader_ids))
        # Every canonical static record page also carries background, including
        # context/analysis pages which deliberately never enter Reader/material lists.
        for rid, record in records.items():
            with self.subTest(static_record=rid):
                cards = select_background(record, {}, library)
                self.assertGreaterEqual(len(cards), 1)
                self.assertLessEqual(len(cards), 3)
                meta = {'eligibility': {}, 'group_id': 'background-render-test',
                        'split': 'development', 'record_sha256': before[ROOT/'data/records'/(rid+'.json')]}
                page = render_record(record, meta, library)
                rendered = render_record_background(record, library)
                self.assertEqual(page.count('data-record-background'), 1)
                self.assertIn(rendered, page)
                intuition = page.split('<section id="intuition"', 1)[1].split('<section id="evidence"', 1)[0]
                self.assertIn(rendered, intuition)
                self.assertLess(intuition.index('id="record-intuition-content"'), intuition.index(rendered))
                self.assertEqual(intuition.count('data-background-id='), len(cards))
                reviewed, extracted = copy.deepcopy(record), copy.deepcopy(record)
                reviewed.setdefault('quality', {})['review_status'] = 'source_reviewed'
                extracted.setdefault('quality', {})['review_status'] = 'source_extracted'
                self.assertEqual(render_record_background(reviewed, library), render_record_background(extracted, library))
        canonical = coverage['all_canonical']
        self.assertEqual(canonical['record_pages'], len(records))
        self.assertEqual(canonical['pages_with_authored_background_after'], len(records))
        self.assertEqual(sum(canonical['background_card_distribution'].values()), len(records))
        self.assertEqual(canonical['Data_only_default_pages'], len(records)-len(reader_ids))
        self.assertEqual(canonical['default_visible_union_before'], coverage['before_sections_visible']+len(records)-len(reader_ids))
        self.assertEqual(canonical['default_visible_union_after'], len(records))
        self.assertEqual({p: hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}, before)
        # Small quote-free counts are also emitted by build_reader_metadata and
        # become dist/data/reader-background-coverage.json in the actual build.
        print('M_CHEMICAL_INTUITION_COVERAGE '+json.dumps(coverage, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
