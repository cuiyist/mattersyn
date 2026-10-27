"""Synthetic backup-path regression; no model/server or real paper data."""
import os
from pathlib import Path
import tempfile
import unittest

import run_local_simple_batch_two_workers as controller

HERE = Path(__file__).resolve().parent


def native_path(path):
    absolute = os.path.abspath(path)
    if os.name == 'nt' and not absolute.startswith('\\\\?\\'):
        absolute = ('\\\\?\\UNC\\' + absolute[2:] if absolute.startswith('\\\\')
                    else '\\\\?\\' + absolute)
    return Path(absolute)


def ordinary_path(path):
    value = str(path)
    if os.name == 'nt':
        if value.startswith('\\\\?\\UNC\\'):
            value = '\\\\' + value[8:]
        elif value.startswith('\\\\?\\'):
            value = value[4:]
    return Path(value)


class BackupPathTests(unittest.TestCase):
    def close_fixture(self, temporary, test_root):
        root = Path(temporary.name)
        if root.resolve().parent != native_path(test_root).resolve():
            raise RuntimeError('Synthetic cleanup target escaped its verified test root')
        temporary.cleanup()  # Windows root retains its extended prefix for cleanup.
        self.assertFalse(root.exists())

    def test_long_destination_preserves_versions_and_reuses_identical_bytes(self):
        test_root = HERE / 'synthetic-test-temp'
        test_root.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='simple-two-worker-backup-',
                                                 dir=native_path(test_root))
        self.addCleanup(self.close_fixture, temporary, test_root)
        root = ordinary_path(temporary.name)
        self.assertEqual(native_path(root).resolve().parent, native_path(test_root).resolve())
        name = 'synthetic-sici-' + 'x' * 60 + '.meta.json'
        source = native_path(root / name)
        source.write_bytes(b'first metadata bytes')
        destination = root / 'reused-originals' / ('paper-' + 'x' * 60) / 'before-command'
        while len(str(destination / name)) <= 300:
            destination /= 'nested-backup-directory'
        self.assertGreater(len(str(destination / name)), 260)
        # Pass an ordinary long destination: the production function must prefix it.
        target = native_path(destination / name)
        controller.preserve_files([source], destination)
        self.assertEqual(target.read_bytes(), b'first metadata bytes')
        controller.preserve_files([source], destination)
        self.assertEqual([p.name for p in native_path(destination).iterdir()], [name])
        source.write_bytes(b'second metadata bytes')
        controller.preserve_files([source], destination)
        second = native_path(destination / (name + '.preserved-2'))
        self.assertEqual(target.read_bytes(), b'first metadata bytes')
        self.assertEqual(second.read_bytes(), b'second metadata bytes')
        source.write_bytes(b'first metadata bytes')
        controller.preserve_files([source], destination)
        self.assertEqual(sorted(p.name for p in native_path(destination).iterdir()),
                         sorted([name, name + '.preserved-2']))
        self.assertEqual(target.read_bytes(), b'first metadata bytes')
        self.assertEqual(second.read_bytes(), b'second metadata bytes')
        self.assertEqual(source.read_bytes(), b'first metadata bytes')


if __name__ == '__main__':
    unittest.main(verbosity=2)
