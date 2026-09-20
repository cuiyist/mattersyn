"""Independent exact sample-to-symbol audit, private outputs only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
A=Path(__file__).resolve().parent;G=A.parent;P=G/'site-integration-proposal/v1';O=G/'site-integration-proposal/product-context-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks=[];bound={}
def bind(p):
 p=Path(p);bound[str(p)]=sha(p);return read(p) if p.suffix=='.json' else p
def same(a,b,label):
 checks.append({'passed':a==b,'check':label})
 if a!=b:print('FAILED '+label)
def check(ok,label):same(bool(ok),True,label)
f=bind(O/'package-freeze.json');same(sha(O/'package-freeze.json'),'497ce2ecce876e0b15abcff47da21474ecad83f93fcccb800554366186fac4db','exact product freeze')
same(f['author'],'/root','distinct author')
for row in f['files']:bind(O/row['path']);same(sha(O/row['path']),row['sha256'],'frozen product file '+row['path'])
bind(G/'prepare_product_contexts.py');same(sha(G/'prepare_product_contexts.py'),f['script_sha256'],'frozen author script')
binding=bind(O/'bindings.json');contexts=bind(O/'product-contexts-additions.json')
same(binding['promotion_freeze_sha256'],sha(P/'package-freeze.json'),'exact promotion dependency')
promotion=bind(A/'promotion-delta-audit.json');same(promotion['status'],'passed','promotion independently passed');same(promotion['proposal_freeze_sha256'],sha(P/'package-freeze.json'),'passed promotion exact freeze')
reg=bind(P/'molecules/registry-additions.json');same(sha(P/'molecules/registry-additions.json'),f['registry_sha256'],'frozen registry dependency');registry={e['id']:e for e in reg['entries']}
rm=bind(G/'canonical-proposal/v2/record-manifest.json');records={};old={}
for row in rm['records']:
 rid=row['record_id'];old[rid]=bind(row['path']);same(sha(row['path']),row['sha256'],'audited canonical bytes '+rid);records[rid]=bind(P/'records'/(rid+'.json'))
 same(records[rid]['products'],old[rid]['products'],'all canonical products unchanged '+rid);same(binding['source_record_sha256'][rid],sha(P/'records'/(rid+'.json')),'promoted product hash '+rid)
same(set(binding['source_record_sha256']),set(records),'record hash set exact')
expected={
 'anneal-series':{f'anneal-row-{i}' for i in range(1,6)},
 'constant-s-variant':{'constant-s'},'core-large-variant':{'core-5p5'},'core-only-control':{'core-only-7nm'},
 'core-small-variant':{'core-2p2'},'core-standard-route':{'core-3-or-4'},'optimized-shell-route':{'optimized-shell'},
 'photophysical-results':{'optimized-performance','four-core-series','si-large-core-example','si-blinking-examples'}|{f'lifetime-row-{i:02}' for i in range(1,19)},
 'single-dot-procedure':{'si-blinking-examples'},
 'solvent-ligand-series':{'ode-primary','od-primary','od-late-dilution','od-extreme-dilution','od-secondary','od-no-added-amine','od-long-anneal'},
 'stoichiometry-series':{'withdraw-10','withdraw-1','withdraw-1-oa','constant-s'},
}
expected={'ghosh-2012-'+k:v for k,v in expected.items()}
same(set(contexts['recordContexts']),set(expected),'exact eleven record dispatches')
mapped=set();manual=[]
for rid,rows in contexts['recordContexts'].items():
 same({x['sample_id'] for x in rows},expected[rid],'explicit allowed sample set '+rid);same(len(rows),len(expected[rid]),'no duplicate sample entry '+rid)
 for row in rows:
  sid=row['sample_id'];mapped.add((rid,sid));idx=int(row['canonical_product_pointer'].split('/')[-1]);product=records[rid]['products'][idx]
  same(product['sample_id'],sid,'exact product pointer '+rid+' '+sid)
  formula='CdSe' if sid in ('core-3-or-4','core-2p2','core-5p5','core-only-7nm') else 'CdSe/CdS'
  eid='ghosh2012-cdse-core-reference' if formula=='CdSe' else 'ghosh2012-cdse-cds-reference';e=registry[row['registry_id']]
  same(product['composition']['value'],formula,'explicit canonical composition '+rid+' '+sid);same(row['registry_id'],eid,'correct source symbol '+sid);same(e['formula'],formula,'registry composition '+sid)
  same(row['phase'],product['phase'],'exact phase status/evidence '+rid+' '+sid);same(row['morphology'],product['morphology'],'exact morphology status/evidence '+rid+' '+sid);same(row['composition_evidence'],product['composition']['evidence'],'exact composition evidence '+rid+' '+sid)
  check(bool(row['composition_evidence']),'nonempty source locator '+sid)
  same(e['depictionKind'],'symbolic_context','symbol only '+sid);same(e.get('model2dPath'),None,'no molecular graph '+sid);same(e.get('model3dPath'),None,'no 3D structure '+sid)
  same(row['atomic_model'],False,'no atomic model '+sid);same(row['training_eligible'],False,'no training '+sid)
  check('Symbolic material identity only' in row['caption'] and 'no atomic coordinates' in row['caption'] and 'specimen equivalence' in row['caption'],'explicit interpretive limits '+sid)
  same(row['caption'].split('. Symbolic')[0],row['label'],'caption uses exact sample label '+sid)
  manual.append({'record_id':rid,'sample_id':sid,'label':row['label'],'composition':formula,'phase':row['phase']['value'],'morphology':row['morphology']['value'],'recipe_link':product['recipe_link']})
  if sid.startswith('lifetime-row-'):check('SI lifetime table row '+str(int(sid.rsplit('-',1)[1])) in row['label'],'literal lifetime row label '+sid)
  if sid.startswith('anneal-row-'):check('annealing table row '+sid.rsplit('-',1)[1] in row['label'],'literal anneal row label '+sid)
all_products={(rid,p['sample_id']) for rid,r in records.items() for p in r['products']}
excluded={(x['record_id'],x['sample_id']) for x in binding['excluded_contexts']}
same(len(excluded),len(binding['excluded_contexts']),'unique explicit exclusions');same(mapped&excluded,set(),'no mapped/excluded overlap');same(mapped|excluded,all_products,'every product has exact mapped or excluded disposition')
same(len(mapped),45,'45 scoped contexts');same(len(contexts['recordContexts']),11,'11 records');same(len(excluded),44,'44 excluded contexts')
same(set(contexts['sourceNotices']),{'ghosh2012'},'source notice cannot affect other sources')
check('No exact structure–recipe pair or DFT-ready input is inferred' in contexts['sourceNotices']['ghosh2012'],'source notice prevents exact structure/training claim')
same(binding['no_coordinate_files_added'],True,'no coordinate files added')
for eid in ('ghosh2012-cdse-core-reference','ghosh2012-cdse-cds-reference'):
 e=registry[eid];p=P/'dist/assets/chemical-registry'/e['svgPath'];bind(p);same(sha(p),e['assetHashes']['svgPath'],'qualified exact SVG '+eid)
 preview=G/'visuals/molecules/previews'/(eid+'.png');bind(preview)
 text=p.read_text(encoding='utf8');check('no inferred crystal or surface geometry' in text,'SVG explicit no geometry '+eid)
bind(G/'visuals/molecules-independent-audit/independent-audit.json');bind(G/'canonical-reader-independent-audit/independent-audit-v2.json');bind(Path(__file__))
findings=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-independent-product-context-audit/1','author':'/root','auditor':'/root/peng1998_reader_assets','source_id':'ghosh2012','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not findings else 'open_findings','proposal_freeze_sha256':sha(O/'package-freeze.json'),'check_count':len(checks),'open_findings':findings,'counts':{'records':11,'symbolic_contexts':45,'excluded_contexts':44,'original_symbols':2,'new_coordinate_files':0},'actual_manual_scope':['Read complete root mapping script and all 45 labels/captions. Inspected canonical product scopes, distinct core branches, optimized shell family, solvent/ligand/withdrawal controls, five anneal and eighteen lifetime table rows, and SI optical cohorts.','Viewed both original qualified symbol PNGs and inspected exact SVG text. Core card explicitly distinguishes growth branches from the separate 7 nm control; shell card makes no thickness, morphology, phase or surface geometry assignment.','Checked all 44 exclusions including pure oleic acid, FTIR mixtures, generic acquisition contexts, source references, models and unresolved structural comparisons. No formula-only mapping used.','Repeated sample labels on distinct records remain distinct record/sample keys. No cross-technique physical-batch equivalence or new synthetic run is inferred.','Audited existing scientific data transported from canonical v2; did not re-audit all original PDF pages or approve an integrated browser.'],'mapped_scope_review':manual,'bound_files':dict(sorted(bound.items())),'site_changed':False,'integration_approved':False,'browser_approved':False,'publication_approved':False,'atomic_model_approved':False,'training_approved':False}
for name,data in [('product-context-audit.json',out),('product-context-checks.json',{'checks':checks})]:(A/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(A/'product-context-audit.md').write_text(f"# Ghosh symbolic product-context audit\n\nStatus: **{out['status']}**; {len(checks)} independent checks, {len(findings)} open findings. Bound freeze `{out['proposal_freeze_sha256']}`.\n\nAll 45 contexts on 11 exact records map to independently qualified CdSe or CdSe/CdS identity cards. Exact canonical sample IDs, compositions, phase/morphology statements and evidence are retained; all 44 other contexts remain explicitly excluded. Both actual card previews were viewed. Growth branches and the separate 7 nm control are distinguished, and the shell-family card assigns no fixed geometry, phase or layer count.\n\nThe proposal adds no coordinates, specimen equivalence, training task or exact recipe–structure pair. Integration, browser and publication verification remain separate.\n",encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'open_findings':findings,'audit_sha256':sha(A/'product-context-audit.json')}))
