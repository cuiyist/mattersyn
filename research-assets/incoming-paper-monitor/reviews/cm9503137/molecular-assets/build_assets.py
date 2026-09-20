"""Build private Danek1996 chemical references and exact draft-material bindings.

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
DOI='https://doi.org/10.1021/cm9503137'
SOURCE_HASH='cde428b3707ab7e0fe1a24cd747e6c884d6903265d4d745a93e36d60e553321f'
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
 'cdme2':'dimethylcadmium','selenium':'selenium-element','ar':'argon','n2':'nitrogen','h2':'hydrogen','he':'helium','helium':'helium'}
REUSE=sorted(set(REUSE_MAP.values()))
for ident in REUSE:
    for key,h in old[ident]['assetHashes'].items():assert sha(EXISTING/old[ident][key])==h
MOLECULES=[
 ('dezn','diethylzinc','Diethylzinc','C4H10Zn','CC[Zn]CC',
  'Conventional neutral diethylzinc monomer connectivity with two ethyl groups bonded to Zn. Reference identity is shared by solution and OMCVD grades, while their supplier and treatment remain record-specific. No measured solution association, adduct, precursor concentration or adsorption state is assigned.'),
 ('h2se','hydrogen-selenide','Hydrogen selenide','H2Se','[SeH2]',
  'Free H2Se connectivity reference for the OMCVD selenium feed. It is distinct from TOPSe used in solution overgrowth. No surface decomposition pathway or reactive intermediate is modeled.'),
 ('nonane','nonane','Nonane','C9H20','CCCCCCCCC',
  'Conventional straight-chain nonane reference. In this source it is an optional, small, unspecified amount used to accelerate redispersion. One computed conformer is not a measured solvent conformation or a prescribed amount.'),
 ('acetonitrile','acetonitrile','Acetonitrile','C2H3N','CC#N',
  'Free acetonitrile reference for the electrospray cosolvent. The source says twofold excess over the pyridine dispersion; the molecular model establishes neither the ratio basis nor a unique final concentration.')]
CARDS=[
 ('identity-danek-cdse-seeds','CdSe nanocrystal seeds','CdSe','CdSe seeds','support',
  'Source-scoped CdSe seed family. Purified, size-selected seeds are used in the standard overgrowth; comparison controls do not restate an exact seed sample. Formula refers to inorganic composition, not a finite molecular formula. Surface ligands, particle dimensions and batch identity remain record-specific.'),
 ('identity-danek-bare-cdse-film-feed','Bare CdSe dots for film deposition','CdSe','CdSe · no ZnSe overlayer','support',
  'Pyridine-capped CdSe feed for bare-dot film comparisons. Bare means no preformed ZnSe overlayer, not ligand-free. The specimen varies among figure cohorts; no universal size, atom count or experimentally refined core lattice is assigned.'),
 ('identity-danek-overcoated-cdse-film-feed','ZnSe-overcoated CdSe dots for film deposition','CdSe/ZnSe','CdSe core / ZnSe overlayer','support',
  'Architecture identity for the overcoated film-feed family. Composition ratio and initial size differ among source cohorts. No uniform concentric shell, measured interface coordinates, surface ligand arrangement or perfect shell phase is asserted.'),
 ('identity-danek-annealing-particles','CdSe/ZnSe particles for annealing film','CdSe/ZnSe','CdSe/ZnSe · annealing specimen','support',
  'Particles with reported [ZnSe/CdSe]=2.5 deposited from solution for the annealing comparison. This is distinct from a ZnSe-matrix ES-OMCVD film. The 400/450 °C source conflict and pre/post-anneal state are retained in the record, not resolved by this card.'),
 ('identity-danek-electrospray-particle-options','Pyridine-capped particle feed alternatives',None,'CdSe OR CdSe/ZnSe','support',
  'The source permits bare CdSe or ZnSe-overcoated CdSe as alternative particle feeds. This card is an alternative identity family, not proof of a physical mixture, shared batch or simultaneous use. Pyridine surface coverage is unspecified.'),
 ('identity-danek-characterization-specimen','Particle or film characterization specimen',None,'Particle / film specimen','support',
  'Procedure-level sample family selected by measurement. Separate dispersions, precipitated powders and films are prepared for different instruments. No universal formula, single serial specimen or one-to-one batch linkage is invented.'),
 ('identity-danek-glass-slide','Glass slide substrate',None,'Glass slide','support',
  'Source-named glass substrate. ES-OMCVD uses degreased Fisher microscope slides; the annealing experiment names a glass slide. Composition, degreasing reagent and atomistic structure are unspecified; this is not a quartz crystal model.'),
 ('identity-butanol-unspecified-isomer','Butanol (isomer unspecified)','C4H10O','C₄H₁₀O · isomer unspecified','formula',
  'Source names butanol without an isomer. Formula is compatible with the alcohol family but no connectivity, stereochemistry or PubChem identity is assigned. The existing 1-butanol model is deliberately not substituted.'),
 ('identity-danek-rhodamine590','Rhodamine 590 fluorescence standard',None,'Rhodamine 590','formula',
  'Source designation of the fluorescence standard in methanol. Exact salt, counterion, CAS identity and concentration are unverified; no molecular graph is assigned and the earlier R6G reference is not silently substituted.'),
 ('identity-danek-silicon-wafer','Silicon wafer for XRF/XRD','Si','Si wafer','support',
  'Solid specimen support. The XRD procedure specifies (100), whereas the XRF procedure names a silicon wafer without orientation. The card does not propagate the XRD orientation to XRF or invent measured surface coordinates.'),
 ('identity-danek-cdse-xrf-standard','CdSe powder XRF standard','CdSe','CdSe powder standard','support',
  'The source uses 99.99% CdSe powder from Alfa as an XRF standard. It is not the synthesized CdSe seed population and its crystal structure or coordinates are not reported here.'),
 ('identity-danek-znse-xrf-standard','OMCVD ZnSe film XRF standard','ZnSe','ZnSe film standard','support',
  'Authors’ laboratory-grown OMCVD ZnSe reference film used for XRF. Standard-specific synthesis details and atomic coordinates are not restated. It is distinct from the colloidal overlayer and the composite-film matrix.'),
 ('identity-danek-nickel-tem-grid','Nickel component of TEM grid','Ni','Ni · TEM grid','support',
  'Nickel component of the source nickel/carbon TEM grid. Grid geometry and lattice coordinates are unreported. No copper grid substitution or nickel nanocrystal is implied.'),
 ('identity-danek-carbon-tem-support','Carbon TEM support and overcoat','C','C · support / overcoat','support',
  'The source names carbon on the nickel/carbon grid and an added carbon overcoat for beam stability. These are distinct preparation roles. Carbon allotrope, thickness and coordinates are unspecified; no holey-film or whisker geometry is substituted.'),
 ('identity-palladium-gas-purifier','Palladium hydrogen-purification cell','Pd','Pd · purifier','support',
  'Equipment material for purification of the hydrogen carrier. No Pd nanocrystal synthesis, cell geometry, molecular Pd species or measured metal structure is supplied.'),
 ('identity-chromium-xrf-anode','Chromium XRF-generator anode','Cr','Cr · XRF anode','support',
  'Instrument component named for the XRF generator. This is not a sample reagent, chromium nanocrystal or experimentally reconstructed anode.'),
 ('identity-copper-xrd-source','Copper XRD radiation source','Cu','Cu · XRD source','support',
  'Source specifies Cu Kα radiation. Copper is a radiation-source reference, not a synthesized specimen, reagent or an additional TEM-grid assignment.')]
GROUPS=[('Zinc–carbon bonds','[#6]-[Zn]-[#6]'),('Selenium hydride','[Se]'),('Nitrile group','[C]#[N]')]
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
     'provenance':{'identitySource':'Source-named compound or material in Danek et al. 1996','sourceDoi':'10.1021/cm9503137','sourceSha256':SOURCE_HASH,
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
mapping.update({'cdse':'identity-danek-cdse-seeds','cdse-seeds':'identity-danek-cdse-seeds','sample':'identity-danek-characterization-specimen','glass':'identity-danek-glass-slide',
 'butanol':'identity-butanol-unspecified-isomer','rhodamine590':'identity-danek-rhodamine590','si-wafer':'identity-danek-silicon-wafer','cdse-standard':'identity-danek-cdse-xrf-standard',
 'znse-standard':'identity-danek-znse-xrf-standard','nickel':'identity-danek-nickel-tem-grid','carbon':'identity-danek-carbon-tem-support','palladium':'identity-palladium-gas-purifier',
 'chromium':'identity-chromium-xrf-anode','copper':'identity-copper-xrd-source'})
DOTS={'danek-1996-annealing-control':'identity-danek-annealing-particles','danek-1996-bare-dot-film':'identity-danek-bare-cdse-film-feed',
 'danek-1996-overcoated-dot-film':'identity-danek-overcoated-cdse-film-feed','danek-1996-electrospray-dispersion':'identity-danek-electrospray-particle-options'}
new={e['id']:e for e in entries};allentries={**old,**new};bindings={};notes={};hashes={}
for path in sorted((REVIEW/'canonical-drafts').glob('*.json')):
    record=read(path);rid=record['record_id'];bindings[rid]={};notes[rid]={};hashes[rid]=sha(path)
    for mat in record['materials']:
        mid=mat['id'];ident=DOTS[rid] if mid=='dots' else mapping[mid];entry=allentries[ident]
        assert mat.get('formula')==entry.get('formula'),(rid,mid,mat.get('formula'),entry.get('formula'))
        bindings[rid][mid]=ident;notes[rid][mid]=' '.join(entry.get('limitations',[]))
        if ident in new:entry['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':mat.get('evidence',[])})
        if mid=='dezn':notes[rid][mid]+=' The exact supplier/treatment for this use is retained in the canonical material and is not transferred between solution and OMCVD grades.'
        elif mid=='pyridine':notes[rid][mid]='Free pyridine reference; surface adsorption, ligand count and geometry are not established. '+notes[rid][mid]
        elif mid=='hexane':notes[rid][mid]='Reference n-hexane connectivity does not establish a measured bottle composition. '+notes[rid][mid]
        elif mid=='topse':notes[rid][mid]='TOPSe molecule only; initial 0.5 mmol, 1.0 M cited stock and equimolar feed are separate quantities. '+notes[rid][mid]
        elif mid=='helium':notes[rid][mid]='Element identity reused for liquid-helium coolant; this card is not a gas-phase assumption. '+notes[rid][mid]
summary={'newEntryCount':len(entries),'reusedEntryCount':len(REUSE),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),
 'new2dModels':len(MOLECULES),'new3dModels':len(models),'referenceCards':len(CARDS),'unminimizedIllustrativeModels':['diethylzinc']}
assert len(bindings)==12
dump(OUT/'registry-additions.json',{'schemaVersion':'1.0.0','assetPurpose':'Proposed Danek1996 illustrative references; no Site modification','entries':entries,'summary':summary})
dump(OUT/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':hashes,'unresolved':[]})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'reused-references.json',{'existingRegistrySha256':sha(EXISTING/'registry.json'),'entries':[{'id':i,'sourceUrls':old[i]['sourceUrls'],'assetPaths':{k:old[i][k] for k in ['svgPath','model2dPath','model3dPath'] if old[i].get(k)},'assetHashes':old[i]['assetHashes']} for i in REUSE]})
dump(OUT/'missing-identities.json',{'entries':[{'id':i,'name':name,'formula':f,'limitation':note,'model2d':False,'model3d':False} for i,name,f,display,kind,note in CARDS],
 'extraLimits':['PTFE filters occur in source/operations but not in these drafts’ materials arrays; no extra material binding was invented.','No salt identity was assigned to rhodamine 590 or isomer to butanol.','No core/shell atomic coordinates, CIF, ligands, alloy lattice or synthetic crystal were generated.','Exact external identifiers were not looked up or guessed.']})
dump(OUT/'model-provenance.json',{'sourceDoi':'10.1021/cm9503137','sourceSha256':SOURCE_HASH,'software':'RDKit '+RDVERSION,'randomSeed':SEED,
 'identityVerification':'Four explicit compound names checked against conventional formula and connectivity; no network or PubChem ID lookup. No claim of direct bond-structure determination by the source.',
 'newReferences':[{k:e[k] for k in ['id','formula','provenance','assetHashes']} for e in entries],'summary':summary})
print(json.dumps(summary,indent=2))
