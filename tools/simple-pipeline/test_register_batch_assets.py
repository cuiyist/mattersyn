import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import register_batch_assets as helper
# Installed under tools/simple-pipeline, or in the private engineering fixture.
GUARD = next((p for p in (BASE / 'mattersyn-release/public_release_guard.py',
                         BASE / 'tools/mattersyn-release/public_release_guard.py') if p.is_file()), None)
if GUARD is None:
    raise RuntimeError('Run these integration tests beside the project release guard.')
spec = importlib.util.spec_from_file_location('extracted_guard', GUARD)
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)


class RegistrationTest(unittest.TestCase):
    def put(self, rel, data):
        target = self.repo / rel; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else (json.dumps(data, indent=2) + '\n').encode())
        return target

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=BASE); self.repo = Path(self.tmp.name)
        self.rid, self.sid, self.doi = 'synthetic-core', 'synthetic2026', '10.1234/synthetic'
        self.old = {'asset_hash': 'f' * 64, 'classification': 'generated_artwork', 'source_bindings': [],
                    'delivery_paths': [{'repo': 'mattersyn-site', 'path': 'assets/already-live.svg', 'bytes': 1}],
                    'rights': {'status': 'not_source_derived', 'attribution': 'Existing authored asset'}}
        registry = {'schema_version': guard.RIGHTS_SCHEMA, 'assets': [self.old], 'snapshots': [], 'scope': 'Existing unchanged metadata'}
        self.registry_path = self.put('publication/asset-rights-registry.json', registry)
        self.old_rule = {'rule_id': 'existing-readme', 'repo': 'mattersyn', 'path_glob': 'README.md', 'content_class': 'authored_docs',
                         'decision': 'allow', 'review_status': 'approved', 'reviewer': 'Existing reviewer'}
        self.policy = {'schema_version': guard.POLICY_SCHEMA, 'approval_status': 'approved', 'approved_by': 'Existing policy owner',
                       'asset_rights_registry_sha256': helper.digest(self.registry_path.read_bytes()),
                       'allowed_content_classes': ['site_asset', 'authored_docs'], 'path_rules': [self.old_rule],
                       'blob_approvals': [], 'exact_blob_approval_classes': []}
        self.policy_path = self.put('publication/public-release-policy.json', self.policy)
        record = {'record_id': self.rid, 'lineage': {'source_group': self.sid}, 'quality': {'review_status': 'source_extracted'},
                  'sources': [{'id': self.sid, 'doi': self.doi}], 'operations': [{'id': 'heat'}]}
        self.record_path = self.put(f'recipe-atlas/data/records/{self.rid}.json', record)
        self.fig_path = f'assets/paper-reviews/{self.sid}/figure-1.png'
        self.fig_raw = b'\x89PNG\r\n\x1a\nsynthetic fixture crop'
        self.put('recipe-atlas/static/' + self.fig_path, self.fig_raw)
        diagram = f'assets/protocol/{self.rid}-heat.svg'; diagram_raw = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Conceptual action</title></svg>'
        self.put('recipe-atlas/static/' + diagram, diagram_raw)
        card_raw = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Chemical name</title></svg>'
        self.put('recipe-atlas/static/assets/chemical-registry/svg/name-card-synthetic.svg', card_raw)
        self.put('recipe-atlas/static/assets/chemical-registry/registry.json', {'entries': [{'id': 'name-card-synthetic', 'depictionKind': 'formula',
                  'model3dPath': None, 'svgPath': 'svg/name-card-synthetic.svg', 'assetHashes': {'svgPath': helper.digest(card_raw)}}]})
        self.put('recipe-atlas/static/assets/chemical-registry/bindings.json', {'recordBindings': {self.rid: {'chemical1': 'name-card-synthetic'}}})
        self.side = {'records': {self.rid: {'source_id': self.sid,
                    'figures': [{'public_asset': self.fig_path, 'public_asset_sha256': helper.digest(self.fig_raw),
                                 'source_locator': {'document_role': 'main', 'page': 2, 'figure': 'Figure 1'},
                                 'caption': 'PRIVATE CAPTION MUST NOT TRANSFER',
                                 'provenance': {'render_tool': 'PyMuPDF crop', 'asset_sha256': helper.digest(self.fig_raw)}}],
                    'protocol_art': {'record_id': self.rid, 'bindings': [{'operation_id': 'heat', 'asset_path': diagram,
                                     'asset_sha256': helper.digest(diagram_raw), 'source_locator': 'Main PDF p.2'}]}}}}
        self.side_path = self.put('recipe-atlas/data/reader-presentation-reviewed.json', self.side)

    def tearDown(self): self.tmp.cleanup()

    def run_registration(self, apply=True):
        return helper.register(self.repo, [self.rid], '2026-10-10T22:00:00Z', 'owner-simple-lane-20261010-evening', 'Synthetic delivery reviewer', guard, apply)

    def test_exact_entries_and_rules_keep_existing_entries_unchanged(self):
        result = self.run_registration()
        self.assertEqual(result['new_assets'], 3)
        self.assertEqual(result['new_exact_path_rules'], 6)
        registry, policy = helper.read(self.registry_path), helper.read(self.policy_path)
        self.assertEqual(registry['assets'][0], self.old)
        self.assertEqual(policy['path_rules'][0], self.old_rule)
        self.assertEqual(policy['asset_rights_registry_sha256'], helper.digest(self.registry_path.read_bytes()))
        for key, value in self.policy.items():
            if key not in ('path_rules', 'asset_rights_registry_sha256'): self.assertEqual(policy[key], value)
        config = guard.load_config(self.policy_path, self.registry_path)
        crop = next(a for a in registry['assets'] if a['classification'] == 'source_figure')
        self.assertEqual(crop['rights']['permission_status'], 'permission_not_established')
        self.assertFalse(crop['rights']['copyright_permission_verified'])
        self.assertEqual(crop['record_status'], 'source_extracted')
        self.assertEqual(crop['source_bindings'][0]['locators'], {'document_role': 'main', 'page': 2, 'id': 'figure-1'})
        self.assertNotIn('PRIVATE CAPTION', json.dumps(registry))
        for delivery in crop['delivery_paths']:
            projected = guard.history_project(delivery['repo'], delivery['path'], self.fig_raw, config)
            self.assertEqual(projected['action'], 'allow')
            self.assertEqual(projected['content'], self.fig_raw)

    def test_dry_run_does_not_change_files_and_repeat_is_idempotent(self):
        before = self.registry_path.read_bytes(), self.policy_path.read_bytes()
        self.run_registration(False)
        self.assertEqual(before, (self.registry_path.read_bytes(), self.policy_path.read_bytes()))
        self.run_registration()
        after = self.registry_path.read_bytes(), self.policy_path.read_bytes()
        result = self.run_registration()
        self.assertEqual(result['new_assets'], 0)
        self.assertEqual(result['new_exact_path_rules'], 0)
        self.assertEqual(after, (self.registry_path.read_bytes(), self.policy_path.read_bytes()))

    def test_tampered_crop_and_audited_records_cannot_be_registered(self):
        before = self.registry_path.read_bytes(), self.policy_path.read_bytes()
        self.side['records'][self.rid]['figures'][0]['public_asset_sha256'] = 'a' * 64
        self.side['records'][self.rid]['figures'][0]['provenance']['asset_sha256'] = 'a' * 64
        self.put('recipe-atlas/data/reader-presentation-reviewed.json', self.side)
        with self.assertRaisesRegex(ValueError, 'checksum differs'): self.run_registration()
        record = helper.read(self.record_path); record['quality']['review_status'] = 'source_reviewed'; self.put(str(self.record_path.relative_to(self.repo)), record)
        with self.assertRaisesRegex(ValueError, 'not an extracted record'): self.run_registration()
        self.assertEqual(before, (self.registry_path.read_bytes(), self.policy_path.read_bytes()))

    def test_new_scope_remains_narrow_and_permission_is_never_claimed(self):
        self.run_registration()
        asset = next(a for a in helper.read(self.registry_path)['assets'] if a['classification'] == 'source_figure')
        for change in ('wrong-status', 'wrong-page', 'wrong-paper', 'permission', 'whole-page'):
            bad = copy.deepcopy(asset); path = self.fig_path
            if change == 'wrong-status': bad['record_status'] = 'source_reviewed'
            elif change == 'wrong-page': bad['source_bindings'][0]['locators']['page'] = True
            elif change == 'wrong-paper': bad['rights']['user_direction']['paper_id'] = 'other'
            elif change == 'permission': bad['rights']['copyright_permission_verified'] = True
            elif change == 'whole-page': path = path.replace('figure-1', 'main-page-2')
            self.assertIsNotNone(guard.user_directed_display_error(bad, 'mattersyn-site', path))

    def test_numbered_chart_and_optional_crop_pins_are_registered(self):
        chart_path = f'assets/paper-reviews/{self.sid}/chart-2.png'
        self.put('recipe-atlas/static/' + chart_path, self.fig_raw)
        figure = copy.deepcopy(self.side['records'][self.rid]['figures'][0])
        figure.update(public_asset=chart_path)
        figure['source_locator']['figure'] = 'Chart 2'
        figure['provenance'].update(source_pdf_sha256='b' * 64, render_dpi=180,
                                    crop_box_pdf_points=[10.25, 20.25, 400.75, 500.5],
                                    page_size_pdf_points=[612, 792], pixel_size=[975, 1200])
        self.side['records'][self.rid]['figures'].append(figure)
        self.put('recipe-atlas/data/reader-presentation-reviewed.json', self.side)
        result = self.run_registration()
        self.assertEqual(result['new_assets'], 4)
        asset = next(a for a in helper.read(self.registry_path)['assets'] if any(d['path'] == chart_path for d in a['delivery_paths']))
        self.assertEqual(asset['source_bindings'][0]['locators']['id'], 'chart-2')
        self.assertEqual(asset['source_bindings'][0]['locators']['source_sha256'], 'b' * 64)
        self.assertEqual(asset['source_bindings'][0]['crop']['render_dpi'], 180)
        self.assertIsNone(guard.user_directed_display_error(asset, 'mattersyn-site', chart_path))
        bad = copy.deepcopy(asset)
        bad['rights']['user_direction']['scope'] = 'display_source_figures_for_reviewed_papers'
        self.assertIsNotNone(guard.user_directed_display_error(bad, 'mattersyn-site', chart_path))


if __name__ == '__main__': unittest.main()
