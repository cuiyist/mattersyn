from pathlib import Path
import re
review=Path(__file__).resolve().parent
out=review/'molecular-assets'
out.mkdir(exist_ok=True)
source=review.parent/'cm9503137/molecular-assets/build_assets.py'
s=source.read_text(encoding='utf-8').replace('Danek1996','Dabbousi1997').replace('Danek et al. 1996','Dabbousi et al. 1997').replace('10.1021/cm9503137','10.1021/jp971091y').replace('cde428b3707ab7e0fe1a24cd747e6c884d6903265d4d745a93e36d60e553321f','dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d')
a=s.index('REUSE_MAP=');b=s.index('def groups(m):')
s=s[:a]+'''REUSE_MAP={'hexane':'hexane','methanol':'methanol','pyridine':'pyridine','top':'top','topo':'topo','topse':'topse',
 'cdme2':'dimethylcadmium','se':'selenium-element','n2':'nitrogen','dezn':'diethylzinc','tms2s':'bis-trimethylsilyl-sulfide',
 'butanol':'1-butanol','chloroform':'chloroform','toluene':'toluene','thf':'thf','si100':'identity-silicon-100-wafer','cu':'identity-copper-xrd-source'}
REUSE=sorted(set(REUSE_MAP.values()))
for ident in REUSE:
    for key,h in old[ident]['assetHashes'].items():assert sha(EXISTING/old[ident][key])==h
MOLECULES=[('octane','octane','Octane','C8H18','CCCCCCCC',
 'Conventional straight-chain octane identity named for TEM-grid deposition. One locally computed free-molecule conformer is illustrative; it does not specify solvent purity, amount, surface adsorption or an observed geometry.')]
CARDS=[
 ('identity-dabbousi-cdse-seeds','CdSe nanocrystal seed family','CdSe','CdSe seed family','support',
  'Source-scoped CdSe seed family. The size depends on the recipe or measurement cohort. Formula refers to inorganic composition, not a finite molecular formula. TOP/TOPO ligand coverage, individual batch identity and atomic coordinates are not supplied by this card.'),
 ('identity-dabbousi-bare-or-zns-dots','Bare or ZnS-coated CdSe specimen family','CdSe or CdSe/ZnS','CdSe OR CdSe/ZnS','support',
  'Alternative specimen identities used by the selected characterization procedure. This is not a physical mixture, a universal coating thickness, one continuous specimen chain or an exact batch assignment. Broad family identity does not join the separate solution-SAXS cohort to the coverage series.'),
 ('identity-dabbousi-optical-dots','Bare or shell-coated CdSe optical specimens','CdSe or CdSe/ZnS or CdSe/CdS','CdSe / ZnS- or CdS-coated','support',
  'Optical procedure accepts bare CdSe, ZnS-overcoated CdSe or CdS-overcoated CdSe as alternative specimen families. These are not a three-component mixture or a common atomistic interface; sample-specific source links remain in the record.'),
 ('identity-dabbousi-wds-dots','ZnS-overcoated CdSe WDS specimens','CdSe/ZnS','CdSe core / ZnS overlayer','support',
  'Architecture identity for WDS specimens. No unique dot size, atomic interface, shell continuity or refined crystal coordinates are assigned by this identity card.'),
 ('identity-dabbousi-xps-films','Bare or ZnS-coated CdSe XPS films','CdSe or CdSe/ZnS','CdSe OR CdSe/ZnS · XPS films','support',
  'Film specimen family for the air-exposure comparison. Exposure groups and bare versus coated surfaces remain separate observations. This card does not assign all films to one batch, exposure duration or oxide species.'),
 ('identity-dabbousi-silicon-wafer','Silicon wafer substrate','Si','Si wafer','support',
  'Solid wafer support named for film preparation. The WDS procedure separately specifies Si(100); that orientation is not transferred to every XPS, SAXS or WAXS substrate. No measured atomic coordinates, doping or dimensions are supplied.'),
 ('identity-dabbousi-copper-tem-grid','Copper TEM grid','Cu','Cu · TEM grid','support',
  'Copper component of the amorphous-carbon-coated TEM grid. This is a support material, not the rotating copper X-ray anode or a synthesized copper nanocrystal. No grid dimensions or atomic coordinates are assigned.'),
 ('identity-amorphous-carbon-support-coating','Amorphous carbon support or coating','C','Amorphous C · support / coating','support',
  'Source explicitly names amorphous carbon for TEM support and overcoat, and the WDS conductive coating. Application method is procedure-specific: evaporation is explicit for the added TEM layer, but not for WDS. No graphite crystal, molecular graph or layer thickness is inferred.'),
 ('identity-dabbousi-rhodamine590','Rhodamine 590 fluorescence standard',None,'Rhodamine 590','formula',
  'Source designation of one alternative quantum-yield reference. Salt, counterion, exact chemical identity, concentration and reference solvent are not resolved. Danek\u2019s methanol solvent is not transferred to this source. No molecular graph is assigned.'),
 ('identity-dabbousi-rhodamine640','Rhodamine 640 fluorescence standard',None,'Rhodamine 640','formula',
  'Source designation of the other alternative quantum-yield reference. Exact salt, counterion, concentration and solvent are unresolved; no molecular graph or PubChem identity is assigned.'),
 ('identity-poly-vinylbutyral-source','Poly(vinylbutyral) matrix',None,'Poly(vinylbutyral)','formula',
  'Source-named PVB polymer used as a 10 wt % solution in toluene for one SAXS-film procedure. Chain length, composition of residual copolymer units, molecular-weight distribution and stereochemistry are not supplied; no single repeat-unit or finite-polymer formula is imposed.'),
 ('identity-mtd300p20-source','MTD300P20 diblock copolymer',None,'MTD300P20','formula',
  'Source describes a phosphine-functionalized diblock copolymer, [methyltetracyclododecene]300-[norbornene-CH2O(CH2)5P(oct)2]20, used in the separate THF-based SAXS-film procedure. Printed block counts and substituent notation are preserved; stereochemistry, sequence, end groups and an exact finite molecular graph are unresolved. No computed polymer conformation is invented.'),
 ('identity-quartz-saxs-capillary','Quartz SAXS capillary','SiO2','Quartz capillary · SiO2','support',
  'Source-named capillary with an approximately 1 mm optical path. SiO2 is a bulk composition reference, not a discrete molecule or an assignment of crystalline quartz coordinates. Wall thickness, phase and capillary dimensions are not inferred.'),
 ('identity-magnesium-xps-anode','Magnesium XPS anode','Mg','Mg · XPS anode','support',
  'Instrument component. The reported spectra use Mg K-alpha excitation. This is not a reagent, specimen or synthesized magnesium material; no atomistic anode model is supplied.'),
 ('identity-aluminum-xps-anode-option','Aluminum option of dual-anode XPS source','Al','Al · instrument option','support',
  'Aluminum is named as the second option of the Mg/Al XPS instrument. The reported measurements use Mg K-alpha, so Al is not a simultaneously applied source or a required sample ingredient.'),
 ('identity-air-environment','Air exposure environment',None,'Air · environmental mixture','formula',
  'Exposure atmosphere named by the source. Composition, humidity, flow, temperature and contaminant concentrations are unreported. No fixed N2/O2 stoichiometry or single molecular formula is assigned.')]
GROUPS=[]
''' + s[b:]
a=s.index("mapping.update(");b=s.index('new={e',a)
s=s[:a]+'''mapping.update({'cdse-seeds':'identity-dabbousi-cdse-seeds','rhodamine590':'identity-dabbousi-rhodamine590','rhodamine640':'identity-dabbousi-rhodamine640',
 'si':'identity-dabbousi-silicon-wafer','copper-grid':'identity-dabbousi-copper-tem-grid','carbon':'identity-amorphous-carbon-support-coating',
 'pvb':'identity-poly-vinylbutyral-source','mtd300p20':'identity-mtd300p20-source','quartz':'identity-quartz-saxs-capillary',
 'mg':'identity-magnesium-xps-anode','al':'identity-aluminum-xps-anode-option','air':'identity-air-environment','xps-films':'identity-dabbousi-xps-films'})
DOTS={'dabbousi-1997-optical-characterization':'identity-dabbousi-optical-dots','dabbousi-1997-wds-preparation':'identity-dabbousi-wds-dots'}
''' + s[b:]
s=s.replace("ident=DOTS[rid] if mid=='dots' else mapping[mid]","ident=DOTS.get(rid,'identity-dabbousi-bare-or-zns-dots') if mid=='dots' else mapping[mid]")
a=s.index("        if mid=='dezn':");b=s.index("summary=",a)
s=s[:a]+'''        if mid=='dezn':notes[rid][mid]+=' The 0.2 micrometer source filtration does not specify filter material; no PTFE or Danek vacuum-transfer treatment is inherited.'
        elif mid=='pyridine':notes[rid][mid]='Free pyridine reference; surface adsorption, ligand count and geometry are not established. '+notes[rid][mid]
        elif mid=='hexane':notes[rid][mid]='Reference n-hexane connectivity does not establish a measured bottle composition. '+notes[rid][mid]
        elif mid=='topse':notes[rid][mid]='TOPSe molecular identity only; the source stock is 0.1 mol Se in 100 mL TOP, reported as 1 M. Stock graph and charge values remain in the recipe. '+notes[rid][mid]
        elif mid=='butanol':notes[rid][mid]='The source explicitly specifies 1-butanol. In ZnS overgrowth 5 mL prevents TOPO solidification; in CdS storage equal amounts of hexane and butanol are used. This is not a stated quench. '+notes[rid][mid]
        elif mid=='cu':notes[rid][mid]='Copper is the radiation-source element, not a sample ingredient; procedure-specific operating values remain in the record. '+notes[rid][mid]
''' + s[b:]
s=s.replace("'unminimizedIllustrativeModels':['diethylzinc']","'newUnminimizedIllustrativeModels':[],'reusedUnminimizedIllustrativeModels':['diethylzinc']").replace('assert len(bindings)==12','assert len(bindings)==17')
a=s.index(" 'extraLimits':");b=s.index("dump(OUT/'model-provenance.json'",a)
s=s[:a]+''' 'extraLimits':['Rhodamine 590 and 640 remain unresolved identity cards; PVB and MTD300P20 have no invented finite molecular graphs.', 'Solid supports, instrument anodes, environmental air and nanocrystal families are reference cards, not atomic models.', 'No CdSe/ZnS or CdSe/CdS atomic interface, measured lattice, CIF, ligand geometry or exact batch is generated.', '1-butanol is explicitly named in this source; this identity does not resolve unspecified butanol in other papers.', 'No external identifier was guessed or looked up. Existing reused molecular provenance is retained.']})
''' + s[b:]
s=s.replace('Four explicit compound names checked against conventional formula and connectivity','Explicit octane name checked against conventional straight-chain formula and connectivity')
(out/'build_assets.py').write_text(s,encoding='utf-8')
v=(source.parent/'validate_assets.py').read_text(encoding='utf-8').replace('10.1021/cm9503137','10.1021/jp971091y')
v=v.replace("len(new)==21", "len(new)==17").replace('Twenty-one unique','Seventeen unique')
v=re.sub(r"expected=\{.*?\}\nimages=", "expected={'octane':{'C':8,'H':18}}\nimages=",v,flags=re.S)
a=v.index("check(new['identity-butanol");b=v.index('contact_paths=[]',a)
v=v[:a]+'''check(new['identity-dabbousi-rhodamine590']['formula'] is None and new['identity-dabbousi-rhodamine640']['formula'] is None,'Dye standard identities remain unresolved')
check(bindings['recordBindings']['dabbousi-1997-zns-overgrowth']['butanol']=='1-butanol','Explicit 1-butanol correctly resolves')
check(bindings['recordBindings']['dabbousi-1997-wds-preparation']['si100']=='identity-silicon-100-wafer','WDS (100) substrate is explicit')
check(bindings['recordBindings']['dabbousi-1997-xps-preparation']['si']=='identity-dabbousi-silicon-wafer','Generic XPS wafer does not inherit WDS orientation')
check(len(bindings['recordBindings'])==17,'All 17 canonical draft records represented')
''' + v[b:]
(out/'validate_assets.py').write_text(v,encoding='utf-8')
