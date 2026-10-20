"""Synthetic read/hash fixtures; no Git, repository preparation or apply calls."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from prepare_source_release import PreparationError, member, read_staged_members


def serial_reference(root, staged):
    """The original sequential read and exact no-filter blob identity contract."""
    result = {}
    for name, info in staged.items():
        content = member(root, name).read_bytes()
        digest = hashlib.new('sha1' if len(info['oid']) == 40 else 'sha256')
        digest.update(b'blob %d\0' % len(content))
        digest.update(content)
        if digest.hexdigest() != info['oid']:
            raise PreparationError('Working file differs from exact staged bytes: ' + name)
        result[name] = content
    return result


class ParallelSourceReads(unittest.TestCase):
    def setUp(self):
        self.temp_parent = Path(tempfile.gettempdir()).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix='source-parallel-', dir=self.temp_parent)
        self.root = Path(self.temp.name).resolve()
        self.assertEqual(self.root.parent, self.temp_parent)
        self.addCleanup(self.cleanup_fixture)

    def cleanup_fixture(self):
        self.assertEqual(self.root.parent, self.temp_parent)
        self.assertTrue(self.root.name.startswith('source-parallel-'))
        self.temp.cleanup()

    def fixture(self, count=24):
        staged = {}
        payloads = [b'', b'CRLF\r\nunchanged\r\n', bytes(range(256)), 'unicode \u00b5'.encode()]
        for i in range(count):
            name = ('nested/' if i % 2 else '') + f'{count - i:03d}.bin'
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            content = payloads[i % 4] + bytes([i]) * i
            path.write_bytes(content)
            digest = hashlib.new('sha1' if i % 2 else 'sha256')
            digest.update(b'blob %d\0' % len(content))
            digest.update(content)
            staged[name] = {'mode': '100755' if i % 3 == 0 else '100644',
                            'oid': digest.hexdigest()}
        return staged

    def test_delayed_reads_preserve_bytes_order_and_eight_worker_limit(self):
        staged = self.fixture()
        before = copy.deepcopy(staged)
        expected = serial_reference(self.root, staged)
        original = Path.read_bytes
        lock = threading.Lock()
        state = {'active': 0, 'peak': 0, 'calls': []}

        def delayed(path):
            with lock:
                state['active'] += 1
                state['peak'] = max(state['peak'], state['active'])
                state['calls'].append(path.relative_to(self.root).as_posix())
            try:
                time.sleep(.004 + (int(path.stem) % 4) * .002)
                return original(path)
            finally:
                with lock:
                    state['active'] -= 1

        with patch.object(Path, 'read_bytes', delayed):
            actual = read_staged_members(self.root, staged)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual), list(staged))
        self.assertEqual(staged, before)
        self.assertCountEqual(state['calls'], staged)
        self.assertEqual(len(state['calls']), len(staged))
        self.assertGreater(state['peak'], 1)
        self.assertLessEqual(state['peak'], 8)

    def test_repeated_results_are_deterministic_and_never_cached(self):
        staged = self.fixture(12)
        expected = serial_reference(self.root, staged)
        for _ in range(4):
            self.assertEqual(list(read_staged_members(self.root, staged).items()),
                             list(expected.items()))
        name = next(iter(staged))
        (self.root / name).write_bytes(b'changed after previous successful reads')
        for read in [serial_reference, read_staged_members]:
            with self.subTest(read=read.__name__), self.assertRaisesRegex(
                    PreparationError, 'Working file differs from exact staged bytes: ' + name):
                read(self.root, staged)

    def test_first_error_follows_index_order_not_completion_order(self):
        staged = self.fixture(3)
        first, second = list(staged)[:2]
        original = Path.read_bytes

        def failing(path):
            name = path.relative_to(self.root).as_posix()
            if name == first:
                time.sleep(.035)
                raise PermissionError('first ordered read')
            if name == second:
                raise FileNotFoundError('second fast read')
            return original(path)

        for read in [serial_reference, read_staged_members]:
            with self.subTest(read=read.__name__), patch.object(Path, 'read_bytes', failing):
                with self.assertRaisesRegex(PermissionError, 'first ordered read'):
                    read(self.root, staged)

    def test_missing_member_refuses_like_serial(self):
        staged = self.fixture(3)
        (self.root / list(staged)[1]).unlink()
        for read in [serial_reference, read_staged_members]:
            with self.subTest(read=read.__name__), self.assertRaises(FileNotFoundError):
                read(self.root, staged)

    def test_changed_bytes_during_read_refuse_staged_identity(self):
        staged = self.fixture(3)
        changed = list(staged)[1]
        original = Path.read_bytes

        def changed_read(path):
            if path.relative_to(self.root).as_posix() == changed:
                path.write_bytes(b'new bytes raced before read')
            return original(path)

        with patch.object(Path, 'read_bytes', changed_read), self.assertRaisesRegex(
                PreparationError, 'Working file differs from exact staged bytes'):
            read_staged_members(self.root, staged)

    def test_noncanonical_names_and_existing_symlink_guard_refuse(self):
        for name in ['../outside', 'nested/../outside', 'C:/outside', 'a\\b']:
            with self.subTest(name=name), self.assertRaises(PreparationError):
                read_staged_members(self.root, {name: {'mode': '100644', 'oid': '0' * 40}})
        staged = self.fixture(1)
        target = self.root / next(iter(staged))
        original = Path.is_symlink

        def link(path):
            return path == target or original(path)

        with patch.object(Path, 'is_symlink', link), self.assertRaisesRegex(
                PreparationError, 'Symlink source path'):
            read_staged_members(self.root, staged)

    def test_real_symlink_when_platform_allows_creation(self):
        staged = self.fixture(1)
        target = self.root / next(iter(staged))
        original = self.root / 'preserved-target.bin'
        original.write_bytes(target.read_bytes())
        target.unlink()
        try:
            os.symlink(original, target)
        except (OSError, NotImplementedError) as error:
            self.skipTest('Symlink creation unavailable: ' + type(error).__name__)
        for read in [serial_reference, read_staged_members]:
            with self.subTest(read=read.__name__), self.assertRaisesRegex(
                    PreparationError, 'Symlink source path'):
                read(self.root, staged)


if __name__ == '__main__':
    unittest.main()
