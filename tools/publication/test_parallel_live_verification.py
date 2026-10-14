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
                              sample=kwargs.pop('sample', 0), timeout_s=0, opener=kwargs.pop('opener', self.opener),
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
        first_route = next(i for i, (_, query, _) in enumerate(self.calls) if 'method=new' in query)
        file_probes = [name for name, _, parallel in self.calls[:first_route] if parallel]
        self.assertEqual(set(file_probes), set(self.changed) | {
            'index.html', 'data/dataset-manifest.json', 'data/release-snapshot.json', 'data/materials-index.json'})
        route_calls = self.calls[first_route:]
        self.assertTrue(route_calls)
        self.assertTrue(all(parallel for _, _, parallel in route_calls))
        self.assertIn('method=new', route_calls[0][1])


    def route_fixture(self):
        self.write('reader.html', b'invented Reader page')
        self.write('data/reader-a.json', b'invented Reader A')
        self.write('data/reader-b.json', b'invented Reader B')
        self.write('data/records.jsonl', b'invented record inventory')
        self.write('data/materials-index.json', b'invented material inventory')
        papers = {f'p{i:02}': {'route': f'reader.html?method=p{i:02}', 'page': 'reader.html',
                  'data': f'data/reader-{chr(97 + i % 2)}.json', 'inventory': 'data/records.jsonl'}
                  for i in reversed(range(16))}
        materials = {}
        for i in reversed(range(8)):
            self.write(f'data/materials/m{i}.json', f'invented material {i}'.encode())
            materials[f'p{i:02}'] = [{'id': f'm{i}', 'route': f'reader.html?id=m{i}',
                                    'page': 'reader.html', 'data': f'data/materials/m{i}.json',
                                    'inventory': 'data/materials-index.json'}]
        materials['p02'].append(dict(materials['p02'][0]))
        self.route_active = self.route_peak = 0
        self.route_page_failures = set()
        return papers, materials

    def route_opener(self, request, timeout):
        query = parse_qs(urlsplit(request.full_url).query)
        label = (query.get('method') or query.get('id') or [None])[0]
        if label is None:
            return self.opener(request, timeout)
        with self.lock:
            self.route_active += 1
            self.route_peak = max(self.route_peak, self.route_active)
        try:
            # Slow early labels so completion order differs from source order.
            time.sleep(0.006 + (15 - int(label[1:])) * 0.0002)
            response = self.opener(request, timeout)
            if label in self.route_page_failures:
                response.close()
                raise URLError('invented route-page failure')
            return response
        finally:
            with self.lock:
                self.route_active -= 1

    def test_route_workers_are_bounded_and_receipts_keep_binding_order(self):
        papers, materials = self.route_fixture()
        report = self.verify(paper_routes=papers, material_routes=materials, opener=self.route_opener)
        self.assertTrue(report['passed'])
        self.assertEqual(report['checked_paper_routes'], sorted(papers))
        self.assertEqual(report['checked_material_routes'],
                         [f"{source}:{binding['id']}" for source, bindings in sorted(materials.items())
                          for binding in bindings])
        self.assertGreater(self.route_peak, 1)
        self.assertLessEqual(self.route_peak, 8)
        paper_positions = [i for i, (_, query, _) in enumerate(self.calls) if 'method=' in query]
        material_positions = [i for i, (_, query, _) in enumerate(self.calls) if 'id=' in query]
        self.assertLess(max(paper_positions), min(material_positions))

    def test_repeated_route_GETs_are_not_cached_or_deduplicated(self):
        papers, materials = self.route_fixture()
        report = self.verify(paper_routes=papers, material_routes=materials, opener=self.route_opener)
        self.assertTrue(report['passed'])
        names = [name for name, _, _ in self.calls]
        self.assertEqual(names.count('data/reader-a.json'), 8)
        self.assertEqual(names.count('data/reader-b.json'), 8)
        self.assertEqual(names.count('data/records.jsonl'), 16)
        self.assertEqual(names.count('data/materials-index.json'), 10)  # one file probe and nine routes
        self.assertEqual(names.count('data/materials/m2.json'), 2)
        self.assertEqual(report['checked_material_routes'].count('p02:m2'), 2)

    def test_route_failures_keep_exact_order_and_check_remaining_bindings(self):
        papers, materials = self.route_fixture()
        self.route_page_failures = {'p03'}
        self.failures = {'data/reader-b.json'}
        self.stale = {'data/materials/m2.json'}
        report = self.verify(paper_routes=papers, material_routes=materials, opener=self.route_opener)
        self.assertFalse(report['passed'])
        self.assertEqual(report['failed_paper_routes'], [f'p{i:02}' for i in range(16) if i % 2])
        self.assertEqual(report['checked_paper_routes'], [f'p{i:02}' for i in range(16) if not i % 2])
        self.assertEqual(report['failed_material_routes'], ['p02:m2', 'p02:m2'])
        self.assertEqual(len(report['checked_material_routes']) + len(report['failed_material_routes']), 9)
        route_queries = [query for _, query, _ in self.calls if 'method=' in query or 'id=' in query]
        self.assertEqual(len(route_queries), 25)
        self.assertLessEqual(self.route_peak, 8)



if __name__ == '__main__': unittest.main(verbosity=2)
