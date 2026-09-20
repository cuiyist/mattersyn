from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={'agacac':'identity-shah-ag-acac','ir-precursor':'ir-mecp-cod','pt-precursor':'identity-shah-pt-precursor','c8-thiol':'perfluorooctanethiol','co2':'carbon-dioxide','hydrogen':'hydrogen','acetone':'acetone','heptane':'heptane','fluorinert':'identity-shah-fluorinert','freon':'trichlorotrifluoroethane','c10-thiol':'perfluorodecanethiol','dodecanethiol':'dodecanethiol','octanethiol':'octanethiol','hexanethiol':'hexanethiol','ag-no3':'identity-shah-agno3','water':'water','chloroform':'chloroform','hexane':'hexane','ethanol':'ethanol','ag':'identity-shah-ag','ir':'identity-shah-ir','pt':'identity-shah-pt','grid':'identity-shah-tem-grid','specimen':'identity-shah-metal-dispersion','distributions':'identity-shah-size-data'}
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']}
additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
bindings={};products={};recordhash={};checks=[];reuse={}
for p in sorted((B/'canonical-drafts').glob('*.json')):
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']];assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula']==e['formula'],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref
  checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:
   reuse[ref]={'entry':e,'assetHashes':{k:sha(S/'dist/assets/chemical-registry'/e[k])for k in ['svgPath','model2dPath','model3dPath']if e.get(k)}}
 if rid in ['shah-2001-ag-'+c for c in 'abcdefghi']+['shah-2001-ag-typical-framework','shah-2001-ag-structure']:products[rid]='identity-shah-ag'
 if rid in ['shah-2001-ir','shah-2001-pt']:products[rid]='identity-shah-'+rid.rsplit('-',1)[1]
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Molecular drawings are identity references or computed conformers, never measured experimental structures. Ambiguous Pt precursor remains unresolved; AgNO3 and C10/hydrocarbon thiols retain cited-comparator scope.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Source-specific product identity references only. No measured atomic coordinates or guessed ligand shells. No product binding for combined comparative/model contexts.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'record bindings;',len(checks),'material slots;',len(products),'product cards;',len(reuse),'existing references checked')
