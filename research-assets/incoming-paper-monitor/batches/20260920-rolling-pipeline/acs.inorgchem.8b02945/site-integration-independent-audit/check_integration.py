import copy, datetime, hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
M=Path('[local path redacted]'); S=M/'recipe-atlas'; O=Path(__file__).parent; F=O.parent
P=F/'site-integration-proposal'; V=P/'v1'; B=P/'base-site-inputs'
sys.path.insert(0,str(M/'research-assets')); from sync_github_public import io_path
checks=[];bound={};deltas={}
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def read(p):bind(p);return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def ck(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),**({'detail':detail} if detail is not None else {})})
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'old':a,'new':b}]
 if isinstance(a,dict):
  out=[]
  for k in a.keys()|b.keys():
   if k not in a:out.append({'path':p+'/'+k,'added':b[k]})
   elif k not in b:out.append({'path':p+'/'+k,'removed':a[k]})
   else:out+=diff(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'old':a,'new':b}]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [{'path':p,'old':a,'new':b}]

audit=read(O/'promotion-delta-audit.json');freeze=read(V/'package-freeze.json')
ck('audited exact frozen proposal',audit['status']=='passed' and audit['proposal_freeze_sha256']==sha(V/'package-freeze.json')=='1714710fcab2068a7b9dc13e0392ccb8dd708cc661961c324ef969c6fee34612')
for x in freeze['files']:ck('frozen proposal member '+x['path'],bind(V/x['path'])==x['sha256'])
man=read(V/'promotion-manifest.json'); imp=read(P/'site-import-manifest.json');bind(F/'import_reviewed_friedfeld.py')
ck('import receipt binds proposal audit',imp['audits']['promotion-delta-audit.json']==sha(O/'promotion-delta-audit.json') and imp['proposal_freeze_sha256']==sha(V/'package-freeze.json'))
base=read(P/'base-record-hashes.json'); exports=read(P/'base-training-export-hashes.json')
ck('626 base record hashes',len(base)==626)
for name,h in base.items():ck('old record unchanged '+name,bind(S/'data/records'/name)==h)
ck('six old training exports',len(exports)==6)
for name,h in exports.items():ck('old training export unchanged '+name,bind(S/'dist/data/exports'/name)==h)
records={p.stem:read(p) for p in sorted((V/'records').glob('*.json'))}
ck('exact total record inventory',set(p.name for p in (S/'data/records').glob('*.json'))==set(base)|{r+'.json' for r in records})
for rid,r in records.items():
 ck('canonical import exact bytes '+rid,bind(S/'data/records'/(rid+'.json'))==sha(V/'records'/(rid+'.json')))
 ck('public record exact bytes '+rid,bind(S/'dist/data/records'/(rid+'.json'))==sha(V/'records'/(rid+'.json')))
 ck('training stays unrequested '+rid,r['quality']['requested_tasks']==[] and r['structure_assets']==[])
 html=S/'dist/records'/(rid+'.html');bind(html)
 ck('record HTML source review navigation '+rid,'paper-review.html?id=friedfeld2019' in io_path(html).read_text(encoding='utf-8'))

