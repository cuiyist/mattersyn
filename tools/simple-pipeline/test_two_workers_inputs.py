"""Synthetic input-selection regressions; no model/server or real paper data."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import run_local_simple_batch_two_workers as controller
from test_two_workers import Fixture, HERE, RUNTIME, read


class CoordinatorInputSelectionTests(unittest.TestCase):
    def fixture(self, kinds):
        value = Fixture(kinds)
        self.addCleanup(value.close)
        return value

    def r2(self, fixture, indices):
        manifest = fixture.batch / 'identity-supported-manifest-r2.json'
        papers = [fixture.papers[i] for i in indices]
        manifest.write_text(json.dumps({'papers': papers}), encoding='utf8')
        trusted = fixture.batch / 'trusted-meta-r2'
        trusted.mkdir()
        for paper in papers:
            name = Path(paper['batch_pdf_path']).stem + '.meta.json'
            (trusted / name).write_text(json.dumps({'doi': paper['doi']}), encoding='utf8')
        return manifest, trusted

    def test_default_inputs_and_model_are_unchanged(self):
        fixture = self.fixture(['ok', 'ok'])
        task = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 987654)
        self.assertEqual(task.manifest_path, fixture.batch / 'identity-supported-manifest.json')
        self.assertEqual(task.trusted_meta, fixture.batch / 'trusted-meta')
        self.assertEqual(task.papers, fixture.papers)
        self.assertEqual(task.model, 'qwen3-32b')
        self.assertEqual(task.work, fixture.batch / 'work')
        self.assertEqual(task.pairs, fixture.batch / 'pairs')
        self.assertFalse(task.work.exists())

    def test_explicit_default_paths_select_same_inputs(self):
        fixture = self.fixture(['ok', 'ok'])
        implicit = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 987654)
        explicit = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 987654,
                                          manifest=fixture.batch / 'identity-supported-manifest.json',
                                          trusted_meta=fixture.batch / 'trusted-meta')
        self.assertEqual(implicit.papers, explicit.papers)
        self.assertEqual(implicit.trusted_meta, explicit.trusted_meta)
        self.assertEqual(implicit.summary['generation_papers'], explicit.summary['generation_papers'])
        self.assertEqual(implicit.summary['identity_holds'], explicit.summary['identity_holds'])

    def test_each_optional_input_can_be_selected_independently(self):
        fixture = self.fixture(['ok', 'ok'])
        manifest, trusted = self.r2(fixture, [1])
        selected_manifest = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 1,
                                                   manifest=manifest)
        self.assertEqual(selected_manifest.papers, [fixture.papers[1]])
        self.assertEqual(selected_manifest.trusted_meta, fixture.batch / 'trusted-meta')
        selected_meta = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 1,
                                               trusted_meta=trusted)
        self.assertEqual(selected_meta.papers, fixture.papers)
        self.assertEqual(selected_meta.trusted_meta, trusted)

    def test_cli_defaults_pass_no_input_override(self):
        argv = ['controller', '--batch', 'synthetic-batch', '--script', 'synthetic-cli', '--server-pid', '987654']
        with patch.object(sys, 'argv', argv), patch.object(controller, 'Coordinator') as factory:
            factory.return_value.run.return_value = 0
            self.assertEqual(controller.main(), 0)
        factory.assert_called_once_with(Path('synthetic-batch'), Path('synthetic-cli'), 987654,
                                        'qwen3-32b', manifest=None, trusted_meta=None)

    def test_cli_explicit_input_paths_and_model_are_forwarded(self):
        argv = ['controller', '--batch', 'synthetic-batch', '--script', 'synthetic-cli',
                '--server-pid', '987654', '--model', 'synthetic-local-model',
                '--manifest', 'synthetic-r2.json', '--trusted-meta', 'synthetic-meta-r2']
        with patch.object(sys, 'argv', argv), patch.object(controller, 'Coordinator') as factory:
            factory.return_value.run.return_value = 7
            self.assertEqual(controller.main(), 7)
        factory.assert_called_once_with(Path('synthetic-batch'), Path('synthetic-cli'), 987654,
                                        'synthetic-local-model', manifest=Path('synthetic-r2.json'),
                                        trusted_meta=Path('synthetic-meta-r2'))

    def test_selected_r2_papers_own_only_selected_disjoint_outputs_and_history_is_unchanged(self):
        fixture = self.fixture(['ok', 'ok', 'ok'])
        default = fixture.batch / 'identity-supported-manifest.json'
        default.write_text(json.dumps({'papers': [fixture.papers[0]]}), encoding='utf8')
        manifest, trusted = self.r2(fixture, [1, 2])
        retained = [fixture.batch / 'manifest.json', default, manifest,
                    *list((fixture.batch / 'trusted-meta').glob('*.meta.json')),
                    *list(trusted.glob('*.meta.json')),
                    *[Path(p['batch_pdf_path']) for p in fixture.papers]]
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in retained}
        with patch.dict(os.environ, {'SIMPLE_SYNTHETIC_CHECK_SCRIPT': str(RUNTIME)}), contextlib.redirect_stdout(io.StringIO()):
            task = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 987654,
                                          manifest=manifest, trusted_meta=trusted)
            self.assertEqual(task.run(), 0)
        self.assertEqual(task.summary['cohort_papers'], 3)
        self.assertEqual(task.summary['generation_papers'], 2)
        self.assertEqual(task.summary['identity_holds'], [fixture.papers[0]['doi']])
        self.assertEqual(task.summary['successful_two_pass_papers'], 2)
        self.assertEqual(task.summary['coordinator']['state_writers'], 1)
        self.assertEqual(task.summary['coordinator']['paper_workers'], 2)
        self.assertFalse(list(task.work.glob('synthetic-0.*')))
        self.assertFalse((task.pairs / 'synthetic-0.pairs.json').exists())
        for index in [1, 2]:
            self.assertEqual(read(task.work / f'synthetic-{index}.meta.json'), {'doi': fixture.papers[index]['doi']})
            self.assertEqual([x['mode'] for x in fixture.invocations(index)], ['extract', 'figures'])
            pair = read(task.pairs / f'synthetic-{index}.pairs.json')
            self.assertEqual(pair['doi'], fixture.papers[index]['doi'])
            self.assertEqual(pair['check'], 'two passes agree, quotes found')
        self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in retained})

    def test_selected_meta_preserves_different_prior_work_override(self):
        fixture = self.fixture(['ok'])
        manifest, trusted = self.r2(fixture, [0])
        work = fixture.batch / 'work'
        work.mkdir()
        previous = b'{"doi": "10.9999/old-synthetic-metadata"}'
        (work / 'synthetic-0.meta.json').write_bytes(previous)
        with patch.dict(os.environ, {'SIMPLE_SYNTHETIC_CHECK_SCRIPT': str(RUNTIME)}), contextlib.redirect_stdout(io.StringIO()):
            task = controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 987654,
                                          manifest=manifest, trusted_meta=trusted)
            self.assertEqual(task.run(), 0)
        preserved = fixture.batch / 'reused-originals/synthetic-0.meta/before-command/synthetic-0.meta.json'
        self.assertEqual(preserved.read_bytes(), previous)
        self.assertEqual(read(work / 'synthetic-0.meta.json'), {'doi': fixture.papers[0]['doi']})

    def test_duplicate_override_DOI_or_stem_still_refused_before_work_writes(self):
        for key in ['doi', 'batch_pdf_path']:
            fixture = self.fixture(['ok', 'ok'])
            manifest, trusted = self.r2(fixture, [0, 1])
            rows = read(manifest)
            rows['papers'][1][key] = rows['papers'][0][key]
            manifest.write_text(json.dumps(rows), encoding='utf8')
            with self.assertRaises(ValueError):
                controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 1,
                                       manifest=manifest, trusted_meta=trusted)
            self.assertFalse((fixture.batch / 'work').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
