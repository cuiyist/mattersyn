"""Invented-data equivalence, complete coverage, concurrency and failure tests."""
from pathlib import Path
import importlib.util
import datetime as dt
import hashlib
import json
import subprocess
import threading
import time
import unittest
from collections import Counter
from unittest.mock import patch
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

parallel = load('receipt_parallel', 'make_review_receipt.py')
serial = SimpleNamespace(git=parallel.git, blob=parallel.blob, CONTROLS=parallel.CONTROLS)
AT = '2026-10-11T00:00:00+00:00'

def serial_build_receipt(root, reviewer, at=None):
    """Small reference for the pre-parallel loop; production Git/blob reads are mocked."""
    if not reviewer or not reviewer.strip():
        raise SystemExit('--reviewer is required')
    root = Path(root).resolve()
    head = serial.git(root, 'rev-parse', 'HEAD').decode().strip()
    at = at or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    rows = []
    for line in serial.git(root, 'diff', '--cached', '--name-status', '--no-renames').decode().splitlines():
        status, path = line.split('\t', 1)
        if path in serial.CONTROLS:
            continue
        before = serial.blob(root, 'HEAD:' + path)
        common = {'path': path, 'before_sha256': hashlib.sha256(before).hexdigest() if before is not None else None,
                  'review_status': 'approved', 'reviewer': reviewer, 'reviewed_at': at, 'source_refs': []}
        if status.startswith('D'):
            rows.append({**common, 'decision': 'delete'})
            continue
        staged = serial.blob(root, ':' + path)
        mode = serial.git(root, 'ls-files', '-s', '--', path).decode().split()[0]
        rows.append({**common, 'decision': 'allow', 'sha256': hashlib.sha256(staged).hexdigest(),
                     'bytes': len(staged), 'git_mode': mode})
    if not rows:
        raise SystemExit('nothing staged: git add the reviewed changes first')
    return {'schema': 'mattersyn-reviewed-source-changes/1', 'base_commit': head, 'files': rows}

serial.build_receipt = serial_build_receipt

class Fixture:
    def __init__(self, changes, before=None, staged=None, mode=None):
        self.changes = changes
        self.before = before or {}
        self.staged = staged or {}
        self.mode = mode or {}
        self.calls = []
        self.lock = threading.Lock()
        self.active = self.peak = 0

    def git(self, root, *args):
        with self.lock:
            self.calls.append(('git', args))
        if args == ('rev-parse', 'HEAD'):
            return b'abc123\n'
        if args[0] == 'diff':
            return ''.join(status + '\t' + path + '\n' for status, path in self.changes).encode()
        if args[:2] == ('ls-files', '-s'):
            path = args[-1]
            value = self.mode.get(path, '100644')
            if isinstance(value, Exception):
                raise value
            return (value + ' deadbeef 0\t' + path + '\n').encode()
        raise AssertionError(args)

    def blob(self, root, spec):
        with self.lock:
            self.calls.append(('blob', spec))
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            path = spec.removeprefix('HEAD:') if spec.startswith('HEAD:') else spec[1:]
            time.sleep(0.004 if path.startswith('slow') else 0.001)
            value = self.before.get(path) if spec.startswith('HEAD:') else self.staged.get(path)
            if isinstance(value, Exception):
                raise value
            return value
        finally:
            with self.lock:
                self.active -= 1

    def run(self, module):
        with patch.object(module, 'git', self.git), patch.object(module, 'blob', self.blob):
            return module.build_receipt(HERE, 'synthetic-reviewer', at=AT)

