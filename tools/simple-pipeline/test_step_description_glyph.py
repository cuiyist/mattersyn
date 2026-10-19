"""Pure step-text/substrate regressions; no papers, pair files, model or site writes."""
import ast
import copy
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import unittest


def converter_namespace():
    path = Path(os.environ.get('MATTERSYN_TO_SITE_TEST_MODULE', Path(__file__).with_name('to_site.py')))
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    definitions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign))]
    namespace = {'re': re, 'json': json, 'sys': sys, 'unicodedata': unicodedata, 'Path': Path}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


API = converter_namespace()
BAD_GLYPH = '\U00100010'
SUBSTRATE = '25 × 25 mm ITO-coated glass substrate'


def fixture(reactor):
    document = {'id': 'synthetic', 'doi': '10.0000/synthetic', 'authors': 'Example Author',
                'year': 2026, 'title': 'Synthetic fixture'}
    pair = {'product': 'CdSe', 'structure': {'composition': {'value': 'CdSe', 'page': 2}},
            'recipe': {'reactor': {'value': reactor, 'page': 2},
                'reaction_temperature': {'value': 270, 'unit': 'degC', 'page': 2},
                'reaction_time': {'value': 1, 'unit': 'h', 'page': 2},
                'steps': [{'action': 'cool', 'description': f'Solution is cooled to {n} {BAD_GLYPH}C.',
                           'temperature': n, 'temperature_unit': 'degC', 'page': 2}
                          for n in (270, 140)]}}
    before = copy.deepcopy(pair)
    record = API['Builder'](document).record(pair, 1)
    return record, pair, before


class StepDescriptionGlyphTests(unittest.TestCase):
    def test_only_numeric_actual_degree_glyph_is_normalized(self):
        for value in ('270', '140', '-1.5', '.5'):
            with self.subTest(value=value):
                text = f'Solution is cooled to {value} {BAD_GLYPH}C.'
                self.assertEqual(API['first_upper'](text), f'Solution is cooled to {value} °C.')

    def test_other_glyphs_units_nonnumbers_and_already_correct_text_are_preserved(self):
        cases = (f'Value {BAD_GLYPH}C', f'word270 {BAD_GLYPH}C',
                 f'270 {BAD_GLYPH}K', f'270 {BAD_GLYPH}Celsius',
                 '270 \U000F0010C', '270 8C', '270 °C', 'Ordinary step', '')
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(API['first_upper'](text), text[:1].upper() + text[1:])

    def test_record_label_description_and_typed_temperatures_agree_without_input_mutation(self):
        record, pair, before = fixture('quartz flask')
        self.assertEqual(pair, before)
        for operation, temperature in zip(record['operations'], (270, 140)):
            with self.subTest(temperature=temperature):
                expected = f'Solution is cooled to {temperature} °C.'
                self.assertEqual(operation['label'], expected)
                self.assertEqual(operation['description'], expected)
                self.assertEqual(operation['parameters']['temperature']['value'], temperature)
                self.assertEqual(operation['parameters']['temperature']['unit'], 'degC')
                self.assertTrue(operation['evidence'])
        self.assertEqual(record['quality']['review_status'], 'source_extracted')

    def test_exact_substrate_does_not_become_reactor_but_other_notes_remain(self):
        record, pair, before = fixture(SUBSTRATE)
        self.assertEqual(pair, before)
        self.assertEqual(record['products'][0]['notes'], [
            'Reaction temperature: 270 degC (Main PDF p.2).',
            'Reaction time: 1 h (Main PDF p.2).'])
        self.assertFalse(API['reactor_value_compatible'](SUBSTRATE))
        for previous in ('2 mL distilled water',
                         'thin films of silicon oxide (SiOx) on p-type silicon (111) substrates'):
            with self.subTest(previous=previous):
                self.assertFalse(API['reactor_value_compatible'](previous))

    def test_valid_and_unknown_containing_vessels_are_not_broadened(self):
        for value in ('quartz flask', 'unknown apparatus',
                      SUBSTRATE + ' in a vacuum chamber',
                      'flask containing 2 mL distilled water'):
            with self.subTest(value=value):
                self.assertTrue(API['reactor_value_compatible'](value))
                record, pair, before = fixture(value)
                self.assertEqual(pair, before)
                self.assertEqual(record['products'][0]['notes'][0],
                                 f'Reactor: {value} (Main PDF p.2).')

    def test_substrate_diagram_context_matches_absent_vessel_without_affecting_temperature(self):
        record, _, _ = fixture(SUBSTRATE)
        operation = record['operations'][0]
        svg, caption = API['step_svg'](operation, SUBSTRATE)
        self.assertEqual((svg, caption), API['step_svg'](operation, None))
        self.assertNotIn(SUBSTRATE, svg)
        self.assertNotIn(SUBSTRATE, caption)
        self.assertNotIn(BAD_GLYPH, svg)
        self.assertIn('270 °C', caption)


if __name__ == '__main__':
    unittest.main()
