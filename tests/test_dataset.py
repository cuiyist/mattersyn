"""Scientific integrity and training leakage regression tests. Synthetic fixtures are not data."""
import sys
sys.dont_write_bytecode = True
import copy
import json
import os
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / 'scripts'))
from record_helpers import ev, fact, qty, source, record, material, operation, state, product, measurement
from dataset_lib import validate_record, eligibility, training_view, build_groups, chemical_signature


def fixture(record_id='test-a'):
    """Schema-valid synthetic recipe: not a claim about a published experiment."""
    src = source('synthetic-source', '10.0000/synthetic-test', 'Synthetic unit-test fixture', 'Test fixture', 2000)
    evidence = ev(src['id'], 'Synthetic fixture, protocol and sample A')
    r = record(record_id, 'Synthetic fixture', 'ZnO', 'test', 'aqueous synthesis', src, 'Synthetic fixture')
    r['quality']['experimental_outcome'] = 'reported_product'
    r['quality']['missing_fields'] = ['No exact sample coordinates']
    r['materials'] = [
        material('zinc', 'zinc precursor', 'ZnCl2', 'metal_precursor', 'synthesis', evidence),
        material('water', 'water', 'H2O', 'solvent', 'synthesis', evidence),
    ]
    r['stocks'] = [{
        'id': 'stock-a', 'name': 'Synthetic stock',
        'components': [{'material_id': 'zinc', 'quantities': {'amount': qty(1, 'mmol', evidence)}},
                       {'material_id': 'water', 'quantities': {'volume': qty(10, 'mL', evidence)}}],
        'concentrations': {}, 'preparation_operation_ids': ['prepare-stock'],
        'scope': 'Synthetic stock with quantities stored here, not duplicated as operation parameters.',
        'evidence': evidence,
    }]
    r['material_states'] = [state('product-state', 'Product', ['stock-a'], kind='product')]
    r['operations'] = [
        operation('prepare-stock', 'dissolve', 'Prepare stock', evidence, ['zinc', 'water'], ['stock-a'], stage='precursor_preparation'),
        operation('react', 'heat', 'React', evidence, ['stock-a'], ['product-state'], depends=['prepare-stock'], parameters={'temperature': qty(80, 'degC', evidence)}),
    ]
    p = product('sample-a', 'ZnO', evidence, link='explicit', state='product-state', phase='wurtzite')
    p['source_sample_label'] = 'A'
    r['products'] = [p]
    for op in r['operations']:
        op['environment']=fact('ambient air',evidence)
        op['endpoint']=fact('specified endpoint',evidence)
    r['measurements'] = [measurement('diameter-a', 'sample-a', 'diameter', qty(3.8, 'nm', evidence), 'TEM', evidence)]
    return r


def reorigin(r, record_id, source_id, doi):
    """Same scientific payload, different independent documentary origin."""
    r = copy.deepcopy(r)
    old = r['sources'][0]['id']
    r['record_id'] = record_id
    r['sources'][0]['id'] = source_id
    r['sources'][0]['doi'] = doi
    r['sources'][0]['url'] = 'https://doi.org/' + doi
    r['lineage']['source_group'] = source_id
    r['lineage']['recipe_family'] = source_id + '-family'
    def recurse(x):
        if isinstance(x, dict):
            if x.get('source_id') == old: x['source_id'] = source_id
            for value in x.values(): recurse(value)
        elif isinstance(x, list):
            for value in x: recurse(value)
    recurse(r)
    return r


def add_optical_benchmark_features(r):
    """Synthetic values for the supported published-experiment feature contract."""
    e=ev('synthetic-source','Synthetic published benchmark row')
    values={
        'ambient_temperature_proxy':(20,'degC'),
        'lead_oleate_stock_volume':(1,'mL'),
        'ode_reaction_volume':(10,'mL'),
        'oleylamine_volume':(1,'mL'),
        'injection_temperature':(100,'degC'),
        'bis_trimethylsilyl_sulfide_volume':(0.1,'mL'),
        'ode_sulfur_stock_volume':(1,'mL'),
        'chloride_high_temperature_concentration':(0,'mol/L'),
        'chloride_60c_concentration':(0,'mol/L'),
    }
    r['operations'].append(operation('benchmark-features','published_experiment_features','Synthetic benchmark features',e,[],[],parameters={name:qty(value,unit,e) for name,(value,unit) in values.items()}))


