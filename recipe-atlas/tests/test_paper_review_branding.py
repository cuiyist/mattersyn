"""Synthetic current review-note projection; never reads records or papers."""
import contextlib
import copy
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_paper_reviews as reviews


class CurrentReviewBrandTests(unittest.TestCase):
    def test_five_exact_publication_status_notes_only(self):
        for note in reviews.CURRENT_PUBLICATION_BRAND_NOTES:
            with self.subTest(note=note):
                source = {'publication_status': note, 'source_payload': {'text': note},
                          'schema': 'mattersyn-paper-review/1', 'date': '2026-09-16',
                          'evidence': [{'summary': note}], 'title': 'MatterSyn historical example'}
                before = copy.deepcopy(source)
                projected = reviews.public_review_branding(source)
                expected = copy.deepcopy(source)
                expected['publication_status'] = note.replace('MatterSyn', 'NanoXtalSyn')
                self.assertEqual(projected, expected)
                self.assertEqual(source, before)
                source['publication_status'] = note + ' Historical qualification.'
                self.assertEqual(reviews.public_review_branding(source), source)

    def test_exact_authored_illustration_summary_only(self):
        note = reviews.CURRENT_ILLUSTRATION_BRAND_NOTE
        source = {'authored_illustrations': [{'summary': note, 'source_payload': {'summary': note}},
                                            {'summary': note + ' Extra authored context.'}],
                  'reader_sections': [{'items': [{'summary': note}]}], 'source_payload': {'summary': note}}
        before = copy.deepcopy(source)
        projected = reviews.public_review_branding(source)
        expected = copy.deepcopy(source)
        expected['authored_illustrations'][0]['summary'] = note.replace('MatterSyn', 'NanoXtalSyn')
        self.assertEqual(projected, expected)
        self.assertEqual(source, before)

    def test_main_writes_projected_review_without_changing_input_evidence(self):
        note = next(iter(reviews.CURRENT_PUBLICATION_BRAND_NOTES))
        source = {'paper_id': 'synthetic', 'doi': '10.fixture/synthetic', 'title': 'Synthetic',
                  'publication_status': note, 'source_payload': {'text': note},
                  'figures': [], 'tables': [], 'recipe_inventory': [], 'documents': []}
        outputs = []
        scope = {'label': 'Synthetic', 'scope': 'synthetic', 'si_status': 'unknown', 'main_status': 'unknown'}
        with patch.object(reviews, 'DATA', SimpleNamespace(glob=lambda _: [Path('synthetic.json')])), \
             patch.object(reviews, 'read', return_value=source), \
             patch.object(reviews, 'display_view', side_effect=lambda value, *_: copy.deepcopy(value)), \
             patch.object(reviews, 'stage_reader_evidence'), patch.object(reviews, 'validate', return_value=[]), \
             patch.object(reviews, 'source_review_scope', return_value=scope), \
             patch.object(reviews, 'reviewed_page_count', return_value=0), \
             patch.object(reviews, 'write', side_effect=lambda p, value: outputs.append((p, value))), \
             contextlib.redirect_stdout(io.StringIO()):
            reviews.main()
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0][1]['publication_status'], note.replace('MatterSyn', 'NanoXtalSyn'))
        self.assertEqual(outputs[0][1]['source_payload'], source['source_payload'])
        self.assertEqual(source['publication_status'], note)
        self.assertEqual(outputs[1][1]['papers'][0]['id'], 'synthetic')


if __name__ == '__main__':
    unittest.main()
