"""Source-complete identity inventory and apparatus proposal; no Site mutation."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SITE=Path('[local path redacted]')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old={e['id']:e for e in json.loads((SITE/'registry.json').read_text(encoding='utf-8'))['entries']}
items=[]
def add(id,name,formula,roles,pages,scope,reuse=None,kind='molecule',compound=None,limits=None):
 e={'inventory_id':id,'source_name':name,'formula_reference':formula,'roles':roles,'source_locators':[f'Main PDF p. {p}, printed p. {2116+p}' for p in pages],
 'source_scope':scope,'proposed_depiction':kind,'source_compound_label':compound,'existing_registry_id':reuse,'new_asset_needed':not bool(reuse),'limitations':limits or [],'eligible_training':False}
 if reuse:
  assert reuse in old,reuse
  e['reuse_assets']={k:old[reuse][k] for k in ['svgPath','model2dPath','model3dPath'] if old[reuse].get(k)}
  e['reuse_hashes']=old[reuse]['assetHashes']
  for k,h in e['reuse_hashes'].items():assert sha(SITE/old[reuse][k])==h,(reuse,k)
 items.append(e)
add('toluene','Toluene','C7H8',['precursor solvent','recrystallization solvent'],[1,2,3],'Dried over 4 Å sieves and filtered; dry toluene is used for acyl-chloride routes and recrystallization.',reuse='toluene')
add('sieves','4 Å molecular sieves',None,['drying medium'],[1],'Toluene conditioning; sieve composition and loading are not stated.',kind='material_card')
add('dmso','Dimethyl sulfoxide','C2H6OS',['reaction solvent','dispersion solvent','solubility test'],[1,2,3,4,6],'ACS spectrophotometric grade; QDOH and esterification stocks use DMSO. Distinct from DMSO-d6 used for NMR.')
add('water','Water','H2O',['stock solvent','quench','washing solvent','residual NMR signal'],[1,2,4],'Deionized then charcoal-filtered for preparation. Water quench is after ice-bath cooling in esterification.',reuse='water')
add('ion-exchange','Mixed-bed ion-exchange medium',None,['water purification'],[1],'Sybron-Barnstead D8902 column; resin chemistry and regenerants are unreported.',kind='material_card')
add('activated-charcoal','Activated charcoal','C',['water purification'],[1],'Sybron-Barnstead D8204 activated-charcoal filter; no graphite lattice or pore-size model.',kind='material_card')
add('sulfide','Sodium sulfide nonahydrate','H18Na2O9S',['sulfide precursor'],[1],'Reported 2.53 g, 11 mmol; keep source quantities without forcing exact mass/mole agreement.',kind='salt_formula_card',limits=['Hydrate formula is explicit. No salt lattice, solvation shell or molecular coordination geometry is established.'])
add('cadmium-acetate','Cadmium acetate',None,['cadmium precursor'],[1],'Recrystallized from glacial acetic acid; dried at 100 °C under vacuum. Charge printed 5.05 g, 29 mmol.',kind='salt_formula_card',limits=['Hydration state is not stated. The anhydrous formula-unit reference is Cd(C2H3O2)2; the printed mass and amount are inconsistent with its molar mass. Do not choose a hydrate to repair them.'])
add('acetic-acid','Glacial acetic acid','C2H4O2',['recrystallization solvent','possible precursor-route byproduct'],[1,2],'Explicit for cadmium-acetate recrystallization; anhydride-route liquid contains corresponding acid and excess anhydride.')
add('hydroxythiophenol','4-Hydroxythiophenol','C6H6OS',['capping precursor'],[1,2,3,4],'Fresh reduced-pressure distillation; free precursor is chemically distinct from the sulfur-bound thiolate cap. Reported 4.93 g, 39 mmol.')
add('acetonitrile','Acetonitrile','C2H3N',['stock solvent'],[1,3],'QDOH solvent mixture is acetonitrile/methanol/water 1:1:2 by volume.',reuse='acetonitrile')
add('methanol','Methanol','CH4O',['stock solvent','washing solvent','QDOH optical solvent','solubility context'],[1,2,3,5,6],'Methanol optical solvent applies to QDOH; esters use chloroform.',reuse='methanol')
add('acetone','Acetone','C3H6O',['washing solvent','TEM-grid cleaning','solubility test'],[2,6],'Separate washing and grid-cleaning uses; butanoyl and decanoyl esters are reported soluble in acetone.',reuse='acetone')
add('ether-workup','Ether (workup wording)',None,['washing solvent'],[2],'QDOH and ester workup simply say ether; the later solubility discussion explicitly names diethyl ether.',kind='identity_card',limits=['Do not silently convert every source ether mention into an atomistic model without labeling that source-context inference.'])
add('diethyl-ether','Diethyl ether','C4H10O',['solubility context'],[6],'Explicitly named in chain-length-dependent solubility discussion. The decanoyl ester is soluble; acetyl and benzoyl are not.')
add('nitrogen','Nitrogen','N2',['reaction atmosphere'],[1,2],'QDOH formation under nitrogen; precursor formation and esterification specify dry nitrogen.',reuse='nitrogen')
add('imidazole','Imidazole','C3H4N2',['acyl-transfer reagent precursor','reaction byproduct'],[1,2,3,4],'Anhydride route and 2.05-equivalent acyl-chloride route; imidazole is released during surface acyl transfer.')
add('pyrene-acid','1-Pyrenecarboxylic acid','C17H10O2',['precursor for acyl chloride'],[1,2],'1.0 g, 4.1 mmol reacted in 20 mL thionyl chloride; pyrene substitution is explicitly position 1.')
add('thionyl-chloride','Thionyl chloride','Cl2OS',['reagent','reaction medium'],[1,2],'20 mL excess removed in vacuum after preparation of the pyrene acid chloride.')
add('butanoyl-chloride','n-Butanoyl chloride','C4H7ClO',['purchased chemical','general acyl-chloride family'],[1,3],'Listed as purchased; specific 3b preparation uses butyric anhydride rather than assigning this as a mandatory input.')
add('decanoyl-chloride','Decanoyl chloride','C10H19ClO',['3e precursor'],[1,2,3],'Acyl chloride for N-decanoylimidazole; 50% solution basis and absolute charge are unreported.')
add('benzoyl-chloride','Benzoyl chloride','C7H5ClO',['3d precursor'],[1,2,3],'Benzoyl identity is explicit despite the anomalous methyl assignment in the Table 1 precursor NMR row.')
add('acetic-anhydride','Acetic anhydride','C4H6O3',['3a precursor','reaction medium'],[1,2,3],'Large excess, room temperature, 30 min; charge not supplied.')
add('butyric-anhydride','Butyric anhydride','C8H14O3',['3b precursor','reaction medium'],[1,2,3],'Large excess. Experimental common method says 30 min; Table 1 lists 15 min for 3b. Both are retained.')
add('pyrene-acid-chloride','1-Pyrenecarboxylic acid chloride','C17H9ClO',['prepared precursor for 3c'],[2],'Orange-yellow solid used immediately after excess thionyl chloride removal; no isolated yield is given.')
for letter,name,formula in [('a','N-Acetylimidazole','C5H6N2O'),('b','N-Butanoylimidazole','C7H10N2O'),('c','N-Pyrene-1-carboxoylimidazole','C20H12N2O'),('d','N-Benzoylimidazole','C10H8N2O'),('e','N-Decanoylimidazole','C13H22N2O')]:
 add('acylimidazole-3'+letter,name,formula,['prepared molecular precursor','surface-acylation reagent'],[2,3,4],f'Compound 3{letter} maps to cluster ester 2{letter}. Small-molecule product, not a CdS nanocluster.',compound='3'+letter,limits=['A computed free-molecule conformer would be illustrative, not the measured crystal or solution conformation.'])
add('imidazole-hydrochloride','Imidazole hydrochloride','C3H5ClN2',['chloride-route byproduct'],[2,3,4],'White precipitate removed by hot filtration in the acyl-chloride preparation. No requirement to add HCl to QDOH.',kind='salt_formula_card')
add('corresponding-acid','Corresponding organic acid',None,['anhydride-route or control-workup byproduct'],[2,5],'Exact acid follows the selected acyl group; source control does not identify a unique recovered acid or tested precursor.',kind='identity_card')
add('qdoh','Surface-phenolic CdS quantum dots',None,['prepared nanocluster','surface-acylation substrate','analytical specimen'],[1,2,3,4,5,6],'Compound 1 (QDOH), sulfur-bound phenolic thiolate cap. Core composition CdS; whole-particle stoichiometry unknown.',kind='surface_material_card',compound='1',limits=['No exact ligand count or atomic coordinates. Gravimetric estimates conflict: 20 mol % versus 34 mol % cap-derived sulfur.','No CdS polymorph or experimental CIF is established.'])
for letter,name in [('a','acetyl'),('b','butanoyl'),('c','pyrene-1-carbonyl'),('d','benzoyl'),('e','decanoyl')]:
 add('ester-2'+letter,f'{name.capitalize()} ester of surface-phenolic CdS',None,['surface-functionalized product','analytical specimen'],[2,3,4,5,6],f'Compound 2{letter}: terminal phenolic O-acylation with {name} group. Distinct from precursor 3{letter}.',kind='surface_material_card',compound='2'+letter,limits=['Whole-particle formula, grafting distribution and measured ligand geometry are unknown.','Conversion is phenolic esterification by NMR, not isolated particle yield or a crystal-phase fraction.'])
add('unfunctionalized-cds','Unfunctionalized thiophenol-capped CdS',None,['control substrate'],[3,4,5],'No reaction with N-acylimidazoles in source control; exact synthesis charge and tested reagent are not restated.',kind='surface_material_card',limits=['Thiophenol-capped is not bare or ligand-free CdS.'])
add('bulk-cds','Bulk CdS degradation product','CdS',['observed degradation product','bulk optical comparison'],[5],'Long exposure >12 h precipitates bulk CdS; a bulk bandgap of 2.53 eV is used separately as an optical comparison.',kind='material_card',limits=['No crystalline polymorph, refined cell or measured atomic coordinates are specified.'])
add('os-diester','Corresponding O,S-diester',None,['observed degradation coproduct'],[5],'Crystalline organic coproduct of prolonged reaction; exact acyl group and full compound identity are not singled out.',kind='identity_card',limits=['Do not bind a single O,S-diacyl molecular graph to the whole failure family.'])
add('dmso-d6','DMSO-d6','C2D6OS',['NMR solvent'],[1,2,4],'Explicit isotopic solvent for QDOH, esters except 2e, and Figure 2 precursor 3e. Distinct from ordinary DMSO.')
add('chloroform-d','Deuterated chloroform','CDCl3',['NMR solvent'],[1,2,4],'CDCl3 specifically used for 2e proton NMR; ordinary chloroform is not an identical isotopic reference.')
add('heavy-water','D2O','D2O',['NMR exchange probe'],[2,4],'One drop added to QDOH/DMSO-d6 for the Figure 1 exchange observation; no isotopic purity or volume is given.')
add('tms-nmr','TMS (NMR marker)',None,['NMR reference marker'],[4],'Figure 3 labels a TMS signal. The article does not expand the abbreviation or prescribe an added reference amount.',kind='identity_card',limits=['Do not conflate this NMR marker with trimethylsilyl reagents from other papers.'])
add('kbr','Potassium bromide','KBr',['FTIR pellet medium'],[2,3,5],'KBr pellets; source does not report pellet mass, dimensions or pressing conditions.',reuse='potassium-bromide')
add('chloroform','Chloroform','CHCl3',['ester optical solvent','TEM dispersion solvent','grid cleaning','solubility context'],[2,4,6],'Ester electronic spectra and general TEM preparation use CHCl3. Figure 6 labels a QDOH/CHCl3 suspension despite the discussion stating QDOH is insoluble.',reuse='chloroform')
add('quartz-cuvette','Quartz optical cuvette','SiO2',['optical support'],[2,5],'1 cm path length; no silica polymorph or molecular SiO2 graph is assigned.',kind='material_card')
add('carbon-copper-grid','Carbon-coated copper TEM grid',None,['TEM support'],[2,6],'JBS-183, 300 mesh. Clean in acetone, then chloroform, then acetone and air-dry.',reuse='identity-carbon-coated-copper-tem-grid-b47959',kind='material_card')
add('filter-paper','Filter paper',None,['TEM solvent absorption'],[2],'A layer of filter paper absorbs solvent through the grid; paper composition and grade are not stated.',kind='material_card')
add('silicon-grid','Precision silicon calibration grid','Si',['TEM size calibration'],[2],'21 600 lines per cm; this is a calibration standard, not a synthesis substrate or sample crystal.',kind='material_card')
add('air','Air',None,['TEM-grid drying atmosphere'],[2],'Air drying at room temperature; no composition or humidity is supplied.',reuse='identity-air-environment',kind='identity_card')
add('dmf','Dimethylformamide','C3H7NO',['solubility context'],[3],'QDOH clear colloidal suspension; not specified as an input to the principal synthesis.')
add('ethanol','Ethanol','C2H6O',['solubility context'],[3],'QDOH solubility attributed to surface hydrogen bonding; not a prescribed synthesis stock.',reuse='ethanol')
add('hexane','Hexane','C6H14',['solubility context'],[3],'QDOH reported insoluble; not an obligatory recovery solvent.',reuse='hexane')
inventory={'source_id':'veinot1997','source_doi':'10.1021/cm970189m','source_sha256':'eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc','scope':'All actual-work chemicals, supports, analytical media, named products and solubility comparators in the six-page main article. Prior-work PbS/CdSe and device examples are not synthesis ingredients.',
 'items':items,'counts':{'entries':len(items),'reused_identities':len(set(e['existing_registry_id'] for e in items if e['existing_registry_id'])),'candidate_new_molecule_identities':sum(e['proposed_depiction']=='molecule' and not e['existing_registry_id'] for e in items)},
 'binding_status':'Awaiting root canonical material arrays for exact record/material IDs. This inventory is a proposal, not guessed bindings.',
 'surface_reference_policy':'Use an explicitly conceptual CdS region with S-bound para-phenyl-OH or para-phenyl-O-C(=O)-R fragments, showing only reaction connectivity. Do not place atoms on a guessed CdS lattice, assign 130 exact caps, create a measured particle diameter or imply complete acylation for every branch.',
 'source_conflicts':['Cadmium acetate mass/amount mismatch and unspecified hydration.','QDOH cap-derived sulfur 20 versus 34 mol %.','General anhydride 30 min versus Table 1 3b 15 min.','Benzoyl precursor 3d Table 1 includes an unexpected methyl NMR assignment.','QDOH Experimental UV 295/305 nm versus main optical discussion 390 nm.','Figure 6 6 nm scale versus body 1100 Å aggregate.','TEM/QDOH chloroform suspension versus colloidal solubility statement; keep procedure and solubility separately.'],
 'excluded_from_material_bindings':['Bulk/reference electronic tight-binding parameters are observations or model context, not reagents.','He–Ne laser and instrument names are apparatus; no helium/neon charge is implied.','Cited prior-work CdSe/PbS and hypothetical chromophores, luminophores or wires are not additional synthesized material families.']}
dump(ROOT/'chemical-identity-inventory.json',inventory)
print(json.dumps(inventory['counts']))
