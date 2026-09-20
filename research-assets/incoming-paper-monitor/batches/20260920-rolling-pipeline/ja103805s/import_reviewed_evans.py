"""Root-only Evans import after independent review of the frozen promotion."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,shutil
E=Path(__file__).resolve().parent;O=E/'site-integration-proposal';P=O/'v2';S=E.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(a)==sha(b),('Unexpected existing file',str(b))
 else:shutil.copy2(a,b)
ap=argparse.ArgumentParser();ap.add_argument('--promotion-audit',type=Path,required=True);args=ap.parse_args()
assert not (O/'site-import-manifest.json').exists(),'Inspect prior import; do not repeat'
a=read(args.promotion_audit);assert a['status']=='passed' and not a.get('open_findings');assert a['proposal_freeze_sha256']==sha(P/'package-freeze.json')
freeze=read(P/'package-freeze.json')
for x in freeze['files']:assert sha(P/x['path'])==x['sha256'],x['path']
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==480
snap=O/'base-site-inputs'
snapshot=['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','data/measurement-display.json','data/inventory-summary.json','dist/protocol-visuals.mjs','dist/material-hub.mjs','dist/illustrated-record.mjs','dist/crystal-viewer.mjs','scripts/build_dataset.py','scripts/build_atlas.py','dist/source-evidence.mjs']
for rel in snapshot:cp(S/rel,snap/rel)
save(O/'base-record-hashes.json',old)
for x in read(P/'promotion-manifest.json')['public_assets']:
 src=P/'dist'/x['public_path'];assert sha(src)==x['sha256'];cp(src,S/'dist'/x['public_path'])
for src in (P/'records').glob('*.json'):cp(src,S/'data/records'/src.name)
V=S/'dist/assets/chemical-registry';registry=read(V/'registry.json');bindings=read(V/'bindings.json')
entries=read(P/'molecules/registry-additions.json')['entries'];known={e['id'] for e in registry['entries']}
for e in entries:assert e['id'] not in known;e['published']=True;registry['entries'].append(e)
delta=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 target=bindings.setdefault(key,{})
 for rid,v in delta[key].items():assert rid not in target;target[rid]=v
save(V/'registry.json',registry);save(V/'bindings.json',bindings)
reader=read(P/'reader/evans2010.json');reader['presentation_gates']['site_integration']=True;reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';reader['audit_details']['promotion_audit_sha256']=sha(args.promotion_audit);save(S/'data/paper-reviews/evans2010.json',reader)
display=read(S/'data/measurement-display.json');newmap=read(P/'record-structural-measurements.json');target=display.setdefault('record_structural_measurement_ids',{})
for rid,ids in newmap.items():assert rid not in target;target[rid]=ids
save(S/'data/measurement-display.json',display)
changes=[]
def edit(rel,oldtext,newtext,count=1):
 p=S/rel;t=p.read_text(encoding='utf8');assert t.count(oldtext)==count,(rel,oldtext[:70],t.count(oldtext));p.write_text(t.replace(oldtext,newtext),encoding='utf8');changes.append({'file':rel,'before':oldtext,'after':newtext,'occurrences':count})
rel='dist/protocol-visuals.mjs';p=S/rel;t=p.read_text(encoding='utf8');p.write_text("import {buildEvans2010Scene,createEvans2010Art,createEvans2010ConditionGrid} from './evans2010-protocol.mjs';\n"+t,encoding='utf8')
edit(rel,'const sourceArt=createHeo2003Art','const sourceArt=createEvans2010Art(o,r)||createHeo2003Art')
edit(rel,'const heo=buildHeo2003Scene','const evans=buildEvans2010Scene(o,r),heo=buildHeo2003Scene')
edit(rel,"el('p',heo?.caption","el('p',evans?.caption||heo?.caption")
edit(rel,'if(heo||nagasaki||ribeiro||norberg){','if(evans||heo||nagasaki||ribeiro||norberg){')
edit(rel,'const dl=heo?createHeo2003ConditionGrid','const dl=evans?createEvans2010ConditionGrid(o,r):heo?createHeo2003ConditionGrid')
edit(rel,'if(!aerosol&&!heo)for','if(!aerosol&&!heo&&!evans)for')
edit(rel,"if(!heo){const env=el('div')","if(!heo&&!evans){const env=el('div')")
rel='scripts/build_dataset.py'
edit(rel,"def is_structural(m):return m['property'] in DISPLAY['structural_properties'] or any(part in m['property'] for part in DISPLAY['structural_property_fragments'])","def is_structural(m,record_id=None):\n    scoped=DISPLAY.get('record_structural_measurement_ids',{})\n    if record_id in scoped:return m['id'] in scoped[record_id]\n    return m['property'] in DISPLAY['structural_properties'] or any(part in m['property'] for part in DISPLAY['structural_property_fragments'])")
edit(rel,'if is_structural(m)]',"if is_structural(m,r['record_id'])]")
edit(rel,'if not is_structural(m)]',"if not is_structural(m,r['record_id'])]")
edit(rel,"'dataset_version':'0.24.0'","'dataset_version':'0.25.0'",2)
rel='dist/material-hub.mjs'
edit(rel,'const structural=m=>displayCategories.structural_properties.includes(m.property)||displayCategories.structural_property_fragments.some(part=>m.property.includes(part));',"const structural=(m,r)=>Object.hasOwn(displayCategories.record_structural_measurement_ids||{},r.record_id)?displayCategories.record_structural_measurement_ids[r.record_id].includes(m.id):displayCategories.structural_properties.includes(m.property)||displayCategories.structural_property_fragments.some(part=>m.property.includes(part));")
edit(rel,'structural(m)===isStructure','structural(m,r)===isStructure')
# Cache revision only: these files are already authored/generated in the Site.
versioned=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.24.0-r1','0.25.0-r1')
 if t!=n:
  rel=p.relative_to(S).as_posix()
  if not (snap/rel).exists():cp(p,snap/rel)
  p.write_text(n,encoding='utf8');versioned.append(rel)
assert all(sha(S/'data/records'/name)==digest for name,digest in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versioned,'new_import':"import {buildEvans2010Scene,createEvans2010Art,createEvans2010ConditionGrid} from './evans2010-protocol.mjs';"})
save(O/'site-import-manifest.json',{'schema':'mattersyn.evans_site_import/1','at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_code_browser_release_checks','promotion_audit_sha256':sha(args.promotion_audit),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'new_records':32,'old_records_preserved':480,'new_routes':3,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':50,'selected_source_crops':25,'apparatus_scenes':46,'pending':['integration code audit','species9 final-structure adapter review','actual integrated browser checks','anonymous deployment verification']})
print(json.dumps({'integrated_records':32,'unchanged_old_records':480,'code_changes':len(changes),'candidate_dataset':'0.25.0','published':False}))
