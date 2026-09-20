"""Build 2D depictions, optional illustrative 3D, and explicit record bindings.

Chemistry is from cached primary PubChem records or previously verified assets.
Unknown mixtures/specimens never receive invented molecular coordinates.
"""
import sys,json,copy,re,hashlib,math,html,collections
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
RESEARCH=OUT.parents[1];SITE=OUT.parents[2]/'recipe-atlas'
sys.path.insert(0,str(RESEARCH/'rdkit-runtime'))
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem,rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
SEED=20260918
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def slug(s):return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def formula_counts(s):return collections.Counter({a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)})
catalog=json.loads((OUT/'source-catalog.json').read_text(encoding='utf-8'))
previous={};old_sources={}
for file in ['molecular-structures.json','cdse-molecular-structures.json','peng2000-molecular-structures.json']:
    p=SITE/'dist/assets'/file
    for m in json.loads(p.read_text(encoding='utf-8')):
        if m.get('atoms') and (m.get('representation')=='3d' or '3D conformer' in m.get('modelType','')):
            if m['id'] not in previous:
                previous[m['id']]=m;old_sources[m['id']]={'filename':file,'sha256':sha(p)}

PATTERNS=[
 ('Carboxylic acid','[CX3;$([C]-[#6]),$([CH1])](=[OX1])[OX2H1]'),
 ('Carboxylate','[CX3;$([C]-[#6]),$([CH1])](=[OX1])[O-]'),
 ('Phosphonic acid','[P;$([P]-[#6])](=[OX1])([OX2H1])[OX2H1]'),
 ('Phosphine oxide','[P;X4;$([P](=[OX1])([#6])([#6])[#6])]=[OX1]'),
 ('Phosphine selenide head','[P](=[Se])'),
 ('Tertiary phosphine center','[P;X3;$([P]([#6])([#6])[#6])]'),
 ('Aminophosphine head group','[P;X3]([NX3])([NX3])[NX3]'),
 ('Quaternary ammonium center','[N+;X4]'),
 ('Quaternary phosphonium center','[P+;X4]'),
 ('Amine nitrogen','[N;X3;$([N]-[#6]);!$(N-P);!$(N=O);!$(N-C=O)]'),
 ('Ammonia','[NH3;X3;+0;!$(N-[!#1])]'),
 ('Alcohol group','[OX2H1][CX4]'),
 ('Ether oxygen','[OD2]([C;!$(C=O)])[C;!$(C=O)]'),
 ('Ester','[CX3;$([C]-[#6]),$([CH1])](=[OX1])[OX2][#6]'),
 ('Acyl bromide','[CX3](=[OX1])[Br]'),
 ('Silyl sulfide head','[Si]-[S]-[Si]'),
 ('Silyl selenide head','[Si]-[Se]-[Si]'),
 ('Chlorosilane head','[Si]-[Cl]'),
 ('Aromatic nitrogen','[n]'),
 ('Alkene','[CX3]=[CX3]'),
 ('Carbonate','[O-][C](=[O])[O-]'),
 ('Nitrate','[O-][N+](=[O])[O-]'),
 ('Sulfate','[O-][S](=[O])(=[O])[O-]'),
]
def groups(m):
    result=[];seen=set()
    for label,smarts in PATTERNS:
        p=Chem.MolFromSmarts(smarts)
        for match in m.GetSubstructMatches(p):
            ids=sorted(match);key=(label,tuple(ids))
            if key in seen:continue
            seen.add(key);bids=[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]
            result.append({'label':label,'atomIndices':ids,'bondIndices':bids})
    return result

def model(m,e,rep):
    c=m.GetConformer()
    atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()]
    bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()]
    return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':e.get('pubchemCid'),'source':e['sourceUrls'][0] if e['sourceUrls'] else None,'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d','indexConvention':'zero-based','coordinateUnits':'angstrom' if rep=='3d' else 'drawing units','atoms':atoms,'bonds':bonds,'functionalGroups':groups(m)}

