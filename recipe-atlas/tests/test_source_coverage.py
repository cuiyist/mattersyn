"""Homepage paper totals count unique primary sources in regular records only."""
import html
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from source_coverage import source_coverage, collection_metrics_html
from reader_collection import collection_summary
from catalog_view import render
from build_reader_views import library_body


def record(rid='record-a', doi='10.9999/paper-a', source='source-a'):
    return {'record_id':rid, 'collection':'reviewed_literature',
            'record_type':'literature_protocol', 'reader_role':'synthesis_route',
            'quality':{'review_status':'source_reviewed', 'requested_tasks':[]},
            'material':{'formula':'ZnO'}, 'operations':[{'stage':'synthesis'}],
            'lineage':{'source_group':source},
            'sources':[{'id':'supporting-citation', 'doi':'10.9999/not-primary'},
                       {'id':source, 'doi':doi}]}


class SourceCoverageTests(unittest.TestCase):
    def test_primary_source_only_many_variants_count_once(self):
        report = source_coverage([record('one'), record('two'), record('three')])
        self.assertEqual(1, report['total_contributing_papers'])
        self.assertEqual(1, report['reviewed_contributing_papers'])

    def test_distinct_primary_sources_use_casefolded_doi_url_or_id(self):
        first = record('one','10.9999/PAPER-A')
        second = record('two','10.9999/paper-a','different-lineage-same-paper')
        third = record('three',None,'source-b')
        third['sources'][1]['url'] = 'https://example.org/paper-c'
        fourth = record('four',None,'paper-d')
        fourth['sources'][1].pop('doi')
        report = source_coverage([first, second, third, fourth])
        self.assertEqual(3, report['total_contributing_papers'])

    def test_missing_primary_source_is_not_replaced_by_a_citation(self):
        broken = record(); broken['lineage']['source_group']='missing'
        with self.assertRaises(StopIteration):
            source_coverage([broken])

    def test_empty_regular_collection_is_zero(self):
        self.assertEqual(0, source_coverage([])['total_contributing_papers'])

    def test_machine_sources_cannot_inflate_audited_count(self):
        row=record();row['collection']='machine_extracted'
        with self.assertRaisesRegex(ValueError,'cannot contribute'):source_coverage([row])

    def test_collection_cards_explain_paper_level_count(self):
        collection = collection_summary([record()], [], [])
        page = collection_metrics_html(collection)
        self.assertIn('1 + <b data-machine-papers>0</b>', page)
        self.assertIn('Audited + machine-extracted papers',page)
        self.assertIn('do not imply an independently audited complete paper', page)
        self.assertEqual(['10.9999/paper-a'],collection['source_coverage']['audited_primary_dois'])
        self.assertNotIn('preliminary', page.lower())
        self.assertIn('Each contributing primary paper counts once', page)

    def test_dataset_and_library_have_no_preliminary_lane(self):
        collection = collection_summary([record()], [], [])
        dataset = render({'reader_collection':collection}, {'records':[]},
                         lambda title:'<html><head></head>', lambda:'', html.escape, str)
        library = library_body(collection)
        for page in (dataset, library):
            self.assertNotIn('preliminary', page.lower())
            self.assertNotIn('Papers across all tiers', page)


if __name__ == '__main__':
    unittest.main()
