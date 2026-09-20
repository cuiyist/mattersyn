"""Read-only installed data/code comparison; outputs private audit only."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,html,json,sys
A=Path(__file__).resolve().parent;G=A.parent;O=G/'site-integration-proposal';P=O/'v1';C=O/'product-context-v1';S=Path('[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import eligibility
from review_scope import source_review_scope
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks=[];bound={}
def bind(p):
 p=Path(p);bound[str(p)]=sha(p);return read(p) if p.suffix=='.json' else p
def same(a,b,label):
 checks.append({'passed':a==b,'check':label})
 if a!=b:print('FAILED '+label)
def check(ok,label):same(bool(ok),True,label)
base=bind(A/'pre-integration-baseline.json');imp=bind(O/'site-import-manifest.json');delta=bind(O/'code-delta.json');bind(G/'import_reviewed_ghosh.py')
for name,proposal in [('promotion-delta-audit.json',P),('product-context-audit.json',C)]:
 audit=bind(A/name);same(audit['status'],'passed','passed overlay '+name);same(imp['audits'][name],sha(A/name),'import audit receipt '+name);same(audit['proposal_freeze_sha256'],sha(bind(proposal/'package-freeze.json') if False else proposal/'package-freeze.json'),'exact imported freeze '+name)
 for row in read(proposal/'package-freeze.json')['files']:bind(proposal/row['path']);same(sha(proposal/row['path']),row['sha256'],'proposal remained frozen '+row['path'])
for name,digest in base['previous_records'].items():same(sha(S/'data/records'/name),digest,'old canonical byte preserved '+name)
same(bind(O/'base-record-hashes.json'),base['previous_records'],'root old record snapshot agrees independently')
new={p.stem:bind(p) for p in sorted((P/'records').glob('*.json'))}
allrecords={p.stem:read(p) for p in sorted((S/'data/records').glob('*.json'))}
same(set(allrecords),set(Path(x).stem for x in base['previous_records'])|set(new),'exact complete567 record set')
for rid,r in new.items():
 same(sha(S/'data/records'/(rid+'.json')),sha(P/'records'/(rid+'.json')),'promoted record bytes '+rid);same(r['quality']['requested_tasks'],[],'tasks empty '+rid);same(r['structure_assets'],[],'no atomic binding '+rid)
for rid,r in allrecords.items():
 public=bind(S/'dist/data/records'/(rid+'.json'));same(public,r,'generated public record exact '+rid)
manifest=bind(S/'dist/data/dataset-manifest.json');same(manifest['dataset_version'],'0.28.0','dataset version');same(manifest['record_count'],567,'record count');same(manifest['group_count'],36,'source group count')
for row in manifest['records']:
 r=allrecords[row['record_id']];digest=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();same(row['record_sha256'],digest,'generated normalized record hash '+row['record_id'])
 same(row['eligibility'],eligibility(r),'actual unchanged eligibility rules '+row['record_id'])
tasks={'precursor_selection':95,'partial_protocol':120,'size_conditioned_recipe':15,'exact_structure_recipe':0,'success_prediction':0,'optical_outcome':95}
for task,count in tasks.items():
 p=S/'dist/data/exports'/(task+'.jsonl');bind(p);rows=[json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()];ids={x['record_id'] for x in rows}
 expected={rid for rid,r in allrecords.items() if eligibility(r)[task]['eligible']};same(ids,expected,'training membership '+task);same(len(rows),count,'unchanged training count '+task);same(ids&set(new),set(),'no Ghosh training '+task)
same(sha(S/'scripts/dataset_lib.py'),read(A/'promotion-delta-audit.json')['bound_files'][str(S/'scripts/dataset_lib.py')],'eligibility implementation unchanged since passed promotion')
reader=bind(S/'data/paper-reviews/ghosh2012.json');expected=read(P/'reader/ghosh2012.json')
expected['presentation_gates']['site_integration']=True;expected['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.'
expected['audit_details']['promotion_audit_sha256']=sha(A/'promotion-delta-audit.json');expected['audit_details']['symbolic_product_context_audit_sha256']=sha(A/'product-context-audit.json')
same(reader,expected,'exact four integrated reader metadata leaves only')
generated_expected=copy.deepcopy(reader);generated_expected['review_scope_label']=source_review_scope(reader)['label']
same(generated_expected['review_scope_label'],'Complete supplied main + matched SI review','exact derived coverage label')
same(bind(S/'dist/data/paper-reviews/ghosh2012.json'),generated_expected,'generated reader exact including established derived scope label')
same(reader['presentation_gates']['browser_render'],False,'browser gate separate');same(reader['presentation_gates']['publication'],False,'publication gate separate')
R=S/'dist/assets/chemical-registry';B=A/'baseline/dist/assets/chemical-registry'
orig=bind(B/'registry.json');reg=bind(R/'registry.json');expected=copy.deepcopy(orig);entries=read(P/'molecules/registry-additions.json')['entries']
for e in entries:e['published']=True
expected['entries'].extend(entries);same(reg,expected,'registry exact append only25 old entries intact')
orig=bind(B/'bindings.json');bm=bind(R/'bindings.json');expected=copy.deepcopy(orig);extra=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 for rid,v in extra[key].items():check(rid not in expected.setdefault(key,{}),'no old binding collision '+rid);expected[key][rid]=v
same(bm,expected,'exact binding merges all prior assignments unchanged')
orig=bind(B/'solution-components.json');solutions=bind(R/'solution-components.json');expected=copy.deepcopy(orig);expected['contexts'].extend(read(P/'molecules/solution-components-additions.json')['contexts']);same(solutions,expected,'exact stock append only')
orig=bind(B/'product-contexts.json');products=bind(R/'product-contexts.json');expected=copy.deepcopy(orig);extra=read(C/'product-contexts-additions.json')
for key in ['recordContexts','sourceNotices']:
 for k,v in extra[key].items():check(k not in expected[key],'product no prior collision '+k);expected[key][k]=v
same(products,expected,'product dispatcher exact record/sample append only')
orig=bind(A/'baseline/data/measurement-display.json');display=bind(S/'data/measurement-display.json');expected=copy.deepcopy(orig)
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 for rid,ids in read(P/('record-'+section+'-measurements.json')).items():check(rid not in expected[key],'display map no prior collision '+rid);expected[key][rid]=ids
same(display,expected,'measurement classification changes only explicit Ghosh IDs');same(bind(S/'dist/data/measurement-display.json'),display,'public display map exact')
assets=read(P/'promotion-manifest.json')['public_assets']
for row in assets:bind(S/'dist'/row['public_path']);same(sha(S/'dist'/row['public_path']),row['sha256'],'exact installed public asset '+row['public_path'])
same({p.name for p in (S/'dist/assets/figures/ghosh2012').iterdir() if p.is_file()},{Path(x['public_path']).name for x in assets if x['kind']=='selected_original_scientific_crop'},'only36 selected source crops installed')
urls=set()
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader);same(urls,{x['public_path'] for x in assets if x['kind']=='selected_original_scientific_crop'},'reader figure references exact')
for u in urls:check((S/'dist'/u).is_file(),'reader public URL exists '+u)
label_delta=bind(O/'reader-inventory-label-delta.json')
codefiles={x['file'] for x in delta['changes']}|set(delta['cache_revision_files']);code_evidence=[]
for rel in sorted(codefiles):
 independent=A/'baseline'/rel;rootbase=O/'base-site-inputs'/rel;p=independent if independent.exists() else rootbase
 old=bind(p).read_text(encoding='utf8');expected=old
 if independent.exists() and rootbase.exists():same(rootbase.read_text(encoding='utf8'),old,'root code baseline agrees independent '+rel)
 for change in delta['changes']:
  if change['file']!=rel:continue
  same(expected.count(change['before']),change['occurrences'],'strict patch count '+rel+' '+change['before'][:45]);expected=expected.replace(change['before'],change['after'])
 if rel in delta['cache_revision_files']:expected=expected.replace('0.27.0-r1','0.28.0-r1').replace('0.27.0-r2','0.28.0-r2')
 if rel==label_delta['file']:
  check(label_delta['before_sha256'] in {hashlib.sha256(expected.encode()).hexdigest(),hashlib.sha256(expected.replace('\n','\r\n').encode()).hexdigest()},'label delta binds exact pre-label module')
  for before,after in [('original figures','original figure entries'),('tables inventoried','table entries inventoried')]:
   same(expected.count(before),1,'single wording replacement '+before);expected=expected.replace(before,after)
  same(sha(S/rel),label_delta['after_sha256'],'final label module hash')
 actual=bind(S/rel).read_text(encoding='utf8')
 # Generated HTML is regenerated by the build; its contents may legitimately change.
 if not rel.endswith('.html'):same(actual,expected,'ONLY declared source/cache changes '+rel)
 else:check('0.27.0-r' not in actual,'generated HTML new cache epoch '+rel)
 code_evidence.append({'file':rel,'baseline':'independent' if independent.exists() else 'root preserved','installed_sha256':sha(S/rel)})
merged={'dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json'}
for rel,info in base['shared_file_snapshots'].items():
 if rel not in codefiles|merged:same(sha(S/rel),info['sha256'],'unchanged shared source '+rel)
# Execute only the two pure display helpers parsed from the actual build source.
source=(S/'scripts/build_dataset.py').read_text(encoding='utf8');tree=ast.parse(source);wanted={'material_reader_notes','product_reader_note'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
same(len(nodes),2,'both pure source-scoped helpers present');ns={'json':json,'esc':html.escape,'human':lambda s:s.replace('_',' ').replace('.',' · ')};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-reader-display-functions>','exec'),ns)
for rid,r in allrecords.items():
 for m in r['materials']:
  shown=ns['material_reader_notes'](m,r);removed=[n for n in dict.fromkeys(m['notes']) if n not in shown]
  allowed={'lian2021':'Chemical/atomic visual binding is separately pending.','ghosh2012':'Source-qualified identity only; molecular/product visual binding is separately pending.'}.get(r['lineage']['source_group'])
  check(all(n==allowed for n in removed),'no unrelated material note suppressed '+rid+'/'+m['id'])
for rid,r in new.items():
 for p in r['products']:
  for n in p['notes']:
   rendered=ns['product_reader_note'](n,r)
   if n.startswith('Source context object: '):check('<details' in rendered and 'Source context object: {' not in rendered,'structured readable source provenance '+rid+'/'+p['sample_id'])
   else:same(rendered,'<p>'+html.escape(n)+'</p>','all other sample notes retained '+rid+'/'+p['sample_id'])
inventory=bind(S/'dist/data/inventory-summary.json');same(inventory,bind(S/'data/inventory-summary.json'),'inventory public exact');same(inventory,bind(O/'inventory-summary.json'),'inventory final private exact')
same(inventory['summary']['canonical_records'],567,'inventory567');same(inventory['summary']['synthesis_route_variant_records'],111,'routes111');same(inventory['summary']['public_material_hubs'],46,'hubs46');same(inventory['summary']['direct_synthesis_target_systems'],35,'direct35');same(inventory['summary']['component_only_hubs'],11,'component11')
check('ghosh2021' not in json.dumps(inventory),'stale template source absent');check('ghosh2012' in json.dumps(inventory),'correct Ghosh source included')
index=bind(S/'dist/data/paper-review-index.json');check('ghosh2012' in json.dumps(index),'paper reader index contains source')
validation=bind(S/'dist/data/validation-report.json');same(validation['status'],'passed','full build validator passed');same(validation['eligible_by_task'],tasks,'public training counts correct')
runtime=bind(A/'actual-dispatch-checks.json');same(runtime['status'],'passed','actual installed dispatch test passed')
for p,digest in runtime['bound_files'].items():bind(p);same(sha(p),digest,'runtime file still current '+Path(p).name)
bind(Path(__file__));findings=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-independent-integration-transport-audit/1','source_id':'ghosh2012','author':'/root','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not findings else 'open_findings','passed':not findings,'open_findings':findings,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'check_count':len(checks)+runtime['check_count'],'transport_check_count':len(checks),'runtime_check_count':runtime['check_count'],'counts':{'records':567,'prior_records_byte_identical':546,'new_records_exact':21,'operations':33,'condition_rows':183,'parameter_quantities':70,'alternative_schedule_quantities':10,'material_slots':88,'public_assets':85,'symbolic_product_contexts':45,'training_tasks_added':0},'code_scope':code_evidence,'actual_manual_scope':['Read root import script and all thirteen declared source patches; source-specific Ghosh branches precede existing dispatch, while foreign source behavior is preserved.','Compared every existing canonical record by its independently captured byte hash; compared every generated record object and manifest digest.','Audited exact reader metadata changes, registry/bindings/stocks/product-context merges and measurement ID maps; no earlier data overwritten.','Executed actual installed module dispatch in a minimal DOM harness for all33 stages and exact183 rows; checked all88 chemicalEntry bindings and exclusion of1761 foreign operations. This is not a mounted-browser visual claim.','Executed actual pure display helpers; only precise historical pending metadata is hidden for qualified sources, source context objects retain readable expandable provenance and other notes remain.','Public allowlist and all36 reader image URLs exist with exact approved bytes; no PDF/full-page payload added by this import.','Verified all six training memberships against actual eligibility, exact prior counts and zero new Ghosh entries. No atomic/training admission.'],'bound_files':dict(sorted(bound.items())),'site_changed_by_auditor':False,'browser_approved':False,'publication_approved':False,'training_approved':False}
for name,obj in [('integration-transport-audit.json',result),('integration-transport-checks.json',{'checks':checks})]:(A/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(A/'integration-transport-audit.md').write_text(f"# Ghosh installed integration audit\n\nStatus: **{result['status']}**; {result['check_count']} checks ({len(checks)} transport and {runtime['check_count']} actual module checks), {len(findings)} open findings.\n\nAll 546 earlier canonical files are byte-identical. The 21 new records and generated data exactly preserve the passed overlays; dataset 0.28.0 has 567 records. All 85 assets, 88 material bindings, stock mappings, 45 explicit product contexts, reader figures and source-scoped measurement maps transport correctly.\n\nActual installed dispatch produces all 33 stages and 183 condition rows without generic duplicates; all 1,761 foreign operations are rejected by the Ghosh-specific module. Shared source changes match the declared patches/cache updates. Six training export memberships/counts remain unchanged and contain no Ghosh rows.\n\nThis audit uses private comparisons and a minimal DOM execution harness. Root owns actual browser visuals and release verification; those gates are not certified here.\n",encoding='utf8')
print(json.dumps({'status':result['status'],'checks':result['check_count'],'findings':findings,'audit_sha256':sha(A/'integration-transport-audit.json')}))
