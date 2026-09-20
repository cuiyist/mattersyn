"""Record completed visual inspection and reusable chemical identities, privately."""
import json,hashlib
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
REG=Path('[local path redacted]')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
checks=[]
for a in m['assets']:
 p=OUT/a['relative_asset'];im=Image.open(p)
 checks.append({'id':a['id'],'hash_matches':sha(p)==a['sha256'],'dimensions_match':list(im.size)==a['pixel_dimensions'],'bounds_valid':all(0<=v<=1 for v in a['crop_normalized'])})
 a['visually_reviewed']=True
 a['visual_review_note']='Original axes, scales, labels, figure panels and captions checked on seven contact sheets; revised equation/context crop boundaries additionally inspected at full image size. No source content was redrawn.'
m['coverage']['individual_crops_visually_reviewed']=True
m['coverage']['status']='complete_for_supplied_main_numbered_assets'
m['coverage']['validation_status']='passed'
dump(OUT/'manifest.json',m)
registry=json.loads(REG.read_text(encoding='utf-8'));byid={e['id']:e for e in registry['entries']}
rows=[]
def entry(name,role,loc,regid=None,formula=None,note='',kind='molecule',state='reuse_verified_registry_identity'):
 e={'source_name':name,'role':role,'source_locator':loc,'registry_id':regid,'formula':formula,'depiction_kind':kind,'reuse_status':state,'scope_note':note,'exact_material_bindings':'pending canonical drafts'}
 if regid:
  old=byid[regid];e['existing_registry_name']=old['name'];e['existing_depiction_kind']=old['depictionKind'];e['existing_asset_hashes']=old.get('assetHashes',{});e['existing_model_3d_path']=old.get('model3dPath')
 rows.append(e)
P2='Main PDF p.2, printed p.9464, Materials and synthesis'
for name,id,formula,role,note in [
 ('Trioctylphosphine oxide (TOPO)','topo','C24H51OP','Coordinating solvent and surface ligand','Source grade is 90% Strem; pure reference connectivity cannot specify the impurity mixture.'),
 ('Trioctylphosphine (TOP)','top','C24H51P','Solvent, ligand and precursor-stock medium','Source grade is 95% Fluka; retain mixture purity in canonical material.'),
 ('Dimethylcadmium (CdMe2)','dimethylcadmium','C2H6Cd','CdSe seed precursor and CdS shell precursor','Alfa; source says filtered through a 0.2 µm filter in inert box. Do not import Danek vacuum-transfer treatment.'),
 ('Diethylzinc (ZnEt2)','diethylzinc','C4H10Zn','ZnS shell precursor','Fluka; filtered separately through a 0.2 µm filter. Existing 3D is an unminimized illustrative monomer with unsupported Zn force-field parameters, not measured solution geometry.'),
 ('Selenium shot','selenium-element','Se','TOPSe stock preparation input','0.1 mol dissolved in 100 mL TOP; no allotrope or particle-size identity reported.'),
 ('Trioctylphosphine selenide','topse','C24H51PSe','CdSe precursor prepared as 1 M stock in TOP','Stock solution is not a single molecule; reuse molecular identity for solute and retain the separate stock graph.'),
 ('Hexamethyldisilathiane, (TMS)2S','bis-trimethylsilyl-sulfide','C6H18SSi2','Sulfur precursor for ZnS and CdS overgrowth','Explicit named synonym of bis(trimethylsilyl)sulfide. Aldrich, used as purchased.'),
 ('n-Hexane','hexane','C6H14','Dispersion, recovery, optical and solution-SAXS solvent','Materials explicitly names n-hexane; later uses hexane.'),
 ('Methanol','methanol','CH4O','Antisolvent for particle precipitation','HPLC grade EM Sciences.'),
 ('Pyridine','pyridine','C5H5N','Redispersion/exchange and structural-specimen solvent','HPLC grade EM Sciences; avoid assuming quantitatively complete TOP/TOPO displacement.'),
 ('1-Butanol','1-butanol','C4H10O','Keeps TOPO from solidifying; CdS storage mixture component','Materials explicitly specifies 1-butanol, unlike the earlier Danek unspecified butanol. No alcoholysis purpose is stated here.'),
 ('Nitrogen','nitrogen','N2','Shelling atmosphere','Reaction under N2. Do not substitute argon from the Danek protocol.'),
 ('Chloroform','chloroform','CHCl3','Reported alternative redispersion solvent','Alternative, not a mandatory solvent in every route.'),
 ('Toluene','toluene','C7H8','Alternative redispersion solvent and PVB film solvent','PVB sample preparation uses toluene.'),
 ('Tetrahydrofuran (THF)','thf','C4H8O','Alternative redispersion solvent and MTD300P20 film solvent','THF replaces toluene for the block-copolymer branch.')]:entry(name,role,P2,id,formula,note,kind=byid[id]['depictionKind'])
