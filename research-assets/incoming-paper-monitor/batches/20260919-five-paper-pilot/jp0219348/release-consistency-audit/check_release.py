"""Bounded read-only Site release consistency audit; writes this audit folder only."""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib, re, copy, importlib.util

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
H = A.parent
M = H.parents[4]
S = M / 'recipe-atlas'
D = S / 'dist'
O = H / 'site-integration-proposal'
V = H / 'canonical-proposal/v2'
bound, checks = {}, []

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
    p = Path(p).resolve(); bound[str(p)] = sha(p); return p
def read(p): return json.loads(bind(p).read_bytes())
def ck(label, ok): checks.append({'check': label, 'passed': bool(ok)})
def walk(x, path=''):
    yield path, x
    if isinstance(x, dict):
        for k, v in x.items(): yield from walk(v, path + '/' + k)
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from walk(v, path + '/' + str(i))
def diff(a, b, path=''):
    if type(a) is not type(b): return [path]
    if isinstance(a, dict):
        out = []
        for k in a.keys() | b.keys():
            out += [path + '/' + k] if k not in a or k not in b else diff(a[k], b[k], path + '/' + k)
        return out
    if isinstance(a, list):
        if len(a) != len(b): return [path + '/length']
        return [p for i, (x, y) in enumerate(zip(a,b)) for p in diff(x,y,path+'/'+str(i))]
    return [] if a == b else [path]

policy_path = bind(M/'research-assets/public_projection_policy.py')
spec=importlib.util.spec_from_file_location('audited_public_policy', policy_path)
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
metadata=policy.policy_metadata()
baseline=bind(M/'research-assets'/policy.REPORT_RELATIVE)
ck('Policy is 2026-09-20.2 with exact reviewed baseline',metadata['version']=='2026-09-20.2' and sha(baseline)==policy.EXPECTED_REPORT_SHA256 and metadata['baseline_excluded_path_count']==12556)
plan=read(H/'publication-projection-audit/publication-projection-proposal.json')
source_assets=read(V/'public-review-proposal/reader-original-assets-manifest.json')
prior=read(H/'site-integration-independent-audit/promotion-projection-delta-audit.json')
product_audit=read(H/'visuals/products-independent-audit/product-si-source-audit.json')
app_audit=read(H/'visuals/apparatus/audit-v1/apparatus-source-audit.json')
imp=read(O/'site-import-manifest.json'); browser=read(O/'browser-validation.json')
ck('Prior scientific/projection audit scopes passed',prior['status'].startswith('passed_') and product_audit['status'].startswith('passed_') and app_audit['status'].startswith('passed_'))
ck('Root actual browser pass bound by import manifest',browser['status']=='passed' and sha(O/'browser-validation.json')==imp['browser_validation_sha256'] and browser['reviewer']=='root')
reader=read(D/'data/paper-reviews/heo2003.json'); staged=read(O/'promoted-reader/heo2003.json')
allowed_changes={
 '/audit_details/apparatus_audit_sha256','/audit_details/product_reflection_audit_sha256',
 '/audit_details/promotion_audit_sha256','/presentation_gates/apparatus_bindings',
 '/presentation_gates/average_position_occupancy_binding','/presentation_gates/browser_render',
 '/presentation_gates/site_integration','/publication_status','/review_scope_label'}
reader_delta=sorted(diff(staged,reader))
ck('Integrated reader differs only in nine documented status/audit fields',set(reader_delta)==allowed_changes)
source_reader=read(S/'data/paper-reviews/heo2003.json')
source_reader_expected=copy.deepcopy(source_reader)
source_reader_expected['review_scope_label']='Complete supplied main + matched SI review'
ck('Integrated source reader equals public copy apart from generated review-scope label',source_reader_expected==reader and 'review_scope_label' not in source_reader)
ck('Audit status hashes identify passed independent scopes',reader['audit_details']['apparatus_audit_sha256']==sha(H/'visuals/apparatus/audit-v1/apparatus-source-audit.json') and reader['audit_details']['product_reflection_audit_sha256']==sha(H/'visuals/products-independent-audit/product-si-source-audit.json') and reader['audit_details']['promotion_audit_sha256']==sha(H/'site-integration-independent-audit/promotion-projection-delta-audit.json'))
ck('Browser and integration true, exact ordered structure and training false',reader['presentation_gates']['browser_render'] is True and reader['presentation_gates']['site_integration'] is True and reader['presentation_gates']['exact_ordered_atomic_structure_binding'] is False and reader['training_eligible'] is False)
items=[i for sec in reader['reader_sections'] for i in sec['items']]
ck('372 items and 535 typed fact attachments retained byte-content equal',len(items)==372 and sum(len(i['facts']) for i in items)==535 and reader['reader_sections']==staged['reader_sections'])
ck('All source documents, conflicts and source/sample associations retained',all(reader[k]==staged[k] for k in ['documents','evidence_conflicts','route_evidence_contexts','route_evidence_scope_notes','source_notes','figures','tables','equations','remaining_gaps']))
ck('All 23 source-page cards retained without public attachments',sum(i['id'].startswith(('asset-heo2003-main-page-','asset-heo2003-si-page-')) for i in items)==23 and all(not i.get('original_assets') for i in items if i['id'].startswith(('asset-heo2003-main-page-','asset-heo2003-si-page-'))))

