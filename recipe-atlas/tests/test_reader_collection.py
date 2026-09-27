"""Reader counts and presentation must not promote reference models into evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reader_collection import collection_summary, pair_documentation
from structure_recipe_metrics import recipe_structure_outcome_coverage
from generate_release_metadata import remove_public_progress


class ReaderCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/records').glob('*.json')]
        cls.policy=json.loads((ROOT/'data/structure-outcome-policy.json').read_text(encoding='utf-8'))
        cls.pairs=recipe_structure_outcome_coverage(cls.records,cls.policy)['rows']

    def test_one_paper_with_many_rows_is_counted_once(self):
        rows=[r for r in self.records if r['lineage']['source_group']=='voznyy2019']
        report=collection_summary(rows,[],[])
        self.assertEqual(100,len(rows))
        self.assertEqual(1,report['contributing_papers'])
        self.assertEqual(0,report['synthesis_structure_pairs'])
        self.assertEqual(100,report['experimental_series_rows'])

    def test_new_reference_cells_do_not_create_pairs_or_modify_records(self):
        before=json.dumps(self.records,sort_keys=True)
        a=collection_summary(self.records,self.pairs,[])
        refs=[{'id':'generic-reference','record_ids':[r['record_id'] for r in self.records]}]
        b=collection_summary(self.records,self.pairs,refs)
        self.assertEqual(a['synthesis_structure_pairs'],b['synthesis_structure_pairs'])
        self.assertEqual(a['contributing_papers'],b['contributing_papers'])
        self.assertEqual(a['material_families'],b['material_families'])
        self.assertEqual([x['pair_row_id'] for x in a['pairs']],[x['pair_row_id'] for x in b['pairs']])
        self.assertEqual(before,json.dumps(self.records,sort_keys=True))
        self.assertFalse(any(x['source_group']=='voznyy2019' for x in b['pairs']))
        self.assertEqual(a['synthesis_structure_pairs'],b['more_comprehensive_pairs']+b['partial_pairs'])

    def test_reference_for_another_specimen_does_not_fill_this_gap(self):
        row=self.pairs[0];record=next(r for r in self.records if r['record_id']==row['record_id'])
        ref={'id':'other-sample','record_ids':[record['record_id']],'displayPolicy':'sample_context_choice','sample_context_ids':['different-specimen']}
        detail=pair_documentation(row,record,[ref])
        self.assertFalse(detail['checks']['reference_unit_cell_available'])

    def test_unknown_quantity_and_reference_phase_cannot_complete_description(self):
        row=copy.deepcopy(self.pairs[0]);record=copy.deepcopy(next(r for r in self.records if r['record_id']==row['record_id']))
        row['product_structure_fields']=[];row['structural_measurements']=[]
        for material in record['materials']:
            for quantity in material.get('quantities',{}).values():quantity['status']='not_reported'
        detail=pair_documentation(row,record,[{'id':'reference','record_ids':[record['record_id']]}])
        self.assertEqual('partial',detail['category'])
        self.assertFalse(detail['checks']['reported_phase'])
        self.assertFalse(detail['checks']['quantified_recipe_and_ordered_conditions'])

    def test_per_record_reference_contexts_remain_separate(self):
        row=self.pairs[0];record=next(r for r in self.records if r['record_id']==row['record_id'])
        ref={'id':'contextual-cell','record_ids':[record['record_id']],'displayPolicy':'sample_context_choice','sample_context_ids':[row['sample_id']],'sampleContextIdsByRecord':{record['record_id']:['other-sample']}}
        self.assertFalse(pair_documentation(row,record,[ref])['checks']['reference_unit_cell_available'])

    def test_purity_is_not_a_reagent_charge_but_explicit_stock_mass_is(self):
        from charge_coverage import quantified_inputs
        q={'value':99,'unit':'%','status':'reported','evidence':[{'source_id':'source','locator':'Table 1'}]}
        record={'sources':[{'id':'source'}],'materials':[{'id':'precursor','stage':'synthesis','quantities':{'purity':q}}],'stocks':[],'operations':[]}
        self.assertEqual([],quantified_inputs(record)['material_ids'])
        mass={**q,'value':0.1,'unit':'g'}
        record['stocks']=[{'id':'stock','components':[{'material_id':'precursor','quantities':{'mass':mass}}]}]
        self.assertEqual(['precursor'],quantified_inputs(record)['material_ids'])
        record['stocks'][0]['components'][0]['quantities']['mass']['status']='not_reported'
        self.assertEqual([],quantified_inputs(record)['material_ids'])

    def test_owner_progress_is_removed_but_source_scope_and_data_stay(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir();(root/'records').mkdir()
            for name in ('progress.mjs','progress.css','data/review-progress.json','data/pilot-source-queue.json'):(root/name).write_text('owner work queue')
            record=root/'data/record.json';record.write_text('{"phase":null}');before=hashlib.sha256(record.read_bytes()).hexdigest()
            page=root/'records/a.html';page.write_text('<a href="../progress.html">Review progress</a><p>SI unreviewed; source scope preserved.</p><script src="../progress.mjs?v=1"></script>')
            remove_public_progress(root)
            self.assertNotIn('progress.html',page.read_text())
            self.assertNotIn('progress.mjs',page.read_text())
            self.assertIn('SI unreviewed',page.read_text())
            self.assertFalse((root/'data/review-progress.json').exists())
            self.assertEqual(before,hashlib.sha256(record.read_bytes()).hexdigest())
            self.assertIn('url=dataset.html',(root/'progress.html').read_text())


if __name__=='__main__':unittest.main()
