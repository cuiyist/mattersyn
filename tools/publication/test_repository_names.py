"""Offline rename/identity compatibility tests; no credentials, Git or network."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repository_names as names
import release_batch as rb
import ci_site_publish as publisher
import prepare_allowlist
import github_release_control as control
import source_link_artifacts as links

ROOT = Path(__file__).resolve().parents[2]


class RepositoryNamesTests(unittest.TestCase):
    def test_only_exact_known_new_names_map_to_unchanged_policy_labels(self):
        for old, new in [('mattersyn', 'nanoxtalsyn'), ('mattersyn-site', 'nanoxtalsyn-site'),
                         ('mattersyn2', 'nanoxtalsyn2')]:
            for value in (old, 'cuiyist/'+old, new, 'cuiyist/'+new):
                self.assertEqual(names.policy_repo_label(value), old)
                self.assertEqual(names.canonical_repository(value), 'cuiyist/'+new)
        for value in ('other/nanoxtalsyn', 'cuiyist/nanoxtalsyn-other', 'nanoxtalsyn/',
                      ' nanoxtalsyn', 'NanoXtalSyn', 'https://github.com/cuiyist/nanoxtalsyn', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                names.policy_repo_label(value)

    def test_source_and_site_numeric_identity_pins_are_not_renamed_or_relaxed(self):
        self.assertEqual(control.IDS, {'mattersyn': 1377877572, 'mattersyn-site': 1377878442})
        self.assertEqual(names.SOURCE_REPO, 'cuiyist/nanoxtalsyn')
        self.assertEqual(names.SITE_REPO, 'cuiyist/nanoxtalsyn-site')
        self.assertEqual(names.SITE_URL, 'https://cuiyist.github.io/nanoxtalsyn-site/')

    def test_Built_from_old_and_new_footers_bind_the_same_exact_commit(self):
        sha = 'a'*40
        for repo in ('mattersyn', 'nanoxtalsyn'):
            self.assertEqual(names.built_source_commit('Publish site\n\nBuilt from cuiyist/'+repo+' '+sha+'.'), sha)
            self.assertEqual(names.built_source_commit('Built from cuiyist/'+repo+' '+sha+' by the site publish workflow.'), sha)
        self.assertEqual(names.built_source_commit('Built from cuiyist/mattersyn '+sha+'.\nBuilt from cuiyist/nanoxtalsyn '+sha+'.'), sha)
        for message in ('Built from other/nanoxtalsyn '+sha, 'Built from cuiyist/nanoxtalsyn-site '+sha,
                        'Built from cuiyist/nanoxtalsyn '+sha[:-1], 'Built from cuiyist/nanoxtalsyn '+sha+'a'):
            self.assertEqual(names.built_source_commit(message), '')
        with self.assertRaises(ValueError):
            names.built_source_commit('Built from cuiyist/mattersyn '+sha+'.\nBuilt from cuiyist/nanoxtalsyn '+'b'*40+'.')

    def test_renamed_workflow_lookups_and_public_defaults_are_consistent(self):
        self.assertEqual(rb.CI_WORKFLOW, names.CI_WORKFLOW_NAME)
        self.assertEqual(publisher.PAGES_WORKFLOW, names.PAGES_WORKFLOW_NAME)
        validate = (ROOT/'.github/workflows/validate-project.yml').read_text(encoding='utf-8')
        publish = (ROOT/'.github/workflows/site-publish.yml').read_text(encoding='utf-8')
        self.assertTrue(validate.startswith('name: '+names.CI_WORKFLOW_NAME+'\n'))
        self.assertTrue(publish.startswith('name: '+names.SITE_PUBLISH_WORKFLOW_NAME+'\n'))
        self.assertIn("workflows: ['"+names.CI_WORKFLOW_NAME+"']", publish)
        self.assertIn('CI_WORKFLOW: '+names.CI_WORKFLOW_NAME, publish)
        self.assertIn('SITE_REPO: '+names.SITE_REPO, publish)
        self.assertIn('SITE_URL: '+names.SITE_URL, publish)
        self.assertNotIn('--base https://cuiyist.github.io/mattersyn-site/', validate)
        self.assertIn('http://127.0.0.1:8172/nanoxtalsyn-site/', publish)
        self.assertIn('$WORK/serve/nanoxtalsyn-site', publish)

    def test_internal_schema_artifact_job_concurrency_and_folder_names_stay(self):
        publish = (ROOT/'.github/workflows/site-publish.yml').read_text(encoding='utf-8')
        validate = (ROOT/'.github/workflows/validate-project.yml').read_text(encoding='utf-8')
        self.assertIn('mattersyn-site-dry-run-', publish)
        self.assertIn("'mattersyn-site-publish'", publish)
        self.assertIn('mattersyn-site-${{ env.MODE }}-${{ env.SOURCE_COMMIT }}', publish)
        self.assertIn('mattersyn-validation-', validate)
        self.assertIn('  validate:', validate)
        self.assertIn('  compare-artifacts:', validate)
        self.assertIn('  site:', publish)
        self.assertIn('tools/mattersyn-release', (ROOT/'tools/publication/ci_site_publish.py').read_text(encoding='utf-8'))

    def test_allowlist_unknown_repository_fails_before_reading_any_tree(self):
        args = ['prepare', '--root', 'unused', '--guard', 'unused', '--policy', 'unused',
                '--registry', 'unused', '--repo', 'other/nanoxtalsyn', '--source-commit', 'a'*40,
                '--release-id', 'synthetic', '--reviewer', 'test', '--out', 'unused']
        with patch.object(sys, 'argv', args), self.assertRaisesRegex(ValueError, 'Unknown repository identity'):
            prepare_allowlist.main()

    def test_authored_graphic_and_source_library_default_use_new_visible_brand(self):
        raw = links.authored_graphic('og.png')
        self.assertIn(b'>NanoXtalSyn</text>', raw)
        self.assertIn(b'>N</text>', raw)
        self.assertIn(b'Nanocrystal synthesis atlas', raw)
        self.assertNotIn(b'MatterSyn', raw)
        self.assertEqual(links.url_for({}), names.SITE_URL+'library.html')


class HistoricalPagesCompatibilityTests(unittest.TestCase):
    def test_historical_source_keeps_old_Site_workflow_byte_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, site = Path(tmp)/'source', Path(tmp)/'site'
            (src/'.github/workflows').mkdir(parents=True)
            (site/'.github/workflows').mkdir(parents=True)
            (src/'.github/workflows/site-publish.yml').write_text('name: MatterSyn site publish\n', encoding='utf-8')
            raw = b'name: MatterSyn validated Pages release\r\njobs:\r\n  publish:\r\n    name: retained-check\r\n'
            target = site/'.github/workflows/pages.yml'; target.write_bytes(raw)
            self.assertFalse(rb.stage_pages_workflow_name(src, site))
            self.assertEqual(target.read_bytes(), raw)

    def test_new_Source_changes_only_the_authorized_Pages_display_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, site = Path(tmp)/'source', Path(tmp)/'site'
            (src/'.github/workflows').mkdir(parents=True)
            (site/'.github/workflows').mkdir(parents=True)
            (src/'.github/workflows/site-publish.yml').write_text('name: '+names.SITE_PUBLISH_WORKFLOW_NAME+'\n', encoding='utf-8')
            raw = b'name: MatterSyn validated Pages release\r\njobs:\r\n  publish:\r\n    name: retained-check\r\n'
            target = site/'.github/workflows/pages.yml'; target.write_bytes(raw)
            self.assertTrue(rb.stage_pages_workflow_name(src, site))
            expected = raw.replace(b'name: MatterSyn validated Pages release', b'name: NanoXtalSyn validated Pages release', 1)
            self.assertEqual(target.read_bytes(), expected)
            self.assertFalse(rb.stage_pages_workflow_name(src, site))
            self.assertEqual(target.read_bytes(), expected)

    def test_unknown_Source_or_Site_workflow_identity_fails_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, site = Path(tmp)/'source', Path(tmp)/'site'
            (src/'.github/workflows').mkdir(parents=True)
            (site/'.github/workflows').mkdir(parents=True)
            source = src/'.github/workflows/site-publish.yml'; target = site/'.github/workflows/pages.yml'
            source.write_text('name: unrelated\n', encoding='utf-8'); target.write_bytes(b'name: unchanged\n')
            with self.assertRaises(SystemExit): rb.stage_pages_workflow_name(src, site)
            self.assertEqual(target.read_bytes(), b'name: unchanged\n')
            source.write_text('name: '+names.SITE_PUBLISH_WORKFLOW_NAME+'\n', encoding='utf-8')
            with self.assertRaises(SystemExit): rb.stage_pages_workflow_name(src, site)
            self.assertEqual(target.read_bytes(), b'name: unchanged\n')


if __name__ == '__main__':
    unittest.main()
