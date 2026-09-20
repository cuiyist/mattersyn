"""Private Heath1996 reference assets; read the Site, write only this directory.

No network, PubChem guesses, measured coordinates, or atomistic solid/polymer models.
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
from rdkit import Chem,__version__ as rdversion
from rdkit.Chem import AllChem,rdMolDescriptors,rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
DOI='https://doi.org/10.1021/jp951903v'
SOURCE_HASH='016e78158e4f83837f13b1412f3e08d5f7134724a3758d14468a41ff926e156a'
SEED=20260918
for folder in ['svg','models','sdf','review']:(OUT/folder).mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def composition(f):
    result=collections.Counter()
    for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',f):result[e]+=int(n or 1)
    return result
old={x['id']:x for x in read(EXISTING/'registry.json')['entries']}
REUSE=['2-propanol','acetone','helium']
for ident in REUSE:
    for key,h in old[ident]['assetHashes'].items():assert sha(EXISTING/old[ident][key])==h
MOLECULES=[
 ('mibk','methyl-isobutyl-ketone','Methyl isobutyl ketone','C6H12O','CC(=O)CC(C)C',1,
  'Conventional connectivity of the source-named methyl isobutyl ketone (4-methylpentan-2-one). The IPA:MIBK developer is 3:1, but its ratio basis and total volume are not reported.'),
 ('cf4','tetrafluoromethane','Carbon tetrafluoride','CF4','FC(F)(F)F',1,
  'Free CF4 reference. The reactive-ion-etch mixture also contains CHF3; gas ratio, flows, pressure, power and exposure time are not stated. No plasma fragments are modeled.'),
 ('chf3','trifluoromethane','Trifluoromethane','CHF3','FC(F)F',1,
  'Free CHF3 reference. A molecular depiction does not establish the plasma composition or the unspecified CF4/CHF3 mixture ratio.'),
 ('hf','hydrogen-fluoride','Hydrogen fluoride','HF','[H]F',2,
  'Neutral HF connectivity reference only. The source uses a 10% HF solution without reporting percentage basis or solvent. This molecule does not represent solution speciation, ions or a verified aqueous formulation.'),
 ('geh4','germane','Germane','GeH4','[GeH4]',2,
  'Free GeH4 reference. The source supplies a 10% GeH4-in-He mixture at 90 sccm; this flow belongs to the mixture. This is not the growing Ge solid, an adsorbed intermediate or a stock-mixture complex.')]
CARDS=[
 ('si-wafer','identity-silicon-100-wafer','Silicon (100) wafer','Si','Si (100)','support',1,
  'Source-named solid substrate. The (100) orientation is reported, but no measured atomic coordinates, wafer dimensions, doping or reconstructed surface are supplied. No discrete silicon molecule is modeled.'),
 ('silica-mask','identity-thermally-grown-silicon-dioxide-mask','Thermally grown silicon dioxide mask','SiO2','SiO₂ film','support',1,
  'Approximately 20 nm in-situ-grown oxide mask. No crystalline polymorph or atomic coordinates are assigned. Oxidant, growth temperature and oxidation time are not reported.'),
 ('pmma','identity-pmma-resist','Poly(methyl methacrylate) resist','(C5H8O2)n','PMMA · (C₅H₈O₂)ₙ','formula',1,
  'Polymer identity reference; (C5H8O2)n is a conventional repeat-unit notation, not an exact molecular formula. Chain length, molecular weight, tacticity, end groups, formulation and coating solvent are unspecified. No finite chain or methyl methacrylate monomer is substituted.'),
 ('carbon-tip','identity-carbon-whisker-afm-tip','Carbon whisker on AFM tip','C','C · carbon whisker','support',2,
  'Equipment material used on a silicon nitride AFM tip. Carbon allotrope, atomistic structure and fabrication procedure are unspecified. This is distinct from a holey-carbon TEM support film.'),
 ('silicon-nitride-tip','identity-silicon-nitride-afm-tip','Silicon nitride AFM tip',None,'Silicon nitride','support',2,
  'Equipment support identity. The source does not specify stoichiometry, so Si3N4, an atomic lattice or a molecular formula is not imposed.')]
GROUPS=[('Ketone carbonyl','[CX3](=[OX1])([#6])[#6]'),('Carbon–fluorine bond','[#6]-[F]'),('Hydrogen–fluorine bond','[H]-[F]'),('Germanium hydride','[Ge]')]
def groups(m):
    result=[]
    for name,smarts in GROUPS:
        for match in m.GetSubstructMatches(Chem.MolFromSmarts(smarts)):
            ids=sorted(match)
            result.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
    return result
def model(m,e,rep):
    c=m.GetConformer()
    return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':None,'source':DOI,
     'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d','indexConvention':'zero-based',
     'coordinateUnits':'angstrom' if rep=='3d' else 'drawing units',
     'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],
     'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()],
     'functionalGroups':groups(m),'computedBy':'RDKit '+rdversion,'eligible_training':False}
def base(ident,name,formula,kind,page,note):
    return {'id':ident,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,
     'pubchemCid':None,'sourceUrls':[DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],
     'caption':note,'limitations':[note],
     'provenance':{'identitySource':'Source-named chemical or material in Heath et al. 1996','sourceDoi':'10.1021/jp951903v',
      'sourceSha256':SOURCE_HASH,'locator':f'Main PDF p. {page}, printed p. {3143+page}',
      'sourceLookupStatus':'local_source_identity; no external identifier lookup performed','sourceRecords':[],
      'limitations':'Illustrative reference only; not measured sample, solution, surface, polymer or crystal coordinates.'}}
entries=[];models=[];geometry=[];mapping={'ipa':'2-propanol','acetone':'acetone','he':'helium'}
for mid,ident,name,formula,smiles,page,note in MOLECULES:
    assert ident not in old
    e=base(ident,name,formula,'molecule',page,note)
    e['provenance'].update({'connectivitySource':'Conventional connectivity assigned from the explicitly named compound/formula','smiles':smiles,'depictionSoftware':'RDKit '+rdversion})
    m=Chem.MolFromSmiles(smiles);assert m is not None
    if ident in ['germane','hydrogen-fluoride']:m=Chem.AddHs(m)
    assert composition(rdMolDescriptors.CalcMolFormula(m))==composition(formula),(ident,rdMolDescriptors.CalcMolFormula(m))
    assert Chem.GetFormalCharge(m)==0 and len(Chem.GetMolFrags(m))==1
    rdDepictor.Compute2DCoords(m,canonOrient=True)
    drawer=rdMolDraw2D.MolDraw2DSVG(840,360);options=drawer.drawOptions();options.clearBackground=False;options.padding=.14;options.minFontSize=20;options.maxFontSize=30;options.bondLineWidth=2
    drawer.DrawMolecule(m);drawer.FinishDrawing();svg=drawer.GetDrawingText()
    svg=svg.replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(note)+'</desc>')
    e['svgPath']='svg/'+ident+'.svg';(OUT/e['svgPath']).write_text(svg,encoding='utf-8')
    two=model(m,e,'2d');two.update({'modelType':'RDKit 2D reference connectivity layout','caption':'Illustrative compound connectivity, not measured geometry. '+note})
    e['model2dPath']='models/'+ident+'-2d.json';dump(OUT/e['model2dPath'],two);e['functionalGroups']=two['functionalGroups']
    mol=Chem.AddHs(m);mol.RemoveAllConformers();params=AllChem.ETKDGv3();params.randomSeed=SEED;params.numThreads=1;params.maxIterations=1500
    embed=AllChem.EmbedMolecule(mol,params);assert embed==0,(ident,embed)
    ff=None;method=None;energy=None;result=None
    if AllChem.MMFFHasAllMoleculeParams(mol):
        method='MMFF94s';ff=AllChem.MMFFGetMoleculeForceField(mol,AllChem.MMFFGetMoleculeProperties(mol,mmffVariant=method))
    elif AllChem.UFFHasAllMoleculeParams(mol):method='UFF';ff=AllChem.UFFGetMoleculeForceField(mol)
    if ff is not None:result=ff.Minimize(maxIts=2000);energy=ff.CalcEnergy();assert result==0,(ident,result)
    three=model(mol,e,'3d');three.update({'modelType':'Locally computed illustrative conformer','sourceType':'Source-named connectivity with locally computed coordinates','coordinateSource':'local-rdkit',
     'caption':'One computed illustrative free-compound conformer, not a measured structure. No experimental geometry, solution species or surface binding is established.',
     'method':'ETKDGv3'+(' + '+method if method else '; no parameterized minimization'),
     'conformerGeneration':{'randomSeed':SEED,'numThreads':1,'embeddingStatus':embed,'forceField':method,'minimizationReturnCode':result,
      'minimizationStatus':'converged' if result==0 else 'unminimized; no fully parameterized force field','energyKcalMol':energy,'energyMeaning':'Local classical conformer energy only; not an experimental, thermodynamic or globally minimized value.'},
     'connectivitySmiles':Chem.MolToSmiles(Chem.RemoveHs(mol)),'notes':[note]})
    e['model3dPath']='models/'+ident+'-3d.json';dump(OUT/e['model3dPath'],three);models.append(three)
    Chem.MolToMolFile(mol,str(OUT/'sdf'/(ident+'-computed-illustrative-3d.sdf')))
    e['provenance']['computed3d']={k:three[k] for k in ['computedBy','method','conformerGeneration']}
    e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath']};entries.append(e);mapping[mid]=ident
for mid,ident,name,formula,display,kind,page,note in CARDS:
    assert ident not in old
    e=base(ident,name,formula,kind,page,note);e['displayFormula']=display
    e['provenance']['connectivitySource']=None
    if mid=='pmma':e['provenance']['formulaScope']='Conventional repeat-unit notation; n and end groups are unspecified.'
    sub='Polymer reference · chain length unspecified' if mid=='pmma' else 'Solid or equipment reference · no molecular model'
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(note)+'</desc><rect x="22" y="36" width="796" height="288" rx="18" fill="#f1f6fa" stroke="#ccdae5"/><text x="420" y="157" text-anchor="middle" font-family="Arial,sans-serif" font-size="40" fill="#18384d">'+html.escape(display)+'</text><text x="420" y="219" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#476276">'+html.escape(sub)+'</text></svg>'
    e['svgPath']='svg/'+ident+'.svg';(OUT/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(OUT/e['svgPath'])};entries.append(e);mapping[mid]=ident
new={e['id']:e for e in entries};allentries={**old,**new};bindings={};notes={};sourcehashes={}
for p in sorted((REVIEW/'canonical-drafts').glob('*.json')):
    record=read(p);rid=record['record_id'];bindings[rid]={};notes[rid]={};sourcehashes[rid]=sha(p)
    for material in record['materials']:
        mid=material['id'];ident=mapping[mid];entry=allentries[ident]
        assert material.get('formula')==entry.get('formula'),(rid,mid,material.get('formula'),entry.get('formula'))
        bindings[rid][mid]=ident;notes[rid][mid]=' '.join(entry.get('limitations',[]))
        if ident in new:entry['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':material.get('evidence',[])})
        if mid=='ipa':notes[rid][mid]='Existing 2-propanol reference matches isopropyl alcohol; one molecule does not establish the 3:1 IPA:MIBK mixture basis.'
        elif mid=='acetone':notes[rid][mid]='Existing acetone reference reused for removal of PMMA resist; not a product ligand.'
        elif mid=='he':notes[rid][mid]='Helium carrier element reference reused. The metered gas stock is 10% GeH4 in He; no mixture geometry is modeled.'
summary={'newEntryCount':len(entries),'reusedEntryCount':len(REUSE),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),
 'new2dModels':len(MOLECULES),'new3dModels':len(models),'referenceCards':len(CARDS)}
dump(OUT/'registry-additions.json',{'schemaVersion':'1.0.0','assetPurpose':'Proposed Heath1996 illustrative reference additions; no Site modification','entries':entries,'summary':summary})
dump(OUT/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':sourcehashes,'unresolved':[]})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'reused-references.json',{'existingRegistrySha256':sha(EXISTING/'registry.json'),'entries':[{'id':i,'sourceUrls':old[i]['sourceUrls'],'assetPaths':{k:old[i][k] for k in ['svgPath','model2dPath','model3dPath'] if old[i].get(k)},'assetHashes':old[i]['assetHashes']} for i in REUSE]})
dump(OUT/'missing-identities.json',{'entries':[{'id':i,'sourceMaterialId':mid,'name':name,'formula':f,'limitation':note,'model2d':False,'model3d':False} for mid,i,name,f,display,kind,page,note in CARDS],
 'extraLimits':['HF solution solvent and percentage basis remain unreported.','PMMA coating solvent and wafer-cleaning reagents are not reported.','The thermally grown oxide does not establish the oxidant used.','No external identifiers were looked up or guessed.','No Ge crystal model or lattice constant was generated.']})
dump(OUT/'model-provenance.json',{'sourceDoi':'10.1021/jp951903v','sourceSha256':SOURCE_HASH,'software':'RDKit '+rdversion,'randomSeed':SEED,'sourceLookup':'No network requests. Conventional connectivity assigned from explicit source identities.','newReferenceModels':[{k:e[k] for k in ['id','formula','provenance','assetHashes']} for e in entries],'summary':summary})
print(json.dumps(summary,indent=2))
