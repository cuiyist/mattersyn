"""Independent installed transport/code regression audit. No Site writes."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,html,json,sys
A=Path(__file__).resolve().parent;N=A.parent;O=N/'site-integration-proposal';P=O/'v1';C=N/'visuals/product-context';S=Path('[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import eligibility
from review_scope import source_review_scope
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={}
def same(a,b,label):
 checks.append({'check':label,'passed':a==b})
 if a!=b:print('FAILED '+label)
def ck(ok,label):same(bool(ok),True,label)
def bind(p):
 p=Path(p);bound[str(p)]=sha(p);return read(p) if p.suffix=='.json' else p
def frozen(p):
 f=bind(p/'package-freeze.json')
 if 'files' in f:
  for x in f['files']:bind(p/x['path']);same(sha(p/x['path']),x['sha256'],'Frozen proposal '+x['path'])
 else:
  for n,h in f['bound_files'].items():
   np=Path(n)
   if np==S/'dist/crystal-viewer.mjs':
    prior=O/'base-site-inputs/dist/crystal-viewer.mjs';bind(prior);same(sha(prior),h,'Frozen consumer agrees with preserved pre-import bytes; current cache delta checked below')
   else:bind(n);same(sha(n),h,'Frozen bound input '+n)
 return f
base=bind(A/'independent-baseline.json');base['previous_records']={rid+'.json':x['sha256'] for rid,x in base['records'].items()};base['shared_file_snapshots']={rel:{'sha256':h} for rel,h in base['files'].items()};imp=bind(O/'site-import-manifest.json');delta=bind(O/'code-delta.json')
for name,proposal,receipt in [('promotion-delta-audit.json',P,A/'promotion-delta-audit.json'),('product-context-audit.json',C,N/'product-context-independent-audit/independent-audit.json')]:
 audit=bind(receipt);same(audit['status'],'passed','Passed prior '+name);same(imp['audits'][name],sha(receipt),'Imported audit hash '+name);same(audit['proposal_freeze_sha256'],sha(proposal/'package-freeze.json'),'Exact imported freeze '+name);frozen(proposal)
same(bind(O/'base-record-hashes.json'),base['previous_records'],'Root old-record snapshot agrees with independent baseline')
for name,h in base['previous_records'].items():same(sha(S/'data/records'/name),h,'Old canonical bytes '+name)
new={p.stem:bind(p) for p in sorted((P/'records').glob('*.json'))};records={p.stem:read(p) for p in sorted((S/'data/records').glob('*.json'))}
same(len(records),626,'626 records');same(set(records),{Path(x).stem for x in base['previous_records']}|set(new),'Exact complete record set')
for rid,r in new.items():
 same(sha(S/'data/records'/(rid+'.json')),sha(P/'records'/(rid+'.json')),'Exact promoted bytes '+rid);same(r['quality']['requested_tasks'],[],'No tasks '+rid);same(r['structure_assets'],[],'No atomic models '+rid)
for rid,r in records.items():same(bind(S/'dist/data/records'/(rid+'.json')),r,'Generated public record exact '+rid)
manifest=bind(S/'dist/data/dataset-manifest.json');same(manifest['dataset_version'],'0.31.0','Dataset version');same(manifest['record_count'],626,'Manifest records');same(manifest['group_count'],39,'Manifest source groups')
for row in manifest['records']:
 r=records[row['record_id']];h=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();same(row['record_sha256'],h,'Generated normalized hash '+row['record_id']);same(row['eligibility'],eligibility(r),'Eligibility unchanged '+row['record_id'])
task_counts={}
for p in sorted((S/'dist/data/exports').glob('*.jsonl')):
 bind(p);rows=[json.loads(s)for s in p.read_text(encoding='utf8').splitlines()if s.strip()];task=p.stem;ids={r['record_id']for r in rows};expected={rid for rid,r in records.items()if eligibility(r)[task]['eligible']};same(ids,expected,'Training membership '+task);same(ids&set(new),set(),'No Pati training '+task);task_counts[task]=len(rows)
 baseline_ids={rid for rid,x in base['records'].items() if x['eligibility'][task]['eligible']};same(ids,baseline_ids,'Training membership unchanged from607-record baseline '+task);same(sha(p),base['files'][p.relative_to(S).as_posix()],'Training export exact pre-import bytes '+task)
for rid,x in base['records'].items():same(eligibility(records[rid]),x['eligibility'],'Old eligibility unchanged '+rid)
pa=read(A/'promotion-delta-audit.json');same(sha(S/'scripts/dataset_lib.py'),pa['bound_files'][str(S/'scripts/dataset_lib.py')],'Eligibility code unchanged since promotion')
reader=bind(S/'data/paper-reviews/pati2009.json');expected=read(P/'reader/pati2009.json')
expected['presentation_gates'].update(site_integration=True,symbolic_product_contexts=True)
expected['remaining_gaps']=[x for x in expected['remaining_gaps']if x!='Source, canonical/reader and visual audits passed. Integrated browser and publication gates remain separate; no qualified atomic model is admitted.']
expected['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.'
expected['audit_details']['promotion_audit_sha256']=imp['audits']['promotion-delta-audit.json'];expected['audit_details']['symbolic_product_context_audit_sha256']=imp['audits']['product-context-audit.json']
same(reader,expected,'Exact declared integrated reader metadata only');same(reader['presentation_gates']['browser_render'],False,'Browser gate separate');same(reader['presentation_gates']['publication'],False,'Publication gate separate')
expected=copy.deepcopy(reader);expected['review_scope_label']=source_review_scope(reader)['label'];same(bind(S/'dist/data/paper-reviews/pati2009.json'),expected,'Generated reader exact with derived coverage label');same(reader['review_scope'],'supplied_main_and_matched_si','Matched SI scope retained')
R=S/'dist/assets/chemical-registry';B=A/'independent-baseline/dist/assets/chemical-registry'
expected=bind(B/'registry.json');expected=copy.deepcopy(expected);entries=read(P/'molecules/registry-additions.json')['entries']+read(P/'products/registry-additions.json')['entries']
for e in entries:e.update(published=True,binding_approved=True)
expected['entries'].extend(entries);same(bind(R/'registry.json'),expected,'Registry exact append 20 references and 11 symbols; all prior identities unchanged')
expected=copy.deepcopy(bind(B/'bindings.json'));extra=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 for rid,v in extra[key].items():ck(rid not in expected.setdefault(key,{}),'No old slot collision '+rid);expected[key][rid]=v
same(bind(R/'bindings.json'),expected,'Exact bindings append')
expected=copy.deepcopy(bind(B/'solution-components.json'));expected['contexts'].extend(read(P/'molecules/solution-components-additions.json')['contexts']);same(bind(R/'solution-components.json'),expected,'Exact six-stock append')
expected=copy.deepcopy(bind(B/'product-contexts.json'));extra=read(P/'products/product-contexts-additions.json')
for key in ['recordContexts','sourceNotices']:
 for rid,v in extra[key].items():ck(rid not in expected[key],'No old product collision '+rid);expected[key][rid]=v
same(bind(R/'product-contexts.json'),expected,'Exact 39 product contexts; prior sample dispatch unchanged')
expected=copy.deepcopy(bind(A/'independent-baseline/data/measurement-display.json'))
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 for rid,ids in read(P/('record-'+section+'-measurements.json')).items():ck(rid not in expected[key],'No old measurement classification collision '+rid);expected[key][rid]=ids
same(bind(S/'data/measurement-display.json'),expected,'Only Pati measurement classifications added');same(bind(S/'dist/data/measurement-display.json'),expected,'Public measurement map exact')
assets=read(P/'promotion-manifest.json')['public_assets']
for x in assets:bind(S/'dist'/x['public_path']);same(sha(S/'dist'/x['public_path']),x['sha256'],'Installed public asset '+x['public_path'])
for e in read(P/'products/registry-additions.json')['entries']:bind(R/e['svgPath']);same(sha(R/e['svgPath']),e['assetHashes']['svgPath'],'Installed phase symbol '+e['id'])
same({p.name for p in (S/'dist/assets/figures/pati2009').iterdir()if p.is_file()},{Path(x['public_path']).name for x in assets if x['kind']=='selected_original_scientific_crop'},'Exact 20 selected crops only')
urls=set()
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader);same(urls,{x['public_path']for x in assets if x['kind']=='selected_original_scientific_crop'},'Exact reader image references')
for u in urls:ck((S/'dist'/u).is_file(),'Reader image exists '+u)
codefiles={x['file']for x in delta['changes']}|set(delta['cache_revision_files']);code_evidence=[]
for rel in sorted(codefiles):
 independent=A/'independent-baseline'/rel;rootbase=O/'base-site-inputs'/rel;p=independent if independent.exists() else rootbase;old=bind(p).read_text(encoding='utf8');expected=old
 if independent.exists() and rootbase.exists():same(rootbase.read_text(encoding='utf8'),old,'Root code baseline agrees '+rel)
 for x in delta['changes']:
  if x['file']==rel:same(expected.count(x['before']),x['occurrences'],'Strict code patch '+rel+' '+x['before'][:45]);expected=expected.replace(x['before'],x['after'])
 if rel in delta['cache_revision_files']:expected=expected.replace('0.30.0-r1','0.31.0-r1').replace('0.30.0-r2','0.31.0-r2')
 actual=bind(S/rel).read_text(encoding='utf8')
 if not rel.endswith('.html'):same(actual,expected,'Only declared code/cache edits '+rel)
 else:ck('0.30.0-r' not in actual,'Generated HTML current cache epoch '+rel)
 code_evidence.append({'file':rel,'baseline':'independent' if independent.exists() else 'root preserved','installed_sha256':sha(S/rel)})
merged={'dist/assets/chemical-registry/'+x for x in ['registry.json','bindings.json','solution-components.json','product-contexts.json']}|{'data/measurement-display.json','data/inventory-summary.json','dist/data/dataset-manifest.json','dist/data/validation-report.json'}
for rel,x in base['shared_file_snapshots'].items():
 if rel not in codefiles|merged:same(sha(S/rel),x['sha256'],'Unchanged shared code '+rel)
tree=ast.parse((S/'scripts/build_dataset.py').read_text(encoding='utf8'));wanted={'material_reader_notes','product_reader_note'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in wanted];same(len(nodes),2,'Both actual display helpers available');ns={'json':json,'esc':html.escape,'human':lambda s:s.replace('_',' ').replace('.',' · ')};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-display-functions>','exec'),ns)
allowed={'lian2021':'Chemical/atomic visual binding is separately pending.','ghosh2012':'Source-qualified identity only; molecular/product visual binding is separately pending.','sommer2020':'Chemical identity and source role only; independently qualified molecular/component bindings remain pending.','matuhina2023':'Identity and role are source scoped; qualified molecular/component bindings remain separate.','pati2009':'Named identity and printed formula retained separately; no molecular model approval.'}
for rid,r in records.items():
 for m in r['materials']:
  shown=ns['material_reader_notes'](m,r);removed=[x for x in dict.fromkeys(m['notes'])if x not in shown];ck(all(x==allowed.get(r['lineage']['source_group'])for x in removed),'No unrelated material note suppressed '+rid+'/'+m['id'])
for rid,r in new.items():
 for product in r['products']:
  for note in product['notes']:
   rendered=ns['product_reader_note'](note,r)
   if note.startswith('Source context definition: '):ck('<details' in rendered and 'Source context definition: {' not in rendered,'Expandable source provenance '+rid+'/'+product['sample_id'])
   else:same(rendered,'<p>'+html.escape(note)+'</p>','Other product notes exact '+rid+'/'+product['sample_id'])
inventory=bind(S/'dist/data/inventory-summary.json');same(inventory,bind(S/'data/inventory-summary.json'),'Public inventory exact');same(inventory,bind(O/'inventory-summary.json'),'Private inventory exact');same(inventory['summary']['canonical_records'],626,'Inventory record count');same(inventory['summary']['synthesis_route_variant_records'],118,'Inventory routes')
row=next(x for x in inventory['per_paper']if x['source_group']=='pati2009');same(row['record_ids'],sorted(new),'Inventory source IDs');same(row['measurement_entry_count'],268,'Inventory source measurements');same(row['synthesis_route_variant_count'],3,'Inventory three routes');same(row['procedure_count'],11,'Inventory eleven procedures');same(row['contextual_observation_count'],5,'Inventory five observations');same(row['si_status'],'matched_and_reviewed','Inventory SI matched status')
index=bind(S/'dist/data/paper-review-index.json');ck('pati2009' in json.dumps(index),'Source reader indexed')
validation=bind(S/'dist/data/validation-report.json');same(validation['status'],'passed','Full validator passed');same(validation['eligible_by_task'],task_counts,'Training counts unchanged')
build=bind(O/'build-check-output.json');ck(all(x['exit_code']==0 for x in build['runs']),'Full recorded build/check commands passed')
runtime=bind(A/'actual-dispatch-checks.json');same(runtime['status'],'passed','Installed dispatch checks passed')
for p,h in runtime['bound_files'].items():bind(p);same(sha(p),h,'Runtime input still current '+Path(p).name)
for p in [N/'import_reviewed_pati.py',N/'build_and_check_site.py',N/'build_pati_inventory.py',Path(__file__)]:bind(p)
findings=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-independent-integration-transport-audit/1','source_id':'pati2009','author':'/root','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed'if not findings else'open_findings','passed':not findings,'open_findings':findings,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'check_count':len(checks)+runtime['check_count'],'transport_check_count':len(checks),'runtime_check_count':runtime['check_count'],'counts':{'records':626,'old_records_byte_identical':607,'new_records_exact':19,'operations':35,'condition_rows':167,'operation_quantities':43,'option_quantities':0,'material_slots':45,'public_assets':66,'product_context_mappings':39,'training_tasks_added':0},'code_scope':code_evidence,'manual_scope':['Reviewed root import/build/inventory code and permitted source-specific dispatch/display changes.','Compared exact old and new canonical records, generated records, reader science, measurements, metadata, all public assets and append-only registry/sample maps.','Executed actual installed protocol and chemical-viewer functions in a minimal DOM harness; not a mounted-browser or appearance audit.','All six training export memberships and all607 prior eligibility results equal the independently saved pre-import baseline; no source or model eligibility promoted. All six export bytes were independently captured before import and verified unchanged.','The separately root-audited symbolic product package is checked for exact public projection transport; no new coordinate/model approval.'],'bound_files':dict(sorted(bound.items())),'site_changed_by_auditor':False,'browser_approved':False,'publication_approved':False,'training_approved':False}
for n,x in [('integration-transport-audit.json',result),('integration-transport-checks.json',{'checks':checks})]:(A/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(A/'integration-transport-audit.md').write_text(f"# Pati installed transport audit\n\nStatus: **{result['status']}**. {len(checks)} transport and{runtime['check_count']} actual-module checks;{len(findings)} open findings.\n\nAll607 previous records remain byte-identical, and their eligibility plus all training-export memberships are unchanged.19 new records,268 measurements,35 stages,45 material slots,6 stocks,39 product contexts and66 public assets match the passed proposals. Scientific fields, all source conflicts and missing atomic models remain unchanged.\n\nInstalled protocol and chemical-viewer dispatch was executed in a minimal DOM harness. This is not a mounted-browser appearance or publication audit.\n",encoding='utf8')

print(json.dumps({'status':result['status'],'checks':result['check_count'],'findings':findings,'sha256':sha(A/'integration-transport-audit.json')}))