expected_assets={r['public_path']:r['sha256'] for r in plan['retained_selected_assets']}
actual_assets={p.relative_to(D).as_posix():sha(bind(p)) for p in (D/'assets/figures/heo2003').iterdir() if p.is_file()}
ck('Exactly 16 selected source crops match approved original bytes',len(expected_assets)==16 and actual_assets==expected_assets)
whole_urls={r['proposed_public_path'] for r in plan['binary_exclusions']}
for row in plan['binary_exclusions']:
    rel=row['proposed_public_path']; ck('Whole-page omitted and policy rejects '+row['asset_id'],not(D/rel).exists() and bool(policy.exclude_path('recipe-atlas/dist/'+rel)))
whole_hashes={r['sha256'] for aid,r in source_assets['assets'].items() if aid.startswith(('heo2003-main-page-','heo2003-si-page-'))}
ck('23 whole-page originals identified for renamed-copy check',len(whole_hashes)==23)
image_paths=[p for p in D.rglob('*') if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp')]
renamed_pages=[p.relative_to(D).as_posix() for p in image_paths if sha(p) in whole_hashes]
ck('No byte-identical Heo whole-page image anywhere in authored dist',not renamed_pages)
reader_urls=[x for p,x in walk(reader) if isinstance(x,str) and (x in whole_urls or re.search(r'(?:assets/figures/heo2003/)(?:main|si)-\d+\.png',x))]
ck('No remaining Heo whole-page attachment URL in reader',not reader_urls)
policy_probes={
 'research-assets/incoming-paper-monitor/batches/new-paper/complete-source-payloads.json':True,
 'research-assets/new-paper/private/text/main.json':True,
 'research-assets/new-paper/cache/text/main.json':True,
 'research-assets/new-paper/first-page-text/main.json':True,
 'research-assets/new-paper/main.txt':True,
 'research-assets/new-paper/source.pdf':True,
 'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/jp0219348/reader-assets/si-03-left-top.png':True,
 'recipe-atlas/dist/assets/heo2003/heo2003-reflections.json':False,
 'recipe-atlas/dist/assets/heo2003/heo2003-reflections.tsv':False,
 'recipe-atlas/dist/assets/crystal-references/heo2003-average-position-occupancy.cif':False,
 **{'recipe-atlas/dist/'+p:False for p in expected_assets}}
for rel,wanted in policy_probes.items():ck('Policy local-only vs retained: '+rel,bool(policy.exclude_path(rel))==wanted)
sample={'firstPagePreviewPrivate':'LOCAL SOURCE TEXT','nested':[{'firstPagePreviewPrivate':'LOCAL SI TEXT','source_locator':'SI page 2'}],'typed_measurement':3.14}
filtered,stats=policy.project_bytes('research-assets/test-audit-projection.json',json.dumps(sample).encode())
ck('Embedded private source-preview fields removed without typed evidence loss',json.loads(filtered)=={'nested':[{'source_locator':'SI page 2'}],'typed_measurement':3.14} and stats['private_fields_removed']==2)

public_files=imp['public_files']
for rel,digest in public_files.items():ck('Audited viewer/data transport '+rel,sha(bind(D/rel))==digest)
si=read(D/'assets/heo2003/heo2003-reflections.json')
numeric_cells=[c for row in si['rows'] for c in row['cells'] if c['cell_id'].rsplit('-',1)[-1]!='marker']
ck('1209 reflection rows and exact independently audited JSON/TSV retained',len(si['rows'])==1209 and sha(D/'assets/heo2003/heo2003-reflections.json')=='e622e8a3db322fe4e7bad73add3a164b23c6e1a7b2a092925dda04a276cae830' and sha(D/'assets/heo2003/heo2003-reflections.tsv')=='d72d8ed69e2424fd05f0afc131e789ea4ff408b9c24da728885f98e0870f2600')
ck('Reflection uncertainty counts unchanged',len(numeric_cells)==7254 and sum(c['numeric_value'] is None for c in numeric_cells)==2 and si['counts']['definite_negative_Fobs2']==137 and si['counts']['zero_Fobs2']==1 and si['training_approved'] is False)

heo_files=[p for p in D.rglob('*') if p.is_file() and (any('heo2003' in x or 'heo-2003-' in x or 'jp0219348' in x for x in p.relative_to(D).parts))]
leaks=[]
for p in heo_files:
    bind(p);rel=p.relative_to(D).as_posix()
    if policy.exclude_path('recipe-atlas/dist/'+rel):leaks.append((rel,'excluded_path_present'))
    if p.suffix.lower() in ('.pdf','.doc','.docx','.txt','.zip'):leaks.append((rel,'source_document_type'))
    if p.suffix.lower() in ('.json','.mjs','.html','.tsv'):
        text=p.read_text(encoding='utf-8-sig')
        if re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]',text):leaks.append((rel,'absolute_local_path'))
        if 'complete-source-payloads.json' in text:leaks.append((rel,'raw_source_payload_reference'))
        if 'firstPagePreviewPrivate' in text:leaks.append((rel,'private_source_preview_field'))
        if p.suffix.lower()=='.json':
            obj=json.loads(text)
            for pointer,node in walk(obj):
                if isinstance(node,dict) and any(k in node for k in ['complete_source_payloads','full_text','fullText','extracted_full_text','source_text']):leaks.append((rel,pointer+' raw full-text field'))
