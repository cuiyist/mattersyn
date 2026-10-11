import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import release_batch as rb


class ExtractedRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=BASE)
        self.dist = Path(self.temp.name)
        self.source, self.rid, self.doi = 'local-extracted-source', 'local-extracted-core', '10.1234/local'
        self.record = {'record_id': self.rid, 'lineage': {'source_group': self.source},
                       'quality': {'review_status': 'source_extracted'}, 'sources': [{'id': self.source, 'doi': self.doi}]}
        self.row = {'source_group': self.source, 'paper_id': self.source, 'doi': self.doi,
                    'review_status': 'source_extracted', 'main_status': 'extracted_not_expert_reviewed',
                    'review_scope': 'Local-model extraction; not independently audited.',
                    'documents': [{'role': 'main', 'page_count': 4, 'pages_read': [2, 3],
                                   'all_text_read': False, 'all_visually_reviewed': False}],
                    'paper_review_url': None, 'record_ids': [self.rid],
                    'evidence_locator': f'data/records/{self.rid}.json',
                    'record_urls': {self.rid: f'records/{self.rid}.html'}}
        self.flush()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, rel, data):
        target = self.dist / rel; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data if isinstance(data, str) else json.dumps(data), encoding='utf-8')

    def flush(self):
        self.put('data/paper-review-index.json', {'papers': []})
        self.put('data/inventory-summary.json', {'per_paper': [self.row]})
        self.put(f'data/records/{self.rid}.json', self.record)
        self.put(f'records/{self.rid}.html', '<html>Source extracted</html>')

    def routes(self):
        return rb.new_paper_routes(self.dist, {self.source: [self.rid]})

    def test_exact_extracted_route_preserves_bound_data_and_inventory(self):
        route = self.routes()[self.source]
        self.assertEqual(route['route'], f'records/{self.rid}.html')
        self.assertEqual(route['data'], f'data/records/{self.rid}.json')
        self.assertEqual(route['inventory'], 'data/inventory-summary.json')

    def test_one_page_extracted_paper_is_valid_without_changing_audited_scope(self):
        doc = self.row['documents'][0]
        doc.update(page_count=1, pages_read=[1], all_text_read=True)
        self.flush()
        self.assertEqual(self.routes()[self.source]['page'], f'records/{self.rid}.html')
        self.assertFalse(rb.selected_page_scope([doc]))

    def test_extract_cannot_claim_an_independent_audit(self):
        self.row['main_status'] = 'scoped_independently_audited'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()
        self.row['main_status'] = 'extracted_not_expert_reviewed'
        self.row['documents'][0]['all_visually_reviewed'] = True
        self.flush()
        with self.assertRaises(SystemExit): self.routes()

    def test_every_record_must_have_source_extracted_status(self):
        for status in ('source_reviewed', 'reviewed', None):
            self.record['quality']['review_status'] = status
            self.flush()
            with self.assertRaisesRegex(SystemExit, 'differently labelled record'):
                self.routes()

    def test_bad_pages_and_full_read_claims_are_rejected(self):
        original = dict(self.row['documents'][0])
        for change in ({'pages_read': [2, 2]}, {'pages_read': [0]}, {'pages_read': [5]},
                       {'pages_read': [True]}, {'page_count': True}, {'all_text_read': 0},
                       {'all_text_read': True}, {'role': 'si'}):
            self.row['documents'][0] = dict(original, **change)
            self.flush()
            with self.assertRaises(SystemExit): self.routes()

    def test_identity_and_browser_route_checks_remain_active(self):
        self.record['sources'][0]['doi'] = '10.1234/other'; self.flush()
        with self.assertRaisesRegex(SystemExit, 'record identity differs'):
            self.routes()
        self.record['sources'][0]['doi'] = self.doi; self.flush()
        (self.dist / f'records/{self.rid}.html').unlink()
        with self.assertRaisesRegex(SystemExit, 'not a local built page'):
            self.routes()


if __name__ == '__main__':
    unittest.main()
