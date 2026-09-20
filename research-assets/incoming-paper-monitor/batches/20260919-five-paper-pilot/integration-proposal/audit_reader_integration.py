"""Independent ROOT transport/presentation audit; no promotion-science approval."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

I = Path(__file__).resolve().parent
B = I.parent
S = B.parents[3] / 'recipe-atlas'
D = S / 'dist'
checks, findings, bound, readers, records, reader_deltas, url_rows = [], [], {}, {}, {}, {}, []

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
def check(label, ok, detail=''):
    row = {'check': label, 'passed': bool(ok), 'detail': detail}; checks.append(row)
    if not ok: findings.append(row)
def bind(p, expected=None):
    p = Path(p).resolve(); value = sha(p); bound[str(p)] = value
    if expected is not None: check('sha256: ' + str(p), value == expected)
    return value
def walk(value, p=''):
    yield p, value
    if isinstance(value, dict):
        for k, v in value.items(): yield from walk(v, p + '/' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value): yield from walk(v, p + '/' + str(i))
def pointer(obj, path):
    for part in path.split('/')[1:]: obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj
def set_pointer(obj, path, value):
    parts = path.split('/')[1:]
    for p in parts[:-1]: obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    p = parts[-1]; obj[int(p) if isinstance(obj, list) else p] = value
def diff(a, b, p=''):
    if type(a) is not type(b): return [p]
    if isinstance(a, dict): return [d for k in sorted(set(a) | set(b)) for d in ([p + '/' + k] if k not in a or k not in b else diff(a[k], b[k], p + '/' + k))]
    if isinstance(a, list):
        if len(a) != len(b): return [p]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, p + '/' + str(i))]
    return [] if a == b else [p]

imports = read(I / 'record-import-manifest.json'); bind(I / 'record-import-manifest.json')
provisional_path = I / 'reader-integration-independent-audit.provisional.json'
provisional = read(provisional_path)
bind(provisional_path, '11ee5cf2cbb37c1ef128d99abb244d584dbe8745a4cc498053050c17865e528b')
bind(I / 'reader-integration-independent-audit.provisional.md')
check('Preserved initial report contains the three corrected current-status findings', len(provisional['open_findings']) == 3 and all('no contradictory current uncurated metadata' in x['check'] for x in provisional['open_findings']))
normalization = read(I / 'publication-url-normalization.json'); bind(I / 'publication-url-normalization.json')
normalized = {x['record_id']: x for x in normalization['records']}
check('12 records and 18 documented deployment URL replacements', len(normalized) == 12 and sum(len(x['deltas']) for x in normalized.values()) == 18)
bind(B / 'import_batch_records.py'); bind(B / 'normalize_public_asset_links.py')
baseline = read(I / 'base-record-hashes.json'); bind(I / 'base-record-hashes.json')
check('424 baseline record hashes retained', len(baseline) == 424)
for name, h in baseline.items(): bind(S / 'data/records' / name, h)
config = {'nagasaki2004': ('la036034c', 16, 2, 5, 'CdS'), 'ribeiro2004': ('jp0473669', 11, 1, 1, 'SnO2'), 'norberg2004': ('ja048427j', 19, 1, 4, 'Mn:ZnO')}
workflow_gaps = {
 'nagasaki2004': ('Molecular, polymer, protein, apparatus and crystal-reference bindings remain pending; no source-specific 3D geometry is approved by this proposal.', 'Molecular reference and symbolic polymer/protein depictions are separately audited illustrations. No source-specific CdS atomic coordinates or measured ligand geometry are supplied.'),
 'norberg2004': ('Molecular, apparatus, product/crystal visual assets and their exact source bindings remain pending separate review. No CIF or exact atomic coordinates are supplied.', 'Molecular and product illustrations and an external undoped ZnO crystal reference are separately audited. No sample-specific Mn:ZnO CIF, measured atom coordinates or resolved dopant-site occupations are supplied.'),
}
for sid, (folder, count, prec, partial, formula) in config.items():
    root = B / folder; row = next(x for x in imports['source_imports'] if x['source_id'] == sid)
    promotion_audit = read(root / 'promotion-source-audit.json'); bind(root / 'promotion-source-audit.json', row['promotion_audit_sha256'])
    check(sid + ': separate ROOT promotion audit dependency', promotion_audit['status'].startswith('passed') and not promotion_audit['open_findings'])
    old_path = root / f'public-review-proposal/{sid}.json'; old = read(old_path); bind(old_path, row['private_reader_sha256'])
    new_path = S / f'data/paper-reviews/{sid}.json'; new = read(new_path); bind(new_path, row['public_reader_sha256']); readers[sid] = new
    private_records = {p.stem: read(p) for p in (root / 'promotion-proposal/records').glob('*.json')}
    check(sid + ': full transported record set', len(private_records) == count and set(private_records) == set(row['records']))
    for rid, original in private_records.items():
        path = S / f'data/records/{rid}.json'; current = read(path); records[rid] = current
        bind(root / f'promotion-proposal/records/{rid}.json', row['records'][rid]); bind(path)
        restored = deepcopy(current)
        delta = normalized.get(rid)
        if delta:
            check(rid + ': transport hash before normalization', delta['before_sha256'] == row['records'][rid])
            check(rid + ': current normalized hash', sha(path) == delta['after_sha256'])
            for change in delta['deltas']:
                p = change['pointer']
                check(rid + p + ': URL-only documented change', p.startswith('/context_links/') and p.endswith('/url') and pointer(original, p) == change['old'] and pointer(current, p) == change['new'])
                asset_path = change['new'].removeprefix('../')
                candidates = [v for _, v in walk(old) if isinstance(v, dict) and v.get('public_asset') == asset_path]
                hashes = {v.get('public_asset_sha256', v.get('sha256')) for v in candidates}
                check(rid + p + ': same-named unique approved source image', asset_path.startswith('assets/figures/norberg2004/') and Path(change['old']).name == Path(asset_path).name and hashes == {change['asset_sha256']})
                bind(D / asset_path, change['asset_sha256']); set_pointer(restored, p, change['old']); url_rows.append({'record_id': rid, **change})
        check(rid + ': exact proposal after only deployment-URL restore', restored == original)
        generated_path = D / f'data/records/{rid}.json'; bind(generated_path)
        check(rid + ': public JSON exactly equals integrated record', read(generated_path) == current)
        html = D / f'records/{rid}.html'; bind(html)
        check(rid + ': generated record page exists', html.is_file())
        original_html_hash = provisional['bound_files'][str(html.resolve())]
        restored_html = html.read_bytes().replace(b'illustrated-guide.css?v=0.23.0-r2', b'illustrated-guide.css?v=0.23.0-r1')
        check(rid + ': generated HTML changes only approved stylesheet cache revision', hashlib.sha256(restored_html).hexdigest() == original_html_hash)
    expected = deepcopy(old)
    scope = next(iter(private_records.values()))['quality']['review_scope']
    expected.update(coverage_status=old['review_scope'] + '_review_complete', source_review_promoted=True, independent_audit=scope, publication_status='Reviewed contribution integrated into the existing MatterSyn atlas; deployment tracked separately.', training_note=f'{prec} precursor-selection and {partial} partial-protocol task rows are admitted from this source. Supporting procedures and analytical/model contexts retain distinct records. Missing source details and specimen links remain explicit; no exact-structure, size-conditioned, optical-outcome or success-prediction task is admitted.')
    if sid in workflow_gaps:
        removed, added = workflow_gaps[sid]; check(sid + ': exact superseded workflow sentence exists', removed in expected['remaining_gaps'])
        expected['remaining_gaps'].remove(removed); expected['remaining_gaps'].append(added)
    if expected.get('presentation_gates'):
        for key in ['molecular_bindings', 'apparatus_bindings', 'independent_reader_audit']: expected['presentation_gates'][key] = 'passed'
    for category in ['figures', 'tables', 'schemes', 'equations', 'source_notes']:
        for item in expected.get(category, []): item['reviewed'] = True
    for item in expected['recipe_inventory']:
        item['status'] = 'source_reviewed'
        item['gaps'] = [x for x in item['gaps'] if x not in ['Viewer bindings and presentation review pending.', 'Presentation and source-to-reader binding review pending.']]
    flag_paths = []
    for path, value in list(walk(expected['reader_sections'], '/reader_sections')):
        if isinstance(value, dict):
            for key in ['exact_molecular_asset_binding_approved', 'apparatus_binding_approved']:
                if value.get(key) is False: value[key] = True; flag_paths.append(path + '/' + key)
    check(sid + ': presentation flags limited to documented binding paths', set(flag_paths) == set(row['approved_presentation_flag_paths']))
    check(sid + ': exact reader equality after allowed metadata transforms', new == expected)
    reader_deltas[sid] = diff(old, new)
    for field in ['review_scope', 'documents', 'supporting_information', 'evidence_conflicts', 'material_evidence_records', 'material_original_asset_ids', 'route_evidence_contexts']:
        check(sid + ': preserved ' + field, new.get(field) == old.get(field))
    check(sid + ': unchanged item/section IDs', [(s['id'], [x['id'] for x in s['items']]) for s in new['reader_sections']] == [(s['id'], [x['id'] for x in s['items']]) for s in old['reader_sections']])
    public_reader = D / f'data/paper-reviews/{sid}.json'; bind(public_reader)
    generated_reader = read(public_reader)
    expected_public = deepcopy(new)
    expected_public['review_scope_label'] = 'Complete supplied main review; SI unverified' if new['review_scope'] == 'supplied_main_only_si_unverified' else 'Complete supplied main + matched SI review'
    check(sid + ': public reader adds only generated scope label', generated_reader == expected_public)
    for p, val in walk(new):
        if isinstance(val, dict) and val.get('record_id') in private_records and val.get('json_pointer'):
            try: pointer(records[val['record_id']], val['json_pointer']); ok = True
            except (KeyError, IndexError, ValueError): ok = False
            check(sid + p + ': canonical pointer resolves after import', ok)

allrecords = {p.stem: read(p) for p in (S / 'data/records').glob('*.json')}
check('470 records = unchanged 424 plus new 46', len(allrecords) == 470 and set(allrecords) == {Path(n).stem for n in baseline} | set(records))
bind(D / 'data/dataset-manifest.json'); dataset = read(D / 'data/dataset-manifest.json')
check('Dataset version and total', dataset['dataset_version'] == '0.23.0' and dataset['record_count'] == 470)
dataset_rows = {r['record_id']: r for r in dataset['records']}
for rid, record in records.items():
    check(rid + ': dataset manifest content digest', dataset_rows[rid]['record_sha256'] == digest(record))
check('Three distinct preserved source split groups', len({dataset_rows[r]['group_id'] for r in records}) == 3 and all(len({dataset_rows[r]['group_id'] for r in records if records[r]['lineage']['source_group'] == sid}) == 1 for sid in config))
review_index = read(D / 'data/paper-review-index.json'); bind(D / 'data/paper-review-index.json')
library = read(D / 'data/library-index.json'); bind(D / 'data/library-index.json')
materials = read(D / 'data/materials-index.json'); bind(D / 'data/materials-index.json')
inventory_path = S / 'data/inventory-summary.json'; inventory = read(inventory_path); bind(inventory_path)
for path in [D / 'data/inventory-summary.json', I / 'inventory-summary.json']:
    bind(path); check('Inventory transport: ' + str(path), read(path) == inventory)
check('Inventory totals reflect current records/hubs/source groups', inventory['summary']['canonical_records'] == 470 and inventory['summary']['public_material_hubs'] == len(materials['materials']) == 42 and inventory['summary']['reviewed_literature_source_groups'] == 30 and inventory['summary']['published_benchmark_source_groups'] == 1)
check('Inventory record IDs exhaustive without duplication', len([r for row in inventory['per_paper'] for r in row['record_ids']]) == 470 and {r for row in inventory['per_paper'] for r in row['record_ids']} == set(allrecords))
check('Inventory current normalized canonical tree', inventory['provenance']['canonical_tree_sha256'] == digest({k: digest(r) for k, r in sorted(allrecords.items())}))
for path, expected in inventory['provenance']['summary_artifact_sha256'].items(): bind(S / path, expected)
check('Historical inventory provenance explicitly separated', 'Historical' in inventory['provenance']['baseline_provenance_scope'])
navigation = []
for sid, (_, count, _, _, formula) in config.items():
    reader = readers[sid]; ids = {rid for rid, r in records.items() if r['lineage']['source_group'] == sid}
    rev = next(x for x in review_index['papers'] if x['id'] == sid)
    paper = next(x for x in library['papers'] if x['doi'] == reader['doi'])
    material = next(x for x in materials['materials'] if x['formula'] == formula)
    shard_path = D / f'data/materials/{material["id"]}.json'; shard = read(shard_path); bind(shard_path)
    paper_path = D / f'data/papers/{paper["id"]}.json'; bind(paper_path)
    paper_shard = read(paper_path)
    check(sid + ': source library compact fields match full shard', {k: paper_shard[k] for k in paper} == paper)
    check(sid + ': no contradictory current uncurated metadata', paper_shard.get('recipeCurationStatus') != 'not_curated_by_this_pipeline' and paper_shard.get('materialContributionStatus') != 'title_mentions_only_not_verified_material_or_recipe_contribution', str(paper_path) + ': ' + str({k: paper_shard.get(k) for k in ['recipeCurationStatus', 'materialContributionStatus', 'reviewStatus']}))
    check(sid + ': corrected exact current contribution status', paper_shard.get('recipeCurationStatus') == 'source_reviewed_records' and paper_shard.get('materialContributionStatus') == 'verified_synthesis_contribution')
    check(sid + ': old candidate status explicitly nested as indexing history', paper_shard.get('indexingStageStatus') == {'recipeCurationStatus': 'not_curated_by_this_pipeline', 'materialContributionStatus': 'title_mentions_only_not_verified_material_or_recipe_contribution'})
    restored_shard = deepcopy(paper_shard)
    restored_shard.update(restored_shard.pop('indexingStageStatus'))
    restored_shard_bytes = (json.dumps(restored_shard, ensure_ascii=False, separators=(',', ':')) + '\r\n').encode('utf-8')
    check(sid + ': only documented status correction changes paper shard bytes', hashlib.sha256(restored_shard_bytes).hexdigest() == provisional['bound_files'][str(paper_path.resolve())])
    check(sid + ': complete reader/source navigation', set(rev['record_ids']) == set(paper['reviewedRecordIds']) == ids and paper['fullDocumentReview']['url'] == rev['url'] == 'paper-review.html?id=' + sid)
    check(sid + ': source scope consistent across navigation', paper['fullDocumentReview']['scope'] == rev['review_scope'] == reader['review_scope'])
    check(sid + ': all requested evidence records reachable from material', set(reader['material_evidence_records'][formula]) <= {x['record_id'] for x in shard['evidence_records']})
    expected_routes = {r for r in ids if records[r]['record_type'] in ['literature_protocol', 'protocol_variant']}
    check(sid + ': only synthesis routes enter material route list', {r for r in shard['record_ids'] if r in ids} == expected_routes)
    check(sid + ': source contribution reachable in material hub', reader['doi'] in shard['paper_dois'] and any(x['doi'] == reader['doi'] and x['fullDocumentReview']['url'] == rev['url'] for x in shard['papers']))
    inv = next(x for x in inventory['per_paper'] if x['source_group'] == sid)
    check(sid + ': inventory preserves record and measurement counts', set(inv['record_ids']) == ids and inv['canonical_record_count'] == count and inv['measurement_entry_count'] == sum(len(records[r]['measurements']) for r in ids))
    if sid == 'ribeiro2004':
        check('Ribeiro SI remains unverified throughout', rev['si_status'] == 'not_located_or_verified' and inv['si_status'] == 'unverified' and paper['reviewStatus'] == 'main_only_reviewed' and len(inv['documents']) == 1)
    navigation.append({'source_id': sid, 'paper_url': 'paper.html?id=' + paper['id'], 'reader_url': rev['url'], 'material_url': material['url'], 'record_count': len(ids), 'direct_route_count': len(expected_routes), 'material_evidence_records': len(set(reader['material_evidence_records'][formula]))})

# Static transport contracts only: actual controls and layout are ROOT browser QA.
renderer_names = ['chemical-viewer.mjs', 'crystal-viewer.mjs', 'source-evidence.mjs', 'protocol-visuals.mjs', 'material-guide.mjs', 'material-app.mjs', 'library-app.mjs', 'paper-app.mjs', 'paper-review.mjs', 'illustrated-record.mjs']
for name in renderer_names: bind(D / name)
for name in ['build_atlas.py', 'build_paper_reviews.py', 'review_scope.py']: bind(S / 'scripts' / name)
bind(B / 'build_inventory_actual.py')
protocol_text = (D / 'protocol-visuals.mjs').read_text(encoding='utf-8')
for name in ['Nagasaki2004', 'Ribeiro2004', 'Norberg2004']:
    check(name + ': root protocol dispatch imports and invokes dedicated module', f'create{name}Art(o,r)' in protocol_text and f'build{name}Scene(o,r)' in protocol_text)
guide = (D / 'material-guide.mjs').read_text(encoding='utf-8')
check('Guide retains source-section navigation and source-scoped gallery controls', all(x in guide for x in ['route_evidence_contexts', 'material_original_asset_ids', 'paper-review.html?id=']))
chemical = (D / 'chemical-viewer.mjs').read_text(encoding='utf-8')
check('Chemical entry override remains approval-gated and allowlisted', "note?.binding_approved?note.viewOverrides:null" in chemical and "['name','caption','limitations']" in chemical)
check('Stock and reagent component mount contracts present', all(x in chemical for x in ['mountStockComponents', 'mountReagentComponents', 'does not assign solution speciation']))
for name in ['material.html', 'paper.html', 'paper-review.html', 'library.html']:
    check('Navigation shell exists: ' + name, (D / name).is_file()); bind(D / name)
bind(__file__)

result = {'schema': 'mattersyn.independent-reader-integration-audit/1', 'author': '/root', 'auditor': '/root/backlog_eta', 'status': 'passed_reader_transport_and_navigation_scope' if not findings else 'pending_root_correction', 'audited_at': datetime.now(timezone.utc).isoformat(),
 'scope': 'Independent ROOT reader/record transport, generated navigation/inventory and static renderer-contract audit. Explicitly excludes independent review of this auditor\'s task-selection or promotion science; those have separate ROOT audits. No browser or Site writes.',
 'counts': {'checks': len(checks), 'open_findings': len(findings), 'readers': 3, 'new_records': len(records), 'unchanged_old_records': len(baseline), 'reader_items': {sid: sum(len(s['items']) for s in r['reader_sections']) for sid, r in readers.items()}, 'deployment_url_changes': len(url_rows), 'url_changed_records': len(normalized), 'material_hubs': 42, 'canonical_records': 470, 'bound_files': len(bound)},
 'checks': checks, 'open_findings': findings, 'reader_changed_leaf_paths': reader_deltas, 'documented_url_deltas': url_rows, 'navigation': navigation, 'bound_files': bound,
 'correction_history': {'initial_report': str(provisional_path), 'initial_report_sha256': sha(provisional_path), 'initial_open_findings': provisional['open_findings'], 'resolved_scope': 'All three source shards now distinguish reviewed current contributions from historical indexing-stage candidate statuses. Restoring only the two current status values and removing their new historical wrapper reproduces each exact initial shard hash; no source/scientific shard fields changed.'},
 'scientific_payload_preserved': all(x['passed'] for x in checks if 'exact reader equality' in x['check'] or 'exact proposal after only' in x['check']), 'promotion_science_independently_audited_here': False, 'browser_approved': False, 'site_modified': False, 'ledger_modified': False, 'publication_approved': False,
 'actual_review_scope': ['Compared every reader field by exact nested equality after the documented metadata-only transformation, including all source facts, values, original assets, canonical links, conflicts and scientific gaps.', 'Checked transport of all 46 records against private proposals, restoring only 18 documented Norberg publication URLs across 12 records; original image names and hashes match approved source-scoped assets.', 'Verified all 424 pre-existing record hashes and the generated public JSON, record pages, source-library/reader indices, three material shards and inventory counts/provenance.', 'Read root renderer contracts for dedicated protocol dispatch, evidence/context navigation and approved chemical overrides. This is static inspection, not actual browser interaction.'],
 'limits': ['This audit cannot establish actual browser layout, control behavior or anonymous deployment.', 'Ribeiro retains full supplied-main-only review with SI unverified.', 'No sample/coordinate linkage or training eligibility is independently inferred by this transport audit.']}
(I / 'reader-integration-independent-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
md = [f'# Reader integration audit — {result["status"]}', '', 'Author: `/root`; independent transport auditor: `/root/backlog_eta`.', '', f'{len(checks)} checks; {len(findings)} open findings. All three readers preserve their scientific payload after documented promotion/presentation changes. All 46 records match the private proposals after restoring only 18 deployment URLs across 12 Norberg records. The 424 existing records are unchanged.', '', 'The initial three-finding report is preserved as reader-integration-independent-audit.provisional.json/.md. The three current paper shards now report source_reviewed_records and verified_synthesis_contribution, with former candidate values explicitly nested under indexingStageStatus. Reversing only this metadata correction reconstructs each exact original shard hash. Generated record HTML permits only the documented r1-to-r2 stylesheet cache revision; renderer appearance and interactions require ROOT browser QA.', '', 'The atlas exposes the CdS, SnO2 and Mn:ZnO contributions with full reader/source navigation and their supporting evidence records. Generated inventory reports 470 records, 42 material hubs, 30 reviewed-literature source groups plus one benchmark group. Ribeiro SI remains unverified.', '', 'Task-selection/promotion science was authored by this auditor and is explicitly outside this independent audit; ROOT supplied the separate promotion audits. Renderer inspection is static. Browser interaction and publication remain separate gates. Exact hashes, every reader delta and all URL changes are in the JSON report.']
if findings: md += ['', 'Open findings:'] + ['- ' + x['check'] + ': ' + x['detail'] for x in findings]
(I / 'reader-integration-independent-audit.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'counts': result['counts'], 'findings': findings, 'json_sha256': sha(I / 'reader-integration-independent-audit.json')}, indent=2))
