"""Offline tests for release_batch.py (synthetic trees and fake network responses only).

The end-to-end path was additionally checked against the real repositories: a dry run
of source 844c5121 reproduced the live site exactly, and the same source staged onto the
previous site release reproduced the published Zhang 2011 release byte for byte.
"""
import hashlib, io, json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workflow'))
import release_batch as rb
import package_workflow as pw


def write(root, rel, data):
    p = Path(root) / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode()); return p


def record(rid, source):
    return json.dumps({'record_id': rid, 'lineage': {'source_group': source}})


class FakeResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


class StageTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); r = Path(self.t.name)
        self.dist, self.site = r / 'dist', r / 'site'
        write(self.dist, 'index.html', 'new home'); write(self.dist, 'data/records/b.json', record('b', 'paper-b'))
        write(self.dist, 'same.txt', 'same')
        write(self.site, 'index.html', 'old home'); write(self.site, 'same.txt', 'same'); write(self.site, 'stale/old.html', 'x')
        for keep in ('.release-control/site-allowlist.json', '.github/workflows/pages.yml', 'tools/mattersyn-release/gate.py', '.gitattributes'):
            write(self.site, keep, 'control')
    def tearDown(self): self.t.cleanup()

    def test_stage_adds_changes_removes_and_keeps_controls(self):
        added, changed, removed = rb.stage_dist(self.dist, self.site)
        self.assertEqual(added, ['data/records/b.json']); self.assertEqual(changed, ['index.html']); self.assertEqual(removed, ['stale/old.html'])
        self.assertFalse((self.site / 'stale').exists(), 'empty directories are removed')
        for keep in ('.release-control/site-allowlist.json', '.github/workflows/pages.yml', 'tools/mattersyn-release/gate.py', '.gitattributes'):
            self.assertEqual((self.site / keep).read_text(), 'control')
        self.assertEqual(rb.stage_dist(self.dist, self.site), ([], [], []), 'second staging is a no-op')

    def test_build_output_may_not_overwrite_controls(self):
        write(self.dist, 'tools/evil.py', 'x')
        with self.assertRaises(SystemExit): rb.stage_dist(self.dist, self.site)

    def test_new_papers_counted_by_source_group(self):
        write(self.site, 'data/records/a.json', record('a', 'paper-a'))
        write(self.dist, 'data/records/a.json', record('a', 'paper-a')); write(self.dist, 'data/records/b2.json', record('b2', 'paper-b'))
        self.assertEqual(rb.new_papers(self.site, self.dist), {'paper-b': ['b', 'b2']})


class SiteHistoryTests(unittest.TestCase):
    def test_papers_added_by_last_site_commit(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            g=lambda *x: subprocess.run(['git','-C',d,*x],check=True,capture_output=True)
            g('init','-q'); g('config','user.email','t@example.invalid'); g('config','user.name','t')
            write(d,'data/records/a.json',record('a','paper-a')); g('add','-A'); g('commit','-qm','one')
            write(d,'data/records/b.json',record('b','paper-b')); write(d,'data/records/a.json',record('a','paper-a')+' ')
            write(d,'data/release-snapshot.json',json.dumps({'source_commit':'f'*40})); g('add','-A'); g('commit','-qm','two')
            self.assertEqual(rb.papers_added_by_last_site_commit(d),{'paper-b':['b']})
            self.assertTrue(rb.site_built_from(d,'f'*40)); self.assertFalse(rb.site_built_from(d,'0'*40))

class NetworkTests(unittest.TestCase):
    def test_ci_check_requires_named_successful_run(self):
        runs = {'workflow_runs': [{'name': 'Other', 'conclusion': 'success'}, {'name': rb.CI_WORKFLOW, 'status': 'completed', 'conclusion': 'failure'}]}
        ok, _ = rb.source_ci_passed('o/r', 'a' * 40, opener=lambda req, timeout: FakeResponse(json.dumps(runs).encode()))
        self.assertFalse(ok)
        runs['workflow_runs'].append({'name': rb.CI_WORKFLOW, 'status': 'completed', 'conclusion': 'success'})
        ok, _ = rb.source_ci_passed('o/r', 'a' * 40, opener=lambda req, timeout: FakeResponse(json.dumps(runs).encode()))
        self.assertTrue(ok)

    def test_wait_for_ci_polls_until_success_and_stops_on_failure(self):
        seq=[[{'name': rb.CI_WORKFLOW, 'status': 'in_progress', 'conclusion': None}],
             [{'name': rb.CI_WORKFLOW, 'status': 'completed', 'conclusion': 'success'}]]
        calls=[]
        def opener(req, timeout):
            calls.append(1); return FakeResponse(json.dumps({'workflow_runs': seq[min(len(calls)-1, 1)]}).encode())
        self.assertTrue(rb.wait_for_ci('o/r', 'a'*40, 5, opener=opener, sleep=lambda s: None)[0]); self.assertEqual(len(calls), 2)
        failed=lambda req, timeout: FakeResponse(json.dumps({'workflow_runs': [{'name': rb.CI_WORKFLOW, 'status': 'completed', 'conclusion': 'failure'}]}).encode())
        self.assertFalse(rb.wait_for_ci('o/r', 'a'*40, 5, opener=failed, sleep=lambda s: None)[0])

    def live(self, dist, served):
        def opener(req, timeout):
            rel = req.full_url.split('/site/', 1)[1].split('?', 1)[0]
            return FakeResponse(served[rel])
        return rb.verify_live('https://example.test/site/', dist, 'c' * 40, sample=10, timeout_s=0, opener=opener, sleep=lambda s: None)

    def test_live_check_passes_only_on_matching_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            dist = Path(t)
            snap = json.dumps({'source_commit': 'c' * 40}).encode()
            write(dist, 'data/release-snapshot.json', snap); write(dist, 'index.html', 'home'); write(dist, 'a.html', 'a')
            served = {'data/release-snapshot.json': snap, 'index.html': b'home', 'a.html': b'a'}
            self.assertTrue(self.live(dist, served)['passed'])
            served['a.html'] = b'stale'
            result = self.live(dist, served)
            self.assertFalse(result['passed']); self.assertEqual(result['mismatched_files'], ['a.html'])

    def test_live_check_times_out_on_old_snapshot(self):
        with tempfile.TemporaryDirectory() as t:
            dist = Path(t); write(dist, 'index.html', 'home')
            served = {'data/release-snapshot.json': json.dumps({'source_commit': 'old'}).encode()}
            self.assertFalse(self.live(dist, served)['passed'])


class LedgerTests(unittest.TestCase):
    def test_events_accepted_by_metrics_tool(self):
        events = rb.ledger_events({'paper-a': ['r1'], 'paper-b': ['r2', 'r3']}, 'd' * 40, 'https://example.test/site/', 'e' * 64,
                                  '2026-10-01T01:00:00+00:00')
        result = pw.event_metrics(events, '2026-10-01T00:00:00Z', '2026-10-01T02:00:00Z')
        self.assertEqual(result['new_distinct_source_papers'], 2)


if __name__ == '__main__':
    unittest.main()
