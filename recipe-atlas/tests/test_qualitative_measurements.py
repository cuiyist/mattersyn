"""Typed source observations and surface-target supervision; fixtures are not experiments."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_dataset import fixture
from record_helpers import ev,fact,measurement,material
from dataset_lib import validate_record,fmt,eligibility,training_view

class QualitativeEvidenceTests(unittest.TestCase):
    def test_solubility_fact_is_preserved_without_numeric_target(self):
        r=fixture();r['schema_version']='1.1.0';e=ev('synthetic-source','Synthetic solubility observation')
        r['measurements']=[measurement('solubility','sample-a','colloidal_solubility',fact('Stable dispersion',e),'Visual observation',e)]
        self.assertEqual([],validate_record(r))
        self.assertEqual('Stable dispersion',fmt(r['measurements'][0]['value']))
        self.assertFalse(eligibility(r)['size_conditioned_recipe']['eligible'])
        self.assertFalse(eligibility(r)['optical_outcome']['eligible'])
        self.assertNotIn('Stable dispersion',str(training_view(r,'partial_protocol')['input']))

    def test_qualitative_missingness_and_provenance_are_enforced(self):
        r=fixture();e=ev('synthetic-source','Synthetic observation')
        r['measurements']=[measurement('q','sample-a','observation',fact('Present',[],status='reported'),'Visual',e)]
        self.assertTrue(validate_record(r))
        r['measurements'][0]['value']=fact('Present',e,status='not_reported')
        self.assertTrue(validate_record(r))
        r['measurements'][0]['value']=fact(None,e)
        self.assertEqual([],validate_record(r))
        self.assertEqual('Not reported',fmt(r['measurements'][0]['value']))

    def test_surface_target_keeps_seed_and_acyl_reagent(self):
        r=fixture();e=ev('synthetic-source','Synthetic surface modification')
        r['intended_target']['surface']=fact('Acetylated phenolic surface',e)
        r['materials']=[material('seed','Phenolic seed','CdS','seed','synthesis',e),material('acyl','Acyl reagent','C5H6N2O','surface_functionalization_reagent','synthesis',e)]
        r['stocks']=[];r['material_states']=[];r['operations']=[];r['products']=[];r['measurements']=[]
        self.assertEqual([],validate_record(r))
        self.assertTrue(eligibility(r)['precursor_selection']['eligible'])
        exported=training_view(r,'precursor_selection')
        self.assertEqual(['seed','surface_functionalization_reagent'],[m['role']for m in exported['output']['precursors']])
        self.assertEqual('Acetylated phenolic surface',exported['input']['requested_surface']['value'])

if __name__=='__main__':unittest.main()
