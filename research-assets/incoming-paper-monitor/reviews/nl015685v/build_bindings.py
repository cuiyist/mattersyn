from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={'cadmium-adsorbed-film':'identity-besson-cd-loaded-film','teos':'tetraethyl-orthosilicate','water':'water','acidified-water':'identity-besson-acidified-water','ethanol':'ethanol','ctab':'cetyltrimethylammonium-bromide','pyrex':'identity-besson-pyrex','air':'identity-besson-air','cadmium-nitrate':'cadmium-nitrate-hydration-unspecified','ammonia':'ammonia','sodium-citrate':'identity-besson-citrate','h2s':'hydrogen-sulfide','ctab-host':'identity-besson-empty-film','copolymer-host':'identity-besson-copolymer-host','cadmium-stock':'identity-besson-loading-solution','silicon':'identity-besson-silicon','mesoporous-film':'identity-besson-pl-host','ctab-loaded':'identity-besson-ctab-cds-film','copolymer-loaded':'identity-besson-copolymer-cds-film','pl-film':'identity-besson-pl-film','cds-colloid':'identity-besson-cds-colloid'}
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
 for suffix,ref in [('ctab-silica-host','identity-besson-empty-film'),('ctab-cds-loading','identity-besson-ctab-cds-film'),('copolymer-cds-loading','identity-besson-copolymer-cds-film')]:
  if rid.endswith(suffix):products[rid]=ref
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Reference chemical identities and mesoscale film schematics; no measured solution or crystal coordinates. Hydration, citrate form, unknown acid and unspecified copolymer remain unresolved.'for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Mesoscopic host and pore-filling illustrations only. Atomic CdS blende-type fringes are distinct evidence, with no supplied atomic CIF. Unassigned analytical/theory contexts have no generic product binding.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'records;',len(checks),'material bindings;',len(products),'product references;',len(reuse),'reused references')

