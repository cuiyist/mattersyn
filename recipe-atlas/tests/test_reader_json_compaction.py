"""Synthetic Reader serialization checks; no real papers, server or release inputs."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONVERTER = load('compaction_converter', 'tools/simple-pipeline/to_site.py')
CAPTIONS = load('compaction_captions', 'tools/simple-pipeline/local_caption_backfill.py')
REGISTRY = load('compaction_registry', 'recipe-atlas/scripts/reader_presentation_registry.py')


def sample():
    return {
        'records': {
            'audited-example': {
                'source_id': 'audited-source', 'review_status': 'source_reviewed',
                'scopeLabel': 'Audited synthetic example', 'figures': [{
                    'id': 'figure-2', 'public_caption': 'Synthetic µm description with a "quoted" label.\nSecond line.',
                    'source_locator': {'page': 4, 'figure': 'Figure 2'},
                    'permission_status': 'unverified', 'license': None,
                    'public_asset_sha256': 'a' * 64,
                }],
            },
            'extracted-example': {
                'source_id': 'extracted-source', 'review_status': 'source_extracted',
                'scopeLabel': 'Machine-extracted, not independently audited',
                'figures': [], 'values': [1.0, 1e-7, 9007199254740993, False, None],
            },
        },
        'materials': {'example': {'record_ids': ['audited-example', 'extracted-example']}},
        'figures_by_source': {},
    }


def assert_same(test, raw, value):
    parsed = json.loads(raw.decode('utf-8-sig'))
    test.assertEqual(parsed, value)
    original = json.dumps(value, ensure_ascii=False)
    test.assertEqual(json.loads(raw.decode('utf-8-sig'), object_pairs_hook=list),
                     json.loads(original, object_pairs_hook=list))


def emit_build_projection(target, source, data, view):
    """Execute only the real builder's serialization expression on fixtures."""
    tree = ast.parse((ROOT / 'recipe-atlas/scripts/build_reader_metadata.py').read_text(encoding='utf-8'))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    candidates = [node for node in main.body if isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.IfExp)
                  and isinstance(node.value.body, ast.Call)
                  and isinstance(node.value.body.func, ast.Attribute)
                  and node.value.body.func.attr == 'write_bytes']
    if len(candidates) != 1:
        raise AssertionError('Expected one unchanged identity/filtered serialization branch')
    code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(candidates[0])], type_ignores=[])),
                   '<synthetic-reader-serialization>', 'exec')
    exec(code, {'target': target, 'source': source, 'data': data, 'view': view,
                'json': json, 'source_paths': REGISTRY.source_paths})


class ReaderJsonCompactionTests(unittest.TestCase):
    def test_converter_compacts_only_reader_and_preserves_complete_values_and_order(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            path = Path(tmp) / 'reader-presentation-reviewed.json'
            value = sample()
            pretty = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
            path.write_bytes(pretty)
            CONVERTER.dump_like(path, value)
            compact = path.read_bytes()
            assert_same(self, compact, value)
            self.assertLess(len(compact), len(pretty))
            self.assertEqual(compact, (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode())

    def test_converter_keeps_generic_record_json_bytes_exact(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            path = Path(tmp) / 'audited-record.json'
            value = sample()['records']['audited-example']
            expected = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
            path.write_bytes(expected)
            CONVERTER.dump_like(path, value)
            self.assertEqual(path.read_bytes(), expected)

    def test_converter_preserves_crlf_and_optional_final_newline(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            path = Path(tmp) / 'reader-presentation-reviewed.json'
            value = sample()
            path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\r\n').replace('\n', '\r\n').replace('\r\r\n', '\r\n').encode())
            CONVERTER.dump_like(path, value)
            self.assertTrue(path.read_bytes().endswith(b'\r\n'))
            assert_same(self, path.read_bytes(), value)
            path.write_bytes(json.dumps(value, ensure_ascii=False).encode())
            CONVERTER.dump_like(path, value)
            self.assertFalse(path.read_bytes().endswith(b'\n'))
            assert_same(self, path.read_bytes(), value)

    def test_nearby_filename_does_not_minify_generic_json(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            path = Path(tmp) / 'reader-presentation-reviewed-other.json'
            value = sample()
            CONVERTER.dump_like(path, value)
            self.assertEqual(path.read_bytes(), (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

    def test_reader_write_leaves_frozen_canonical_fixture_bytes_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            root = Path(tmp)
            audited = root / 'audited-record.json'
            extracted = root / 'source-extracted-record.json'
            audited.write_bytes(b'{"quality":{"review_status":"source_reviewed"},"exact":1.000}\n')
            extracted.write_bytes(b'{"quality":{"review_status":"source_extracted"},"training_ready":false}\n')
            before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (audited, extracted)]
            CONVERTER.dump_like(root / 'reader-presentation-reviewed.json', sample())
            self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in (audited, extracted)])

    def test_caption_writer_keeps_reader_compact_without_changing_status_caption_or_rights(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            path = Path(tmp) / 'reader-presentation-reviewed.json'
            value = sample()
            CAPTIONS.write(path, value)
            assert_same(self, path.read_bytes(), value)
            self.assertEqual(path.read_bytes(), (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
            self.assertFalse(path.with_name(path.name + '.caption-tmp').exists())

    def test_caption_writer_keeps_all_other_outputs_pretty(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            value = {'papers': [], 'shared_files_changed': False}
            for name in ('public-caption-updates.json', 'caption-progress.json', 'audited-record.json'):
                path = Path(tmp) / name
                CAPTIONS.write(path, value)
                self.assertEqual(path.read_bytes(), (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

    def test_unfiltered_build_keeps_exact_source_bytes(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            folder = Path(tmp) / 'data'
            folder.mkdir()
            source, target = folder / REGISTRY.BASE, Path(tmp) / 'reader-presentation.json'
            data = sample()
            source.write_bytes((json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
            emit_build_projection(target, source, data, data)
            self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_filtered_build_compacts_only_existing_display_view(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-compact-') as tmp:
            folder = Path(tmp) / 'data'
            folder.mkdir()
            source, target = folder / REGISTRY.BASE, Path(tmp) / 'reader-presentation.json'
            data = sample()
            source.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())
            original = source.read_bytes()
            view = copy.deepcopy(data)
            view['records']['audited-example']['figures'] = []
            emit_build_projection(target, source, data, view)
            assert_same(self, target.read_bytes(), view)
            self.assertEqual(target.read_bytes(), (json.dumps(view, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
            self.assertEqual(source.read_bytes(), original)

    def test_split_build_emits_complete_unfiltered_combination(self):
        with tempfile.TemporaryDirectory(prefix='mattersyn-reader-split-projection-') as tmp:
            source = Path(tmp) / 'data' / REGISTRY.BASE
            target = Path(tmp) / 'reader-presentation.json'
            data = sample()
            REGISTRY.write_reviewed_reader(source, data, True)
            originals = {p: p.read_bytes() for p in REGISTRY.source_paths(source)}
            self.assertEqual(len(originals), 2)
            combined = REGISTRY.load_reviewed_reader(source)
            emit_build_projection(target, source, combined, combined)
            assert_same(self, target.read_bytes(), data)
            self.assertNotIn(REGISTRY.MARKER, json.loads(target.read_bytes()))
            self.assertEqual(target.read_bytes(),
                             (json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
            for path, raw in originals.items():
                self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
