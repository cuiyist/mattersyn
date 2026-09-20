"""Record completed visual QA and narrowly inspect existing reusable assets."""
import json,hashlib,os,re
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SITE=Path('[local path redacted]')
ASSETS=SITE/'dist/assets'
ROOT=SITE.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(OUT/'manifest.json');errors=[]
assert len(manifest['items'])==13
for item in manifest['items']:
    p=OUT/item['file']
    if sha(p)!=item['sha256']:errors.append(item['id']+' hash mismatch')
    with Image.open(p) as im:
        if list(im.size)!=item['dimensions_px']:errors.append(item['id']+' dimensions mismatch')
    if not item['sample_scope'] or not item['quantitative_context']:errors.append(item['id']+' missing source scope')
    item['visual_review']='passed; final original crop visually inspected for complete figure, caption, labels, scales and symbols'
manifest['rendering_notes']=['Poppler reported fallback-font warnings. Final visible mathematical signs, Greek letters, superscripts, captions, axes and legend symbols were inspected. No glyph, curve, bar or spectrum was reconstructed.','The reaction crop was widened after initial QA to retain the complete free-energy sentence. The corrected crop was re-inspected.']
manifest['validation']={'status':'passed' if not errors else 'failed','asset_count':13,'figure_count':11,'hashes_and_dimensions_checked':True,'all_final_crops_visually_inspected':True,'errors':errors}
dump(OUT/'manifest.json',manifest)
registry_path=ASSETS/'chemical-registry/registry.json';registry=read(registry_path);old={x['id']:x for x in registry['entries']}
REUSE=[
 ('hexane','Hexane','Purification and antisolvent','The registry is an n-hexane reference. The paper specifies HPLC-grade hexane; the molecule must not imply a separately measured solvent formulation.'),
 ('methanol','Methanol','Precipitation; reference-dye solvent','Reference compound only. Electronics-grade source solvent and dye solvent are separate uses.'),
 ('pyridine','Pyridine','Redispersion, surface derivatization and film-feed solvent','Free pyridine model is reusable; actual adsorption geometry and ligand coverage are not known.'),
 ('top','Trioctylphosphine','Coordinating solvent and precursor-solution medium','Molecule does not establish the quantity of DEZn/TOPSe in the 10 mL dosing solution.'),
 ('topo','Trioctylphosphine oxide','CdSe starting-particle synthesis context','The starting-particle route cites Murray1993; do not attach all Murray variants and quantities to this paper by default.'),
 ('topse','Trioctylphosphine selenide','ZnSe overgrowth selenium source','The 1.0 M stock, 0.5 mmol initially added TOPSe, and equimolar dosing mixture are different source contexts. Reusing the molecular identity does not collapse them.'),
 ('dimethylcadmium','Dimethylcadmium','Listed material for referenced CdSe nucleus synthesis','Vacuum transfer is explicit here; detailed nucleus-synthesis quantities are deferred to cited work.'),
 ('selenium-element','Selenium','Listed material / referenced TOPSe preparation','Elemental Se reference only, not proof of an allotrope or a separate direct injection into overgrowth.'),
 ('argon','Argon','Schlenk atmosphere and flask backfill','Element reference.'),
 ('nitrogen','Nitrogen','Storage of purified pyridine dispersion','Gas identity only.'),
 ('hydrogen','Hydrogen','ES-OMCVD precursor/aerosol carrier','Carrier purified through a palladium cell; the source gives 1000 sccm aerosol transport. Not a particle ligand.'),
 ('helium','Helium','Annealing stream and liquid-helium cryostat','Same elemental reference, two distinct experimental roles and phases. Preserve temperature conflict in the annealing record.'),
 ('identity-silicon-100-wafer','(100) silicon wafer','XRD specimen support','May reuse the solid-support card for the expressly (100) XRD wafer. XRF only says silicon wafer; do not propagate the orientation to that support.')]
