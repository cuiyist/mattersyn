from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={e['id'].removeprefix('identity-yi-'):e['id'] for e in read(V/'registry-additions.json')['entries']};mapping['water']='water'
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==18
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula']in[e['formula'],e.get('displayFormula')],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:reuse[ref]={'entry':e,'assetHashes':{k:sha(S/'dist/assets/chemical-registry'/e[k])for k in ['svgPath','model2dPath','model3dPath']if e.get(k)}}
 suffix=rid.removeprefix('yi-2002-')
 if suffix in ['anneal-600','anneal-700','anneal-800','anneal-900','anneal-1000','bulk']:products[rid]='identity-yi-'+suffix+'-specimen'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Source formula/composition identities and illustrative specimen states; generic analysis specimens do not inherit a specific annealing batch. Reference stock quantities do not assign comparison-batch charges. Printed mass/mole and feed/formula conflicts remain explicit.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Five annealed phosphor conditions and the distinct bulk comparator, with illustrative specimen identity. No source atomic structure or dopant occupancy is supplied; unassigned analysis contexts have no route product binding.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material bindings;',len(products),'product references;',len(reuse),'reused reference')
