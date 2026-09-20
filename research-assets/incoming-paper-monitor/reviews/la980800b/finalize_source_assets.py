from pathlib import Path
import json,hashlib,re
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'crop-assets'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(O/'manifest.json');checks=[]
def polish(s):
 s=re.sub(r'\b(Figure|Table|Scheme|note|to|spans|approximately|assume|assuming|at|than|within|Same|same|gives|shows|mean|spread|slope|N|Q|sigma)(?=[0-9])',r'\1 ',s)
 s=re.sub(r'\b(at|to|for)(?=[−≈])',r'\1 ',s)
 return s.replace('each sample. Approximate','each sample. Approximate').replace('Fifteen depositions at−','Fifteen depositions at −').replace('at300','at 300').replace('0.999','0.999')
for a in m['assets']:
 for key in ['title','caption_paraphrase','sample_scope','renderer']:a[key]=polish(a[key])
 for key in ['scope_caveats','panels']:a[key]=[polish(s) for s in a[key]]
 a['visually_reviewed']=True
 p=O/a['relative_asset'];im=Image.open(p);checks.extend([{'check':a['id']+' actual hash','passed':sha(p)==a['sha256']},{'check':a['id']+' dimensions','passed':list(im.size)==a['pixel_dimensions']},{'check':a['id']+' crop bounds','passed':all(0<=v<=1 for v in a['crop_normalized'])},{'check':a['id']+' original/reference training flags','passed':a['original_source_asset'] and not a['synthetic'] and not a['eligible_training']}])