reusable=[]
for ident,source_name,role,note in REUSE:
    e=old[ident];paths={k:e[k] for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    for k,p in paths.items():assert sha(ASSETS/'chemical-registry'/p)==e['assetHashes'][k],ident
    reusable.append({'registry_id':ident,'source_name':source_name,'source_locator':'Main PDF pp. 2–4, experimental and annealing sections','role':role,'status':'reuse_reference_with_scope_note','formula':e.get('formula'),'sourceUrls':e.get('sourceUrls',[]),'assetPaths':paths,'assetHashes':e.get('assetHashes',{}),'limitation':note})
missing=[
 {'source_name':'Diethylzinc','formula':'C4H10Zn','status':'new molecular identity needed','role':'Solution overgrowth reagent and separate OMCVD matrix reagent','limitation':'Same reference identity may be reused for two distinct supplier/preparation contexts; preserve filtered Aldrich versus electronic-grade Texas Alkyls use. No stock quantity or association state inferred.'},
 {'source_name':'Acetonitrile','formula':'C2H3N','status':'new molecular identity needed','role':'ES-OMCVD dispersion cosolvent','limitation':'Source says 2-fold excess; retain the original ratio wording rather than silently assigning a volume or final concentration basis.'},
 {'source_name':'Nonane','formula':'C9H20','status':'new molecular identity needed','role':'Optional redispersion aid','limitation':'Small amount only if necessary; dose is not reported.'},
 {'source_name':'Hydrogen selenide','formula':'H2Se','status':'new molecular identity needed','role':'OMCVD matrix selenium precursor','limitation':'Distinct from TOPSe; 20 µmol/min belongs to the matrix gas feed.'},
 {'source_name':'Butanol','formula':'C4H10O','status':'isomer not explicitly specified','candidate_registry_id':'1-butanol','role':'Alcoholysis of residual DEZn','limitation':'Source does not print n-butanol or 1-butanol. Existing 1-butanol should not be asserted as an exact identity without qualification or further evidence.'},
 {'source_name':'Rhodamine 590','formula':None,'status':'source-specific identity card / verification needed','role':'PL-yield reference in methanol','candidate_registry_id':'identity-rhodamine-6g-unspecified-salt','limitation':'Do not equate the source label to the existing R6G card or assert counterion/formula without verified identity mapping.'},
 {'source_name':'0.2 µm PTFE filters','formula':None,'status':'polymer apparatus card needed if displayed','role':'Filtration','limitation':'No discrete PTFE molecule, chain length or finite molecular model is established.'},
 {'source_name':'Degreased glass microscope slides','formula':None,'status':'support card needed if displayed','role':'ES-OMCVD substrate; glass also supports the separate annealing film','limitation':'Composition and degreasing reagents are not supplied. Existing quartz XRD substrate is not an exact replacement.'},
 {'source_name':'Nickel/carbon TEM grids','formula':None,'status':'composite support card needed if displayed','role':'HRTEM sample support','limitation':'Do not reuse copper/carbon grid as the same material.'},
 {'source_name':'Carbon overcoat','formula':'C','status':'support card needed if displayed','role':'Electron-beam stabilization','limitation':'Not the same identity as a holey-carbon film or carbon whisker; no carbon allotrope or atomic model is reported.'},
 {'source_name':'CdSe powder standard','formula':'CdSe','status':'source-scoped standard card needed if displayed','role':'XRF standard, 99.99%, Alfa','limitation':'Bulk powder standard is not a synthesized core sample; its crystal coordinates are not reported.'},
 {'source_name':'ZnSe film standard','formula':'ZnSe','status':'source-scoped standard card needed if displayed','role':'XRF standard grown by OMCVD in authors’ laboratory','limitation':'Not a colloidal ZnSe synthesis contribution and not interchangeable with the ZnSe shell.'},
 {'source_name':'Palladium purification cell','formula':'Pd','status':'equipment component only','role':'Hydrogen purification','limitation':'No Pd nanocrystal synthesis or measured structure; a reference material card is sufficient if needed.'}]
crystal_registry=read(ASSETS/'crystal-references/registry.json')
cdse=read(ASSETS/'cdse-structures/download-manifest.json')
cif=ASSETS/'cdse-structures/cdse-wurtzite-cod-9016056-original.cif'
assert sha(cif)==cdse['downloads'][0]['sha256']
crystals={'cdse_bulk_reference':{'file':'assets/cdse-structures/cdse-wurtzite-cod-9016056-original.cif','sha256':sha(cif),'source':cdse['parentReference'],
 'proposed_scope':'Optional external wurtzite CdSe reference alongside Figure 3(d); not experimental coordinates of Danek’s initial particles or heterostructures.','eligible_training':False},
 'do_not_reuse_as_sample':['The existing Murray-sized 3.5×3.0 nm illustrative CdSe finite cluster is not the Danek 4.0/6.8 nm population.','The earlier ideal Si model is at most a generic substrate reference, not measured wafer coordinates.','No perfect concentric CdSe/ZnSe atomistic shell should be inferred from the schematic architecture or composition.'],
 'znse_registry_status':'No ZnSe entry in the currently inspected public crystal registry. Figure 3 supplies wurtzite reference lines; Figures 9/10 instead show cubic-ZnSe bulk band-gap markers, which are different contexts.','registered_crystal_ids':[x['id'] for x in crystal_registry['entries']],
 'sample_phase_limit':'The paper does not resolve a unique shell lattice from its broad XRD features and HRTEM. No actual-sample CIF, SAED pattern or refined core/shell coordinates are supplied.'}
reuse={'source_doi':'10.1021/cm9503137','source_sha256':manifest['source_sha256'],'chemical_registry_sha256':sha(registry_path),'reusable_references':reusable,'missing_or_unresolved':missing,'crystal_references':crystals,
 'binding_status':'Planning only. No registry additions, bindings, molecular generation or Site modification performed.',
 'other_source_materials':['Pyridine-capped CdSe nuclei and overcoated CdSe/ZnSe nanocrystals require source-scoped material/state cards; do not reuse another paper’s batch-specific identity.','Chromium XRF anode, Si:Li detector and silicon photodiode are instrument components, not synthesis reagents.','Unspecified TEM rinse solvent, glass degreaser and glovebox atmosphere must remain unspecified.']}
dump(OUT/'asset-reuse-plan.json',reuse)
print(json.dumps({'crop_assets':len(manifest['items']),'validation':manifest['validation']['status'],'reusable_references':len(reusable),'missing_or_unresolved':len(missing),'manifest_sha256':sha(OUT/'manifest.json')}))
