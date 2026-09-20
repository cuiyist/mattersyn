from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(O/'package-freeze.json').exists()
assert read(O/'persisted-validation.json')['status']=='passed_author_persisted_checks'
assert read(O/'viewer-contract-validation.json')['status']=='passed'
inputs=read(O/'input-bindings.json')
for p,h in inputs.items():assert sha(p)==h,p
entries=read(O/'registry-additions.json')['entries'];visual_paths=[p for folder in ['previews','stock-previews','conformer-previews']for p in sorted((O/folder).glob('*.png'))]
assert len(visual_paths)==25
visual={'author':'/root/backlog_eta','status':'rendered_author_visual_review_passed','reviewed_at':datetime.now(timezone.utc).isoformat(),'actual_scope':'All 15 identity previews, five stock cards and five retained-reference projections viewed through five original contact sheets. Final SbCl3 formal-ion and composite identity cards reopened individually; the complete final five-stock contact sheet reopened after label refinement. No browser or independent scientific audit claim.','reviewed_assets':{str(p.relative_to(O)):sha(p)for p in visual_paths},'contact_sheets':{str(p.relative_to(O)):sha(p)for p in sorted((O/'contacts').glob('*.png'))},'scientific_focus':['Four n-propyl branches and separate chloride counterion','Formal Sb3+ and three Cl− ions without coordination/speciation claim','Named cis-oleic reference distinct from technical-grade composition','NIST nitrogen reference; TGA gas versus coolant roles','PS repeat identity without invented chain/units','Four salt/DMF feeds, separate solvent charges and solution aliquots','Unknown PS/toluene amounts and beta-film composition'],'browser_validation':'not_claimed','independent_approval':False}
save(O/'author-visual-review.json',visual)
validation=read(O/'author-validation.json');validation.update(status='author_automated_and_rendered_visual_checks_passed',persisted_check_count=read(O/'persisted-validation.json')['check_count'],actual_viewer_function_checks=read(O/'viewer-contract-validation.json')['check_count'],visual_review_sha256=sha(O/'author-visual-review.json'));save(O/'author-validation.json',validation)
assets={}
for e in entries:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):
   assets[e[k]]=sha(O/e[k]);assert not re.search(r'[A-Z]:[\\/]|/Users/',(O/e[k]).read_text(encoding='utf-8')),e[k]
assert len(assets)==27
save(O/'public-asset-proposal.json',{'status':'private_allowlist_pending_independent_molecular_audit','relative_asset_files':assets,'count':len(assets),'excluded':['reference-snapshots','contacts','previews','stock-previews','conformer-previews','stock-svg','author programs','validation and local input path maps'],'note':'Assets only. Registry, binding and component-selector JSON require distinct approval before merging. No raw source payload, complete source page or product coordinate asset is included.'})
bound={str(p):sha(p)for p in sorted(O.rglob('*'),key=str)if p.is_file()};bound.update(inputs)
manifest={'schema':'mattersyn-private-molecular-proposal/1','source_id':'lian2021','doi':'10.1021/acsami.1c18038','author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_checks_passed_independent_molecular_audit_pending','canonical_version':1,'canonical_package_sha256':sha(P/'canonical-proposal/v1/package-manifest.json'),'canonical_independent_audit_sha256':sha(P/'canonical-reader-independent-audit/independent-audit-v1.json'),'source_independent_audit_sha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'counts':validation['counts'],'author_checks':{'generation':validation['check_count'],'persisted':validation['persisted_check_count'],'actual_viewer_function':validation['actual_viewer_function_checks'],'rendered_identity_previews':15,'rendered_stock_cards':5,'rendered_conformer_projections':5},'quantity_reference_count':read(O/'persisted-validation.json')['quantity_reference_count'],'public_asset_file_count':len(assets),'bound_files':bound,'bound_file_count':len(bound),'binding_approved':False,'independent_molecular_audit':'pending','site_imported':False,'published':False,'browser_approved':False,'training_approved':False,'limitations':['No product/sample bindings or new atomic coordinates','No assigned dissolved coordination, ion pairing, hydrate, ligand coverage or polymer chain','Two new 2D reference graphs only; all retained 3D arrays unchanged','No assumed final solution volumes or inferred aliquot solute doses','Source grades and relative composite mass parts remain typed and explicitly scoped']}
save(O/'package-freeze.json',manifest)
print(json.dumps({'manifest_sha256':sha(O/'package-freeze.json'),'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'stock_map_sha256':sha(O/'stock-component-map.json'),'bound_files':len(bound),'checks':manifest['author_checks'],'public_assets':len(assets)}))
