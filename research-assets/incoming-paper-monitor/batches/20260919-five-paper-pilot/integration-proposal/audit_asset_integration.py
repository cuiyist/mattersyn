"""Independent audit of root's asset import, excluding promotion authoring.

Reads live imported assets and retained private packages; writes only auditor
JSON/Markdown in this integration-proposal directory. No author scripts run.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

I = Path(__file__).resolve().parent
B = I.parent
S = B.parents[3] / 'recipe-atlas'
V = S / 'dist/assets/chemical-registry'
C = S / 'dist/assets/crystal-references'
checks, findings, bound, copies, changed_metadata = [], [], {}, [], []

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p, expected=None):
    p = Path(p).resolve(); value = sha(p); bound[str(p)] = value
    if expected is not None: check('sha256: ' + str(p), value == expected)
    return value
def check(name, ok, detail=''):
    row = {'check': name, 'passed': bool(ok), 'detail': detail}; checks.append(row)
    if not ok: findings.append(row)
def exact_copy(src, dest, expected=None, kind='asset'):
    source_hash = bind(src, expected); dest_hash = bind(dest)
    check(kind + ': exact copy ' + str(dest), source_hash == dest_hash)
    copies.append({'kind': kind, 'source': str(src), 'destination': str(dest), 'sha256': dest_hash})
def pointer(obj, p):
    for token in p.split('/')[1:]: obj = obj[int(token)] if isinstance(obj, list) else obj[token]
    return obj

manifest = read(I / 'asset-import-manifest.json'); bind(I / 'asset-import-manifest.json')
baseline = read(I / 'base-site-inputs.json'); bind(I / 'base-site-inputs.json')
bind(B / 'integrate_batch_assets.py')
for original, info in baseline.items():
    check('Baseline destination is inside retained directory', Path(info['snapshot']).resolve().is_relative_to((I / 'base-site-inputs').resolve()))
    bind(info['snapshot'], info['sha256'])
def base(path):
    info = baseline[str(path)]; return read(info['snapshot'])
for audit_path, expected in manifest['audits'].items():
    ap = Path(audit_path); audit = read(ap); bind(ap, expected)
    check(ap.name + ': passed independent private audit', audit['status'].startswith('passed'))
    raw = audit['bound_files']; bf = {x['path']: x['sha256'] for x in raw} if isinstance(raw, list) else raw
    for name, digest in bf.items():
        path = Path(name); path = path if path.is_absolute() else ap.parent / path
        if path.is_relative_to(S):
            saved = baseline.get(str(path))
            check('Audit-bound Site baseline retained: ' + str(path), saved is not None and saved['sha256'] == digest)
            if saved: bind(saved['snapshot'], digest)
        else: bind(path, digest)

registry = read(V / 'registry.json'); bind(V / 'registry.json')
reg_entries = {x['id']: x for x in registry['entries']}
base_registry = base(V / 'registry.json'); old_entries = {x['id']: x for x in base_registry['entries']}
check('Current registry IDs unique', len(reg_entries) == len(registry['entries']))
check('Existing registry entries unchanged', all(reg_entries.get(k) == value for k, value in old_entries.items()))
check('Registry metadata unchanged', {k: v for k, v in registry.items() if k != 'entries'} == {k: v for k, v in base_registry.items() if k != 'entries'})
new_ids = set(reg_entries) - set(old_entries)
check('Exactly 87 manifest-listed registry additions', len(new_ids) == 87 and new_ids == {x['id'] for x in manifest['new_registry_entries']})
roots = [
 ('la036034c', 'nagasaki2004', 'visuals/components', 'registry-additions.json'),
 ('jp0473669', 'ribeiro2004', 'visuals/molecules', 'registry-additions.json'),
 ('ja048427j', 'norberg2004', 'visuals/molecules', 'registry-additions.json'),
 ('ja048427j', 'norberg2004', 'visuals/products', 'product-registry-additions.json'),
]
proposed_ids = set()
for paper, sid, folder, filename in roots:
    root = B / paper / folder; proposal = read(root / filename); bind(root / filename)
    for old in proposal['entries']:
        expected = deepcopy(old); proposed_ids.add(old['id'])
        for field, value in [('independentScientificAudit', 'passed_source_scoped_reference_audit'), ('published', True), ('binding_approved', True)]:
            if field in expected: expected[field] = value
        expected['eligible_training'] = False
        current = reg_entries[old['id']]
        check(old['id'] + ': exact approved entry with metadata-only promotion', current == expected)
        check(old['id'] + ': manifest source', {'id': old['id'], 'source_id': sid} in manifest['new_registry_entries'])
        changed_metadata.append({'id': old['id'], 'allowed_fields': ['independentScientificAudit', 'published', 'binding_approved', 'eligible_training']})
        for key in ['svgPath', 'model2dPath', 'model3dPath']:
            if old.get(key): exact_copy(root / old[key], V / current[key], old['assetHashes'][key], 'chemical')
check('All new registry entries resolve to audited source proposals', proposed_ids == new_ids)

bindings = read(V / 'bindings.json'); bind(V / 'bindings.json'); old_bindings = base(V / 'bindings.json')
papers = {'la036034c': ('nagasaki2004', 'visuals/components/molecule-bindings-proposal.json'), 'jp0473669': ('ribeiro2004', 'visuals/molecules/molecule-bindings-proposal.json'), 'ja048427j': ('norberg2004', 'visuals/molecules/bindings-additions.json')}
records, slots, reader_counts = {}, {}, {}
for suffix, (sid, delta_name) in papers.items():
    root = B / suffix; delta = read(root / delta_name); bind(root / delta_name)
    ca = read(root / 'canonical-records-audit.json'); bind(root / 'canonical-records-audit.json')
    count = 0
    for path in sorted((root / 'canonical-drafts').glob('*.json')):
        record = read(path); rid = record['record_id']; records[rid] = record
        bind(path, ca['record_hashes'][rid])
        proposed = delta['recordBindings'].get(rid, {}); current = bindings['recordBindings'].get(rid)
        check(rid + ': all canonical material slots', current == proposed and set(proposed) == {m['id'] for m in record['materials']})
        notes = deepcopy(delta['bindingNotes'].get(rid, {}))
        for note in notes.values():
            if isinstance(note, dict):
                note['binding_approved'] = True
                note['independent_scientific_audit'] = 'Passed source-scoped molecular and specimen-reference audit.'
                if 'approval_status' in note: note['approval_status'] = 'passed'
        check(rid + ': source caption and notes preserved', bindings['bindingNotes'].get(rid) == notes)
        for mid, entry_id in proposed.items():
            check(rid + '/' + mid + ': registry resolves', entry_id in reg_entries)
            note = notes[mid]
            ptr = next((note[k] for k in ['canonical_material_pointer', 'json_pointer', 'canonical_pointer'] if k in note), None)
            check(rid + '/' + mid + ': exact source material pointer', ptr is not None and pointer(record, ptr)['id'] == mid)
            expected_hash = note.get('canonical_record_sha256', note.get('canonical_sha256'))
            if expected_hash: check(rid + '/' + mid + ': exact canonical hash', expected_hash == sha(path))
        count += len(proposed)
    slots[sid] = count
    exact_copy(root / f'visuals/apparatus/{sid}-protocol.mjs', S / f'dist/{sid}-protocol.mjs', kind='protocol')
    reader_path = root / f'public-review-proposal/{sid}.json'; reader = read(reader_path); bind(reader_path)
    needs = {}
    for category in ['figures', 'tables', 'schemes', 'equations', 'source_notes']:
        for item in reader[category]:
            if item.get('public_asset'): needs[item['public_asset']] = item['public_asset_sha256']
    for section in reader['reader_sections']:
        for item in section['items']:
            for a in item.get('original_assets', []): needs[a['public_asset']] = a.get('public_asset_sha256', a.get('sha256'))
    source_root = root / ('public-review-proposal/original-assets-pdfium' if suffix == 'ja048427j' else 'reader-assets')
    candidates = {sha(p): p for p in source_root.rglob('*.png')}
    for path, digest in needs.items():
        destination = S / 'dist' / path
        check('Original image destination confined to dist', destination.resolve().is_relative_to((S / 'dist').resolve()))
        check(sid + ': original reader image found in frozen package', digest in candidates)
        if digest in candidates: exact_copy(candidates[digest], destination, digest, 'original')
    reader_counts[sid] = len(needs)
check('147 slots with correct per-paper counts', slots == manifest['material_slots'] == {'nagasaki2004': 61, 'ribeiro2004': 13, 'norberg2004': 73})
check('63 originals with correct per-paper counts', reader_counts == manifest['original_assets'] == {'nagasaki2004': 8, 'ribeiro2004': 15, 'norberg2004': 40})
restored_bindings = deepcopy(bindings)
for rid in records:
    check(rid + ': new binding record only', rid not in old_bindings['recordBindings'])
    restored_bindings['recordBindings'].pop(rid, None); restored_bindings['bindingNotes'].pop(rid, None)
    # Root subsequently imported records and attached their current byte hashes.
    # Check provenance only here; promotion-science approval is outside scope.
    imported_record = S / 'data/records' / (rid + '.json')
    imported_hash = bind(imported_record)
    check(rid + ': current imported-record binding hash', bindings['sourceRecordSha256'].get(rid) == imported_hash)
    check(rid + ': source hash addition did not overwrite baseline', rid not in old_bindings['sourceRecordSha256'])
    restored_bindings['sourceRecordSha256'].pop(rid, None)
check('All existing binding data exactly unchanged', restored_bindings == old_bindings)

products = read(V / 'product-bindings.json'); bind(V / 'product-bindings.json')
product_delta_path = B / 'ja048427j/visuals/products/product-reference-proposal.json'; bind(product_delta_path)
product_delta = read(product_delta_path)['recordBindings']
expected_products = deepcopy(base(V / 'product-bindings.json')); expected_products['recordBindings'].update(product_delta)
check('Only audited Norberg overview bindings added', products == expected_products)
check('Ten audited Norberg overview bindings', len(product_delta) == 10 and all(r in records and e in reg_entries for r, e in product_delta.items()))

contexts = read(V / 'product-contexts.json'); bind(V / 'product-contexts.json')
nagasaki_path = B / 'la036034c/visuals/products/product-context-bindings-proposal.json'; bind(nagasaki_path)
expected_contexts = {}
for row in read(nagasaki_path)['contexts']:
    expected_contexts.setdefault(row['record_id'], []).append({'sample_id': row['sample_id'], 'registry_id': row['registry_id'], 'label': row['canonical_product']['source_sample_label'] or row['sample_id'], 'caption': row['source_caption'], 'phase': row['canonical_phase'], 'canonical_pointer': row['canonical_pointer']})
for rid, record in records.items():
    if not rid.startswith('ribeiro-'): continue
    for i, product in enumerate(record['products']):
        if product['composition']['value'] != 'SnO2': continue
        expected_contexts.setdefault(rid, []).append({'sample_id': product['sample_id'], 'registry_id': 'identity-ribeiro-sno2-colloid', 'label': product['source_sample_label'] or product['sample_id'], 'caption': 'Source-defined SnO₂ specimen or series. The symbol does not supply a measured particle envelope, atomic coordinates or an exact cross-technique sample association.', 'phase': product['phase'], 'canonical_pointer': f'/products/{i}'})
check('Exact 22 Nagasaki plus 20 Ribeiro context mappings', contexts['recordContexts'] == expected_contexts and sum(map(len, expected_contexts.values())) == 42)
check('Context counts exactly agree with manifest', {k: len(v) for k, v in expected_contexts.items()} == manifest['source_product_contexts'])
context_rows = []
for rid, rows in contexts['recordContexts'].items():
    check(rid + ': unique context sample IDs', len({x['sample_id'] for x in rows}) == len(rows))
    for row in rows:
        product = pointer(records[rid], row['canonical_pointer']); entry = reg_entries[row['registry_id']]
        check(rid + '/' + row['sample_id'] + ': exact product and phase', product['sample_id'] == row['sample_id'] and product['phase'] == row['phase'])
        check(rid + '/' + row['sample_id'] + ': no atomic model', entry.get('model2dPath') is None and entry.get('model3dPath') is None)
        context_rows.append({'record_id': rid, 'sample_id': row['sample_id'], 'phase': row['phase']['value'], 'phase_status': row['phase']['status'], 'registry_id': row['registry_id']})
check('Ribeiro assigned phase only in preparation-series context', [(x['record_id'], x['sample_id']) for x in context_rows if x['record_id'].startswith('ribeiro') and x['phase'] is not None] == [('ribeiro-2004-hydrolysis', 'final-series')])
check('Nagasaki assigned phase only in SI XRD context', [(x['record_id'], x['sample_id']) for x in context_rows if x['record_id'].startswith('nagasaki') and x['phase'] is not None] == [('nagasaki-2004-xrd', 'si-xrd-cds')])

solutions = read(V / 'solution-components.json'); bind(V / 'solution-components.json')
component_path = B / 'jp0473669/visuals/molecules/component-view-proposal.json'; component = read(component_path); bind(component_path)
source_extra = [x for x in component['components'] if not x.get('canonical_stock_pointer')]
check('Exactly two supplemental aqueous component contexts', len(solutions['contexts']) == len(source_extra) == 2)
for current, proposed in zip(solutions['contexts'], source_extra):
    check(current['label'] + ': correct canonical record', current['record_id'] == proposed['canonical_record_id'] == 'ribeiro-2004-ph-treatment')
    check(current['label'] + ': unchanged context/uncertainty', current['label'] == proposed['context'] and current['scope'] == proposed['scope'])
    check(current['label'] + ': exact component identity and role', [(x['registry_id'], x['role']) for x in current['components']] == [(x['registry_id'], x['role']) for x in proposed['components']])
    for entry in current['components']:
        check(current['label'] + ': component resolves', entry['registry_id'] in reg_entries)
        if entry['registry_id'] == 'water':
            check(current['label'] + ': source-neutral solvent override', entry['viewOverrides'] == {'name': 'Water · aqueous reagent solvent', 'caption': 'Water component reference for this aqueous reagent. Its grade, number of solvent molecules and solution geometry are not specified.', 'limitations': ['This is a separate solvent reference, not an assigned solution structure.']})
        else: check(current['label'] + ': neutral reference metadata retained', entry['viewOverrides'] == {})
    material = pointer(records[current['record_id']], proposed['canonical_material_pointer'])
    if 'TBAOH' in current['label']:
        check('TBAOH stock remains 0.4 mol/L, not a final concentration', any(q['value'] == 0.4 and q['status'] == 'reported' for q in material['quantities'].values()))

crystals = read(C / 'registry.json'); bind(C / 'registry.json'); base_crystals = base(C / 'registry.json')
crystal_path = B / 'ja048427j/visuals/products/crystal-reference-proposal.json'; proposal_crystals = read(crystal_path); bind(crystal_path)
expected_crystals = deepcopy(base_crystals); expected_crystals['entries'] += proposal_crystals['entries']
check('Crystal registry changes only by one exact audited entry', crystals == expected_crystals and len(proposal_crystals['entries']) == 1)
for entry in proposal_crystals['entries']:
    check('New crystal is undoped external ZnO only', entry['formula'] == 'ZnO' and entry['referenceOnly'] is True and entry['trainingEligible'] is False and entry['measuredSampleStructure'] is False and entry['structureAssetRole'] == 'external_reference')
    for key, hkey in [('cifPath', 'cifSha256'), ('modelPath', 'modelSha256'), ('finiteModelPath', 'finiteModelSha256')]:
        exact_copy(crystal_path.parent / entry[key], C / entry[key], entry[hkey], 'crystal')
    for d in entry['additionalDownloads']: exact_copy(crystal_path.parent / d['path'], C / d['path'], d['sha256'], 'crystal')
check('Manifest claims no measured structure imports', manifest['exact_measured_structure_imports'] == 0 and manifest['external_crystal_references_added'] == 1)
preview = B / 'jp0473669/visuals/molecules/review/identity-ribeiro-sno2-colloid.png'; bind(preview)
bind(__file__)

manual = [
 'Root subsequently added 46 sourceRecordSha256 keys after importing records. Each matches the current Site record bytes; all 424 baseline keys remain unchanged. This narrow provenance check does not independently approve the promotion proposals authored by this auditor.',
 'Read the root import script without executing it and compared the four entry proposals, three complete material-binding proposals, product/context and solution proposals against current imported JSON.',
 'Read all root-created Ribeiro context labels: HRTEM concentration and histogram series, acid-set pH and post-TBAOH optical contexts, acquisition, UV/PL and zeta remain separate record/sample keys. Only final-series carries reported cassiterite; no phase is propagated into the other 19 contexts.',
 'Actually viewed the retained Ribeiro SnO2 preview: five unequal symbolic discs are explicitly labeled as composition symbols without size scale or atomic lattice. The copied SVG is hash-identical. This rechecks its suitability for root context assignment, not a new independent audit of this auditor\'s earlier asset authoring.',
 'Checked all 22 Nagasaki mappings against the passed private product audit. Approximate abstract size, optical 4.8 nm estimate, biotin donor and generic SI TEM/XRD contexts are not merged; only SI XRD carries the author wurtzite assignment.',
 'Read source notices and supplemental aqueous-reagent scopes. Ribeiro acid concentration, water stoichiometry, final TBAOH dose/concentration and final measurement pH remain unknown; TBAOH is not TBAB, and reagent solvent water does not inherit dialysis/deionized grade.',
 'Norberg imports retain distinct sample/film/control cards and the exact previously audited external undoped ZnO cell/finite crop. They introduce no Mn sites, measured nanocrystal CIF or exact recipe-structure pair.',
]
result = {'schema': 'mattersyn.independent-asset-integration-audit/1', 'author': '/root', 'auditor': '/root/backlog_eta', 'audited_at': datetime.now(timezone.utc).isoformat(), 'status': 'passed_asset_import_scope' if not findings else 'pending_root_correction',
 'scope': 'Independent audit of ROOT asset import and newly assembled product/solution contexts only. Does not audit this auditor\'s authored canonical promotion proposals. Existing private scientific/model/visual approvals are dependencies. No renderer/browser/publication approval.',
 'counts': {'checks': len(checks), 'findings': len(findings), 'baseline_snapshots': len(baseline), 'new_registry_entries': len(new_ids), 'material_slots': slots, 'original_images': reader_counts, 'product_contexts': len(context_rows), 'supplemental_solution_contexts': len(solutions['contexts']), 'external_crystal_entries': len(proposal_crystals['entries']), 'measured_structure_imports': 0, 'copied_files_by_kind': dict(Counter(x['kind'] for x in copies)), 'bound_files': len(bound)},
 'checks': checks, 'open_findings': findings, 'actual_manual_scope': manual, 'context_phase_rows': context_rows, 'exact_copies': copies, 'allowed_entry_metadata_deltas': changed_metadata, 'baseline_resolution_policy': 'Every earlier audit-bound Site path is checked against its retained baseline copy and original hash. Mutable current renderer files are outside this scope; imported registries and assets are checked against explicit allowed deltas.',
 'bound_files': bound, 'auditor_site_edits': False, 'auditor_ledger_edits': False, 'author_scripts_rerun': False, 'promotion_proposals_audited': False, 'browser_approved': False, 'publication_approved': False,
 'retained_limits': ['Asset published/approval flags are integration metadata, not proof of public delivery.', 'Root context selectors and solution-component runtime behavior require separate renderer/browser tests.', 'No new experimental coordinates or resolved cross-technique sample joins are established.', 'Prior source and visual audits remain bounded to their actual manual scope.']}
(I / 'asset-integration-independent-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
md = [f'# Asset integration audit — {result["status"]}', '', 'Author: `/root`; independent integration auditor: `/root/backlog_eta`.', '', f'{len(checks)} checks; {len(findings)} open findings. Verified 57 retained baseline snapshots, 87 registry additions, 147 material slots, 63 original images, three protocol modules, 42 product contexts, two supplemental aqueous-component contexts and one external undoped ZnO reference with four copied files.', '', 'All existing registry and binding data remain unchanged. New entry/binding science matches the audited private proposals exactly after the explicit approval/status metadata changes. The 20 new Ribeiro SnO2 mappings preserve their canonical sample and phase scopes; Nagasaki\'s 22 precise mappings are unchanged.', '']
md += ['- ' + x for x in manual]
md += ['', 'No measured atomic-structure import, exact sample join, publication proof or browser approval is established. Canonical promotion proposals are outside this audit. The auditor changed no Site, ledger, source, canonical or author files. Exact current hashes and baseline resolution are retained in the JSON report.']
if findings: md += ['', 'Open findings:'] + ['- ' + x['check'] + ': ' + x['detail'] for x in findings]
(I / 'asset-integration-independent-audit.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'counts': result['counts'], 'findings': findings, 'json_sha256': sha(I / 'asset-integration-independent-audit.json'), 'md_sha256': sha(I / 'asset-integration-independent-audit.md')}, indent=2))
