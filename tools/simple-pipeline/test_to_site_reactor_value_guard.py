"""Pure converter regressions; no pair files, papers, model, or site writes."""
import ast
import copy
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import unittest
import xml.etree.ElementTree as ET


def converter_namespace():
    path = Path(os.environ.get('MATTERSYN_TO_SITE_TEST_MODULE', Path(__file__).with_name('to_site.py')))
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    # Definitions/constants only: exclude module path changes, registry import, CLI, and I/O.
    body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign))]
    scope = {'re': re, 'json': json, 'sys': sys, 'unicodedata': unicodedata, 'Path': Path}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), scope)
    return scope


API = converter_namespace()
BAD_VALUES = ('2 mL distilled water',
              'thin films of silicon oxide (SiOx) on p-type silicon (111) substrates')
OTHER_VALUES = ('10 mL flask containing 2 mL distilled water',
                'sealed vial with distilled water',
                'unidentified apparatus',
                '2 mL distilled water in a glass vessel')
OP = {'label': 'Synthetic heating step', 'action': 'heat',
      'parameters': {'temperature': {'value': 650, 'unit': 'degC'},
                     'duration': {'value': 1, 'unit': 'h'}}}


def record_for(value):
    doc = {'id': 'synthetic', 'doi': '10.0000/synthetic', 'authors': 'Example Author',
           'year': 2026, 'title': 'Synthetic fixture'}
    pair = {'product': 'CdSe', 'structure': {'composition': {'value': 'CdSe', 'page': 2}},
            'recipe': {'reactor': {'value': value, 'page': 2},
                       'reaction_temperature': {'value': 650, 'unit': 'degC', 'page': 2},
                       'reaction_time': {'value': 1, 'unit': 'h', 'page': 2},
                       'steps': [{'action': 'heat', 'description': 'Synthetic heating step',
                                  'temperature': 650, 'temperature_unit': 'degC', 'page': 2}]}}
    before = copy.deepcopy(pair)
    result = API['Builder'](doc).record(pair, 1)
    return result, pair, before


class ReactorValueGuardTests(unittest.TestCase):
    def test_only_known_normalized_nonvessel_forms_are_rejected(self):
        for value in (*BAD_VALUES, '  2  ML\tDISTILLED WATER\n',
                      BAD_VALUES[1].upper()):
            with self.subTest(value=value):
                self.assertFalse(API['reactor_value_compatible'](value))
        for value in (*OTHER_VALUES, None, '', '2mL distilled water', 'quartz tube'):
            with self.subTest(value=value):
                self.assertTrue(API['reactor_value_compatible'](value))

    def test_known_bad_values_do_not_become_product_reactor_notes(self):
        for value in BAD_VALUES:
            with self.subTest(value=value):
                result, pair, before = record_for(value)
                self.assertEqual(pair, before)
                self.assertEqual(result['products'][0]['notes'], [
                    'Reaction temperature: 650 degC (Main PDF p.2).',
                    'Reaction time: 1 h (Main PDF p.2).'])
                self.assertEqual(result['operations'][0]['parameters']['temperature']['value'], 650)
                self.assertEqual(result['quality']['review_status'], 'source_extracted')

    def test_known_bad_values_do_not_become_svg_or_caption_vessels(self):
        expected = API['step_svg'](OP, None)
        for value in BAD_VALUES:
            with self.subTest(value=value):
                svg, caption = API['step_svg'](OP, value)
                self.assertEqual((svg, caption), expected)
                self.assertNotIn(value, svg)
                self.assertNotIn(value, caption)
                self.assertIn('650 °C', caption)
                ET.fromstring(svg)

    def test_valid_and_unknown_vessel_wording_is_preserved(self):
        for value in OTHER_VALUES:
            with self.subTest(value=value):
                result, pair, before = record_for(value)
                self.assertEqual(pair, before)
                self.assertEqual(result['products'][0]['notes'][0],
                                 f'Reactor: {value} (Main PDF p.2).')
                svg, caption = API['step_svg'](OP, value)
                self.assertIn(f'Recipe-level reported vessel: {value}.', caption)
                self.assertIn('650 °C', caption)
                ET.fromstring(svg)


if __name__ == '__main__':
    unittest.main()
