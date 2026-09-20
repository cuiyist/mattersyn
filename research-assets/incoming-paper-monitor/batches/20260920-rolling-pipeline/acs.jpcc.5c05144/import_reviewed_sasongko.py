"""Root-only import of an independently audited Sasongko publication projection."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,copy
J=Path(__file__).resolve().parent;O=J/'site-integration-proposal';P=O/'v1';Q=J/'visuals/products';S=J.parents[4]/'recipe-atlas'
sys.path.insert(0,str(J.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text('utf8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def save(p,x):
 p=io_path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def cp(a,b):
 a=io_path(a);b=io_path(b);b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(a)==sha(b),str(b)
 else:b.write_bytes(a.read_bytes())
assert not (O/'site-import-manifest.json').exists()
auditpath=J/'site-integration-independent-audit/promotion-delta-audit.json';a=read(auditpath)
assert a['status']=='passed' and not a.get('open_findings') and not a.get('findings') and a['proposal_freeze_sha256']==sha(P/'package-freeze.json')
overlay=O/'reader-status-overlay'
assert a['reader_status_overlay_freeze_sha256']==sha(overlay/'package-freeze.json')
for f in read(overlay/'package-freeze.json')['files']:assert sha(overlay/f['path'])==f['sha256']
for f in read(P/'package-freeze.json')['files']:assert sha(P/f['path'])==f['sha256']
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==656
snap=O/'base-site-inputs'
def backup(rel):
 if not io_path(snap/rel).exists():cp(S/rel,snap/rel)
edits=[]
def plan(rel,before,after,count=1):
 assert (S/rel).read_text('utf8').count(before)==count,(rel,before)
 edits.append((rel,before,after,count))
rel='dist/protocol-visuals.mjs'
plan(rel,'import {buildFriedfeld2019Scene',"import {buildSasongko2025Scene,createSasongko2025Art,createSasongko2025ConditionGrid} from './sasongko2025-protocol.mjs';\nimport {buildFriedfeld2019Scene")
plan(rel,'const sourceArt=createFriedfeld2019Art','const sourceArt=createSasongko2025Art(o,r)||createFriedfeld2019Art')
plan(rel,'const friedfeld=buildFriedfeld2019Scene','const sasongko=buildSasongko2025Scene(o,r),friedfeld=buildFriedfeld2019Scene')
plan(rel,"el('p',friedfeld?.caption","el('p',sasongko?.caption||friedfeld?.caption")
plan(rel,'if(friedfeld||pati||','if(sasongko||friedfeld||pati||')
plan(rel,'const dl=friedfeld?createFriedfeld2019ConditionGrid','const dl=sasongko?createSasongko2025ConditionGrid(o,r):friedfeld?createFriedfeld2019ConditionGrid')
plan(rel,'&&!pati&&!friedfeld)for','&&!pati&&!friedfeld&&!sasongko)for')
plan(rel,"&&!pati&&!friedfeld){const env=el('div')","&&!pati&&!friedfeld&&!sasongko){const env=el('div')")
plan('scripts/build_dataset.py',"'dataset_version':'0.32.0'","'dataset_version':'0.33.0'",2)
plan('scripts/build_dataset.py',"('friedfeld2019','private_unapproved_reader')}","('friedfeld2019','private_unapproved_reader'),('sasongko2025','private_unapproved_reader')}")
plan('scripts/build_dataset.py',"r['lineage']['source_group']=='friedfeld2019'","r['lineage']['source_group'] in ('friedfeld2019','sasongko2025')",2)
# Expand the source-reviewed formamidinium abbreviation for periodic-table indexing;
# FA is CH(NH2)2, not a fluorine-containing empirical formula. Canonical wording stays literal.
plan('scripts/build_atlas.py',"COMPONENT_ELEMENTS={'MWNT':['C']}","COMPONENT_ELEMENTS={'MWNT':['C'],'FAPbI3':['C','H','N','Pb','I']}\nNAMES['FAPbI3']='Formamidinium lead iodide quantum dots'")
plan('scripts/build_atlas.py',"els=r['material'].get('elements') or re.findall('[A-Z][a-z]?',f)","els=r['material'].get('elements') or COMPONENT_ELEMENTS.get(f,re.findall('[A-Z][a-z]?',f))")
linkpatch=read(Q/'original-evidence-consumer-insertion.json')
assert sha(S/linkpatch['target'])==linkpatch['baseline_sha256']
plan(linkpatch['target'],linkpatch['anchor'],linkpatch['replacement'])
# Complete all namespace and copy-conflict checks before the first shared write.
public=read(P/'promotion-manifest.json')['public_assets']
for f in public:
 src=P/'dist'/f['public_path'];dest=S/'dist'/f['public_path']
 assert sha(src)==f['sha256']
 assert not io_path(dest).exists() or sha(dest)==f['sha256'],str(dest)
for src in (P/'records').glob('*.json'):assert not (S/'data/records'/src.name).exists()
assert not (S/'data/paper-reviews/sasongko2025.json').exists()
v=S/'dist/assets/chemical-registry';current_entries={e['id'] for e in read(v/'registry.json')['entries']}
new_entries=read(P/'molecules/registry-additions.json')['entries']+read(P/'products/registry-additions.json')['entries']
assert len({e['id'] for e in new_entries})==len(new_entries) and not ({e['id'] for e in new_entries}&current_entries)
for key,values in read(P/'molecules/bindings-additions.json').items():
 if key in ['recordBindings','bindingNotes','sourceRecordSha256']:assert not (set(values)&set(read(v/'bindings.json').get(key,{})))
assert not ({c['record_id'] for c in read(v/'solution-components.json')['contexts']}&{c['record_id'] for c in read(P/'molecules/solution-components-additions.json')['contexts']})
for key,values in read(P/'products/product-contexts-additions.json').items():
 if key in ['recordContexts','sourceNotices']:assert not (set(values)&set(read(v/'product-contexts.json').get(key,{})))
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 assert not (set(read(P/('record-'+section+'-measurements.json')))&set(read(S/'data/measurement-display.json')[key]))
for rel in ['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','data/inventory-summary.json']:
 backup(rel)
save(O/'base-record-hashes.json',old)
exports={p.name:sha(p) for p in (S/'dist/data/exports').glob('*.jsonl')};assert len(exports)==6;save(O/'base-training-export-hashes.json',exports)
for f in read(P/'promotion-manifest.json')['public_assets']:
 src=P/'dist'/f['public_path'];assert sha(src)==f['sha256'];cp(src,S/'dist'/f['public_path'])
for src in (P/'records').glob('*.json'):cp(src,S/'data/records'/src.name)
V=S/'dist/assets/chemical-registry';registry=read(V/'registry.json');known={e['id'] for e in registry['entries']}
for e in read(P/'molecules/registry-additions.json')['entries']+read(P/'products/registry-additions.json')['entries']:
 assert e['id'] not in known;known.add(e['id']);e.update(published=True,binding_approved=True);registry['entries'].append(e)
save(V/'registry.json',registry)
bindings=read(V/'bindings.json');delta=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 target=bindings.setdefault(key,{})
 for rid,value in delta[key].items():assert rid not in target;target[rid]=value
save(V/'bindings.json',bindings)
solutions=read(V/'solution-components.json');extra=read(P/'molecules/solution-components-additions.json')['contexts']
assert not ({c['record_id'] for c in solutions['contexts']}&{c['record_id'] for c in extra});solutions['contexts'].extend(extra);save(V/'solution-components.json',solutions)
products=read(V/'product-contexts.json');extra=read(P/'products/product-contexts-additions.json')
for key in ['recordContexts','sourceNotices']:
 for k,v in extra[key].items():assert k not in products[key];products[key][k]=v
save(V/'product-contexts.json',products)
display=read(S/'data/measurement-display.json')
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 for rid,ids in read(P/('record-'+section+'-measurements.json')).items():assert rid not in display[key];display[key][rid]=ids
save(S/'data/measurement-display.json',display)
reader=read(overlay/'reader/sasongko2025.json');reader['presentation_gates']['site_integration']=True;reader['publication_status']='Source-reviewed contribution integrated locally; browser and publication remain separate.';reader['audit_details']['promotion_audit_sha256']=sha(auditpath);save(S/'data/paper-reviews/sasongko2025.json',reader)
changes=[]
for rel,before,after,count in edits:
 backup(rel);p=S/rel;t=p.read_text('utf8');assert t.count(before)==count;p.write_text(t.replace(before,after),'utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text('utf8');n=t.replace('0.32.0-r1','0.33.0-r1').replace('0.32.0-r2','0.33.0-r2')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,'utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','promotion_audit_sha256':sha(auditpath),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(Q/'package-freeze.json'),'new_records':19,'old_records_preserved':656,'new_routes':1,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':13,'selected_source_crops':17,'apparatus_scenes':21,'named_source_contexts':33})
print(json.dumps({'integrated_records':19,'unchanged_old_records':656,'dataset_candidate':'0.33.0','published':False}))

