"""Material-page first view: record order, route names for generic methods, common names."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from material_names import common_name  # noqa: E402
from route_labels import completeness, reader_sort_key, route_label  # noqa: E402


def q(value, unit, status='reported'):
    return {'value': value, 'minimum': None, 'maximum': None, 'unit': unit, 'status': status}


def op(action, label='', temperature=None, environment=None, **params):
    parameters = dict(params)
    if temperature is not None:
        parameters['temperature'] = q(temperature, 'degC')
    return {'action': action, 'label': label, 'parameters': parameters,
            'environment': {'value': environment, 'status': 'reported' if environment else 'not_reported'}}


def material(name, role, **quantities):
    return {'name': name, 'role': role, 'quantities': quantities}


def record(operations, materials=(), method='Synthesis as described in the source', status='source_extracted', products=(), measurements=()):
    return {'method': method, 'operations': list(operations), 'materials': list(materials), 'products': list(products),
            'measurements': list(measurements), 'quality': {'review_status': status}}


class RouteLabelTest(unittest.TestCase):
    def test_injection_into_a_hot_solution_is_hot_injection(self):
        r = record([op('heat', temperature=300), op('inject', 'inject TOP-Se'), op('cool')])
        self.assertEqual(route_label(r), 'Hot injection')
        self.assertEqual(route_label(record([op('inject', 'injection into hot oleylamine')])), 'Hot injection')

    def test_room_temperature_or_quench_injection_is_not_hot_injection(self):
        self.assertEqual(route_label(record([op('stir', temperature=25), op('inject', 'inject precursor')])), '')
        self.assertEqual(route_label(record([op('heat', temperature=300), op('inject', 'inject cold toluene to quench')])), '')
        self.assertEqual(route_label(record([op('heat', temperature=300), op('cool', temperature=25), op('inject', 'inject Se')])), '')

    def test_autoclave_with_water_or_organic_solvent(self):
        steps = [op('add', 'transfer to a Teflon-lined autoclave'), op('heat', temperature=180)]
        self.assertEqual(route_label(record(steps, [material('deionized water', 'solvent')])), 'Hydrothermal')
        self.assertEqual(route_label(record(steps, [material('ethylene glycol', 'solvent')])), 'Solvothermal')
        self.assertEqual(route_label(record(steps, [material('water', 'solvent'), material('ethanol', 'solvent')])), '')

    def test_explicit_technique_and_beam_flux(self):
        self.assertEqual(route_label(record([op('grow', 'MBE growth of InAs')])), 'Molecular beam epitaxy')
        self.assertEqual(route_label(record([op('grow', 'grow GaAs buffer', environment='As4')])), 'Molecular beam epitaxy')
        self.assertEqual(route_label(record([op('deposit', 'deposit GaAs')])), '')

    def test_heat_up_requires_combined_reagents_and_no_hot_addition(self):
        mats = [material('CdO', 'metal_precursor'), material('S', 'chalcogen_precursor'), material('1-octadecene', 'solvent')]
        self.assertEqual(route_label(record([op('mix'), op('heat', temperature=240)], mats)), 'Heat-up')
        self.assertEqual(route_label(record([op('heat', temperature=240)], mats)), '')
        self.assertEqual(route_label(record([op('mix'), op('heat', temperature=240), op('add', 'add shell precursor')], mats)), '')

    def test_only_generic_methods_get_a_route_name(self):
        self.assertEqual(route_label(record([op('heat', temperature=300), op('inject')], method='Heat-up')), '')
        self.assertEqual(route_label(record([op('heat', temperature=300), op('inject')], method='Other')), 'Hot injection')


    def test_thermal_decomposition_fallback_requires_a_synthesis_step(self):
        self.assertEqual(route_label(record([op('heat', 'Thermal decomposition of a metal precursor', temperature=250)])), 'Thermal decomposition')
        self.assertEqual(route_label(record([op('decompose', 'Decompose the precursor', temperature=300)])), 'Thermal decomposition')
        self.assertEqual(route_label(record([op('heat', 'Pyrolysis in ammonia', temperature=300)])), 'Thermal decomposition')
        self.assertEqual(route_label(record([op('wash', 'Wash to remove decomposition products')])), '')
        self.assertEqual(route_label(record([op('cool', 'Cooled after pyrolysis')])), '')
        self.assertEqual(route_label(record([op('heat', 'Heat slowly to prevent thermal decomposition', temperature=250)])), '')
        self.assertEqual(route_label(record([op('synthesize', 'Synthesize selenium precursor by thermal decomposition')])), '')

    def test_chemical_reduction_fallback_requires_its_own_positive_step(self):
        mats = [material('metal salt', 'metal_precursor')]
        self.assertEqual(route_label(record([op('reduce', 'Reduce metal ions')], mats)), 'Chemical reduction')
        self.assertEqual(route_label(record([op('add', 'Add reductant to reduce metal ions')], mats)), 'Chemical reduction')
        self.assertEqual(route_label(record([op('heat', 'Heat under reduced pressure')], mats)), '')
        self.assertEqual(route_label(record([op('reduce', 'Reduce particle size')], mats)), '')
        self.assertEqual(route_label(record([op('wash', 'Wash the reduced particles')], mats)), '')
        self.assertEqual(route_label(record([op('react', 'React without reduction of the metal ions')], mats)), '')
        self.assertEqual(route_label(record([op('add', 'Add previously reduced metal nanoparticles')], mats)), '')
        self.assertEqual(route_label(record([op('heat', 'Heat the reduced metal nanoparticles')], mats)), '')
        self.assertEqual(route_label(record([op('reduce', 'Reduce the metal salt concentration by dilution')], mats)), '')
        self.assertEqual(route_label(record([op('mix')], mats + [material('NaBH4', 'reducing_agent')])), '')

    def test_reflux_fallback_requires_precursors_not_purification(self):
        mats = [material('metal salt', 'metal_precursor'), material('sulfide', 'chalcogen_precursor')]
        self.assertEqual(route_label(record([op('reflux', 'Reflux the reaction mixture')], mats)), 'Reflux')
        self.assertEqual(route_label(record([op('heat', 'Heat and reflux the solution', temperature=100)], mats)), 'Reflux')
        self.assertEqual(route_label(record([op('reflux', 'Reflux to remove impurities')], mats)), '')
        self.assertEqual(route_label(record([op('reflux', 'Prepare tetrameric precursor')], mats)), '')
        self.assertEqual(route_label(record([op('reflux', 'Reflux QDs for ligand exchange')], mats)), '')
        self.assertEqual(route_label(record([op('sonicate', 'Sonicate the dispersion')], mats)), '')
        self.assertEqual(route_label(record([op('heat', 'Heat the mixture without reflux')], mats)), '')
        self.assertEqual(route_label(record([op('heat', 'Precursor preparation under reflux')], mats)), '')
        self.assertEqual(route_label(record([op('reflux', 'Reflux the precursor to prepare a stock solution')], mats)), '')
        self.assertEqual(route_label(record([op('reflux', 'Reflux without a reduction step')], mats)), 'Reflux')

    def test_existing_routes_and_ambiguous_autoclaves_keep_precedence(self):
        mats = [material('metal salt', 'metal_precursor'), material('sulfide', 'chalcogen_precursor')]
        self.assertEqual(route_label(record([op('heat', 'Hydrothermal chemical reduction')], mats)), 'Hydrothermal')
        steps = [op('heat', 'React in a Teflon-lined autoclave'), op('reduce', 'Reduce metal ions')]
        self.assertEqual(route_label(record(steps, mats + [material('water', 'solvent'), material('ethanol', 'solvent')])), '')


class OrderTest(unittest.TestCase):
    def test_completeness_counts_amounts_conditions_size_phase_morphology(self):
        r = record([op('heat', temperature=200, duration=q(10, 'min')), op('cool'), op('stir', environment='N2')],
                   [material('CdO', 'metal_precursor', mass=q(1, 'g')), material('Se', 'chalcogen_precursor', purity=q(99, '%')),
                    material('ODE', 'solvent', volume=q(None, 'mL', 'not_reported'))],
                   products=[{'sample_id': 's1', 'phase': {'status': 'reported'}, 'morphology': {'status': 'not_reported'}}],
                   measurements=[{'property': 'diameter', 'sample_id': 's1', 'value': q(3.1, 'nm')}])
        self.assertEqual(completeness(r), 1 + 2 + 1 + 1)

    def test_reviewed_first_then_score_then_previous_order(self):
        rows = {
            'old-extracted': (record([], status='source_extracted'), True, 9, (1991, 0, 'a')),
            'reviewed-low': (record([], status='source_reviewed'), True, 1, (2005, 0, 'b')),
            'reviewed-high': (record([], status='source_reviewed'), True, 5, (2010, 0, 'c')),
            'reviewed-tie': (record([], status='structured_data_verified'), True, 5, (2012, 0, 'd')),
            'component': (record([], status='source_reviewed'), False, 50, (1990, 0, 'e')),
        }
        order = sorted(rows, key=lambda rid: reader_sort_key(*rows[rid]))
        self.assertEqual(order, ['reviewed-high', 'reviewed-tie', 'reviewed-low', 'old-extracted', 'component'])


class NameTest(unittest.TestCase):
    def test_common_names_or_formula_alone(self):
        self.assertEqual(common_name('GaAs'), 'Gallium arsenide')
        self.assertEqual(common_name('Au'), 'Gold')
        self.assertEqual(common_name('InP/ZnS'), 'InP/ZnS')
        self.assertEqual(common_name('Cu-Zn-In-S'), 'Cu-Zn-In-S')

    def test_built_names_never_end_in_literature_collection(self):
        source = (Path(__file__).resolve().parents[1] / 'scripts/build_atlas.py').read_text(encoding='utf-8')
        self.assertNotIn("+' literature collection'", source)
        self.assertIn("'name':NAMES.get(formula) or common_name(formula)", source)


if __name__ == '__main__':
    unittest.main()
