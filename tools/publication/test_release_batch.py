"""Offline tests for release_batch.py (synthetic trees and fake network responses only).

The end-to-end path was additionally checked against the real repositories: a dry run
of source 844c5121 reproduced the live site exactly, and the same source staged onto the
previous site release reproduced the published Zhang 2011 release byte for byte.
"""
import hashlib, io, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

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

    def live(self, dist, served, routes=None, materials=None):
        def opener(req, timeout):
            rel = req.full_url.split('/site/', 1)[1].split('?', 1)[0]
            return FakeResponse(served[rel])
        return rb.verify_live('https://example.test/site/', dist, 'c' * 40, routes, materials, sample=10,
                              timeout_s=0, opener=opener, sleep=lambda s: None)

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

    def test_changed_files_are_mandatory_beyond_existing_global_sample(self):
        with tempfile.TemporaryDirectory() as t:
            dist=Path(t);snap=json.dumps({'source_commit':'c'*40}).encode()
            write(dist,'data/release-snapshot.json',snap);write(dist,'index.html','home')
            write(dist,'data/dataset-manifest.json','{}');write(dist,'styles.css','new')
            served={name:path.read_bytes() for name,path in rb.tree_files(dist).items()}
            def opener(req,timeout):
                return FakeResponse(served[req.full_url.split('/site/',1)[1].split('?',1)[0]])
            args={'sample':0,'timeout_s':0,'opener':opener,'sleep':lambda _:None,'changed_paths':['styles.css']}
            report=rb.verify_live('https://example.test/site/',dist,'c'*40,**args)
            self.assertTrue(report['passed']);self.assertEqual(report['checked_changed_files'],['styles.css'])
            self.assertEqual(report['checked_files'],4) # all global files retained even sample=0
            served['styles.css']=b'old'
            report=rb.verify_live('https://example.test/site/',dist,'c'*40,**args)
            self.assertFalse(report['passed']);self.assertIn('styles.css',report['mismatched_files'])
            for invalid in [['../private'],['missing'],['styles.css','styles.css']]:
                args['changed_paths']=invalid
                self.assertFalse(rb.verify_live('https://example.test/site/',dist,'c'*40,**args)['passed'])

    def test_live_check_times_out_on_old_snapshot(self):
        with tempfile.TemporaryDirectory() as t:
            dist = Path(t); write(dist, 'index.html', 'home')
            served = {'data/release-snapshot.json': json.dumps({'source_commit': 'old'}).encode()}
            self.assertFalse(self.live(dist, served)['passed'])

    def test_every_new_paper_route_and_backing_data_is_mandatory(self):
        with tempfile.TemporaryDirectory() as t:
            dist = Path(t); snap = json.dumps({'source_commit': 'c' * 40}).encode()
            write(dist, 'data/release-snapshot.json', snap); write(dist, 'index.html', 'home')
            write(dist, 'paper-review.html', 'paper shell')
            write(dist, 'data/paper-reviews/a.json', 'a'); write(dist, 'data/paper-reviews/b.json', 'b')
            routes = {'a': {'route': 'paper-review.html?id=a', 'page': 'paper-review.html', 'data': 'data/paper-reviews/a.json'},
                      'b': {'route': 'paper-review.html?id=b', 'page': 'paper-review.html', 'data': 'data/paper-reviews/b.json'}}
            served = {name: path.read_bytes() for name, path in rb.tree_files(dist).items()}
            self.assertEqual(self.live(dist, served, routes)['checked_paper_routes'], ['a', 'b'])
            served['data/paper-reviews/b.json'] = b'stale'
            result = self.live(dist, served, routes)
            self.assertFalse(result['passed']); self.assertEqual(result['failed_paper_routes'], ['b'])

    def test_every_affected_material_page_and_shard_is_mandatory(self):
        with tempfile.TemporaryDirectory() as t:
            dist = Path(t); snap = json.dumps({'source_commit': 'c' * 40}).encode()
            write(dist, 'data/release-snapshot.json', snap); write(dist, 'index.html', 'home')
            write(dist, 'material.html', 'hub shell'); write(dist, 'cdse.html', 'special hub')
            write(dist, 'data/materials-index.json', '{}')
            write(dist, 'data/materials/ordinary.json', 'ordinary')
            write(dist, 'data/materials/cdse.json', 'cdse')
            materials = {'paper-a': [
                {'id': 'ordinary', 'route': 'material.html?id=ordinary', 'page': 'material.html',
                 'data': 'data/materials/ordinary.json'},
                {'id': 'cdse', 'route': 'cdse.html', 'page': 'cdse.html', 'data': 'data/materials/cdse.json'}]}
            served = {name: path.read_bytes() for name, path in rb.tree_files(dist).items()}
            self.assertEqual(self.live(dist, served, materials=materials)['checked_material_routes'],
                             ['paper-a:ordinary', 'paper-a:cdse'])
            served['data/materials/ordinary.json'] = b'stale'
            result = self.live(dist, served, materials=materials)
            self.assertFalse(result['passed'])
            self.assertEqual(result['failed_material_routes'], ['paper-a:ordinary'])
            served['data/materials/ordinary.json'] = b'ordinary'
            served['data/materials-index.json'] = b'stale'
            self.assertFalse(self.live(dist, served, materials=materials)['passed'])