def from_legacy(x):
    rw=Chem.RWMol()
    for a in x['atoms']:
        at=Chem.Atom(a.get('element',a.get('elem')));at.SetFormalCharge(a.get('formalCharge',a.get('charge',0)));rw.AddAtom(at)
    for b in x['bonds']:
        rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    m=rw.GetMol();Chem.SanitizeMol(m)
    c=Chem.Conformer(len(x['atoms']));c.Set3D(True)
    for i,a in enumerate(x['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
    m.AddConformer(c);return m

def depiction(m,e):
    draw=rdMolDraw2D.MolDraw2DSVG(840,360)
    opt=draw.drawOptions();opt.clearBackground=False;opt.bondLineWidth=2.2;opt.minFontSize=16;opt.maxFontSize=24;opt.padding=.09
    opt.addStereoAnnotation=False
    gg=groups(m);aa=sorted({i for g in gg for i in g['atomIndices']});bb=sorted({i for g in gg for i in g['bondIndices']})
    draw.DrawMolecule(m,highlightAtoms=aa,highlightBonds=bb,highlightAtomColors={i:(.76,.89,.94) for i in aa},highlightBondColors={i:(.54,.76,.84) for i in bb})
    draw.FinishDrawing();svg=draw.GetDrawingText()
    title=e['name']+' — '+('ionic components, not a crystal or solution coordination model' if e['depictionKind']=='ionic_components' else '2D connectivity reference')
    svg=svg.replace('<!-- END OF HEADER -->','<title>'+html.escape(title)+'</title><desc>'+html.escape(e['caption'])+'</desc>')
    p=OUT/'svg'/(e['id']+'.svg');p.write_text(svg,encoding='utf-8')
    # Native chemistry renderer PNG for visual audit; SVG remains the product asset.
    draw2=rdMolDraw2D.MolDraw2DCairo(840,360);draw2.drawOptions().padding=.09;draw2.drawOptions().bondLineWidth=2.2
    draw2.DrawMolecule(m,highlightAtoms=aa,highlightBonds=bb,highlightAtomColors={i:(.76,.89,.94) for i in aa},highlightBondColors={i:(.54,.76,.84) for i in bb});draw2.FinishDrawing()
    (OUT/'svg'/(e['id']+'-review.png')).write_bytes(draw2.GetDrawingText())
    return 'svg/'+e['id']+'.svg'

def formula_card(e):
    # Formula/species text only: no chemical bonds, lattice, surface or structure invented.
    display=e['displayFormula'] or e['formula'] or 'Composition unspecified'
    label={'mixture':'Mixture · molecular speciation unresolved','specimen':'Particle / specimen · no discrete molecule','support':'Material support · no discrete molecule','formula':'Formula reference · no coordination geometry asserted','single_atom':'Element reference','ionic_components':'Ionic components · no coordination geometry asserted'}.get(e['depictionKind'],'Identity reference')
    text=lambda x:html.escape(x,quote=True)
    size=44 if len(display)<24 else 29 if len(display)<40 else 23
    components='<text x="420" y="258" text-anchor="middle" font-family="Arial,sans-serif" font-size="23" fill="#234f66">'+text(e['ionicFormulaComponents'])+'</text>' if e.get('ionicFormulaComponents') else ''
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>{text(e["name"])}</title><desc>{text(e["caption"])}</desc><rect x="22" y="36" width="796" height="288" rx="18" fill="#f1f6fa" stroke="#ccdae5"/><text x="420" y="159" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#18384d">{text(display)}</text><text x="420" y="219" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#476276">{text(label)}</text>{components}</svg>'
    path=OUT/'svg'/(e['id']+'.svg');path.write_text(s,encoding='utf-8');return 'svg/'+e['id']+'.svg'

def validate_model(m,e):
    assert m['atoms'],e['id']
    assert all(math.isfinite(a[c]) for a in m['atoms'] for c in ['x','y','z'])
    for b in m['bonds']:assert 0<=b['a']<len(m['atoms']) and 0<=b['b']<len(m['atoms']) and b['a']!=b['b']
    for g in m['functionalGroups']:
        assert all(0<=i<len(m['atoms']) for i in g['atomIndices'])
        assert all(0<=i<len(m['bonds']) and {m['bonds'][i]['a'],m['bonds'][i]['b']}<=set(g['atomIndices']) for i in g['bondIndices'])
    if m['representation']=='3d':
        ds=[]
        for b in m['bonds']:
            a,z=m['atoms'][b['a']],m['atoms'][b['b']];d=math.sqrt(sum((a[c]-z[c])**2 for c in ['x','y','z']));ds.append(d)
            assert .45<d<2.9,(e['id'],b,d)
        m['validation']={'formulaVerified':True,'bondLengthsAngstrom':{'minimum':min(ds) if ds else None,'maximum':max(ds) if ds else None},'indicesValid':True}

entries=[];models3d=[];failures=[]
for row in catalog:
    p=row.get('properties',{});id=row['id']
    e={k:copy.deepcopy(row[k]) for k in ['id','name','aliases','depictionKind','pubchemCid']}
    e.update({'formula':p.get('MolecularFormula'),'displayFormula':None,'iupacName':p.get('IUPACName'),'sourceUrls':[row['source']] if row.get('source') else [],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'limitations':[],'provenance':{'connectivitySource':'PubChem' if row.get('fetchStatus')=='verified_api_record' else 'canonical paper identity','primaryApiPropertiesUrl':row.get('propertiesUrl'),'primaryApi2dUrl':row.get('sdfUrl'),'sourcePropertiesSha256':row.get('propertiesSha256'),'source2dSha256':row.get('sdfSha256'),'sourceLookupStatus':row['fetchStatus']}})
    if row['depictionKind']=='molecule':e['caption']='RDKit 2D depiction from verified PubChem connectivity. One reference molecule; no solution speciation, surface binding or measured geometry is claimed.'
    elif row['depictionKind']=='ionic_components':e['caption']='2D ionic-component formula representation from PubChem. Relative ion positions are drawing layout, not crystal packing, hydration coordination or solution speciation.'
    else:e['caption']='Chemical identity/formula reference. No discrete metal coordination, hydrated lattice or molecular geometry is asserted.'
    overrides={'ammonia':'NH3','zinc-nitrate-hexahydrate':'Zn(NO3)2·6H2O','cesium-carbonate':'Cs2CO3','lead-acetate-trihydrate':'Pb(CH3COO)2·3H2O','indium-chloride':'InCl3','zinc-chloride':'ZnCl2','hydrochloric-acid':'HCl(aq)','sodium-carbonate':'Na2CO3','iron-sulfate-heptahydrate':'FeSO4·7H2O','iron-iii-sulfate-hydrate':'Fe2(SO4)3·H2O','iron-ii-carbonate':'FeCO3','cobalt-acetate':'Co(CH3COO)2 · hydrate unspecified','iron-acetate':'Fe(CH3COO)2 · hydrate unspecified','ir-mecp-cod':'(MeCp)Ir(COD) · C14H19Ir'}
    e['displayFormula']=overrides.get(id,e['formula'])
    component_labels={'zinc-nitrate-hexahydrate':'Zn²⁺ + 2 NO₃⁻ + 6 H₂O','lead-acetate-trihydrate':'Pb²⁺ + 2 CH₃COO⁻ + 3 H₂O','iron-sulfate-heptahydrate':'Fe²⁺ + SO₄²⁻ + 7 H₂O'}
    if id in component_labels:e['ionicFormulaComponents']=component_labels[id]
    if id=='zinc-oxide':e['displayFormula']='ZnO'
    if id=='ir-mecp-cod':e['formula']='C14H19Ir';e['limitations'].append('Haptic cyclopentadienyl/cyclooctadiene coordination is not represented by guessed ordinary covalent bonds. PubChem name lookup did not resolve; paper identity is the source.')
    if id=='oleylamine':e['limitations'].append('The (Z)-oleylamine reference does not describe all components or isomer fractions of technical/70% oleylamine.')
    if id=='oleic-acid':e['limitations'].append('Reference oleic-acid connectivity does not specify impurities, ligand binding mode or in-situ metal-oleate species.')
    if id=='hexadecane-1-2-diol':e['limitations'].append('The source identity has unspecified stereochemistry; an illustrative conformer must not be treated as an assigned absolute configuration.')
    if id in ['lead-oleate','iron-iii-sulfate-hydrate']:e['limitations'].append('Database formula is an identity reference; stock composition/coordination and the paper-specific prepared material remain distinct.')
    if id in ['cobalt-acetate','iron-acetate']:e['limitations'].append('The incoming Saha2019 record names acetate, not acetylacetonate; hydration is unreported. Anhydrous PubChem identity does not establish the actual hydrate.')
    if id=='dimethylcadmium':e['displayFormula']='CH3–Cd–CH3';e['limitations'].append('Formula/connectivity schematic only. The PubChem disconnected ionic representation is not used as a molecule or a source of 3D geometry.')
    if id in ['selenium-element','sulfur-element']:e['limitations'].append('Elemental identity only; no powder allotrope, molecular ring, atomic gas or measured crystal structure is assigned.')
    try:
        if row['depictionKind'] in ['molecule','ionic_components'] and row['fetchStatus']=='verified_api_record':
            raw=Chem.MolFromMolFile(str(OUT/'raw'/(id+'-pubchem-2d.sdf')),removeHs=False,sanitize=True)
            assert raw is not None,id
            assert formula_counts(rdMolDescriptors.CalcMolFormula(raw))==formula_counts(e['formula']),(id,rdMolDescriptors.CalcMolFormula(raw),e['formula'])
            m=Chem.RemoveHs(raw);m.RemoveAllConformers();rdDepictor.Compute2DCoords(m,canonOrient=True)
            e['svgPath']=depiction(m,e);m2=model(m,e,'2d');m2.update({'modelType':'RDKit 2D layout from PubChem connectivity','computedBy':'RDKit '+rdkit.__version__,'caption':e['caption']});validate_model(m2,e)
            if e.get('ionicFormulaComponents'):e['svgPath']=formula_card(e)
            e['functionalGroups']=m2['functionalGroups'];e['model2dPath']='models/'+id+'-2d.json';dump(OUT/e['model2dPath'],m2)
            e['provenance']['smiles']=Chem.MolToSmiles(m,isomericSmiles=True);e['provenance']['depictionSoftware']='RDKit '+rdkit.__version__
            if row['depictionKind']=='molecule' and len(Chem.GetMolFrags(m))==1:
                old=previous.get(id)
                if old:
                    m3=copy.deepcopy(old);lm=from_legacy(m3)
                    assert rdMolDescriptors.CalcMolFormula(lm)==e['formula'],(id,'legacy formula')
                    # Connectivity compared without stereo, which stays attributed to the source.
                    assert Chem.MolToSmiles(Chem.RemoveHs(lm),isomericSmiles=False)==Chem.MolToSmiles(m,isomericSmiles=False),(id,'legacy connectivity')
                    m3['representation']='3d';m3['has3D']=True;m3['allowRotation']=True;m3['functionalGroups']=groups(lm)
                    e['provenance']['reused3dAsset']=old_sources[id]
                else:
                    m3mol=Chem.AddHs(m);m3mol.RemoveAllConformers();pp=AllChem.ETKDGv3();pp.randomSeed=SEED;pp.numThreads=1;pp.maxIterations=1500
                    status=AllChem.EmbedMolecule(m3mol,pp)
                    assert status==0,(id,'ETKDG status',status)
                    ff=None;method=None;energy=None;result=None
                    if AllChem.MMFFHasAllMoleculeParams(m3mol):
                        method='MMFF94s';props=AllChem.MMFFGetMoleculeProperties(m3mol,mmffVariant=method);ff=AllChem.MMFFGetMoleculeForceField(m3mol,props)
                    elif AllChem.UFFHasAllMoleculeParams(m3mol):method='UFF';ff=AllChem.UFFGetMoleculeForceField(m3mol)
                    if ff is not None:result=ff.Minimize(maxIts=2000);energy=ff.CalcEnergy()
                    m3=model(m3mol,e,'3d');m3.update({'modelType':'Locally computed illustrative conformer','computedBy':'RDKit '+rdkit.__version__,'sourceType':'PubChem connectivity with locally computed 3D coordinates','caption':'Computed illustrative conformer, not measured and not PubChem3D. No solvent, surface or unique conformational state is asserted.','coordinateSource':'local-rdkit','method':'ETKDGv3'+(' + '+method if method else ' without force-field minimization'),'conformerGeneration':{'randomSeed':SEED,'numThreads':1,'embeddingStatus':status,'forceField':method,'minimizationReturnCode':result,'minimizationStatus':'converged' if result==0 else 'iteration limit' if result is not None else 'unminimized; no fully parameterized force field','energyKcalMol':energy,'energyMeaning':'Classical local conformer energy, not an experimental value or a global minimum'},'connectivitySmiles':Chem.MolToSmiles(m,isomericSmiles=True),'notes':e['limitations']})
                validate_model(m3,e);e['model3dPath']='models/'+id+'-3d.json';dump(OUT/e['model3dPath'],m3);models3d.append(m3)
        if e['svgPath'] is None:e['svgPath']=formula_card(e)
    except Exception as err:
        failures.append({'id':id,'error':str(err)});e['limitations'].append('Optional model generation/validation issue: '+str(err))
        if e['svgPath'] is None:e['svgPath']=formula_card(e)
    entries.append(e);print(id,e['depictionKind'],'2d' if e['model2dPath'] else 'formula','3d' if e['model3dPath'] else '',flush=True)

# Reuse other previously verified discrete molecules for existing CdSe/material inputs.
used={x['id'] for x in entries}
for id,x in previous.items():
    if id in used or x.get('pubchemCid') is None or id=='selenium':continue
    try:
        mol=from_legacy(x);formula=rdMolDescriptors.CalcMolFormula(mol)
        e={'id':id,'name':x['name'],'formula':x['formula'],'displayFormula':x['formula'],'pubchemCid':x.get('pubchemCid'),'aliases':[x['name']], 'depictionKind':'molecule','sourceUrls':[x['source']],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':'RDKit 2D layout from previously verified PubChem-derived connectivity. No measured geometry or solution speciation is asserted.','limitations':x.get('notes',[]),'provenance':{'connectivitySource':'Previously verified PubChem-derived model','reused3dAsset':old_sources[id]}}
        assert formula==x['formula'],(id,formula)
        m=Chem.RemoveHs(mol);m.RemoveAllConformers();rdDepictor.Compute2DCoords(m);e['svgPath']=depiction(m,e);m2=model(m,e,'2d');m2['caption']=e['caption'];validate_model(m2,e);e['model2dPath']='models/'+id+'-2d.json';dump(OUT/e['model2dPath'],m2);e['functionalGroups']=m2['functionalGroups']
        m3=copy.deepcopy(x);m3['representation']='3d';m3['has3D']=True;m3['allowRotation']=True;m3['functionalGroups']=groups(mol);validate_model(m3,e);e['model3dPath']='models/'+id+'-3d.json';dump(OUT/e['model3dPath'],m3);models3d.append(m3);entries.append(e)
    except Exception as err:failures.append({'id':id,'error':'legacy optional: '+str(err)})

# Explicit alias bindings, with conservative identity cards for non-discrete inputs.
aliases={norm(a):e['id'] for e in entries for a in e['aliases']+[e['name'],e['id']]}
aliases.update({norm(a):i for a,i in [('hexylphosphonic acid (HPA)','hpa'),('trioctylphosphine oxide (TOPO)','topo'),('Tributylphosphine (TBP)','tbp'),('Bis(trimethylsilyl)selenium','tms2se')] if i in {x['id'] for x in entries}})
aliases.update({norm(a):i for a,i in [('tri-n-octylphosphine','top'),('tri-n-octylphosphine oxide','topo'),('trioctylphosphine selenide','topse'),('Oleic acid (OA)','oleic-acid'),('1-Octadecene (ODE)','1-octadecene'),('2-Propanol (isopropanol)','2-propanol')] if i in {x['id'] for x in entries}})
bindings={};binding_notes={};fallbacks={};record_sources={};families=set();record_hashes={}
input_paths={p.name:p for p in (OUT.parent/'cofe2o4/canonical').glob('*.json')}
input_paths.update({p.name:p for p in (SITE/'data/records').glob('*.json')})
for path in sorted(input_paths.values(),key=lambda p:p.name):
    r=json.loads(path.read_text(encoding='utf-8'));rid=r['record_id'];families.add(r['material']['formula']);bindings[rid]={};binding_notes[rid]={};record_hashes[rid]=sha(path)
    for mat in r['materials']:
        mid=mat['id'];name=mat['name'];identity=aliases.get(norm(name))
        if identity is None:
            key=(name,mat.get('formula'));f=fallbacks.get(key)
            if f is None:
                identity='identity-'+slug(name)[:65]+'-'+hashlib.sha256(str(key).encode()).hexdigest()[:6]
                role=mat['role'];kind='support' if role in ['support','sample_container_window','calibration_standard'] else 'specimen' if any(z in role for z in ['sample','catalyst','product_input','starting_dispersion','seed']) else 'mixture' if any(z in name.lower() for z in ['mixture','oleate','pooled','stock','precursor','carbonate source']) and not mat.get('formula') else 'formula'
                note='Source-named identity only. No discrete molecular connectivity, coordination geometry, crystal phase or surface structure is inferred.'
                if name.lower()=='hexanol':note='The source says hexanol without a positional/branch isomer. Formula C6H14O is shown without guessing 1-hexanol connectivity.'
                if 'pooled chloride' in name.lower():note='This is a pooled/rescaled author feature, not one specified chloride compound. No chemical formula or molecule is assigned.'
                f={'id':identity,'name':name,'formula':mat.get('formula'),'displayFormula':mat.get('formula') or 'Composition / species unspecified','aliases':[name],'depictionKind':kind,'sourceUrls':[],'svgPath':None,'model2dPath':None,'model3dPath':None,'caption':note,'limitations':[note],'functionalGroups':[],'provenance':{'connectivitySource':None,'identitySource':'Canonical reviewed paper record; no new chemistry inferred','sourceRecords':[]}}
                f['svgPath']=formula_card(f);fallbacks[key]=f;entries.append(f)
            identity=f['id'];f['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid})
            for source in r['sources']:
                if source['url'] not in f['sourceUrls']:f['sourceUrls'].append(source['url'])
        bindings[rid][mid]=identity
        ee=next(x for x in entries if x['id']==identity)
        if not ee.get('sourceUrls'):
            ee['sourceUrls']=[s['url'] for s in r['sources']]
        if 'technical' in name.lower():binding_notes[rid][mid]='Shows one named oleylamine reference component. Technical material composition and purity are retained in the source record, not inferred from the drawing.'
        if ee['depictionKind'] in ['formula','mixture','specimen','support']:binding_notes[rid][mid]=ee['caption']

for e in entries:
    e['aliases']=list(dict.fromkeys(e['aliases']))
    e['assetHashes']={key:sha(OUT/e[key]) for key in ['svgPath','model2dPath','model3dPath'] if e.get(key)}
    e['provenance'].setdefault('limitations','A chemical reference drawing is not an experimentally observed solution species or surface-bound configuration.')
registry={'schemaVersion':'1.0.0','assetPurpose':'Source-linked molecular identity depictions for synthesis reader interfaces','entries':entries,'summary':{'entryCount':len(entries),'recordCount':len(bindings),'bindingCount':sum(map(len,bindings.values())),'depictionKinds':dict(collections.Counter(e['depictionKind'] for e in entries)),'twoDimensionalModels':sum(bool(e['model2dPath']) for e in entries),'rotatableThreeDimensionalModels':sum(bool(e['model3dPath']) for e in entries),'materialFormulas':sorted(families)},'notes':['No browser runtime network lookup is required.','Formula/mixture/specimen depictions must not be offered as rotatable molecular structures.','Technical reagent grades, salts, hydrates and in-situ species remain source-specific.','2D atom indices and 3D atom indices are local to their model files. Never apply a 2D highlight index list to a different model.']}
dump(OUT/'registry.json',registry);dump(OUT/'bindings.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':binding_notes,'sourceRecordSha256':record_hashes,'unresolved':[]});dump(OUT/'molecules-3d.json',models3d);dump(OUT/'generation-report.json',{'rdkitVersion':rdkit.__version__,'seed':SEED,'summary':registry['summary'],'optionalModelIssues':failures,'sourceCatalogSha256':sha(OUT/'source-catalog.json')})
print(json.dumps(registry['summary'],indent=2));print('OPTIONAL ISSUES',json.dumps(failures))
