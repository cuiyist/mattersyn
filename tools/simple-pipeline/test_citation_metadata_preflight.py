"""Citation metadata regressions; fixtures contain no paper/source/model payloads."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parent / 'citation_metadata_preflight.py'
SPEC = importlib.util.spec_from_file_location('citation_metadata_preflight', MODULE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def flags(authors, official):
    meta = {'title': 'Invented title', 'authors': authors, 'year': '2014', 'journal': 'Invented journal'}
    authority = {'citation': {'title': ['Invented title'], 'authors': official,
                              'published': {'date-parts': [[2014]]}}}
    return m.citation_flags(meta, authority)


class CitationMetadataPreflightTests(unittest.TestCase):
    def test_known_pal_family_misspelling(self):
        self.assertIn({'field': 'authors', 'category': 'doi_authority_author_identity_mismatch'},
                      flags('D. Pala and E. Towe', ['D. Pal', 'E. Towe']))

    def test_known_pierz_list_has_wrong_author_membership(self):
        authors = 'K. Pierz, H. W. Schumacher, M. Wenderoth, K. Tornau, H. Pfnür, R. G. Ulbricht'
        official = ['Karen Teichmann', 'Martin Wenderoth', 'Henning Prüser', 'Klaus Pierz', 'Hans W. Schumacher', 'Rainer G. Ulbrich']
        self.assertIn({'field': 'authors', 'category': 'doi_authority_author_identity_mismatch'}, flags(authors, official))

    def test_allowed_initial_full_name_and_separator_styles(self):
        cases = [
            ('D. Pal and E. Towe', ['Debasish Pal', 'Edward Towe']),
            ('D.Pal; E.Towe', ['Debasish Pal', 'Edward Towe']),
            ('Pal, D.; Towe, E.', ['Debasish Pal', 'Edward Towe']),
            ('Pal, Debasish', ['D. Pal']),
            ('L. Maingault, L. Besombes, and C. Bougerol', ['Lucien Maingault', 'L. Besombes', 'C. Bougerol']),
            ('J. M. Gerard', ['Jean-Michel Gérard']),
            ('H.W.Schumacher', ['Hans W. Schumacher']),
            ('Th. Schmidt; Ph. Roussignol; Yu. G. Kusrayev', ['Thomas Schmidt', 'Philippe Roussignol', 'Yuriy G. Kusrayev']),
            ('A. O’Connor & B. Stiff-Roberts', ["Alice O'Connor", 'Beatrice Stiff-Roberts']),
            ('J. Smith Jr.', ['John Smith']),
        ]
        for authors, official in cases:
            with self.subTest(authors=authors):
                self.assertEqual(flags(authors, official), [])

    def test_name_order_membership_and_initial_are_not_formatting(self):
        for authors in ('K. Pal; E. Towe', 'E. Towe; D. Pal', 'D. Pal', 'D. Pal; D. Pal'):
            with self.subTest(authors=authors):
                self.assertFalse(m.author_lists_agree(authors, ['Debasish Pal', 'Edward Towe']))

    def test_incomplete_list_retains_existing_flag(self):
        result = flags('X.J. Shang et al.', ['X. Shang', 'Y. Other'])
        self.assertIn({'field': 'authors', 'category': 'incomplete_author_list'}, result)
        self.assertNotIn({'field': 'authors', 'category': 'doi_authority_author_identity_mismatch'}, result)

    def test_existing_placeholder_and_affiliation_flags_remain(self):
        self.assertIn({'field': 'authors', 'category': 'missing_or_placeholder_citation'}, flags('', ['D. Pal']))
        self.assertIn({'field': 'authors', 'category': 'affiliation_or_footer_as_authors'}, flags('Department of Chemistry', ['D. Pal']))

    def test_cli_requires_explicit_valid_batch_without_writing_output(self):
        for batch in (None, '../batch31', 'batch0'):
            args = ['preflight', '--pairs', 'unused', '--route-summary', 'unused', '--converter', 'unused',
                    '--authority', 'unused', '--out', 'unused']
            if batch is not None:
                args.extend(['--batch', batch])
            with self.subTest(batch=batch), mock.patch.object(sys, 'argv', args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    m.main()
                self.assertEqual(error.exception.code, 2)

    def test_cli_records_requested_batch_and_preserves_invented_pair_bytes(self):
        with tempfile.TemporaryDirectory(prefix='citation-preflight-') as name:
            root = Path(name)
            pairs = root / 'pairs'
            pairs.mkdir()
            pair = {'id': 'invented', 'doi': '10.1234/invented', 'title': 'Invented title',
                    'authors': 'D.Pal', 'year': '2014', 'journal': 'Invented journal', 'pairs': []}
            pair_path = pairs / 'invented.pairs.json'
            pair_path.write_text(json.dumps(pair), encoding='utf-8')
            original = pair_path.read_bytes()
            summary = root / 'summary.json'
            summary.write_text(json.dumps({'papers': [{'doi': pair['doi'], 'records': []}]}), encoding='utf-8')
            authority = root / 'authority.json'
            authority.write_text(json.dumps({'records': [{'doi': pair['doi'], 'citation': {
                'title': [pair['title']], 'authors': ['Debasish Pal'], 'published': {'date-parts': [[2014]]}}}]}), encoding='utf-8')
            converter = root / 'converter.py'
            converter.write_text('class Builder:\n    def __init__(self, value):\n        self.source_id="invented-source"\n', encoding='utf-8')
            out = root / 'preflight.json'
            args = ['preflight', '--batch', 'batch731', '--pairs', str(pairs), '--route-summary', str(summary),
                    '--converter', str(converter), '--authority', str(authority), '--out', str(out)]
            with mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            result = json.loads(out.read_bytes())
            self.assertEqual(result['batch'], 'batch731')
            self.assertEqual(result['completed_pair_files'], 1)
            self.assertEqual(result['metadata_flags'], 0)
            self.assertEqual(result['items'][0]['pair_sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(pair_path.read_bytes(), original)
            with mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'Preserve previous preflight'):
                    m.main()


if __name__ == '__main__':
    unittest.main()
