"""Regression checks for scientifically consequential variant and coverage boundaries."""
import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from dataset_lib import eligibility,build_groups,fmt
from build_paper_reviews import validate
def record(id):return json.loads((ROOT/'data/records'/(id+'.json')).read_text(encoding='utf-8'))
def quantities(x):
    if isinstance(x,dict):
        if 'status' in x and 'unit' in x:yield x
        for v in x.values():yield from quantities(v)
    elif isinstance(x,list):
        for v in x:yield from quantities(v)
class ReviewIntegrity(unittest.TestCase):
    def test_unreported_numeric_temperature_preserves_room_temperature_note(self):
        from record_helpers import qty
        self.assertIn("Room temperature",fmt(qty(unit="C",qualifier="Room temperature; numerical value unspecified")))
    def test_changed_reagent_does_not_inherit_old_charge(self):
        r=record('fu-2007-zno-s3')
        self.assertNotIn('diethanolamine',{m['id'] for m in r['materials']})
        stock=next(s for s in r['stocks'] if s['id']=='ammonia-stock')
        self.assertTrue(all(q['value'] is None for q in quantities(stock)))
        self.assertFalse(any(q['value']==26.3 and q['unit']=='mg' for q in quantities(r['operations'])))
    def test_changed_concentration_does_not_inherit_old_mass(self):
        r=record('fu-2007-zno-s4');stock=next(s for s in r['stocks'] if s['id']=='zinc-stock')
        self.assertEqual(stock['concentrations']['zinc_nitrate']['value'],4)
        self.assertFalse(any(q['value']==37.2 and q['unit']=='mg' for q in quantities(r)))
    def test_distinct_sample_state_for_dry_s2_emission(self):
        r=record('fu-2007-zno-s2')
        peaks=[m for m in r['measurements'] if m['property']=='photoluminescence_peak']
        self.assertTrue(peaks)
        self.assertTrue(all(m['sample_id']=='fu2007-s2-dry' for m in peaks))
        self.assertNotIn('oleic_acid',{m['id'] for m in r['materials']})
    def test_ambiguous_iron_dimensions_cannot_be_diameter_targets(self):
        r=record('feld-2019-iron-oxide-undiluted-cubic-condition')
        self.assertFalse(eligibility(r)['size_conditioned_recipe']['eligible'])
        self.assertFalse(eligibility(r)['exact_structure_recipe']['eligible'])
        self.assertTrue(all(p['phase']['value'] is None for p in r['products']))
    def test_related_control_and_variant_records_stay_together(self):
        records=[record(p.stem) for p in (ROOT/'data/records').glob('*.json')]
        groups=build_groups(records)
        for source in ['fu2007','stowell2005','nakonechnyi2017','feld2019']:
            self.assertEqual(len({groups[r['record_id']]for r in records if r['lineage']['source_group']==source}),1)
    def test_incomplete_page_or_changed_figure_fails_coverage_check(self):
        c=json.loads((ROOT/'data/paper-reviews/fu2007.json').read_text(encoding='utf-8'))
        self.assertEqual(validate(c),[])
        missing=copy.deepcopy(c);missing['documents'][0]['pages'].pop()
        self.assertTrue(validate(missing))
        unread=copy.deepcopy(c);unread['documents'][0]['pages'][0]['text_read']=False
        self.assertTrue(validate(unread))
        altered=copy.deepcopy(c);altered['figures'][0]['public_asset_sha256']='0'*64
        self.assertTrue(validate(altered))
if __name__=='__main__':unittest.main()
