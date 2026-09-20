from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

A = Path(__file__).resolve().parent
L = A.parent.parent
M = L.parents[4]
C = L / 'canonical-proposal/v1'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

assert not (A / 'package-freeze.json').exists(), 'Preserve the existing freeze; revisions must use a new boundary.'
expected = {
    C / 'package-manifest.json': 'd095fb8c95ada7a91831731ab86af875c9ed913ed33e5a498a338eb3e370b0e6',
    L / 'canonical-reader-independent-audit/independent-audit-v1.json': '87e1a7f27e68bace9a6b162b1f1859f18b334391ceb8849ed53960f9988559fa',
    L / 'package-freeze.json': '2eca0b5181f3b60156227095e51833af870c7a3ea7e0590c4d3e782931555ae7',
    L / 'source-independent-audit/independent-audit-v2.json': '794b3637c0d4d83952f83c5a694da41d9f6d0523cf9d6d0327388c1bcc897940',
    L / 'source-facts.json': '12f5829b49643954ccb5caad97ee0dcfc0a7ac79dd468c4bb08b0c39e9cd29b6',
    M / 'downloaded_papers/10.1021_acsami.1c18038.pdf': '4a351221c8398d31f804d2af3d9f8327931c43e6e275e481ce84d7a67522a692',
    M / 'downloaded_papers/10.1021_acsami.1c18038_si_1.pdf': 'a98d80fda37e0d7fd148e5da33b318ba382dd179117613c80f04b01c52659bf4'
}
for path, value in expected.items():
    assert sha(path) == value, str(path)
record_manifest = read(C / 'record-manifest.json')
for entry in record_manifest['records']:
    assert sha(entry['path']) == entry['sha256'], entry['record_id']
validation = read(A / 'author-validation.json')
assert validation['checks'] == 594 and validation['operations'] == 21
assert sha(A / 'quantity-value.mjs') == sha(M / 'recipe-atlas/dist/quantity-value.mjs')

preview = read(A / 'preview-manifest.json')
for scene in preview['scenes']:
    for kind in ['svg', 'png']:
        assert sha(A / scene[kind + '_path']) == scene[kind + '_sha256']
for contact in preview['contacts']:
    assert sha(A / contact['path']) == contact['sha256']
assert len(preview['scenes']) == 21 and len(preview['contacts']) == 6
preview['visual_review_status'] = 'all_21_scenes_viewed_by_author_pending_independent_audit'
write(A / 'preview-manifest.json', preview)

visual_review = {
    'author': '/root/norberg2004_extract',
    'status': 'author_visual_inspection_complete_independent_review_pending',
    'scene_count': 21,
    'inspection_method': 'Actual view_image inspection of all six contact sheets covering all 21 native rendered scenes; film-pl.png individually viewed after the pre-freeze art-label correction.',
    'viewed_contacts': [{'path': x['path'], 'sha256': x['sha256'], 'operation_ids': x['operation_ids']} for x in preview['contacts']],
    'individually_rechecked': [{'path': 'previews/film-pl.png', 'sha256': sha(A / 'previews/film-pl.png')}],
    'targeted_original_source_views': [
        {'path': str(L / rel), 'sha256': sha(L / rel)}
        for rel in ['source-render/main-06.png', 'source-render/main-07.png', 'reader-assets/scheme-1.png']
    ],
    'scope_checks': [
        'A/B bulk variants and explicitly inherited B conditions remain distinct.',
        'NC stock preparation and its 500 microlitre transfer are separate stages; no full-stock transfer implied.',
        'Composite-film mass ratios are context for five blends; no absolute loading invented.',
        'Peeling retains the composite film and separates the glass support; spin coating retains its support.',
        'Nitrogen is stated only for TGA; liquid nitrogen cooling hardware is not a reaction atmosphere.',
        'PLQE of NCs uses dried powder without an invented drying procedure.',
        'Film optical artwork is limited to film PL; no film PLE/decay measurement inferred.',
        'Acquisition panels do not invent measured spectra, atomic structures or apparatus dimensions.',
        'DFT is separate calculation context with composition-specific meshes and strict force bound.',
        'Adjacent conditions and captions were readable without observed crop clipping or label overlap.'
    ],
    'pre_freeze_author_correction': {
        'operation_id': 'film-pl',
        'initial_art_label': 'PL / PLE / decay',
        'final_art_label': 'Film PL',
        'reason': 'The film acquisition description supports PL only; generic optical labels were too broad.',
        'canonical_changes': 0,
        'source_changes': 0,
        're_rendered_and_viewed': True
    },
    'mounted_browser_checked': False,
    'scientific_independent_approval': False,
    'site_imported': False,
    'training_approved': False
}
write(A / 'author-visual-review.json', visual_review)

external = list(expected)
external += [C / 'record-manifest.json', L / 'source-inventory.json', L / 'source-tables.json',
             L / 'public-review-proposal/v1/lian2021.json', M / 'recipe-atlas/dist/quantity-value.mjs']
external += [Path(entry['path']) for entry in record_manifest['records']]
external += [L / rel for rel in ['source-render/main-06.png', 'source-render/main-07.png', 'reader-assets/scheme-1.png']]
configs = read(A / 'scene-config.json')['configs']
files = sorted(p for p in A.rglob('*') if p.is_file() and p.name != 'package-freeze.json' and '__pycache__' not in p.parts)
freeze = {
    'schema': 'mattersyn-private-apparatus-proposal/1',
    'source_id': 'lian2021', 'doi': '10.1021/acsami.1c18038', 'version': 1,
    'author': '/root/norberg2004_extract',
    'frozen_at': datetime.now(timezone.utc).isoformat(),
    'status': 'author_complete_pending_independent_audit',
    'canonical_manifest_sha256': sha(C / 'package-manifest.json'),
    'canonical_reader_audit_sha256': sha(L / 'canonical-reader-independent-audit/independent-audit-v1.json'),
    'source_freeze_sha256': sha(L / 'package-freeze.json'),
    'counts': {'canonical_records': 16, 'operation_records': 9, 'operations': 21,
               'operation_parameters': 34, 'additional_context_fields': 7, 'display_rows': 122,
               'art_types': len(set(x['art'] for x in configs.values())), 'svg_previews': 21,
               'png_previews': 21, 'contact_sheets': 6, 'author_checks': 594},
    'public_allowlist': [{'path': 'lian2021-protocol.mjs', 'sha256': sha(A / 'lian2021-protocol.mjs')}],
    'existing_public_dependency': {'path': 'quantity-value.mjs', 'sha256': sha(A / 'quantity-value.mjs')},
    'bound_files': {str(p): sha(p) for p in files},
    'bound_inputs': {str(p): sha(p) for p in sorted(set(external))},
    'independent_apparatus_approved': False, 'mounted_browser_approved': False,
    'site_imported': False, 'published': False, 'training_approved': False,
    'no_new_atomic_coordinate_or_measured_spectrum_claims': True
}
write(A / 'package-freeze.json', freeze)
print(json.dumps({'freeze_sha256': sha(A / 'package-freeze.json'),
                  'module_sha256': sha(A / 'lian2021-protocol.mjs'),
                  'counts': freeze['counts'], 'bound_files': len(files),
                  'bound_inputs': len(freeze['bound_inputs'])}))
