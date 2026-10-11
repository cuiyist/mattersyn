"""Reader entrypoints and their changed structure display share one cache version."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.41.5'


class ReaderCacheVersionTests(unittest.TestCase):
    def read(self, rel): return (ROOT / rel).read_text(encoding='utf-8')

    def test_material_and_record_entrypoints_share_current_reader_graph(self):
        template = self.read('templates/material-reader.html')
        self.assertIn(f'reader-app.mjs?v={VERSION}', template)
        self.assertIn(f'reader.css?v={VERSION}', template)
        self.assertIn(f'illustrated-record.mjs?v={VERSION}', self.read('scripts/build_dataset.py'))
        illustrated = self.read('static/illustrated-record.mjs')
        self.assertIn(f'./reader-app.mjs?v={VERSION}', illustrated)
        self.assertIn(f'./material-guide.mjs?v={VERSION}', illustrated)

    def test_structure_defaults_and_styles_are_reachable_at_current_version(self):
        expected = {
            'reader-app.mjs': ('reader-structures.mjs', 'reader.css', 'reader-utils.mjs', 'figure-captions.mjs'),
            'reader-structures.mjs': ('reader-particle.mjs', 'crystal-defaults.mjs'),
            'crystal-viewer.mjs': ('reader-structures.mjs', 'crystal-defaults.mjs'),
            'material-guide.mjs': ('reader-app.mjs', 'crystal-viewer.mjs', 'source-evidence.mjs'),
            'paper-review.mjs': ('source-evidence.mjs',),
            'material-hub.mjs': ('material-guide.mjs',),
        }
        for parent, children in expected.items():
            code = self.read('static/' + parent)
            for child in children:
                with self.subTest(parent=parent, child=child):
                    self.assertIn(child + '?v=' + VERSION, code)
                    self.assertNotIn(child + "'", code)
                    self.assertNotIn(child + '"', code)
            self.assertNotIn('?v=0.41.3', code)
        guide = self.read('static/material-guide.mjs')
        self.assertEqual(guide.count('./crystal-viewer.mjs?v=' + VERSION), 2, 'import and export must refer to one module instance')

    def test_legacy_hub_wrapper_refreshes_only_its_reader_dependency(self):
        builder = self.read('scripts/build_reader_views.py')
        # Execute only the actual pure HTML shell function, without build I/O.
        function = next(node for node in ast.parse(builder).body if isinstance(node, ast.FunctionDef) and node.name == 'shell')
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<synthetic-shell>', 'exec'), namespace)
        self.assertIn('material-hub.mjs?v=' + VERSION, namespace['shell']('Synthetic', '<p>Fixture</p>', 'material-hub.mjs'))
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


if __name__ == '__main__': unittest.main()