class LedgerTests(unittest.TestCase):
    def test_events_accepted_by_metrics_tool(self):
        events = rb.ledger_events({'paper-a': ['r1'], 'paper-b': ['r2', 'r3']}, 'd' * 40, 'https://example.test/site/', 'e' * 64,
                                  '2026-10-01T01:00:00+00:00')
        result = pw.event_metrics(events, '2026-10-01T00:00:00Z', '2026-10-01T02:00:00Z')
        self.assertEqual(result['new_distinct_source_papers'], 2)

    def test_reverification_does_not_append_duplicate_live_events(self):
        with tempfile.TemporaryDirectory() as t:
            ledger = Path(t) / 'ledger.jsonl'
            first = rb.ledger_events({'paper-a': ['r1']}, 'd' * 40, 'https://example.test/', 'e' * 64, '2026-10-01T01:00:00Z')
            retry = rb.ledger_events({'paper-a': ['r1']}, 'd' * 40, 'https://example.test/', 'f' * 64, '2026-10-01T01:05:00Z')
            self.assertEqual(rb.append_ledger_events(ledger, first), 1)
            self.assertEqual(rb.append_ledger_events(ledger, retry), 0)
            self.assertEqual(len(ledger.read_text().splitlines()), 1)
            retry[0]['record_ids'] = ['wrong']
            with self.assertRaisesRegex(SystemExit, 'conflicting ledger event id'):
                rb.append_ledger_events(ledger, retry)


