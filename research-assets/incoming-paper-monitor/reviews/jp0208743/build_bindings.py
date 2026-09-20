from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={k:'identity-dantas-'+k for k in ['silica','zinc-oxide','alumina','lead-dioxide','boron-oxide','sulfur-source','aluminum-crucible','glass-host','sg1-specimen','sg2-specimen','sg3-specimen','sg4-specimen','afm1-specimen','afm2-specimen']};mapping['sodium-carbonate']='sodium-carbonate'
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==16
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula']in[e['formula'],e.get('displayFormula')],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:reuse[ref]={'entry':e,'assetHashes':{k:sha(S/'dist/assets/chemical-registry'/e[k])for k in ['svgPath','model2dPath','model3dPath']if e.get(k)}}
 suffix=rid.removeprefix('dantas-2002-')
 if suffix in ['sg1','sg2','sg3','sg4','afm1','afm2']:products[rid]='identity-dantas-'+suffix+'-specimen'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Source powder identities and specimen architecture only. Oxide atom-count diagrams do not represent molecular or crystalline geometry; sulfur identity, glass proportions and literal vessel ambiguity remain unresolved.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Six source-defined PbS/glass specimens, with illustrative embedded-particle architecture. No measured atomic structure supplied; unassigned analysis/model contexts have no generic product binding.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material bindings;',len(products),'product references;',len(reuse),'reused reference')
