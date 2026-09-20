"""Independent, read-only prospective review. Does not run author import/build scripts."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent;J=O.parent;S=J.parents[4]/'recipe-atlas'
NODE=Path('[local path redacted]')
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x): (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[];bound={};planned={};changes=[]
def ck(n,b):
 checks.append({'check':n,'passed':bool(b)})
 assert b,n
def bind(p):bound[str(p)]=sha(p)
scripts=['import_reviewed_sasongko.py','build_sasongko_inventory.py','build_and_check_site.py']
for name in scripts:
 p=J/name;bind(p);ast.parse(p.read_text('utf8'));ck(name+' parses',True)
 snapshot=O/'reviewed-scripts'/name;snapshot.parent.mkdir(parents=True,exist_ok=True)
 if snapshot.exists() and snapshot.read_bytes()!=p.read_bytes():snapshot=snapshot.with_name(snapshot.stem+'-'+sha(p)[:12]+snapshot.suffix)
 if snapshot.exists():ck(name+' reviewed snapshot unchanged',snapshot.read_bytes()==p.read_bytes())
 else:snapshot.write_bytes(p.read_bytes())

import_text=(J/scripts[0]).read_text('utf8');tree=ast.parse(import_text)
link=read(J/'visuals/products/original-evidence-consumer-insertion.json');bind(J/'visuals/products/original-evidence-consumer-insertion.json')
ck('exact current crystal consumer baseline',sha(S/link['target'])==link['baseline_sha256'])
env={'rel':'dist/protocol-visuals.mjs','linkpatch':link}
for node in tree.body:
 if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='plan':
  args=[eval(compile(ast.Expression(a),'<literal plan>', 'eval'),{'__builtins__':{}},env) for a in node.value.args]
  rel,before,after=args[:3];count=args[3] if len(args)>3 else 1
  p=S/rel;bind(p);current=p.read_text('utf8')
  ck('original exact anchor '+rel+' '+before,current.count(before)==count)
  prior=planned.get(rel,current);ck('sequential exact anchor '+rel+' '+before,prior.count(before)==count)
  planned[rel]=prior.replace(before,after)
  changes.append({'file':rel,'before':before,'after':after,'count':count})
ck('all expected planned substitutions',len(changes)==14)
for rel,text in list(planned.items()):
 text=text.replace('0.32.0-r1','0.33.0-r1').replace('0.32.0-r2','0.33.0-r2');planned[rel]=text
 if rel.endswith('.py'):ast.parse(text);ck('prospective Python syntax '+rel,True)
 else:
  proc=subprocess.run([str(NODE),'--input-type=module','--check'],input=text,text=True,capture_output=True)
  ck('prospective JavaScript syntax '+rel,proc.returncode==0)
 p=O/'prospective-code'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf8')
ck('dataset 0.33.0 in both manifest and report',planned['scripts/build_dataset.py'].count("'dataset_version':'0.33.0'")==2)
ck('Sasongko and Friedfeld context link display retains separate source gate',"r['lineage']['source_group'] in ('friedfeld2019','sasongko2025')" in planned['scripts/build_dataset.py'])

records={p.stem:read(p) for p in (S/'data/records').glob('*.json')}
oldhash={str(p):sha(p) for p in (S/'data/records').glob('*.json')};bound.update(oldhash)
exports={str(p):sha(p) for p in (S/'dist/data/exports').glob('*.jsonl')};bound.update(exports)
ck('current 656 canonical records',len(records)==656);ck('current six training exports',len(exports)==6)
ck('current dataset is 0.32.0',read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.32.0');bind(S/'dist/data/dataset-manifest.json')
new={p.stem:read(p) for p in (J/'canonical-proposal/v1/records').glob('*.json')}
ck('19 canonical candidates',len(new)==19);ck('new record IDs do not collide',not(set(new)&set(records)))
for rid,r in new.items():
 p=J/'canonical-proposal/v1/records'/(rid+'.json');bind(p)
 ck(rid+' zero requested tasks',r['quality']['requested_tasks']==[])
 ck(rid+' no structure assets',r['structure_assets']==[])
 ck(rid+' only Sasongko source group',r['lineage']['source_group']=='sasongko2025')

# Evaluate only the established pure route classifier and acronym constants.
sys.path.insert(0,str(S/'scripts'))
ns={'__name__':'independent_readonly_atlas_review','__file__':str(S/'scripts/build_atlas.py')}
exec(compile(planned['scripts/build_atlas.py'],'<prospective atlas>','exec'),ns)
old_ns={'__name__':'independent_readonly_atlas_baseline','__file__':str(S/'scripts/build_atlas.py')}
exec(compile((S/'scripts/build_atlas.py').read_text('utf8'),'<baseline atlas>','exec'),old_ns)
for rid,r in records.items():
 ck(rid+' prior route classification unchanged',ns['synthesis_route'](r)==old_ns['synthesis_route'](r))
 f=r['material']['formula'];before=r['material'].get('elements') or re.findall('[A-Z][a-z]?',f);after=r['material'].get('elements') or ns['COMPONENT_ELEMENTS'].get(f,re.findall('[A-Z][a-z]?',f))
 ck(rid+' prior main element classification unchanged',before==after)
newroutes=[]
for rid,r in new.items():
 t=copy.deepcopy(r);t['collection']='reviewed_literature';t['quality']['review_status']='source_reviewed';t['reader_role']='synthesis_route' if t['record_type'] in ('literature_protocol','protocol_variant') else 'supporting_procedure' if t['record_type']=='procedure' else 'contextual_observation'
 if ns['synthesis_route'](t):newroutes.append(rid)
ck('exactly one new route',newroutes==['sasongko-2025-hot-injection'])
ck('FAPbI3 intended-target elements include no false fluorine',ns['COMPONENT_ELEMENTS']['FAPbI3']==['C','H','N','Pb','I'] and set(ns['COMPONENT_ELEMENTS']['FAPbI3'])<=ns['SYMBOLS'])
ck('FAPbI3 human label',ns['NAMES']['FAPbI3']=='Formamidinium lead iodide quantum dots')

V=S/'dist/assets/chemical-registry'
reg=read(V/'registry.json');bindings=read(V/'bindings.json');sol=read(V/'solution-components.json');prod=read(V/'product-contexts.json');display=read(S/'data/measurement-display.json')
for p in [V/'registry.json',V/'bindings.json',V/'solution-components.json',V/'product-contexts.json',S/'data/measurement-display.json',S/'data/inventory-summary.json']:bind(p)
entries=read(J/'visuals/molecules/registry-additions.json')['entries']+read(J/'visuals/products/registry-additions.json')['entries'];ids=[e['id'] for e in entries]
ck('46 new unique registry identities',len(ids)==len(set(ids))==46);ck('no registry identity collision',not(set(ids)&{e['id'] for e in reg['entries']}))
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:ck('no binding collision '+key,not(set(new)&set(bindings.get(key,{}))))
ck('no solution record collision',not(set(new)&{c['record_id'] for c in sol['contexts']}))
ck('no product record collision',not(set(new)&set(prod['recordContexts'])))
ck('no source notice collision','sasongko2025' not in prod['sourceNotices'])
for key in ['record_structural_measurement_ids','record_property_measurement_ids']:ck('no scoped display collision '+key,not(set(new)&set(display[key])))

assets=read(J/'visuals/molecules/effective-public-assets.json')['assets']+read(J/'visuals/products/public-assets-proposal.json')['assets']
assets += [{'path':str(J/'visuals/apparatus/sasongko2025-protocol.mjs'),'public_path':'sasongko2025-protocol.mjs','sha256':sha(J/'visuals/apparatus/sasongko2025-protocol.mjs')}]
for a in read(J/'original-assets-manifest.json')['assets']:assets.append({'path':a['path'],'public_path':'assets/figures/sasongko2025/'+Path(a['path']).name,'sha256':a['sha256']})
ck('81 unique candidate public files',len(assets)==len({a['public_path'] for a in assets})==81)
for a in assets:
 p=Path(a['path']);bind(p);ck('source asset exact '+a['public_path'],sha(p)==a['sha256'])
 dest=S/'dist'/a['public_path'];ck('public target absent or identical '+a['public_path'],not dest.exists() or sha(dest)==a['sha256'])
 ck('public candidate stays under dist '+a['public_path'],dest.resolve().is_relative_to((S/'dist').resolve()))

P=J/'site-integration-proposal/v1';freeze=read(P/'package-freeze.json');bind(P/'package-freeze.json')
for f in freeze['files']:
 p=P/f['path'];ck('frozen root projection file '+f['path'],sha(p)==f['sha256']);bind(p)
public=read(P/'promotion-manifest.json')['public_assets']
ck('root projection exactly the 81 qualified public assets',{(a['public_path'],a['sha256']) for a in assets}=={(a['public_path'],a['sha256']) for a in public})
for rid,original in new.items():
 projected=read(P/'records'/(rid+'.json'))
 for k in set(original)-{'collection','reader_role','quality','sources'}:ck(rid+' source field unchanged '+k,projected[k]==original[k])
 for k in set(original['quality'])-{'review_status','review_scope'}:ck(rid+' quality field unchanged '+k,projected['quality'][k]==original['quality'][k])
 for a,b in zip(original['sources'],projected['sources']):
  for k in set(a)-{'main_status','si_status','reuse_status'}:ck(rid+' bibliography unchanged '+k,a[k]==b[k])
ck('complete namespace preflight before first shared copy',import_text.index('# Complete all namespace and copy-conflict checks')<import_text.index("for f in read(P/'promotion-manifest.json')['public_assets']:"))
preflight=import_text[import_text.index('# Complete all namespace and copy-conflict checks'):import_text.index("for rel in ['dist/assets/chemical-registry/registry.json'")]
for item in ['public_assets','data/records','data/paper-reviews/sasongko2025.json','current_entries','recordBindings','bindingNotes','sourceRecordSha256','solution-components','recordContexts','sourceNotices','record_structural_measurement_ids','record_property_measurement_ids']:ck('complete preflight covers '+item,item in preflight)

ck('only canonical record operation is non-overwriting copy',"for src in (P/'records').glob('*.json'):cp(src,S/'data/records'/src.name)" in import_text)
ck('existing differing files refused',"if b.exists():assert sha(a)==sha(b)" in import_text)
ck('promotion audit exact freeze required',"a['proposal_freeze_sha256']==sha(P/'package-freeze.json')" in import_text)
ck('frozen proposal file bytes checked',"for f in read(P/'package-freeze.json')['files']:assert sha(P/f['path'])==f['sha256']" in import_text)
ck('reader changes limited to three presentation fields',all(x in import_text for x in ["reader['presentation_gates']['site_integration']=True","reader['publication_status']=","reader['audit_details']['promotion_audit_sha256']="]))
build=(J/'build_and_check_site.py').read_text('utf8')
ck('byte-preservation check for all existing records',"assert len(old)==656 and all(sha(S/'data/records'/n)==h for n,h in old.items())" in build)
ck('byte-preservation check for all six exports',"assert len(exports)==6 and all(sha(S/'dist/data/exports'/n)==h for n,h in exports.items())" in build)
ck('build gates on each subprocess return code',"if p.returncode:raise SystemExit(p.returncode)" in build)
ck('builder order retains dataset reader evidence paper atlas before inventory',build.index("'build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py'")<build.index("str(H/'build_sasongko_inventory.py')"))
ck('schema/quality/quantity/review-role checks remain',all(x in build for x in ['check_site.py','check_atlas.py','check_quality.py','test_quantity_bounds.py','test_review_scope.py','test_reader_role.py']))
inventory=(J/'build_sasongko_inventory.py').read_text('utf8')
ck('inventory operates only Sasongko source row replacement',"newgroups=['sasongko2025']" in inventory)
ck('inventory exact record partition and unknown corpus totals',all(x in inventory for x in ['record_id_inventory_exact','category_partition','full_corpus_totals_unknown','no_exact_structure','no_success_labels']))
ck('inventory leaves historical provenance explicitly historical','Historical inherited inventory provenance' in inventory)
ck('optional insertion exact reviewed text applied',link['replacement'] in planned[link['target']])
ck('source and record prefixes scope original-image insertion',"r.lineage?.source_group==='sasongko2025'&&r.record_id.startsWith('sasongko-2025-')" in link['replacement'])
ck('image link pinned hash, strict local PNG prefix and safe external window',all(x in link['replacement'] for x in ['[a-f0-9]{64}','assets\\/figures\\/sasongko2025\\/','noopener noreferrer',"+'?sha='+link.sha256"]))
for p,h in oldhash.items():ck('read-only record preserved '+p,sha(Path(p))==h)
for p,h in exports.items():ck('read-only export preserved '+p,sha(Path(p))==h)

save('current-site-baseline.json',{'record_hashes':oldhash,'training_export_hashes':exports,'dataset_version':'0.32.0','captured_utc':datetime.now(timezone.utc).isoformat()})
save('prospective-replacements.json',{'changes':changes,'prospective_files':{rel:hashlib.sha256(t.encode()).hexdigest() for rel,t in planned.items()}})
report={'status':'passed_bounded_preexecution_review','scope':'Read-only root import/build implementation review against current Site and frozen projection. No import/build run, new source audit or product-science audit is certified.','reviewer':'/root/peng1998_reader_assets','role_disclosure':'Reviewer authored product proposal and original source extraction; this review only examines distinct root import/build transport. Root separately audits the product proposal.','proposal_freeze_sha256':sha(P/'package-freeze.json'),'check_count':len(checks),'checks':checks,'open_blocking_findings':[],'open_findings':[],'resolved_findings':[{'id':'SAS-IMPORT-PREFLIGHT-01','original_finding':'Collision checks were interleaved with mutation in the initially reviewed importer.','resolution':'Root added complete namespace and destination checks before shared writes; exact actual current inputs and ordering independently verified. Initial script is preserved in reviewed-scripts.'}],'counts':{'existing_records':656,'existing_training_exports':6,'new_records':19,'new_routes':1,'public_candidates':81,'new_registry_entries':46},'pending':['Distinct frozen promotion delta audit','Actual import/build preservation verification','Mounted-browser review','Publication verification'],'bound_files':bound,'site_mutated':False,'author_scripts_executed':False,'created_utc':datetime.now(timezone.utc).isoformat()}
save('preexecution-review.json',report)
(O/'preexecution-review.md').write_text('# Sasongko import/build pre-execution review\n\nPassed the bounded read-only implementation review. All current replacement anchors match, prospective Python and JavaScript parse, FAPbI3 expands to C/H/N/Pb/I, and all 656 prior route and element classifications are unchanged. Nineteen candidates produce one additional synthesis route and no requested training tasks. All 81 public destinations and 46 new registry IDs are conflict-free against the captured Site. The build runner checks all six training exports and all prior record bytes.\n\nThe initial preflight advisory is resolved: root moved complete collision and target checks ahead of the first Site mutation. The frozen root projection contains exactly the expected public asset hash set, and its canonical scientific fields remain unchanged. The distinct promotion audit, actual build output and browser/publication gates remain separate. The reviewer did not run import/build scripts or alter Site. Product science is excluded because this reviewer authored that proposal.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'report_sha256':sha(O/'preexecution-review.json'),'open_findings':report['open_findings']},indent=2))