class CanonicalRecordTests(unittest.TestCase):
    def test_current_canonical_records_validate(self):
        files = sorted((SITE / 'data/records').glob('*.json'))
        self.assertTrue(files, 'Expected existing canonical records')
        for path in files:
            with self.subTest(record=path.name):
                self.assertEqual([], validate_record(json.loads(path.read_text(encoding='utf-8-sig'))))

    def test_murray_small_species_stays_out_of_size_training(self):
        path = SITE / 'data/records/murray-1993-cdse-small-species.json'
        r = json.loads(path.read_text(encoding='utf-8-sig'))
        self.assertFalse(eligibility(r)['size_conditioned_recipe']['eligible'])


class MissingnessAndStructureTests(unittest.TestCase):
    def test_missing_quantity_is_null_in_training_export(self):
        r = fixture()
        r['operations'][-1]['parameters']['duration'] = qty(unit='min', evidence=ev('synthetic-source', 'Unreported in fixture'))
        self.assertEqual([], validate_record(r))
        exported = training_view(r, 'partial_protocol')['output']['operations'][-1]['parameters']['duration']
        self.assertIsNone(exported['value'])
        self.assertEqual('not_reported', exported['status'])

    def test_missing_status_must_not_contain_zero(self):
        r = fixture()
        r['operations'][-1]['parameters']['duration'] = qty(0, 'min', ev('synthetic-source', 'Fixture'), status='not_reported')
        self.assertTrue(validate_record(r))

    def test_reported_zero_remains_valid_zero(self):
        r = fixture()
        r['operations'][-1]['parameters']['temperature'] = qty(0, 'degC', ev('synthetic-source', 'Fixture'))
        self.assertEqual([], validate_record(r))
        self.assertEqual(0, training_view(r, 'partial_protocol')['output']['operations'][-1]['parameters']['temperature']['value'])

    def test_unresolved_diameter_is_not_eligible(self):
        r = fixture()
        r['measurements'][0]['value'] = qty(unit='nm', evidence=ev('synthetic-source', 'Unreported'))
        self.assertFalse(eligibility(r)['size_conditioned_recipe']['eligible'])

    def test_external_reference_cif_cannot_enable_exact_structure_task(self):
        r = fixture()
        r['quality']['missing_fields'] = []
        r['structure_assets'] = [{'id':'reference', 'role':'external_reference', 'sample_id':None, 'url':'https://example.invalid/reference.cif', 'description':'Synthetic external bulk reference', 'eligible_as_measured_label':False}]
        self.assertEqual([], validate_record(r))
        self.assertFalse(eligibility(r)['exact_structure_recipe']['eligible'])

    def test_external_cif_marked_as_measured_is_rejected(self):
        r = fixture()
        r['structure_assets'] = [{'id':'reference', 'role':'external_reference', 'sample_id':'sample-a', 'url':'https://example.invalid/reference.cif', 'description':'Invalid fixture: external reference misused as measured sample', 'eligible_as_measured_label':True}]
        self.assertTrue(validate_record(r))

    def test_empty_missing_fields_summary_cannot_hide_unknown_required_condition(self):
        r = fixture()
        r['quality']['missing_fields'] = []
        r['operations'][-1]['parameters']['temperature'] = qty(unit='degC', evidence=ev('synthetic-source', 'Unreported reactor temperature'))
        r['structure_assets'] = [{'id':'measured', 'role':'measured_sample', 'sample_id':'sample-a', 'url':'https://example.invalid/measured.cif', 'description':'Synthetic measured fixture', 'eligible_as_measured_label':True}]
        self.assertEqual([], validate_record(r))
        self.assertFalse(eligibility(r)['exact_structure_recipe']['eligible'], 'An empty manual summary must not override an explicitly unknown reaction temperature')


