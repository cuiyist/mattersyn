from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;REG=Path('[local path redacted]')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
old={e['id']:e for e in json.loads(REG.read_text(encoding='utf8'))['entries']}
rows=[
('resin','Chelex 100 iminodiacetate chelate resin',None,None,'polymer_motif','As-purchased styrene-divinylbenzene copolymer; 200–400 mesh. Draw the local −CH2N(CH2COO−)2 motif only, not a finite polymer or a fixed charge-balanced chain.'),
('cd-loaded-resin','Cadmium-loaded Chelex 100',None,None,'loaded_polymer_card','Cd2+ uptake state after aqueous loading; coordination number, ligand denticity, stoichiometry per site and exact network are unreported.'),
('hybrid','CdS nanocrystal / Chelex 100 hybrid',None,None,'composite_card','Embedded CdS nanocrystals in polymer microparticles. Particle regional distribution and sample a/b conditions remain source-specific; no atomic core-shell interface or polymer coordinates.'),
('cd-acetate','Cadmium acetate dihydrate','Cd(C2H3O2)2·2H2O',None,'disconnected_ionic_2d','Explicit dihydrate; do not reuse hydration-unspecified Veinot cadmium acetate. Ionic component drawing supplies stoichiometry only, not Cd coordination or lattice.'),
('na2s','Sodium sulfide nonahydrate','Na2S·9H2O','identity-veinot-na2s','reuse_formula_card','Source salt feed; water speciation is discussed separately as Na+, HS− and OH−.'),
('nacl','Sodium chloride','NaCl',None,'disconnected_ionic_2d','Main electrolyte; 10 mL of 0.5 M solution pretreatment, with unresolved postmix concentration basis.'),
('hcl','Hydrochloric acid','HCl',None,'disconnected_ionic_2d','2 M aqueous resin-washing reagent; H+/Cl− schematic does not assign hydration clusters or an isolated gas-phase HCl molecule to the solution.'),
('naoh','Sodium hydroxide','NaOH',None,'disconnected_ionic_2d','2 M aqueous resin-washing reagent. Separate Na+ and OH− components, no invented covalent Na–O bond.'),
('water','Distilled water','H2O','water','reuse_molecule','Distilled water identity; no degassing or source-specific treatment from earlier papers.'),
('methanol','Methanol','CH4O','methanol','reuse_molecule','Conditioning wash; not the growth solvent or a new polymer monomer.'),
('ethanol','Ethanol','C2H6O','ethanol','reuse_molecule','Conditioning treatment and hybrid workup wash; no quantified charge or wash cycle count.'),
('licl','Lithium chloride','LiCl',None,'disconnected_ionic_2d','Footnote 25 qualitative alternative electrolyte, nominal 0.5 M; not a mandatory input to either main route.'),
('kcl','Potassium chloride','KCl',None,'disconnected_ionic_2d','Footnote 25 qualitative alternative electrolyte, nominal 0.5 M; exact branch recipe not restated.'),
('tmacl','Tetramethylammonium chloride','C4H12ClN',None,'disconnected_ionic_2d','Footnote 25 qualitative alternative electrolyte. Finite tetramethylammonium cation and chloride can be shown in 2D; no 3D ion-pair geometry inferred.'),
('diagnostic-hs','Hydrosulfide test solution',None,None,'speciation_card','Supernatant diagnostic uses HS−. Reagent counterion, stock source, dose and detection limit are not reported; do not assign Na2S·9H2O or isolated HS− as a verified feed.')]
items=[]
for mid,name,formula,reuse,rep,note in rows:
 e={'material_id_proposal':mid,'name':name,'formula_reference':formula,'existing_registry_id':reuse,'representation':rep,'source_locator':'Main PDF p. 2, printed p. 596, Experimental Section' if mid not in ['licl','kcl','tmacl'] else 'Main PDF p. 4, printed p. 598, footnote 25','scope':note,'measured_atomic_structure':False}
 if reuse:e.update(existing_asset_hashes=old[reuse]['assetHashes'],existing_asset_paths={k:old[reuse][k] for k in ['svgPath','model2dPath','model3dPath'] if old[reuse].get(k)})
 items.append(e)
save(R/'chemical-representation-proposal.json',{'source_doi':'10.1021/la970480g','source_sha256':'6a7fb66fb56f6daa4aa677c91ddf0d78aa733b165b7537bbac4c4e1327defb06','existing_registry_sha256':sha(REG),'items':items,'context_species':['Cd2+ as uptake/chelation ion','Na+, HS−, OH− in source aqueous sulfide speciation','Cl− as electrolyte counterion'],'excluded_inputs':['Styrene and divinylbenzene are polymer composition descriptors, not free monomers used to synthesize polymer in this paper','No N2 atmosphere or exact pore geometry is reported','Nafion, PbS and homogeneous-solution hosts in introduction are prior-work examples'],'crystal_reference':{'available_verified_cubic_cds_reference':False,'search_scope':'Eight-entry current Site registry and accessible research-assets CIF/reference filenames; runtime directories excluded','source_phase':'Cubic zinc-blende CdS assigned from XRD in main p. 3','limits':'No measured lattice parameter, coordinates or CIF. CdSe references cannot substitute for CdS.'}})
print(len(items))
