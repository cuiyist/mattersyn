"""Independent read-only source-to-publication projection checks; audit files only."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,copy,re,collections
sys.dont_write_bytecode=True
J=Path(__file__).resolve().parents[1]; M=J.parents[4]; S=M/'recipe-atlas'
P=J/'site-integration-proposal/v1'; O=Path(__file__).resolve().parent
sys.path.insert(0,str(M/'research-assets'))
from sync_github_public import io_path
checks=[];bound={};deltas={}
def sha(p):return hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def bind(p):
 p=Path(p);h=sha(p);bound[str(p.resolve())]=h;return h
def read(p):bind(p);return json.loads(io_path(p).read_text('utf8'))
def ck(name,ok,detail=None):
 checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'before':a,'after':b}]
 if isinstance(a,dict):
  return sum((diff(a[k],b[k],p+'/'+k) if k in a and k in b else [{'path':p+'/'+k,'before':a.get(k,'<absent>'),'after':b.get(k,'<absent>')} ] for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p+'#length','before':len(a),'after':len(b)}]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':p,'before':a,'after':b}]
def walk(x,p=''):
 yield p,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
def ptr(x,p):
 for k in p.lstrip('/').split('/') if p else []:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
freeze=read(P/'package-freeze.json');manifest=read(P/'promotion-manifest.json')
ck('Exact requested proposal freeze',sha(P/'package-freeze.json')=='57e60689cbcdd46a32b42a9c6f739f63dfa32465f49c325d8599b07d3ce6825c')
for f in freeze['files']:
 p=P/f['path'];ck('Frozen proposal hash '+f['path'],bind(p)==f['sha256']);ck('Frozen proposal bytes '+f['path'],io_path(p).stat().st_size==f['bytes'])
ck('Root projection builder hash',bind(J/'prepare_site_proposal.py')==freeze['author_script_sha256'])
ck('Same upstream audit map',manifest['source_audits']==freeze['source_audits'])
for rel,h in freeze['source_audits'].items():
 a=read(J/rel);ck('Passed upstream audit '+rel,a['status']=='passed' and not a.get('open_findings'));ck('Exact upstream audit '+rel,sha(J/rel)==h)
upstream={}
for rel in ['canonical-proposal/v1/package-freeze.json','visuals/molecules/package-freeze.json','visuals/apparatus/package-freeze.json','visuals/products/package-freeze.json']:
 f=read(J/rel);upstream[rel]=sha(J/rel)
 # Verify each package's actual frozen scope; do not execute author scripts.
 for name,h in f.get('bound_files',{}).items():
  p=Path(name);p=p if p.is_absolute() else (J/rel).parent/p
  ck('Upstream package '+rel+' '+name,bind(p)==h)
records={};originals={};roles=collections.Counter()
for row in manifest['records']:
 rid=row['record_id'];p=P/'records'/(rid+'.json');b=read(Path(row['original_path']));a=read(p);records[rid]=a;originals[rid]=b;roles[a['reader_role']]+=1
 ck('Original record hash '+rid,sha(Path(row['original_path']))==row['original_sha256']);ck('Promoted record hash '+rid,sha(p)==row['promoted_sha256'])
 d=diff(b,a);deltas[rid]=d
 for z in d:
  path=z['path'];ck('Allowed record leaf '+rid+path,path in ['/collection','/reader_role','/quality/review_scope','/quality/review_status'] or re.fullmatch(r'/sources/\d+/(main_status|si_status|reuse_status)',path))
 expected=copy.deepcopy(b);expected['collection']='reviewed_literature';expected['reader_role']=a['reader_role'];expected['quality']['review_status']='source_reviewed';expected['quality']['review_scope']=manifest['scope']
 for i,source in enumerate(expected['sources']):
  for k in ['main_status','si_status','reuse_status']:source[k]=a['sources'][i][k]
 ck('Complete scientific record equality '+rid,a==expected)
 ck('No task or atomic admission '+rid,a['quality']['requested_tasks']==[] and a['structure_assets']==[])
 ck('Role consistent with actual record type '+rid,a['reader_role']==('synthesis_route' if a['record_type'] in ['literature_protocol','protocol_variant'] else 'supporting_procedure' if a['record_type']=='procedure' else 'contextual_observation'))
 for k in ['materials','stocks','condition_options','material_states','operations','products','measurements','structure_assets','intended_target','lineage']:
  ck('Unchanged scientific array '+rid+'/'+k,a[k]==b[k])
ck('19 records and exact 1/7/11 roles',len(records)==19 and roles=={'synthesis_route':1,'supporting_procedure':7,'contextual_observation':11})
ck('21 operations and 502 measurements',sum(len(r['operations']) for r in records.values())==21 and sum(len(r['measurements']) for r in records.values())==502)
old=read(J/'canonical-proposal/v1/reader/sasongko2025.json');reader=read(P/'reader/sasongko2025.json');d=diff(old,reader);deltas['reader']=d
reader_roots={'/audit_details','/coverage_status','/independent_audit','/publication_status','/review_state','/source_review_promoted','/training_note'}
for z in d:ck('Allowed reader leaf '+z['path'],z['path'] in reader_roots or re.fullmatch(r'/(figures|tables|schemes|equations|source_notes)/\d+/reviewed',z['path']) or re.fullmatch(r'/recipe_inventory/\d+/status',z['path']) or z['path'].startswith('/presentation_gates/'))
for key in ['reader_sections','documents','evidence_conflicts','remaining_gaps','characterization_inventory','chemical_intuition','reader_contract','route_evidence_contexts','route_evidence_scope_notes','counts']:
 ck('Reader science complete unchanged '+key,reader[key]==old[key])
ck('Exact known reader section item count',sum(len(s['items']) for s in reader['reader_sections'])==273)
ck('Exact review scope',reader['review_scope']=='supplied_main_and_matched_si')
ck('Reader status does not admit training',reader['training_eligible'] is False and reader['audit_details']['training_promotions']==0)
ck('Reader no source conflict resolution',reader['audit_details']['source_conflicts_resolved'] is False)
ck('Passed prior gates only',reader['presentation_gates']=={'canonical_source_audit':True,'reader_source_audit':True,'molecules':True,'apparatus':True,'products':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False})
pointer_count=0
for path,x in walk(reader):
 if isinstance(x,dict) and 'record_id' in x and 'json_pointer' in x:
  try:
   a=ptr(records[x['record_id']],x['json_pointer']);b=ptr(originals[x['record_id']],x['json_pointer']);ok=a==b;pointer_count+=1
   if x['json_pointer']=='':
    # Root-record links contain review-only metadata already separately constrained.
    aa=copy.deepcopy(a);bb=copy.deepcopy(b)
    for obj in [aa,bb]:
     obj.pop('collection',None);obj.pop('reader_role',None)
     for k in ['review_scope','review_status']:obj['quality'].pop(k,None)
     for source in obj['sources']:
      for k in ['main_status','si_status','reuse_status']:source.pop(k,None)
    ok=aa==bb
  except (KeyError,IndexError,ValueError,TypeError):ok=False
  ck('Reader pointer resolves to unchanged source value '+path,ok)
V=J/'visuals/molecules';Q=J/'visuals/products'
pairs=[('molecule_registry',V/'registry-additions.json',P/'molecules/registry-additions.json'),('molecule_bindings',V/'bindings-proposal.json',P/'molecules/bindings-additions.json'),('solutions',V/'solution-components-proposal.json',P/'molecules/solution-components-additions.json'),('product_contexts',Q/'public-product-contexts-proposal.json',P/'products/product-contexts-additions.json'),('product_registry',Q/'registry-additions.json',P/'products/registry-additions.json')]
data={}
for name,src,dest in pairs:
 b=read(src);a=read(dest);data[name]=a;d=diff(b,a);deltas[name]=d
 expected=copy.deepcopy(b)
 if name=='molecule_registry':
  expected.update(binding_approved=True,status='independently_passed_source_references_staged_for_integration')
  for e in expected['entries']:e.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_stock_audit',published=False,eligible_training=False)
 elif name=='molecule_bindings':
  expected.update(binding_approved=True,status='independently_passed_source_bindings_staged_for_integration')
  for notes in expected['bindingNotes'].values():
   for note in notes.values():note.update(binding_approved=True,independent_scientific_audit='Separate molecular and exact stock/material binding audit passed; scientific fields unchanged.')
  for rid,r in records.items():
   if not r['materials']:expected['recordBindings'].setdefault(rid,{});expected['bindingNotes'].setdefault(rid,{})
  expected['sourceRecordSha256']={rid:sha(P/'records'/(rid+'.json')) for rid in records}
 elif name=='solutions':
  expected['binding_approved']=True
  for c in expected['contexts']:c['binding_approved']=True
 elif name=='product_contexts':
  for rows in expected['recordContexts'].values():
   for row in rows:row['binding_approved']=True
 elif name=='product_registry':
  lookup={a['entry_id']:a for a in read(Q/'public-assets-proposal.json')['assets']}
  for e in expected['entries']:
   e['svgPath']=lookup[e['id']]['public_path'].removeprefix('assets/chemical-registry/');e.update(binding_approved=True,published=False,independentScientificAudit='passed_source_scoped_product_context_audit')
 ck('Exact permitted visual overlay '+name,a==expected)
ck('Stock diagram source payload unchanged',read(P/'molecules/stock-illustration-proposal.json')==read(V/'stock-illustration-proposal.json'))
bindings=data['molecule_bindings'];registry=data['molecule_registry'];products=data['product_contexts'];preg=data['product_registry'];solutions=data['solutions']
ck('26 material bindings',sum(map(len,bindings['recordBindings'].values()))==26)
ck('Five solution instances and 12 components',len(solutions['contexts'])==5 and sum(len(x['components']) for x in solutions['contexts'])==12)
ck('42 product instances and 33 symbols',sum(map(len,products['recordContexts'].values()))==42 and len(preg['entries'])==33)
for rid,r in records.items():
 ck('Complete exact material slot membership '+rid,set(bindings['recordBindings'][rid])=={m['id'] for m in r['materials']})
 ck('Binding current promoted record bytes '+rid,bindings['sourceRecordSha256'][rid]==sha(P/'records'/(rid+'.json')))
for rid,rows in products['recordContexts'].items():
 for row in rows:
  ck('Product context source sample membership '+rid+'/'+row['sample_id'],row['sample_id'] in {p['sample_id'] for p in records[rid]['products']})
  ck('No atomic product/training/aliquot admission '+rid+'/'+row['sample_id'],row['atomic_model'] is False and row['training_eligible'] is False and row.get('same_physical_batch_asserted') is False)
expected_assets={}
for a in read(J/'original-assets-manifest.json')['assets']:
 ck('Crop is selected original fragment '+a['id'],a['contains_complete_source_page'] is False)
 expected_assets['assets/figures/sasongko2025/'+Path(a['path']).name]=(Path(a['path']),a['sha256'])
for a in read(V/'effective-public-assets.json')['assets']+read(Q/'public-assets-proposal.json')['assets']:expected_assets[a['public_path']]=(Path(a['path']),a['sha256'])
expected_assets['sasongko2025-protocol.mjs']=(J/'visuals/apparatus/sasongko2025-protocol.mjs',sha(J/'visuals/apparatus/sasongko2025-protocol.mjs'))
public={a['public_path']:a for a in manifest['public_assets']}
ck('Exact selected 81 public assets',len(public)==len(manifest['public_assets'])==81 and set(public)==set(expected_assets))
for rel,(src,h) in expected_assets.items():
 a=public[rel];ck('Asset publication path constrained '+rel,not Path(rel).is_absolute() and '..' not in Path(rel).parts and not re.search(r'(^|/)(source-render|audit-pages|raw|source-text)(/|$)|\.(pdf|txt|cif)$',rel,re.I))
 ck('Original asset hash '+rel,bind(src)==h)
 ck('Published asset bytes '+rel,bind(P/'dist'/rel)==h==a['sha256'])
 ck('Approved asset provenance path '+rel,Path(a['source_path'])==src)
 if Path(rel).suffix in ['.svg','.json','.mjs']:
  text=io_path(P/'dist'/rel).read_text('utf8');ck('No private filesystem locator in asset '+rel,not re.search(r'[A-Z]:[\\/]|file://|/Users/|\\\\Users\\',text))
for name,entries in [('molecule',registry['entries']),('product',preg['entries'])]:
 for e in entries:
  for key in ['svgPath','model2dPath','model3dPath']:
   if e.get(key):
    rel='assets/chemical-registry/'+e[key];ck('Registry path resolves '+e['id']+'/'+key,rel in public)
    ck('Registry asset digest '+e['id']+'/'+key,public[rel]['sha256']==e['assetHashes'][key])
  ck('Registry staged not published '+e['id'],e['published'] is False)
for path,obj in [('reader',reader),('molecule_registry',registry),('bindings',bindings),('solutions',solutions),('product_contexts',products),('product_registry',preg)]+list(records.items()):
 ck('No private path exported in '+path,not re.search(r'[A-Z]:[\\/]|file://|/Users/|\\\\Users\\',json.dumps(obj)))
 for p,x in walk(obj):
  if isinstance(x,dict) and x.get('public_asset'):
   rel=x['public_asset'];ck('Original evidence reachable '+path+p,rel in public)
   h=x.get('public_asset_sha256',x.get('sha256'))
   if h:ck('Original evidence exact digest '+path+p,public[rel]['sha256']==h)
maps={k:{rid:set() for rid in records} for k in ['structures','properties']}
for section in reader['reader_sections']:
 if section['id'] in maps:
  for item in section['items']:
   for link in item.get('canonical_links',[]):
    parts=link['json_pointer'].strip('/').split('/')
    if parts[0]=='measurements':maps[section['id']][link['record_id']].add(records[link['record_id']]['measurements'][int(parts[1])]['id'])
for section,rows in maps.items():
 ck('Measurement display map '+section,read(P/('record-'+section+'-measurements.json'))=={rid:sorted(x) for rid,x in rows.items()})
for rid in records:ck('No structure/property duplicate '+rid,not maps['structures'][rid]&maps['properties'][rid])
# Run current validators by import only. Their main/build functions are not invoked.
sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews,dataset_lib
for f in ['build_paper_reviews.py','review_scope.py','dataset_lib.py','schema_definition.py']:bind(S/'scripts'/f)
build_paper_reviews.ROOT=P/'consumer-fixture'
errors=build_paper_reviews.validate(reader);ck('Actual current reader validator',not errors,errors)
for rid,r in records.items():
 errors=dataset_lib.validate_record(r);ck('Current schema and semantic validator '+rid,not errors,errors)
 e=dataset_lib.eligibility(r);ck('Current actual training gates all closed '+rid,not any(v['eligible'] for v in e.values()))
for path,h in list(bound.items()):ck('Final input unchanged '+path,sha(Path(path))==h)
bad=[c for c in checks if not c['passed']]
stale_links=[p+'/relation' for p,x in walk(reader) if isinstance(x,dict) and x.get('json_pointer')=='' and x.get('relation')=='Private canonical record pending independent review.']
findings=[]
if stale_links or reader['supporting_information'].get('status')=='matched_local_source_audit_passed_canonical_review_pending':
 findings.append({'id':'J-PROJ-01','severity':'bounded_presentation_status','status':'open','summary':'The public reader retains an obsolete canonical-review pending label despite passed review.','json_pointers':stale_links+['/supporting_information/status'],'required_change':'Preserve v1 and overlay only these 20 status/relation strings with current completed-review wording. Do not mutate historical raw source payload audit flags.','consumer_evidence':'recipe-atlas/dist/source-evidence.mjs line 33 renders each canonical_links relation as a visible small label.','scientific_effect':'None; no values, source evidence, samples, figures or quantities change.'})
bind(S/'dist/source-evidence.mjs')
save(O/'promotion-delta-checks.json',{'status':'passed' if not bad else 'findings','checks':checks,'failed_checks':bad,'pointer_instances_checked':pointer_count})
save(O/'promotion-exact-deltas.json',deltas)
bind(O/'promotion-delta-checks.json');bind(O/'promotion-exact-deltas.json');bind(Path(__file__))
result={'schema':'mattersyn-independent-publication-projection-audit/1','status':'passed' if not bad and not findings else 'revision_required','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'doi':'10.1021/acs.jpcc.5c05144','proposal_freeze_sha256':sha(P/'package-freeze.json'),'scope':'Independent transport-only audit of root publication projection versus unchanged separately audited canonical, reader, molecules, stock, apparatus and product-context packages. Prior scientific audits are relied on explicitly; this is not self-certification of those author packages. No full paper reread, Site import, browser or network/publication action.','counts':manifest['counts']|{'public_assets':len(public),'reader_items':273,'typed_reader_fields':1197,'executed_checks':len(checks),'passed_checks':len(checks)-len(bad),'reader_pointer_instances_checked':pointer_count,'bound_files':len(bound)},'delta_summary':{k:len(v) for k,v in deltas.items()},'upstream_package_sha256':upstream,'source_audits':freeze['source_audits'],'allowed_deltas':['19 records: collection, reader_role, review status/scope and source status/reuse labels only. All scientific arrays and source metadata outside these statuses exact.','Reader: 50 review/status/gate leaves only; all 273 reader items, 1197 typed fields, 20 page coverage entries, source assets/locators, conflicts and scientific missingness unchanged.','Molecules: audit/binding flags and empty material maps for records without materials; sourceRecordSha256 rebased to promoted bytes. All identities, quantities, selectors and models unchanged.','Products: 42 binding flags and 33 public SVG path/approval overlays only. No atomic coordinates, measured crystal or training approval.','All 81 public assets are exact approved bytes: 17 source fragments, 30 molecular/stock assets, 33 symbolic product assets and one apparatus module.'],'manual_review':['Read root prepare_site_proposal.py without executing it; inspected complete leaf-difference sets.','Reviewed status language for separated audits, all 9+11 page scope, unresolved contradictions and no atomic/training admission.','Inspected exact public allowlist and its origin/byte preservation; source PDFs, text caches and full-page images have no attachment or exported filesystem path.','Used actual current schema/semantic/task validators and reader validator against frozen isolated fixture; no Site writes or browser claims.'],'checker_correction':'Initial diagnostic incorrectly required byte-equivalent whole-record targets for 19 empty JSON pointers. The corrected check excludes only the already independently allowed review metadata from whole-record comparison. Initial diagnostics are preserved in checker-diagnostic-0; no author science change was needed.','open_findings':findings+bad,'bound_files':bound,'remaining_gates':['Status-only correction for J-PROJ-01','Importer independent review and actual Site transport audit','Actual desktop/mobile browser review','Anonymous publication verification'],'actions_performed':{'site_modified':False,'frozen_packages_modified':False,'source_modified':False,'browser_exercised':False,'network_accessed':False,'publication_approved':False}}
save(O/'promotion-delta-audit.json',result)
md=f'''# Sasongko publication-projection delta audit\n\nStatus: **{result['status']}**. Auditor: `/root/backlog_eta`; proposal author: `/root`.\n\nThe frozen projection `{result['proposal_freeze_sha256']}` preserves all scientific content of the 19 records, 21 operations, 502 measurements, 273 reader items and 1,197 typed reader fields. The changes are confined to review/display/binding status, promoted-record digests and selected public asset paths. Empty requested task lists and atomic-product exclusions remain unchanged.\n\nAll 81 selected assets match approved bytes: 17 original fragments, 30 molecular/stock assets, 33 symbolic product cards and one apparatus module. The 26 material slots, five stocks/12 components and 42 product-context instances retain their exact assignments. All public registry/evidence paths resolve inside the proposed asset allowlist; no source PDF, full-page image, text cache or private filesystem path is exported.\n\nExecuted {len(checks)} checks ({len(checks)-len(bad)} passed), including current schema/semantic/training validators and the actual reader validator against the frozen isolated fixture. {pointer_count} canonical pointer instances resolve to unchanged values. {len(bound)} files are hash-bound. Complete leaf deltas and supporting checks are saved alongside this report.\n\nOpen findings: {len(bad)}. This is a publication transport audit; prior source and visual audits supply their separate scientific approvals. Actual Site transport, browser testing and anonymous release verification remain separate gates. No Site, source or frozen author file was changed.\n'''
md=md.replace('Open findings: '+str(len(bad)), 'Open findings: '+str(len(findings)+len(bad)))
if findings:md+='\nRequired bounded correction J-PROJ-01: 19 canonical-link display relations and the SI status still say canonical review is pending. Preserve v1 and correct only those 20 metadata leaves. Current source-evidence.mjs visibly renders the relations. Historical raw payload audit flags stay unchanged.\n'
io_path(O/'promotion-delta-audit.md').write_text(md,'utf8')
print(json.dumps({'status':result['status'],'checks':len(checks),'passed':len(checks)-len(bad),'failures':bad[:20],'bound_files':len(bound),'report_sha256':sha(O/'promotion-delta-audit.json')},ensure_ascii=False))
