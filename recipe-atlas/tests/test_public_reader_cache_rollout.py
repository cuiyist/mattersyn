"""Tiny generated-entry and reachable-import checks for the future split loader."""
import ast
from pathlib import Path
import re
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.41.9'
PUBLIC_READER_VERSION = '0.48.0'
L_VERSION = '0.46.0'
M_MODULES = ('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'reader-app.mjs', 'reader.css')
H_VERSION = '0.43.0'
K_VERSION = '0.45.0'
K_PATCH_VERSION = '0.45.2'
L_MODULES = ('chemical-reference-route.mjs', 'chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-structures.mjs')
K_PATCH_MODULES = ('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reported-protocol-scenes.mjs')
K_MODULES = ('chemical-viewer.mjs', 'crystal-defaults.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-record-fit.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-particle.mjs', 'reader-structures.mjs', 'reported-protocol-scenes.mjs', 'reported-scene-drawing.mjs', 'source-field-copy.mjs')
PUBLIC_MODULES = ('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'method-families.mjs', 'reader-app.mjs')
H_MODULES = ('chemical-reference-route.mjs', 'chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-app.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-presentation-loader.mjs', 'reader-structures.mjs')
N_VERSION='0.48.0'
N_MODULES=('chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'paper-app.mjs', 'paper-review.mjs', 'particle-shapes.mjs', 'protocol-modules.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-figure-morphology.mjs', 'reader-particle.mjs', 'reader-scoped-product-art.mjs', 'reader-structures.mjs', 'williamson2021-protocol.mjs')
def version_for(module):
    name=module.rsplit('/',1)[-1]
    return N_VERSION if name in N_MODULES else '0.47.1' if name == 'reader.css' else '0.44.0' if name == 'method-families.mjs' else PUBLIC_READER_VERSION if name in M_MODULES else L_VERSION if name in L_MODULES else K_PATCH_VERSION if name in K_PATCH_MODULES else K_VERSION if name in K_MODULES else H_VERSION if name in H_MODULES else VERSION
MODULES = ('illustrated-record.mjs', 'material-hub.mjs', 'material-guide.mjs',
           'reader-app.mjs', 'reader-presentation-loader.mjs', 'method-families.mjs')
EXPECTED = {
    'illustrated-record.mjs': {'reader-app.mjs', 'material-guide.mjs'},
    'material-hub.mjs': {'material-guide.mjs'},
    'material-guide.mjs': {'reader-app.mjs', 'reader-presentation-loader.mjs'},
    'reader-app.mjs': {'reader-presentation-loader.mjs', 'method-families.mjs'},
    'reader-presentation-loader.mjs': set(),
    'method-families.mjs': set(),
}


def module_entry(html):
    entries = re.findall(r'<script\b[^>]*type="module"[^>]*src="([^"]+)"', html)
    if len(entries) != 1:
        raise ValueError('Expected one entry module')
    return entries[0]


def validate_graph(entries, modules):
    expected_entries = [f'{name}?v={version_for(name)}' for name in
                        ('reader-app.mjs', '../illustrated-record.mjs', 'material-hub.mjs')]
    if entries != expected_entries:
        raise ValueError('Stale or inconsistent entry module version')
    edges = {}
    for parent, text in modules.items():
        specifiers = re.findall(r"['\"]\./([^'\"]+\.mjs(?:\?[^'\"]*)?)['\"]", text)
        selected = [item for item in specifiers if item.split('?', 1)[0] in MODULES]
        expected = {f'{name}?v={version_for(name)}' for name in EXPECTED[parent]}
        if set(selected) != expected or len(selected) != len(expected):
            raise ValueError('Stale, duplicated, or missing changed-module import: ' + parent)
        edges[parent] = {item.split('?', 1)[0] for item in selected}
    for entry in entries:
        pending, visited = [entry.rsplit('/', 1)[-1].split('?', 1)[0]], set()
        while pending:
            current = pending.pop()
            if current not in visited:
                visited.add(current)
                pending.extend(edges[current])
        if 'reader-presentation-loader.mjs' not in visited:
            raise ValueError('Entry cannot reach verified split loader')
    return edges


class PublicReaderCacheRollout(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def functions(self):
        tree = ast.parse(self.read('scripts/build_reader_views.py'))
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name in ('shell', 'write_reader_entrypoints')]
        self.assertEqual({node.name for node in selected}, {'shell', 'write_reader_entrypoints'})
        namespace = {'ROOT': ROOT}
        exec(compile(ast.Module(body=selected, type_ignores=[]), '<actual-entry-functions>', 'exec'), namespace)
        return namespace

    def record_entry(self):
        tree = ast.parse(self.read('scripts/build_dataset.py'))
        values = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)
                  and isinstance(node.value, str) and 'illustrated-record.mjs?v=' in node.value]
        self.assertEqual(len(values), 1)
        return module_entry(values[0])

    def graph_inputs(self):
        entries = [module_entry(self.read('templates/material-reader.html')), self.record_entry(),
                   module_entry(self.functions()['shell']('Fixture', '<p>Fixture</p>', 'material-hub.mjs'))]
        modules = {name: self.read('static/' + name) for name in MODULES}
        return entries, modules

    def test_actual_template_function_generates_all_six_fresh_entries(self):
        output = ROOT.parents[1] / 'fixtures' / ('cache-' + uuid4().hex)
        output.mkdir(parents=True, exist_ok=False)
        self.functions()['write_reader_entrypoints'](output)
        files = sorted(output.glob('*.html'))
        self.assertEqual(len(files), 6)
        for file in files:
            with self.subTest(entry=file.name):
                html = file.read_text(encoding='utf-8')
                self.assertEqual(module_entry(html), 'reader-app.mjs?v=' + PUBLIC_READER_VERSION)
                self.assertNotIn('{{READER_CONTEXT}}', html)
                self.assertIn('reader.css?v=0.47.1', html)

    def test_actual_shell_changes_only_material_hub_entry_version(self):
        shell = self.functions()['shell']
        for name, version in (('material-hub.mjs', PUBLIC_READER_VERSION), ('paper-review.mjs', '0.48.0'), ('paper-app.mjs', '0.48.0'),
                              ('evidence-gallery.mjs', '0.41.9'), ('library-app.mjs', '0.33.0-r2')):
            with self.subTest(entry=name):
                self.assertEqual(module_entry(shell('Fixture', '<p>Fixture</p>', name)), name + '?v=' + version)

    def test_actual_record_html_entry_reaches_new_illustrated_module(self):
        self.assertEqual(self.record_entry(), '../illustrated-record.mjs?v=' + PUBLIC_READER_VERSION)

    def test_all_three_entry_routes_reach_one_consistently_versioned_loader(self):
        entries, modules = self.graph_inputs()
        validate_graph(entries, modules)
        loader = './reader-presentation-loader.mjs?v=' + version_for('reader-presentation-loader.mjs')
        for consumer in ('reader-app.mjs', 'material-guide.mjs'):
            self.assertEqual(modules[consumer].count(loader), 1)

    def test_stale_entry_fails_same_reachable_graph_check(self):
        entries, modules = self.graph_inputs()
        entries[0] = 'reader-app.mjs?v=0.41.7'
        with self.assertRaisesRegex(ValueError, 'entry module version'):
            validate_graph(entries, modules)

    def test_stale_or_unversioned_import_fails_same_reachable_graph_check(self):
        entries, modules = self.graph_inputs()
        for parent, before, after in (
            ('illustrated-record.mjs', 'reader-app.mjs?v=0.48.0', 'reader-app.mjs?v=0.41.7'),
            ('material-hub.mjs', 'material-guide.mjs?v=0.48.0', 'material-guide.mjs?v=0.41.7'),
            ('material-guide.mjs', 'reader-presentation-loader.mjs?v=0.43.0', 'reader-presentation-loader.mjs'),
            ('reader-app.mjs', 'reader-presentation-loader.mjs?v=0.43.0', 'reader-presentation-loader.mjs?v=0.41.10'),
            ('reader-app.mjs', 'method-families.mjs?v=0.44.0', 'method-families.mjs'),
        ):
            with self.subTest(parent=parent):
                mutated = dict(modules)
                self.assertEqual(mutated[parent].count(before), 1)
                mutated[parent] = mutated[parent].replace(before, after)
                with self.assertRaisesRegex(ValueError, 'changed-module import'):
                    validate_graph(entries, mutated)


if __name__ == '__main__':
    unittest.main()
