"""Build private Veinot1997 chemical references and exact draft-material bindings.

Uses the same RDKit JSON/SVG/SDF format as the prior Littau and Heath packages.
No Site writes, network lookup, experimental coordinate claims, or guessed CIDs.
"""
import sys,json,hashlib,math,re,html,collections
from pathlib import Path
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SITE=Path('[local path redacted]')
EXISTING=SITE/'dist/assets/chemical-registry'
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem,__version__ as RDVERSION
from rdkit.Chem import AllChem,rdMolDescriptors,rdDepictor,rdMolTransforms
from rdkit.Chem.Draw import rdMolDraw2D
DOI='https://doi.org/10.1021/cm970189m'
SOURCE_HASH='eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc'
SEED=20260919
for folder in ['svg','models','sdf','review']:(OUT/folder).mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def composition(s):
    out=collections.Counter()
    for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s):out[e]+=int(n or 1)
    return out
old={e['id']:e for e in read(EXISTING/'registry.json')['entries']}
REUSE_MAP={}
REUSE=[]
MOLECULES=[('dmso', 'dimethyl-sulfoxide', 'Dimethyl sulfoxide', 'C2H6OS', 'CS(C)=O', 'ACS spectrophotometric grade; QDOH and esterification stocks use DMSO. Distinct from DMSO-d6 used for NMR. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('acetic-acid', 'acetic-acid', 'Acetic acid', 'C2H4O2', 'CC(=O)O', 'Explicit for cadmium-acetate recrystallization; anhydride-route liquid contains corresponding acid and excess anhydride. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('hydroxythiophenol', '4-hydroxythiophenol', '4-Hydroxythiophenol', 'C6H6OS', 'Oc1ccc(S)cc1', 'Fresh reduced-pressure distillation; free precursor is chemically distinct from the sulfur-bound thiolate cap. Reported 4.93 g, 39 mmol. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. This free thiol is distinct from the sulfur-bound, deprotonated surface cap; its S–H bond must not be assigned to the nanocluster surface.'), ('diethyl-ether', 'diethyl-ether', 'Diethyl ether', 'C4H10O', 'CCOCC', 'Explicitly named in chain-length-dependent solubility discussion. The decanoyl ester is soluble; acetyl and benzoyl are not. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('imidazole', 'imidazole', 'Imidazole', 'C3H4N2', 'c1ncc[nH]1', 'Anhydride route and 2.05-equivalent acyl-chloride route; imidazole is released during surface acyl transfer. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('pyrene-acid', 'pyrene-1-carboxylic-acid', 'Pyrene-1-carboxylic acid', 'C17H10O2', 'O=C(O)c1ccc2ccc3cccc4ccc1c2c34', '1.0 g, 4.1 mmol reacted in 20 mL thionyl chloride; pyrene substitution is explicitly position 1. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. The substituent is at the source-named pyrene 1-position; the ring graph is checked against the original Scheme 1 and compound illustration.'), ('thionyl-chloride', 'thionyl-chloride', 'Thionyl chloride', 'Cl2OS', 'O=S(Cl)Cl', '20 mL excess removed in vacuum after preparation of the pyrene acid chloride. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('butanoyl-chloride', 'butanoyl-chloride', 'Butanoyl chloride', 'C4H7ClO', 'CCCC(=O)Cl', 'Listed as purchased; specific 3b preparation uses butyric anhydride rather than assigning this as a mandatory input. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('decanoyl-chloride', 'decanoyl-chloride', 'Decanoyl chloride', 'C10H19ClO', 'CCCCCCCCCC(=O)Cl', 'Acyl chloride for N-decanoylimidazole; 50% solution basis and absolute charge are unreported. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('benzoyl-chloride', 'benzoyl-chloride', 'Benzoyl chloride', 'C7H5ClO', 'O=C(Cl)c1ccccc1', 'Benzoyl identity is explicit despite the anomalous methyl assignment in the Table 1 precursor NMR row. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('acetic-anhydride', 'acetic-anhydride', 'Acetic anhydride', 'C4H6O3', 'CC(=O)OC(C)=O', 'Large excess, room temperature, 30 min; charge not supplied. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('butyric-anhydride', 'butyric-anhydride', 'Butyric anhydride', 'C8H14O3', 'CCCC(=O)OC(=O)CCC', 'Large excess. Experimental common method says 30 min; Table 1 lists 15 min for 3b. Both are retained. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('pyrene-acid-chloride', 'pyrene-1-carbonyl-chloride', 'Pyrene-1-carbonyl chloride', 'C17H9ClO', 'O=C(Cl)c1ccc2ccc3cccc4ccc1c2c34', 'Orange-yellow solid used immediately after excess thionyl chloride removal; no isolated yield is given. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. The substituent is at the source-named pyrene 1-position; the ring graph is checked against the original Scheme 1 and compound illustration.'), ('acylimidazole-3a', 'n-acetylimidazole', 'N-Acetylimidazole', 'C5H6N2O', 'CC(=O)n1ccnc1', 'Compound 3a maps to cluster ester 2a. Small-molecule product, not a CdS nanocluster. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('acylimidazole-3b', 'n-butanoylimidazole', 'N-Butanoylimidazole', 'C7H10N2O', 'CCCC(=O)n1ccnc1', 'Compound 3b maps to cluster ester 2b. Small-molecule product, not a CdS nanocluster. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('acylimidazole-3c', 'n-pyrene-1-carbonylimidazole', 'N-Pyrene-1-carbonylimidazole', 'C20H12N2O', 'O=C(n1ccnc1)c1ccc2ccc3cccc4ccc1c2c34', 'Compound 3c maps to cluster ester 2c. Small-molecule product, not a CdS nanocluster. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. The substituent is at the source-named pyrene 1-position; the ring graph is checked against the original Scheme 1 and compound illustration.'), ('acylimidazole-3d', 'n-benzoylimidazole', 'N-Benzoylimidazole', 'C10H8N2O', 'O=C(n1ccnc1)c1ccccc1', 'Compound 3d maps to cluster ester 2d. Small-molecule product, not a CdS nanocluster. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('acylimidazole-3e', 'n-decanoylimidazole', 'N-Decanoylimidazole', 'C13H22N2O', 'CCCCCCCCCC(=O)n1ccnc1', 'Compound 3e maps to cluster ester 2e. Small-molecule product, not a CdS nanocluster. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'), ('dmso-d6', 'dimethyl-sulfoxide-d6', 'Dimethyl sulfoxide-d6', 'C2D6OS', '[2H]C([2H])([2H])S(=O)C([2H])([2H])[2H]', 'Explicit isotopic solvent for QDOH, esters except 2e, and Figure 2 precursor 3e. Distinct from ordinary DMSO. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. Deuterium positions are explicitly represented as hydrogen isotope 2; isotopic purity is not supplied.'), ('chloroform-d', 'chloroform-d', 'Chloroform-d', 'CDCl3', '[2H]C(Cl)(Cl)Cl', 'CDCl3 specifically used for 2e proton NMR; ordinary chloroform is not an identical isotopic reference. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. Deuterium positions are explicitly represented as hydrogen isotope 2; isotopic purity is not supplied.'), ('heavy-water', 'deuterium-oxide', 'Deuterium oxide', 'D2O', '[2H]O[2H]', 'One drop added to QDOH/DMSO-d6 for the Figure 1 exchange observation; no isotopic purity or volume is given. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal. Deuterium positions are explicitly represented as hydrogen isotope 2; isotopic purity is not supplied.'), ('dmf', 'dimethylformamide', 'Dimethylformamide', 'C3H7NO', 'CN(C)C=O', 'QDOH clear colloidal suspension; not specified as an input to the principal synthesis. Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.')]
CARDS=[]
GROUPS=[('Phenolic hydroxyl','[OX2H]-[c]'),('Thiol','[SX2H]'),('Acyl group','[CX3](=O)'),('Imidazole ring','n1ccnc1'),('Sulfoxide','[S](=O)')]
def groups(m):
    result=[]
    for name,smarts in GROUPS:
        for match in m.GetSubstructMatches(Chem.MolFromSmarts(smarts)):
            ids=sorted(match);result.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
    return result
def model(m,e,rep):
    c=m.GetConformer()
    return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':None,'source':DOI,'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d',
     'indexConvention':'zero-based','coordinateUnits':'angstrom' if rep=='3d' else 'drawing units',
     'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],
     'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()],
     'functionalGroups':groups(m),'computedBy':'RDKit '+RDVERSION,'eligible_training':False}
def base(ident,name,formula,kind,note):
    return {'id':ident,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,
     'sourceUrls':[DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':note,'limitations':[note],
     'provenance':{'identitySource':'Source-named compound or material in Veinot et al. 1997','sourceDoi':'10.1021/cm970189m','sourceSha256':SOURCE_HASH,
     'sourceLookupStatus':'local_source_identity; no external identifier lookup performed','sourceRecords':[],
     'limitations':'Illustrative reference only; not measured sample, solution, surface, polymer or crystal coordinates.'}}
entries=[];models=[];mapping=dict(REUSE_MAP)
for mid,ident,name,formula,smiles,note in MOLECULES:
    assert ident not in old,ident
    e=base(ident,name,formula,'molecule',note)
    e['provenance'].update({'connectivitySource':'Conventional connectivity of the explicitly source-named compound, checked for formula, valence and bond topology','smiles':smiles,'depictionSoftware':'RDKit '+RDVERSION})
    m=Chem.MolFromSmiles(smiles);assert m is not None
    if ident=='hydrogen-selenide':m=Chem.AddHs(m)
    assert composition(rdMolDescriptors.CalcMolFormula(m,separateIsotopes=True,abbreviateHIsotopes=True))==composition(formula)
    assert Chem.GetFormalCharge(m)==0 and len(Chem.GetMolFrags(m))==1
    rdDepictor.Compute2DCoords(m,canonOrient=True)
    drawer=rdMolDraw2D.MolDraw2DSVG(840,360);opt=drawer.drawOptions();opt.clearBackground=False;opt.padding=.14;opt.minFontSize=20;opt.maxFontSize=30;opt.bondLineWidth=2
    drawer.DrawMolecule(m);drawer.FinishDrawing();svg=drawer.GetDrawingText().replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(note)+'</desc>')
    e['svgPath']='svg/'+ident+'.svg';(OUT/e['svgPath']).write_text(svg,encoding='utf-8')
    two=model(m,e,'2d');two.update({'modelType':'RDKit 2D reference connectivity layout','caption':'Illustrative compound connectivity, not measured geometry. '+note})
    e['model2dPath']='models/'+ident+'-2d.json';dump(OUT/e['model2dPath'],two);e['functionalGroups']=two['functionalGroups']
    mol=Chem.AddHs(m);mol.RemoveAllConformers();p=AllChem.ETKDGv3();p.randomSeed=SEED;p.numThreads=1;p.maxIterations=1500
    status=AllChem.EmbedMolecule(mol,p);assert status==0,(ident,status)
    ff=None;method=None;result=None;energy=None
    if AllChem.MMFFHasAllMoleculeParams(mol):
        method='MMFF94s';ff=AllChem.MMFFGetMoleculeForceField(mol,AllChem.MMFFGetMoleculeProperties(mol,mmffVariant=method))
    elif AllChem.UFFHasAllMoleculeParams(mol):method='UFF';ff=AllChem.UFFGetMoleculeForceField(mol)
    if ff is not None:result=ff.Minimize(maxIts=2000);energy=ff.CalcEnergy();assert result==0,(ident,result)
    extra=[]
    if method is None:
        extra=['RDKit reported no complete MMFF/UFF parameterization for this molecule. Coordinates are an unminimized ETKDG distance-geometry illustration; no optimized bond lengths or angles are claimed.']
        e['limitations']+=extra
    three=model(mol,e,'3d');three.update({'modelType':'Locally computed illustrative conformer','sourceType':'Source-named connectivity with locally computed coordinates','coordinateSource':'local-rdkit',
     'caption':'One computed illustrative free-compound conformer, not a measured structure. No solution association, adsorption geometry or unique conformation is established.'+(' '+extra[0] if extra else ''),
     'method':'ETKDGv3'+(' + '+method if method else '; unminimized distance geometry'),
     'conformerGeneration':{'randomSeed':SEED,'numThreads':1,'embeddingStatus':status,'forceField':method,'minimizationReturnCode':result,
      'minimizationStatus':'converged' if result==0 else 'unminimized; no fully parameterized force field','energyKcalMol':energy,'energyMeaning':'Classical conformer energy only when present; not experimental or thermodynamic energy.'},
     'connectivitySmiles':Chem.MolToSmiles(Chem.RemoveHs(mol)),'notes':[note]+extra})
    e['model3dPath']='models/'+ident+'-3d.json';dump(OUT/e['model3dPath'],three);models.append(three)
    Chem.MolToMolFile(mol,str(OUT/'sdf'/(ident+'-computed-illustrative-3d.sdf')))
    e['provenance']['computed3d']={k:three[k] for k in ['computedBy','method','conformerGeneration']}
    e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath']};entries.append(e);mapping[mid]=ident
summary={'newMoleculeEntries':len(entries),'new2dModels':len(entries),'new3dModels':len(models),'allModelsIllustrative':True}
dump(OUT/'molecule-registry-proposal.json',{'schemaVersion':'1.0.0','assetPurpose':'Source-named free-molecule references; no Site changes; exact canonical bindings pending','entries':entries,'summary':summary})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'molecule-identity-map.json',{'inventoryToRegistry':mapping,'sourceDoi':'10.1021/cm970189m','sourceSha256':SOURCE_HASH,'bindingsStatus':'pending canonical material IDs'})
print(json.dumps(summary,indent=2))
