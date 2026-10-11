"""Synthetic source-extracted lane regression checks; no scientific evidence."""
from pathlib import Path
import copy,json,tempfile,unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_atlas
from source_coverage import source_coverage,collection_metrics_html
from record_helpers import source,record,operation,ev
from dataset_lib import eligibility

def fixture(rid,doi,status='source_extracted'):
    src=source('source-'+rid,doi,'Synthetic fixture',[],2026)
    r=record(rid,'Synthetic fixture','ZnO','synthetic','synthetic',src,'Synthetic page 1')
    r.update(collection='reviewed_literature',reader_role='synthesis_route')
    r['quality']['review_status']=status
    r['operations']=[operation('step-1','heat','Synthetic heat',ev(src['id'],'Synthetic page 1'),[],[])]
    return r
class SourceExtractedLaneTests(unittest.TestCase):
    def test_primary_doi_dedup_and_review_counts_stay_separate(self):
        rows=[fixture('gold-a','10.9999/A','source_reviewed'),fixture('same-paper','10.9999/a'),fixture('machine-b','10.9999/B'),fixture('variant-b','10.9999/b')]
        counts=source_coverage(rows)
        self.assertEqual((2,1,1),(counts['total_contributing_papers'],counts['audited_contributing_papers'],counts['machine_extracted_contributing_papers']))
        self.assertEqual(['10.9999/a'],counts['audited_primary_dois'])
        self.assertEqual(['10.9999/b'],counts['source_extracted_primary_dois'])
    def test_nonroute_extracted_records_do_not_add_a_paper(self):
        row=fixture('procedure','10.9999/procedure');row['record_type']='procedure'
        self.assertEqual(0,source_coverage([row])['total_contributing_papers'])
    def test_rendered_counter_keeps_extracted_base_and_doi_binding(self):
        counts=source_coverage([fixture('machine-b','10.9999/B')])
        page=collection_metrics_html({'source_coverage':counts,'material_families':1,'synthesis_structure_pairs':0})
        self.assertIn('data-source-extracted-papers="1"',page)
        self.assertIn('>1</b>',page)
        self.assertIn('not independently audited',page)
    def test_extracted_records_remain_ineligible_for_every_training_task(self):
        self.assertFalse(any(v['eligible'] for v in eligibility(fixture('machine-b','10.9999/B')).values()))
    def test_tiny_atlas_has_disjoint_status_membership_and_counts(self):
        original=build_atlas.ROOT
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=root/'data';(data/'records').mkdir(parents=True);(data/'paper-reviews').mkdir();(data/'corpus').mkdir()
            (data/'inventory-evidence.json').write_text('{"per_paper": []}',encoding='utf-8')
            rows=[fixture('gold-a','10.9999/a','source_reviewed'),fixture('machine-b','10.9999/b')]
            for row in rows:(data/'records'/(row['record_id']+'.json')).write_text(json.dumps(row),encoding='utf-8')
            try:build_atlas.ROOT=root;build_atlas.main()
            finally:build_atlas.ROOT=original
            library=json.loads((root/'dist/data/library-index.json').read_text())['papers']
            extracted=next(p for p in library if p['doi']=='10.9999/b')
            self.assertEqual([],extracted['reviewedRecordIds']);self.assertEqual(['machine-b'],extracted['extractedRecordIds'])
            self.assertEqual('source_extracted',extracted['reviewStatus'])
            shard=json.loads(next((root/'dist/data/materials').glob('*.json')).read_text())
            self.assertEqual((1,1,2),(shard['reviewed_records'],shard['source_extracted_records'],shard['route_records']))
            paper=json.loads((root/'dist/data/papers'/(extracted['id']+'.json')).read_text())
            self.assertEqual('source_extracted_records',paper['recipeCurationStatus'])
            self.assertEqual('source_extracted_contribution',paper['materialContributionStatus'])
if __name__=='__main__':unittest.main()
