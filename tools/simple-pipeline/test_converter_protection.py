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


if __name__ == '__main__':
    unittest.main()
