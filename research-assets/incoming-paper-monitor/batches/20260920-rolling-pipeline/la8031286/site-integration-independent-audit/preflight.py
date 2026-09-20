"""Read-only Site preflight; writes only private independent baseline/audit files."""
from pathlib import Path
import json,hashlib,sys,datetime,shutil,importlib.util
A=Path(__file__).resolve().parent;N=A.parent;S=Path('[local path redacted]');sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'scripts'))
from dataset_lib import eligibility,validate_record
from review_scope import source_review_scope
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[];bound={}
def ck(label,v):checks.append({'check':label,'passed':bool(v)})
def bind(p):p=Path(p);bound[str(p)]=sha(p);return read(p)
baseline=A/'independent-baseline.json'
if not baseline.exists():
 records={p.stem:{'sha256':sha(p),'eligibility':eligibility(read(p))}for p in sorted((S/'data/records').glob('*.json'))}
 files={}
 paths=['scripts/build_dataset.py','scripts/build_paper_reviews.py','scripts/build_reader_views.py','scripts/dataset_lib.py','scripts/schema_definition.py','scripts/review_scope.py','dist/chemical-viewer.mjs','dist/crystal-viewer.mjs','dist/protocol-visuals.mjs','dist/quantity-value.mjs','dist/source-evidence.mjs','dist/material-hub.mjs','dist/illustrated-guide.css','dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','data/inventory-summary.json','dist/data/dataset-manifest.json']
 paths += [p.relative_to(S).as_posix()for p in sorted((S/'dist/data/exports').glob('*.jsonl'))]
 for rel in paths:
  p=S/rel;dest=A/'independent-baseline'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);files[rel]=sha(p)
 write(baseline,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'pre_import_snapshot','records':records,'files':files,'record_count':len(records),'full_export_bytes_preserved':True,'scope':'Independent read-only current Site capture before Pati import; all canonical hashes and complete six training export byte snapshots.'})
base=bind(baseline);ck('607 prior canonical records',base['record_count']==607)
for rid,x in base['records'].items():ck('Baseline remains pre-import '+rid,sha(S/'data/records'/(rid+'.json'))==x['sha256'])
identity=bind(N/'intake-identity.json');ck('Current intake generation1',identity['source_generation']==1 and identity['bundle_sha256']=='b90762f8d91a417cdecfdd62da360d015e6dc40902529806048dfc5635a28db3')
for x in identity['file_copies']:bound[x['source_path']]=sha(x['source_path']);ck('Original still equals retained generation '+x['role'],sha(x['source_path'])==x['sha256'])
pairs=[('source',N/'package-freeze.json',N/'source-independent-audit/independent-audit.json'),('canonical',N/'canonical-proposal/v2/package-manifest.json',N/'canonical-reader-independent-audit/independent-audit-v2.json'),('molecules',N/'visuals/molecules/annotation-correction-v2/package-freeze.json',N/'visuals/molecules-independent-audit/independent-audit-v2.json'),('apparatus',N/'visuals/apparatus/package-freeze.json',N/'visuals/apparatus-independent-audit/independent-audit.json'),('product_context',N/'visuals/product-context/package-freeze.json',N/'product-context-independent-audit/independent-audit.json')]
summary=[]
for label,fp,ap in pairs:
 f=bind(fp);a=bind(ap);ck(label+' separate passed audit',a['status']=='passed')
 ah=a.get('proposal_freeze_sha256',a.get('source_freeze_sha256',a.get('package_manifest_sha256')))
 if ah:ck(label+' exact audit freeze pointer',ah==sha(fp))
 for p,h in f['bound_files'].items():bound[p]=sha(p);ck(label+' frozen bytes '+p,sha(p)==h)
 summary.append({'scope':label,'freeze_path':str(fp),'freeze_sha256':sha(fp),'audit_path':str(ap),'audit_sha256':sha(ap)})
canonical={p.stem:read(p)for p in (N/'canonical-proposal/v2').glob('pati-2009-*.json')};ck('19 canonical records',len(canonical)==19)
for rid,r in canonical.items():
 ck('Current schema '+rid,not validate_record(r));ck('Zero current training admission '+rid,not any(v['eligible']for v in eligibility(r).values()))
reader=bind(N/'public-review-proposal/v2/pati2009.json');ck('Current supported main-SI contract',source_review_scope(reader)['scope']=='supplied_main_and_matched_si')
fixture=A/'reader-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True)
for rid in canonical:shutil.copyfile(N/'canonical-proposal/v2'/(rid+'.json'),fixture/'data/records'/(rid+'.json'))
assets={}
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):assets[x['public_asset']]=x.get('public_asset_sha256',x.get('sha256'))
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader)
available={sha(p):p for p in (N/'reader-assets').rglob('*')if p.is_file()and p.suffix in ['.png','.svg','.jpg']}
for rel,h in assets.items():
 ck('Selected asset exists '+rel,h in available)
 if h in available:dest=fixture/'dist'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(available[h],dest)
spec=importlib.util.spec_from_file_location('pati_independent_build_paper_reviews',S/'scripts/build_paper_reviews.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=fixture
errors=module.validate(reader);ck('Actual current reader consumer validation',not errors)
for rel in ['scripts/build_paper_reviews.py','scripts/dataset_lib.py','scripts/schema_definition.py','scripts/review_scope.py']:bound[str(S/rel)]=sha(S/rel)
result={'schema':'mattersyn-independent-integration-preflight/1','auditor':'/root/norberg2004_extract','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed'if all(x['passed']for x in checks)else'open_findings','generation_check':'Rehashed both actual supplied PDFs; exact generation1 bytes unchanged. No fresh full-corpus classification is claimed.','checked_boundaries':summary,'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'reader_errors':errors,'fixture_selected_assets':len(assets),'checks':checks,'bound_files':bound,'scope':'Prior science/audit hash preflight and current consumer/schema compatibility only. No promotion, Site import, browser or publication approval.'}
write(A/'preflight.json',result)
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':result['failures'],'baseline_sha256':sha(baseline),'preflight_sha256':sha(A/'preflight.json'),'reader_errors':errors}))
