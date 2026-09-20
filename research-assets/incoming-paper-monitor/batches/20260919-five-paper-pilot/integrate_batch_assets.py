"""Site-owner import of three independently audited scientific visual packages."""
from pathlib import Path
import json,hashlib,shutil,copy
from datetime import datetime,timezone
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';O=B/'integration-proposal';VBASE=S/'dist/assets/chemical-registry'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def copy_exact(src,dst,h=None):
 assert src.is_file();h=h or sha(src);assert sha(src)==h
 if dst.exists():assert sha(dst)==h,('Existing asset differs',str(dst))
 else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 return h
configs={'la036034c':('nagasaki2004',['reader','component','apparatus','product']), 'jp0473669':('ribeiro2004',['reader','visual']), 'ja048427j':('norberg2004',['reader','visual'])}
assert not (O/'asset-import-manifest.json').exists(),'Inspect existing integration instead of reimporting'
assert S.is_dir(),S
O.mkdir(exist_ok=True);before={};audits={}
# All audits are checked before any registry is changed. Preserve Site inputs as
# immutable evidence of the exact shared references used by the private audits.
for suffix,(sid,names) in configs.items():
 P=B/suffix
 for name in names:
  ap=P/(name+'-source-audit.json');a=read(ap);assert a['status'].startswith('passed') and not a.get('open_findings')
  bf=a['bound_files'];bf={x['path']:x['sha256'] for x in bf} if isinstance(bf,list) else bf
  for rel,h in bf.items():
   p=Path(rel);p=p if p.is_absolute() else P/p;assert sha(p)==h,('Audit input changed',str(p))
   if p.is_relative_to(S):
    dest=O/'base-site-inputs'/p.relative_to(S);copy_exact(p,dest,h);before[str(p)]={'snapshot':str(dest),'sha256':h}
  audits[str(ap)]=sha(ap)