class ReferenceAndGraphTests(unittest.TestCase):
    def test_unknown_operation_input_is_rejected(self):
        r = fixture()
        r['operations'][-1]['inputs'] = ['does-not-exist']
        self.assertTrue(validate_record(r))

    def test_blank_material_identifier_is_rejected(self):
        r = fixture()
        r['materials'][0]['id'] = ''
        r['stocks'][0]['components'][0]['material_id'] = ''
        r['operations'][0]['inputs'][0] = ''
        self.assertTrue(validate_record(r), 'A consistently blank ID is still invalid')

    def test_duplicate_source_identifiers_are_rejected(self):
        r = fixture()
        conflicting_source = copy.deepcopy(r['sources'][0])
        conflicting_source['doi'] = '10.0000/different-document'
        r['sources'].append(conflicting_source)
        self.assertTrue(validate_record(r), 'Evidence cannot resolve two different documents under one source ID')

    def test_source_group_must_resolve_to_primary_source(self):
        r = fixture()
        r['lineage']['source_group'] = 'unknown-primary-source'
        self.assertTrue(validate_record(r), 'Otherwise DOI-based grouping can silently omit the actual primary source')

    def test_material_state_cycle_is_rejected(self):
        r = fixture()
        r['material_states'] += [state('cycle-a','A',['cycle-b']),state('cycle-b','B',['cycle-a'])]
        self.assertTrue(validate_record(r))

    def test_measurement_derivation_cycle_is_rejected(self):
        r = fixture()
        other = copy.deepcopy(r['measurements'][0])
        other['id'] = 'diameter-b'
        other['derives_from'] = ['diameter-a']
        r['measurements'][0]['derives_from'] = ['diameter-b']
        r['measurements'].append(other)
        self.assertTrue(validate_record(r), 'A->B->A is a cycle even when neither node directly refers to itself')

    def test_product_parent_cycle_is_rejected(self):
        r = fixture()
        other = copy.deepcopy(r['products'][0])
        other['sample_id'] = 'sample-b'
        other['parent_sample_id'] = 'sample-a'
        r['products'][0]['parent_sample_id'] = 'sample-b'
        r['products'].append(other)
        self.assertTrue(validate_record(r))

    def test_nonexistent_retained_fraction_is_rejected(self):
        r = fixture()
        r['operations'][-1]['retained_fraction'] = 'nonexistent-pellet'
        self.assertTrue(validate_record(r), 'The selected material fraction must resolve to an actual output/state')

    def test_consuming_a_stock_before_its_preparation_is_rejected(self):
        r = fixture()
        # Explicit depends_on is missing, but input stock still names its producer.
        r['operations'][1]['depends_on'] = []
        r['operations'].reverse()
        self.assertTrue(validate_record(r), 'A declared stock input cannot be consumed before its preparation operation')


class DeduplicationAndGroupingTests(unittest.TestCase):
    def test_duplicate_marked_record_is_excluded_from_supervised_exports(self):
        r = fixture('duplicate-a')
        r['lineage']['duplicate_of'] = 'original-a'
        self.assertTrue(all(not entry['eligible'] for entry in eligibility(r).values()))

    def test_same_doi_variants_cannot_cross_groups(self):
        a = fixture()
        b = reorigin(a,'test-b','other-local-source-id','10.0000/SYNTHETIC-TEST')
        b['operations'][-1]['parameters']['temperature']['value'] = 90
        groups = build_groups([a,b])
        self.assertEqual(groups[a['record_id']], groups[b['record_id']])

    def test_parent_and_duplicate_lineage_is_transitively_grouped(self):
        a = fixture()
        b = reorigin(a,'test-b','source-b','10.0000/b')
        c = reorigin(a,'test-c','source-c','10.0000/c')
        b['operations'][-1]['parameters']['temperature']['value'] = 90
        c['operations'][-1]['parameters']['temperature']['value'] = 100
        b['lineage']['parent_record_id'] = a['record_id']
        c['lineage']['duplicate_of'] = b['record_id']
        groups = build_groups([c,a,b])
        self.assertEqual(1, len(set(groups.values())))

    def test_material_array_order_does_not_change_recipe_signature(self):
        a = fixture()
        b = copy.deepcopy(a)
        b['materials'].reverse()
        self.assertEqual(chemical_signature(a),chemical_signature(b), 'Material inventory is unordered; permutation is not a new recipe')

    def test_copied_recipe_with_permuted_materials_cannot_cross_groups(self):
        a = fixture()
        b = reorigin(a,'test-b','source-b','10.0000/b')
        b['materials'].reverse()
        groups = build_groups([a,b])
        self.assertEqual(groups[a['record_id']],groups[b['record_id']])

    def test_stock_quantity_changes_affect_recipe_signature(self):
        a = fixture()
        b = copy.deepcopy(a)
        b['stocks'][0]['components'][0]['quantities']['amount']['value'] = 2
        self.assertNotEqual(chemical_signature(a),chemical_signature(b), 'Twofold precursor loading is a chemically meaningful recipe difference')


