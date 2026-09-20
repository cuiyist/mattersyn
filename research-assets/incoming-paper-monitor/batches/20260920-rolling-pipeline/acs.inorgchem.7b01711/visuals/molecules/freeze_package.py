from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (O/'package-freeze.json').exists()
assert read(O/'persisted-validation.json')['status']=='passed_author_persisted_checks'
assert read(O/'viewer-contract-validation.json')['status']=='passed'
inputs=read(O/'input-bindings.json')
for p,h in inputs.items():assert sha(p)==h,p
entries=read(O/'registry-additions.json')['entries']
visual_paths=[p for folder in ['previews','stock-previews','conformer-previews'] for p in sorted((O/folder).glob('*.png'))]
assert len(visual_paths)==43
visual={'author':'/root/backlog_eta','status':'rendered_author_visual_review_passed','reviewed_at':datetime.now(timezone.utc).isoformat(),'actual_scope':'All 29 identity images, five stock cards and nine retained-conformer projections inspected through eight original contact sheets. Final water, Cd(PTC)2 powder and ambiguous crystallization cards separately reopened after the last display changes. No browser action or independent audit is claimed.','reviewed_assets':{str(p.relative_to(O)):sha(p) for p in visual_paths},'contact_sheets':{str(p.relative_to(O)):sha(p) for p in sorted((O/'contacts').glob('*.png'))},'scientific_focus':['Formal Cd²⁺ plus two Cl⁻; no Cd–Cl coordination bonds','NH4+ / phenyldithiocarbamate− connectivity and separated ions','Six versus eight explicit deuterium labels','Primary amines, ether, amide, sulfoxide, thiourea and isothiocyanate connectivity','Precursor powder/crystal versus nanocrystal symbolic scope','Five stock summaries, approximations, charge-versus-volume distinction and ambiguous 20 mmol wording'],'browser_validation':'not_claimed','independent_approval':False}
save(O/'author-visual-review.json',visual)
validation=read(O/'author-validation.json');validation['status']='author_automated_and_rendered_visual_checks_passed';validation['canonical_version']=2;validation['persisted_check_count']=read(O/'persisted-validation.json')['check_count'];validation['actual_viewer_function_checks']=read(O/'viewer-contract-validation.json')['check_count'];validation['visual_review_sha256']=sha(O/'author-visual-review.json');save(O/'author-validation.json',validation)
assets={}
for e in entries:
 for key in ['svgPath','model2dPath','model3dPath']:
  if e.get(key):assets[e[key]]=sha(O/e[key])
assert len(assets)==56
save(O/'public-asset-proposal.json',{'status':'private_allowlist_pending_independent_audit','relative_asset_files':assets,'count':len(assets),'excluded':['reference-snapshots','contacts','previews','stock-previews','conformer-previews','stock-svg','author programs','local path maps and input manifests'],'note':'Registry/binding/selector JSON must be independently approved and merged separately; this list is assets only.'})
paths=sorted((p for p in O.rglob('*') if p.is_file()),key=str)
bound={str(p):sha(p) for p in paths};bound.update(inputs)
manifest={'schema':'mattersyn-private-molecular-proposal/1','source_id':'morrison2017','author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_checks_passed_independent_molecular_audit_pending','canonical_version':2,'canonical_package_sha256':sha(P/'canonical-proposal/v2/package-manifest.json'),'canonical_independent_audit_sha256':sha(P/'canonical-reader-independent-audit/independent-audit-v2.json'),'source_independent_audit_sha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'counts':validation['counts'],'author_checks':{'persisted':validation['persisted_check_count'],'actual_viewer_function':validation['actual_viewer_function_checks'],'rendered_identity_previews':29,'rendered_stock_cards':5,'rendered_conformer_projections':9},'public_asset_file_count':len(assets),'bound_files':bound,'bound_file_count':len(bound),'binding_approved':False,'independent_molecular_audit':'pending','site_imported':False,'published':False,'browser_approved':False,'training_approved':False,'limitations':['No product atomic coordinates or precursor-to-product structure transfer','No recovered dissolved species, nanocrystal ligand geometry, hydrate or exact hexane isomer','New graphs are named-identity 2D references only; retained 3D references are illustrative','No stock amount or property is joined across independent canonical records']}
save(O/'package-freeze.json',manifest)
print(json.dumps({'manifest_sha256':sha(O/'package-freeze.json'),'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'stock_map_sha256':sha(O/'stock-component-map.json'),'bound_files':len(bound),'checks':manifest['author_checks']}))
