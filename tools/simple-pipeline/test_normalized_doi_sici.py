"""Metadata strings only; no real source inputs or converter execution."""
import ast
from pathlib import Path
import re
import unittest

MODULE = Path(__file__).resolve().parent / 'summarize_batch.py'
tree = ast.parse(MODULE.read_bytes())
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'normalized_doi')
namespace = {'re': re}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(MODULE), 'exec'), namespace)
normalized_doi = namespace['normalized_doi']
TITANIA = '10.1002/1521-3862(200010)6:5<239::aid-cvde239>3.0.co;2-q'
NI3N = '10.1002/1521-396x(200202)189:3<691::aid-pssa691>3.0.co;2-3'


class NormalizedDoiTests(unittest.TestCase):
    def test_two_complete_sici_identifiers(self):
        for doi in (TITANIA, NI3N):
            self.assertEqual(normalized_doi(doi), doi)

    def test_existing_prefix_handling_and_casefold(self):
        self.assertEqual(normalized_doi('https://doi.org/' + TITANIA.upper()), TITANIA)
        self.assertEqual(normalized_doi('HTTP://DX.DOI.ORG/' + NI3N.upper()), NI3N)
        self.assertEqual(normalized_doi('doi: ' + TITANIA), TITANIA)

    def test_markup_and_incomplete_sici_rejected(self):
        for value in ('10.1002/test<em>word</em>', TITANIA + '</a>', '<' + TITANIA + '>',
                      TITANIA.replace('::aid-', '::other-'), TITANIA.replace(';2-q', ''),
                      TITANIA.replace('>3.0.co;', '>3.0.;'), TITANIA.replace('239::', '239 ::'),
                      TITANIA.replace('<239', '<239,'), TITANIA.replace(';2-q', ';2-qq')):
            self.assertEqual(normalized_doi(value), '')

    def test_ordinary_and_original_labels_unchanged(self):
        for value, expected in (
            ('10.1021/acs.langmuir.0c02477', '10.1021/acs.langmuir.0c02477'),
            ('10.1023/a:1023013913102', '10.1023/a:1023013913102'),
            ('doi: 10.1234/AbC', '10.1234/abc'),
            ('10.1234/a;b', '10.1234/a;b'), ('10.1234/a,b', '10.1234/a,b'),
            ('not a doi', ''), ('', ''), (None, ''),
        ):
            self.assertEqual(normalized_doi(value), expected)
        old = '10.1002/1521-3862(200010)6_5_239__aid-cvde239_3.3.co;2-h'
        self.assertEqual(normalized_doi(old), old)
        self.assertNotEqual(normalized_doi(old), TITANIA)


if __name__ == '__main__':
    unittest.main()