class ParallelReceiptTests(unittest.TestCase):
    def test_exact_serial_equivalence_full_coverage_and_order(self):
        changes = [('M', 'slow-change.md'), ('A', 'new/empty.bin'), ('D', 'removed.bin'),
                   ('A', 'chemical-\u03b1.md'), ('M', 'executable.py'), ('A', 'binary.bin'),
                   ('M', 'publication/build-inputs.json'), ('M', 'publication/project-allowlist.json')]
        before = {'slow-change.md': b'old', 'removed.bin': b'gone', 'executable.py': b'old program'}
        staged = {'slow-change.md': b'new', 'new/empty.bin': b'', 'chemical-\u03b1.md': '\u03b2'.encode(),
                  'executable.py': b'program', 'binary.bin': bytes(range(256)) * 8192}
        a = Fixture(changes, before, staged, {'executable.py': '100755'})
        b = Fixture(changes, before, staged, {'executable.py': '100755'})
        expected, actual = a.run(serial), b.run(parallel)
        self.assertEqual(actual, expected)
        self.assertEqual(json.dumps(actual), json.dumps(expected))
        self.assertEqual(Counter(a.calls), Counter(b.calls), 'all original commands remain; no extra commands')
        self.assertEqual([x['path'] for x in actual['files']], [x[1] for x in changes[:6]])
        self.assertTrue(all(x['reviewed_at'] == AT for x in actual['files']))

    def test_concurrency_is_bounded_and_each_blob_is_read_once(self):
        changes = [('A', f'slow-{i:02}.bin') for i in range(40)]
        fixture = Fixture(changes, staged={path: b'fixture' for _, path in changes})
        receipt = fixture.run(parallel)
        self.assertEqual(len(receipt['files']), 40)
        self.assertGreater(fixture.peak, 1)
        self.assertLessEqual(fixture.peak, 8)
        for _, path in changes:
            self.assertEqual(fixture.calls.count(('blob', 'HEAD:' + path)), 1)
            self.assertEqual(fixture.calls.count(('blob', ':' + path)), 1)
            self.assertEqual(fixture.calls.count(('git', ('ls-files', '-s', '--', path))), 1)

    def test_first_input_order_read_error_is_preserved(self):
        changes = [('M', 'slow-first'), ('M', 'later')]
        for module in (serial, parallel):
            fixture = Fixture(changes, {'slow-first': OSError('first input error'), 'later': OSError('later error')})
            with self.assertRaisesRegex(OSError, 'first input error'):
                fixture.run(module)

    def test_earlier_blob_error_wins_over_later_malformed_row(self):
        for module in (serial, parallel):
            fixture = Fixture([('M', 'slow-first')], {'slow-first': OSError('first input error')})
            original_git = fixture.git
            def malformed_later(root, *args):
                return b'M\tslow-first\nmalformed-row\n' if args[0] == 'diff' else original_git(root, *args)
            with patch.object(module, 'git', malformed_later), patch.object(module, 'blob', fixture.blob):
                with self.assertRaisesRegex(OSError, 'first input error'):
                    module.build_receipt(HERE, 'synthetic-reviewer', at=AT)

    def test_staged_blob_and_mode_failures_still_fail(self):
        for module in (serial, parallel):
            with self.assertRaises(TypeError):
                Fixture([('A', 'missing')]).run(module)
            with self.assertRaises(subprocess.CalledProcessError):
                Fixture([('A', 'mode-failure')], staged={'mode-failure': b'x'},
                        mode={'mode-failure': subprocess.CalledProcessError(7, ['git'])}).run(module)

    def test_no_cache_changed_blob_is_hashed_fresh(self):
        fixture = Fixture([('A', 'fresh')], staged={'fresh': b'first'})
        first = fixture.run(parallel)
        fixture.staged['fresh'] = b'second'
        second = fixture.run(parallel)
        self.assertNotEqual(first['files'][0]['sha256'], second['files'][0]['sha256'])
        self.assertEqual(fixture.calls.count(('blob', ':fresh')), 2)

    def test_nothing_staged_and_controls_only_still_refused(self):
        for module in (serial, parallel):
            for changes in ([], [('M', 'publication/build-inputs.json')]):
                with self.assertRaisesRegex(SystemExit, 'nothing staged'):
                    Fixture(changes).run(module)

    def test_missing_reviewer_and_malformed_changes_still_refused(self):
        for module in (serial, parallel):
            with patch.object(module, 'git', side_effect=AssertionError('must not read Git')):
                with self.assertRaisesRegex(SystemExit, 'reviewer is required'):
                    module.build_receipt(HERE, ' ')
            fixture = Fixture([('A', 'one')], staged={'one': b'x'})
            original_git = fixture.git
            def malformed_git(root, *args):
                return b'malformed-row\n' if args[0] == 'diff' else original_git(root, *args)
            with patch.object(module, 'git', malformed_git), patch.object(module, 'blob', fixture.blob):
                with self.assertRaises(ValueError):
                    module.build_receipt(HERE, 'synthetic-reviewer', at=AT)

if __name__ == '__main__':
    unittest.main()
