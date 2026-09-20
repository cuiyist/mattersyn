"""Private Ghosh molecular author freeze; independent approval remains separate."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(O/'package-freeze.json').exists()
persisted=read(O/'persisted-validation.json');viewer=read(O/'viewer-contract-validation.json')
assert persisted['status']=='passed_author_persisted_checks'and viewer['status']=='passed'
inputs=read(O/'input-bindings.json')
for p,h in inputs.items():assert sha(p)==h,p
entries=read(O/'registry-additions.json')['entries'];visual_paths=[p for folder in ['previews','stock-previews','conformer-previews']for p in sorted((O/folder).glob('*.png'))]
assert len(visual_paths)==38
visual={'author':'/root/backlog_eta','status':'rendered_author_visual_review_passed','reviewed_at':datetime.now(timezone.utc).isoformat(),'actual_scope':'All 25 identity cards, ten retained-coordinate projections and three stock cards actually viewed across eight contact sheets. The final TOP–Se injection stock card was reopened after removing irrelevant per-layer language. No browser or independent scientific audit claim.','reviewed_assets':{str(p.relative_to(O)):sha(p)for p in visual_paths},'contact_sheets':{str(p.relative_to(O)):sha(p)for p in sorted((O/'contacts').glob('*.png'))},'scientific_focus':['Terminal 1-octadecene versus saturated linear octadecane','Primary oleylamine versus secondary di-n-octylamine and unresolved SI naming conflict','Free TOP, TOPO and named TOP–Se connectivity kept separate','Cis molecular references do not establish technical reagent isomer purity','Elemental sulfur/selenium versus unresolved precursor-stock species','Cd-oleate and Rhodamine 6G incomplete identity remains symbolic','NIST nitrogen reference is detector coolant, not synthesis atmosphere','Whole injection charges, two 0.2 M stocks and evolving Cd:OA ratios without invented layer doses','No atomic nanocrystal or surface ligand coordinates'],'browser_validation':'not_claimed','independent_approval':False}
save(O/'author-visual-review.json',visual)
validation=read(O/'author-validation.json');validation.update(status='author_automated_and_rendered_visual_checks_passed',persisted_check_count=persisted['check_count'],actual_viewer_function_checks=viewer['check_count'],visual_review_sha256=sha(O/'author-visual-review.json'));save(O/'author-validation.json',validation)
notes='''# Ghosh 2012 — private molecule and stock proposal

This package maps all 88 material slots in the frozen 21-record canonical v1 proposal and all three stocks/eight component slots. The complete main/SI source extraction passed a separate revision-2 audit. Canonical and molecular independent approvals remain separate; all registry/binding approval flags here are false. No Site or shared state was changed and no network retrieval was used.

Twenty-five source identities have distinct reference cards. Thirteen have checked 2D connectivity: oleic acid, 1-octadecene, octadecane, oleylamine, dioctylamine, TOP, TOPO, TOP–Se, ethanol, hexane, toluene, acetone and nitrogen. Eleven reuse exact local named references; the two new 2D graphs are linear octadecane and di-n-octylamine, supported by the named source identity and checked formula/chain topology. Ten retained illustrative 3D models preserve every cached atom/bond/coordinate array. No new 3D conformer or nanocrystal coordinates were generated. TOP–Se uses connectivity only; its cached embedding-only conformer is deliberately excluded.

Oleic acid and oleylamine show qualified cis reference identities; they do not establish an isomer assay or the composition of the 90%/technical-grade reagents. Dioctylamine contains two straight eight-carbon substituents around an NH centre; the source's SI secondary-amine versus oleylamine/NH2 conflict remains unresolved. Octadecane follows the conventional saturated identity while preserving the source's literal 1-octadecane wording. Straight-chain hexane is an illustrative reference, without a source grade or isomer-composition assay.

Twelve identities stay symbolic: CdO, elemental sulfur, elemental selenium, cadmium oleate, argon, R6G, glass, silicon, diamond, immersion oil, CdSe cores and CdSe/CdS particles. These cards do not invent a Cd=O molecule, S8 allotrope, Se chain, cadmium-oleate coordination/hydration, dye counterion, oil composition, substrate orientation, bound-ligand configuration or particle lattice. The silicon and diamond entries are measurement supports. Product-family entries are material identities, not product/sample coordinate bindings.

The nitrogen model is the qualified NIST 14N2 ground-state 1.09768 Å reference; the historical 1.460 Å model is rejected. Here nitrogen is liquid detector coolant, not a synthesis atmosphere or added reagent. Argon is scoped to reported core heat-up. Storage, gas-flow and unreported reagent amounts remain unknown rather than inherited from another paper.

Slot notes preserve exact canonical quantities and typed grades, including selenium ≥99.999% and approximate 2×10−7 mol core charge. Dose links distinguish the 8 mL initial ODE charge from 1 mL injection ODE and the 0.38 mmol initial cadmium charge from the separate 0.8 mmol extra-feed branch. Source comparison quantities are labeled context rather than universal charges: initial amine, later OA, dot dilution, withdrawal fraction, OA factor and 5–8-cycle transition. Every value has a canonical JSON pointer and record hash.

The TOP–Se injection selector preserves 4 mmol TOP–Se, 3 mL oleylamine and 1 mL ODE as one source formulation; it is not an additional dosing event or a calibrated final volume. The sulfur/OD and cadmium-oleate/OA/OD stocks retain 0.2 mol/L precursor concentration. Their absolute component amounts, final volumes and layer-specific aliquots remain unreported. Cd:OA 1:4 then 1:10 are formulation ratios, not a molecular complex stoichiometry. No elemental-S, CdO or Se/TOP upstream preparation is fabricated.

Reference snapshots retain exact prior registry entries, models, SVGs and available primary cache records; the public candidates contain source-neutral model prose plus Ghosh-specific binding captions. Other-paper grades and specimen conditions are removed from display metadata. The public allowlist includes only 25 SVG identity cards and 23 model JSON files. Local reference snapshots, source paths, contact sheets, author programs and validation outputs are not public model assets.

Generation, persisted graph/formula/stereochemistry/indices/geometry checks, exact slot/stock/quantity checks and actual chemicalEntry contract tests passed. All 38 static previews were actually viewed. In-memory approval simulations verify the current viewer overrides; saved flags remain false. This is not a browser review, independent molecular audit, publication approval or training admission.
'''
(O/'README.md').write_text(notes,encoding='utf-8')
assets={}
for e in entries:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):
   assets[e[k]]=sha(O/e[k]);assert not re.search(r'[A-Z]:[\\/]|/Users/',(O/e[k]).read_text(encoding='utf-8')),e[k]
assert len(assets)==48
save(O/'public-asset-proposal.json',{'status':'private_allowlist_pending_independent_molecular_audit','relative_asset_files':assets,'count':48,'excluded':['reference-snapshots','contacts','previews','stock-previews','conformer-previews','stock-svg','author programs','validation and local input path maps'],'note':'Assets only. Registry/binding/component-selector proposals require separate approval. No source page, raw source text or product coordinate asset is included.'})
bound={str(p):sha(p)for p in sorted(O.rglob('*'),key=str)if p.is_file()};bound.update(inputs)
manifest={'schema':'mattersyn-private-molecular-proposal/1','source_id':'ghosh2012','doi':'10.1021/ja212032q','author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_checks_passed_independent_molecular_audit_pending','canonical_version':1,'canonical_package_sha256':sha(P/'canonical-proposal/v1/package-manifest.json'),'canonical_independent_audit':'separate_pending_at_author_freeze','source_independent_audit_sha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'counts':validation['counts'],'author_checks':{'generation':validation['check_count'],'persisted':persisted['check_count'],'actual_viewer_function':viewer['check_count'],'rendered_identity_previews':25,'rendered_stock_cards':3,'rendered_conformer_projections':10},'quantity_reference_count':persisted['quantity_reference_count'],'public_asset_file_count':48,'bound_files':bound,'bound_file_count':len(bound),'binding_approved':False,'independent_molecular_audit':'pending','site_imported':False,'published':False,'browser_approved':False,'training_approved':False,'limitations':['No product/sample bindings or new atomic coordinates','No unreported precursor complex, dissolved speciation, allotrope, surface coverage or salt identity','Two new 2D named references only; all retained 3D arrays unchanged','No exact final stock volume or inferred aliquot dose','Source comparisons/grades remain distinct from material charge amounts']}
save(O/'package-freeze.json',manifest)
print(json.dumps({'manifest_sha256':sha(O/'package-freeze.json'),'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'stock_map_sha256':sha(O/'stock-component-map.json'),'bound_files':len(bound),'checks':manifest['author_checks']}))