class TrainingViewLeakageTests(unittest.TestCase):
    def test_recipe_inputs_exclude_measured_outcome_text_and_assets(self):
        r = fixture()
        marker='MEASURED_OUTCOME_ONLY_987654'
        r['measurements'][0]['conditions']=marker
        r['products'][0]['notes'].append(marker)
        r['structure_assets']=[{'id':'illustration','role':'illustrative','sample_id':None,'url':'https://example.invalid/'+marker,'description':marker,'eligible_as_measured_label':False}]
        inputs=training_view(r,'partial_protocol')['input']
        self.assertNotIn(marker,json.dumps(inputs))

    def test_characterization_steps_are_not_recipe_output_steps(self):
        r=fixture()
        e=ev('synthetic-source','Synthetic post-synthesis characterization')
        r['operations'].append(operation('characterize','measure','Measure final PL',e,['product-state'],[],stage='characterization',parameters={'measured_peak':qty(987.654,'nm',e)}))
        exported=training_view(r,'partial_protocol')['output']['operations']
        self.assertNotIn('characterize',[o['id'] for o in exported], 'Synthesis feedback operations may remain; standalone final characterization is not a synthesis instruction')

    def test_optical_target_uses_explicitly_linked_measurement(self):
        r=fixture()
        add_optical_benchmark_features(r)
        e=ev('synthetic-source','Synthetic optical results')
        unknown=product('unresolved-sample','ZnO',e,link='unresolved')
        r['products'].append(unknown)
        r['measurements']=[measurement('unknown-abs','unresolved-sample','absorption_peak',qty(999,'nm',e),'absorption',e),measurement('linked-abs','sample-a','absorption_peak',qty(350,'nm',e),'absorption',e)]
        r['quality']['requested_tasks'].append('optical_outcome')
        self.assertEqual([],validate_record(r))
        self.assertTrue(eligibility(r)['optical_outcome']['eligible'])
        self.assertEqual(350,training_view(r,'optical_outcome')['output']['absorption_peak']['value'])

    def test_optical_features_exclude_characterization_target_values(self):
        r=fixture()
        add_optical_benchmark_features(r)
        e=ev('synthetic-source','Synthetic optical results')
        r['quality']['requested_tasks'].append('optical_outcome')
        r['measurements']=[measurement('linked-abs','sample-a','absorption_peak',qty(350,'nm',e),'absorption',e)]
        # A separately prepared characterization specimen may precede recipe operations
        # in serialized source order; stage, not array index, defines its role.
        r['operations'].insert(0,operation('characterize','measure','Independent reported characterization',e,[],[],stage='characterization',parameters={'measured_absorption_peak':qty(350,'nm',e)}))
        self.assertEqual([],validate_record(r))
        self.assertTrue(eligibility(r)['optical_outcome']['eligible'])
        features=training_view(r,'optical_outcome')['input']['features']
        self.assertNotIn('measured_absorption_peak',features)

    def test_exact_structure_export_actually_contains_measured_structure_input(self):
        r=fixture()
        r['quality']['missing_fields']=[]
        url='https://example.invalid/measured-sample-structure.cif'
        r['structure_assets']=[{'id':'measured','role':'measured_sample','sample_id':'sample-a','url':url,'description':'Synthetic measured fixture','eligible_as_measured_label':True}]
        self.assertTrue(eligibility(r)['exact_structure_recipe']['eligible'])
        exported=training_view(r,'exact_structure_recipe')
        self.assertIn(url,json.dumps(exported['input']), 'A structure-conditioned training example cannot silently contain only composition and method')


if __name__=='__main__':
    unittest.main(verbosity=2)
