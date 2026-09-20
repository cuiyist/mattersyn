from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={'cd2':'identity-cadmium-ii-aqueous','hg2':'identity-mercury-ii-aqueous','hexametaphosphate':'identity-hexametaphosphate-unresolved','h2s':'hydrogen-sulfide','h2s-aqueous':'identity-braun-h2s-water','water':'water','argon':'argon','specimen':'identity-braun-qdqw-specimens','system-i-specimen':'identity-braun-system-i','system-ii-specimen':'identity-braun-system-ii','system-iii-specimen':'identity-braun-system-iii','sapphire':'identity-braun-sapphire','glass-cell':'identity-braun-glass-cell','cds-core':'identity-braun-cds-core'}
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert drafts,'Canonical drafts not ready'
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula'] in [e['formula'],e.get('displayFormula')],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:reuse[ref]={'entry':e,'assetHashes':{k:sha(S/'dist/assets/chemical-registry'/e[k])for k in ['svgPath','model2dPath','model3dPath']if e.get(k)}}
 if rid in ['braun-2001-system-'+s for s in ['i','ii','iii']]:products[rid]='identity-braun-system-'+rid.split('system-')[1]
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Reference chemical identities and layer schematics, not measured solution or crystal coordinates. Cd2+/Hg2+ counterions and hexametaphosphate form remain unreported; aqueous feeds retain separate water/solute context.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Three source-assigned architectures shown schematically. No atomistic interface, measured phase, exact core diameter, or CIF inferred. Analytical and theoretical contexts have no generic product binding.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material bindings;',len(products),'product references;',len(reuse),'reused references')
