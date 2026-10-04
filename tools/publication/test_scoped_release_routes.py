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
                    'review_scope_kind': 'scoped_independent_audit',
                    'review_scope_contract_version': 1,
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
                       'scoped_synthesis_and_figures_independently_audited',
                       'main_screen_hold_scoped_independently_audited',
                       'all_main_pages_scoped_independently_audited',
                       'main_pp1_2_scoped_independently_audited'):
            with self.subTest(status=status):
                self.row['main_status'] = status
                self.flush()
                self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')

        self.row['main_status'] = 'main_screen_hold'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()

    def test_typed_status_rejects_unreviewed_and_unknown_versions(self):
        for status in ('selected_method_unreviewed', 'not_independently_audited',
                       'main_screen_hold', 'new_plausible_audit_wording'):
            with self.subTest(status=status):
                self.row['main_status'] = status
                self.flush()
                with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
                    self.routes()
        self.row['main_status'] = 'selected_colloidal_method_and_figure_independently_audited'
        for kind, version in ((None, 1), ('scoped_independent_audit', None),
                              ('pending', 1), ('scoped_independent_audit', 3),
                              ('scoped_independent_audit', True)):
            with self.subTest(kind=kind, version=version):
                self.row['review_scope_kind'] = kind
                self.row['review_scope_contract_version'] = version
                self.flush()
                with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
                    self.routes()

    def test_new_frozen_enum_uses_one_canonical_status(self):
        self.row['review_scope_contract_version'] = 2
        self.row['main_status'] = 'scoped_independently_audited'
        self.flush()
        self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')
        self.row['main_status'] = 'not_independently_audited'
        self.flush()
        with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
            self.routes()

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

    def test_complete_document_flags_preserve_scoped_record_route(self):
        self.row['documents'][0]['pages_read'] = list(range(1, 7))
        self.row['review_scope'] = 'All main pages read; scoped preparation audit only; SI excluded.'
        self.row['review_scope_contract_version'] = 2
        self.row['main_status'] = 'scoped_independently_audited'
        for text_read, visual_read in ((True, True), (True, False), (False, True), (False, False)):
            with self.subTest(text_read=text_read, visual_read=visual_read):
                self.row['documents'][0].update(all_text_read=text_read, all_visually_reviewed=visual_read)
                self.flush()
                self.assertEqual(self.routes()[self.source]['route'], f'records/{self.rid}.html')
                self.assertEqual(self.routes()[self.source]['inventory'], 'data/inventory-summary.json')

    def test_either_complete_flag_requires_every_page_for_each_document(self):
        for role in ('main', 'si'):
            for flags in ((True, False), (False, True), (True, True)):
                for pages in ([1], [1, 2, 3], [2, 3, 4, 5, 6]):
                    with self.subTest(role=role, flags=flags, pages=pages):
                        doc = {'role': role, 'page_count': 6, 'pages_read': pages,
                               'all_text_read': flags[0], 'all_visually_reviewed': flags[1]}
                        documents = [doc] if role == 'main' else [self.row['documents'][0], doc]
                        self.assertFalse(rb.selected_page_scope(documents))
                doc['pages_read'] = list(range(1, 7))
                self.assertTrue(rb.selected_page_scope(documents))

    def test_document_flags_and_page_identifiers_are_strictly_typed(self):
        original = self.row['documents'][0]
        for key in ('all_text_read', 'all_visually_reviewed'):
            for value in (None, 0, 1, 'false', 'true', [], {}):
                with self.subTest(key=key, value=value):
                    doc = dict(original, pages_read=list(range(1, 7)))
                    doc[key] = value
                    self.assertFalse(rb.selected_page_scope([doc]))
            doc = dict(original)
            del doc[key]
            self.assertFalse(rb.selected_page_scope([doc]))
        for value in (None, True, 1, 0, -1, '6', 6.0):
            self.assertFalse(rb.selected_page_scope([dict(original, page_count=value)]))
        for pages in (None, [], (1, 2), '123', [True, 2], [1.0, 2], ['1', 2],
                      [1, None], [1, {}], [1, []], [0, 1], [-1, 1], [1, 7], [1, 1], [2, 1]):
            with self.subTest(pages=pages):
                self.assertFalse(rb.selected_page_scope([dict(original, pages_read=pages)]))

        self.assertFalse(rb.selected_page_scope([dict(original, page_count=10**100, all_text_read=True)]))

    def test_complete_reading_does_not_bypass_scope_or_identity(self):
        self.row['documents'][0].update(pages_read=list(range(1, 7)), all_text_read=True,
                                        all_visually_reviewed=True)
        for key, bad_value in (('main_status', 'not_independently_audited'),
                               ('review_status', 'formal_paper_review'),
                               ('review_scope_kind', 'complete_paper_review'),
                               ('review_scope_contract_version', True),
                               ('review_scope', ''),
                               ('paper_review_url', 'paper-review.html?id=unverified'),
                               ('record_ids', ['other-record']), ('paper_id', 'other-paper')):
            with self.subTest(key=key):
                original = self.row[key]
                self.row[key] = bad_value
                self.flush()
                with self.assertRaisesRegex(SystemExit, 'independently audited scoped inventory'):
                    self.routes()
                self.row[key] = original

    def test_document_roles_and_count_remain_bounded(self):
        main = dict(self.row['documents'][0])
        si = dict(main, role='si')
        for documents in (None, {}, [], [None], ['main'], [si], [main, main],
                          [main, si, si], [main, dict(si, role='unknown')], [main, []]):
            with self.subTest(documents=documents):
                self.assertFalse(rb.selected_page_scope(documents))

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
