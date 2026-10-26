"""Portable synthetic phase admission tests; no real disk query, build or delete."""
import io
import json
from types import SimpleNamespace
import unittest
from unittest import mock

import release_batch as rb
from test_generated_raw_lifecycle import FakeFS, FreshRawLifecycleTests


class Budget:
    def __init__(self, raw): self.raw, self.read_sizes, self.opens = raw, [], 0
    def open(self, mode):
        if mode != 'rb': raise AssertionError(mode)
        self.opens += 1; owner = self
        class Reader(io.BytesIO):
            def read(self, size=-1):
                owner.read_sizes.append(size)
                if size != 16385: raise AssertionError('physically bounded read required')
                return super().read(size)
        return Reader(self.raw)


def document():
    return {'schema': 'mattersyn-complete-owned-phase-peaks/1', 'workspace': '/workspace',
            'reserve_bytes': 100 * 1024 ** 3,
            'coverage': 'all_remaining_phase_and_concurrent_owned_writes',
            'phases': {phase: {step: 1 for step in steps} for phase, steps in rb.PHASE_CAPACITY_STEPS.items()}}


class PhaseCapacityTests(FreshRawLifecycleTests):
    def setUp(self):
        super().setUp()
        self.fs.add('/workspace/source'); self.fs.add('/workspace/site')
        self.free = [rb.PHASE_CAPACITY_RESERVE + 100]
        self.disk_calls = []
        self.shutil.disk_usage = self.disk_usage
        patcher = mock.patch.object(rb, 'Path', self.fs.path)
        patcher.start(); self.addCleanup(patcher.stop)

    def disk_usage(self, path):
        self.assertEqual(str(path), '/workspace')
        value = self.free.pop(0) if len(self.free) > 1 else self.free[0]
        self.disk_calls.append(value)
        return SimpleNamespace(free=value)

    def capacity(self, data=None, raw=None):
        budget = Budget(json.dumps(data or document()).encode() if raw is None else raw)
        result = rb._PhaseCapacity(budget, self.fs.path('/workspace/fresh'), self.fs.path('/workspace'),
                                   self.fs.path('/workspace/source'), self.fs.path('/workspace/site'))
        self.assertEqual((budget.opens, budget.read_sizes), (1, [16385]))
        return result

    def test_complete_strict_positive_integer_schema(self):
        cases = []
        for value in (None, True, False, 0, -1, 1.0, '1', float('nan')):
            data = document(); data['phases']['candidate']['build'] = value; cases.append(data)
        for value in (True, rb.PHASE_CAPACITY_RESERVE - 1, 100.0):
            data = document(); data['reserve_bytes'] = value; cases.append(data)
        data = document(); del data['phases']['final']; cases.append(data)
        data = document(); data['phases']['final']['extra'] = 1; cases.append(data)
        data = document(); data['extra'] = True; cases.append(data)
        data = document(); data['coverage'] = 'anticipated_cleanup_gain'; cases.append(data)
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(SystemExit): self.capacity(data)

    def test_bounded_same_buffer_rejects_duplicate_and_oversize(self):
        for raw in (b' ' * 16385, b'{"schema":1,"schema":2}', b'\xff'):
            with self.subTest(raw_length=len(raw)):
                with self.assertRaises(SystemExit): self.capacity(raw=raw)

    def test_exact_threshold_and_fresh_free_for_every_admission(self):
        capacity = self.capacity()
        self.free = [rb.PHASE_CAPACITY_RESERVE + 1, rb.PHASE_CAPACITY_RESERVE]
        capacity.admit('candidate', 'snapshot')
        with self.assertRaisesRegex(SystemExit, 'HOLD before candidate/build'):
            capacity.admit('candidate', 'build')
        self.assertEqual(len(self.disk_calls), 2)
        for value in (True, -1, 1.0):
            self.free = [value]
            with self.assertRaises(SystemExit): capacity.admit('candidate', 'build')

    def test_workspaces_and_checkout_filesystem_identity_are_bound(self):
        data = document(); data['workspace'] = '/source'
        with self.assertRaises(SystemExit): self.capacity(data)
        self.fs.nodes['/workspace/site'].st_dev = 2
        with self.assertRaises(SystemExit): self.capacity()
        self.fs.nodes['/workspace/site'].st_dev = 1
        capacity = self.capacity(); self.fs.nodes['/workspace/site'].st_ino += 1
        with self.assertRaises(SystemExit): capacity.admit('publication', 'copy')
        self.assertEqual(self.disk_calls, [])

    def test_after_successful_retirement_next_phase_uses_actual_free(self):
        self.main_with_budget(hold_before_final=True, fail_retirement=False)
        self.assertEqual(len(self.removals()), 5)
        self.assertEqual(len(self.disk_calls), 3)
        self.assertFalse(any(event == ('build_start', 'final') for event in self.fs.events))

    def test_retirement_failure_never_admits_or_allocates_next_phase(self):
        self.main_with_budget(hold_before_final=False, fail_retirement=True)
        self.assertEqual(self.removals(), [])
        self.assertEqual(len(self.disk_calls), 2)
        self.assertFalse(any(event == ('build_start', 'final') for event in self.fs.events))

    def main_with_budget(self, hold_before_final, fail_retirement):
        del self.fs.nodes['/workspace/fresh']
        budget = Budget(json.dumps(document()).encode())
        args = SimpleNamespace(source=self.fs.path('/workspace/source'), site=self.fs.path('/workspace/site'),
                               work=self.fs.path('/workspace/fresh'), raw_workspace=self.fs.path('/workspace'),
                               phase_budget=budget, retire_generated_raw=True, push=False, verify=False,
                               skip_ci_check=False, source_repo='example/source', wait_ci=0, sync_gate_tools=False,
                               release_id='unit', reviewer='unit')
        self.free = [rb.PHASE_CAPACITY_RESERVE + 100, rb.PHASE_CAPACITY_RESERVE + 100,
                     rb.PHASE_CAPACITY_RESERVE if hold_before_final else rb.PHASE_CAPACITY_RESERVE + 100]
        if fail_retirement: self.fs.fail_removal_number = 0
        def run(argv, cwd=None):
            strings = [str(value) for value in argv]
            if any(value.endswith('/build_release.py') for value in strings):
                phase = 'candidate' if '--candidate' in strings else 'final'
                self.fs.events.append(('build_start', phase)); self.fs.build(phase)
        with mock.patch.object(rb.argparse.ArgumentParser, 'parse_args', return_value=args), \
                mock.patch.object(rb, 'git', side_effect=lambda *args: '' if args[1] == 'status' else 'a' * 40), \
                mock.patch.object(rb, 'wait_for_ci', return_value=(True, [])), \
                mock.patch.object(rb, 'run', side_effect=run):
            with self.assertRaises(OSError if fail_retirement else SystemExit): rb.main()


if __name__ == '__main__': unittest.main()
