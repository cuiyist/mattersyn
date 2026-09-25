"""A reviewed synthesis must not silently disappear when its formula is a family label."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_atlas import material_elements,synthesis_route

def record(formula,elements=None,role='synthesis_route'):
    return {'record_id':'family-fixture','collection':'reviewed_literature','record_type':'literature_protocol',
            'reader_role':role,'quality':{'review_status':'source_reviewed','requested_tasks':[]},
            'operations':[{'stage':'synthesis'}],'material':{'formula':formula,'elements':elements or []}}

class MaterialElementAdmission(unittest.TestCase):
    def test_missing_family_elements_stop_build(self):
        with self.assertRaisesRegex(ValueError,'family-fixture'):
            material_elements(record('Cs3Cu2X5 (X = Cl, Br, I)'))

    def test_source_scoped_explicit_elements_support_family_label(self):
        self.assertEqual(['Cs','Cu','Cl','Br','I'],material_elements(record('Cs3Cu2X5 (X = Cl, Br, I)',['Cs','Cu','Cl','Br','I'])))

    def test_ordinary_formula_keeps_existing_inference(self):
        self.assertEqual(['Cd','Se'],material_elements(record('CdSe')))

    def test_symbolic_context_is_not_promoted(self):
        context=record('unresolved X',role='context_observation')
        self.assertFalse(synthesis_route(context))
        material_elements(context)

    def test_all_existing_reviewed_routes_have_valid_elements(self):
        for path in (ROOT/'data/records').glob('*.json'):
            data=json.loads(path.read_bytes())
            if synthesis_route(data):
                with self.subTest(record=data['record_id']):self.assertTrue(material_elements(data))
