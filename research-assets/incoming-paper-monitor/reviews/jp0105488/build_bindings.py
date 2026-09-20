from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals';N=B/'neutralized-references'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping={'cdse-zns-stock':'identity-gerion-cdse-zns','topo':'topo','butanol':'identity-butanol-unspecified-isomer','methanol':'methanol','mps':'mps-trimethoxy','tmah-methanol':'tetramethylammonium-hydroxide','tmah-pentahydrate':'tetramethylammonium-hydroxide-pentahydrate','phosphonate-stock':'identity-gerion-phosphonate','tmscl':'tmscl','aps':'aps-trimethoxy','water':'water','nitrogen':'nitrogen','mpa':'mercaptopropionic-acid','dmf':'dimethylformamide','dmap':'dimethylaminopyridine','pb':'identity-gerion-pb','k2hpo4':'dipotassium-hydrogen-phosphate','kh2po4':'potassium-dihydrogen-phosphate','mes':'mes-buffer-acid','tbe':'identity-gerion-tbe','nacl':'sodium-chloride','glycerol':'glycerol','agarose':'identity-gerion-agarose','sephadex-g25':'identity-gerion-sephadex','rhodamine6g':'identity-rhodamine-6g-unspecified-salt','dtnb':'dtnb','toluene':'toluene','chloroform':'chloroform','carbon-grid':'identity-gerion-carbon-grid','mica':'identity-gerion-mica','specimen':'identity-gerion-specimens','znsshell-precursors':'identity-gerion-zns-precursors','silica-specimen':'identity-gerion-siloxane','mpa-specimen':'identity-gerion-mpa','hplc-silica':'identity-gerion-hplc-phase','siloxane-complexes':'identity-gerion-siloxane-complexes'}
mapping.update({'tmah':'tetramethylammonium-hydroxide','phosphonate':'identity-gerion-phosphonate'})
registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']}
additions={e['id']:e for e in read(V/'registry-additions.json')['entries']};registry.update(additions)
neutral={e['id']:e for e in read(N/'registry-updates.json')['entries']};registry.update(neutral)
bindings={};products={};recordhash={};checks=[];reuse={}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert drafts,'Canonical drafts not ready'
for p in drafts:
 r=read(p);rid=r['record_id'];bindings[rid]={};recordhash[rid]=sha(p)
 for m in r['materials']:
  ref=mapping[m['id']]
  if rid=='gerion-2001-aps-functionalization' and m['id']=='silica-specimen':ref='identity-gerion-mps-primed'
  assert ref in registry,(rid,m['id'],ref);e=registry[ref]
  if m.get('formula') and e.get('formula'):assert m['formula'] in [e['formula'],e.get('displayFormula')],(rid,m['id'],m['formula'],e['formula'])
  bindings[rid][m['id']]=ref;checks.append({'record':rid,'material':m['id'],'reference':ref,'formula_agrees_or_explicitly_unspecified':True})
  if ref not in additions:
   reuse[ref]={'entry':e,'assetHashes':{k:sha((N if ref in neutral else S/'dist/assets/chemical-registry')/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)},'metadata_neutralized':ref in neutral}
 if rid in ['gerion-2001-silica-silanization','gerion-2001-aps-functionalization']:products[rid]='identity-gerion-siloxane'
 if rid=='gerion-2001-mpa-exchange':products[rid]='identity-gerion-mpa'
 if rid=='gerion-2001-core-shell-stock':products[rid]='identity-gerion-cdse-zns'
write(V/'bindings-additions.json',{'recordBindings':bindings,'sourceRecordSha256':recordhash,'bindingNotes':{r:'Molecular drawings/conformers are identity references, not measured solution or surface structures. Ionic mixtures have no inferred ion-pair geometry. Ambiguous phosphonate stock and butanol isomer remain unresolved; all source-specific doses and solvent contexts remain in the record.' for r in bindings}})
write(V/'product-reference-proposal.json',{'scope':'Source architecture identity references only. No atomistic coating, uniform shell, unique core count or measured lattice inferred. Combined comparative/assay observations have no generic product binding.','recordBindings':products})
write(V/'reused-reference-audit-input.json',{'entries':reuse})
write(V/'binding-generation-check.json',{'status':'passed','records':len(bindings),'material_bindings':len(checks),'product_bindings':len(products),'checks':checks})
print(len(bindings),'record bindings;',len(checks),'material slots;',len(products),'product references;',len(reuse),'reused references')