ck('Heo authored assets/reader contain no excluded source file, private preview, raw full-text payload or absolute local path',not leaks)
forbidden_files=[p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file() and (p.name=='complete-source-payloads.json' or p.suffix.lower() in ('.pdf','.doc','.docx'))]
ck('No complete-source-payloads JSON or source document binaries anywhere in dist',not forbidden_files)

sys.path.insert(0,str(S/'scripts'))
import dataset_lib, build_atlas
records={p.stem:read(p) for p in sorted((S/'data/records').glob('heo-2003-*.json'))}
ck('10 integrated records and 473 measurements retained',len(records)==10 and sum(len(r['measurements']) for r in records.values())==473)
for rid,r in records.items():
    ck(rid+' proposed/canonical/public bytes identical',sha(bind(O/'records'/(rid+'.json')))==sha(S/'data/records'/(rid+'.json'))==sha(bind(D/'data/records'/(rid+'.json'))))
    ck(rid+' actual schema/semantic validation',not dataset_lib.validate_record(r))
    ck(rid+' empty requests and no task eligibility',r['quality']['requested_tasks']==[] and all(not v['eligible'] for v in dataset_lib.eligibility(r).values()))
route_ids=[rid for rid,r in records.items() if build_atlas.synthesis_route(r)]
ck('Exactly one displayed Heo route independent of training admission',route_ids==['heo-2003-in66-route'] and records[route_ids[0]]['reader_role']=='synthesis_route')
control=copy.deepcopy(records['heo-2003-in66-route']);control.pop('reader_role')
ck('Reader role is the only additional navigation admission',not build_atlas.synthesis_route(control))
base_hashes=read(O/'base-record-hashes.json')
ck('470 pre-existing canonical records retain original bytes',len(base_hashes)==470 and all(sha(S/'data/records'/name)==digest for name,digest in base_hashes.items()))
manifest=read(D/'data/dataset-manifest.json')
heo_manifest=[r for r in manifest['records'] if r['record_id'] in records]
ck('Generated dataset admits zero Heo training tasks',manifest['record_count']==480 and len(heo_manifest)==10 and all(not task['eligible'] for row in heo_manifest for task in row['eligibility'].values()))
for p in sorted((D/'data/exports').glob('*.jsonl')):
    text=bind(p).read_text(encoding='utf-8');ck('No Heo in actual training export '+p.name,not any(rid in text for rid in records))
materials=[]
for p in (D/'data/materials').glob('*.json'):
    d=json.loads(p.read_bytes())
    if any(rid in d.get('record_ids',[]) for rid in records):bind(p);materials.append(d)
