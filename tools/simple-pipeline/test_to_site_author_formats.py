"""Pure stdlib constructor/source regressions; no records, papers or model calls.

Place beside to_site.py. A private proposal can be selected with the
MATTERSYN_TO_SITE_TEST_MODULE environment variable.
"""
import ast
import copy
import os
from pathlib import Path
import re
import unicodedata
import unittest

MODULE = Path(os.environ.get('MATTERSYN_TO_SITE_TEST_MODULE', str(Path(__file__).with_name('to_site.py'))))
tree = ast.parse(MODULE.read_bytes())
slug = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'slug')
builder = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Builder')
methods = [n for n in builder.body if isinstance(n, ast.FunctionDef) and n.name in {'__init__', 'source'}]
if len(methods) != 2:
    raise AssertionError('Expected normal Builder constructor/source methods')
minimal = ast.ClassDef(name='Builder', bases=[], keywords=[], body=methods, decorator_list=[])
module = ast.fix_missing_locations(ast.Module(body=[slug, minimal], type_ignores=[]))
namespace = {'re': re, 'unicodedata': unicodedata}
exec(compile(module, str(MODULE), 'exec'), namespace)
Builder = namespace['Builder']


def document(**extra):
    return {'id': 'fixture', 'doi': '10.0000/fixture', 'year': 2009, 'title': 'Fixture', **extra}


class AuthorFormats(unittest.TestCase):
    def test_lists_equal_exact_joined_string_and_preserve_original(self):
        for authors in (['Ada Lovelace'], ['Ada Lovelace', 'Grace Hopper'],
                        ['Hope T. Beier', 'Gerard L. Coté', 'Kenith E. Meissner'],
                        ['  Ada Lovelace ', ' Grace Hopper  ']):
            with self.subTest(authors=authors):
                original = document(authors=authors)
                before = copy.deepcopy(original)
                actual = Builder(original)
                expected = Builder(document(authors='; '.join(authors)))
                self.assertEqual(actual.source_id, expected.source_id)
                self.assertEqual(actual.source(), expected.source())
                self.assertEqual(original, before)
                self.assertIsNot(actual.doc, original)

    def test_existing_strings_preserve_legacy_source_and_input(self):
        for authors in ('Ada Lovelace', 'Ada Lovelace; Grace Hopper', 'É. Curie and A. Lovelace', ''):
            with self.subTest(authors=authors):
                original = document(authors=authors)
                before = copy.deepcopy(original)
                actual = Builder(original)
                self.assertEqual(actual.source()['authors'], authors or 'not reported')
                self.assertEqual(original, before)
                self.assertIs(actual.doc, original)

    def test_none_and_missing_retain_legacy_fallback(self):
        for original in (document(authors=None), document()):
            with self.subTest(original=original):
                before = copy.deepcopy(original)
                self.assertEqual(Builder(original).source()['authors'], 'not reported')
                self.assertEqual(Builder(original).source_id, Builder(document(authors='')).source_id)
                self.assertEqual(original, before)

    def test_empty_blank_mixed_and_unsupported_representations_refuse(self):
        for authors in ([], [''], [' '], ['Ada Lovelace', None], ['Ada Lovelace', 3], 3, {}, ('Ada Lovelace',)):
            with self.subTest(authors=authors):
                original = document(authors=authors)
                before = copy.deepcopy(original)
                with self.assertRaises(ValueError):
                    Builder(original)
                self.assertEqual(original, before)


if __name__ == '__main__':
    unittest.main()
