"""Normal Source test: pure converter function only; no record conversion or data access."""
import ast
from pathlib import Path
import unittest


def parser():
    tree = ast.parse(Path(__file__).with_name('to_site.py').read_bytes())
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and
             any(isinstance(t, ast.Name) and t.id == 'ELEMENT' for t in n.targets)]
    nodes += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'elements_of']
    env = {}; exec('import re', env)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'converter-pure-function', 'exec'), env)
    return env['elements_of']


class PrintedPhaseElements(unittest.TestCase):
    def test_phase_suffix_is_not_element_boron(self):
        for text in ('TiO2(B)', 'TiO2(B) and anatase', '(TiO2(B))'):
            self.assertEqual(parser()(text), ['Ti', 'O'])

    def test_real_grouped_boron_and_elements_are_preserved(self):
        for text, expected in [('B2O3', ['B', 'O']), ('Ti(BO3)2', ['Ti', 'B', 'O']),
                               ('NaYF4', ['Na', 'Y', 'F']), ('Pt/C', ['Pt', 'C']),
                               ('TiO2(B)/C', ['Ti', 'O', 'C'])]:
            self.assertEqual(parser()(text), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
