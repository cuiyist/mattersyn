"""One synthetic CLI regression; no model or actual paper data."""
import copy
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
MODULE = HERE / 'mattersyn_simple.py'
spec = importlib.util.spec_from_file_location('simple_title_render_fixture', MODULE)
simple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple)


def has_quotes(value):
    if isinstance(value, dict):
        return any(str(k).casefold() in ('quote', 'quotes') or has_quotes(v) for k, v in value.items())
    return isinstance(value, list) and any(has_quotes(v) for v in value)


class BuildTitleRender(unittest.TestCase):
    def test_cli_singleton_title_is_display_only_and_export_remains_quote_free(self):
        private_quote = 'SYNTHETIC_PRIVATE_QUOTE_NOT_FOR_EXPORT'
        document = {'id': 'synthetic', 'doi': '10.9999/synthetic',
                    'title': ['Synthetic <title> & display'],
                    'authors': [{'given': 'Ada', 'family': 'Lovelace'}],
                    'year': 2001, 'check': 'two passes agree, quotes found', 'figures': [],
                    'pairs': [{'product': 'synthetic particles',
                               'structure': {'composition': {'value': 'InP', 'page': 1, 'quote': private_quote},
                                             'size': {'value': 2.75, 'unit': 'nm', 'page': 1, 'quote': private_quote}},
                               'recipe': {'reaction_temperature': {'value': 123.5, 'unit': 'C', 'page': 2, 'quote': private_quote},
                                          'reaction_time': {'value': 90, 'unit': 'min', 'page': 2, 'quote': private_quote},
                                          'steps': []}}]}
        before = copy.deepcopy(document)
        temporary = tempfile.TemporaryDirectory(prefix='title-render-cli-', dir=HERE)
        root = Path(temporary.name)
        try:
            self.assertEqual(root.resolve().parent, HERE.resolve())
            pairs = root / 'pairs'; pairs.mkdir()
            input_path = pairs / 'synthetic.pairs.json'
            raw = json.dumps(document).encode(); input_path.write_bytes(raw)
            output = root / 'built'
            result = subprocess.run([sys.executable, '-B', str(MODULE), 'build', str(pairs), '--out', str(output)],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            public = json.loads((output / 'pairs.json').read_text(encoding='utf-8'))
            self.assertEqual(public, [simple.public_document(before)])
            self.assertEqual(public[0]['title'], before['title'])
            self.assertEqual(public[0]['pairs'][0]['structure']['size']['value'], 2.75)
            self.assertEqual(public[0]['pairs'][0]['recipe']['reaction_temperature']['value'], 123.5)
            self.assertEqual(public[0]['pairs'][0]['recipe']['reaction_time']['value'], 90)
            self.assertFalse(has_quotes(public))
            self.assertNotIn(private_quote, (output / 'pairs.json').read_text())
            self.assertIn('<h1>' + html.escape(before['title'][0]) + '</h1>', (output / 'p/synthetic.html').read_text())
            self.assertEqual(input_path.read_bytes(), raw)
            self.assertEqual(document, before)
        finally:
            if root.resolve().parent != HERE.resolve():
                raise RuntimeError('Synthetic cleanup target escaped its verified proposal root')
            temporary.cleanup()


if __name__ == '__main__':
    unittest.main(verbosity=2)
