"""Freeze completed Sasongko private author work; refuse overwrite."""
from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'package-freeze.json').exists()
ci=read(O/'contact-index.json');val=read(O/'author-validation.json');consumer=read(O/'consumer-checks.json');inp=read(O/'input-bindings.json')
assert ci['panel_count']==23 and all(x['passed'] for x in val['checks']) and all(x['passed'] for x in consumer['checks'])
manual={
 'identity_and_formal_salt':'All 13 reference cards actually viewed; formula, charges, disconnected ions and chemically justified highlights checked. The new formal-salt card reopened at native size.',
 'reference_geometry':'All six exact-array static projections actually viewed; arbitrary projection/computed or NIST reference caveats visible. This is not a browser image review.',
 'stocks':'All four final formulation cards actually viewed; final readable volume-part labels re-viewed on contact 06. Complete FA-stock card reopened at native size. Whole charges and later 0.51 mL injection remain separate.',
 'scoped_unknowns':'Generic hexane, bulk PbI2, FA-oleate and phase/cited-context cards retain explicit missing identity/speciation/geometry scope. No extra hydration or product coordinates.',
 'layout':'No clipped headings, overlapping formula/graph/text or missing caption glyphs observed at reviewed native/contact sizes. Browser/mobile integration remains pending.'}
save('author-visual-review.json',{'schema':'mattersyn-author-static-visual-review/1','author':'/root/peng1998_reader_assets','status':'completed_author_visual_review','independent_approval':False,'browser_review':False,'all_panels_viewed':True,'panel_count':23,'contact_sheets':ci['contacts'],'native_reopened':[{'path':str(O/p),'sha256':sha(O/p)} for p in ['previews/sasongko2025-formamidine-acetate-reference.png','stock-previews/sasongko2025-fa-oleate-stock.png']],'actual_manual_scope':manual})
(O/'author-progress.md').write_text('''# Sasongko molecular author checkpoint — complete private freeze

Authoring is complete and frozen by package-freeze.json. Distinct molecular/binding audit, Site integration, browser review and publication remain pending. All persisted approval/training/publication flags remain false. No source/canonical/Site/ledger files were changed; no downloads or new 3D coordinates.

Completed: 13 identities; 26 material slots; five stock instances / four formulations / 12 component slots; 74 exact quantity references; seven 2D models, six unchanged qualified reference 3D arrays, six symbolic identities; 30 public candidates. All 23 static panels were actually viewed across six contacts, with new formal salt and complete precursor stock reopened at native size.

Checks: build_package.py 75; build_bindings.py 121; validate_package.py 1,217 generated graph/pointer/hash/preview checks; check_consumer.mjs 1,043 actual current consumer checks. Consumer scope: 26 slots, 13 popups, six 3D entries, 12 stock and 12 context transitions, private gate and cross-source exclusion. Minimal DOM/data sink only; no mounted browser claim.

Commands: [local path redacted] -B -X utf8 for Python scripts, with local research-assets/rdkit-runtime and research-assets/corpus-20260917/runtime; [local path redacted] for check_consumer.mjs. Do not rerun writers in this frozen directory. Any correction must preserve this boundary and use a separate overlay.

Integration handoff: effective-file-map.json, effective-public-assets.json, README.md and package-freeze.json. Source v2 and canonical v1 exact inputs and independent source/canonical receipts are in input-bindings.json. The package does not approve product/sample geometry or training.
''','utf8')
bound={str(p):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts}
for key,v in inp.items():
 if isinstance(v,dict) and 'path' in v and 'sha256' in v:assert sha(v['path'])==v['sha256'];bound[v['path']]=v['sha256']
for p,h in inp['canonical_records'].items():assert sha(p)==h;bound[p]=h
for x in read(O/'effective-public-assets.json')['assets']:assert sha(x['path'])==x['sha256']
for x in ci['contacts']:
 assert sha(x['path'])==x['sha256']
 for p in x['panels']:assert sha(p['path'])==p['sha256']
counts={**val['counts'],'model2d':7,'retained3d':6,'symbolic_identities':6,'quantity_references':74,'contact_sheets':6,'bound_files':len(bound)}
out={'schema':'mattersyn-private-molecular-package/1','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_id':'sasongko2025','doi':'10.1021/acs.jpcc.5c05144','status':'frozen_author_proposal_pending_distinct_molecular_audit','source_generation':1,'source_revision':2,'source_freeze_sha256':inp['source_freeze']['sha256'],'source_audit_sha256':inp['source_audit']['sha256'],'canonical_revision':1,'canonical_package_sha256':inp['canonical_freeze']['sha256'],'canonical_audit_sha256':inp['canonical_audit']['sha256'],'counts':counts,'validation_counts':{n:read(O/n)['check_count'] for n in ['generation-checks.json','binding-author-checks.json','author-validation.json','consumer-checks.json']},'scope':['Source-qualified references for all material and stock component slots.','Source stock charges, aliquot and complete paired alternatives remain separate.','Six unchanged reference arrays; zero new 3D or product atom models.','No product/sample bindings or unqualified solution species.','Author static and consumer checks only; independent visual, integrated browser and publication gates pending.'],'cached_input_policy':'Reference snapshots are immutable inputs. Historical original shared-registry paths are provenance only and are not dependencies on later shared edits.','public_projection':'Only the 30 assets in effective-public-assets.json are public candidates; no original documents/pages or private reference snapshots.','independent_approval':False,'browser_approval':False,'training_approval':False,'bound_files':bound}
save('package-freeze.json',out)
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':counts,'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'stock_map_sha256':sha(O/'stock-component-map.json')}))
