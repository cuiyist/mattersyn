"""Package provenance and the completed visual inspection, without Site writes."""
import json,hashlib,os,re
from pathlib import Path
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
ROOT=Path('[local path redacted]')
SITE=ROOT/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
registry=read(OUT/'registry-additions.json');bindings=read(OUT/'bindings-additions.json')
check=read(OUT/'validation-report.json');assert check['status']=='passed'
check['visualReview']={'status':'passed','asset':'review/svg-contact-sheet.png','sha256':sha(OUT/'review/svg-contact-sheet.png'),
 'scope':'All ten actual SVGs rendered and inspected. Compound formulas/connectivity and explicit H–F/Ge–H labels are legible; five solid/polymer/equipment cards are distinct and carry limitations. This is not a browser or measured-geometry validation.'}
dump(OUT/'validation-report.json',check)
creg=SITE/'dist/assets/crystal-references/registry.json'
cinventory=[];errors=[]
for base in [SITE/'dist/assets',ROOT/'research-assets']:
 for folder,dirs,files in os.walk(base,onerror=lambda e:errors.append(str(e))):
  dirs[:]=[d for d in dirs if 'runtime' not in d.lower() and d!='python-packages']
  for f in files:
   if not f.lower().endswith('.cif'):continue
   p=Path(folder)/f;text=p.read_text(encoding='utf-8',errors='replace')
   cinventory.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'mentionsGeElement':bool(re.search(r'(?<![A-Za-z])Ge(?![a-z])',text))})
crystals={'status':'No local Ge crystal reference located in the inspected asset inventory','scope':'Existing public crystal registry and .cif files under recipe-atlas/dist/assets and research-assets; runtime/dependency folders excluded. No paper search or network retrieval.',
 'registrySha256':sha(creg),'registeredReferences':[{'id':x['id'],'name':x['name']} for x in read(creg)['entries']],
 'cifFiles':cinventory,'geCandidateFiles':[x['path'] for x in cinventory if x['mentionsGeElement']],'readErrors':errors,
 'limits':['The source reports epitaxy and lattice mismatch, but no measured Ge unit-cell model or coordinates are supplied.','No Ge lattice constant was computed from a Si value or the 4% mismatch.','No crystal model, CIF, or assignment to a measured Ge quantum dot has been generated.']}
dump(OUT/'ge-crystal-local-inventory.json',crystals)
inventory=[]
for ident in ['svg','models','sdf']:
 for p in sorted((OUT/ident).glob('*')):
  if p.is_file():inventory.append({'file':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'scope':'Illustrative reference only; not experimental sample coordinates','eligible_training':False})
dump(OUT/'asset-manifest.json',{'sourceDoi':'10.1021/jp951903v','sourceSha256':'016e78158e4f83837f13b1412f3e08d5f7134724a3758d14468a41ff926e156a','summary':registry['summary'],'files':inventory,
 'metadataHashes':{p:sha(OUT/p) for p in ['registry-additions.json','bindings-additions.json','model-provenance.json','validation-report.json','reused-references.json','missing-identities.json','ge-crystal-local-inventory.json']}})
new={x['id']:x for x in registry['entries']}
reused={x['id']:x for x in read(OUT/'reused-references.json')['entries']}
source_refs=[]
for rid,mapping in bindings['recordBindings'].items():
 for mid,ident in mapping.items():
  row={'recordId':rid,'materialId':mid,'registryId':ident,'status':'reuse_existing' if ident in reused else 'new_private_reference',
   'limitation':bindings['bindingNotes'][rid][mid]}
  if ident in reused:row.update(reused[ident])
  else:row.update({k:new[ident][k] for k in ['name','formula','depictionKind','sourceUrls','assetHashes']})
  source_refs.append(row)
dump(REVIEW/'crop-assets/chemical-reference-plan.json',{'status':'Completed as private molecular-assets package','sourceDoi':'10.1021/jp951903v','uniqueIdentities':13,'sourceMaterialBindings':source_refs,
 'package':'../molecular-assets','notAdded':['Unreported wafer-cleaning reagents','PMMA coating solvent','HF solution solvent or water by assumption','Oxidation reagent','Etch plasma fragments or byproducts','Background comparison materials from cited work'],
 'productScope':'Ge islands are the product, not a molecular reagent. No Ge crystal asset was found or created.'})
print(json.dumps({'assetFiles':len(inventory),'cifInventory':len(cinventory),'geCandidates':crystals['geCandidateFiles'],'errors':errors,'validationChecks':check['checkCount']}))