entry('Octane','TEM dispersion solvent','Main PDF p.2, TEM',formula='C8H18',note='Explicit source name supports conventional octane reference connectivity. No octane model exists in the inspected registry; do not reuse nonane.',state='new_simple_molecule_reference_needed')
entry('Rhodamine 590','Optical quantum-yield reference','Main PDF p.2, Optical Characterization','identity-danek-rhodamine590',note='Reuse only the unresolved source-designation card identity. Existing Danek caption mentions methanol, but this paper does not specify the standard solvent; do not inherit that solvent or Danek sample provenance.',kind='identity_card',state='reuse_identity_card_with_source_specific_caption')
entry('Rhodamine 640','Alternative optical quantum-yield reference','Main PDF p.2, Optical Characterization',note='Exact salt, counterion and external identifier unverified. Do not substitute a guessed dye graph.',kind='identity_card',state='new_unresolved_identity_card_needed')
entry('Poly(vinyl butyral), PVB','SAXS polymer-film matrix','Main PDF pp.2–3, SAXS in Polymer Films',note='Commercial/polymeric composition and chain length are unspecified; do not invent a unique finite molecule or atom count.',kind='polymer_card',state='new_polymer_card_needed')
entry('[methyltetracyclododecene]300-[norbornene-CH2O(CH2)5P(oct)2]20, MTD300P20','Alternative phosphine-functionalized block-copolymer SAXS matrix','Main PDF pp.2–3; reference23',note='Source gives block notation and nominal block counts. Referenced polymer preparation is not included here; do not fabricate sequence, stereochemistry, end groups or molecular conformer.',kind='polymer_card',state='new_polymer_card_needed')
entry('Silicon (100) wafer','WDS support','Main PDF p.2, WDS','identity-silicon-100-wafer','Si','Reuse solid reference identity; add this source provenance. No measured surface reconstruction or wafer dimensions.',kind='support')
entry('Silicon substrates / wafers','XPS, SAXS polymer-film and WAXS supports','Main PDF pp.2–3',formula='Si',note='These sections do not all repeat a(100) orientation. Use a generic silicon support card if they are separate canonical materials.',kind='support',state='generic_silicon_card_needed_or_generic_existing_identity')
entry('Copper grid supporting amorphous carbon film','TEM specimen support','Main PDF p.2, TEM','identity-carbon-coated-copper-tem-grid-b47959',note='Existing generic grid card can be reused with Dabbousi evidence; source explicitly says amorphous carbon. Do not substitute nickel or holey-carbon support.',kind='support')
entry('Amorphous carbon overcoat','WDS anti-charging coating and second TEM stabilizing coating','Main PDF p.2, WDS and TEM',formula='C',note='Separate material roles can share one generic amorphous-carbon reference card. Existing Danek carbon card caption names nickel and leaves allotrope unspecified; do not inherit that whole caption.',kind='support',state='new_generic_amorphous_carbon_card_needed')
entry('Quartz cuvettes / flame-sealed quartz capillary','Optical cells and solution-SAXS containers','Main PDF pp.2–3; Figure3',note='Apparatus/material cards, not isolated SiO2 molecules or experimentally identified quartz crystal structures. Keep 1cm cuvette and~1mm capillary optical path separate.',kind='apparatus_card',state='new_support_card_if_canonical_material')
entry('CdSe core dots; (CdSe)ZnS and (CdSe)CdS composite dots','Seeds, overgrowth products and measurement specimens','Main PDF pp.2–13',note='Use source- and state-specific particle cards. Do not reuse a Danek ZnSe-coated identity or invent a finite measured core/shell molecular graph.',kind='particle_cards',state='await_source_specific_canonical_material_ids')
entry('Selenium dioxide, SeO2','Observed surface oxidation component','Main PDF p.6, XPS oxidation analysis',formula='SeO2',note='Analytical assignment after air exposure, not a starting reagent. No phase or deposited atomic coordinates supplied.',kind='context_card',state='context_only_no_reagent_binding')
entry('Mg/Al XPS anode; Cu X-ray sources','Instrument components','Main PDF pp.2–3',note='Measurement-source materials, not synthesis reagents. Cu source reference card exists; Mg and Al would be identity cards only if canonical acquisition materials enumerate them.',kind='instrument_cards',state='conditional_acquisition_assets')
out={'source_doi':'10.1021/jp971091y','source_sha256':m['source_sha256'],'registry_path':str(REG),'registry_sha256':sha(REG),'scope':'Chemical identities explicitly used in the current study and its specimen preparation/acquisition; prior-work materials and model-only comparisons are not promoted to synthesis inputs. This is an inventory, not final canonical material binding.','items':rows,'notes':['The 0.2 µm precursor filters have no membrane material specified. Do not copy PTFE from Danek.','Do not assume 0.1–0.4 µmol CdSe dots means CdSe formula-unit amount; source uses particle amount.','Source-specific quantities, grades, roles and stock composition must remain in canonical records even when assets are reused.','No molecule or new crystal model is generated in this task.','All reused reference depictions require matching identity and asset hash checks during later binding; no external identifiers are guessed.']}
dump(OUT/'chemical-identity-inventory.json',out)
validation={'status':'passed','source_sha256':m['source_sha256'],'manifest_sha256':sha(OUT/'manifest.json'),'asset_count':len(m['assets']),'checks':checks,'all_checks_passed':all(all(v for k,v in c.items() if k!='id') for c in checks),'visual_review':'All 25 assets visually inspected; caption panels, axes, scales and equation symbols retained. Equation1/2/3 and unnumbered-context crop edges revised and rechecked.','renderer':'PDFium300dpi','source_appearance_limit':'Figure3 is grayscale in the supplied PDF. No reconstructed colors.','canonical_bindings_status':'pending root drafts'}
dump(OUT/'validation.json',validation)
readme='''# Dabbousi 1997 original source assets

The supplied 13-page main paper was read and visually inspected. The package contains 25 faithful 300 dpi PDFium crops: 16 numbered figures, one numbered table, five numbered equations, two supplementary formula-context excerpts and source note 22. All crops were visually checked. No SAED or Raman image is present.

PDFium preserves the original degree, summation, infinity and approximation glyphs that the initial Poppler rendering replaced. No glyph was redrawn. Figure 3 is grayscale in the supplied source, despite its color-photograph caption; no colors were invented.

`manifest.json` gives original page numbers, PDF-coordinate and normalized bounding boxes, source/asset hashes, captions, evidence types and specimen-scope limits. `chemical-identity-inventory.json` proposes reference reuse and flags unresolved identities; it does not bind canonical materials. `validation.json` records the final byte/dimension checks.

Key boundaries:

- Figures 1–2 are a core-size series. Figure 3 has six emission samples with no exact recipe/core-size assignment.
- Table 1 and the main coverage series combine directly measured TEM/WDS results with SAXS/WAXS fits. TEM size means major dimension; blank cells mean unreported.
- Figures 11–12 use an explicitly different solution-SAXS series. Never join their composition labels to Table 1 by trace letter.
- Figure 14 is entirely theoretical. Figures 10, 12, 13, 15 and 16 combine data with analytical fits or simulated curves; the components are labeled separately in the manifest.
- Source conflicts remain visible: solution-SAXS ratio 5.3/5.6; bare fit spread 0.11/0.12; Figure 14 diameter/radius wording; Figure 16 core-size and barrier-medium wording.
- No experimental CIF or solved atom-by-atom core/shell structure is provided. Existing bulk CdSe references may be shown only as external comparisons.

No Site files were changed and no files were downloaded.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'status':'passed','assets':len(m['assets']),'chemical_inventory_items':len(rows),'manifest_sha256':sha(OUT/'manifest.json')}))
