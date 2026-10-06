"""Tiny source-state conformance/fault fixtures; no production tree or build."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

import one_build as p


class SourceStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix='source-state-unit-', dir=os.environ.get('MATTERSYN_SOURCE_STATE_TEST_TMP'))
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(self.temporary.cleanup)
        for scope in (*p.COPY_DIRS, 'tools'):
            (self.root / scope).mkdir(parents=True, exist_ok=True)
        self.head = 'a' * 40
        self.data = {f'recipe-atlas/data/{n:02d}.json': bytes([n]) * 17 for n in range(13)}
        self.data['recipe-atlas/static/caf\u00e9.txt'] = b'one\r\ntwo\n'
        self.data['recipe-atlas/static/empty'] = b''
        for name, raw in self.data.items():
            (self.root / name).write_bytes(raw)
        self.entries = [self.entry(name, raw) for name, raw in sorted(self.data.items())]
        self.expected = [{'path': name, 'sha256': p.digest(raw), 'bytes': len(raw)}
                         for name, raw in sorted(self.data.items())]

    @staticmethod
    def entry(name, raw, mode='100644', kind='blob'):
        oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        return f'{mode} {kind} {oid}\t{name}'.encode()

    def git(self, source, *args):
        self.assertEqual(Path(source), self.root)
        if args == ('rev-parse', '--show-toplevel'):
            return (str(self.root) + '\n').encode()
        if args == ('rev-parse', 'HEAD'):
            return (self.head + '\n').encode()
        if args == ('status', '--porcelain', '--untracked-files=all'):
            return b''
        if args == ('ls-tree', '-rz', '--full-tree', 'HEAD'):
            return b'\0'.join(self.entries) + b'\0'
        self.fail('Unexpected Git request: ' + str(args))

    def run_state(self, git=None):
        with mock.patch.object(p, 'git', git or self.git):
            return p.source_state(self.root, self.head)

    def test_exact_binary_unicode_empty_and_final_sorted_rows(self):
        self.entries.reverse()
        self.assertEqual(self.run_state(), self.expected)

    def test_actual_tiny_git_repository(self):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE)
        git('init', '--quiet')
        git('config', 'core.autocrlf', 'false')
        git('add', '--all')
        git('-c', 'user.name=Private Fixture', '-c', 'user.email=fixture@example.invalid',
            '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'private source fixture')
        head = git('rev-parse', 'HEAD').decode().strip()
        self.assertEqual(p.source_state(self.root, head), self.expected)

    def test_four_readers_overlap_and_never_exceed_four(self):
        original = p.stable_bytes
        barrier = threading.Barrier(4)
        lock = threading.Lock()
        state = {'entered': 0, 'active': 0, 'peak': 0}
        def read(path):
            with lock:
                state['entered'] += 1
                number = state['entered']
                state['active'] += 1
                state['peak'] = max(state['peak'], state['active'])
            try:
                if number <= 4:
                    barrier.wait(timeout=5)
                return original(path)
            finally:
                with lock:
                    state['active'] -= 1
        with mock.patch.object(p, 'stable_bytes', read):
            self.assertEqual(self.run_state(), self.expected)
        self.assertEqual(state, {'entered': len(self.data), 'active': 0, 'peak': 4})

    def test_git_entry_failure_order_and_join_before_return(self):
        entered = threading.Event()
        failed = threading.Event()
        release = threading.Event()
        finished = threading.Event()
        original = p.stable_bytes
        first_error = PermissionError(13, 'first-entry')
        def read(path):
            if path.name == '00.json':
                if not entered.wait(5):
                    raise AssertionError('fixture synchronization timed out')
                failed.set()
                raise first_error
            if path.name == '01.json':
                entered.set()
                try:
                    if not release.wait(5):
                        raise AssertionError('fixture release timed out')
                    raise ValueError('later-entry')
                finally:
                    finished.set()
            return original(path)
        with mock.patch.object(p, 'git', self.git), mock.patch.object(p, 'stable_bytes', read), \
                concurrent.futures.ThreadPoolExecutor(max_workers=1) as outer:
            future = outer.submit(p.source_state, self.root, self.head)
            try:
                self.assertTrue(failed.wait(5))
                self.assertFalse(future.done())
            finally:
                release.set()
            with self.assertRaises(PermissionError) as caught:
                future.result(timeout=5)
        self.assertIs(caught.exception, first_error)
        self.assertTrue(finished.is_set())

    def test_at_most_four_submitted_results_outstanding(self):
        state = {'outstanding': 0, 'peak': 0, 'consumed': 0}
        test = self
        class Result:
            def __init__(self, future):
                self.future = future
            def result(self):
                try:
                    return self.future.result()
                finally:
                    state['outstanding'] -= 1
                    state['consumed'] += 1
        class Pool:
            def __init__(self, max_workers):
                test.assertEqual(max_workers, 4)
                self.inner = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            def __enter__(self):
                return self
            def submit(self, fn, entry):
                state['outstanding'] += 1
                state['peak'] = max(state['peak'], state['outstanding'])
                return Result(self.inner.submit(fn, entry))
            def __exit__(self, *args):
                self.inner.shutdown(wait=True)
        with mock.patch.object(p, 'ThreadPoolExecutor', Pool):
            self.assertEqual(self.run_state(), self.expected)
        self.assertEqual(state, {'outstanding': 0, 'peak': 4, 'consumed': len(self.data)})

    def test_submission_failure_joins_and_preserves_exception(self):
        release = threading.Event()
        completed = []
        failure = OSError(11, 'submission failure')
        original = p.stable_bytes
        test = self
        class Pool:
            def __init__(self, max_workers):
                test.assertEqual(max_workers, 4)
                self.inner = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
                self.count = 0
            def __enter__(self):
                return self
            def submit(self, fn, entry):
                self.count += 1
                if self.count == 3:
                    release.set()
                    raise failure
                return self.inner.submit(fn, entry)
            def __exit__(self, *args):
                self.inner.shutdown(wait=True)
        def read(path):
            if not release.wait(5):
                raise AssertionError('fixture release timed out')
            raw = original(path)
            completed.append(path.name)
            return raw
        with mock.patch.object(p, 'ThreadPoolExecutor', Pool), \
                mock.patch.object(p, 'stable_bytes', read):
            with self.assertRaises(OSError) as caught:
                self.run_state()
        self.assertIs(caught.exception, failure)
        self.assertEqual(sorted(completed), ['00.json', '01.json'])

    def test_dirty_and_wrong_head_reject_before_reads(self):
        for kind, reason in [('dirty', 'dirty_source'), ('head', 'source_head_drift')]:
            def git(source, *args):
                if kind == 'dirty' and args[0] == 'status':
                    return b' M changed\n'
                if kind == 'head' and args == ('rev-parse', 'HEAD'):
                    return b'b' * 40 + b'\n'
                return self.git(source, *args)
            with self.subTest(kind=kind), mock.patch.object(p, 'stable_bytes') as read:
                with self.assertRaisesRegex(p.Rejected, reason):
                    self.run_state(git)
                read.assert_not_called()

    def test_missing_file_after_clean_status_rejects(self):
        (self.root / 'recipe-atlas/data/00.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_state()

    def test_same_size_same_mtime_hidden_edit_fails_git_blob_identity(self):
        target = self.root / 'recipe-atlas/data/00.json'
        before = target.stat()
        target.write_bytes(b'X' * len(self.data['recipe-atlas/data/00.json']))
        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(p.Rejected, 'working_bytes_differ_from_commit'):
            self.run_state()

    def test_link_and_reparse_leaf_or_ancestor_rejected(self):
        target = self.root / 'recipe-atlas/data/00.json'
        original = Path.lstat
        for member in [target, target.parent]:
            for reparse in [False, True]:
                def lstat(path, *args, **kwargs):
                    value = original(path, *args, **kwargs)
                    if path == member:
                        return SimpleNamespace(st_mode=value.st_mode if reparse else stat.S_IFLNK | 0o777,
                                               st_file_attributes=0x400 if reparse else 0)
                    return value
                with self.subTest(member=member.name, reparse=reparse), \
                        mock.patch.object(Path, 'lstat', lstat):
                    with self.assertRaisesRegex(p.Rejected, 'symlink_or_reparse'):
                        self.run_state()

    def test_unsupported_mode_and_unsafe_git_path_rejected(self):
        original = self.entries[0]
        for entry, reason in [(self.entry('recipe-atlas/data/00.json', b'', mode='120000'), 'unsupported_git_entry'),
                              (self.entry('../escape', b''), 'unsafe_path_segment')]:
            self.entries[0] = entry
            with self.subTest(reason=reason), self.assertRaisesRegex(p.Rejected, reason):
                self.run_state()
        self.entries[0] = original

    def test_case_colliding_tracked_names_rejected_on_every_host(self):
        # Both spellings exist on a case-sensitive host; one ordinary file backs
        # both on a case-insensitive host. Neither spelling is fictitiously missing.
        for name in ['A', 'a']:
            (self.root / 'recipe-atlas/data' / name).write_bytes(b'x')
        self.entries += [self.entry('recipe-atlas/data/' + name, b'x') for name in ['A', 'a']]
        with self.assertRaisesRegex(p.Rejected, 'duplicate_or_case_colliding_path'):
            self.run_state()

    def test_ignored_extra_build_input_rejected(self):
        (self.root / 'recipe-atlas/static/extra.ignored').write_bytes(b'extra')
        with self.assertRaisesRegex(p.Rejected, 'untracked_or_ignored_build_input'):
            self.run_state()

    def test_closing_head_or_status_drift_rejected(self):
        for kind in ['head', 'status']:
            calls = {'head': 0, 'status': 0}
            def git(source, *args):
                key = 'head' if args == ('rev-parse', 'HEAD') else 'status' if args[0] == 'status' else None
                if key:
                    calls[key] += 1
                    if key == kind and calls[key] == 2:
                        return b'b' * 40 + b'\n' if kind == 'head' else b' M changed\n'
                return self.git(source, *args)
            with self.subTest(kind=kind), self.assertRaisesRegex(p.Rejected, 'source_race'):
                self.run_state(git)

    def test_membership_change_during_reads_rejected(self):
        original = p.stable_bytes
        def read(path):
            value = original(path)
            if path.name == '00.json':
                (self.root / 'tools/extra.ignored').write_bytes(b'race')
            return value
        with mock.patch.object(p, 'stable_bytes', read):
            with self.assertRaisesRegex(p.Rejected, 'untracked_or_ignored_build_input'):
                self.run_state()


if __name__ == '__main__':
    unittest.main()
