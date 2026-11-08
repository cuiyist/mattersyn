"""Reader entrypoints and their changed structure display share one cache version."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.41.9'
PUBLIC_READER_VERSION = '0.43.0'
PUBLIC_MODULES = ('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'method-families.mjs', 'reader-app.mjs')
H_MODULES = ('chemical-reference-route.mjs', 'chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-app.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-presentation-loader.mjs', 'reader-structures.mjs')
G_HEATER_VERSION = '0.41.10'
G_HEATER_MODULES = ('reported-protocol-scenes.mjs', 'reported-scene-drawing.mjs')
def version_for(module): return PUBLIC_READER_VERSION if module in H_MODULES else '0.42.0' if module in PUBLIC_MODULES or module == 'reader.css' else G_HEATER_VERSION if module in G_HEATER_MODULES else VERSION


class ReaderCacheVersionTests(unittest.TestCase):
    def read(self, rel): return (ROOT / rel).read_text(encoding='utf-8')

    def test_material_and_record_entrypoints_share_current_reader_graph(self):
        template = self.read('templates/material-reader.html')
        self.assertIn(f'reader-app.mjs?v={PUBLIC_READER_VERSION}', template)
        self.assertIn('reader.css?v=' + version_for('reader.css'), template)
        self.assertIn(f'illustrated-record.mjs?v={PUBLIC_READER_VERSION}', self.read('scripts/build_dataset.py'))
        illustrated = self.read('static/illustrated-record.mjs')
        self.assertIn(f'./reader-app.mjs?v={PUBLIC_READER_VERSION}', illustrated)
        self.assertIn(f'./material-guide.mjs?v={PUBLIC_READER_VERSION}', illustrated)

    def test_structure_defaults_and_styles_are_reachable_at_current_version(self):
        expected = {
            'reader-app.mjs': ('reader-structures.mjs', 'reader.css', 'reader-utils.mjs', 'figure-captions.mjs', 'method-families.mjs'),
            'reader-structures.mjs': ('reader-particle.mjs', 'crystal-defaults.mjs'),
            'crystal-viewer.mjs': ('reader-structures.mjs', 'crystal-defaults.mjs'),
            'material-guide.mjs': ('reader-app.mjs', 'crystal-viewer.mjs', 'source-evidence.mjs'),
            'paper-review.mjs': ('source-evidence.mjs', 'figure-captions.mjs'),
            'material-hub.mjs': ('material-guide.mjs',),
        }
        for parent, children in expected.items():
            code = self.read('static/' + parent)
            for child in children:
                with self.subTest(parent=parent, child=child):
                    self.assertIn(child + '?v=' + (version_for(child)), code)
                    self.assertNotIn(child + "'", code)
                    self.assertNotIn(child + '"', code)
            self.assertNotIn('?v=0.41.3', code)
        guide = self.read('static/material-guide.mjs')
        self.assertEqual(guide.count('./crystal-viewer.mjs?v=' + version_for('crystal-viewer.mjs')), 2, 'import and export must refer to one module instance')

    def test_legacy_hub_wrapper_refreshes_only_its_reader_dependency(self):
        builder = self.read('scripts/build_reader_views.py')
        # Execute only the actual pure HTML shell function, without build I/O.
        function = next(node for node in ast.parse(builder).body if isinstance(node, ast.FunctionDef) and node.name == 'shell')
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<synthetic-shell>', 'exec'), namespace)
        self.assertIn('material-hub.mjs?v=' + PUBLIC_READER_VERSION, namespace['shell']('Synthetic', '<p>Fixture</p>', 'material-hub.mjs'))
        self.assertIn('library.mjs?v=0.33.0-r2', namespace['shell']('Synthetic', '<p>Fixture</p>', 'library.mjs'))
        for script in ('paper-review.mjs', 'evidence-gallery.mjs'):
            self.assertIn(script+'?v='+VERSION, namespace['shell']('Synthetic', '<p>Fixture</p>', script))

    def test_archive_builder_passes_plain_gallery_identity_to_shared_shell(self):
        tree = ast.parse(self.read('scripts/build_evidence_views.py'))
        gallery_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'shell' and len(node.args) == 3 and isinstance(node.args[2], ast.Constant)]
        self.assertGreaterEqual(len(gallery_calls), 2)
        for call in gallery_calls:
            self.assertEqual('evidence-gallery.mjs', call.args[2].value)

    def test_loading_text_does_not_call_source_extracted_materials_reviewed(self):
        for rel in ('templates/material-reader.html', 'static/reader-app.mjs'):
            text = self.read(rel)
            self.assertIn('Loading material…', text)
            self.assertNotIn('Loading reviewed material', text)



    def test_connected_reader_parent_imports_have_no_stale_cache_tokens(self):
        for rel in ('templates/material-reader.html', 'scripts/build_dataset.py', 'scripts/build_reader_views.py',
                    'static/atlas-app.mjs', 'static/crystal-viewer.mjs', 'static/illustrated-record.mjs',
                    'static/material-hub.mjs', 'static/material-guide.mjs', 'static/paper-review.mjs',
                    'static/protocol-references.mjs', 'static/reader-app.mjs', 'static/reader-figure-morphology.mjs',
                    'static/reader-particle.mjs', 'static/reader-structures.mjs', 'static/wu2008-reader-context.mjs'):
            with self.subTest(parent=rel):
                text = self.read(rel)
                self.assertIn(PUBLIC_READER_VERSION if rel in ('templates/material-reader.html', 'scripts/build_dataset.py', 'scripts/build_reader_views.py', 'static/illustrated-record.mjs', 'static/material-hub.mjs', 'static/material-guide.mjs', 'static/reader-app.mjs') else version_for(Path(rel).name), text)
                self.assertNotIn('0.41.6', text)
        # Fresh record and legacy-material parents must reach both corrected modules.
        self.assertIn('material-guide.mjs?v=' + PUBLIC_READER_VERSION, self.read('static/illustrated-record.mjs'))
        self.assertIn('material-guide.mjs?v=' + PUBLIC_READER_VERSION, self.read('static/material-hub.mjs'))
        self.assertIn('reader-particle.mjs?v=' + VERSION, self.read('static/reader-structures.mjs'))

    def test_heater_drawing_is_reachable_with_current_child_and_parent_tokens(self):
        expected = {
            'reported-protocol-scenes.mjs': ('reported-scene-drawing.mjs',),
            'protocol-visuals.mjs': ('reported-protocol-scenes.mjs',),
            'reader-app.mjs': ('protocol-visuals.mjs',),
            'material-guide.mjs': ('protocol-visuals.mjs',),
            'illustrated-record.mjs': ('protocol-visuals.mjs',),
        }
        for parent, children in expected.items():
            code = self.read('static/' + parent)
            for child in children:
                with self.subTest(parent=parent, child=child):
                    self.assertEqual(code.count('./' + child + '?v=' + version_for(child)), 1)
                    self.assertNotIn('./' + child + "'", code)
                    self.assertNotIn('./' + child + '"', code)

if __name__ == '__main__': unittest.main()
