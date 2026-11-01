"""Synthetic-only coverage of the controller's shared whole-pass shape check."""
import json
import queue
import unittest
from unittest.mock import patch

import run_local_simple_batch_two_workers as controller
from test_two_workers import Fixture, read


class StrictPassShapeCoordinatorTests(unittest.TestCase):
    def fixture(self, kinds):
        fixture = Fixture(kinds)
        self.addCleanup(fixture.close)
        return fixture

    def test_nested_malformed_containers_are_failed_passes(self):
        fixture = self.fixture([])
        work = fixture.batch / 'work'
        work.mkdir()
        malformed = [
            {'structure': []},
            {'structure': None},
            {'recipe': ['not a recipe object']},
            {'structure': {'size': [17]}},
            {'recipe': {'reaction_time': 3}},
            {'recipe': {'chemicals': {'name': 'synthetic'}}},
            {'recipe': {'chemicals': [None]}},
            {'recipe': {'steps': 'synthetic step'}},
            {'recipe': {'steps': [None]}},
        ]
        for index, pair in enumerate(malformed):
            with self.subTest(pair=pair):
                stem = f'nested-{index}'
                (work / f'{stem}.passA.json').write_text(
                    json.dumps({'pairs': [pair]}), encoding='utf8')
                (work / f'{stem}.passB.json').write_text(
                    json.dumps({'pairs': []}), encoding='utf8')
                self.assertEqual(controller.invalid_passes(work, stem), ['A'])

    def test_engine_accepted_empty_optional_containers_stay_accepted(self):
        fixture = self.fixture([])
        work = fixture.batch / 'work'
        work.mkdir()
        accepted = [
            {'pairs': []},
            {'pairs': [{}]},
            {'pairs': [{'recipe': None}]},
            {'pairs': [{'structure': {'size': None},
                        'recipe': {'reaction_time': None, 'chemicals': [], 'steps': []}}]},
        ]
        for index, value in enumerate(accepted):
            with self.subTest(value=value):
                stem = f'accepted-{index}'
                for letter in ('A', 'B'):
                    (work / f'{stem}.pass{letter}.json').write_text(
                        json.dumps(value), encoding='utf8')
                self.assertEqual(controller.invalid_passes(work, stem), [])

    def run_nested_failure(self, permanent):
        fixture = self.fixture(['ok', 'ok'])
        target_doi = fixture.papers[0]['doi']
        original_command = controller.Coordinator._command
        original_failed_pass, redo_reservations = [], []

        def command(task, phase, paper, arguments):
            # No model is used: the existing local fixture emits synthetic JSON.
            if '--redo' in arguments:
                redo_reservations.append(read(fixture.batch / 'processing-summary.json')['retry_papers'])
            code = original_command(task, phase, paper, arguments)
            if (phase == 'extract' and paper['doi'] == target_doi
                    and (permanent or '--redo' not in arguments)):
                path = task.work / 'synthetic-0.passA.json'
                value = read(path)
                value['pairs'][0]['recipe']['steps'] = [None]
                path.write_text(json.dumps(value), encoding='utf8')
                if not original_failed_pass:
                    original_failed_pass.append(path.read_bytes())
            return code

        # Exercise the real extraction coordinator and its two-worker pool only.
        # Neither figures nor final CHECK is invoked in these regressions.
        task = controller.Coordinator(fixture.batch, controller.Path(__file__).with_name('synthetic_cli.py'), 987654)
        task.work.mkdir(); task.pairs.mkdir()
        task.writer.write('extract')
        with patch.object(controller.Coordinator, '_command', command):
            task._pool('extract', task.papers, task._extract)
        return fixture, task, original_failed_pass[0], redo_reservations

    def test_nested_failure_uses_existing_one_redo_then_continues(self):
        fixture, task, original, reservations = self.run_nested_failure(permanent=False)
        self.assertEqual(task.summary['original_failed_pass_executions'], 1)
        self.assertEqual(task.summary['redo_failed_pass_executions'], 0)
        self.assertEqual(task.summary['retry_papers'], [fixture.papers[0]['doi']])
        self.assertEqual(task.summary['successful_two_pass_papers'], 2)
        self.assertEqual(task.summary['left_out'], [])
        self.assertEqual(len(task.writer.write_threads), 1)
        self.assertEqual(reservations, [[fixture.papers[0]['doi']]])
        self.assertEqual([row['redo'] for row in fixture.invocations(0)], [False, True])
        self.assertEqual([row['mode'] for row in fixture.invocations(1)], ['extract'])
        retained = fixture.batch / 'retries/synthetic-0/before-redo/synthetic-0.passA.json'
        self.assertEqual(retained.read_bytes(), original)

    def test_nested_failure_after_one_redo_is_left_out_and_second_reservation_is_denied(self):
        fixture, task, original, reservations = self.run_nested_failure(permanent=True)
        self.assertEqual(task.summary['original_failed_pass_executions'], 1)
        self.assertEqual(task.summary['redo_failed_pass_executions'], 1)
        self.assertEqual(task.summary['successful_two_pass_papers'], 1)
        self.assertEqual(len(task.summary['left_out']), 1)
        failed = task.summary['extraction_results'][fixture.papers[0]['doi']]
        self.assertFalse(failed['valid'])
        self.assertEqual(failed['failed_passes'], ['A'])
        self.assertEqual(failed['redo_failed_passes'], ['A'])
        self.assertEqual([row['mode'] for row in fixture.invocations(0)], ['extract', 'extract'])
        self.assertEqual([row['mode'] for row in fixture.invocations(1)], ['extract'])
        self.assertEqual(reservations, [[fixture.papers[0]['doi']]])
        retained = fixture.batch / 'retries/synthetic-0/before-redo/synthetic-0.passA.json'
        self.assertEqual(retained.read_bytes(), original)
        # The existing coordinator ledger refuses a second redo for this paper.
        answer = queue.Queue(maxsize=1)
        task._event({'type': 'retry_request', 'doi': fixture.papers[0]['doi'],
                     'bad': ['A'], 'answer': answer}, 'extract')
        self.assertFalse(answer.get_nowait())
        self.assertEqual(task.summary['original_failed_pass_executions'], 1)
        self.assertEqual(task.summary['retry_papers'], [fixture.papers[0]['doi']])
        self.assertEqual(len(task.writer.write_threads), 1)


if __name__ == '__main__':
    unittest.main()
