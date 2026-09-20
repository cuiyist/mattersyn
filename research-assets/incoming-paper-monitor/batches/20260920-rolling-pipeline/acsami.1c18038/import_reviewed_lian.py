"""Root-only import; both independently audited frozen projections are required."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';P=O/'v1';C=O/'product-context-v1';S=N.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(a)==sha(b),str(b)
 else:shutil.copy2(a,b)
assert not (O/'site-import-manifest.json').exists(),'Inspect prior import; do not repeat.'
audits={}
for name,proposal in [('promotion-delta-audit.json',P),('product-context-audit.json',C)]:
 path=N/'site-integration-independent-audit'/name;a=read(path)
 assert a['status']=='passed' and not a.get('open_findings') and a['proposal_freeze_sha256']==sha(proposal/'package-freeze.json')
 audits[name]=sha(path)
 for f in read(proposal/'package-freeze.json')['files']:assert sha(proposal/f['path'])==f['sha256']
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==530
snap=O/'base-site-inputs'
def backup(rel):
 if not (snap/rel).exists():cp(S/rel,snap/rel)
for rel in ['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','data/inventory-summary.json','dist/protocol-visuals.mjs','scripts/build_dataset.py']:
 backup(rel)
save(O/'base-record-hashes.json',old)
for a in read(P/'promotion-manifest.json')['public_assets']:
 src=P/'dist'/a['public_path'];assert sha(src)==a['sha256'];cp(src,S/'dist'/a['public_path'])
for src in (P/'records').glob('*.json'):cp(src,S/'data/records'/src.name)
V=S/'dist/assets/chemical-registry';registry=read(V/'registry.json');bindings=read(V/'bindings.json')
known={e['id'] for e in registry['entries']}
for e in read(P/'molecules/registry-additions.json')['entries']:
 assert e['id'] not in known;e['published']=True;registry['entries'].append(e)
delta=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 target=bindings.setdefault(key,{})
 for rid,value in delta[key].items():assert rid not in target;target[rid]=value
save(V/'registry.json',registry);save(V/'bindings.json',bindings)
solutions=read(V/'solution-components.json');extra=read(P/'molecules/solution-components-additions.json')['contexts']
assert not ({c['record_id'] for c in solutions['contexts']}&{c['record_id'] for c in extra})
solutions['contexts'].extend(extra);save(V/'solution-components.json',solutions)
products=read(V/'product-contexts.json');extra=read(C/'product-contexts-additions.json')
for key in ['recordContexts','sourceNotices']:
 for k,v in extra[key].items():assert k not in products[key];products[key][k]=v
save(V/'product-contexts.json',products)
display=read(S/'data/measurement-display.json')
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 for rid,ids in read(P/('record-'+section+'-measurements.json')).items():assert rid not in display[key];display[key][rid]=ids
save(S/'data/measurement-display.json',display)
reader=read(P/'reader/lian2021.json');reader['presentation_gates']['site_integration']=True;reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';reader['audit_details']['promotion_audit_sha256']=audits['promotion-delta-audit.json'];reader['audit_details']['symbolic_product_context_audit_sha256']=audits['product-context-audit.json'];save(S/'data/paper-reviews/lian2021.json',reader)
changes=[]
def edit(rel,before,after,count=1):
 p=S/rel;t=p.read_text(encoding='utf8');assert t.count(before)==count,(rel,before[:80],t.count(before));backup(rel);p.write_text(t.replace(before,after),encoding='utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
rel='dist/protocol-visuals.mjs'
edit(rel,"import {buildMorrison2017Scene", "import {buildLian2021Scene,createLian2021Art,createLian2021ConditionGrid} from './lian2021-protocol.mjs';\nimport {buildMorrison2017Scene")
edit(rel,'const sourceArt=createMorrison2017Art','const sourceArt=createLian2021Art(o,r)||createMorrison2017Art')
edit(rel,'const morrison=buildMorrison2017Scene','const lian=buildLian2021Scene(o,r),morrison=buildMorrison2017Scene')
edit(rel,"el('p',morrison?.caption","el('p',lian?.caption||morrison?.caption")
edit(rel,'if(morrison||evans||heo||nagasaki||ribeiro||norberg){','if(lian||morrison||evans||heo||nagasaki||ribeiro||norberg){')
edit(rel,'const dl=morrison?createMorrison2017ConditionGrid','const dl=lian?createLian2021ConditionGrid(o,r):morrison?createMorrison2017ConditionGrid')
edit(rel,'if(!aerosol&&!heo&&!evans&&!morrison)for','if(!aerosol&&!heo&&!evans&&!morrison&&!lian)for')
edit(rel,"if(!heo&&!evans&&!morrison){const env=el('div')","if(!heo&&!evans&&!morrison&&!lian){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.26.0'","'dataset_version':'0.27.0'",2)
edit('scripts/build_dataset.py',"('morrison2017','private_reader_pending_independent_review')}","('morrison2017','private_reader_pending_independent_review'),('lian2021','private_unapproved_reader_proposal')}")
versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.26.0-r1','0.27.0-r1')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,encoding='utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','audits':audits,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'new_records':16,'old_records_preserved':530,'new_routes':3,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':15,'selected_source_crops':53,'apparatus_scenes':21,'symbolic_product_contexts':22})
print(json.dumps({'integrated_records':16,'unchanged_old_records':530,'dataset_candidate':'0.27.0','published':False}))
