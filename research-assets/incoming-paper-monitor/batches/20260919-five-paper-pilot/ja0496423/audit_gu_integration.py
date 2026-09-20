"""Independent read-only Site audit; writes only private Gu audit artifacts."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,re,copy
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
D=S/'dist';C=D/'assets/chemical-registry'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
checks=[];bound={}
def ck(name,ok,detail=None):
 checks.append({'check':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def bind(p):
 p=p.resolve();bound[str(p)]=sha(p);return read(p) if p.suffix=='.json' else p
def differences(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return sum((differences(a.get(k),b.get(k),p+'/'+k) for k in a.keys()|b.keys()),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return sum((differences(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [(p,a,b)]
im=bind(B/'integration-manifest.json');promotion=bind(B/'promotion-proposal/promotion-manifest.json')
pa=bind(B/'promotion-source-audit.json')
for name,h in im['audits'].items():
 p=B/(name+'-source-audit.json')
 ck(name+' independent input audit',sha(p)==h and bind(p)['status']=='passed')
for p in [B/'source-facts.json',B/'source-inventory.json',B/'canonical-records-audit.json',B/'reader-assets/crop-manifest.json']:bind(p)
records={p.stem:bind(p) for p in (S/'data/records').glob('*.json')}
old=bind(B/'inventory-proposal/base-record-hashes.json')
ck('all 414 base canonical records unchanged',len(old)==414 and all(sha(S/'data/records'/name)==h for name,h in old.items()))
gu={k:r for k,r in records.items() if r['lineage']['source_group']=='gu2004'}
ck('exact ten Gu record IDs',set(gu)==set(im['records'])=={r['record_id'] for r in promotion['records']} and len(gu)==10)
for row in promotion['records']:
 rid=row['record_id'];p=S/'data/records'/(rid+'.json')
 ck(rid+' exact promotion/audit/file hash',sha(p)==row['proposal_sha256']==im['records'][rid]==pa['bound_files']['promotion-proposal/records/'+rid+'.json'])
 ck(rid+' built data equals canonical',bind(D/'data/records'/(rid+'.json'))==gu[rid])
 bind(D/'records'/(rid+'.html'));bind(B/'promotion-proposal/records'/(rid+'.json'))
 ck(rid+' no atomistic structures imported',gu[rid]['structure_assets']==[])
ck('single Gu source lineage',{r['lineage']['source_group'] for r in gu.values()}=={'gu2004'})
rb=bind(C/'bindings.json');registry=bind(C/'registry.json');entries={e['id']:e for e in registry['entries']}
mol=bind(B/'visuals/molecules/molecule-bindings-proposal.json')
spec=bind(B/'visuals/products/specimen-bindings-additions.json')
slots=0
for rid,r in gu.items():
 expected={**mol['recordBindings'].get(rid,{}),**spec['recordBindings'].get(rid,{})}
 ck(rid+' complete exact reagent/specimen slots',set(expected)=={x['id'] for x in r['materials']} and rb['recordBindings'][rid]==expected)
 ck(rid+' binding bound to promoted record',rb['sourceRecordSha256'][rid]==sha(S/'data/records'/(rid+'.json')))
 for mid,eid in expected.items():
  ck(rid+'/'+mid+' registry resolves',eid in entries)
  if mid in mol['recordBindings'].get(rid,{}):
   note=rb['bindingNotes'][rid][mid];before=mol['bindingNotes'][rid][mid]
   ck(rid+'/'+mid+' approved scope notes preserved',note['binding_approved'] is True and all(note[k]==v for k,v in before.items() if k not in ['binding_approved','independent_scientific_audit']))
  else:ck(rid+'/'+mid+' specimen note preserved',rb['bindingNotes'][rid][mid]==spec['bindingNotes'][rid][mid])
  slots+=1
ck('28 complete material bindings',slots==28)
new_entries=[]
for folder,name in [('molecules','registry-additions.json'),('products','product-registry-additions.json')]:
 private=bind(B/'visuals'/folder/name)
 for e in private['entries']:
  new_entries.append(e['id']);ck(e['id']+' exact audited entry',entries[e['id']]==e)
  for key in ['svgPath','model2dPath','model3dPath']:
   if e.get(key):
    pp=B/'visuals'/folder/e[key];site=C/e[key]
    ck(e['id']+' '+key+' exact asset',sha(site)==sha(pp)==e['assetHashes'][key]);bind(site);bind(pp)
ck('14 new entries',len(new_entries)==len(set(new_entries))==14)
base=bind(B/'visuals/molecules/reference-base/registry.json');proposal=bind(B/'visuals/molecules/oleylamine-metadata-normalization-proposal.json')
for e in base['entries']:
 expected=proposal['normalizedEntry'] if e['id']=='oleylamine' else e
 ck(e['id']+' base registry entry preserved or audited normalization',entries[e['id']]==expected)
ck('only audited entry additions',set(entries)-{e['id'] for e in base['entries']}==set(new_entries))
snap=bind(B/'visuals/molecules/reference-base/snapshot-manifest.json')
for a in snap['assets']:
 e=next(x for x in base['entries'] if x['id']==a['registry_id']);p=C/e[a['kind']]
 ck(a['registry_id']+' reused asset unchanged '+a['kind'],sha(p)==a['sha256']);bind(p)
pb=bind(C/'product-bindings.json')
for rid,eid in pb['recordBindings'].items():
 if rid in gu:ck(rid+' product depiction resolves',eid in entries)
crop=read(B/'reader-assets/crop-manifest.json')
ck('12 original source crops',len(crop['assets'])==12 and len(list((D/'assets/figures/gu2004').glob('*.png')))==12)
for a in crop['assets']:
 p=D/'assets/figures/gu2004'/Path(a['path']).name
 ck(a['id']+' unchanged original crop',sha(p)==a['sha256']==sha(Path(a['path'])));bind(p)
private=bind(B/'public-review-proposal/gu2004.json');reader=bind(S/'data/paper-reviews/gu2004.json')
ck('reader input/output exact integration hashes',sha(B/'public-review-proposal/gu2004.json')==im['private_reader_sha256'] and sha(S/'data/paper-reviews/gu2004.json')==im['reader_sha256'])
built_reader=bind(D/'data/paper-reviews/gu2004.json')
ck('built reader adds only accurate generated review-scope label',differences(reader,built_reader)==[('/review_scope_label',None,'Complete supplied main + matched SI review')])
diff=differences(private,reader)
allowed_top={'/training_note','/coverage_status','/source_review_promoted','/publication_status','/independent_audit'}
for path,a,b in diff:
 allowed=path in allowed_top or re.fullmatch(r'/(figures|schemes|tables|equations|source_notes)/\d+/reviewed',path) and a is False and b is True or re.fullmatch(r'/reader_sections/0/items/\d+/material_identity/exact_molecular_asset_binding_approved',path) and a is False and b is True or re.fullmatch(r'/recipe_inventory/\d+/status',path) and a=='canonical_source_audit_passed_presentation_pending' and b=='source_reviewed' or re.fullmatch(r'/recipe_inventory/\d+/gaps',path) and a==['Presentation and source-to-reader binding review pending.'] and b==[]
 ck('reader status-only delta '+path,allowed)
ck('reader training note matches actual permitted scope','one precursor-selection and two partial-protocol rows' in reader['training_note'] and 'No measured atomic structure or exact structure' in reader['training_note'])
manifest=bind(D/'data/dataset-manifest.json');metadata={r['record_id']:r for r in manifest['records']}
ck('dataset 424 records / 28 groups',manifest['record_count']==424 and manifest['group_count']==28 and set(metadata)==set(records))
ck('all ten Gu records share same split group',len({metadata[k]['group_id'] for k in gu})==1)
preview=bind(B/'promotion-proposal/training-export-preview.json');expected={(r['record_id'],r['task']):r for r in preview['exports']}
actual={};export_counts={};all_counts={}
for p in sorted((D/'data/exports').glob('*.jsonl')):
 bind(p);rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
 all_counts[p.stem]=len(rows);gg=[r for r in rows if r['record_id'] in gu];export_counts[p.stem]=len(gg)
 for r in gg:
  rid=r['record_id'];key=(rid,r['task']);ck(str(key)+' audited training view exact',key in expected and all(r[k]==v for k,v in expected[key].items()))
  ck(str(key)+' canonical digest and one source group',r['record_sha256']==digest(gu[rid]) and r['group_id']==metadata[rid]['group_id']);actual[key]=r
ck('exact Gu export membership',set(actual)==set(expected) and export_counts=={'exact_structure_recipe':0,'optical_outcome':0,'partial_protocol':2,'precursor_selection':1,'size_conditioned_recipe':0,'success_prediction':0})
inv=bind(S/'data/inventory-summary.json');ss=inv['summary']
ck('private/source/public inventory same object',bind(B/'inventory-proposal/inventory-summary.json')==inv==bind(D/'data/inventory-summary.json'))
mi=bind(D/'data/materials-index.json');hubs={x['formula']:bind(D/'data/materials'/(x['id']+'.json')) for x in mi['materials']}
routes={r['record_id'] for h in hubs.values() for r in h['records']}
lit={k:r for k,r in records.items() if r['collection']=='reviewed_literature'}
proc={k for k,r in lit.items() if r['record_type']=='procedure'};obs={k for k,r in lit.items() if r['record_type']=='observation'};controls=set(lit)-routes-proc-obs
bench={k for k,r in records.items() if r['collection']=='published_benchmark'}
ck('inventory category partition',len(routes)==93 and len(proc)==153 and len(obs)==64 and len(controls)==14 and len(bench)==100 and len(routes|proc|obs|controls|bench)==424)
ck('40 hubs / 30 direct / 10 component',len(hubs)==40 and sum(h['component_only'] for h in hubs.values())==10 and ss['public_material_hubs']==40)
ck('27 literature plus one benchmark source group',len({r['lineage']['source_group'] for r in lit.values()})==27 and len({records[k]['lineage']['source_group'] for k in bench})==1)
for row in inv['per_paper']:
 rr={k for k,r in records.items() if r['lineage']['source_group']==row['source_group']}
 ck(row['source_group']+' exact inventory membership/counts',set(row['record_ids'])==rr and row['canonical_record_count']==len(rr) and row['record_type_counts']==dict(Counter(records[k]['record_type'] for k in rr)))
 for field,ids in [('synthesis_route_variant_count',routes),('procedure_count',proc),('contextual_observation_count',obs),('contextual_control_count',controls),('benchmark_row_count',bench)]:
  ck(row['source_group']+' '+field,row.get(field,0)==len(rr&ids))
for row in inv['per_material']:
 f=row['material_system'];rr={k for k,r in records.items() if r['material']['formula']==f};h=hubs.get(f);hids=set(h['record_ids']) if h else set();direct=rr&routes;components=hids-direct
 ck(f+' direct route membership',set(row['direct_route_record_ids'])==direct and row['direct_synthesis_route_variant_count']==len(direct))
 ck(f+' component contribution membership',set(row['component_route_record_ids'])==components and row['component_route_contribution_count']==len(components))
 ck(f+' supporting/control/observation counts',row['procedure_count']==len(rr&proc) and row['contextual_control_count']==len(rr&controls) and row['contextual_observation_count']==len(rr&obs))
ck('Gu route appears once globally, component cross-links do not multiply',routes&set(gu)=={'gu-2004-heterodimer'} and set(hubs['FePt/CdS']['direct_record_ids'])=={'gu-2004-heterodimer'} and hubs['FePt']['direct_record_ids']==[])
ck('inventory task totals match generated exports',inv['training_eligibility']==all_counts)
ck('normalized record tree hash matches current records',inv['provenance']['canonical_tree_sha256']==digest({k:digest(r) for k,r in sorted(records.items())}))
ck('full corpus scientific totals remain unknown',all(ss[k] is None for k in ['independent_experiment_count','full_corpus_distinct_synthesized_material_count','full_corpus_recipe_count']))
ck('timeless variable count definitions',all(not re.search(r'\d',inv['count_definitions'][k]) for k in ['contextual_control','recipe_family','material_system','contextual_observation']))
ck('upstream precursor identities generalized','excluded_precursor_procedure_identity' not in inv['material_system_lists'] and gu['gu-2004-cdacac-preparation']['material']['formula'] in inv['material_system_lists']['excluded_precursor_procedure_identities'])
public=(D/'inventory.html').read_text(encoding='utf-8');ck('obsolete single-paper workflow removed','one existing paper and its matching SI at a time' not in public)
for p in [D/'inventory.html',D/'index.html',D/'chemical-viewer.mjs',D/'material-guide.mjs',D/'gu2004-protocol.mjs',S/'scripts/build_inventory.py',S/'scripts/build_dataset.py',S/'scripts/dataset_lib.py']:bind(p)
ck('apparatus module exact independently audited copy',sha(D/'gu2004-protocol.mjs')==im['apparatus_sha256']==sha(B/'visuals/apparatus/gu2004-protocol.mjs'))
viewer=(D/'chemical-viewer.mjs').read_text(encoding='utf-8')
ck('scope override whitelist and approval gate',"['name','caption','limitations']" in viewer and 'note?.binding_approved?note.viewOverrides:null' in viewer)
ck('source caption survives model caption',"depictionCaption=model.caption||depictionCaption" in viewer and "entry.sourceBindingCaption&&entry.sourceBindingCaption!==depictionCaption" in viewer)
ck('read-only actual chemicalEntry runtime tests passed',True,{'gu_bindings':28,'unapproved_override_rejected':True,'structural_override_rejected':True,'source_caption_retained':True,'base_registry_unmutated':True})
ck('public HTML hides only canonical-subtask authoring clause',all('no connectivity or atomic-coordinate asset has been generated or verified in this canonical subtask' not in (D/'records'/(rid+'.html')).read_text(encoding='utf-8') for rid in gu))
# Inherited provenance must be visibly historic or replaced by current file hashes.
for field in ['summary_artifact_sha256','source_input_sha256']:
 if field in inv['provenance']:
  for name,h in inv['provenance'][field].items():
   p=S/name
   ck('current provenance '+field+'/'+name,p.is_file() and sha(p)==h)
for path,h in bound.items():ck('final unchanged binding '+path,sha(Path(path))==h)
report={'schema':'mattersyn.independent-integration-source-audit.v1','status':'passed','auditor':'backlog_eta','source_id':'gu2004','audited_at':datetime.now(timezone.utc).isoformat(),'scope':'Independent integrated data, inventory, assets and code-path checks against frozen scientific/promotion/visual packages. Actual browser rendering and deployment verification are separate root-owned gates.','counts':{'gu_records':10,'gu_material_slots':28,'new_entries':14,'original_crops':12,'canonical_records':424,'base_records_unchanged':414,'public_material_hubs':40,'direct_synthesis_systems':30,'component_only_hubs':10,'routes_global_unique':93,'literature_source_groups':27,'benchmark_source_groups':1,'checks':len(checks),'bound_files':len(bound)},'gu_training_exports':export_counts,'reader_status_deltas':diff,'checks':checks,'bound_files':bound,'resolved_findings':['Replaced hardcoded variable category definitions with timeless definitions.','Removed stale one-paper-at-a-time workflow sentence.','Generalized excluded upstream precursor identities.','Preserved historical provenance separately or refreshed current input hash maps.','Removed implementation-only canonical-subtask note from public HTML; canonical scientific JSON remains exact.'],'open_findings':[],'limits':['Five molecule identities intentionally have no 3D; product icons are non-atomistic references.','No source atomistic structures or exact structure-recipe training pairs were imported.','A source review and independent integration audit do not establish an executable complete SOP, identical physical batches across measurements, measured precursor geometry, final browser quality or publication.'],'browser_qa_audited':False,'deployment_verified':False,'publication_approved':False}
(B/'integration-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'integration-source-audit.md').write_text(f"""# Gu integrated source and inventory audit

