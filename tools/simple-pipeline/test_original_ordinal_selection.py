"""Generated-fixture engineering tests; no papers, saved pools or model calls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

import to_site as converter
import mattersyn_simple as simple
import select_quote_free_export as export

HERE = Path(__file__).resolve().parent


def generated_pair(number, active=True):
    return {'product': 'ZnS fixture ' + str(number),
            'structure': {'composition': {'value': 'ZnS', 'page': 1}},
            'recipe': {'chemicals': [{'name': 'zinc acetate', 'role': 'metal source', 'page': 1,
                                     'quote': 'generated private sentinel'}],
                       'reactor': {'value': 'generated vessel ' + str(number), 'page': 1},
                       'steps': ([{'action': 'heat', 'description': 'Generated fixture step',
                                   'uses': ['zinc acetate'], 'temperature': 200 + number,
                                   'temperature_unit': 'degC', 'page': 1}] if active else [])}}


def generated_documents():
    common = {'authors': 'Generated Author', 'year': 2000, 'journal': 'Generated fixture',
              'check': 'two passes agree, quotes found', 'figures': [], 'pages_read': [1], 'page_count': 1}
    return [dict(common, id='generated-a', doi='10.0000/generated-a', title='Generated fixture A',
                 pairs=[generated_pair(1, False), generated_pair(2), generated_pair(3)]),
            dict(common, id='generated-b', doi='10.0000/generated-b', title='Generated fixture B',
                 pairs=[generated_pair(1), generated_pair(2, False)])]


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def fixture(root, status=None):
    docs = generated_documents()
    if status is not None:
        for doc in docs:
            doc['check'] = status
    pairs = root / 'inputs'
    rows = []
    for doc, ordinals in zip(docs, ([2, 3], [1])):
        path = pairs / (doc['id'] + '.pairs.json')
        put(path, doc)
        raw = path.read_bytes()
        builder, records = converter.records_of(doc, original_ordinals=ordinals)
        rows.append(dict(doi=doc['doi'], source_id=builder.source_id,
                         pair_bytes=len(raw), pair_sha256=hashlib.sha256(raw).hexdigest(),
                         original_ordinals=ordinals, record_ids=[r['record_id'] for r in records]))
    control = root / 'selection.json'
    put(control, dict(schema='normal-original-ordinal-selection/1', papers=rows))
    return docs, pairs, control, rows


def record_args(root, pairs, control=None):
    repo = root / 'generated-repo'
    (repo / 'recipe-atlas/data/records').mkdir(parents=True, exist_ok=True)
    put(repo / 'recipe-atlas/data/inventory-evidence.json', {'per_paper': []})
    return SimpleNamespace(repo=repo, pairs=pairs, original_ordinals=control, replace=True, include_optical=False)


class OriginalOrdinalSelectionTest(unittest.TestCase):
    def test_default_legacy_projection_keeps_original_all_pairs(self):
        docs = generated_documents()
        for doc in docs:
            before = copy.deepcopy(doc)
            _, default = converter.records_of(doc)
            builder = converter.Builder(doc)
            expected = [builder.record(pair, n) for n, pair in enumerate(doc['pairs'], 1)]
            self.assertEqual(default, expected)
            self.assertEqual(doc, before)
        self.assertEqual(sum(len(converter.records_of(d)[1]) for d in docs), 5)

    def test_opt_in_preserves_exact_original_ids_and_every_nested_field(self):
        for doc, ordinals in zip(generated_documents(), ([2, 3], [1])):
            _, full = converter.records_of(doc)
            _, selected = converter.records_of(doc, original_ordinals=ordinals)
            self.assertEqual(selected, [full[n - 1] for n in ordinals])
            for n, record in zip(ordinals, selected):
                self.assertTrue(record['record_id'].endswith('-' + str(n)))
                self.assertEqual(record, converter.Builder(doc).record(doc['pairs'][n - 1], n))
            self.assertEqual(len(doc['pairs']), len(full))

    def test_sync_reactors_follow_same_original_selection(self):
        tree = ast.parse(Path(converter.__file__).read_bytes())
        command = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cmd_sync')
        expr = next(n.value for loop in command.body if isinstance(loop, ast.For) for n in loop.body
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'reactors' for t in n.targets))
        for doc, ordinals in zip(generated_documents(), ([2, 3], [1])):
            actual = eval(compile(ast.Expression(expr), '<generated reactor selection>', 'eval'),
                          dict(doc=doc, original_ordinals=ordinals,
                               original_ordinal_pairs=converter.original_ordinal_pairs,
                               _composition_from=converter._composition_from))
            expected = [doc['pairs'][n - 1]['recipe']['reactor']['value'] for n in ordinals]
            self.assertEqual(actual, expected)

    def test_duplicate_object_keys_reject_even_if_identical_or_nested(self):
        for raw in ('{"schema":1,"schema":1}', '{"x":{"n":1,"n":2}}',
                    '{"papers":[{"doi":"generated","doi":"generated"}]}'):
            with self.assertRaises(ValueError):
                json.loads(raw, object_pairs_hook=converter.unique_selection_object)
        self.assertEqual(json.loads('{"x":1,"x":2}'), {'x': 2})

    def test_real_selector_reader_rejects_duplicates_before_pair_read(self):
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            control = root / 'duplicate.json'
            control.write_text('{"schema":1,"schema":1}', encoding='utf-8')
            pair = mock.Mock()
            with self.assertRaises(ValueError):
                converter.selected_pair_input(SimpleNamespace(original_ordinals=control), pair)
            pair.read_bytes.assert_not_called()

    def test_one_MiB_cap_is_bounded_before_decode(self):
        reads = []
        class Buffer(io.BytesIO):
            def read(self, size=-1):
                reads.append(size)
                return super().read(size)
        path = SimpleNamespace(open=lambda mode: Buffer(b' ' * 1048577))
        with mock.patch.object(converter, 'Path', return_value=path):
            with self.assertRaises(ValueError):
                converter.selected_pair_input(SimpleNamespace(original_ordinals='generated'), mock.Mock())
        self.assertEqual(reads, [1048577])

    def test_malformed_selection_and_ordinal_shapes_hold(self):
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            _, pairs, control, rows = fixture(root)
            first = next(pairs.glob('*.pairs.json'))
            for value in ({}, {'schema': 'other', 'papers': rows},
                          {'schema': 'normal-original-ordinal-selection/1', 'papers': []},
                          {'schema': 'normal-original-ordinal-selection/1', 'papers': [rows[0], rows[0]]}):
                put(control, value)
                with self.assertRaises(ValueError):
                    converter.selected_pair_input(SimpleNamespace(original_ordinals=control, include_optical=False), first)
        for ordinals in ([], [True], [0], [4], [2, 2], [3, 2], ['2']):
            with self.assertRaises(ValueError):
                converter.original_ordinal_pairs(generated_documents()[0], ordinals)

    def test_selector_pin_source_ID_and_RIDs_are_exact(self):
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            _, pairs, control, rows = fixture(root)
            first = pairs / 'generated-a.pairs.json'
            for field, value in (('pair_bytes', True), ('pair_bytes', 0), ('pair_sha256', '0' * 64),
                                 ('source_id', 'other'), ('record_ids', []), ('original_ordinals', None)):
                changed = copy.deepcopy(rows)
                changed[0][field] = value
                put(control, dict(schema='normal-original-ordinal-selection/1', papers=changed))
                with self.assertRaises(ValueError):
                    converter.selected_pair_input(SimpleNamespace(original_ordinals=control, include_optical=False), first)

    def test_generated_records_command_default_and_selected_counts(self):
        schema = ModuleType('schema_definition')
        schema.SCHEMA = {}
        for selected, expected in ((False, 5), (True, 3)):
            with self.subTest(selected=selected), TemporaryDirectory(dir=HERE) as name:
                root = Path(name)
                _, pairs, control, _ = fixture(root)
                args = record_args(root, pairs, control if selected else None)
                with mock.patch.dict(sys.modules, {'schema_definition': schema}):
                    converter.cmd_records(args)
                records = list((args.repo / 'recipe-atlas/data/records').glob('*.json'))
                self.assertEqual(len(records), expected)

    def test_selected_scope_does_not_bypass_existing_source_collision(self):
        schema = ModuleType('schema_definition')
        schema.SCHEMA = {}
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            docs, pairs, control, rows = fixture(root)
            args = record_args(root, pairs, control)
            put(args.repo / 'recipe-atlas/data/inventory-evidence.json', {'per_paper': [dict(
                source_group=rows[0]['source_id'], doi=docs[0]['doi'], review_status='source_reviewed')]})
            with mock.patch.dict(sys.modules, {'schema_definition': schema}):
                converter.cmd_records(args)
            written = list((args.repo / 'recipe-atlas/data/records').glob('*.json'))
            self.assertEqual([p.stem for p in written], rows[1]['record_ids'])

    def test_selected_scope_does_not_replace_reviewed_record(self):
        schema = ModuleType('schema_definition')
        schema.SCHEMA = {}
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            docs, pairs, control, rows = fixture(root)
            args = record_args(root, pairs, control)
            _, records = converter.records_of(docs[0], original_ordinals=[2, 3])
            protected = copy.deepcopy(records[0])
            protected['quality']['review_status'] = 'source_reviewed'
            target = args.repo / 'recipe-atlas/data/records' / (rows[0]['record_ids'][0] + '.json')
            put(target, protected)
            before = target.read_bytes()
            with mock.patch.dict(sys.modules, {'schema_definition': schema}):
                converter.cmd_records(args)
            self.assertEqual(target.read_bytes(), before)

    def test_selected_single_pass_is_not_written(self):
        schema = ModuleType('schema_definition')
        schema.SCHEMA = {}
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            _, pairs, control, _ = fixture(root, status='one pass, checked')
            args = record_args(root, pairs, control)
            with mock.patch.dict(sys.modules, {'schema_definition': schema}):
                converter.cmd_records(args)
            self.assertEqual(list((args.repo / 'recipe-atlas/data/records').glob('*.json')), [])

    def test_unchanged_normal_build_then_adapter_exports_only_selected_entries(self):
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            docs, pairs, control, rows = fixture(root)
            originals = {p: p.read_bytes() for p in pairs.glob('*.pairs.json')}
            built = root / 'normal-build'
            simple.cmd_build(SimpleNamespace(pairs=pairs, out=built, label='Generated fixture', quotes=False))
            full = json.loads((built / 'pairs.json').read_text(encoding='utf-8'))
            self.assertEqual(sum(len(d['pairs']) for d in full), 5)
            out, mapping = root / 'selected-public.json', root / 'private-mapping.json'
            export.run(SimpleNamespace(pairs=pairs, built_public_json=built / 'pairs.json', original_ordinals=control,
                                       out=out, private_mapping=mapping))
            selected = json.loads(out.read_text(encoding='utf-8'))
            private = json.loads(mapping.read_text(encoding='utf-8'))
            self.assertEqual(sum(len(d['pairs']) for d in selected), 3)
            for whole, narrowed, row, entry in zip(full, selected, rows, private['papers']):
                self.assertEqual(set(whole), set(narrowed))
                self.assertEqual(narrowed['pairs'], [whole['pairs'][n - 1] for n in row['original_ordinals']])
                self.assertEqual([x['canonical_record_id'] for x in entry['entries']], row['record_ids'])
                self.assertEqual([x['source_original_ordinal'] for x in entry['entries']], row['original_ordinals'])
            self.assertFalse(export.has_quotes(selected))
            self.assertNotIn('generated private sentinel', out.read_text(encoding='utf-8'))
            self.assertEqual({p: p.read_bytes() for p in pairs.glob('*.pairs.json')}, originals)

    def test_export_projection_equality_preserves_JSON_types_and_key_order(self):
        docs = generated_documents()
        inputs = []
        for doc, ordinals in zip(docs, ([2, 3], [1])):
            _, records = converter.records_of(doc, original_ordinals=ordinals)
            inputs.append(dict(doc=doc, original_ordinals=ordinals,
                               record_ids=[r['record_id'] for r in records]))
        full = [simple.public_document(d) for d in docs]
        self.assertIs(type(full[0]['pairs'][1]['structure']['composition']['page']), int)
        for bad in (True, 1.0, float('nan'), float('inf')):
            changed = copy.deepcopy(full)
            changed[0]['pairs'][1]['structure']['composition']['page'] = bad
            with self.subTest(changed_type=type(bad).__name__), self.assertRaises(ValueError):
                export.select_export(changed, inputs)
        def reverse_keys(value):
            if isinstance(value, dict):
                return {k: reverse_keys(v) for k, v in reversed(list(value.items()))}
            if isinstance(value, list):
                return [reverse_keys(v) for v in value]
            return value
        reordered = reverse_keys(full)
        selected, mapping = export.select_export(reordered, inputs)
        self.assertEqual([d['pairs'] for d in selected],
                         [[full[0]['pairs'][1], full[0]['pairs'][2]], [full[1]['pairs'][0]]])
        self.assertEqual([x['source_original_ordinal'] for x in mapping[0]['entries']], [2, 3])
        self.assertEqual(full, [simple.public_document(d) for d in docs])

    def test_export_mutation_and_overwrite_are_rejected(self):
        docs = generated_documents()
        inputs = []
        for doc, ordinals in zip(docs, ([2, 3], [1])):
            _, records = converter.records_of(doc, original_ordinals=ordinals)
            inputs.append(dict(doc=doc, original_ordinals=ordinals, record_ids=[r['record_id'] for r in records]))
        full = [simple.public_document(d) for d in docs]
        changed = copy.deepcopy(full)
        changed[0]['pairs'][0]['product'] = 'Changed generated object'
        for invalid in (changed, full[:-1], full + [full[0]]):
            with self.assertRaises(ValueError):
                export.select_export(invalid, inputs)
        with TemporaryDirectory(dir=HERE) as name:
            root = Path(name)
            _, pairs, control, _ = fixture(root)
            old = root / 'exists.json'
            old.write_text('generated existing output', encoding='utf-8')
            with self.assertRaises(ValueError):
                export.run(SimpleNamespace(pairs=pairs, built_public_json=root / 'not-read.json',
                                           original_ordinals=control, out=old, private_mapping=root / 'private.json'))
            self.assertEqual(old.read_text(encoding='utf-8'), 'generated existing output')


if __name__ == '__main__':
    unittest.main()