m['coverage']['individual_crops_visually_reviewed']=True
m['visual_review_scope']='All nine full source pages and all fifteen 300 dpi crops were inspected. Full caption and axis/panel context retained; standalone measured SAED panel links to parent Figure 6. No source pixel editing beyond rectangular crops.'
save(O/'manifest.json',m);save(O/'validation.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'manifest_sha256':sha(O/'manifest.json')})
REG=Path('[local path redacted]');entries={e['id']:e for e in read(REG/'registry.json')['entries']};reuse=['water','ethanol','nitrogen','sulfuric-acid','hydrogen-fluoride','acetonitrile'];refs=[]
for rid in reuse:
 e=entries[rid];hs={k:v for k,v in e.get('assetHashes',{}).items()};valid={k:sha(REG/e[k])==h for k,h in hs.items()}
 refs.append({'registry_id':rid,'name':e['name'],'formula':e['formula'],'asset_hashes':hs,'hash_checks':valid,'source_scoped_notes':'Reference chemical identity only. Source concentrations, mixture ratios and treatments must come from Stiger 1999, not this registry entry\'s prior-paper context.','caption_neutralization_needed':rid=='sulfuric-acid'})
new=[
 ('n++-Si(100), Sb doped','Si','solid substrate card','As-received and H-terminated states must differ; doping 10^20 cm−3 is not a stoichiometric compound or measured defect map.'),
 ('n-Si(100), Sb doped','Si','solid substrate card','Nondegenerate 10^15 cm−3 comparison; distinguish from deposition substrate n++-Si.'),
 ('Gallium-indium eutectic',None,'mixture/alloy card','Composition and phase geometry unreported; contact material, not particle precursor.'),
 ('Colloidal silver paint',None,'formulation card','Silver-containing contact paint; binder, solvent and silver fraction unspecified.'),
 ('Silver perchlorate monohydrate','AgClO4·H2O','ionic component reference','Explicit source reagent; disconnected Ag+, perchlorate and water components, no molecular coordination geometry.'),
 ('Lithium perchlorate','LiClO4','ionic component reference','No hydrate specified. Supporting electrolyte, not Ag feed.'),
 ('Silver wire','Ag','solid electrode card','Reference electrode in silver-containing solutions; not the deposited nanocrystal specimen.'),
 ('Platinum wire','Pt','solid electrode card','Counter electrode; no Pt synthesis or nanoparticle outcome.'),
 ('Saturated calomel electrode',None,'reference-electrode equipment card','Used in silver-free solutions; final potentials referenced to Ag. Do not invent a numerical conversion or exact electrode electrolyte recipe.'),
 ('Carbon-coated gold TEM grid',None,'composite support card','Mechanical particle transfer; coating thickness, grid mesh and transfer tool unreported.'),
 ('Highly oriented pyrolytic graphite','C','solid calibration-reference card','Single-crystal flakes used for astigmatism correction, not a synthesized graphite product.'),
 ('Teflon holder',None,'polymer equipment card','0.28 cm² exposed wafer area; no finite PTFE molecule or unit cell.'),
 ('Diamond scribe','C','equipment card','Back-contact scratching tool; no source-grown diamond or nanoparticle product.'),
 ('Silver nanoparticles on H-Si(100)',None,'composite product illustration','No single solved Ag/Si lattice, atomically measured interface, assigned Ag-H bonds or oxide thickness.'),
 ('Transferred silver nanoparticles','Ag','product illustration','Same source TEM/SAED scope; no exact pulse-duration or batch assignment.'),
 ('Surface silicon oxide','SiO2','surface-state card','Oxidized preparation or electrochemical passivation state; no crystalline polymorph or refined interface.'),
 ('Glass electrochemical cell',None,'equipment card','Cell geometry and glass formulation unreported.'),
 ('Ultralever AFM probes',None,'equipment card','Source gives Ultralever dimensions of 0.6 µm and 2 µm without naming the dimension type, plus an NC resonance range. Tip material and radius are not specified.')]
proposal={'source_id':'stiger1999','source_doi':'10.1021/la980800b','source_sha256':m['source_sha256'],'status':'Identity inventory for root canonical binding; exact material IDs pending','source_identity_locator':'Main PDF p. 2, printed p. 791, Experimental Methods; product-state interpretation throughout pp. 3–9','verified_reuse':refs,'proposed_cards_or_ionic_references':[{'name':x[0],'formula':x[1],'representation':x[2],'limits':x[3]} for x in new],'product_crystal_opportunities':{'Ag':'No verified local Ag CIF/model found in the current eight-entry reference registry. Source Table 1 gives ICDD 03-0931 comparison, not coordinates. Do not substitute Ir FCC or derive a purported measured Ag cell.','Si':'Existing Littau ideal diamond-Si bulk reference may be reused only as a separately attributed bulk-Si illustration. It does not encode Sb doping, (100) hydrogen termination, oxide or Ag interface. Its 3 nm finite-sphere model is inappropriate for these macroscopic wafer substrates.','composite':'No unified experimentally refined Ag/Si lattice or atomistic substrate-plus-particle model.'},'binding_limits':['AgO aqueous-instability discussion and Ag2O candidate phase are characterization context, not separate demonstrated new recipes.','Other metals/substrates in introduction and graphite comparisons are prior work, not additional synthesized products here.','Unknown polymer formulations, electrode mixtures and contacts remain cards, not guessed molecule or crystal files.','Atmospheric water was not rigorously excluded; N2 purging does not imply glovebox preparation or rigorously anhydrous electrolyte.'],'apparatus_plan':['Coupon cutting, backside diamond scratch, Ga-In contact and silver paint; polished face kept distinct from electrical contact.','Chemical oxidation at 80 °C approximately10 min, brief Nanopure rinse, HF/ethanol oxide stripping5 min, water rinse; H-termination shown only after treatment.','Electrolyte stock preparation and N2 purge; silver-containing and silver-free control solutions distinct.','Three-electrode functional cell: Si working electrode, Pt counter, Ag wire reference for plating; SCE for silver-free control. Exposed wafer area0.28 cm², not coupon area1 cm².','Open circuit → applied potential pulse → return to open circuit; exact source duration selected, no interpolated size response.','Immediate withdrawal, pure MeCN rinse and air drying. Unknown rinse volumes, drying time and transfer delay remain unknown.','Separate mechanical TEM-grid transfer, 200 keV printed, SAED500 mm camera length/10 µm aperture, HOPG astigmatism correction; measured pattern linked, never generated.','Contact AFM and NC-AFM separate; source warns contact mode can remove particles. Measured height distinct from tip-convolved lateral diameter.']}
save(R/'chemical-reference-proposal.json',proposal)
print(json.dumps({'crop_count':len(m['assets']),'passed':sum(c['passed'] for c in checks),'manifest_sha256':sha(O/'manifest.json'),'reused_identities':len(refs),'proposed_identity_cards':len(new)}))