class ReleaseFlowTests(unittest.TestCase):
    def test_dry_run_preserves_site_then_exact_review_push_and_reverify(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); source, site, work, remote = (root / name for name in ('source', 'site', 'work', 'remote.git'))
            real_run = rb.run

            def git(*args):
                subprocess.run(['git', *map(str, args)], check=True, capture_output=True)

            for repo in (source, site):
                repo.mkdir(); git('-C', repo, 'init', '-q'); git('-C', repo, 'config', 'user.email', 'test@example.invalid')
                git('-C', repo, 'config', 'user.name', 'Test')
            write(source, 'publication/asset-rights-registry.json', '{}')
            write(source, 'publication/public-release-policy.json', '{}')
            write(site, 'index.html', 'old home')
            for path in ('.release-control/site-allowlist.json', '.release-control/asset-rights-registry.json',
                         '.release-control/site-policy.json', 'tools/mattersyn-release/export_release.py'):
                write(site, path, '{}')
            for repo in (source, site):
                git('-C', repo, 'add', '-A'); git('-C', repo, 'commit', '-qm', 'base')
            git('init', '--bare', '-q', remote); git('-C', site, 'remote', 'add', 'origin', remote)
            source_commit = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip()

            def fake_run(cmd, cwd=None):
                args = [str(x) for x in cmd]
                def write_arg(flag, value):
                    # Windows runners may expose the temporary directory through
                    # both its 8.3 alias and its long path. Write the requested
                    # absolute output without comparing those spellings.
                    path = Path(args[args.index(flag) + 1])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(value, encoding='utf-8')
                if args[0] == 'git':
                    return real_run(cmd, cwd)
                if args[1].endswith('make_runtime_snapshot.py'):
                    write_arg('--output', '{}')
                elif args[1].endswith('prepare_allowlist.py'):
                    write_arg('--out', '{}')
                elif args[1].endswith('build_release.py'):
                    dist = Path(args[args.index('--output') + 1]) / 'project/recipe-atlas/dist'
                    write(dist, 'index.html', 'new home')
                    write(dist, 'paper-review.html', 'paper shell')
                    write(dist, 'material.html', 'material shell')
                    write(dist, 'data/release-snapshot.json', json.dumps({'source_commit': source_commit}))
                    write(dist, 'data/records/r1.json', record('r1', 'paper-a'))
                    write(dist, 'data/paper-review-index.json', json.dumps({'papers': [
                        {'id': 'paper-a', 'record_ids': ['r1'], 'url': 'paper-review.html?id=paper-a'}]}))
                    write(dist, 'data/paper-reviews/paper-a.json', '{}')
                    write(dist, 'data/materials-index.json', json.dumps({'materials': [
                        {'id': 'material-a', 'url': 'material.html?id=material-a'}]}))
                    write(dist, 'data/materials/material-a.json', json.dumps({'id': 'material-a', 'record_ids': ['r1']}))
                elif len(args) > 2 and args[1] == '-B' and args[2].endswith('export_release.py'):
                    write_arg('--manifest-out', '{}')
                    write_arg('--report-out', '{"status":"passed"}')
                    Path(args[args.index('--destination') + 1]).mkdir()
                else:
                    self.fail(f'unexpected command: {args}')
                return ''

            base = ['release_batch.py', '--source', str(source), '--site', str(site), '--work', str(work),
                    '--release-id', 'test-batch', '--reviewer', 'auditor']
            with mock.patch.object(rb, 'run', side_effect=fake_run), mock.patch.object(sys, 'argv', base + ['--skip-ci-check']):
                self.assertEqual(rb.main(), 0)
            self.assertEqual((site / 'index.html').read_text(), 'old home')
            self.assertEqual(subprocess.check_output(['git', '-C', site, 'status', '--porcelain'], text=True), '')
            self.assertEqual((work / 'site-preview/index.html').read_text(), 'new home')
            plan = json.loads((work / 'release-plan.json').read_text())
            self.assertEqual(plan['review_routes'], ['material.html?id=material-a', 'paper-review.html?id=paper-a'])

            with mock.patch.object(sys, 'argv', base + ['--push', '--verify']):
                with self.assertRaisesRegex(SystemExit, 'review-receipt'):
                    rb.main()
            review = json.loads((work / 'browser-review.template.json').read_text())
            review.update(passed=True, reviewer='browser reviewer', reviewed_at='2026-10-01T00:50:00Z',
                          checked_routes=plan['review_routes'])
            receipt = work / 'browser-review.json'; rb.write_json(receipt, review)
            push_args = base + ['--review-receipt', str(receipt), '--push', '--verify']
            final_home = work / 'final/project/recipe-atlas/dist/index.html'
            final_home.write_text('changed after review')
            with mock.patch.object(sys, 'argv', push_args):
                with self.assertRaisesRegex(SystemExit, 'final_tree_sha256'):
                    rb.main()
            final_home.write_text('new home')
            bad_review = dict(review, candidate_tree_sha256='0' * 64)
            rb.write_json(receipt, bad_review)
            with mock.patch.object(sys, 'argv', push_args):
                with self.assertRaisesRegex(SystemExit, 'candidate_tree_sha256'):
                    rb.main()
            rb.write_json(receipt, review)
            self.assertEqual(subprocess.check_output(['git', '-C', site, 'status', '--porcelain'], text=True), '')
            live = {'passed': True, 'checked_files': 3, 'mismatched_files': [],
                    'checked_paper_routes': ['paper-a'], 'failed_paper_routes': [],
                    'checked_material_routes': ['paper-a:material-a'], 'failed_material_routes': [],
                    'verified_at': '2026-10-01T01:00:00Z'}
            ledger = root / 'ledger.jsonl'
            with (mock.patch.object(rb, 'wait_for_ci', return_value=(True, [])),
                  mock.patch.object(rb, 'verify_live', return_value=live),
                  mock.patch.object(sys, 'argv', base + ['--review-receipt', str(receipt), '--push', '--verify', '--ledger', str(ledger)])):
                self.assertEqual(rb.main(), 0)
            self.assertEqual((site / 'index.html').read_text(), 'new home')
            self.assertEqual(subprocess.check_output(['git', '-C', site, 'status', '--porcelain'], text=True), '')
            with mock.patch.object(rb, 'verify_live', return_value=live), mock.patch.object(sys, 'argv', base + ['--verify', '--ledger', str(ledger)]):
                self.assertEqual(rb.main(), 0)
            self.assertEqual(len(ledger.read_text().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
