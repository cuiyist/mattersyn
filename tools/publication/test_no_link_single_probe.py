"""Bounded filesystem primitives only; no build, network or repository writes."""
import errno
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import one_build as p


class NoLinkSingleProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.file = self.root / 'file'
        self.file.write_bytes(b'content')

    def tearDown(self):
        # All temporary fixtures are explicitly owned by this test.
        self.temp.cleanup()

    def test_existing_file_directory_and_new_output(self):
        for path in (self.file, self.root, self.root / 'new' / 'out.json'):
            self.assertEqual(p.no_link(path), path)
        output = self.root / 'out.json'
        p.write_new(output, {'checked': True})
        self.assertEqual(p.read(output), {'checked': True})
        with self.assertRaises(FileExistsError):
            p.write_new(output, {'overwrite': True})
        with self.assertRaises(FileNotFoundError):
            p.write_new(self.root / 'missing-parent' / 'out.json', {})

    def test_new_disjoint_directory_and_missing_parent(self):
        out = self.root / 'new'
        self.assertEqual(p.disjoint_new(out, [self.file]), out)
        with self.assertRaisesRegex(p.Rejected, 'parent_missing'):
            p.disjoint_new(self.root / 'absent' / 'new', [self.file])

    def test_each_ancestor_exactly_one_lstat_and_no_pre_probe(self):
        original, calls = Path.lstat, []
        def observed(path, *args, **kwargs):
            calls.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'lstat', observed), \
             patch.object(Path, 'exists', side_effect=AssertionError('exists probe')), \
             patch.object(Path, 'is_symlink', side_effect=AssertionError('link probe')):
            self.assertEqual(p.no_link(self.file), self.file)
        self.assertEqual(calls, [self.file, *self.file.parents])

    def test_permission_and_other_errors_propagate(self):
        original = Path.lstat
        for exception in (PermissionError(errno.EACCES, 'denied'), OSError(errno.EIO, 'io failure')):
            def denied(path, *args, **kwargs):
                if path == self.file:
                    raise exception
                return original(path, *args, **kwargs)
            with self.subTest(error=type(exception).__name__), patch.object(Path, 'lstat', denied):
                with self.assertRaises(type(exception)):
                    p.no_link(self.file)

    def test_missing_leaf_still_checks_all_existing_ancestors(self):
        original = Path.lstat
        def blocked_ancestor(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == self.root:
                return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
            return value
        with patch.object(Path, 'lstat', blocked_ancestor), self.assertRaisesRegex(p.Rejected, 'reparse'):
            p.no_link(self.root / 'missing' / 'out.json')

    def test_simulated_file_directory_symlinks_and_reparse(self):
        original = Path.lstat
        for target in (self.file, self.root):
            for kind in ('symlink', 'reparse'):
                def altered(path, *args, **kwargs):
                    value = original(path, *args, **kwargs)
                    if path == target:
                        return SimpleNamespace(st_mode=stat.S_IFLNK if kind == 'symlink' else value.st_mode,
                                               st_file_attributes=0x400 if kind == 'reparse' else 0)
                    return value
                with self.subTest(target=target.name, kind=kind), patch.object(Path, 'lstat', altered):
                    with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
                        p.no_link(self.file)

    def make_link(self, target, name, directory=False):
        link = self.root / name
        try:
            os.symlink(target, link, target_is_directory=directory)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314 or error.errno in (errno.EPERM, errno.EACCES):
                self.skipTest('Host lacks symlink creation permission; simulated checks still run')
            raise
        return link

    def test_actual_file_symlink(self):
        link = self.make_link(self.file, 'link')
        with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
            p.no_link(link)

    def test_actual_directory_symlink(self):
        target = self.root / 'dir'
        target.mkdir()
        (target / 'leaf').write_bytes(b'x')
        link = self.make_link(target, 'dir-link', directory=True)
        with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
            p.no_link(link / 'leaf')

    def test_actual_broken_symlink(self):
        link = self.make_link(self.root / 'absent', 'broken')
        with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
            p.no_link(link)

    def test_stable_bytes_checks_ancestry_before_and_after(self):
        real, calls = p.no_link, []
        def second_is_reparse(path):
            calls.append(Path(path))
            if len(calls) == 2:
                raise p.Rejected('symlink_or_reparse')
            return real(path)
        with patch.object(p, 'no_link', second_is_reparse):
            with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
                p.stable_bytes(self.file)
        self.assertEqual(calls, [self.file, self.file])

    def test_stable_bytes_reads_same_handle_twice(self):
        original, reads = Path.open, []
        class Observed:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def fileno(self): return self.stream.fileno()
            def seek(self, *args): return self.stream.seek(*args)
            def read(self):
                reads.append(self.stream.fileno())
                return self.stream.read()
        with patch.object(Path, 'open', lambda path, *a, **k: Observed(original(path, *a, **k))):
            self.assertEqual(p.stable_bytes(self.file), b'content')
        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0], reads[1])

    def test_enotdir_fails_closed(self):
        # A child of a regular file can never be a legitimate new output path.
        with self.assertRaises((NotADirectoryError, FileNotFoundError, OSError)):
            p.stable_bytes(self.file / 'invalid-child')


if __name__ == '__main__':
    unittest.main()
