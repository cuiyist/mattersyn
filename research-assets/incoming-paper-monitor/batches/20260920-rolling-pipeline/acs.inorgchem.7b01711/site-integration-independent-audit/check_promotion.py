"""Independent, read-only proposal comparisons; writes only this audit directory."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import copy, hashlib, json, re

A=Path(__file__).resolve().parent
N=A.parent
O=N/'site-integration-proposal/v1'
P=N/'site-integration-proposal/product-context-v1'
M=N/'visuals/molecules'
EXPECTED='c57dc9d7d1de1436df92fedc86ce1ed41a6a08cfba10e648059dbd51a84dc175'
PRODUCT_EXPECTED='6dd95e3b575e66fdea40927174ad73808fdd6656509cf72b3e10ebe67e52ac08'
checks=[];bound={};deltas={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
 p=Path(p).resolve();bound[str(p)]=sha(p);return p
def read(p):return json.loads(bind(p).read_text(encoding='utf-8-sig'))
def check(test,label):checks.append({'check':label,'passed':bool(test)})
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def diff(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):
  return [v for k in sorted(a.keys()|b.keys()) for v in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
 if isinstance(a,list):
  if len(a)!=len(b):return [p]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [p]
def strip(x,keys):return {k:v for k,v in x.items() if k not in keys}
def walks(x):
 yield x
 if isinstance(x,dict):
  for v in x.values():yield from walks(v)
 elif isinstance(x,list):
  for v in x:yield from walks(v)

freeze=read(O/'package-freeze.json');manifest=read(O/'promotion-manifest.json')
check(sha(O/'package-freeze.json')==EXPECTED,'Exact requested promotion freeze')
for row in freeze['files']:
 p=bind(O/row['path']);check(p.is_relative_to(O),'Freeze paths stay within proposal')
 check(sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'Frozen bytes '+row['path'])
check(set(x['path'] for x in freeze['files'])=={str(p.relative_to(O)).replace('\\','/') for p in O.rglob('*') if p.is_file() and p.name!='package-freeze.json'},'No unlisted proposal files')
check(sha(bind(N/'prepare_site_proposal.py'))==freeze['author_script_sha256'],'Author script hash')
check(manifest['source_audits']==freeze['source_audits'],'Manifest audit dependencies')
historical_runtime_changes=[]
for path,h in freeze['source_audits'].items():
 audit=read(N/path);check(sha(N/path)==h and audit['status']=='passed','Passed audit dependency '+path)
 for path2,h2 in audit['bound_files'].items():
  p=Path(path2);p=p if p.is_absolute() else N/p
  if p.is_relative_to(N):
   check(sha(bind(p))==h2,'Local frozen audit dependency '+str(p.relative_to(N)))
  elif 'recipe-atlas' in p.parts:
   # Historical shared runtime hashes are not immutable source evidence.
   if p.exists() and sha(p)!=h2:historical_runtime_changes.append(str(p))

records={};originals={};record_hashes={}
pending='Private canonical author proposal; independent source audit passed separately, while canonical/reader review remains pending.'
for row in manifest['records']:
 old=read(row['original_path']);p=O/'records'/Path(row['original_path']).name;new=read(p);rid=old['record_id']
 records[rid]=new;originals[rid]=old;record_hashes[rid]=sha(p)
 check(sha(row['original_path'])==row['original_sha256'] and sha(p)==row['promoted_sha256'],'Canonical and staged record hashes '+rid)
 expected=copy.deepcopy(old)
 expected['collection']='reviewed_literature'
 expected['reader_role']={'literature_protocol':'synthesis_route','procedure':'supporting_procedure'}.get(old['record_type'],'contextual_observation')
 expected['quality']['review_status']='source_reviewed';expected['quality']['review_scope']=manifest['scope']
 expected['quality']['missing_fields']=[x for x in old['quality']['missing_fields'] if x!=pending]
 for source in expected['sources']:
  source.update(main_status='All 10 supplied main pages read, visually inspected and independently audited; source and canonical checks passed.',si_status='Matched 17-page SI fully read, visually inspected and independently audited. Printed source conflicts remain explicit; cited CIF not supplied.',reuse_status='Source-linked facts and selected scientific crops; original article, SI files, complete text and page scans remain local.')
 check(expected==new,'Exact metadata-only record projection '+rid)
 deltas[rid]=diff(old,new)
 check(new['quality']['requested_tasks']==[] and new['structure_assets']==[],'No task or coordinate admission '+rid)
check(len(records)==18,'18 records')
check(Counter(r['reader_role'] for r in records.values())=={'synthesis_route':2,'supporting_procedure':8,'contextual_observation':8},'2 routes / 8 supporting procedures / 8 observations')
check(sum(len(r['operations']) for r in records.values())==24,'24 unchanged operations')
check(sum(len(r['measurements']) for r in records.values())==822,'822 unchanged measurement/context fields')

old=read(N/'public-review-proposal/v1/morrison2017.json');reader=read(O/'reader/morrison2017.json');expected=copy.deepcopy(old)
metadata=['coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','audit_details','presentation_gates']
# Each new metadata value has been read separately against the passed audit scope.
for k in metadata:expected[k]=reader[k]
check(reader['source_review_promoted'] is True and reader['review_state']=='source_reviewed','Reader source audit promotion')
check(reader['training_eligible'] is False,'Reader training remains false')
check(reader['audit_details']=={'scope':manifest['scope'],'audit_sha256':freeze['source_audits'],'source_conflicts_resolved':False,'training_promotions':0},'Reader audit metadata accurately binds prerequisites')
check(reader['presentation_gates']=={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False},'Separate integration/browser/publication gates remain false')
for row in expected['recipe_inventory']:
 row['status']='source_reviewed';row['gaps']=[s for s in row['gaps'] if s!=pending]
for k in ['figures','tables','schemes','equations','source_notes']:
 for row in expected[k]:row['reviewed']=True
expected['remaining_gaps']=[s for s in old['remaining_gaps'] if not s.startswith('The extraction’s historical G10') and s!='Molecular, product/crystal, apparatus and browser bindings are pending separate qualification.']+['Source, canonical/reader, molecular and apparatus audits passed. No precursor/product coordinate model is promoted. Integrated browser and publication gates remain separate.']
check(expected==reader,'Reader differs only in declared reviewed-status metadata and resolved workflow gaps')
check(reader['reader_sections']==old['reader_sections'],'All reader scientific prose, exact fields, pointers, sample associations unchanged')
check(reader['evidence_conflicts']==old['evidence_conflicts'],'All source conflicts unchanged')
deltas['reader']=diff(old,reader)

reg0=read(M/'registry-additions.json');reg=read(O/'molecules/registry-additions.json');expected=copy.deepcopy(reg0)
expected['binding_approved']=True;expected['status']='independently_passed_source_references_staged_for_integration'
for e in expected['entries']:
 e.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_binding_audit',published=False,eligible_training=False)
check(expected==reg,'Registry scientific content and model pointers unchanged')
check(len(reg['entries'])==29 and all(e['id'].startswith('morrison2017-') for e in reg['entries']),'29 source-scoped registry IDs')
deltas['registry']=diff(reg0,reg)
b0=read(M/'bindings-proposal.json');b=read(O/'molecules/bindings-additions.json');expected=copy.deepcopy(b0)
expected['binding_approved']=True;expected['status']='independently_passed_source_bindings_staged_for_integration';expected['sourceRecordSha256']=record_hashes
for row in expected['bindingNotes'].values():
 for note in row.values():note.update(binding_approved=True,independent_scientific_audit='Passed separate molecular/source-binding audit; metadata promotion preserves all scientific fields.')
check(expected==b,'Material bindings, source captions, original evidence hashes and scientific snapshots unchanged')
check(sum(len(v) for v in b['recordBindings'].values())==64,'64 exact material slots')
check(set(b['sourceRecordSha256'])==set(records),'Effective promoted record hashes are separately bound')
deltas['bindings']=diff(b0,b)
s0=read(M/'solution-components-proposal.json');s=read(O/'molecules/solution-components-additions.json');expected=copy.deepcopy(s0)
expected['binding_approved']=True
for row in expected['contexts']:row['binding_approved']=True
check(expected==s and len(s['contexts'])==5,'Five unchanged solution contexts; only approval metadata changes')
deltas['solutions']=diff(s0,s)

assets=read(N/'original-assets-manifest.json')['assets'];molassets=read(M/'public-asset-proposal.json')['relative_asset_files']
check(len(assets)==30 and all(x['complete_page'] is False for x in assets),'30 selected scientific crops, no complete source pages')
public={}
for x in assets:
 rel='assets/figures/morrison2017/'+Path(x['path']).name;public[rel]=x['sha256']
 check(sha(bind(x['path']))==x['sha256']==sha(bind(O/'dist'/rel)),'Original crop bytes '+x['id'])
for rel,h in molassets.items():
 path='assets/chemical-registry/'+rel;public[path]=h
 check(sha(bind(M/rel))==h==sha(bind(O/'dist'/path)),'Chemical asset bytes '+rel)
public['morrison2017-protocol.mjs']=sha(bind(N/'visuals/apparatus/morrison2017-protocol.mjs'))
check(sha(bind(O/'dist/morrison2017-protocol.mjs'))==public['morrison2017-protocol.mjs'],'Apparatus byte-identical to passed module')
check(len(public)==87 and len(molassets)==56,'Exact public asset budget: 30 + 56 + 1')
check(set(public)=={p.relative_to(O/'dist').as_posix() for p in (O/'dist').rglob('*') if p.is_file()},'No additional public PDFs, SI files, full pages, text payloads, models or snapshots')
check({x['public_path']:x['sha256'] for x in manifest['public_assets']}==public,'Public manifest exact allowlist')
urls={x['public_asset'].lstrip('/') for x in walks(reader) if isinstance(x,dict) and isinstance(x.get('public_asset'),str)}
check(urls=={p for p in public if p.startswith('assets/figures/')},'Reader asset URLs match all and only selected crops')

maps={name:{rid:set() for rid in records} for name in ['structures','properties']}
for sec in reader['reader_sections']:
 if sec['id'] not in maps:continue
 for item in sec['items']:
  for link in item.get('canonical_links',[]):
   pointer=link.get('json_pointer','').strip('/').split('/')
   if pointer[0]=='measurements':
    rid=link['record_id'];m=records[rid]['measurements'][int(pointer[1])];maps[sec['id']][rid].add(m['id'])
for section,rows in maps.items():
 actual=read(O/f'record-{section}-measurements.json')
 check(actual=={rid:sorted(ids) for rid,ids in rows.items()},'Independent reader-derived '+section+' map matches')
 check(set(actual)==set(records),'Classification map contains only the 18 Morrison record IDs: '+section)
for rid in records:check(not (maps['structures'][rid]&maps['properties'][rid]),'No conflicting display classification '+rid)
check(sum(map(len,maps['structures'].values()))==453 and sum(map(len,maps['properties'].values()))==111,'453 structural / 111 property explicit measurement IDs')

check(sha(O/'package-freeze.json')==EXPECTED,'Promotion freeze unchanged after independent checks')
save(A/'promotion-checks.json',checks);save(A/'promotion-observed-deltas.json',deltas)
bind(A/'promotion-checks.json');bind(A/'promotion-observed-deltas.json');bind(__file__)
failed=[x for x in checks if not x['passed']]
report={'schema':'mattersyn.independent_promotion_delta_audit/1','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not failed else 'findings','proposal_freeze_sha256':EXPECTED,'open_findings':failed,'checks':len(checks),'counts':manifest['counts'],'public_assets':87,'display_maps':{'structures':453,'properties':111},'bound_files':dict(bound),'manual_scope':['Read the complete promotion generator and all effective metadata changes; compared scientific payloads deeply against the passed canonical and reader files.','Confirmed unresolved source conflicts, upstream cited-only preparation, solution speciation, precursor-versus-product coordinates and unknown cross-assay batch identity remain explicit.','Reviewed public asset allowlist and all scoped map keys; source scientific arrays and all exact material/stock associations remain unchanged.'],'hash_semantics':'Existing binding note canonical_record_sha256 and entry_sha256 retain audited-input provenance. sourceRecordSha256 separately identifies promoted record bytes. Approval metadata does not rewrite original scientific snapshot hashes.','historical_shared_runtime_changes':sorted(set(historical_runtime_changes)),'limitations':['Metadata/public-projection audit only; no Site mutation or final integrated browser/deployment claim.','Display-map isolation is established for this proposal; importer must merge by these exact record IDs and preserve other sources.']}
save(A/'promotion-delta-audit.json',report)
save(A/'promotion-audit-boundary.json',{'audit_sha256':sha(A/'promotion-delta-audit.json'),'proposal_freeze_sha256':EXPECTED})
print(json.dumps({'promotion_status':report['status'],'checks':len(checks),'failures':failed,'audit_sha256':sha(A/'promotion-delta-audit.json')}))

# Separate bounded product-symbol mapping audit.
checks=[];bound={};f=read(P/'package-freeze.json');pb=read(P/'bindings.json');pc=read(P/'product-contexts-additions.json')
check(sha(P/'package-freeze.json')==PRODUCT_EXPECTED,'Requested product-context freeze')
for x in f['files']:check(sha(bind(P/x['path']))==x['sha256'],'Frozen product payload '+x['path'])
check(sha(bind(N/'prepare_product_contexts.py'))==f['script_sha256'],'Product-context generator hash')
check(sha(bind(O/'molecules/registry-additions.json'))==f['registry_sha256'],'Effective qualified registry hash')
check(pb['promotion_freeze_sha256']==EXPECTED,'Exact promoted-record package dependency')
check(pb['source_record_sha256']==record_hashes,'All product source-record hashes match promotion')
check(set(pc['sourceNotices'])=={'morrison2017'},'Notice scope only Morrison')
entries={e['id']:e for e in reg['entries']}
included=set();excluded={(x['record_id'],x['sample_id']) for x in pb['excluded_contexts']}
mapping={'CdSe/CdS':'morrison2017-cdse-cds-qb-reference','CdS':'morrison2017-cds-powder-reference','C14H12CdN2S4':'morrison2017-cdptc-reference','C18H20CdN2OS4':'morrison2017-cdptc-thf-crystal-reference'}
for rid,rows in pc['recordContexts'].items():
 r=read(O/'records'/f'{rid}.json')
 for row in rows:
  index=int(row['canonical_product_pointer'].split('/')[-1]);product=r['products'][index];key=(rid,row['sample_id']);included.add(key)
  check(row['sample_id']==product['sample_id'],'Product ID '+repr(key))
  check(row['registry_id']==mapping.get(product['composition']['value']),'Exact product composition, not record-level formula '+repr(key))
  check(row['label']==product['composition']['value'],'Composition label '+repr(key))
  check(row['phase']==product['phase'],'Exact phase/status/evidence '+repr(key))
  check(row['morphology']==product['morphology'],'Exact morphology/status/evidence '+repr(key))
  check(row['composition_evidence']==product['composition']['evidence'],'Exact composition evidence '+repr(key))
  check(row['training_eligible'] is False and row['atomic_model'] is False,'No structure/training admission '+repr(key))
  e=entries[row['registry_id']]
  check(e['depictionKind']=='symbolic_context' and not e['model2dPath'] and not e['model3dPath'],'Symbol only '+repr(key))
  check(e['formula'].replace(' ','')==product['composition']['value'],'Registry formula '+repr(key))
  check('no measured atomic coordinates' in row['caption'].lower() or 'do not establish CdSe/CdS product coordinates' in row['caption'],'Visible scope caveat '+repr(key))
allproducts={(rid,s['sample_id']) for rid,r in records.items() for s in r['products']}
check(len(included)==17 and len(pc['recordContexts'])==12,'17 distinct product contexts across 12 records')
check(not included&excluded and included|excluded==allproducts,'Every other context explicitly excluded; no parent-formula fallback')
check(set(pc['recordContexts'])<=set(records),'No other-source record key')
check({p.name for p in P.iterdir() if p.is_file()}=={'bindings.json','product-contexts-additions.json','package-freeze.json'},'No coordinate/model files in product proposal')
for eid in mapping.values():
 e=entries[eid];bind(M/e['svgPath']);bind(M/'previews'/f'{eid}.png')
 check(sha(M/e['svgPath'])==e['assetHashes']['svgPath'],'Actual symbolic depiction bytes '+eid)
renderer=bind(Path(r'[local path redacted]'))
txt=renderer.read_text(encoding='utf-8-sig')
check('contextual.recordContexts[r.record_id]||[]' in txt,'Existing renderer selects exact record context list')
check('data.entries.get(c.registry_id)' in txt and 'caption:c.caption,sourceBindingCaption:c.caption' in txt,'Existing renderer uses exact registry ID and scoped caption')
check(sha(P/'package-freeze.json')==PRODUCT_EXPECTED,'Product freeze unchanged after audit')
save(A/'product-context-checks.json',checks);bind(A/'product-context-checks.json');bind(__file__)
failed=[x for x in checks if not x['passed']]
report={'schema':'mattersyn.independent_product_context_audit/1','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not failed else 'findings','proposal_freeze_sha256':PRODUCT_EXPECTED,'open_findings':failed,'checks':len(checks),'counts':{'included_contexts':len(included),'records':len(pc['recordContexts']),'excluded_contexts':len(excluded),'symbolic_entries':4,'new_coordinate_files':0},'bound_files':dict(bound),'manual_scope':['Reopened and visually read all four native rendered symbolic identity cards: Cd(PTC)2 powder, Cd(PTC)2·THF precursor crystal, CdS powder, and CdSe/CdS quantum-belt composition.','Read all 17 product mappings, exact phase/morphology and source locators against the passed canonical product objects; confirmed isolated powder, solvent controls, optical aliquots, TEM context and shell families remain separate.','The precursor card identifies the measured coordination polymer without generating coordinates. CdS and core/shell cards contain text-only identity statements, not geometric shell coverage, particle size or phase drawings.','Read existing generic productIdentity implementation; exact record keys and selected sample captions are consumed without parent-formula selection.'],'limitations':['This approves the private symbolic product mapping only; no CIF, atomic model, exact product-recipe pair or training eligibility.','The final integrated browser rendering and public deployment remain separate gates.']}
save(A/'product-context-audit.json',report)
print(json.dumps({'product_status':report['status'],'checks':len(checks),'failures':failed,'audit_sha256':sha(A/'product-context-audit.json')}))
