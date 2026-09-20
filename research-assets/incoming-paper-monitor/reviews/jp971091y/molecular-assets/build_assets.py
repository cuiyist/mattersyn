"""Build private Dabbousi1997 chemical references and exact draft-material bindings.

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
DOI='https://doi.org/10.1021/jp971091y'
SOURCE_HASH='dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d'
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
REUSE_MAP={'hexane':'hexane','methanol':'methanol','pyridine':'pyridine','top':'top','topo':'topo','topse':'topse',
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
  'Source designation of one alternative quantum-yield reference. Salt, counterion, exact chemical identity, concentration and reference solvent are not resolved. Danek’s methanol solvent is not transferred to this source. No molecular graph is assigned.'),
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
     'provenance':{'identitySource':'Source-named compound or material in Dabbousi et al. 1997','sourceDoi':'10.1021/jp971091y','sourceSha256':SOURCE_HASH,
     'sourceLookupStatus':'local_source_identity; no external identifier lookup performed','sourceRecords':[],
     'limitations':'Illustrative reference only; not measured sample, solution, surface, polymer or crystal coordinates.'}}
entries=[];models=[];mapping=dict(REUSE_MAP)
for mid,ident,name,formula,smiles,note in MOLECULES:
    assert ident not in old,ident
    e=base(ident,name,formula,'molecule',note)
    e['provenance'].update({'connectivitySource':'Conventional connectivity of the explicitly source-named compound, checked for formula, valence and bond topology','smiles':smiles,'depictionSoftware':'RDKit '+RDVERSION})
    m=Chem.MolFromSmiles(smiles);assert m is not None
    if ident=='hydrogen-selenide':m=Chem.AddHs(m)
    assert composition(rdMolDescriptors.CalcMolFormula(m))==composition(formula)
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
    if ident=='diethylzinc':
        assert method is None
        extra=['RDKit reported no complete MMFF/UFF parameterization for Zn. Coordinates are an unminimized ETKDG distance-geometry illustration; no optimized Zn–C bond length or exact C–Zn–C angle is claimed.']
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
for ident,name,formula,display,kind,note in CARDS:
    assert ident not in old
    e=base(ident,name,formula,kind,note);e['displayFormula']=display;e['provenance']['connectivitySource']=None
    sub='Source designation · connectivity unresolved' if kind=='formula' else 'Material reference · no atomic model'
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(note)+'</desc><rect x="22" y="36" width="796" height="288" rx="18" fill="#f1f6fa" stroke="#ccdae5"/><text x="420" y="154" text-anchor="middle" font-family="Arial,sans-serif" font-size="32" fill="#18384d">'+html.escape(display)+'</text><text x="420" y="217" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#476276">'+html.escape(sub)+'</text></svg>'
    e['svgPath']='svg/'+ident+'.svg';(OUT/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(OUT/e['svgPath'])};entries.append(e)
mapping.update({'cdse-seeds':'identity-dabbousi-cdse-seeds','rhodamine590':'identity-dabbousi-rhodamine590','rhodamine640':'identity-dabbousi-rhodamine640',
 'si':'identity-dabbousi-silicon-wafer','copper-grid':'identity-dabbousi-copper-tem-grid','carbon':'identity-amorphous-carbon-support-coating',
 'pvb':'identity-poly-vinylbutyral-source','mtd300p20':'identity-mtd300p20-source','quartz':'identity-quartz-saxs-capillary',
 'mg':'identity-magnesium-xps-anode','al':'identity-aluminum-xps-anode-option','air':'identity-air-environment','xps-films':'identity-dabbousi-xps-films'})
DOTS={'dabbousi-1997-optical-characterization':'identity-dabbousi-optical-dots','dabbousi-1997-wds-preparation':'identity-dabbousi-wds-dots'}
new={e['id']:e for e in entries};allentries={**old,**new};bindings={};notes={};hashes={}
for path in sorted((REVIEW/'canonical-drafts').glob('*.json')):
    record=read(path);rid=record['record_id'];bindings[rid]={};notes[rid]={};hashes[rid]=sha(path)
    for mat in record['materials']:
        mid=mat['id'];ident=DOTS.get(rid,'identity-dabbousi-bare-or-zns-dots') if mid=='dots' else mapping[mid];entry=allentries[ident]
        assert mat.get('formula')==entry.get('formula'),(rid,mid,mat.get('formula'),entry.get('formula'))
        bindings[rid][mid]=ident;notes[rid][mid]=' '.join(entry.get('limitations',[]))
        if ident in new:entry['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':mat.get('evidence',[])})
        if mid=='dezn':notes[rid][mid]+=' The 0.2 micrometer source filtration does not specify filter material; no PTFE or Danek vacuum-transfer treatment is inherited.'
        elif mid=='pyridine':notes[rid][mid]='Free pyridine reference; surface adsorption, ligand count and geometry are not established. '+notes[rid][mid]
        elif mid=='hexane':notes[rid][mid]='Reference n-hexane connectivity does not establish a measured bottle composition. '+notes[rid][mid]
        elif mid=='topse':notes[rid][mid]='TOPSe molecular identity only; the source stock is 0.1 mol Se in 100 mL TOP, reported as 1 M. Stock graph and charge values remain in the recipe. '+notes[rid][mid]
        elif mid=='butanol':notes[rid][mid]='The source explicitly specifies 1-butanol. In ZnS overgrowth 5 mL prevents TOPO solidification; in CdS storage equal amounts of hexane and butanol are used. This is not a stated quench. '+notes[rid][mid]
        elif mid=='cu':notes[rid][mid]='Copper is the radiation-source element, not a sample ingredient; procedure-specific operating values remain in the record. '+notes[rid][mid]
summary={'newEntryCount':len(entries),'reusedEntryCount':len(REUSE),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),
 'new2dModels':len(MOLECULES),'new3dModels':len(models),'referenceCards':len(CARDS),'newUnminimizedIllustrativeModels':[],'reusedUnminimizedIllustrativeModels':['diethylzinc']}
assert len(bindings)==17
dump(OUT/'registry-additions.json',{'schemaVersion':'1.0.0','assetPurpose':'Proposed Dabbousi1997 illustrative references; no Site modification','entries':entries,'summary':summary})
dump(OUT/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':hashes,'unresolved':[]})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'reused-references.json',{'existingRegistrySha256':sha(EXISTING/'registry.json'),'entries':[{'id':i,'sourceUrls':old[i]['sourceUrls'],'assetPaths':{k:old[i][k] for k in ['svgPath','model2dPath','model3dPath'] if old[i].get(k)},'assetHashes':old[i]['assetHashes']} for i in REUSE]})
dump(OUT/'missing-identities.json',{'entries':[{'id':i,'name':name,'formula':f,'limitation':note,'model2d':False,'model3d':False} for i,name,f,display,kind,note in CARDS],
 'extraLimits':['Rhodamine 590 and 640 remain unresolved identity cards; PVB and MTD300P20 have no invented finite molecular graphs.', 'Solid supports, instrument anodes, environmental air and nanocrystal families are reference cards, not atomic models.', 'No CdSe/ZnS or CdSe/CdS atomic interface, measured lattice, CIF, ligand geometry or exact batch is generated.', '1-butanol is explicitly named in this source; this identity does not resolve unspecified butanol in other papers.', 'No external identifier was guessed or looked up. Existing reused molecular provenance is retained.']})
dump(OUT/'model-provenance.json',{'sourceDoi':'10.1021/jp971091y','sourceSha256':SOURCE_HASH,'software':'RDKit '+RDVERSION,'randomSeed':SEED,
 'identityVerification':'Explicit octane name checked against conventional straight-chain formula and connectivity; no network or PubChem ID lookup. No claim of direct bond-structure determination by the source.',
 'newReferences':[{k:e[k] for k in ['id','formula','provenance','assetHashes']} for e in entries],'summary':summary})
print(json.dumps(summary,indent=2))
