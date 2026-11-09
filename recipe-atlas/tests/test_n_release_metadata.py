"""Synthetic generated-branding checks; no real records, papers or site build."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import generate_release_metadata as metadata


class ReleaseMetadataBrandingTests(unittest.TestCase):
    def test_source_review_link_uses_current_public_namespace(self):
        source = {'id': 'synthetic', 'authors': 'Test author', 'year': 2000,
                  'title': 'Synthetic citation', 'doi': '10.0000/synthetic'}
        text = metadata.citation(source, {'paper_id': 'synthetic'})
        self.assertIn('https://cuiyist.github.io/nanoxtalsyn-site/paper-review.html?id=synthetic', text)
        self.assertIn('https://doi.org/10.0000/synthetic', text)

    def test_reference_markers_and_existing_dated_history_remain_unchanged(self):
        history = '# NanoXtalSyn\n\n2026-11-08: MatterSyn history retained verbatim.\n'
        result = metadata.readme_with_references(history, 'Unused current introduction', 'Synthetic references')
        self.assertTrue(result.startswith(history))
        self.assertIn('<!-- mattersyn-generated-references:start -->', result)
        self.assertIn('<!-- mattersyn-generated-references:end -->', result)

    def test_generated_introduction_references_and_redirect_title_use_new_brand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'project/recipe-atlas'
            for rel in ['data/records', 'data/paper-reviews', 'dist/data']:
                (root/rel).mkdir(parents=True)
            source = {'id': 'synthetic', 'authors': 'Test author', 'year': 2000,
                      'title': 'Synthetic citation', 'doi': '10.0000/synthetic'}
            record = {'record_id': 'synthetic', 'sources': [source],
                      'lineage': {'source_group': 'synthetic'}}
            (root/'data/records/synthetic.json').write_text(json.dumps(record), encoding='utf-8')
            (root/'dist/data/dataset-manifest.json').write_text(json.dumps({
                'dataset_version': 'test', 'records': [{'record_id': 'synthetic'}]}), encoding='utf-8')
            snapshot = {'record_count': 1, 'release_id': 'test', 'updated_at': '2000-01-01T00:00:00Z',
                        'source_commit': 'a'*40}
            result = metadata.generate(root, snapshot)
            for folder in (root.parent, root/'dist'):
                readme = (folder/'README.md').read_text(encoding='utf-8')
                self.assertTrue(readme.startswith('# NanoXtalSyn'))
                self.assertIn('Nanocrystal synthesis atlas.', readme)
                self.assertIn('https://cuiyist.github.io/nanoxtalsyn-site/', readme)
                self.assertNotIn('\\n', readme)
                self.assertTrue((folder/'REFERENCES.md').read_text(encoding='utf-8').startswith('# NanoXtalSyn references'))
            self.assertIn('<title>NanoXtalSyn synthesis dataset</title>', (root/'dist/progress.html').read_text(encoding='utf-8'))
            self.assertEqual(result['schema'], 'mattersyn-generated-release-metadata/1')
            self.assertEqual(result['canonical_records'], 1)
            self.assertEqual((root/'data/records/synthetic.json').read_text(encoding='utf-8'), json.dumps(record))


if __name__ == '__main__':
    unittest.main()