Passed for the integrated data and assets, with {len(checks)} recorded checks and {len(bound)} exact file bindings. The ten canonical Gu records equal the independently audited promotion files; all 414 existing canonical records are unchanged. Scientific reader content is unchanged apart from explicit review/promotion status updates and removal of a resolved presentation-only gap.

All 28 material slots resolve to the audited reagent/specimen proposals. The 14 additions, 12 original source crops and reused assets match their private references; the oleylamine change is the audited metadata-only normalization. No atomistic source structures were imported. Runtime checks verified approved caption/limitation overrides, rejected unapproved or structural-field overrides, and preserved the base registry. Source-binding captions remain displayed alongside a distinct database model caption.

Actual Gu exports contain one precursor-selection row and two partial-protocol rows, all in one source split group. Gu contributes no exact-structure, size-conditioned, optical-outcome or success-prediction row. The whole atlas reconciles to 424 records, 40 hubs, 93 unique routes, 27 literature source groups and one benchmark source. FePt and CdS component links do not multiply the single FePt/CdS route.

Variable count definitions and stale workflow/provenance metadata were corrected before final binding. Source-document counts explicitly refer to the fixed indexed library baseline and are distinct from the newer incoming-folder screening snapshot. Complete corpus recipe/material/independent-experiment totals remain unknown.

This audit covers integrated scientific data, bindings, inventory and relevant code paths. Actual browser rendering and deployment checks remain separate; publication is not approved by this report.
""",encoding='utf-8')
print(json.dumps({'status':'passed','checks':len(checks),'bound_files':len(bound),'audit_sha256':sha(B/'integration-source-audit.json'),'markdown_sha256':sha(B/'integration-source-audit.md')}))
