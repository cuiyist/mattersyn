"""Observed characterization must not become a material synthesis method."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_atlas import synthesis_route

class MaterialRouteAdmissionTests(unittest.TestCase):
    def route(self):
        return {'record_id':'synthetic-control','collection':'reviewed_literature',
                'record_type':'protocol_variant','reader_role':'synthesis_route',
                'quality':{'review_status':'source_reviewed','requested_tasks':[]},
                'operations':[{'stage':'synthesis'}]}

    def test_reviewed_control_route_does_not_require_training_admission(self):
        self.assertTrue(synthesis_route(self.route()))

    def test_observation_is_excluded_even_with_inherited_route_metadata(self):
        r=self.route();r['record_type']='observation'
        for role in ['synthesis_route','contextual_observation',None]:
            r['reader_role']=role;r['quality']['requested_tasks']=['precursor_selection']
            with self.subTest(role=role):self.assertFalse(synthesis_route(r))

    def test_explicit_context_role_overrides_legacy_task(self):
        r=self.route();r['reader_role']='contextual_observation'
        r['quality']['requested_tasks']=['precursor_selection']
        self.assertFalse(synthesis_route(r))

    def test_legacy_admission_remains_available_only_without_explicit_role(self):
        r=self.route();del r['reader_role'];r['quality']['requested_tasks']=['precursor_selection']
        self.assertTrue(synthesis_route(r))

    def test_procedure_unreviewed_and_assay_records_stay_out(self):
        for field,value in [('record_type','procedure'),('review','candidate'),('stage','characterization')]:
            r=self.route()
            if field=='review':r['quality']['review_status']=value
            elif field=='stage':r['operations'][0]['stage']=value
            else:r[field]=value
            with self.subTest(field=field):self.assertFalse(synthesis_route(r))

if __name__=='__main__':unittest.main()
