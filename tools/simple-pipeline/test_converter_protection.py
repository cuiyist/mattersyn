import copy
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('to_site_protected', Path(__file__).with_name('to_site.py'))
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class ConverterProtectionTest(unittest.TestCase):
    def record(self, status='source_extracted'):
        return {'record_id': 'new-core', 'lineage': {'source_group': 'new-source'},
                'quality': {'review_status': status}, 'sources': [{'id': 'new-source', 'doi': '10.1234/new'}],
                'materials': [], 'operations': [], 'measurements': []}

    def test_only_same_extracted_record_is_replaceable(self):
        incoming = self.record()
        self.assertTrue(converter.same_extracted_identity(copy.deepcopy(incoming), incoming))
        for change in ({'quality': {'review_status': 'source_reviewed'}}, {'record_id': 'other'},
                       {'lineage': {'source_group': 'other'}}, {'sources': [{'id': 'new-source', 'doi': '10.1234/other'}]}):
            existing = dict(incoming, **change)
            self.assertFalse(converter.same_extracted_identity(existing, incoming))

    def test_source_group_collision_cannot_mutate_audited_or_other_source(self):
        row = {'source_group': 'new-source', 'doi': '10.1234/new', 'review_status': 'source_extracted'}
        self.assertFalse(converter.source_collision({'per_paper': [row]}, 'new-source', '10.1234/NEW'))
        for change in ({'review_status': 'selected_recipe_and_figure_review'}, {'doi': '10.1234/other'}):
            self.assertTrue(converter.source_collision({'per_paper': [dict(row, **change)]}, 'new-source', '10.1234/new'))

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    def test_records_replace_does_not_overwrite_audited_target(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); pairs = repo / 'pairs'
            incoming = self.record(); target = repo / 'recipe-atlas/data/records/new-core.json'
            self.put(target, self.record('source_reviewed')); original = target.read_bytes()
            self.put(repo / 'recipe-atlas/data/inventory-evidence.json', {'per_paper': []})
            self.put(pairs / 'new.pairs.json', {'id': 'new', 'doi': '10.1234/new', 'check': 'two passes agree, quotes found'})
            schema = ModuleType('schema_definition'); schema.SCHEMA = {}
            validator = SimpleNamespace(iter_errors=lambda record: [])
            builder = SimpleNamespace(source_id='new-source')
            with mock.patch.dict(sys.modules, {'schema_definition': schema}), mock.patch('jsonschema.Draft202012Validator', return_value=validator), mock.patch.object(converter, 'records_of', return_value=(builder, [incoming])):
                converter.cmd_records(SimpleNamespace(repo=repo, pairs=pairs, replace=True, include_optical=False))
            self.assertEqual(target.read_bytes(), original)

    def test_sync_leaves_audited_record_figures_and_sidecar_untouched(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); pairs = repo / 'pairs'; atlas = repo / 'recipe-atlas'
            target = atlas / 'data/records/new-core.json'; self.put(target, self.record('source_reviewed'))
            old = target.read_bytes()
            self.put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
            side = atlas / 'data/reader-presentation-reviewed.json'
            self.put(side, {'records': {'new-core': {'scopeLabel': 'Audited'}}, 'figures_by_source': {'new-source': [{'title': 'Audited figure'}]}, 'materials': {}})
            original_side = side.read_bytes()
            self.put(pairs / 'new.pairs.json', {'id': 'new', 'doi': '10.1234/new', 'check': 'two passes agree, quotes found', 'pairs': [], 'figures': [{'file': 'figure-1.png'}]})
            crop = pairs / 'figures/figure-1.png'; crop.parent.mkdir(); crop.write_bytes(b'new crop')
            protected = atlas / 'static/assets/paper-reviews/new-source/figure-1.png'; protected.parent.mkdir(parents=True); protected.write_bytes(b'audited crop')
            builder = SimpleNamespace(source_id='new-source')
            with mock.patch.object(converter, 'records_of', return_value=(builder, [self.record()])):
                converter.cmd_sync(SimpleNamespace(repo=repo, pairs=pairs, dist=None, include_optical=False))
            self.assertEqual(target.read_bytes(), old)
            self.assertEqual(side.read_bytes(), original_side)
            self.assertEqual(protected.read_bytes(), b'audited crop')

    def test_sync_rejects_pair_changes_until_canonical_record_replaced(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); pairs = repo / 'pairs'; atlas = repo / 'recipe-atlas'
            canonical = self.record(); canonical['title'] = 'Current'
            incoming = self.record(); incoming['title'] = 'Changed draft'
            self.put(atlas / 'data/records/new-core.json', canonical)
            self.put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
            self.put(atlas / 'data/reader-presentation-reviewed.json', {'records': {}, 'figures_by_source': {}, 'materials': {}})
            self.put(pairs / 'new.pairs.json', {'id': 'new', 'doi': '10.1234/new', 'check': 'two passes agree, quotes found'})
            with mock.patch.object(converter, 'records_of', return_value=(SimpleNamespace(source_id='new-source'), [incoming])), mock.patch.object(converter, 'bind_chemicals') as bind:
                converter.cmd_sync(SimpleNamespace(repo=repo, pairs=pairs, dist=None, include_optical=False))
                bind.assert_not_called()

    def run_guard_case(self, command, status):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); pairs = repo / 'pairs'; atlas = repo / 'recipe-atlas'
            self.put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
            self.put(atlas / 'data/reader-presentation-reviewed.json', {'records': {}, 'figures_by_source': {}, 'materials': {}})
            doc = {'id': 'new', 'doi': '10.1234/new'}
            if status is not None: doc['check'] = status
            self.put(pairs / 'new.pairs.json', doc)
            originals = {p: p.read_bytes() for p in atlas.rglob('*.json')}
            schema = ModuleType('schema_definition'); schema.SCHEMA = {}
            validator = SimpleNamespace(iter_errors=lambda record: [])
            with mock.patch.dict(sys.modules, {'schema_definition': schema}), mock.patch('jsonschema.Draft202012Validator', return_value=validator), mock.patch.object(converter, 'records_of', return_value=(SimpleNamespace(source_id='new-source'), [])) as records:
                getattr(converter, 'cmd_' + command)(SimpleNamespace(repo=repo, pairs=pairs, replace=True, dist=None, include_optical=False))
                if status == 'two passes agree, quotes found': records.assert_called_once()
                else: records.assert_not_called()
            self.assertEqual({p: p.read_bytes() for p in atlas.rglob('*.json')}, originals)

    def test_records_and_sync_reject_single_pass_missing_or_stale_check(self):
        for command in ('records', 'sync'):
            for status in (None, 'one pass, quotes found', 'two passes agree', 'two passes agree, quotes found '):
                with self.subTest(command=command, status=status):
                    self.run_guard_case(command, status)

    def test_records_and_sync_accept_exact_two_pass_check(self):
        for command in ('records', 'sync'):
            with self.subTest(command=command):
                self.run_guard_case(command, 'two passes agree, quotes found')


    def test_empty_sync_preserves_pretty_reader_bytes_and_does_not_write(self):
        for crlf, final_newline, bom in ((False, True, False), (True, True, False), (False, False, True)):
            with self.subTest(crlf=crlf, final_newline=final_newline, bom=bom), TemporaryDirectory(dir=Path(__file__).parent) as tmp:
                repo = Path(tmp); atlas = repo / 'recipe-atlas'; pairs = repo / 'pairs'; pairs.mkdir()
                self.put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
                side_path = atlas / 'data/reader-presentation-reviewed.json'
                data = {'records': {'audited': {'scopeLabel': 'Audited µm'}}, 'figures_by_source': {}, 'materials': {}}
                text = json.dumps(data, ensure_ascii=False, indent=2) + ('\n' if final_newline else '')
                if crlf: text = text.replace('\n', '\r\n')
                before = (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')
                side_path.write_bytes(before)
                with mock.patch.object(converter, 'dump_like', wraps=converter.dump_like) as write:
                    converter.cmd_sync(SimpleNamespace(repo=repo, pairs=pairs, dist=None, include_optical=False))
                    write.assert_not_called()
                self.assertEqual(side_path.read_bytes(), before)

    def test_empty_sync_still_reconciles_changed_hubs_then_preserves_noop_bytes(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); atlas = repo / 'recipe-atlas'; pairs = repo / 'pairs'; pairs.mkdir(); dist = repo / 'dist'
            self.put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
            side_path = atlas / 'data/reader-presentation-reviewed.json'
            original_records = {'audited': {'scopeLabel': 'Audited fixture'}}
            self.put(side_path, {'records': original_records, 'figures_by_source': {}, 'materials': {
                'existing': {'id': 'existing', 'formula': 'CdS', 'record_ids': [], 'scopeLabel': 'Original kept scope'},
                'obsolete': {'record_ids': ['audited']}}})
            self.put(dist / 'data/materials/existing.json', {'formula': 'CdS', 'record_ids': ['audited']})
            self.put(dist / 'data/materials/new.json', {'formula': 'ZnS', 'record_ids': ['route'], 'component_only': True})
            manifest = {'records': [], 'record_count': 0, 'group_count': 0, 'families': []}
            baseline = atlas / 'data/release-baseline-manifest.json'
            self.put(baseline, manifest); self.put(dist / 'data/dataset-manifest.json', manifest)
            baseline_bytes = baseline.read_bytes(); original_side_bytes = side_path.read_bytes()
            converter.cmd_sync(SimpleNamespace(repo=repo, pairs=pairs, dist=dist, include_optical=False))
            changed = side_path.read_bytes(); result = json.loads(changed)
            self.assertEqual(result['records'], original_records)
            self.assertEqual(set(result['materials']), {'existing', 'new'})
            self.assertEqual(result['materials']['existing']['record_ids'], ['audited'])
            self.assertEqual(result['materials']['existing']['scopeLabel'], 'Original kept scope')
            self.assertEqual(result['materials']['new']['record_ids'], ['route'])
            self.assertTrue(result['materials']['new']['component_only'])
            expected = json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n'
            if b'\r\n' in original_side_bytes: expected = expected.replace('\n', '\r\n')
            self.assertEqual(changed, expected.encode('utf-8'))
            self.assertEqual(baseline.read_bytes(), baseline_bytes)
            with mock.patch.object(converter, 'dump_like', wraps=converter.dump_like) as write:
                converter.cmd_sync(SimpleNamespace(repo=repo, pairs=pairs, dist=dist, include_optical=False))
                write.assert_not_called()
            self.assertEqual(side_path.read_bytes(), changed)



if __name__ == '__main__':
    unittest.main()
