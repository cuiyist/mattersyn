"""Root-only import; both independently audited frozen projections are required."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil,sys
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';P=O/'v1';C=N/'visuals/product-context';S=N.parents[4]/'recipe-atlas'
sys.path.insert(0,str(N.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def save(p,x):
 p=io_path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cp(a,b):
 a=io_path(a);b=io_path(b)
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(a)==sha(b),str(b)
 else:b.write_bytes(a.read_bytes())
assert not (O/'site-import-manifest.json').exists(),'Inspect prior import; do not repeat.'
# Preflight every deterministic code edit before copying any reviewed inputs.
for node in ast.walk(ast.parse(Path(__file__).read_text('utf8'))):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='edit':
  args=node.args
  rel='dist/protocol-visuals.mjs' if isinstance(args[0],ast.Name) else ast.literal_eval(args[0])
  before=ast.literal_eval(args[1]);count=ast.literal_eval(args[3]) if len(args)>3 else 1
  assert (S/rel).read_text('utf8').count(before)==count,(rel,before)
audits={}
for name,proposal,path in [
 ('promotion-delta-audit.json',P,N/'site-integration-independent-audit/promotion-delta-audit.json'),
 ('product-context-audit.json',C,N/'product-independent-audit/independent-audit.json')]:
 audit=read(path)
 bound_freeze=audit['inputs']['product_freeze']['sha256'] if name=='product-context-audit.json' else audit['proposal_freeze_sha256']
 assert audit['status']=='passed' and not audit.get('open_findings') and not audit.get('findings') and bound_freeze==sha(proposal/'package-freeze.json')
 audits[name]=sha(path)
 frozen=read(proposal/'package-freeze.json')
 if 'files' in frozen:
  for f in frozen['files']:assert sha(proposal/f['path'])==f['sha256']
 else:
  for path,h in frozen['bound_files'].items():assert sha(Path(path) if Path(path).is_absolute() else proposal/path)==h
old={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(old)==626
snap=O/'base-site-inputs'
def backup(rel):
 if not (snap/rel).exists():cp(S/rel,snap/rel)
for rel in ['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','data/inventory-summary.json','dist/protocol-visuals.mjs','scripts/build_dataset.py']:
 backup(rel)
save(O/'base-record-hashes.json',old)
exports={p.name:sha(p) for p in (S/'dist/data/exports').glob('*.jsonl')};assert len(exports)==6
save(O/'base-training-export-hashes.json',exports)
for a in read(P/'promotion-manifest.json')['public_assets']:
 src=P/'dist'/a['public_path'];assert sha(src)==a['sha256'];cp(src,S/'dist'/a['public_path'])
for src in (P/'records').glob('*.json'):cp(src,S/'data/records'/src.name)
V=S/'dist/assets/chemical-registry';registry=read(V/'registry.json');bindings=read(V/'bindings.json')
known={e['id'] for e in registry['entries']}
for e in read(P/'molecules/registry-additions.json')['entries']+read(P/'products/registry-additions.json')['entries']:
 assert e['id'] not in known;e.update(published=True,binding_approved=True);registry['entries'].append(e)
 # All product SVGs already copied from the passed public asset allowlist.
delta=read(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 target=bindings.setdefault(key,{})
 for rid,value in delta[key].items():assert rid not in target;target[rid]=value
save(V/'registry.json',registry);save(V/'bindings.json',bindings)
solutions=read(V/'solution-components.json');extra=read(P/'molecules/solution-components-additions.json')['contexts']
assert not ({c['record_id'] for c in solutions['contexts']}&{c['record_id'] for c in extra})
solutions['contexts'].extend(extra);save(V/'solution-components.json',solutions)
products=read(V/'product-contexts.json');extra=read(P/'products/product-contexts-additions.json')
for key in ['recordContexts','sourceNotices']:
 for k,v in extra[key].items():assert k not in products[key];products[key][k]=v
save(V/'product-contexts.json',products)
display=read(S/'data/measurement-display.json')
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 for rid,ids in read(P/('record-'+section+'-measurements.json')).items():assert rid not in display[key];display[key][rid]=ids
save(S/'data/measurement-display.json',display)
reader=read(P/'reader/friedfeld2019.json');reader['presentation_gates'].update(site_integration=True,symbolic_product_contexts=True);reader['remaining_gaps']=[x for x in reader['remaining_gaps'] if x!='Source, canonical/reader and visual audits passed. Integrated browser and publication gates remain separate; no qualified atomic model is admitted.'];reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';reader['audit_details']['promotion_audit_sha256']=audits['promotion-delta-audit.json'];reader['audit_details']['symbolic_product_context_audit_sha256']=audits['product-context-audit.json'];save(S/'data/paper-reviews/friedfeld2019.json',reader)
changes=[]
def edit(rel,before,after,count=1):
 p=S/rel;t=p.read_text('utf8');assert t.count(before)==count,(rel,before[:80],t.count(before));backup(rel);p.write_text(t.replace(before,after),'utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
rel='dist/protocol-visuals.mjs'
edit(rel,"import {buildPati2009Scene", "import {buildFriedfeld2019Scene,createFriedfeld2019Art,createFriedfeld2019ConditionGrid} from './friedfeld2019-protocol.mjs';\nimport {buildPati2009Scene")
edit(rel,'const sourceArt=createPati2009Art','const sourceArt=createFriedfeld2019Art(o,r)||createPati2009Art')
edit(rel,'const pati=buildPati2009Scene','const friedfeld=buildFriedfeld2019Scene(o,r),pati=buildPati2009Scene')
edit(rel,"el('p',pati?.caption","el('p',friedfeld?.caption||pati?.caption")
edit(rel,'if(pati||matuhina||','if(friedfeld||pati||matuhina||')
edit(rel,'const dl=pati?createPati2009ConditionGrid','const dl=friedfeld?createFriedfeld2019ConditionGrid(o,r):pati?createPati2009ConditionGrid')
edit(rel,'&&!matuhina&&!pati)for','&&!matuhina&&!pati&&!friedfeld)for')
edit(rel,"&&!matuhina&&!pati){const env=el('div')","&&!matuhina&&!pati&&!friedfeld){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.31.0'","'dataset_version':'0.32.0'",2)
edit('scripts/build_dataset.py',"('pati2009','private_unapproved_reader')}","('pati2009','private_unapproved_reader'),('friedfeld2019','private_unapproved_reader')}")
edit('scripts/build_dataset.py',"links=[dict(l,url=", "links=[dict(l,label=('Source document review' if r['lineage']['source_group']=='friedfeld2019' and l['relation']=='private_unapproved_reader' else l['label']),url=")
edit('scripts/build_dataset.py',"('pati2009','Named identity and printed formula retained separately; no molecular model approval.')}","('pati2009','Named identity and printed formula retained separately; no molecular model approval.'),('friedfeld2019','Printed identity/formula is not an approved graph, conformer or solution coordination model.')}")
versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text('utf8');n=t.replace('0.31.0-r1','0.32.0-r1').replace('0.31.0-r2','0.32.0-r2')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,'utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','audits':audits,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'new_records':30,'old_records_preserved':626,'new_routes':4,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':39,'new_phase_symbol_entries':14,'selected_source_crops':51,'apparatus_scenes':58,'symbolic_product_contexts':88,'record_sample_phase_contexts':88})
print(json.dumps({'integrated_records':30,'unchanged_old_records':626,'dataset_candidate':'0.32.0','published':False}))
