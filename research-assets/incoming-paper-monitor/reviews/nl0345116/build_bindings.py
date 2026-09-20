from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
adds={e['id']:e for e in read(V/'registry-additions.json')['entries']}
mapping={e.removeprefix('identity-sashchiuk-'):e for e in adds}
mapping.update({'selenium':'selenium-element','tbp':'tbp','topo-component':'topo','argon':'argon','methanol':'methanol','butanol':'identity-butanol-unspecified-isomer','trimethylsilane':'trimethylsilane'})
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']};registry.update(adds)
bindings={};products={};recordhash={};checks=[];reuse={}
for p in sorted((B/'canonical-drafts').glob('*.json')):
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula'] in {e['formula'],e.get('displayFormula')},(m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref})
  if ref not in adds:reuse[ref]={'entry':e,'assetHashes':{e[k]:sha(S/'dist/assets/chemical-registry'/e[k])for k in ['svgPath','model2dPath','model3dPath']if e.get(k)}}
 k=rid.removeprefix('sashchiuk-2004-')
 if k.startswith('individual-'):products[rid]='identity-sashchiuk-pbse-individual'
 if k.startswith('sphere-')or k=='absorption':products[rid]='identity-sashchiuk-pbse-spheres'
 if k.startswith('wire-')or k in ['device-fabrication','electrical']:products[rid]='identity-sashchiuk-pbse-wires'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Named chemical identities are reference depictions, not measured stock speciation or surface ligands. Pb-cHxBu molecular identity and butanol isomer remain unresolved. Trimethylsilane depicts the literal source name, not verified surface-treatment chemistry.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Illustrative particle/assembly identities; no measured surface atoms or wire geometry. Ideal PbSe crystal reference is separately labeled and excluded from training labels.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed_generator_checks_independent_audit_pending','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material slots;',len(reuse),'reused references')
