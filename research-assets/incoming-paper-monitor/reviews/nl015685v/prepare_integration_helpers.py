from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'jp010002l'
s=(P/'integrate_review.py').read_text(encoding='utf-8')
s=s.replace('Braun2001','Besson2002').replace('braun2001','besson2002').replace('len(drafts)==9','len(drafts)==12').replace("['asset_count']==8","['asset_count']==10").replace('All four','All six').replace('all four','all six')
s=s.replace('Three CdS/HgS/CdS architectures retain distinct exchange/deposition sequences and source-assigned optical contexts. Counterions, several feed doses and the core-size discrepancy remain unresolved.','Mesoporous silica preparation, repeated CdS pore loading, optical properties and microscopy retain separate host and nanoparticle structure scopes. Copolymer identity, several operation conditions and the Figure4 stage-assignment conflict remain unresolved.')
s=s.replace('Three source-described layer sequences remain distinct. Recipe completeness, actual specimen joins and task eligibility are explicit; named architecture, cited tetrahedral shape and illustrated layers do not supply measured atomic coordinates or exact-structure labels. Water-reference subtraction is not a nanocrystal Raman measurement.','Repeated impregnation and H2S exposure remain a loading trajectory, not independent synthesis batches. Copolymer details, PL substrate identity and caption conflict remain explicit. Mesostructure symmetry and image Fourier power spectra do not become atomic CIF or SAED labels.')
# Replace the source-module dispatch edit block against the current Braun-enabled Site.
a=s.index("p=S/'dist/protocol-visuals.mjs'");z=s.index("p=S/'data/measurement-display.json'",a)
s=s[:a]+'''p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8');assert "from './besson2002-protocol.mjs'" not in t
t="import {buildBesson2002Scene,createBesson2002Art} from './besson2002-protocol.mjs';\\n"+t
t=t.replace('const sourceArt=createBraun2001Art','const sourceArt=createBesson2002Art(o,r)||createBraun2001Art')
t=t.replace('braun=buildBraun2001Scene(o,r);','braun=buildBraun2001Scene(o,r),besson=buildBesson2002Scene(o,r);')
t=t.replace('braun?.caption||','besson?.caption||braun?.caption||')
t=t.replace('||gerion||braun){','||gerion||braun||besson){').replace('=>(gerion||braun)?','=>(gerion||braun||besson)?')
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8');t=t.replace("'gerion2001','braun2001']","'gerion2001','braun2001','besson2002']")
t=t.replace(" if(r.lineage?.source_group==='braun2001'&&entryId)"," if(r.lineage?.source_group==='besson2002'&&entryId)host.append(el('p','Pore and particle illustrations describe the mesoscopic arrangement. The original HRTEM supports some blende-type CdS 111 fringes; P6₃/mmc and nanometre lattice dimensions describe the mesostructure. Figure 3d is an image Fourier power spectrum, not SAED. No measured atomic coordinates or source CIF are supplied.','guide-notice'));\\n if(r.lineage?.source_group==='braun2001'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\\nNAMES['CdS/SiO2']='CdS nanocrystals in mesoporous silica'\\nNAMES['SiO2']='Mesoporous silica films'");p.write_text(t,encoding='utf-8')
'''+s[z:]
s=s.replace("['diameter','size','thickness','shape','morphology','well_count','layer_count','architecture']","['diameter','size','thickness','shape','morphology','lattice','mesostructure','space_group','pore','filling','contrast','fringes','orientation','phase']")
s=s.replace("replace(\"'dataset_version':'0.14.0'\",\"'dataset_version':'0.15.0'\")","replace(\"'dataset_version':'0.15.0'\",\"'dataset_version':'0.16.0'\")")
s=s.replace("replace('0.14.0-r1','0.15.0-r1')","replace('0.15.0-r1','0.16.0-r1')")
s=s.replace('Imported 9 audited','Imported 12 audited')
(B/'integrate_review.py').write_text(s,encoding='utf-8')
t=(P/'run_build.py').read_text(encoding='utf-8').replace('braun2001-protocol','besson2002-protocol');(B/'run_build.py').write_text(t,encoding='utf-8')
t=(P/'build_inventory_actual.py').read_text(encoding='utf-8').replace('braun','besson').replace('2001','2002').replace('All four supplied','All six supplied').replace("'page_count':4","'page_count':6")
a=t.index("'notes':['Three CdS/HgS/CdS");z=t.index("\ninv['per_paper']",a)
t=t[:a]+"'notes':['Silica-host preparation and two host-specific CdS loading routes preserve precursor composition, repeated impregnation/rinse/vacuum/H2S operations and incomplete copolymer preparation.','Original four figures and six methodological/source-note excerpts are retained. Optical, XRD, HRTEM, SIMS and silicon-wafer PL specimen scopes are separate.','Figure3d is an image Fourier power spectrum, not SAED. Mesostructure lattice parameters differ from atomic CdS blende-type fringes.','The Figure4 caption/prose conflict, optical pore-filling estimate and residual empty pores remain explicit. No measured atomic CIF or absent raw spectrum is invented.']}"+t[z:]
t=t.replace("'three_besson_routes':row['synthesis_route_variant_count']==3,",'').replace("'no_new_unpaired_size_labels':elig['size_conditioned_recipe']==15,",'')
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
print('Root import/build helpers staged. No Site edits performed.')
