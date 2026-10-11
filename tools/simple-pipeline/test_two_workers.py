"""Synthetic-only regressions: no model HTTP calls, GPU use, or real paper data."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import run_local_simple_batch_two_workers as controller

HERE = Path(__file__).resolve().parent
RUNTIME = HERE / 'mattersyn_simple.py'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


class Fixture:
    def __init__(self, kinds):
        self.test_root = HERE / 'synthetic-test-temp'
        self.test_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='simple-two-worker-synthetic-', dir=self.test_root)
        self.batch = Path(self.temp.name)
        (self.batch / 'papers').mkdir(); (self.batch / 'trusted-meta').mkdir()
        self.papers = []
        for index, kind in enumerate(kinds):
            doi = f'10.9999/synthetic-{index}'
            pdf = self.batch / 'papers' / f'synthetic-{index}.pdf'
            pdf.write_text(json.dumps({'doi': doi, 'kind': kind}), encoding='utf8')
            self.papers.append({'doi': doi, 'batch_pdf_path': str(pdf)})
            (self.batch / 'trusted-meta' / f'{pdf.stem}.meta.json').write_text(json.dumps({'doi': doi}), encoding='utf8')
        value = {'papers': self.papers}
        for name in ('manifest.json', 'identity-supported-manifest.json'):
            (self.batch / name).write_text(json.dumps(value), encoding='utf8')

    def run(self):
        with patch.dict(os.environ, {'SIMPLE_SYNTHETIC_CHECK_SCRIPT': str(RUNTIME)}), contextlib.redirect_stdout(io.StringIO()):
            task = controller.Coordinator(self.batch, HERE / 'synthetic_cli.py', 987654)
            code = task.run()
        return task, code

    def invocations(self, index):
        path = self.batch / 'work' / f'synthetic-{index}.invocations.jsonl'
        return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]

    def close(self):
        if self.batch.resolve().parent != self.test_root.resolve() or not self.batch.name.startswith('simple-two-worker-synthetic-'):
            raise RuntimeError('Synthetic cleanup target escaped its verified test root')
        self.temp.cleanup()


class TwoPaperCoordinatorTests(unittest.TestCase):
    def fixture(self, kinds):
        fixture = Fixture(kinds)
        self.addCleanup(fixture.close)
        return fixture

    def test_two_requests_overlap_but_never_exceed_two_and_A_precedes_B(self):
        fixture = self.fixture(['ok'] * 4)
        task, code = fixture.run()
        self.assertEqual(code, 0)
        events = []
        for index in range(4):
            rows = [json.loads(line) for line in (fixture.batch / 'work' / f'synthetic-{index}.request-times.jsonl').read_text().splitlines()]
            a_end = next(r['time'] for r in rows if r['name'] == 'A' and r['event'] == 'end')
            b_start = next(r['time'] for r in rows if r['name'] == 'B' and r['event'] == 'start')
            self.assertLessEqual(a_end, b_start)
            events.extend((r['time'], 1 if r['event'] == 'start' else -1) for r in rows)
        active = maximum = 0
        for _, delta in sorted(events):
            active += delta; maximum = max(maximum, active)
            self.assertGreaterEqual(active, 0)
        self.assertEqual(maximum, 2)
        self.assertEqual(active, 0)
        self.assertEqual(task.summary['successful_two_pass_papers'], 4)
        self.assertEqual(task.summary['pair_files'], 4)
        self.assertEqual(task.summary['coordinator']['state_writers'], 1)
        self.assertEqual(len(list((fixture.batch / 'logs' / 'extract').glob('*.console.log'))), 4)


    def test_parallel_nested_directory_creation_is_serialized(self):
        fixture = self.fixture(['once-fail', 'always-fail', 'malformed-once'])
        original_mkdir = Path.mkdir
        active = {}
        guard = threading.Lock()
        overlaps = []
        def contested_mkdir(path, *args, **kwargs):
            ident = threading.get_ident()
            with guard:
                active[ident] = active.get(ident, 0) + 1
                overlap = len(active) > 1
                if overlap:
                    overlaps.append(str(path))
            try:
                if overlap:
                    raise PermissionError('invented Windows concurrent ancestor creation failure')
                time.sleep(0.002)
                return original_mkdir(path, *args, **kwargs)
            finally:
                with guard:
                    active[ident] -= 1
                    if not active[ident]:
                        del active[ident]
        with patch.object(Path, 'mkdir', contested_mkdir):
            task, code = fixture.run()
        self.assertEqual(overlaps, [])
        self.assertEqual(code, 0)
        self.assertEqual(len(task.summary['retry_papers']), 3)
        self.assertEqual(task.summary['original_failed_pass_executions'], 3)
        self.assertEqual(task.summary['redo_failed_pass_executions'], 1)
        self.assertEqual(task.summary['successful_two_pass_papers'], 2)
        self.assertEqual(task.summary['pair_files'], 2)

    def test_permanent_snapshot_creation_error_remains_a_technical_hold(self):
        fixture = self.fixture(['ok'])
        original_make_directory = controller.make_directory
        def permanently_denied(path):
            if 'reused-originals' in Path(path).parts:
                raise PermissionError('invented permanent snapshot permission failure')
            return original_make_directory(path)
        with patch.object(controller, 'make_directory', permanently_denied):
            task, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual(task.summary['retry_papers'], [])
        self.assertEqual(task.summary['successful_two_pass_papers'], 0)
        self.assertEqual(task.summary['left_out'][0]['reason'], 'extract_orchestration_error')
        self.assertEqual(task.summary['left_out'][0]['error_type'], 'PermissionError')
        self.assertEqual(task.summary['pair_files'], 0)
        self.assertFalse((fixture.batch / 'work/synthetic-0.invocations.jsonl').exists())

    def test_each_bad_paper_has_one_redo_and_original_passes_are_preserved(self):
        fixture = self.fixture(['once-fail', 'always-fail', 'malformed-once'])
        task, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual(len(task.summary['retry_papers']), 3)
        self.assertEqual(task.summary['original_failed_pass_executions'], 3)
        self.assertEqual(task.summary['redo_failed_pass_executions'], 1)
        self.assertEqual(task.summary['successful_two_pass_papers'], 2)
        self.assertEqual(len(task.summary['left_out']), 1)
        for index in range(3):
            extraction = [x for x in fixture.invocations(index) if x['mode'] == 'extract']
            self.assertEqual([x['redo'] for x in extraction], [False, True])
            before = fixture.batch / 'retries' / f'synthetic-{index}' / 'before-redo'
            self.assertTrue((before / f'synthetic-{index}.passA.json').exists())
            self.assertTrue((before / f'synthetic-{index}.passB.json').exists())
            self.assertTrue((before / f'synthetic-{index}.text.txt').exists())
        self.assertIn('error', read(fixture.batch / 'retries/synthetic-0/before-redo/synthetic-0.passB.json'))
        self.assertEqual(task.summary['pair_files'], 2)
        self.assertFalse((fixture.batch / 'pairs/synthetic-1.pairs.json').exists())

    def test_resume_reuses_finished_papers_without_any_second_redo(self):
        fixture = self.fixture(['ok', 'always-fail'])
        first, _ = fixture.run()
        invocations = [copy.deepcopy(fixture.invocations(i)) for i in range(2)]
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (fixture.batch / 'work').glob('*.pass*.json')}
        second, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual([fixture.invocations(i) for i in range(2)], invocations)
        self.assertEqual(second.summary['retry_papers'], first.summary['retry_papers'])
        self.assertEqual(second.summary['original_failed_pass_executions'], 1)
        self.assertEqual(second.summary['redo_failed_pass_executions'], 1)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (fixture.batch / 'work').glob('*.pass*.json')}
        self.assertEqual(before, after)

    def test_crash_after_redo_reservation_never_grants_a_second_redo(self):
        fixture = self.fixture(['always-fail'])
        work = fixture.batch / 'work'; work.mkdir()
        (work / 'synthetic-0.text.txt').write_text('[page 1]\nSynthetic CdSe prepared at 120 C for 3 minutes.\n', encoding='utf8')
        (work / 'synthetic-0.passA.json').write_text(json.dumps({'pairs': []}), encoding='utf8')
        (work / 'synthetic-0.passB.json').write_text(json.dumps({'error': 'reserved retry interrupted'}), encoding='utf8')
        doi = fixture.papers[0]['doi']
        (fixture.batch / 'processing-summary.json').write_text(json.dumps({
            'retry_papers': [doi], 'original_failed_pass_executions': 1,
            'redo_failed_pass_executions': 0, 'completed_generation_papers': 0,
        }), encoding='utf8')
        task, code = fixture.run()
        self.assertEqual(code, 0)
        extracts = [x for x in fixture.invocations(0) if x['mode'] == 'extract']
        self.assertEqual([x['redo'] for x in extracts], [False])
        self.assertEqual(task.summary['retry_papers'], [doi])
        self.assertEqual(task.summary['original_failed_pass_executions'], 1)
        self.assertEqual(task.summary['redo_failed_pass_executions'], 0)
        self.assertEqual(task.summary['successful_two_pass_papers'], 0)
        self.assertEqual(len(task.summary['left_out']), 1)
        self.assertFalse((fixture.batch / 'pairs/synthetic-0.pairs.json').exists())
        self.assertFalse(list(fixture.batch.glob('*.tmp')))

    def test_legacy_serial_prefix_reuses_successful_saved_passes(self):
        fixture = self.fixture(['ok', 'ok'])
        work = fixture.batch / 'work'; work.mkdir()
        prior = json.dumps({'pairs': []}).encode('utf8')
        (work / 'synthetic-0.text.txt').write_text('[page 1]\nSynthetic CdSe prepared at 120 C for 3 minutes.\n', encoding='utf8')
        for letter in ('A', 'B'):
            (work / f'synthetic-0.pass{letter}.json').write_bytes(prior)
        (fixture.batch / 'processing-summary.json').write_text(json.dumps({
            'completed_generation_papers': 1, 'successful_two_pass_papers': 1,
            'extract_wall_minutes': 12.25,
        }), encoding='utf8')
        task, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual([x['mode'] for x in fixture.invocations(0)], ['figures'])
        self.assertEqual([x['mode'] for x in fixture.invocations(1)], ['extract', 'figures'])
        for letter in ('A', 'B'):
            self.assertEqual((work / f'synthetic-0.pass{letter}.json').read_bytes(), prior)
        self.assertEqual(task.summary['completed_generation_papers'], 2)
        self.assertEqual(task.summary['successful_two_pass_papers'], 2)
        self.assertTrue(task.summary['extraction_results'][fixture.papers[0]['doi']]['reused_saved_result'])
        self.assertGreater(task.summary['extract_wall_minutes'], 12.25)
        self.assertFalse(list(fixture.batch.glob('*.tmp')))

    def test_pass_validity_predicate_matches_existing_controller_cases(self):
        fixture = self.fixture([])
        work = fixture.batch / 'work'; work.mkdir()
        good = {'pairs': []}
        cases = [(good, good, []), ({'error': 'synthetic', 'pairs': []}, good, ['A']),
                 ({'pairs': [None]}, good, ['A']), ({'pairs': {}}, good, ['A']),
                 ([], good, ['A']), ({}, good, ['A']), (good, None, ['B']),
                 (None, None, ['A', 'B']), ({'pairs': [{}]}, {'pairs': [{}]}, [])]
        for index, (a, b, bad) in enumerate(cases):
            for letter, content in [('A', a), ('B', b)]:
                path = work / f'case{index}.pass{letter}.json'
                if content is not None:
                    path.write_text(json.dumps(content), encoding='utf8')
            self.assertEqual(controller.invalid_passes(work, f'case{index}'), bad)
        (work / 'broken.passA.json').write_text('{', encoding='utf8')
        (work / 'broken.passB.json').write_text(json.dumps(good), encoding='utf8')
        self.assertEqual(controller.invalid_passes(work, 'broken'), ['A'])

    def test_duplicate_DOI_or_stem_is_refused_before_any_work_writes(self):
        for collision in ['doi', 'stem']:
            fixture = self.fixture(['ok', 'ok'])
            path = fixture.batch / 'identity-supported-manifest.json'
            manifest = read(path)
            key = 'doi' if collision == 'doi' else 'batch_pdf_path'
            manifest['papers'][1][key] = manifest['papers'][0][key]
            path.write_text(json.dumps(manifest), encoding='utf8')
            with self.assertRaises(ValueError):
                controller.Coordinator(fixture.batch, HERE / 'synthetic_cli.py', 1)
            self.assertFalse((fixture.batch / 'work').exists())

    def test_state_writer_rejects_worker_thread(self):
        fixture = self.fixture([])
        writer = controller.StateWriter(fixture.batch, {'successful_two_pass_papers': 0}, 1, fixture.batch / 'work')
        failures = []
        def worker():
            try:
                writer.write('synthetic')
            except Exception as error:
                failures.append(type(error).__name__)
        thread = threading.Thread(target=worker); thread.start(); thread.join()
        self.assertEqual(failures, ['RuntimeError'])
        writer.write('synthetic')
        self.assertEqual(len(writer.write_threads), 1)

    def test_original_pdf_and_prior_text_pass_and_pair_bytes_are_preserved(self):
        fixture = self.fixture(['ok'])
        pdf = Path(fixture.papers[0]['batch_pdf_path'])
        original_pdf = pdf.read_bytes()
        work = fixture.batch / 'work'; work.mkdir()
        original_text = b'prior synthetic text, retained locally'
        (work / 'synthetic-0.text.txt').write_bytes(original_text)
        original_pass = {'pairs': []}
        (work / 'synthetic-0.passA.json').write_text(json.dumps(original_pass), encoding='utf8')
        pairs = fixture.batch / 'pairs'; pairs.mkdir()
        original_pair = b'{"synthetic_original": true}'
        (pairs / 'synthetic-0.pairs.json').write_bytes(original_pair)
        fixture.run()
        self.assertEqual(pdf.read_bytes(), original_pdf)
        preserved = fixture.batch / 'reused-originals/synthetic-0/before-command'
        self.assertEqual((preserved / 'synthetic-0.text.txt').read_bytes(), original_text)
        self.assertEqual(read(preserved / 'synthetic-0.passA.json'), original_pass)
        self.assertEqual((pairs / 'originals-before-check/synthetic-0.pairs.json').read_bytes(), original_pair)

    def test_proxy_environment_is_removed_and_existing_model_argument_is_preserved(self):
        fixture = self.fixture(['ok'])
        with patch.dict(os.environ, {'HTTP_PROXY': 'http://synthetic.invalid', 'https_proxy': 'http://synthetic.invalid'}):
            fixture.run()
        for invocation in fixture.invocations(0):
            self.assertEqual(invocation['model'], 'qwen3-32b')
            self.assertEqual(invocation['proxy_keys_present'], [])
            self.assertEqual(invocation['NO_PROXY'], '127.0.0.1,localhost,::1')

    def test_actual_unchanged_check_enforces_quote_number_and_both_pass_rules(self):
        fixture = self.fixture(['ok', 'unfound-quote', 'wrong-number', 'disagreement'])
        _, code = fixture.run()
        self.assertEqual(code, 0)
        for index in range(4):
            result = read(fixture.batch / 'pairs' / f'synthetic-{index}.pairs.json')
            self.assertEqual(result['check'], 'two passes agree, quotes found')
            self.assertEqual('reaction_temperature' in result['pairs'][0]['recipe'], index == 0)
            self.assertEqual(result['values_kept'], 3 if index == 0 else 2)
        console = (fixture.batch / 'check.console.log').read_text(encoding='utf8')
        self.assertIn('dropped: quote not in paper', console)
        self.assertIn('dropped: number not in quote', console)
        self.assertIn('dropped: passes disagree', console)

    def test_figure_failure_is_reported_and_no_single_pass_admission_occurs(self):
        fixture = self.fixture(['figure-fail', 'always-fail', 'no-pairs'])
        task, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual(task.summary['successful_two_pass_papers'], 2, json.dumps(task.summary))
        self.assertEqual(task.summary['figures_failures'], [{'doi': fixture.papers[0]['doi'], 'exit_code': 5}])
        self.assertFalse((fixture.batch / 'pairs/synthetic-1.pairs.json').exists())
        self.assertEqual(read(fixture.batch / 'pairs/synthetic-2.pairs.json')['pairs'], [])

    def test_batch_lock_prevents_a_second_coordinator_owner(self):
        fixture = self.fixture([])
        with controller.BatchLock(fixture.batch):
            with self.assertRaises(RuntimeError):
                with controller.BatchLock(fixture.batch):
                    pass
        # Ownership releases without deleting the retained lock file.
        with controller.BatchLock(fixture.batch):
            pass
        self.assertTrue((fixture.batch / '.controller-two-workers.lock').exists())

    def test_worker_exception_is_a_technical_hold_with_private_diagnostics(self):
        fixture = self.fixture(['ok'])
        with patch.object(controller.Coordinator, '_extract', side_effect=OSError('invented synthetic filesystem failure')):
            task, code = fixture.run()
        self.assertEqual(code, 0)
        self.assertEqual(task.summary['successful_two_pass_papers'], 0)
        self.assertEqual(task.summary['retry_papers'], [])
        self.assertEqual(task.summary['left_out'][0]['reason'], 'extract_orchestration_error')
        self.assertEqual(task.summary['left_out'][0]['error_type'], 'OSError')
        log = (fixture.batch / 'logs/extract/synthetic-0.console.log').read_text(encoding='utf8')
        self.assertIn('invented synthetic filesystem failure', log)
        self.assertEqual(task.summary['pair_files'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
