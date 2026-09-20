from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={e['id'].removeprefix('identity-banerjee-'):e['id'] for e in read(V/'registry-additions.json')['entries']}
mapping.update({k:k for k in ['sulfuric-acid','water','cadmium-oxide','topo','top','argon','toluene','methanol','ethanol','dimethylformamide']})
mapping.update({'hydrochloric-acid':'hydrochloric-acid-aqueous','tdpa':'tetradecylphosphonic-acid'})
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==14
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula'] in [e['formula'],e.get('displayFormula')],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:reuse[ref]={'entry':e,'assetHashes':{k:sha(S/'dist/assets/chemical-registry'/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}}
 if rid=='banerjee-2003-growth':products[rid]='identity-banerjee-composite-specimen'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Chemical identity references do not assign unreported quantities or stock speciation. Oxidized nanotube surfaces and composite specimen diagrams are illustrative, with no refined atomic geometry. Bound, free/washings and no-tube comparison particles retain separate sample scopes.' for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Illustrative CdTe–oxidized MWNT heterostructure identity for the reported growth route. No refined atomic coordinates or measured junction model supplied; no inferred crystal file. Analysis contexts do not become additional synthesis products.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material bindings;',len(products),'product references;',len(reuse),'reused references')