before=read(V/'reader/friedfeld2019.json');cur=read(S/'data/paper-reviews/friedfeld2019.json');expected=copy.deepcopy(before)
expected['presentation_gates'].update(site_integration=True,symbolic_product_contexts=True)
stale='Source, canonical/reader and visual audits passed. Integrated browser and publication gates remain separate; no qualified atomic model is admitted.'
expected['remaining_gaps']=[x for x in expected['remaining_gaps'] if x!=stale]
expected['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.'
expected['audit_details']['promotion_audit_sha256']=sha(O/'promotion-delta-audit.json')
expected['audit_details']['symbolic_product_context_audit_sha256']=sha(F/'product-independent-audit/independent-audit.json')
deltas['reader']=diff(before,cur)
ck('reader exact allowed integration metadata only',expected==cur,diff(expected,cur))
ck('all reader scientific cards and links unchanged',cur['reader_sections']==before['reader_sections'])
pubreader=read(S/'dist/data/paper-reviews/friedfeld2019.json');copy_pub=copy.deepcopy(pubreader);label=copy_pub.pop('review_scope_label',None)
ck('public reader same plus scope label',copy_pub==cur and label=='Complete supplied main + matched SI review')
ck('browser/live not claimed at initial integration checkpoint',cur['presentation_gates']['browser_render'] is False and cur['presentation_gates']['publication'] is False)

for a in man['public_assets']:ck('approved actual public asset '+a['public_path'],bind(S/'dist'/a['public_path'])==sha(V/'dist'/a['public_path'])==a['sha256'])
allowed={a['public_path'] for a in man['public_assets']}
actual={p.relative_to(S/'dist').as_posix() for p in (S/'dist/assets').rglob('*') if p.is_file() and ('friedfeld2019' in p.as_posix().lower())}
actual.add('friedfeld2019-protocol.mjs')
ck('162 scoped assets exact allowlist, no extra source attachments',actual==allowed,{'missing':sorted(allowed-actual),'extra':sorted(actual-allowed)})
for rel in allowed:
 p=S/'dist'/rel
 if p.suffix in ['.json','.mjs','.svg']:
  ck('new public asset no private-source references '+rel,not re.search(r'[A-Z]:[\\/]|file://|/Users/|source-render|complete-source-payload',io_path(p).read_text(encoding='utf-8')))

R='dist/assets/chemical-registry'
for name in ['registry.json','bindings.json','solution-components.json','product-contexts.json']:
 old=read(B/R/name);new=read(S/R/name);e=copy.deepcopy(old)
 if name=='registry.json':
  additions=read(V/'molecules/registry-additions.json')['entries']+read(V/'products/registry-additions.json')['entries']
  for entry in additions:
   x=copy.deepcopy(entry);x.update(published=True,binding_approved=True);e['entries'].append(x)
  ck('53 unique scoped registry additions',len(additions)==53 and len({x['id'] for x in new['entries']})==len(new['entries']))
 elif name=='bindings.json':
  additions=read(V/'molecules/bindings-additions.json')
  for key in ['recordBindings','bindingNotes','sourceRecordSha256']:e.setdefault(key,{}).update(additions[key])
 elif name=='solution-components.json':e['contexts']+=read(V/'molecules/solution-components-additions.json')['contexts']
 else:
  additions=read(V/'products/product-contexts-additions.json')
  for key in ['recordContexts','sourceNotices']:e[key].update(additions[key])
 ck('exact additive registry transport and all prior data unchanged '+name,e==new,diff(e,new))
display=read(B/'data/measurement-display.json');actualdisplay=read(S/'data/measurement-display.json')
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:display[key].update(read(V/('record-'+section+'-measurements.json')))
ck('exact additive display maps',display==actualdisplay)
ck('generated display map copy',read(S/'dist/data/measurement-display.json')==actualdisplay)

cd=read(P/'code-delta.json')
for p in B.rglob('*'):
 if not p.is_file() or p.suffix not in ['.py','.mjs','.html']:continue
 rel=p.relative_to(B).as_posix();bind(p);bind(S/rel);text=io_path(p).read_text(encoding='utf-8')
 for d in cd['changes']:
  if d['file']==rel:
   ck('code delta occurrence '+rel+' '+d['before'],text.count(d['before'])==d['occurrences']);text=text.replace(d['before'],d['after'])
 if rel in cd['cache_revision_files']:text=text.replace('0.31.0-r1','0.32.0-r1').replace('0.31.0-r2','0.32.0-r2')
 if rel not in ['dist/dataset.html','dist/inventory.html']:ck('exact code/cache replay '+rel,text==io_path(S/rel).read_text(encoding='utf-8'))
dispatch=read(O/'integration-dispatch-checks.json');bind(O/'check_integration_dispatch.mjs')
ck('actual imported source-scoped factory checks',dispatch['passed'] and dispatch['friedfeld_operation_instances']==58 and dispatch['unrelated_operation_instances']==1899)

ds=read(S/'dist/data/dataset-manifest.json');idx={r['record_id']:r for r in ds['records']}
ck('v0.32.0 and656 generated records',ds['dataset_version']=='0.32.0' and ds['record_count']==656 and len(idx)==656)
for rid,r in records.items():
 # Dataset manifest uses canonical JSON-content digest, not serialized file bytes.
 ck('manifest record canonical content digest '+rid,idx[rid]['record_sha256']==hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
 ck('manifest zero training eligibility '+rid,all(not t['eligible'] for t in idx[rid]['eligibility'].values()))
inventory=read(S/'data/inventory-summary.json');ck('inventory public exact copy',read(S/'dist/data/inventory-summary.json')==inventory)
sm=inventory['summary'];ck('inventory656records122routes49hubs',sm['canonical_records']==656 and sm['synthesis_route_variant_records']==122 and sm['public_material_hubs']==49)
baseinv=read(B/'data/inventory-summary.json')
ck('training totals unchanged',inventory['training_eligibility']==baseinv['training_eligibility'])
ck('no exact structure pairs or independent-experiment inference',sm['verified_exact_structure_recipe_pairs']==0 and sm['independent_experiment_count'] is None)
mi=read(S/'dist/data/materials-index.json');ck('49 material hub entries',len(mi['materials'])==49)
inp=read(S/'dist/data/materials/inp-9eb58d.json');routes={rid for rid,r in records.items() if r['reader_role']=='synthesis_route'}
ck('exact four Friedfeld routes reachable in InP hub',{r for r in inp['direct_record_ids'] if r.startswith('friedfeld-')}==routes and len(routes)==4)
ck('InP evidence inventory retains direct routes without blanket material assignment',{r['record_id'] for r in inp['evidence_records'] if r['record_id'].startswith('friedfeld-')}==routes)
ck('all declared route context records available',set(cur['route_evidence_contexts'])==routes and all(rid in records and (S/'dist/data/records'/(rid+'.json')).exists() for ids in cur['route_evidence_contexts'].values() for rid in ids))
lib=read(S/'dist/data/library-index.json');lp=[r for r in lib['papers'] if r.get('doi')=='10.1021/acs.inorgchem.8b02945']
ck('one source library review with all30 records',len(lp)==1 and set(lp[0]['reviewedRecordIds'])==set(records) and lp[0]['fullDocumentReview']['pages']==33)
if lp:bind(S/'dist/data/papers'/(lp[0]['id']+'.json'))
ri=read(S/'dist/data/paper-review-index.json');rr=[r for r in ri['papers'] if r['id']=='friedfeld2019']
ck('one reader index with exact scope',len(rr)==1 and rr[0]['review_scope']=='supplied_main_and_matched_si' and set(rr[0]['record_ids'])==set(records))
bind(S/'scripts/dataset_lib.py');bind(S/'scripts/build_paper_reviews.py');bind(S/'scripts/build_atlas.py');bind(Path(__file__))
sys.path.insert(0,str(S/'scripts'));import dataset_lib,build_paper_reviews
for rid,r in records.items():
 ck('current imported record validator '+rid,not dataset_lib.validate_record(read(S/'data/records'/(rid+'.json'))))
 ck('current actual zero eligibility '+rid,all(not t['eligible'] for t in dataset_lib.eligibility(r).values()))
errors=build_paper_reviews.validate(cur);ck('actual integrated reader validator',not errors,errors)
result={'status':'passed' if all(c['pass'] for c in checks) else 'findings_required','author':'/root','auditor':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_freeze_sha256':sha(V/'package-freeze.json'),'checks':checks,'dispatch_check_count':dispatch['executed'],'reader_delta':deltas['reader'],'bound_files':bound,'summary':{'executed':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']]}}
io_path(O/'integration-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
