"""Architecture distinctions for source-reported phase mixtures."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_atlas import component_contribution_role, component_scope_note
from check_quality import component_role_matches_architecture
from schema_definition import SCHEMA

class PhaseMixtureArchitectureTests(unittest.TestCase):
    def test_schema_accepts_phase_mixture_without_removing_existing_architectures(self):
        values=SCHEMA['properties']['material']['properties']['architecture']['enum']
        self.assertIn('phase_mixture',values)
        for existing in ('single_material','core_shell','heterostructure','alloy','composite','unresolved'):
            self.assertIn(existing,values)

    def test_builder_assigns_new_role_only_to_phase_mixtures(self):
        self.assertEqual('component_of_phase_mixture',component_contribution_role('phase_mixture'))
        for architecture in ('core_shell','heterostructure'):
            with self.subTest(architecture=architecture):
                self.assertEqual('component_of_heterostructure',component_contribution_role(architecture))
        for architecture in ('composite','alloy','unresolved'):
            self.assertEqual('component_of_product_system',component_contribution_role(architecture))

    def test_quality_validator_matches_role_to_architecture_and_rejects_single_material_component(self):
        self.assertTrue(component_role_matches_architecture('phase_mixture','component_of_phase_mixture'))
        self.assertFalse(component_role_matches_architecture('phase_mixture','component_of_heterostructure'))
        self.assertFalse(component_role_matches_architecture('core_shell','component_of_phase_mixture'))
        self.assertTrue(component_role_matches_architecture('core_shell','component_of_heterostructure'))
        self.assertFalse(component_role_matches_architecture('composite','component_of_heterostructure'))
        self.assertTrue(component_role_matches_architecture('composite','component_of_product_system'))
        self.assertFalse(component_role_matches_architecture('unresolved','component_of_heterostructure'))
        self.assertTrue(component_role_matches_architecture('unresolved','component_of_product_system'))
        self.assertFalse(component_role_matches_architecture('single_material','component_of_heterostructure'))

    def test_phase_mixture_scope_rejects_particle_heterostructure_inference(self):
        note=component_scope_note({'phase_mixture'}).lower()
        self.assertIn('phase component',note)
        self.assertIn('not establish a within-particle heterostructure',note)
        self.assertIn('not standalone',note)
        self.assertNotIn('component of the explicitly named heterostructures below',note)

    def test_other_component_scope_keeps_existing_wording(self):
        self.assertEqual('This material is a component of the explicitly named heterostructures below; these are not standalone pure-material syntheses.',component_scope_note({'core_shell'}))

    def test_unresolved_or_composite_membership_does_not_assign_particle_architecture(self):
        for architecture in ('unresolved','composite','alloy'):
            note=component_scope_note({architecture})
            self.assertNotIn('explicitly named heterostructures',note)
            self.assertIn('does not establish a within-particle arrangement',note)

if __name__=='__main__':unittest.main()
