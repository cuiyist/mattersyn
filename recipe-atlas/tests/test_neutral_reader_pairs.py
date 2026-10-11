"""Synthetic display inventory checks; audited data and training gates remain separate."""
from pathlib import Path
import copy, html, json, sys, unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from reader_collection import collection_summary,source_extracted_record_pairs
from catalog_view import structure_coverage_html
from source_coverage import collection_metrics_html
from dataset_lib import eligibility

def fixture(rid,status='source_extracted',kind='literature_protocol',products=None):
    return {'record_id':rid,'title':'Synthetic fixture '+rid,'record_type':kind,
            'collection':'reviewed_literature','reader_role':'synthesis_route',
            'material':{'formula':'ZnO','family':'synthetic','elements':['Zn','O']},
            'quality':{'review_status':status,'requested_tasks':[]},'method':'synthetic',
            'sources':[{'id':'source-'+rid,'doi':'10.9999/'+rid,'year':2026}],
            'lineage':{'source_group':'source-'+rid,'duplicate_of':None},'materials':[], 'stocks':[],
            'operations':[{'id':'heat','stage':'synthesis','evidence':[{'source_id':'source-'+rid,'locator':'Synthetic page 1'}],'parameters':{}}],
            'products':products or [],'measurements':[],'structure_assets':[]}

def audited_pair(rid,sample='product'):
    return {'pair_row_id':rid+'::'+sample,'record_id':rid,'record_page_path':'records/'+rid+'.html',
            'title':'Synthetic fixture '+rid,'source_group':'source-'+rid,'year':2026,
            'sample_id':sample,'source_sample_label':'','composition':{},
            'product_structure_fields':[],'structural_measurements':[]}

class NeutralReaderPairs(unittest.TestCase):
    def test_every_extracted_record_contributes_exactly_one_display_row(self):
        rows=[fixture('main'),fixture('support','source_extracted','procedure'),fixture('assembly','source_extracted','observation')]
        before=copy.deepcopy(rows)
        result=source_extracted_record_pairs(rows)
        self.assertEqual(3,len(result));self.assertEqual(3,len({r['pair_row_id'] for r in result}))
        self.assertEqual(rows,before)
        self.assertTrue(all(r['display_pair_basis']=='one_record' and r['review_status']=='source_extracted' for r in result))
    def test_multiple_products_do_not_inflate_the_record_count(self):
        row=fixture('multi',products=[{'sample_id':'a'},{'sample_id':'b'}])
        pairs=source_extracted_record_pairs([row]);self.assertEqual(1,len(pairs));self.assertEqual('a',pairs[0]['sample_id'])
    def test_missing_product_and_outcome_cells_remain_blank(self):
        row=fixture('missing');collection=collection_summary([row],[],[])
        page=structure_coverage_html({'reader_collection':collection},html.escape,collection['pairs'])
        self.assertIn('<td><small></small></td><td></td>',page)
        self.assertNotIn('Composition unspecified',page)
        self.assertNotIn('not reported',page.lower())
    def test_reported_and_inferred_values_are_not_relabelled(self):
        row=fixture('facts',products=[{'sample_id':'a','phase':{'value':'Synthetic phase','status':'inferred'},'morphology':{'value':None,'status':'not_reported'}}])
        before=copy.deepcopy(row);collection=collection_summary([row],[],[])
        self.assertEqual('inferred',collection['pairs'][0]['product_structure_fields'][0]['value']['status'])
        page=structure_coverage_html({'reader_collection':collection},html.escape,collection['pairs'])
        self.assertIn('Synthetic phase (inferred)',page);self.assertEqual(before,row)
    def test_only_sample_linked_existing_structural_measurements_are_projected(self):
        row=fixture('measure',products=[{'sample_id':'a'}])
        for ident,sample,prop in [('right','a','particle_diameter'),('wrong','b','particle_diameter'),('optical','a','emission_peak')]:
            row['measurements'].append({'id':ident,'sample_id':sample,'property':prop,'value':{'value':3,'status':'reported'}})
        pairs=source_extracted_record_pairs([row],{'measurement_properties':['particle_diameter'],'measurement_fields':{'particle_diameter':'size.diameter'}})
        self.assertEqual(['right'],[m['measurement_id'] for m in pairs[0]['structural_measurements']])
    def test_audited_rows_and_record_statuses_remain_unchanged(self):
        gold=fixture('gold','source_reviewed');machine=fixture('machine')
        original=[audited_pair('gold')];before=copy.deepcopy(original);records_before=copy.deepcopy([gold,machine])
        combined=collection_summary([gold,machine],original,[])
        self.assertEqual(original,before);self.assertEqual(records_before,[gold,machine])
        projected=copy.deepcopy(combined['pairs'][0]);projected.pop('documentation')
        self.assertEqual(before[0],projected)
        self.assertEqual((2,1,1),(combined['synthesis_structure_pairs'],combined['audited_synthesis_structure_pairs'],combined['source_extracted_record_pairs']))
    def test_expected_864_plus_284_display_arithmetic(self):
        gold=fixture('gold','source_reviewed');records=[gold]+[fixture('machine-'+str(i)) for i in range(284)]
        rows=[audited_pair('gold','sample-'+str(i)) for i in range(864)]
        summary=collection_summary(records,rows,[])
        self.assertEqual((1148,864,284),(summary['synthesis_structure_pairs'],summary['audited_synthesis_structure_pairs'],summary['source_extracted_record_pairs']))
    def test_neutral_paper_total_keeps_internal_doi_and_scope_metadata(self):
        summary=collection_summary([fixture('gold','source_reviewed'),fixture('machine')],[],[])
        page=collection_metrics_html(summary)
        self.assertIn('>2</strong><span>Papers</span>',page)
        self.assertIn('data-source-extracted-papers="1"',page)
        visible=__import__('re').sub('<[^>]*>',' ',page)
        self.assertNotRegex(visible.lower(),r'machine|source.extracted|not independently audited')
    def test_all_six_training_tasks_still_exclude_extracted_records(self):
        tasks=eligibility(fixture('not-training'))
        self.assertEqual(6,len(tasks));self.assertTrue(all(not v['eligible'] for v in tasks.values()))

if __name__=='__main__':unittest.main()