ck('Direct and component material hubs reference same single route',len(materials)==2 and all(d['record_ids']==['heo-2003-in66-route'] for d in materials) and sum(not d.get('component_only',False) for d in materials)==1)
material=next(d for d in materials if not d.get('component_only',False))
ck('Main material hub preserves all ten evidence contexts',{x['record_id'] for x in material['evidence_records']}==set(records))
index=read(D/'data/paper-review-index.json');entry=[p for p in index['papers'] if p['id']=='heo2003']
ck('Source navigation reports correct 23-page main/SI scope',len(entry)==1 and entry[0]['pages_read']==23 and set(entry[0]['record_ids'])==set(records) and entry[0]['si_status']=='matched_and_reviewed')
for p in [S/'scripts/build_atlas.py',S/'scripts/build_paper_reviews.py',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',Path(__file__)]:bind(p)
changed=[p for p,h in bound.items() if sha(p)!=h]
ck('All bound files stable across this bounded check',not changed)
failures=[c for c in checks if not c['passed']]
report={
 'schema':'mattersyn.heo_release_consistency_audit/1','at':datetime.now(timezone.utc).isoformat(),
 'author':'/root (integration, projection policy and browser QA); prior source authors as recorded in bound audits',
 'auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta',
 'status':'passed_bounded_local_release_consistency' if not failures else 'findings',
 'scope':'Current authored dist Heo transport, local-only source policy, source-reader status and reader-navigation/training separation. No new scientific or published-delivery approval.',
 'counts':{'checks':len(checks),'failed':len(failures),'records':10,'reader_items':372,'typed_reader_facts':535,'canonical_measurements':473,'selected_crops':16,'whole_page_source_identities_retained':23,'whole_page_images_in_dist':len(renamed_pages),'reflection_rows':1209,'reflection_numeric_positions':7254,'reflection_null_signs':2,'unique_synthesis_routes':len(route_ids),'new_training_tasks':0,'old_records_unchanged':470,'dist_images_compared_for_renamed_Heo_pages':len(image_paths),'Heo_scoped_public_files_inspected':len(heo_files)},
 'reader_status_delta_paths':reader_delta,'generated_reader_delta':'build_paper_reviews adds only review_scope_label=Complete supplied main + matched SI review; the integrated source reader is otherwise identical.',
 'checker_revision_note':'Initial checker assumed source-reader and generated-reader byte identity. The sole difference is the documented generated review_scope_label. checker-draft-1.json preserves that false positive; no author correction was needed.',
 'policy':metadata,'browser_evidence':{'author':'/root','sha256':sha(O/'browser-validation.json'),'status':browser['status'],'at':browser['at'],'independent_browser_reexecution':False},
 'findings':failures,'leak_candidates':leaks,'renamed_whole_pages':renamed_pages,'unexpected_source_document_files':forbidden_files,
 'retained_crop_hashes':actual_assets,'checks':checks,
 'limitations':['This audit does not repeat completed source, numerical-cell, molecular, apparatus or average-structure audits.','Actual browser interaction is root-authored and bound by its saved report; this auditor did not rerun a browser.','No publication, remote deployment, anonymous URL or future policy mutation is approved here.','Policy-wide credential/PII completeness and unrelated source-paper assets are outside this Heo consistency scope.','Reflection raw_text fields are individual audited numeric tokens, deliberately retained; they are not full-page/full-article source text. Source-page identity cards and local locator strings remain as evidence without downloadable page images.'],
 'mutations':'Only release-consistency-audit output files written. Site, source evidence, frozen author packages, shared ledger and release state were not edited.',
 'bound_files':bound}
(A/'release-consistency-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Heo release consistency audit

**{report['status']}** — {len(checks)} checks; {len(failures)} findings.

The authored release retains 10 records, 372 reader items, 535 typed fact attachments, all 473 measurements, 16 byte-exact selected crops and all 1,209 reflection rows. The two signed nulls remain unresolved. The 23 source-page identities remain as evidence cards, with no full-page image attached; no identical Heo full-page image was found elsewhere in dist.

Policy 2026-09-20.2 verifies its pinned exclusion baseline and excludes raw source-document binaries, full-text caches, complete-source-payloads.json and full/tiled source pages. The Heo public files contain no excluded file, raw full-text payload, private preview field or absolute local source path. Individual reflection-cell raw tokens remain intentionally preserved.

The actual route predicate selects only heo-2003-in66-route. The component hub references the same route and creates no second method. All ten requested_tasks arrays remain empty, actual task eligibility is false, and every public training export excludes Heo. All 470 earlier canonical records retain their hashes.

The integrated reader differs from the approved staging copy only in nine audit/status fields. Browser status is true and bound to root's saved actual browser QA; this auditor did not independently run a browser. All checked files remained stable during the check. This is local release consistency, not anonymous published-delivery verification.

No Site, source, frozen package or shared state was edited. Exact bound file hashes and individual checks are in the JSON report.
'''
if failures:md+='\nFindings:\n'+''.join('- '+c['check']+'\n' for c in failures)
(A/'release-consistency-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures,'leaks':leaks,'sha256':sha(A/'release-consistency-audit.json')},ensure_ascii=False))
