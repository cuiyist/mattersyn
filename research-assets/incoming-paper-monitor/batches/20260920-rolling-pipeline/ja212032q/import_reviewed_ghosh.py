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
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==546
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
reader=read(P/'reader/ghosh2012.json');reader['presentation_gates']['site_integration']=True;reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';reader['audit_details']['promotion_audit_sha256']=audits['promotion-delta-audit.json'];reader['audit_details']['symbolic_product_context_audit_sha256']=audits['product-context-audit.json'];save(S/'data/paper-reviews/ghosh2012.json',reader)
changes=[]
def edit(rel,before,after,count=1):
 p=S/rel;t=p.read_text(encoding='utf8');assert t.count(before)==count,(rel,before[:80],t.count(before));backup(rel);p.write_text(t.replace(before,after),encoding='utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
rel='dist/protocol-visuals.mjs'
edit(rel,"import {buildLian2021Scene", "import {buildGhosh2012Scene,createGhosh2012Art,createGhosh2012ConditionGrid} from './ghosh2012-protocol.mjs';\nimport {buildLian2021Scene")
edit(rel,'const sourceArt=createLian2021Art','const sourceArt=createGhosh2012Art(o,r)||createLian2021Art')
edit(rel,'const lian=buildLian2021Scene','const ghosh=buildGhosh2012Scene(o,r),lian=buildLian2021Scene')
edit(rel,"el('p',lian?.caption","el('p',ghosh?.caption||lian?.caption")
edit(rel,'if(lian||morrison||evans||heo||nagasaki||ribeiro||norberg){','if(ghosh||lian||morrison||evans||heo||nagasaki||ribeiro||norberg){')
edit(rel,'const dl=lian?createLian2021ConditionGrid','const dl=ghosh?createGhosh2012ConditionGrid(o,r):lian?createLian2021ConditionGrid')
edit(rel,'if(!aerosol&&!heo&&!evans&&!morrison&&!lian)for','if(!aerosol&&!heo&&!evans&&!morrison&&!lian&&!ghosh)for')
edit(rel,"if(!heo&&!evans&&!morrison&&!lian){const env=el('div')","if(!heo&&!evans&&!morrison&&!lian&&!ghosh){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.27.0'","'dataset_version':'0.28.0'",2)

edit('scripts/build_dataset.py',"('lian2021','private_unapproved_reader_proposal')}","('lian2021','private_unapproved_reader_proposal'),('ghosh2012','private_unapproved_reader_proposal')}")
edit('scripts/build_dataset.py',"record['lineage']['source_group']=='lian2021' and n=='Chemical/atomic visual binding is separately pending.'", "(record['lineage']['source_group'],n) in {('lian2021','Chemical/atomic visual binding is separately pending.'),('ghosh2012','Source-qualified identity only; molecular/product visual binding is separately pending.')}")
edit('scripts/build_dataset.py',"prefix='Source sample object: '","prefix='Source context object: ' if record['lineage']['source_group']=='ghosh2012' else 'Source sample object: '")
edit('scripts/build_dataset.py',"record['lineage']['source_group']!='lian2021' or not note.startswith(prefix)","record['lineage']['source_group'] not in {'lian2021','ghosh2012'} or not note.startswith(prefix)")

versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.27.0-r1','0.28.0-r1').replace('0.27.0-r2','0.28.0-r2')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,encoding='utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','audits':audits,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'new_records':21,'old_records_preserved':546,'new_routes':5,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':25,'selected_source_crops':36,'apparatus_scenes':33,'symbolic_product_contexts':45})
print(json.dumps({'integrated_records':21,'unchanged_old_records':546,'dataset_candidate':'0.28.0','published':False}))
