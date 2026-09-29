"""Cross-tier paper counts are deduplicated without promoting preliminary evidence."""
import copy
import html
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from preliminary_contract import SCHEMA, source_id
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


def preliminary(*dois):
    # This synthetic object validates only the public preliminary schema.
    loc = [{'page':1, 'section':'Synthetic fixture'}]
    entries = []
    for doi in dois:
        entries.append({'source_id':source_id(doi), 'doi':doi,
            'title':'SYNTHETIC TEST ONLY', 'citation':'Synthetic test fixture',
            'document_sha256':'0'*64, 'document_role':'main', 'source_pages':1,
            'inspected_pages':[1], 'material':{'label':'Zinc oxide', 'elements':['Zn','O'], 'existing_hub_id':None},
            'method_label':'Synthetic preparation', 'scope':'Synthetic test only',
            'deferred':['Independent review'],
            'precursors':[{'name':'Zinc source', 'amount':'1 g', 'role':'Source', 'locators':loc}],
            'operations':[{'order':1, 'action':'Dissolve the source', 'conditions':[], 'locators':loc},
                          {'order':2, 'action':'Heat the solution', 'conditions':[], 'locators':loc}],
            'outcome':{'sample_label':'Synthetic product', 'link_basis':'The synthetic recipe identifies the test product.',
                'descriptors':[{'kind':'phase', 'reported':'ZnO', 'technique':'XRD', 'locators':loc}], 'locators':loc},
            'missing_fields':['Real source evidence'],
            'review':{'tier':'preliminary', 'author_source_checked':True, 'independent_audit':'pending', 'accuracy':'unmeasured', 'training_ready':False},
            'extraction':{'origin':'assistant_source_checked', 'recipe_scope_complete':True, 'omitted_variants':'Synthetic fixture only', 'source_identity_checked':True},
            'evidence_fingerprint':'0'*64})
    return {'schema':SCHEMA, 'entries':entries}


class SourceCoverageTests(unittest.TestCase):
    def test_primary_source_only_many_variants_count_once(self):
        records = [record('one'), record('two'), record('three')]
        report = source_coverage(records, preliminary())
        self.assertEqual(1, report['total_contributing_papers'])
        self.assertEqual(1, report['reviewed_contributing_papers'])
        self.assertEqual(0, report['additional_preliminary_papers'])

    def test_doi_case_and_cross_tier_overlap(self):
        records = [record('one','10.9999/PAPER-A'), record('two','10.9999/paper-a','other-group')]
        report = source_coverage(records, preliminary('10.9999/paper-a','10.9999/paper-b'))
        self.assertEqual((2,1,2,1,1), tuple(report[k] for k in [
            'total_contributing_papers','reviewed_contributing_papers',
            'preliminary_contributing_papers','additional_preliminary_papers',
            'overlapping_preliminary_papers']))

    def test_missing_doi_keeps_existing_url_then_id_identity(self):
        first = record(); first['sources'][1].update(doi=None, url='https://example.org/source')
        second = record('two',None,'source-b')
        third = copy.deepcopy(second); third['record_id']='three'
        report = source_coverage([first,second,third], preliminary())
        self.assertEqual(2, report['reviewed_contributing_papers'])

    def test_empty_tiers_and_preliminary_only(self):
        self.assertEqual(0, source_coverage([], preliminary())['total_contributing_papers'])
        self.assertEqual(1, source_coverage([record()])['total_contributing_papers'])
        report = source_coverage([], preliminary('10.9999/paper-b'))
        self.assertEqual(1, report['total_contributing_papers'])
        self.assertEqual(0, report['reviewed_contributing_papers'])
        self.assertEqual(1, report['additional_preliminary_papers'])

    def test_unvalidated_catalog_fails_closed(self):
        duplicate = preliminary('10.9999/paper-a','10.9999/paper-a')
        invalid_tier = preliminary('10.9999/paper-a')
        invalid_tier['entries'][0]['review']['training_ready'] = True
        for invalid in [duplicate, invalid_tier, {'entries':[]}]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                source_coverage([record()], invalid)

    def test_missing_primary_source_is_not_replaced_by_a_citation(self):
        broken = record(); broken['lineage']['source_group']='missing'
        with self.assertRaises(StopIteration):
            source_coverage([broken], preliminary())

    def test_existing_collection_fields_and_inputs_unchanged(self):
        records = [record()]
        catalog = preliminary('10.9999/paper-b')
        before = copy.deepcopy((records,catalog))
        old = collection_summary(records, [], [])
        new = collection_summary(records, [], [], catalog)
        self.assertEqual({k:v for k,v in old.items() if k!='source_coverage'},
                         {k:v for k,v in new.items() if k!='source_coverage'})
        self.assertEqual(1, new['contributing_papers'])
        self.assertEqual(1, new['material_families'])
        self.assertEqual(0, new['synthesis_structure_pairs'])
        self.assertEqual(2, new['source_coverage']['total_contributing_papers'])
        self.assertEqual(before, (records,catalog))

    def test_shared_main_and_inventory_cards_show_union_and_scope(self):
        collection = collection_summary([record()], [], [], preliminary('10.9999/paper-b'))
        page = collection_metrics_html(collection)
        self.assertIn('<strong>2</strong><span>Papers across all tiers</span>', page)
        self.assertIn('1 reviewed-collection papers', page)
        self.assertIn('1 additional preliminary papers', page)
        self.assertIn('Reviewed material families', page)
        self.assertIn('Reviewed recipe–structure pairs', page)
        self.assertIn('preliminary-synthesis.html', page)
        self.assertIn('excluded from training', page)

    def test_dataset_page_counts_union_but_lists_reviewed_records(self):
        collection = collection_summary([record()], [], [], preliminary('10.9999/paper-b'))
        page = render({'reader_collection':collection}, {'records':[]},
                      lambda title:'<html><head></head>', lambda:'', html.escape, str)
        self.assertIn('<strong>2</strong><span>Papers across all tiers</span>', page)
        self.assertIn('Explore reviewed synthesis and evidence records', page)
        self.assertIn('Reviewed synthesis recipe–structure pairs', page)
        self.assertNotIn('<span>Contributing papers</span>', page)

    def test_library_total_is_distinct_from_searchable_reviewed_list(self):
        collection = collection_summary([record()], [], [], preliminary('10.9999/paper-b'))
        page = library_body(collection)
        self.assertIn('<strong>2</strong><span>Papers across all tiers</span>', page)
        self.assertIn('Papers in the reviewed list', page)
        self.assertIn('The searchable list below contains reviewed-collection papers', page)
        self.assertIn('Preliminary-only papers are listed', page)
        self.assertIn('preliminary-synthesis.html', page)
        self.assertNotIn('<span>Contributing papers</span>', page)


if __name__ == '__main__':
    unittest.main()
