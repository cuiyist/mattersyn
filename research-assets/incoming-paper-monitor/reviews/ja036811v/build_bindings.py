from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
adds={e['id']:e for e in read(V/'registry-additions.json')['entries']}
mapping={e.removeprefix('identity-schwartz-'):e for e in adds}
mapping.update({x:x for x in ['tetramethylammonium-hydroxide-pentahydrate','ethanol','ethyl-acetate','heptane','toluene','helium']})
mapping.update({'dmso':'dimethyl-sulfoxide','topo-component':'topo'})
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};registry.update(adds)
neutral=read(V/'registry-neutralizations.json');registry.update({x['id']:x['after']for x in neutral['updates']});neutral_files={x['path']:x for x in neutral['files']}
equivalences={'zinc-acetate-dihydrate':{'Zn(C2H3O2)2·2H2O','Zn(OAc)2·2H2O','C4H10O6Zn'},'cobalt-acetate-tetrahydrate':{'Co(C2H3O2)2·4H2O','Co(OAc)2·4H2O','C4H14CoO8'},'nickel-perchlorate-hexahydrate':{'Ni(ClO4)2·6H2O','H12Cl2NiO14','Cl2H12NiO14'},'tetramethylammonium-hydroxide-pentahydrate':{'C4H13NO·5H2O','C4H23NO6'}}
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==30
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):
   allowed=equivalences.get(ref,{e['formula'],e.get('displayFormula')});assert m['formula'] in allowed,(rid,m['id'],m['formula'],allowed)
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_scoped':True})
  if ref not in adds:reuse[ref]={'entry':e,'assetHashes':{k:neutral_files[e[k]]['sha256']if e[k]in neutral_files else sha(S/'dist/assets/chemical-registry'/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}}
 k=rid.removeprefix('schwartz-2003-')
 if k in ['zno-route','topo-zno','room-aging','thermal-ripening','clarity-restoration']:products[rid]='identity-schwartz-zno-specimen'
 if k in ['co-route','topo-co']:products[rid]='identity-schwartz-co-specimen'
 if k in ['ni-route','topo-ni']:products[rid]='identity-schwartz-ni-specimen'
 if k in ['aggregation','magnetometry']:products[rid]='identity-schwartz-co-aggregate-specimen'
 if k=='surface-cleaning-control':products[rid]='identity-schwartz-surface-co-specimen'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Hydrate formula components and free-molecule structures identify named reagents, not measured solution complexes. Technical TOPO and its named component are separate. Variable dopant contents, surface-bound controls and aggregate powder retain distinct source scopes.' for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Source product identities only; no measured dopant sites, ligand occupancies or particle coordinates. Independent undoped bulk ZnO is a separately labeled reference.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
cr=S/'dist/assets/crystal-references';p=cr/'registry.json';ref=next(e for e in read(p)['entries'] if e['id']=='zno-wurtzite')
asset_hashes={ref[k]:sha(cr/ref[k]) for k in ['cifPath','modelPath']}
assert asset_hashes[ref['cifPath']]==ref['cifSha256'] and asset_hashes[ref['modelPath']]==ref['modelSha256']
write(V/'crystal-reference-proposal.json',{'registry_before_sha256':sha(p),'entry_id':ref['id'],'entry_before':ref,'asset_hashes':asset_hashes,'additional_record_ids':['schwartz-2003-'+k for k in ['zno-route','co-route','ni-route','topo-zno','topo-co','topo-ni']],'scope':'Independent undoped bulk ZnO comparison (Kihara and Donnay1985,COD9004178), not a measured nanocrystal or dopant arrangement. Fu2007 reports wurtzite; Schwartz2003 reports a wurtzite ZnO host. This reference has a=3.2494Å,c=5.2038Å, distinct from the cited bulk parameters a=3.2495Å,c=5.2067Å in Schwartz2003. Co/Ni occupancy, particle surfaces and exact sample geometry are not assigned.','reference_only':True,'training_eligible':False,'measured_sample_coordinates':False})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'chemical bindings;',len(products),'product identities;',len(reuse),'reused chemical references.')
