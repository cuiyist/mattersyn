"""Synthetic-only tests: identical complete tree pins, bounded concurrent reads."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_batch as rb


def legacy_digest(root, skip_top=()):
    rows = {name: rb.sha256(path) for name, path in rb.tree_files(root, skip_top).items()}
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class ParallelTreeDigestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, data):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def test_empty_tree_has_exact_original_digest(self):
        (self.root / 'empty-directory').mkdir()
        self.assertEqual(rb.tree_digest(self.root), legacy_digest(self.root))
        self.assertEqual(rb.tree_digest(self.root), hashlib.sha256(b'{}').hexdigest())

    def test_empty_binary_nested_and_unicode_files_match_serial(self):
        self.write('empty.bin', b'')
        self.write('binary.bin', bytes(range(256)) * 5000)  # exceeds the hash read chunk
        self.write('nested/sub/file.txt', b'invented fixture')
        self.write('unit-cell/\u6676\u683c-\u03b1.json', '{"formula":"CsPbBr3"}'.encode('utf-8'))
        self.assertEqual(rb.tree_digest(self.root), legacy_digest(self.root))

    def test_skip_top_and_file_set_are_unchanged_without_extra_paths(self):
        self.write('.git/ignored', b'control')
        self.write('tools/ignored', b'control')
        included = {self.write('data/a.json', b'{}'), self.write('nested/.git/kept.txt', b'kept')}
        (self.root / 'empty-directory').mkdir()
        hash_file = rb.sha256
        seen = []
        lock = threading.Lock()
        def recording(path):
            with lock:
                seen.append(path)
            return hash_file(path)
        expected = legacy_digest(self.root, ('.git', 'tools'))
        with mock.patch.object(rb, 'sha256', side_effect=recording):
            actual = rb.tree_digest(self.root, ('.git', 'tools'))
        self.assertEqual(actual, expected)
        self.assertEqual(set(seen), included)
        self.assertEqual(len(seen), len(included))

    def test_all_files_once_with_at_most_eight_workers(self):
        for number in range(32):
            self.write(f'file-{number:02}.bin', bytes([number]))
        hash_file = rb.sha256
        lock = threading.Lock()
        state = {'active': 0, 'peak': 0, 'seen': []}
        def delayed(path):
            with lock:
                state['active'] += 1
                state['peak'] = max(state['peak'], state['active'])
                state['seen'].append(path)
            try:
                time.sleep(0.01)
                return hash_file(path)
            finally:
                with lock:
                    state['active'] -= 1
        expected = legacy_digest(self.root)
        with mock.patch.object(rb, 'sha256', side_effect=delayed):
            actual = rb.tree_digest(self.root)
        self.assertEqual(actual, expected)
        self.assertEqual(set(state['seen']), set(rb.tree_files(self.root).values()))
        self.assertEqual(len(state['seen']), 32)
        self.assertGreater(state['peak'], 1)
        self.assertLessEqual(state['peak'], 8)
        self.assertEqual(state['active'], 0)

    def test_reverse_completion_and_discovery_order_do_not_change_digest(self):
        for number in range(12):
            self.write(f'file-{number:02}.bin', bytes([number]))
        hash_file = rb.sha256
        files = rb.tree_files(self.root)
        expected = legacy_digest(self.root)
        def delayed(path):
            time.sleep((12 - int(path.stem[-2:])) * 0.001)
            return hash_file(path)
        with mock.patch.object(rb, 'sha256', side_effect=delayed):
            self.assertEqual(rb.tree_digest(self.root), expected)
        with mock.patch.object(rb, 'tree_files', return_value=dict(reversed(list(files.items())))):
            self.assertEqual(rb.tree_digest(self.root), expected)

    def test_missing_file_after_enumeration_raises_without_swallowing(self):
        good = self.write('good.bin', b'good')
        missing = self.root / 'deleted-after-enumeration.bin'
        files = {'good.bin': good, 'deleted-after-enumeration.bin': missing}
        with mock.patch.object(rb, 'tree_files', return_value=files):
            with self.assertRaises(FileNotFoundError):
                legacy_digest(self.root)
            with self.assertRaises(FileNotFoundError):
                rb.tree_digest(self.root)

    def test_read_error_propagates_and_first_input_error_is_deterministic(self):
        first = self.write('first.bin', b'first')
        second = self.write('second.bin', b'second')
        files = {'first.bin': first, 'second.bin': second}
        def failing(path):
            if path == first:
                time.sleep(0.02)
                raise PermissionError('first-input read failure')
            raise OSError('later-input read failure')
        with mock.patch.object(rb, 'tree_files', return_value=files), mock.patch.object(rb, 'sha256', side_effect=failing):
            with self.assertRaisesRegex(PermissionError, 'first-input read failure'):
                legacy_digest(self.root)
            with self.assertRaisesRegex(PermissionError, 'first-input read failure'):
                rb.tree_digest(self.root)

    def test_repeated_call_rehashes_every_file_and_detects_changed_bytes(self):
        changed = self.write('changed.bin', b'before')
        self.write('stable.bin', b'stable')
        hash_file = rb.sha256
        with mock.patch.object(rb, 'sha256', wraps=hash_file) as tracked:
            before = rb.tree_digest(self.root)
            changed.write_bytes(b'after')
            after = rb.tree_digest(self.root)
        self.assertNotEqual(before, after)
        self.assertEqual(after, legacy_digest(self.root))
        self.assertEqual(tracked.call_count, 4)


if __name__ == '__main__':
    unittest.main()
