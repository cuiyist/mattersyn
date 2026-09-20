"""Root-only import, gated on distinct apparatus/product/promotion audits."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,shutil
H=Path(__file__).resolve().parent;O=H/'site-integration-proposal'
S=Path(r'[local path redacted]')
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cp(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert sha(src)==sha(dst),('Different existing file',str(dst))
 else:shutil.copy2(src,dst)
def edit(path,old,new):
 text=path.read_text(encoding='utf8');assert old in text,(str(path),old[:80]);path.write_text(text.replace(old,new),encoding='utf8')
ap=argparse.ArgumentParser();ap.add_argument('--product-audit',required=True);ap.add_argument('--promotion-audit',required=True);args=ap.parse_args()
assert not (O/'site-import-manifest.json').exists(),'Inspect prior import instead of repeating mutations.'
audit_files=[H/'visuals/apparatus/audit-v1/apparatus-source-audit.json',Path(args.product_audit),Path(args.promotion_audit)]
for p in audit_files:
 a=read(p);assert a['status'].startswith('passed') and not a.get('open_findings'),(str(p),a.get('status'))
 bound=a.get('bound_files',{})
 if isinstance(bound,list):bound={row['path']:row['sha256'] for row in bound}
 for filename,digest in bound.items():
  path=Path(filename);path=path if path.is_absolute() else p.parent/path
  assert sha(path)==digest,('Stale independent audit input',str(path))
promotion=read(O/'promotion-proposal-manifest.json')
assert {p.stem for p in (O/'records').glob('*.json')}=={row['record_id'] for row in promotion['records']}
for row in promotion['records']:assert sha(O/'records'/(row['record_id']+'.json'))==row['proposal_sha256']
before_records={p.name:sha(p) for p in (S/'data/records').glob('*.json')};assert len(before_records)==470
snap=O/'base-site-inputs'
for rel in ['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','data/inventory-summary.json','data/measurement-display.json','dist/protocol-visuals.mjs','dist/crystal-viewer.mjs','dist/source-evidence.mjs','dist/illustrated-record.mjs','dist/illustrated-guide.css','scripts/build_dataset.py','scripts/build_atlas.py','scripts/schema_definition.py','scripts/check_quality.py']:
 cp(S/rel,snap/rel)
write(O/'base-record-hashes.json',before_records)
# Exact source-specific apparatus and reviewed public product/SI files.
A=H/'visuals/apparatus/v1';f=read(A/'package-freeze.json')
for row in f['files']:assert sha(A/row['path'])==row['sha256']
cp(A/'heo2003-protocol.mjs',S/'dist/heo2003-protocol.mjs')
manifest=read(H/'visuals/products/package-manifest.json')
public_files={
 'visuals/products/heo2003-average-viewer.mjs':'heo2003-average-viewer.mjs',
 'visuals/products/heo2003-viewers.css':'heo2003-viewers.css',
 'visuals/products/heo2003-average-view.json':'assets/crystal-references/heo2003-average-view.json',
 'visuals/products/heo2003-average-position-occupancy.cif':'assets/crystal-references/heo2003-average-position-occupancy.cif',
 'visuals/products/heo2003-average-cell.svg':'assets/crystal-references/heo2003-average-cell.svg',
 'si-reader-proposal/heo2003-reflection-viewer.mjs':'heo2003-reflection-viewer.mjs',
 'si-reader-proposal/heo2003-reflections.json':'assets/heo2003/heo2003-reflections.json',
 'si-reader-proposal/heo2003-reflections.tsv':'assets/heo2003/heo2003-reflections.tsv',
}
for src,dst in public_files.items():assert sha(H/src)==manifest['public_assets'][src];cp(H/src,S/'dist'/dst)
selected=read(H/'publication-projection-audit/publication-projection-proposal.json')['retained_selected_assets']
assert {p.relative_to(O/'dist').as_posix() for p in (O/'dist').rglob('*') if p.is_file()}=={row['public_path'] for row in selected}
for row in selected:
 p=O/'dist'/row['public_path'];assert sha(p)==row['sha256'];cp(p,S/'dist'/row['public_path'])
# Qualified model bindings stay in a dedicated source-average registry.
model=read(H/'visuals/products/registry-entry-proposal.json');model['binding_approved']=True
model['independent_audit_sha256']=sha(Path(args.product_audit))
write(S/'dist/assets/crystal-references/source-average-models.json',{'schema':'mattersyn.source-average-models/1','entries':[model]})
V=S/'dist/assets/chemical-registry';reg=read(V/'registry.json');bindings=read(V/'bindings.json');existing={e['id'] for e in reg['entries']}
for original in read(H/'canonical-binding-proposal/revision-2/registry-additions-effective.json')['entries']:
 e=copy.deepcopy(original);assert e['id'] not in existing
 for key in ['svgPath','model2dPath','model3dPath']:
  if e.get(key):
   src=H/'visuals/molecules'/e[key];assert sha(src)==e['assetHashes'][key];cp(src,V/e[key])
 e.update(independentScientificAudit='passed_source_scoped_reference_and_binding_audit',binding_approved=True,published=True,eligible_training=False)
 reg['entries'].append(e);existing.add(e['id'])
delta=read(H/'canonical-binding-proposal/revision-3/bindings-proposal.json')
for rid,bb in delta['recordBindings'].items():
 assert rid not in bindings['recordBindings'];assert set(bb.values())<=existing
 bindings['recordBindings'][rid]=bb;notes=copy.deepcopy(delta['bindingNotes'][rid])
 for note in notes.values():
  note.update(binding_approved=True,independent_scientific_audit='Passed source-scoped molecular and binding audit. Canonical scientific fields unchanged in publication promotion.')
 bindings.setdefault('bindingNotes',{})[rid]=notes
 bindings.setdefault('sourceRecordSha256',{})[rid]=sha(O/'records'/(rid+'.json'))
for p in (O/'records').glob('*.json'):
 r=read(p);bindings['recordBindings'].setdefault(r['record_id'],{})
 assert set(bindings['recordBindings'][r['record_id']])=={m['id'] for m in r['materials']}
 bindings.setdefault('sourceRecordSha256',{})[r['record_id']]=sha(p)
write(V/'registry.json',reg);write(V/'bindings.json',bindings)
for p in (O/'records').glob('*.json'):cp(p,S/'data/records'/p.name)
reader=read(O/'promoted-reader/heo2003.json')
reader['presentation_gates'].update(apparatus_bindings=True,average_position_occupancy_binding=True,site_integration=True)
reader['publication_status']='Source-reviewed contribution integrated; live deployment tracked separately.'
reader['audit_details']['apparatus_audit_sha256']=sha(audit_files[0]);reader['audit_details']['product_reflection_audit_sha256']=sha(audit_files[1]);reader['audit_details']['promotion_audit_sha256']=sha(audit_files[2])
write(S/'data/paper-reviews/heo2003.json',reader)
# Classify source-bound structural measurements for the final-structures section.
display=read(S/'data/measurement-display.json');records={p.stem:read(p) for p in (O/'records').glob('*.json')};props=set()
for sec in reader['reader_sections']:
 if sec['id']=='structures':
  for item in sec['items']:
   for link in item.get('canonical_links',[]):
    parts=link['json_pointer'].strip('/').split('/')
    if parts[0]=='measurements':props.add(records[link['record_id']]['measurements'][int(parts[1])]['property'])
display['structural_properties']=list(dict.fromkeys(display['structural_properties']+sorted(props)));write(S/'data/measurement-display.json',display)
# Wire the source-specific renderers without changing other papers' scenes.
p=S/'dist/protocol-visuals.mjs'
text=p.read_text(encoding='utf8');text="import {buildHeo2003Scene,createHeo2003Art,createHeo2003ConditionGrid} from './heo2003-protocol.mjs';\n"+text
text=text.replace('const sourceArt=createNagasaki2004Art','const sourceArt=createHeo2003Art(o,r)||createNagasaki2004Art')
text=text.replace('const aerosol=buildAerosolScene','const heo=buildHeo2003Scene(o,r),aerosol=buildAerosolScene')
text=text.replace("el('p',nagasaki?.caption", "el('p',heo?.caption||nagasaki?.caption")
text=text.replace('if(nagasaki||ribeiro||norberg){','if(heo||nagasaki||ribeiro||norberg){')
text=text.replace('const dl=aerosol?createAerosolConditionGrid','const dl=heo?createHeo2003ConditionGrid(o,r):aerosol?createAerosolConditionGrid')
text=text.replace('if(!aerosol)for','if(!aerosol&&!heo)for')
text=text.replace("const env=el('div');env.append(el('dt','Environment'),el('dd',fact(o.environment)));dl.append(env);", "if(!heo){const env=el('div');env.append(el('dt','Environment'),el('dd',fact(o.environment)));dl.append(env);}")
p.write_text(text,encoding='utf8')
p=S/'dist/crystal-viewer.mjs';text=p.read_text(encoding='utf8');text="import {mountHeoAverage} from './heo2003-average-viewer.mjs';\n"+text
text=text.replace('if(!host)return;host.replaceChildren();await productIdentity(host,r);','if(!host)return;host.replaceChildren();if(await mountHeoAverage(host,r))return;await productIdentity(host,r);');p.write_text(text,encoding='utf8')
p=S/'dist/source-evidence.mjs';text=p.read_text(encoding='utf8');anchor=' return card;\n}'
insertion=""" if(sourceId==='heo2003'&&item.id==='inventory-supporting_tables-0'){
  const d=el('details'),area=el('div');d.append(el('summary','Browse all 1,209 supporting reflections'),area);let started=false;
  d.addEventListener('toggle',async()=>{if(!d.open||started)return;started=true;area.replaceChildren();try{const {mountHeoReflections}=await import('./heo2003-reflection-viewer.mjs');await mountHeoReflections(area);}catch(e){started=false;area.textContent='Reflection viewer unavailable. Close and reopen this section to retry, or consult the downloadable source table.';console.error(e);}});card.append(d);
 }
 return card;
}"""
assert anchor in text;text=text.replace(anchor,insertion);p.write_text(text,encoding='utf8')
p=S/'dist/illustrated-record.mjs';p.write_text(p.read_text(encoding='utf8')+"\nif(id==='heo-2003-refinement-comparison'){const host=document.getElementById('record-crystal-references');const {mountHeoReflections}=await import('./heo2003-reflection-viewer.mjs');await mountHeoReflections(host);}\n",encoding='utf8')
p=S/'dist/illustrated-guide.css';p.write_text(p.read_text(encoding='utf8')+'\n/* Source-average and supporting-reflection readers: scoped to Heo2003. */\n'+(S/'dist/heo2003-viewers.css').read_text(encoding='utf8'),encoding='utf8')
p=S/'scripts/build_atlas.py';edit(p,"NAMES['FePt']='Iron–platinum · heterodimer-component context'","NAMES['FePt']='Iron–platinum · heterodimer-component context'\nNAMES['In66Si100Al92O384']='Indium nanoclusters in zeolite X · nominal In66-X'\nNAMES['In']='Indium · zeolite-hosted nanocluster component'")
edit(p,"and 'precursor_selection' in r['quality']['requested_tasks']","and (r.get('reader_role')=='synthesis_route' or 'precursor_selection' in r['quality']['requested_tasks'])")
edit(S/'scripts/schema_definition.py',"record['properties']['collection']={'enum':['reviewed_literature','published_benchmark']}","record['properties']['collection']={'enum':['reviewed_literature','published_benchmark']}\n# Reader navigation and machine-training admission are separate decisions.\nrecord['properties']['reader_role']={'enum':['synthesis_route','supporting_procedure','contextual_observation']}")
p=S/'scripts/check_quality.py';edit(p,'self.check(stub.get("is_synthesis_route") is True,',"self.check(r.get('reader_role') == 'synthesis_route' or 'precursor_selection' in r['quality']['requested_tasks'], f'{formula}/{rid}: route lacks a separate reader or legacy training admission')\n                self.check(stub.get(\"is_synthesis_route\") is True,")
edit(S/'scripts/build_dataset.py',"'dataset_version':'0.23.0'","'dataset_version':'0.24.0'")
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 text=p.read_text(encoding='utf8');new=text.replace('0.23.0-r1','0.24.0-r1').replace('0.23.0-r2','0.24.0-r1')
 if text!=new:p.write_text(new,encoding='utf8')
assert all(sha(S/'data/records'/n)==h for n,h in before_records.items())
write(O/'site-import-manifest.json',{'schema':'mattersyn.heo_site_import/1','at':datetime.now(timezone.utc).isoformat(),'status':'integrated_build_and_browser_pending','audits':{str(p):sha(p) for p in audit_files},'new_records':10,'old_records_unchanged':470,'new_molecule_entries':8,'material_slots':14,'apparatus_scenes':14,'reflection_rows':1209,'selected_source_crops':16,'full_page_images':0,'new_exact_structure_pairs':0,'new_training_tasks':0,'public_files':{dst:sha(S/'dist'/dst) for dst in public_files.values()}})
print(json.dumps({'integrated_records':10,'unchanged_records':470,'source':'heo2003','browser_pending':True}))
