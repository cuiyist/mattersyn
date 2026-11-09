"""Small offline fixtures only; no canonical corpus, browser, or network."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error

MODULE = Path(__file__).resolve().parents[2] / 'ci/brand_name_scan.py'
spec = importlib.util.spec_from_file_location('brand_name_scan', MODULE)
n = importlib.util.module_from_spec(spec); spec.loader.exec_module(n)
SOURCE = 'a' * 40
SITE = 'b' * 40


def identifiers():
    return {'schema': 'NanoXtalSyn-N4-exact-identifier-pins/1', 'as_of': n.AS_OF,
            'schema_tokens': ['mattersyn-silver/0.1/reader-catalog'],
            'env_tokens': ['MATTERSYN_SOURCE_ROOT'], 'global_tokens': ['__mattersynChemicalRegistry'],
            'technical_folder_tokens': ['tools/mattersyn-release', 'mattersyn-paper-to-site'],
            'schema_URIs': ['https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/data/record.schema.json'],
            'artifact_prefixes': ['mattersyn-protocol-scenes-'],
            'repo_labels': ['mattersyn', 'mattersyn-site', 'mattersyn2'], 'dated_history_sections': []}


def row(path, raw):
    return {'path': path, 'bytes': len(raw), 'sha256': n.digest(raw), 'decision': 'allow', 'review_status': 'approved'}


class BrandScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ids = identifiers()
        self.blueprint = {'schema': 'mattersyn-build-input-blueprint/1', 'input_files': []}

    def put(self, path, raw):
        file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(raw)
        return row(path, raw)

    def manifest(self, rows, phase='candidate'):
        return {'schema': 'mattersyn-unapproved-build-candidate/1',
                'schema_version': 'mattersyn-public-release-allowlist/1', 'repo': 'mattersyn-site',
                'source_commit': SOURCE, 'release_id': 'site-' + SOURCE[:12], 'files': rows}

    def classify(self, text, path='index.html', records=None):
        return n.classify(path, text.encode(), records or {}, self.ids, n.technical_tokens(self.ids, set()))

    def test_exact_identifiers_policy_labels_and_visible_prose_are_separate(self):
        text = '__mattersynChemicalRegistry MATTERSYN_SOURCE_ROOT "mattersyn-silver/0.1/reader-catalog" --repo mattersyn-site <title>MatterSyn</title> MatterSyn-authored'
        counts, _ = self.classify(text)
        self.assertEqual(counts, {'N4_identifiers': 4, 'anything_else': 2})
        self.assertEqual(self.classify('mattersyn-silver/0.1/reader-catalog/unknown')[0], {'anything_else': 1})

    def test_exact_internal_html_markers_preserved_but_visible_brand_still_fails(self):
        self.ids['internal_marker_tokens'] = ['mattersyn-generated-references:start', 'mattersyn-generated-references:end']
        text = '<!-- mattersyn-generated-references:start -->\n<!-- mattersyn-generated-references:end -->\n<h1>MatterSyn</h1>'
        self.assertEqual(self.classify(text)[0], {'N4_identifiers': 2, 'anything_else': 1})
        self.assertEqual(self.classify('mattersyn-generated-references:start:unknown')[0], {'anything_else': 1})

    def test_old_current_urls_fail_even_when_filename_matches(self):
        text = 'https://cuiyist.github.io/mattersyn-site/index.html https://github.com/cuiyist/mattersyn2'
        counts, evidence = self.classify(text)
        self.assertEqual(counts, {'anything_else': 2})
        self.assertTrue(all(x['proof'] == 'current_old_repository_or_Pages_URL' for x in evidence))

    def test_allowed_schema_uri_but_descriptive_title_is_not_identifier(self):
        text = self.ids['schema_URIs'][0] + ' MatterSyn source-linked synthesis record'
        self.assertEqual(self.classify(text)[0], {'N4_identifiers': 1, 'anything_else': 1})

    def test_record_requires_exact_source_bytes_and_hash(self):
        raw = b'{"record_id":"r","review_scope":"MatterSyn original"}\n'
        records = {'data/records/r.json': row('ignored', raw)}
        self.assertEqual(n.classify('data/records/r.json', raw, records, self.ids, ())[0], {'record_bytes': 1})
        self.assertEqual(n.classify('data/records/r.json', raw + b' ', records, self.ids, ())[0], {'anything_else': 1})

    def test_dated_history_requires_unchanged_exact_section_and_pre_owner_date(self):
        text = '# Log\n## 2026-11-08\nMatterSyn historical title\n## 2026-11-09\nMatterSyn current\n'
        section = '## 2026-11-08\nMatterSyn historical title\n'
        self.ids['dated_history_sections'] = [{'path': 'README.md', 'date': '2026-11-08', 'section_LF_sha256': n.digest(section.encode())}]
        self.assertEqual(self.classify(text, 'README.md')[0], {'dated_history': 1, 'anything_else': 1})
        self.assertEqual(self.classify(text.replace('historical title', 'modified'), 'README.md')[0], {'anything_else': 2})

    def test_record_jsonl_and_training_field_proof(self):
        original = {'record_id': 'r', 'materials': [{'note': 'MatterSyn old record field'}]}
        raw = n.encoded(original); record = self.put('data/records/r.json', raw)
        self.blueprint['input_files'] = [{**record, 'path': 'recipe-atlas/data/records/r.json'}]
        load = n.record_loader(self.root, n.record_pins(self.blueprint), {record['path']: record})
        aggregate = json.dumps(original).encode()
        counts, proof = n.classify('data/records.jsonl', aggregate, {}, self.ids, (), load)
        self.assertEqual(counts, {'record_bytes': 1}); self.assertEqual(proof[0]['proof']['basis'], 'exact_record_object_in_JSONL')
        export = {'record_id': 'r', 'task': 'partial_protocol', 'record_sha256': n.semantic_digest(original), 'input': {}, 'output': {'materials': original['materials']}, 'provenance': []}
        counts, proof = n.classify('data/exports/partial_protocol.jsonl', json.dumps(export).encode(), {}, self.ids, (), load)
        self.assertEqual(counts, {'record_bytes': 1}); self.assertEqual(proof[0]['proof']['Source_field'], '/materials/0/note')
        export['output']['materials'] = [{'note': 'MatterSyn newly invented field'}]
        self.assertEqual(n.classify('data/exports/partial_protocol.jsonl', json.dumps(export).encode(), {}, self.ids, (), load)[0], {'anything_else': 1})
        export['record_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'digest shape'): n.classify('data/exports/partial_protocol.jsonl', json.dumps(export).encode(), {}, self.ids, (), load)

    def test_export_never_uses_record_id_without_exact_source_and_site_pins(self):
        raw = n.encoded({'record_id': 'r', 'note': 'MatterSyn'})
        record = self.put('data/records/r.json', raw)
        records = {'data/records/r.json': {**record, 'sha256': '0' * 64}}
        load = n.record_loader(self.root, records, {record['path']: record})
        with self.assertRaisesRegex(ValueError, 'Source/Site pin'): n.classify('data/records.jsonl', json.dumps(json.loads(raw)).encode(), {}, self.ids, (), load)
        self.assertEqual(n.classify('data/arbitrary.json', raw, {}, self.ids, (), load)[0], {'anything_else': 1})

    def test_every_served_text_type_is_selected_but_unlisted_controls_are_not(self):
        rows = [self.put('data/x.' + ext, b'neutral') for ext in ('jsonl', 'csv', 'xyz', 'sdf', 'cif')]
        rows += [self.put('index.html', b'NanoXtalSyn'), self.put('logo.png', b'\x89PNG\0')]
        self.put('.release-control/private.json', b'MatterSyn unlisted')
        result = n.scan(self.root, self.manifest(rows), self.blueprint, self.ids, 'candidate', SOURCE)
        self.assertTrue(result['passed']); self.assertEqual(result['selected_text_file_count'], 6)
        self.assertEqual(result['selected_files_by_kind'], {'data': 5, 'page': 1})
        self.assertEqual(result['excluded_binary_or_nontext_files_by_suffix'], {'.png': 1})
        rows.append(row('.release-control/private.json', b'MatterSyn unlisted'))
        self.assertFalse(n.scan(self.root, self.manifest(rows), self.blueprint, self.ids, 'candidate', SOURCE)['passed'])

    def test_candidate_source_duplicate_and_hash_tamper_fail(self):
        rows = [self.put('index.html', b'NanoXtalSyn')]
        wrong = self.manifest(rows); wrong['source_commit'] = SITE
        with self.assertRaisesRegex(ValueError, 'Manifest Source'): n.scan(self.root, wrong, self.blueprint, self.ids, 'candidate', SOURCE)
        with self.assertRaisesRegex(ValueError, 'Duplicate'): n.inventory(self.root, self.manifest(rows * 2), 'candidate')
        (self.root / 'index.html').write_bytes(b'changed')
        result = n.scan(self.root, self.manifest(rows), self.blueprint, self.ids, 'candidate', SOURCE)
        self.assertEqual(result['failure_count'], 1); self.assertFalse(result['passed'])

    def test_published_fetches_each_selected_url_anonymously_and_keeps_recovery(self):
        bodies = {'index.html': b'NanoXtalSyn', 'data/a.csv': b'neutral'}
        rows = [self.put(path, raw) for path, raw in bodies.items()]; calls = []; sleeps = []
        def fetch(url, expected):
            calls.append(url)
            self.assertTrue(url.startswith(n.NEW_BASE)); self.assertIn('?n_source=' + SOURCE, url)
            if len(calls) == 1: raise urllib.error.HTTPError(url, 503, 'unavailable', {}, None)
            path = url.split(n.NEW_BASE, 1)[1].split('?', 1)[0]
            return bodies[path]
        result = n.scan(self.root, self.manifest(rows), self.blueprint, self.ids, 'published', SOURCE, fetch, sleeps.append, workers=1)
        self.assertTrue(result['passed']); self.assertTrue(result['all_selected_HTTP_verified'])
        self.assertEqual(result['anonymous_HTTP_verified_files'], 2); self.assertEqual(len(calls), 3)
        self.assertEqual(result['transport_attempt_records'][0]['attempt_failures'][0]['http_status'], 503)

    def test_404_and_successful_wrong_hash_never_retry(self):
        item = row('x.json', b'exact')
        for mode in ('404', 'hash'):
            calls = []
            def fetch(url, expected):
                calls.append(url)
                if mode == '404': raise urllib.error.HTTPError(url, 404, 'not found', {}, None)
                return b'wrong'
            raw, receipt = n.read_live(item, SOURCE, fetch, lambda _: self.fail('No sleep/retry'))
            self.assertIsNone(raw); self.assertEqual(len(calls), 1); self.assertFalse(receipt['attempt_failures'][0]['retryable'])

    def test_transient_bound_and_failures_are_preserved(self):
        calls = []; sleeps = []
        def fetch(url, expected): calls.append(url); raise TimeoutError()
        raw, receipt = n.read_live(row('a.json', b'a'), SOURCE, fetch, sleeps.append)
        self.assertIsNone(raw); self.assertEqual(len(calls), 3); self.assertEqual(sleeps, [1, 2])
        self.assertEqual(len(receipt['attempt_failures']), 3)

    def test_published_binding_requires_actual_matching_receipts(self):
        manifest = self.manifest([])
        files = {
            'build_receipt': {'source_commit': SOURCE, 'release_id': manifest['release_id'], 'candidate_tree_sha256': 'c' * 64, 'final_tree_sha256': 'c' * 64},
            'stage_receipt': {'source_commit': SOURCE, 'release_id': manifest['release_id'], 'site_base_commit': 'd' * 40, 'preview_tree_sha256': 'e' * 64},
            'push_receipt': {'source_commit': SOURCE, 'site_base_commit': 'd' * 40, 'site_commit': SITE, 'pushed': True},
            'live_receipt': {'source_commit': SOURCE, 'passed': True, 'anonymous': True, 'site_url': n.NEW_BASE, 'pages_runs': [[123, 'success']]}}
        manifest_path = self.root / 'manifest.json'; manifest_path.write_bytes(n.encoded(manifest))
        files['build_receipt']['allowlist_sha256'] = n.pin(manifest_path)['sha256']
        args = argparse.Namespace(source_commit=SOURCE, site_commit=SITE, manifest=manifest_path)
        for key, value in files.items():
            path = self.root / (key + '.json'); path.write_bytes(n.encoded(value)); setattr(args, key, path)
        self.assertEqual(len(n.published_binding(args, manifest)), 4)
        files['live_receipt']['mismatched_files'] = ['x']; args.live_receipt.write_bytes(n.encoded(files['live_receipt']))
        with self.assertRaisesRegex(ValueError, 'anonymous'): n.published_binding(args, manifest)

    def test_default_inert_and_full_scan_only_in_ci(self):
        result = subprocess.run([sys.executable, '-B', str(MODULE)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0); self.assertEqual(result.stdout.strip(), 'DEFAULT_INERT_NO_SCAN_NETWORK_OR_FILES')
        import os
        environment = {**os.environ, 'GITHUB_ACTIONS': 'false'}
        result = subprocess.run([sys.executable, '-B', str(MODULE), '--scan'], env=environment, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0); self.assertIn('GitHub CI/publisher only', result.stderr)



    def test_mixed_export_record_identifier_url_and_prose_priority(self):
        original = {'record_id': 'r', 'note': 'MatterSyn exact field', 'source_schema': 'mattersyn-reader-chemicals/1'}
        canonical = n.encoded(original); record = self.put('data/records/r.json', canonical)
        self.blueprint['input_files'] = [{**record, 'path': 'recipe-atlas/data/records/r.json'}]
        load = n.record_loader(self.root, n.record_pins(self.blueprint), {record['path']: record})
        export = {'record_id': 'r', 'task': 'partial_protocol', 'record_sha256': n.semantic_digest(original),
                  'input': {}, 'output': {'note': original['note'], 'schema': original['source_schema'],
                      'global': '__mattersynChemicalRegistry', 'caption': 'MatterSyn current',
                      'link': 'https://cuiyist.github.io/mattersyn-site/'}, 'provenance': []}
        text = '{"note":"neutral \u03bc"}\r\n' + json.dumps(export, ensure_ascii=False) + '\n'
        counts, evidence = n.classify('data/exports/partial_protocol.jsonl', text.encode(), {}, self.ids,
                                     n.technical_tokens(self.ids, set()), load)
        self.assertEqual(counts, {'record_bytes': 2, 'N4_identifiers': 1, 'anything_else': 2})
        self.assertEqual([x['category'] for x in evidence], ['record_bytes', 'record_bytes', 'N4_identifiers', 'anything_else', 'anything_else'])
        self.assertEqual(evidence[0]['proof']['Source_field'], '/note')
        self.assertEqual(evidence[-1]['proof'], 'current_old_repository_or_Pages_URL')
        self.assertTrue(all(x['line'] == 2 for x in evidence))

    def test_all_record_export_proofs_skip_body_tokens_but_keep_validation(self):
        original = {'record_id': 'r', 'note': 'MatterSyn', 'url': 'https://cuiyist.github.io/mattersyn-site/',
                    'schema': 'mattersyn-reader-chemicals/1'}
        raw = json.dumps(original).encode(); source = {'bytes': len(raw), 'sha256': n.digest(raw)}
        load = lambda rid: (original, source)
        native = n.token_spans; bodies = []
        def observed(relative, text, identifiers, exact):
            bodies.append(text); return native(relative, text, identifiers, exact)
        with unittest.mock.patch.object(n, 'token_spans', side_effect=observed):
            counts, evidence = n.classify('data/records.jsonl', raw, {}, self.ids, n.technical_tokens(self.ids, set()), load)
        self.assertEqual(counts, {'record_bytes': 3}); self.assertTrue(all(x['category'] == 'record_bytes' for x in evidence))
        self.assertEqual(bodies, [''])
        with self.assertRaisesRegex(ValueError, 'No bare-brand N4 exemption'):
            n.classify('data/records.jsonl', raw, {}, self.ids, ('mattersyn',), load)

    def test_proof_priorities_and_exact_CRLF_unicode_positions(self):
        raw = '{"record_id":"r",\r\n "note":"\u03bc MatterSyn",\r\n"schema":"mattersyn-reader-chemicals/1"}\r\n'.encode()
        records = {'data/records/r.json': {'bytes': len(raw), 'sha256': n.digest(raw)}}
        counts, evidence = n.classify('data/records/r.json', raw, records, self.ids, ())
        self.assertEqual(counts, {'record_bytes': 2})
        self.assertEqual([(x['line'], x['column']) for x in evidence], [(2, len(' "note":"\u03bc ') + 1), (3, len('"schema":"') + 1)])
        section = '## 2026-11-08\r\n\u03bc MatterSyn https://cuiyist.github.io/mattersyn-site/\r\n'
        self.ids['dated_history_sections'] = [{'path': 'README.md', 'date': '2026-11-08',
            'section_LF_sha256': n.digest(section.replace('\r\n', '\n').encode())}]
        counts, evidence = self.classify(section, 'README.md')
        self.assertEqual(counts, {'dated_history': 2})
        self.assertEqual(evidence[0]['line'], 2); self.assertEqual(evidence[0]['column'], 3)

    def test_invalid_export_digest_still_fails_before_token_shortcut(self):
        original = {'record_id': 'r', 'note': 'MatterSyn'}
        export = {'record_id': 'r', 'task': 'partial_protocol', 'record_sha256': '0' * 64,
                  'input': {}, 'output': {'note': 'MatterSyn'}, 'provenance': []}
        load = lambda rid: (original, {'bytes': 1, 'sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'digest shape differs'):
            n.classify('data/exports/partial_protocol.jsonl', json.dumps(export).encode(), {}, self.ids, ('mattersyn',), load)


if __name__ == '__main__': unittest.main()
