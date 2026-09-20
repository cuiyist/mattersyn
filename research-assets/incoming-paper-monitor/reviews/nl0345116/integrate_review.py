"""Root-only import of independently audited source artifacts into the existing Site."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals';SID='sashchiuk2004'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==15
audits={n:read(B/(n+'-source-audit.json'))for n in ['reader','molecular','visual','bindings','crystal']}
for k,a in audits.items():assert a['status'].startswith('passed'),k
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
hashes={p.stem:sha(p)for p in drafts};assert hashes==a['record_hashes']
assert sha(B/'public-review-proposal/sashchiuk2004.json')==audits['reader']['reader_sha256']
assert sha(B/'reader-assets/crop-manifest.json')==audits['reader']['crop_manifest_sha256']
assert sha(V/'registry-additions.json')==audits['molecular']['registry_sha256']
assert sha(V/'sashchiuk2004-protocol.mjs')==audits['visual']['module_sha256']
assert sha(V/'bindings-additions.json')==audits['bindings']['bindings_sha256']
assert sha(V/'product-reference-proposal.json')==audits['bindings']['product_reference_sha256']
assert sha(V/'crystal-reference-proposal.json')==audits['crystal']['crystal_reference_sha256']
assert read(V/'bindings-additions.json')['sourceRecordSha256']==hashes
assert read(B/'public-review-proposal/proposal-validation.json')['status'].startswith('passed')
O=B/'inventory-proposal';O.mkdir(exist_ok=True);assert not(S/'data/paper-reviews/sashchiuk2004.json').exists()
shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
scope='All seven supplied main pages text-read and visually inspected, with independent source, canonical, reader, molecular, crystal and apparatus audits. No SI located or verified. Individual particles, spherical assemblies, wires, device specimens and author models retain separate scopes; source conflicts and missing parameters remain explicit.'
for p in drafts:
 r=read(p);r['collection']='reviewed_literature';r['quality'].update(review_status='source_reviewed',review_scope=scope);r['sources'][0]['main_status']='All seven supplied main pages text-read and visually inspected; independent source and canonical audits completed. No SI used.';write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/sashchiuk2004.json')
review['remaining_gaps']=[g for g in review.get('remaining_gaps',[])if not g.startswith('Independent')]
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit=scope,publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Four source-scoped growth routes. Ratios are not absolute precursor charges, and caption disagreements remain unresolved. Aliquot workup, microscopy, device processing and model calculations are distinct. Constructed ideal crystal references are excluded from measured-structure training targets.')
for i in review['recipe_inventory']:i['status']='source_reviewed'
assert review['review_scope']=='supplied_main_only_si_unverified';write(S/'data/paper-reviews/sashchiuk2004.json',review)
for asset in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/asset['relative_asset'];assert sha(p)==asset['sha256'];dest=S/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry'
for asset in read(V/'asset-manifest.json')['files']:
 p=V/asset['path'];assert sha(p)==asset['sha256'];dest=dst/asset['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];assert not({e['id']for e in entries}&{e['id']for e in registry['entries']});registry['entries']+=entries;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');delta=read(V/'bindings-additions.json');bindings['recordBindings'].update(delta['recordBindings']);bindings.setdefault('bindingNotes',{}).update(delta['bindingNotes'])
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
cr=S/'dist/assets/crystal-references';proposal=read(V/'crystal-reference-proposal.json');reg=read(cr/'registry.json');reg['entries']+=proposal['entries'];reg['scope']='Independent database references and explicitly constructed ideal prototypes for comparison; never measured sample atomic coordinates or training labels.';write(cr/'registry.json',reg)
for item in proposal['files']:
 p=V/'crystal-reference'/item['path'];assert sha(p)==item['sha256'];dest=cr/item['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
shutil.copy2(V/'sashchiuk2004-protocol.mjs',S/'dist/sashchiuk2004-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf8');t="import {buildSashchiuk2004Scene,createSashchiuk2004Art} from './sashchiuk2004-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createSchwartz2003Art','const sourceArt=createSashchiuk2004Art(o,r)||createSchwartz2003Art').replace('schwartz=buildSchwartz2003Scene(o,r);','schwartz=buildSchwartz2003Scene(o,r),sashchiuk=buildSashchiuk2004Scene(o,r);').replace('schwartz?.caption||','sashchiuk?.caption||schwartz?.caption||').replace('||banerjee||schwartz){','||banerjee||schwartz||sashchiuk){').replace('||banerjee||schwartz)?','||banerjee||schwartz||sashchiuk)?');p.write_text(t,encoding='utf8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf8').replace("'banerjee2003','schwartz2003']","'banerjee2003','schwartz2003','sashchiuk2004']")
t=t.replace(" if(r.lineage?.source_group==='schwartz2003'&&entryId)"," if(r.lineage?.source_group==='sashchiuk2004'&&entryId)host.append(el('p','Original SAED and HRTEM support rock-salt PbSe. The rotatable unit cell and finite block are constructed ideal references using the rounded reported lattice parameter, not measured sample coordinates, fitted wires or ligand-covered surfaces. Caption and text ratios remain unresolved.','guide-notice'));\n if(r.lineage?.source_group==='schwartz2003'&&entryId)")
t=t.replace('Independent bulk references for comparison.','Independent or explicitly constructed bulk references for comparison.');p.write_text(t,encoding='utf8')
p=S/'dist/finite-crystal-reference.mjs';t=p.read_text(encoding='utf8');t=t.replace("viewer.setStyle({}, {sphere:{radius:.37,color:'#6b95b3'},stick:{radius:.07,color:'#a0b7c6'}});","for (const element of new Set(model.atoms.map(a=>a.element))) {\n    const color=({Pb:'#8b9bae',Se:'#bc8957'})[element]||'#6b95b3';\n    viewer.setStyle({elem:element}, {sphere:{radius:.37,color},stick:{radius:.07,color:'#a0b7c6'}});\n  }")
p.write_text(t,encoding='utf8')
p=S/'data/measurement-display.json';d=read(p);d['structural_properties']=list(dict.fromkeys(d['structural_properties']+read(B/'structural-property-additions.json')));write(p,d)
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf8');t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\nNAMES['PbSe']='Lead selenide nanocrystals and assemblies'");p.write_text(t,encoding='utf8')
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf8').replace("'dataset_version':'0.20.0'","'dataset_version':'0.21.0'"),encoding='utf8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.20.0-r1','0.21.0-r1')
 if n!=t:p.write_text(n,encoding='utf8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':SID,'records':{p.stem:sha(S/'data/records'/p.name)for p in drafts},'reader_sha256':sha(S/'data/paper-reviews/sashchiuk2004.json'),'private_reader_sha256':sha(B/'public-review-proposal/sashchiuk2004.json'),'apparatus_sha256':sha(S/'dist/sashchiuk2004-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status'],'schema_additions':[]})
print('Imported 15 audited records into existing MatterSyn. Build, browser and publication pending.')
