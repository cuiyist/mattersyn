"""Focused tests for audited selected-page release routes."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_batch as rb


def put(root, rel, value):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')
    return path


class ScopedRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dist = Path(self.temp.name)
        self.source = 'fanfair2005-bi-cg0502587'
        self.rid = self.source + '-bi-seeds'
        self.doi = '10.1021/cg0502587'
        self.record = {'record_id': self.rid, 'lineage': {'source_group': self.source},
                       'sources': [{'id': self.source, 'doi': self.doi}]}
        self.row = {'source_group': self.source, 'paper_id': self.source, 'doi': self.doi,
                    'review_status': 'selected_recipe_and_figure_review',
                    'main_status': 'selected_colloidal_method_and_figure_independently_audited',
                    'review_scope': 'Main pp. 1–3 and Figure 1A/B only; remaining pages unreviewed.',
                    'documents': [{'role': 'main', 'page_count': 6, 'pages_read': [1, 2, 3],
                                   'all_text_read': False, 'all_visually_reviewed': False}],
                    'paper_review_url': None, 'record_ids': [self.rid],
                    'evidence_locator': f'data/records/{self.rid}.json',
                    'record_urls': {self.rid: f'records/{self.rid}.html'}}
        self.flush()

    def tearDown(self):
        self.temp.cleanup()

    def flush(self):
        put(self.dist, 'data/paper-review-index.json', {'papers': []})
        put(self.dist, 'data/inventory-summary.json', {'per_paper': [self.row]})
        put(self.dist, f'data/records/{self.rid}.json', self.record)
        put(self.dist, f'records/{self.rid}.html', '<html>Scoped record</html>')

    def routes(self):
        return rb.new_paper_routes(self.dist, {self.source: [self.rid]})

    def test_valid_scoped_route_binds_record_page_data_and_inventory(self):
        self.assertEqual(self.routes(), {self.source: {
            'route': f'records/{self.rid}.html', 'page': f'records/{self.rid}.html',
            'data': f'data/records/{self.rid}.json', 'inventory': 'data/inventory-summary.json'}})

    def test_missing_or_wrong_scoped_review_is_rejected(self):
        (self.dist / 'data/inventory-summary.json').unlink()
        with self.assertRaisesRegex(SystemExit, 'scoped inventory missing'):
            self.routes()
        self.row['review_status'] = 'supplied_main_only_si_unverified'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['review_status'] = 'selected_recipe_and_figure_review'
        self.row['main_status'] = 'selected_method_unreviewed'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['main_status'] = 'not_independently_audited'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()

    def test_scoped_pages_may_touch_every_page_without_claiming_complete_read(self):
        self.row['documents'][0]['pages_read'] = [1, 2, 3, 4, 5, 6]
        self.flush()
        self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')
        self.row['documents'][0]['pages_read'] = [1, 2, 3, 4, 5, 6, 7]
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()

    def test_selected_main_scope_can_name_essential_si_pages(self):
        self.row['documents'].append({'role': 'si', 'page_count': 13, 'pages_read': [1, 2, 3, 5, 6, 7],
                                      'all_text_read': False, 'all_visually_reviewed': False})
        self.flush()
        self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')
        self.row['documents'][1]['pages_read'] = [1, 2, 2]
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['documents'][1]['pages_read'] = [1, 2, 3]
        self.row['documents'][1]['all_text_read'] = True
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['documents'][0]['pages_read'] = [1, 2, 3]
        self.row['documents'][0]['all_text_read'] = True
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['documents'][0]['all_text_read'] = False
        self.row['documents'][0]['all_visually_reviewed'] = True
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['documents'][0]['all_visually_reviewed'] = False
        self.row['paper_review_url'] = 'paper-review.html?id=unverified'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()

    def test_independently_audited_scoped_status_aliases(self):
        for status in ('selected_as_prepared_cds_route_and_figures_independently_audited',
                       'selected_colloidal_methods_and_figures_independently_audited',
                       'selected_synthesis_and_figures_independently_audited',
                       'main_synthesis_and_figures_independently_audited',
                       'scoped_synthesis_and_figures_independently_audited'):
            with self.subTest(status=status):
                self.row['main_status'] = status
                self.flush()
                self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')

    def test_record_identity_and_coverage_are_required(self):
        self.row['record_ids'] = ['other-record']
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['record_ids'] = [self.rid]
        self.record['lineage']['source_group'] = 'another-source'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'record identity differs'):
            self.routes()
        self.record['lineage']['source_group'] = self.source
        self.row['evidence_locator'] = 'data/records/other-record.json'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'evidence locator'):
            self.routes()

    def test_changed_route_and_formal_review_missing_records_are_rejected(self):
        self.row['record_urls'][self.rid] = 'records/other-record.html'
        put(self.dist, 'records/other-record.html', '<html>Wrong record</html>')
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'route differs'):
            self.routes()
        self.row['record_urls'][self.rid] = f'records/{self.rid}.html'
        self.flush()
        put(self.dist, 'data/paper-review-index.json', {'papers': [
            {'id': self.source, 'record_ids': [], 'url': f'paper-review.html?id={self.source}'}]})
        with self.assertRaisesRegex(SystemExit, 'omits new records'):
            self.routes()

    def test_live_verification_requires_scoped_inventory_bytes(self):
        route = self.routes()
        put(self.dist, 'index.html', '<html>Home</html>')
        put(self.dist, 'data/release-snapshot.json', {'source_commit': 'c' * 40})
        served = {rel: path.read_bytes() for rel, path in rb.tree_files(self.dist).items()}

        def opener(req, timeout):
            rel = req.full_url.split('/site/', 1)[1].split('?', 1)[0]
            return io.BytesIO(served[rel])

        def verify():
            return rb.verify_live('https://example.test/site/', self.dist, 'c' * 40,
                                  route, sample=2, timeout_s=0, opener=opener, sleep=lambda _: None)

        self.assertEqual(verify()['checked_paper_routes'], [self.source])
        served['data/inventory-summary.json'] = b'changed after publication'
        result = verify()
        self.assertFalse(result['passed'])
        self.assertEqual(result['failed_paper_routes'], [self.source])


if __name__ == '__main__':
    unittest.main()