for rel in ['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/product-bindings.json','dist/assets/crystal-references/registry.json','data/inventory-summary.json']:
 p=S/rel;dest=O/'base-site-inputs'/rel;copy_exact(p,dest);before[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
write(O/'base-site-inputs.json',before);write(O/'base-record-hashes.json',{p.name:sha(p) for p in (S/'data/records').glob('*.json')})
reg=read(VBASE/'registry.json');bindings=read(VBASE/'bindings.json');products=read(VBASE/'product-bindings.json');entries={e['id']:e for e in reg['entries']};added=[];binding_counts={}
def add_entries(root,filename,sid):
 for e0 in read(root/filename)['entries']:
  e=copy.deepcopy(e0);assert e['id'] not in entries,e['id']
  for key in ['svgPath','model2dPath','model3dPath']:
   if e.get(key):copy_exact(root/e[key],VBASE/e[key],e['assetHashes'][key])
  if 'independentScientificAudit' in e:e['independentScientificAudit']='passed_source_scoped_reference_audit'
  if 'published' in e:e['published']=True
  if 'binding_approved' in e:e['binding_approved']=True
  e['eligible_training']=False;entries[e['id']]=e;reg['entries'].append(e);added.append({'id':e['id'],'source_id':sid})
for suffix,(sid,_) in configs.items():
 P=B/suffix;V=P/'visuals'
 roots=[(V/'components','registry-additions.json')] if suffix=='la036034c' else [(V/'molecules','registry-additions.json')]+([(V/'products','product-registry-additions.json')] if suffix=='ja048427j' else [])
 for root,file in roots:add_entries(root,file,sid)
 delta=read(V/('components/molecule-bindings-proposal.json' if suffix=='la036034c' else 'molecules/molecule-bindings-proposal.json' if suffix=='jp0473669' else 'molecules/bindings-additions.json'))
 count=0
 for p in sorted((P/'canonical-drafts').glob('*.json')):
  r=read(p);rid=r['record_id'];bb=delta['recordBindings'].get(rid,{})
  assert rid not in bindings['recordBindings'];assert set(bb)=={m['id'] for m in r['materials']},rid
  assert all(v in entries for v in bb.values()),rid
  nn=copy.deepcopy(delta['bindingNotes'].get(rid,{}))
  for n in nn.values():
   if isinstance(n,dict):
    n['binding_approved']=True;n['independent_scientific_audit']='Passed source-scoped molecular and specimen-reference audit.'
    if 'approval_status' in n:n['approval_status']='passed'
  bindings['recordBindings'][rid]=bb;bindings.setdefault('bindingNotes',{})[rid]=nn;count+=len(bb)
 binding_counts[sid]=count
 copy_exact(V/'apparatus'/(sid+'-protocol.mjs'),S/'dist'/(sid+'-protocol.mjs'))
write(VBASE/'registry.json',reg);write(VBASE/'bindings.json',bindings)
products['recordBindings'].update(read(B/'ja048427j/visuals/products/product-reference-proposal.json')['recordBindings'])
write(VBASE/'product-bindings.json',products)
# A context selector preserves specimen-level phase/size uncertainty; it does
# not promote an observation into measured coordinates or a recipe pair.
ctx={'schema':'mattersyn-source-product-contexts/1','recordContexts':{},'sourceNotices':{}}
for row in read(B/'la036034c/visuals/products/product-context-bindings-proposal.json')['contexts']:
 ctx['recordContexts'].setdefault(row['record_id'],[]).append({'sample_id':row['sample_id'],'registry_id':row['registry_id'],'label':row['canonical_product']['source_sample_label'] or row['sample_id'],'caption':row['source_caption'],'phase':row['canonical_phase'],'canonical_pointer':row['canonical_pointer']})
for p in (B/'jp0473669/canonical-drafts').glob('*.json'):
 r=read(p)
 for i,product in enumerate(r['products']):
  if product['composition']['value']=='SnO2':ctx['recordContexts'].setdefault(r['record_id'],[]).append({'sample_id':product['sample_id'],'registry_id':'identity-ribeiro-sno2-colloid','label':product['source_sample_label'] or product['sample_id'],'caption':'Source-defined SnO₂ specimen or series. The symbol does not supply a measured particle envelope, atomic coordinates or an exact cross-technique sample association.','phase':product['phase'],'canonical_pointer':f'/products/{i}'})
ctx['sourceNotices']={
 'nagasaki2004':'The original SI provides TEM and powder XRD. The authors assign hexagonal wurtzite CdS, but the exact links between those specimens, optical size estimates and individual preparations remain unresolved. No sample coordinates or qualified local CdS reference CIF are available. Symbols are not atomic structures.',
 'ribeiro2004':'The main paper supplies original microscopy and optical plots, and assigns cassiterite in its XRD discussion. It contains no XRD trace, SAED pattern or measured atomic coordinates. SI was not located or verified. No sample CIF or inferred atomistic particle is supplied.',
 'norberg2004':'XRD and HRTEM support the reported ZnO host phase. Specimen cards preserve colloid, control and film identities. The downloadable ZnO lattice is an independent undoped reference; it supplies no measured Mn positions, surface ligands or exact recipe–structure label.'}
write(VBASE/'product-contexts.json',ctx)
extra=[]
for c in read(B/'jp0473669/visuals/molecules/component-view-proposal.json')['components']:
 if c.get('canonical_stock_pointer'):continue # The canonical stock viewer handles this exact stock.
 extra.append({'record_id':c['canonical_record_id'],'label':c['context'],'scope':c['scope'],'components':[{'registry_id':x['registry_id'],'role':x['role'],'viewOverrides':{'name':'Water · aqueous reagent solvent','caption':'Water component reference for this aqueous reagent. Its grade, number of solvent molecules and solution geometry are not specified.','limitations':['This is a separate solvent reference, not an assigned solution structure.']} if x['registry_id']=='water' else {}} for x in c['components']]})
write(VBASE/'solution-components.json',{'schema':'mattersyn-solution-components/1','contexts':extra})
cr=read(S/'dist/assets/crystal-references/registry.json');cv=B/'ja048427j/visuals/products';cdst=S/'dist/assets/crystal-references'
for ref in read(cv/'crystal-reference-proposal.json')['entries']:
 assert ref['id'] not in {x['id'] for x in cr['entries']}
 for key,hkey in [('cifPath','cifSha256'),('modelPath','modelSha256'),('finiteModelPath','finiteModelSha256')]:copy_exact(cv/ref[key],cdst/ref[key],ref[hkey])
 for d in ref['additionalDownloads']:copy_exact(cv/d['path'],cdst/d['path'],d['sha256'])
 cr['entries'].append(ref)
write(cdst/'registry.json',cr)
asset_counts={}
for suffix,(sid,_) in configs.items():
 P=B/suffix;r=read(P/'public-review-proposal'/(sid+'.json'));needs={}
 for cat in ['figures','tables','schemes','equations','source_notes']:
  for item in r[cat]:
   if item.get('public_asset'):needs[item['public_asset']]=item['public_asset_sha256']
 for sec in r['reader_sections']:
  for item in sec['items']:
   for a in item.get('original_assets',[]):needs[a['public_asset']]=a.get('public_asset_sha256',a.get('sha256'))
 source_root=P/'public-review-proposal/original-assets-pdfium' if suffix=='ja048427j' else P/'reader-assets'
 candidates={sha(p):p for p in source_root.rglob('*.png')}
 for path,h in needs.items():
  assert h in candidates,(sid,path);dest=S/'dist'/path;assert dest.resolve().is_relative_to((S/'dist').resolve());copy_exact(candidates[h],dest,h)
 asset_counts[sid]=len(needs)
manifest={'at':datetime.now(timezone.utc).isoformat(),'status':'assets_imported_records_and_browser_pending','audits':audits,'new_registry_entries':added,'material_slots':binding_counts,'original_assets':asset_counts,'source_product_contexts':{k:len(v) for k,v in ctx['recordContexts'].items()},'exact_measured_structure_imports':0,'external_crystal_references_added':1,'base_site_inputs':str(O/'base-site-inputs.json'),'publication':'pending'}
write(O/'asset-import-manifest.json',manifest)
print(json.dumps({'new_entries':len(added),'slots':binding_counts,'original_assets':asset_counts,'exact_structure_pairs':0}))
