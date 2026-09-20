"""Independent, read-only input checks; writes only this auditor's two reports."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
Q = ROOT / 'visuals/products'
EXPECTED_FREEZE = 'bbb0f502241de768766731792e7901c04ebb88329e31adffd4eb80132638dd36'
checks = []
bound = {}

def sha(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return digest

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def check(label, condition):
    checks.append({'check': label, 'passed': bool(condition)})

def bind(path, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    bound[str(path)] = digest
    if expected is not None:
        check('sha256: ' + str(path), digest == expected)
    return digest

def pointer(obj, path):
    for part in path.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

freeze = read(Q / 'package-freeze.json')
bind(Q / 'package-freeze.json', EXPECTED_FREEZE)
check('Distinct author and auditor', freeze['author'] == '/root/peng1998_reader_assets')
for path, digest in freeze['bound_inputs'].items():
    bind(path, digest)
for path, digest in freeze['output_files'].items():
    bind(Q / path, digest)
check('26 frozen output files', len(freeze['output_files']) == 26)
source_audit = read(ROOT / 'source-scientific-audit.json')
bind(ROOT / 'source-scientific-audit.json', 'df5069d3addf63de102f2c2a3563848e2b65df4fa6e38f43b326f56ac797a00c')
check('Previously passed full-source audit retained', source_audit['status'].startswith('pass'))
records = {p.stem: read(p) for p in (ROOT / 'canonical-drafts').glob('*.json')}
check('16 canonical records', len(records) == 16)
all_products = {(rid, x['sample_id']): (f'/products/{i}', x)
                for rid, r in records.items() for i, x in enumerate(r.get('products', []))}
mapping = read(Q / 'product-context-bindings-proposal.json')
contexts, exclusions = mapping['contexts'], mapping['excluded_contexts']
check('22 context bindings', len(contexts) == 22)
check('6 exclusions', len(exclusions) == 6)
keys = [(x['record_id'], x['sample_id']) for x in contexts + exclusions]
check('All 28 canonical products covered exactly once', len(keys) == len(set(keys)) == 28 and set(keys) == set(all_products))
expected = {
 'biotin-cds': {'biotin-cds-generic': 'biotin-cds-specimen-reference', 'abstract-size-context': 'cds-reference'},
 'cho-cds': {'cho-cds-representative': 'cds-reference'},
 'concentration-series': {x: 'cds-reference' for x in ['cho-cds-low-amine', 'cho-cds-mid-amine', 'cho-cds-high-amine', 'figure2-series-context']},
 'fret': {x: 'biotin-cds-specimen-reference' for x in ['figure4-fret-series', 'figure6-response-series']},
 'optical': {'figure2-absorption-sample-unresolved': 'uv-specimen-reference', 'cho-cds-generic': 'cds-reference', 'biotin-cds-optical-context': 'biotin-cds-specimen-reference'},
 'recognition-controls': {x: 'biotin-cds-specimen-reference' for x in ['figure5-competition-series', 'figure5-bsa-series']},
 'salt-challenge': {'cho-cds-salt-challenge': 'salt-cho-specimen-reference', 'figure1-label-context': 'cds-reference'},
 'stabilizer-controls': {'no-polymer-control': 'salt-no-polymer-specimen-reference', 'peg-control': 'salt-peg-specimen-reference', 'pama-control': 'salt-pama-specimen-reference'},
 'tem': {'si-tem-grid': 'si-tem-dispersion-reference'},
 'xrd': {'si-xrd-cds': 'si-xrd-cds-dispersion-reference'},
 'zeta': {'zeta-series': 'zeta-dispersion-reference'},
}
expected = {(f'nagasaki-2004-{r}', s): f'nagasaki2004-{v}' for r, values in expected.items() for s, v in values.items()}
snapshot = read(Q / 'reference-inputs/component-entry-snapshots.json')
entries = {x['id']: x for x in snapshot['entries']}
registry = {x['id']: x for x in read(ROOT / 'visuals/components/registry-additions.json')['entries']}
check('10 symbolic entries', len(entries) == 10)
for entry_id, entry in entries.items():
    check(entry_id + ': exact original component entry', entry == registry[entry_id])
    check(entry_id + ': no atomic model', entry['model2dPath'] is None and entry['model3dPath'] is None)
    check(entry_id + ': no measured coordinates', entry['provenance']['measuredCoordinates'] is False)
    check(entry_id + ': unchanged original SVG', bind(Q / entry['svgPath'], entry['assetHashes']['svgPath']) == sha(ROOT / 'visuals/components' / entry['svgPath']))
    check(entry_id + ': scope/source neutral to unrelated papers', entry['provenance']['sourceId'] == 'nagasaki2004')
for x in contexts:
    rid, sid = x['record_id'], x['sample_id']
    label = f'{rid}::{sid}'
    r = records[rid]
    product = pointer(r, x['canonical_pointer'])
    check(label + ': independently expected depiction', x['registry_id'] == expected[(rid, sid)])
    check(label + ': exact record hash', x['canonical_record_sha256'] == sha(ROOT / 'canonical-drafts' / f'{rid}.json'))
    check(label + ': exact typed canonical product', x['canonical_product'] == product)
    check(label + ': exact sample and context IDs', product['sample_id'] == sid and x['context_id'] == label)
    check(label + ': CdS composition', product['composition']['value'] == 'CdS')
    check(label + ': phase not silently changed', x['canonical_phase'] == product['phase'])
    check(label + ': symbolic diagram only', x['depiction_kind'] == 'symbolic_composition_reference')
    check(label + ': no invented atomic availability', all(x[k] is None for k in ['model_phase', 'unit_cell_asset', 'finite_atomic_asset', 'cif_download', 'vesta_download']))
    check(label + ': pending final integration and training', x['binding_approved'] is False and x['training_eligible'] is False and x['independent_audit'] == 'pending')
    check(label + ': exact SVG association', x['private_svg'] == entries[x['registry_id']]['svgPath'])
    for m in x['associated_source_measurements']:
        check(label + ': exact measurement ' + m['canonical_pointer'], pointer(r, m['canonical_pointer']) == m['measurement'])
        check(label + ': sample-local measurement ' + m['canonical_pointer'], m['measurement']['sample_id'] == sid)
    expected_figures = {'si-tem-grid': ['nagasaki2004-si-figure1'], 'si-xrd-cds': ['nagasaki2004-si-figure2']}.get(sid, [])
    check(label + ': original image not reassigned across contexts', x['direct_original_figure_ids'] == expected_figures)
for x in exclusions:
    product = pointer(records[x['record_id']], x['canonical_pointer'])
    check(x['sample_id'] + ': exclusion preserves composition', x['canonical_composition'] == product['composition'])
    check(x['sample_id'] + ': not a CdS product', product['composition']['value'] != 'CdS')

figures = {x['id']: x for x in read(ROOT / 'public-review-proposal/nagasaki2004.json')['figures']}
originals = read(Q / 'original-evidence-proposal.json')
check('Only two original SI assets', len(originals['assets']) == 2)
for a in originals['assets']:
    fig = a['reader_figure']
    check(fig['id'] + ': complete exact frozen reader metadata', fig == figures[fig['id']])
    check(fig['id'] + ': exact unchanged source crop', bind(Q / a['private_copy'], a['sha256']) == sha(ROOT / 'reader-assets' / Path(a['private_copy']).name))
    check(fig['id'] + ': correct SI source hash', fig['asset_provenance']['source_sha256'] == '224d32916abff15329391fb1f8ba618e13dbfae63253e8ca597f4891e7cf5733')
    check(fig['id'] + ': one explicit technique scope', len(fig['canonical_sample_links']) == 1)
    link = fig['canonical_sample_links'][0]
    check(fig['id'] + ': exact canonical sample exists', (link['record_id'], link['sample_id']) in all_products)

crystal = read(Q / 'crystal-reference-proposal.json')
check('No atomic entries created', crystal['entries'] == [])
phase_pointer = crystal['source_phase_pointer']
check('Author phase preserved at precise XRD product', crystal['source_phase_evidence'] == pointer(records[phase_pointer['record_id']], phase_pointer['pointer']))
check('Only XRD product has an assigned phase', [(x['record_id'], x['sample_id']) for x in contexts if x['canonical_phase']['value'] is not None] == [('nagasaki-2004-xrd', 'si-xrd-cds')])
check('No source or imported structure claim', all(crystal['source_structure_status'][k] is False for k in ['exact_measured_atomic_coordinates', 'CIF_supplied', 'external_structure_imported', 'verified_recipe_structure_sample_join']))
cache = read(Q / 'cached-reference-inventory.json')
crystal_registry = read(Q / 'reference-inputs/crystal-registry-snapshot.json')
cache_entries = {x['id']: x for x in cache['entries']}
original_crystal_entries = {x['id']: x for x in crystal_registry['entries']}
check('All nine cached registry entries inspected by proposal', len(cache_entries) == 9 and set(cache_entries) == set(original_crystal_entries))
for k, v in cache_entries.items():
    check(k + ': exact cached formula', v['formula'] == original_crystal_entries[k]['formula'])
    check(k + ': different composition rejected', v['formula'] != 'CdS' and v['eligible_for_nagasaki_CdS'] is False)
overview = read(Q / 'product-reference-proposal.json')
check('Overview requires context caption support', overview['requires_context_caption_support'] is True and overview['bindingApproved'] is False)
check('Implementation proposal did not apply changes', read(Q / 'implementation-proposal.json')['changes_applied'] is False)
bind(Path(__file__))

manual_scope = [
 {'scope': 'All 22 context mappings and all 6 exclusions', 'result': 'Read against the exact previously audited canonical products. Record plus sample keys preserve context boundaries; exclusions remove only CdS depiction eligibility, not source records or outcomes.'},
 {'scope': '10 unchanged symbolic product depictions', 'viewed_files': [str(ROOT / f'visuals/components/review/contact-{i:02}.png') for i in [5, 6, 7]], 'result': 'Actually viewed all ten relevant previews in three retained contacts. CdS discs, polymer paths and particle counts are explanatory symbols without a measured scale or atomistic geometry. Other contact-sheet entries were visible but are outside this product audit.'},
 {'scope': 'Original SI Figure 1', 'viewed_file': str(Q / 'originals/si-figure1.png'), 'result': 'Actually viewed both original TEM panels, upper 50 nm and lower 20 nm bars and retained caption. No new particle statistics, biotin-specific assignment or lattice coordinates inferred.'},
 {'scope': 'Original SI Figure 2', 'viewed_file': str(Q / 'originals/si-figure2.png'), 'result': 'Actually viewed original powder diffractogram, reference sticks, intensity and 2-theta axes and caption. The author wurtzite assignment comes from main-page-3 discussion; no hkl/card identity, atom refinement or separate polymer-only trace is invented.'},
 {'scope': 'Size and cross-technique associations', 'result': 'Abstract ca. 5 nm remains a summary. The 467 nm absorption-edge/4.8 nm band-gap-model estimate remains an unresolved optical context, not a TEM population, measured SI specimen envelope or biotin-specific particle size. SI TEM, SI XRD, CHO/biotin and assay batch identities remain unresolved.'},
 {'scope': 'Concentration, stabilization and recognition contexts', 'result': 'Low/mid/high amine formulations, no-polymer/PEG/PAMA controls, CHO salt challenge and preformed biotin donor assay contexts retain their distinct purposes. These 22 views are not 22 independent syntheses or measured crystal structures.'},
 {'scope': 'Phase and coordinate availability', 'result': 'Only the SI XRD CdS product carries the authors\' hexagonal-wurtzite phase assignment. No numeric lattice parameters, coordinates, unit cells, finite atomic crops or CIF/VESTA assets are supplied or approved. Nine retained registry candidates have different chemical formulas; no substitutions made.'},
 {'scope': 'Future integration boundary', 'result': 'The optional four record-overview bindings must remain subordinate to record-plus-sample context selection and captions, particularly on the biotin and XRD pages. Renderer integration and actual browser behavior were not tested in this bounded private product audit.'},
]
failed = [x for x in checks if not x['passed']]
report = {
 'schema': 'mattersyn.independent-product-source-audit/1', 'source_id': 'nagasaki2004', 'doi': '10.1021/la036034c',
 'auditor': '/root/backlog_eta', 'author': '/root/peng1998_reader_assets', 'audited_at': datetime.now(timezone.utc).isoformat(),
 'status': 'passed_private_product_mapping_scope' if not failed else 'pending_author_correction',
 'author_freeze_sha256': EXPECTED_FREEZE,
 'scope': 'Independent product/context mapping and availability audit only, relying on previously passed source and canonical audits. No repeat full-source extraction, general component-model approval, Site integration or browser approval.',
 'counts': {'canonical_records': len(records), 'canonical_products': len(all_products), 'CdS_contexts': len(contexts), 'non_CdS_exclusions': len(exclusions), 'symbolic_depictions': len(entries), 'original_SI_images': len(originals['assets']), 'atomic_entries': len(crystal['entries']), 'mechanical_checks': len(checks), 'failed_checks': len(failed), 'manual_review_scopes': len(manual_scope), 'bound_files': len(bound)},
 'actual_manual_review': manual_scope, 'mechanical_checks': checks, 'findings': failed,
 'retained_constraints': ['No exact recipe/TEM/XRD/optical/biotin sample join.', 'The 4.8 nm value is an author optical-model estimate; ca. 5 nm is a separate abstract-level summary.', 'The XRD phase assignment is not an atomistic structure measurement.', 'No qualified CdS coordinate reference was found within the inspected cached scope; this is not a universal absence claim.', 'No atomic viewer or CIF/VESTA download is available.', 'Context-specific captions and selectors remain required before future integration.'],
 'bound_files': bound,
 'author_files_modified': False, 'source_files_modified': False, 'site_modified': False, 'ledger_modified': False,
 'new_downloads': False, 'author_scripts_rerun': False, 'browser_approval': False, 'publication_approval': False, 'training_admission': False,
}
(ROOT / 'product-source-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
lines = [f'# Nagasaki private product mapping audit — {"passed" if not failed else "pending"}', '',
 'Independent auditor: `/root/backlog_eta`; author: `/root/peng1998_reader_assets`.', '',
 f'Author freeze SHA256: `{EXPECTED_FREEZE}`.', '',
 f'Checked all 28 canonical product contexts: 22 CdS mappings and 6 non-CdS exclusions, with 10 unchanged symbolic depictions and 2 original SI images. {len(checks)} mechanical checks passed; {len(failed)} failed. Bound {len(bound)} files. No scientific mismatch or required author correction was found.' if not failed else f'{len(failed)} checks failed; see JSON.', '',
 'This pass covers the private product mapping and availability proposal. Previously passed source and canonical audits provide the underlying extraction basis; this is not a renewed full-source or component-model audit.', '']
for x in manual_scope:
    lines += [f'- **{x["scope"]}:** {x["result"]}']
lines += ['', 'No author/source/Site/ledger files were changed and no author scripts or downloads were run. Integration, final binding flags, actual browser behavior, publication and training admission remain separate gates.', '', 'Exact input/output hashes, each mechanical check and actual manual scope are retained in `product-source-audit.json`.']
(ROOT / 'product-source-audit.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'counts': report['counts'], 'failures': failed, 'json_sha256': sha(ROOT / 'product-source-audit.json'), 'md_sha256': sha(ROOT / 'product-source-audit.md')}, indent=2))
