"""Host and electrolyte supervision without importing measured outcomes into inputs."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_dataset import fixture
from record_helpers import ev,fact,material
from dataset_lib import validate_record,training_view

class HostTargetTests(unittest.TestCase):
    def test_host_target_and_electrolyte_remain_distinct(self):
        a=fixture();a['schema_version']='1.2.0'
        e=ev('synthetic-source','Synthetic host recipe, not an experiment')
        a['intended_target']['host']=fact('Iminodiacetate polymer',e)
        a['materials'].append(material('salt','Sodium chloride','NaCl','electrolyte','synthesis',e))
        self.assertEqual([],validate_record(a))
        exported=training_view(a,'precursor_selection')
        self.assertEqual('Iminodiacetate polymer',exported['input']['requested_host']['value'])
        self.assertEqual('electrolyte',exported['output']['process_materials'][0]['role'])
        self.assertNotIn('electrolyte',str(exported['output']['precursors']))
        self.assertNotIn('measurements',exported['input'])
        a['materials']=[x for x in a['materials'] if x['id']!='salt']
        self.assertNotIn('process_materials',training_view(a,'precursor_selection')['output'])

    def test_unreported_host_is_not_imputed(self):
        a=fixture();e=ev('synthetic-source','Synthetic unspecified host')
        a['intended_target']['host']=fact(None,e)
        self.assertNotIn('requested_host',training_view(a,'partial_protocol')['input'])
        a['intended_target']['host']=fact('invented',e,status='not_reported')
        self.assertTrue(validate_record(a))

if __name__=='__main__':unittest.main()
