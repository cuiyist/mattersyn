"""Root-only import; both independently audited frozen projections are required."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';P=O/'v1';C=N/'product-context-proposal';S=N.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(a)==sha(b),str(b)
 else:shutil.copy2(a,b)
assert not (O/'site-import-manifest.json').exists(),'Inspect prior import; do not repeat.'
audits={}
for name,proposal,path in [
 ('promotion-delta-audit.json',P,N/'site-integration-independent-audit/promotion-delta-audit.json'),
 ('product-context-audit.json',C,N/'product-context-independent-audit/independent-audit.json')]:
 audit=read(path)
 assert audit['status']=='passed' and not audit.get('open_findings') and audit['proposal_freeze_sha256']==sha(proposal/'package-freeze.json')
 audits[name]=sha(path)
 frozen=read(proposal/'package-freeze.json')
 if 'files' in frozen:
  for f in frozen['files']:assert sha(proposal/f['path'])==f['sha256']
 else:
  for path,h in frozen['bound_files'].items():assert sha(Path(path))==h
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==567
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
for e in read(P/'molecules/registry-additions.json')['entries']+read(C/'registry-additions.json')['entries']:
 assert e['id'] not in known;e.update(published=True,binding_approved=True);registry['entries'].append(e)
 if e['id'].endswith('-observed-phase-symbol'):
  src=C/e['svgPath'];assert sha(src)==e['assetHashes']['svgPath'];cp(src,V/e['svgPath'])
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
reader=read(P/'reader/sommer2020.json');reader['presentation_gates'].update(site_integration=True,symbolic_product_contexts=True);reader['remaining_gaps']=[x for x in reader['remaining_gaps'] if x!='Source, canonical/reader, molecular and apparatus audits passed. Symbolic product-context binding, integrated browser and publication gates remain separate.'];reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';reader['audit_details']['promotion_audit_sha256']=audits['promotion-delta-audit.json'];reader['audit_details']['symbolic_product_context_audit_sha256']=audits['product-context-audit.json'];save(S/'data/paper-reviews/sommer2020.json',reader)
changes=[]
def edit(rel,before,after,count=1):
 p=S/rel;t=p.read_text(encoding='utf8');assert t.count(before)==count,(rel,before[:80],t.count(before));backup(rel);p.write_text(t.replace(before,after),encoding='utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
rel='dist/protocol-visuals.mjs'
edit(rel,"import {buildGhosh2012Scene", "import {buildSommer2020Scene,createSommer2020Art,createSommer2020ConditionGrid} from './sommer2020-protocol.mjs';\nimport {buildGhosh2012Scene")
edit(rel,'const sourceArt=createGhosh2012Art','const sourceArt=createSommer2020Art(o,r)||createGhosh2012Art')
edit(rel,'const ghosh=buildGhosh2012Scene','const sommer=buildSommer2020Scene(o,r),ghosh=buildGhosh2012Scene')
edit(rel,"el('p',ghosh?.caption","el('p',sommer?.caption||ghosh?.caption")
edit(rel,'if(ghosh||lian||','if(sommer||ghosh||lian||')
edit(rel,'const dl=ghosh?createGhosh2012ConditionGrid','const dl=sommer?createSommer2020ConditionGrid(o,r):ghosh?createGhosh2012ConditionGrid')
edit(rel,'&&!lian&&!ghosh)for','&&!lian&&!ghosh&&!sommer)for')
edit(rel,"&&!lian&&!ghosh){const env=el('div')","&&!lian&&!ghosh&&!sommer){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.28.0'","'dataset_version':'0.29.0'",2)
edit('scripts/build_dataset.py',"('ghosh2012','private_unapproved_reader_proposal')}","('ghosh2012','private_unapproved_reader_proposal'),('sommer2020','private_unapproved_reader_proposal')}")
edit('scripts/build_dataset.py',"('ghosh2012','Source-qualified identity only; molecular/product visual binding is separately pending.')}","('ghosh2012','Source-qualified identity only; molecular/product visual binding is separately pending.'),('sommer2020','Chemical identity and source role only; independently qualified molecular/component bindings remain pending.')}")
edit('scripts/build_dataset.py',"record['lineage']['source_group']=='ghosh2012' else", "record['lineage']['source_group'] in {'ghosh2012','sommer2020'} else")
edit('scripts/build_dataset.py',"not in {'lian2021','ghosh2012'}", "not in {'lian2021','ghosh2012','sommer2020'}")

versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.28.0-r1','0.29.0-r1').replace('0.28.0-r2','0.29.0-r2')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,encoding='utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','audits':audits,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'new_records':19,'old_records_preserved':567,'new_routes':3,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':28,'new_phase_symbol_entries':3,'selected_source_crops':20,'apparatus_scenes':31,'symbolic_product_contexts':77,'record_sample_phase_contexts':45})
print(json.dumps({'integrated_records':19,'unchanged_old_records':567,'dataset_candidate':'0.29.0','published':False}))
