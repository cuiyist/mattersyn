"""Anonymous file verification keeps every probe and gate with bounded concurrency."""
import io
import json
from pathlib import Path
import random
import tempfile
import threading
import time
import unittest
from urllib.error import URLError
from urllib.parse import urlsplit, parse_qs
import release_batch as rb


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class ParallelLiveVerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dist = Path(self.temp.name)
        self.commit = 'c' * 40
        self.served = {}
        self.calls = []
        self.lock = threading.Lock()
        self.active = self.peak = 0
        self.failures = set()
        self.stale = set()
        self.write('index.html', b'home')
        self.write('data/dataset-manifest.json', b'{}')
        self.write('data/release-snapshot.json', json.dumps({'source_commit': self.commit}).encode())
        self.changed = []
        for number in range(24):
            name = f'assets/change-{number:02}.css'
            self.write(name, f'style {number}'.encode()); self.changed.append(name)
        for number in range(10): self.write(f'unchanged-{number:02}.html', f'page {number}'.encode())

    def tearDown(self): self.temp.cleanup()

    def write(self, name, data):
        target = self.dist / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data); self.served[name] = data

    def opener(self, request, timeout):
        parsed = urlsplit(request.full_url)
        name = parsed.path.split('/site/', 1)[1]
        headers = {k.lower(): v for k, v in request.headers.items()}
        self.assertEqual(headers.get('cache-control'), 'no-cache')
        self.assertNotIn('authorization', headers)
        self.assertNotIn('cookie', headers)
        self.assertEqual(timeout, 60)
        self.assertTrue(parse_qs(parsed.query).get('v'))
        is_parallel = threading.current_thread() is not threading.main_thread()
        with self.lock:
            self.calls.append((name, parsed.query, is_parallel))
            if is_parallel:
                self.active += 1; self.peak = max(self.peak, self.active)
        try:
            if is_parallel:
                # Reverse relative completion timing; receipt order must still
                # follow the original probe list rather than arrival order.
                delay = 0.004 + (24 - int(name[-6:-4])) * 0.0002 if name.startswith('assets/change-') else 0.008
                time.sleep(delay)
            if name in self.failures: raise URLError('synthetic unavailable asset')
            return Response(b'stale' if name in self.stale else self.served[name])
        finally:
            if is_parallel:
                with self.lock: self.active -= 1

    def verify(self, **kwargs):
        return rb.verify_live('https://example.test/site/', self.dist, self.commit,
                              sample=kwargs.pop('sample', 0), timeout_s=0, opener=self.opener,
                              sleep=lambda _: None, changed_paths=self.changed, **kwargs)

    def test_every_changed_file_is_checked_with_at_most_eight_parallel_workers(self):
        report = self.verify()
        self.assertTrue(report['passed'])
        self.assertEqual(report['checked_changed_files'], sorted(self.changed))
        self.assertEqual(report['checked_files'], 27)  # 24 changes and all three globals
        probes = [name for name, _, parallel in self.calls if parallel]
        self.assertEqual(set(probes), set(self.changed) | {'index.html', 'data/dataset-manifest.json', 'data/release-snapshot.json'})
        self.assertEqual(len(probes), len(set(probes)))
        self.assertGreater(self.peak, 1)
        self.assertLessEqual(self.peak, 8)

    def test_hash_and_request_failures_both_fail_without_omitting_other_changes(self):
        self.failures = {'assets/change-03.css', 'assets/change-23.css'}
        self.stale = {'assets/change-12.css'}
        report = self.verify()
        self.assertFalse(report['passed'])
        self.assertEqual(report['mismatched_files'], ['assets/change-03.css', 'assets/change-12.css', 'assets/change-23.css'])
        self.assertEqual(set(report['checked_changed_files']) | set(report['mismatched_files']), set(self.changed))
        probes = [name for name, _, parallel in self.calls if parallel]
        self.assertTrue(set(self.changed).issubset(probes))
        self.assertEqual(len(probes), 27)

    def test_original_seeded_sample_and_all_changes_remain_the_same_probe_set(self):
        report = self.verify(sample=8)
        must = ['index.html', 'data/dataset-manifest.json', 'data/release-snapshot.json']
        rest = sorted(set(self.served) - set(must)); random.Random(self.commit).shuffle(rest)
        expected = list(dict.fromkeys(must + rest[:5] + sorted(self.changed)))
        probes = [name for name, _, parallel in self.calls if parallel]
        self.assertEqual(set(probes), set(expected))
        self.assertEqual(len(probes), len(expected))
        self.assertEqual(report['checked_files'], len(expected))

    def test_mandatory_routes_still_run_after_all_file_probes_and_can_fail(self):
        self.write('records/new.html', b'record page')
        self.write('data/records/new.json', b'record data')
        self.write('material.html', b'material page')
        self.write('data/materials/new.json', b'material data')
        self.write('data/materials-index.json', b'{}')
        papers = {'new-paper': {'route': 'records/new.html?method=new', 'page': 'records/new.html', 'data': 'data/records/new.json'}}
        materials = {'new-paper': [{'id': 'new-material', 'route': 'material.html?id=new', 'page': 'material.html', 'data': 'data/materials/new.json'}]}
        self.stale = {'data/materials/new.json'}
        report = self.verify(paper_routes=papers, material_routes=materials)
        self.assertFalse(report['passed'])
        self.assertEqual(report['checked_paper_routes'], ['new-paper'])
        self.assertEqual(report['failed_material_routes'], ['new-paper:new-material'])
        last_parallel = max(i for i, (_, _, parallel) in enumerate(self.calls) if parallel)
        route_calls = self.calls[last_parallel + 1:]
        self.assertTrue(route_calls)
        self.assertTrue(all(not parallel for _, _, parallel in route_calls))
        self.assertIn('method=new', route_calls[0][1])
        self.assertIn('data/materials-index.json', [name for name, _, parallel in self.calls if parallel])


if __name__ == '__main__': unittest.main(verbosity=2)
