import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('simple_temperature_unit_dimension', Path(__file__).with_name('to_site.py'))
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class TemperatureUnitDimensionTest(unittest.TestCase):
    def pair(self, unit='Watts'):
        return {'product': 'ZnS', 'structure': {'composition': {'value': 'ZnS', 'page': 1}},
                'recipe': {'chemicals': [{'name': 'zinc acetate', 'role': 'metal source', 'amount': 0.4, 'unit': 'mmol', 'page': 1}],
                           'steps': [{'action': 'heat', 'description': 'Heat the synthetic mixture', 'temperature': 100,
                                      'temperature_unit': unit, 'time': 5, 'time_unit': 'min', 'page': 1, 'uses': ['zinc acetate']}],
                           'reaction_temperature': {'value': 100, 'unit': unit, 'page': 1},
                           'reaction_time': {'value': 5, 'unit': 'min', 'page': 1}}}

    def record(self, pair):
        doc = {'id': 'synthetic-temperature-fixture', 'doi': '10.9999/temperature-fixture',
               'authors': 'A. Tester', 'year': 2026, 'title': 'Invented regression fixture'}
        return converter.Builder(doc).record(pair, 1)

    def test_power_or_energy_cannot_become_temperature_or_erase_valid_recipe_values(self):
        for unit in ('W', 'Watts', 'power', 'mW', 'kW/cm²', 'laser power (W)', 'eV', 'keV', 'MeV', 'mTorr', 'rpm'):
            with self.subTest(unit=unit):
                pair = self.pair(unit); original = copy.deepcopy(pair)
                record = self.record(pair); operation = record['operations'][0]
                self.assertNotIn('temperature', operation['parameters'])
                duration = operation['parameters']['duration']
                self.assertEqual((duration['value'], duration['unit']), (5, 'min'))
                self.assertEqual(duration['evidence'][0]['locator'], 'Main PDF p.1')
                amount = record['materials'][0]['quantities']['amount']
                self.assertEqual((amount['value'], amount['unit']), (0.4, 'mmol'))
                notes = '\n'.join(record['products'][0]['notes'])
                self.assertNotIn('Reaction temperature:', notes)
                self.assertIn('Reaction time: 5 min', notes)
                svg, caption = converter.step_svg(operation, None)
                self.assertNotIn('temperature:', svg)
                self.assertNotIn('temperature:', caption)
                self.assertIn('duration: 5 min', svg)
                self.assertIn('duration: 5 min', caption)
                ET.fromstring(svg)
                self.assertEqual(record['quality']['review_status'], 'source_extracted')
                self.assertEqual(pair, original)

    def test_temperature_units_keep_their_values_locators_and_diagrams(self):
        for unit, canonical, displayed in (('°C', 'degC', '°C'), ('degC', 'degC', '°C'),
                                            ('K', 'K', 'K'), ('°F', '°F', '°F'), ('mK', 'mK', 'mK')):
            with self.subTest(unit=unit):
                record = self.record(self.pair(unit)); operation = record['operations'][0]
                temperature = operation['parameters']['temperature']
                self.assertEqual((temperature['value'], temperature['unit']), (100, canonical))
                self.assertEqual(temperature['evidence'][0]['locator'], 'Main PDF p.1')
                self.assertEqual(operation['parameters']['duration']['value'], 5)
                self.assertIn('Reaction temperature: 100', '\n'.join(record['products'][0]['notes']))
                svg, caption = converter.step_svg(operation, None)
                self.assertIn('temperature: 100 ' + displayed, svg)
                self.assertIn('temperature: 100 ' + displayed, caption)
                ET.fromstring(svg)

    def test_existing_missing_unit_temperature_behavior_is_preserved(self):
        pair = self.pair(); del pair['recipe']['steps'][0]['temperature_unit']
        record = self.record(pair)
        temperature = record['operations'][0]['parameters']['temperature']
        self.assertEqual((temperature['value'], temperature['unit']), (100, 'degC'))

    def test_svg_defends_legacy_invalid_temperature_without_mutating_it(self):
        operation = {'action': 'heat', 'label': 'Heat the synthetic mixture',
                     'parameters': {'temperature': {'value': 100, 'unit': 'Watts'},
                                    'duration': {'value': 5, 'unit': 'min'}}}
        original = copy.deepcopy(operation)
        svg, caption = converter.step_svg(operation, None)
        self.assertNotIn('temperature:', svg)
        self.assertNotIn('Watts', svg)
        self.assertNotIn('temperature:', caption)
        self.assertNotIn('Watts', caption)
        self.assertIn('duration: 5 min', svg)
        self.assertIn('duration: 5 min', caption)
        self.assertIn('Conceptual action diagram', caption)
        ET.fromstring(svg)
        self.assertEqual(operation, original)


if __name__ == '__main__':
    unittest.main()
