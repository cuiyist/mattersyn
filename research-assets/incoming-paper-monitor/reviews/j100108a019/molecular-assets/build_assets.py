"""Build proposed Littau chemical-registry additions outside the Site only.

Usage: miniforge Python -B build_assets.py. The existing RDKit runtime is read-only.
Public JSON paths are relative; private record paths are kept only in build provenance.
"""
import sys,copy,json,hashlib,math,re,html,collections
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SITE=Path('[local path redacted]')
REGISTRY=SITE/'dist/assets/chemical-registry'
sys.path.insert(0,'[local path redacted]')
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem,rdMolDescriptors,rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
SEED=20260918
DOI='https://doi.org/10.1021/j100108a019'
for folder in ['svg','models','sdf','review']:(OUT/folder).mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counts(formula):
 result=collections.Counter()
 for element,n in re.findall(r'([A-Z][a-z]?)(\d*)',formula):result[element]+=int(n or 1)
 return result
existing=read(REGISTRY/'registry.json')
old={e['id']:e for e in existing['entries']}
catalog=read(OUT/'source-catalog.json')
REUSE=['toluene','methanol','argon','water','ethanol']
for id in REUSE:
 for key,value in old[id]['assetHashes'].items():assert sha(REGISTRY/old[id][key])==value

GROUPS=[('Silicon–silicon bond','[Si]-[Si]'),('Chlorosilane head','[Si]-[Cl]'),
 ('Hydroxyl group','[OX2H1]-[CX4]'),('Carbonyl group','[CX3]=[OX1]'),
 ('Carbon–chlorine bond','[C]-[Cl]'),('Sulfuric-acid group','[S](=[O])(=[O])([OX2H1])[OX2H1]'),
 ('Methoxide anion','[C]-[O-]'),('Quaternary ammonium center','[N+;X4]'),
 ('Sodium counterion','[Na+]'),('Potassium counterion','[K+]'),('Bromide counterion','[Br-]')]
def groups(m):
 out=[];seen=set()
 for name,smarts in GROUPS:
  for match in m.GetSubstructMatches(Chem.MolFromSmarts(smarts)):
   ids=sorted(match);key=(name,tuple(ids))
   if key in seen:continue
   seen.add(key)
   out.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 return out
def model(m,e,rep):
 c=m.GetConformer()
 return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':e['pubchemCid'],
 'source':e['sourceUrls'][0],'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d',
 'indexConvention':'zero-based','coordinateUnits':'angstrom' if rep=='3d' else 'drawing units',
 'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),
 'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),
 'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],
 'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()],
 'functionalGroups':groups(m)}
def validate(m,e):
 assert counts(rdMolDescriptors.CalcMolFormula(m))==counts(e['formula']),e['id']
 assert Chem.GetFormalCharge(m)==0,e['id']
 c=m.GetConformer()
 assert all(math.isfinite(v) for p in c.GetPositions() for v in p)
 bonds=[];overlaps=[]
 for b in m.GetBonds():
  i,j=b.GetBeginAtomIdx(),b.GetEndAtomIdx();assert i!=j
  d=c.GetAtomPosition(i).Distance(c.GetAtomPosition(j));bonds.append(d)
  if c.Is3D():assert .45<d<2.9,(e['id'],'bond length',d)
 if c.Is3D():
  for i in range(m.GetNumAtoms()):
   for j in range(i):
    if c.GetAtomPosition(i).Distance(c.GetAtomPosition(j))<.45:overlaps.append((i,j))
  assert not overlaps,(e['id'],'gross overlap',overlaps)
 for g in groups(m):
  assert all(0<=i<m.GetNumAtoms() for i in g['atomIndices'])
  assert all(0<=i<m.GetNumBonds() for i in g['bondIndices'])
 return {'formula':rdMolDescriptors.CalcMolFormula(m),'formulaCountsMatch':True,'netFormalCharge':Chem.GetFormalCharge(m),
 'fragmentCount':len(Chem.GetMolFrags(m)),'finiteCoordinates':True,'indicesValid':True,
 'minimumBondLengthAngstrom':round(min(bonds),6) if c.Is3D() and bonds else None,
 'maximumBondLengthAngstrom':round(max(bonds),6) if c.Is3D() and bonds else None,'grossOverlaps':overlaps}
def depict(m,e):
 draw=rdMolDraw2D.MolDraw2DSVG(840,360);opt=draw.drawOptions()
 opt.clearBackground=False;opt.padding=.12;opt.bondLineWidth=2.2;opt.minFontSize=18;opt.maxFontSize=27
 gg=groups(m);aa=sorted({i for g in gg for i in g['atomIndices']});bb=sorted({i for g in gg for i in g['bondIndices']})
 draw.DrawMolecule(m,highlightAtoms=aa,highlightBonds=bb,
 highlightAtomColors={i:(.76,.89,.94) for i in aa},highlightBondColors={i:(.54,.76,.84) for i in bb})
 draw.FinishDrawing();svg=draw.GetDrawingText()
 svg=svg.replace('<!-- END OF HEADER -->','<title>'+html.escape(e['name'])+'</title><desc>'+html.escape(e['caption'])+'</desc>')
 (OUT/'svg'/(e['id']+'.svg')).write_text(svg,encoding='utf-8')
 return 'svg/'+e['id']+'.svg'
def identity_card(e):
 # Text only: an unresolved identity is not assigned a guessed molecular graph.
 display=e['displayFormula'] or e['formula'] or 'Composition unspecified'
 line={'single_atom':'Element reference · no molecular bonds','support':'Support material · no molecular model',
 'formula':'Source identity · molecular structure unresolved'}.get(e['depictionKind'],'Source identity reference')
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img">'
 svg+='<title>'+html.escape(e['name'])+'</title><desc>'+html.escape(e['caption'])+'</desc>'
 svg+='<rect x="22" y="36" width="796" height="288" rx="18" fill="#f1f6fa" stroke="#ccdae5"/>'
 svg+='<text x="420" y="157" text-anchor="middle" font-family="Arial,sans-serif" font-size="40" fill="#18384d">'+html.escape(display)+'</text>'
 svg+='<text x="420" y="219" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#476276">'+html.escape(line)+'</text></svg>'
 (OUT/'svg'/(e['id']+'.svg')).write_text(svg,encoding='utf-8');return 'svg/'+e['id']+'.svg'

LIMITS={
 'disilane':['Free disilane reference; the supplied 0.1% Si2H6/He stock is a mixture whose percentage basis is unreported. No gas-mixture complex or pyrolysis intermediate is modeled.'],
 'helium':['Carrier-gas element identity only; a single-atom symbol is sufficient.'],
 'oxygen':['Conventional O=O connectivity reference. No electronic spin state, oxidation kinetics or solution geometry is established by this drawing.'],
 'ethylene-glycol':['Free solvent reference; one conformer does not represent surface binding, the collection medium or the mixed HPLC solvent.'],
 'dichlorosilane':['The source prints SiH2Cl2 for silanization of the coarse glass frit. This reference is not dimethylchlorosilane, not the disilane feed, and not a model of the treated surface.'],
 'sulfuric-acid':['Neutral H2SO4 reference only; the paper specifies acidic water at pH 1 but not acid concentration, dose or actual protonation/speciation.'],
 'sodium-methoxide':['Sodium methylate and sodium methoxide are the same reference identity. Disconnected ions are shown; their separation is layout, not ion-pair geometry or solution speciation.'],
 'tetrabutylammonium-bromide':['Tetrabutylammonium bromide is C16H36BrN, distinct from tetraoctylammonium bromide and tetraoctylphosphonium bromide. Ion positions are schematic.'],
 'potassium-bromide':['Disconnected K+ and Br− reference ions. No solid lattice, coordination or 3D ion-pair geometry is asserted.'],
 'acetone':['Free washing-solvent reference; not a silicon ligand or a measured sample structure.'],
 'ethylene-dichloride':['The named washing solvent ethylene dichloride resolves to 1,2-dichloroethane. The separately printed TEM-washing term ethylene chloride remains unresolved and is not bound to this entry.']}

entries=[];validation=[];models=[]
for row in catalog:
 assert row['status']=='verified_api_record',row
 id=row['id'];assert id not in old,id
 props=row['properties'];assert counts(props['MolecularFormula'])==counts(row['expectedFormula']),id
 e={'id':id,'name':row['name'],'aliases':[row['name']],'depictionKind':row['depictionKind'],
 'pubchemCid':row['pubchemCid'],'formula':row['expectedFormula'],'displayFormula':row['expectedFormula'],
 'iupacName':props['IUPACName'],'sourceUrls':[row['sourceUrl'],DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,
 'functionalGroups':[],'limitations':LIMITS[id],
 'provenance':{'connectivitySource':'PubChem','primaryApiPropertiesUrl':row['propertiesUrl'],'primaryApi2dUrl':row['sdfUrl'],
 'sourcePropertiesSha256':row['propertiesSha256'],'source2dSha256':row['sdfSha256'],
 'sourceLookupStatus':'verified_api_record','sourceLookupUrl':row['lookupUrl'],'sourceLookupSha256':row['lookupSha256'],
 'depictionSoftware':'RDKit '+rdkit.__version__,'sourceFormula':props['MolecularFormula'],
 'limitations':'Reference connectivity and computed geometry are not experimental particle, solution or surface structures.'}}
 if id=='dichlorosilane':e['aliases'].append('Dichlorosilane (printed SiH2Cl2)')
 if id=='sodium-methoxide':e['aliases']+=['Sodium methylate','Sodium methylate (sodium methoxide)']
 if id=='ethylene-dichloride':e['aliases'].append('Ethylene dichloride')
 e['caption']=('2D disconnected ionic components from verified PubChem connectivity; no relative ion geometry is asserted.' if e['depictionKind']=='ionic_components' else 'Verified chemical reference; any rotatable model is one locally computed illustrative conformer, not an experimental structure.')+' '+LIMITS[id][0]
 m=Chem.MolFromMolFile(str(OUT/'raw'/(id+'-pubchem-2d.sdf')),sanitize=True,removeHs=False)
 assert m is not None and counts(rdMolDescriptors.CalcMolFormula(m))==counts(e['formula'])
 assert Chem.GetFormalCharge(m)==props['Charge']==0
 if e['depictionKind']=='single_atom':
  assert m.GetNumAtoms()==1 and m.GetNumBonds()==0
  e['caption']='Verified helium element identity. A symbol is shown without invented molecular geometry.'
  e['svgPath']=identity_card(e)
 else:
  m=Chem.RemoveHs(m);m.RemoveAllConformers();rdDepictor.Compute2DCoords(m,canonOrient=True)
  e['svgPath']=depict(m,e);m2=model(m,e,'2d');m2.update({'modelType':'RDKit 2D layout from verified PubChem connectivity','caption':e['caption'],'computedBy':'RDKit '+rdkit.__version__})
  check=validate(m,e);m2['validation']=check;validation.append({'id':id,'representation':'2d',**check})
  e['model2dPath']='models/'+id+'-2d.json';dump(OUT/e['model2dPath'],m2);e['functionalGroups']=m2['functionalGroups']
  e['provenance']['smiles']=Chem.MolToSmiles(m,isomericSmiles=True)
  if e['depictionKind']=='ionic_components':
   assert len(Chem.GetMolFrags(m))==2,id
   assert sorted(sum(m.GetAtomWithIdx(i).GetFormalCharge() for i in frag) for frag in Chem.GetMolFrags(m))==[-1,1],id
  if e['depictionKind']=='molecule':
   assert len(Chem.GetMolFrags(m))==1
   m3mol=Chem.AddHs(m);m3mol.RemoveAllConformers();param=AllChem.ETKDGv3();param.randomSeed=SEED;param.numThreads=1;param.maxIterations=1500
   status=AllChem.EmbedMolecule(m3mol,param);assert status==0,(id,status)
   field=None;method=None;result=None;energy=None
   if AllChem.MMFFHasAllMoleculeParams(m3mol):
    method='MMFF94s';propsff=AllChem.MMFFGetMoleculeProperties(m3mol,mmffVariant=method);field=AllChem.MMFFGetMoleculeForceField(m3mol,propsff)
   elif AllChem.UFFHasAllMoleculeParams(m3mol):method='UFF';field=AllChem.UFFGetMoleculeForceField(m3mol)
   if field is not None:result=field.Minimize(maxIts=2000);energy=field.CalcEnergy()
   check=validate(m3mol,e);validation.append({'id':id,'representation':'3d',**check})
   m3=model(m3mol,e,'3d');m3.update({'modelType':'Locally computed illustrative conformer','computedBy':'RDKit '+rdkit.__version__,
    'sourceType':'Verified PubChem connectivity with locally computed coordinates','coordinateSource':'local-rdkit',
    'caption':'One computed illustrative free-compound conformer, not a measured structure or PubChem3D conformer. No solution, particle surface or unique conformation is asserted.',
    'method':'ETKDGv3'+(' + '+method if method else '; unminimized'),
    'conformerGeneration':{'randomSeed':SEED,'numThreads':1,'embeddingStatus':status,'forceField':method,
    'minimizationReturnCode':result,'minimizationStatus':'converged' if result==0 else 'iteration limit' if result is not None else 'unminimized; no fully parameterized force field',
    'energyKcalMol':energy,'energyMeaning':'Local classical conformer energy, not an experimental value, thermodynamic quantity or global minimum.'},
    'connectivitySmiles':Chem.MolToSmiles(m,isomericSmiles=True),'notes':LIMITS[id],'validation':check})
   e['model3dPath']='models/'+id+'-3d.json';dump(OUT/e['model3dPath'],m3);models.append(m3)
   Chem.MolToMolFile(m3mol,str(OUT/'sdf'/(id+'-computed-illustrative-3d.sdf')))
   e['provenance']['computed3d']={k:m3[k] for k in ['computedBy','method','conformerGeneration']}
 e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e[k]};entries.append(e)

UNRESOLVED=[
 ('r6g','identity-rhodamine-6g-unspecified-salt','R6G reference dye (counterion not specified)',None,'formula',
  'The source names R6G but does not specify the salt/counterion or dye concentration. No molecular graph, charge state or whole-salt formula is assigned.'),
 ('polymer-calibrants','identity-polystyrene-sulfonate-calibrants','Polystyrene sulfonate sodium-salt polymers',None,'formula',
  'Calibration polymers of differing molecular weights are named, without molecular weights, chain lengths or a discrete formula. No invented chain or exact calibration standard is modeled.'),
 ('reactivation-acid','identity-littau-reactivation-acid','Acid for fraction reactivation (identity not restated)',None,'formula',
  'The fraction-reactivation acid identity is not restated. Do not bind it to sulfuric acid merely because another procedure uses sulfuric acid.'),
 ('holey-carbon','identity-holey-carbon-film','Holey-carbon film','C','support',
  'A carbon support film is named. The elemental symbol is not a molecular carbon species, graphite lattice or atomic reconstruction of the film.'),
 ('ethylene-chloride','identity-littau-ethylene-chloride-unresolved','Ethylene chloride (source wording; identity unresolved)',None,'formula',
  'Printed ethylene chloride in the TEM procedure remains ambiguous. It is deliberately distinct from the separately named ethylene dichloride washing solvent.'),
 ('aot','identity-littau-aot-soap','AOT soap (identity not expanded)',None,'formula',
  'The paper does not expand AOT or give its composition. No familiar commercial surfactant identity, formula or molecular graph is silently substituted.'),
 ('mylar','identity-mylar-film','Mylar film',None,'support',
  'The paper names the film but not a molecular weight, formulation or atomistic structure. No polymer chain or measured film model is supplied.'),
 ('optical-fiber','identity-optical-fiber','Optical fiber',None,'support',
  'Mechanical mounting fiber; composition and geometry are not specified. No silica formula or crystal is assumed.')]
for material_id,id,name,formula,kind,note in UNRESOLVED:
 assert id not in old
 e={'id':id,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,
 'depictionKind':kind,'pubchemCid':None,'sourceUrls':[DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,
 'functionalGroups':[],'caption':note,'limitations':[note],
 'provenance':{'connectivitySource':None,'identitySource':'Source-named material in Littau 1993; exact graph not established.',
 'sourceLookupStatus':'not_attempted_identity_insufficient','sourceRecords':[]}}
 e['svgPath']=identity_card(e);e['assetHashes']={'svgPath':sha(OUT/e['svgPath'])};entries.append(e)

mapping={e['id']:e['id'] for e in entries[:11]}
mapping.update({id:id for id in REUSE})
mapping.update({m:id for m,id,*_ in UNRESOLVED})
mapping.update({'sodium-methylate':'sodium-methoxide','tbab':'tetrabutylammonium-bromide','kbr':'potassium-bromide'})
all_entries={**old,**{e['id']:e for e in entries}}
bindings={};binding_notes={};record_hashes={};record_paths=[]
for folder in ['canonical-drafts','procedure-drafts','context-drafts']:
 for p in sorted((REVIEW/folder).glob('*.json')):
  r=read(p);rid=r['record_id'];bindings[rid]={};binding_notes[rid]={};record_hashes[rid]=sha(p);record_paths.append(str(p))
  for mat in r['materials']:
   mid=mat['id'];identity=mapping[mid];entry=all_entries[identity]
   if mat.get('formula') and entry.get('formula'):assert counts(mat['formula'])==counts(entry['formula']),(rid,mid)
   bindings[rid][mid]=identity
   binding_notes[rid][mid]=' '.join(entry.get('limitations',[]))
   if 'sourceRecords' in entry['provenance']:
    entry['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':mat.get('evidence',[])})
   if mid=='disilane':binding_notes[rid][mid]+=' The operation meters the 0.1% Si2H6/He stock, not the isolated reference molecule.'
   if mid=='dichlorosilane':binding_notes[rid][mid]+=' Apparatus pretreatment, not a synthesis feed.'
registry={'schemaVersion':'1.0.0','assetPurpose':'Proposed Littau molecular-registry additions; illustrative reference depictions only',
 'entries':entries,'summary':{'entryCount':len(entries),'reusedExistingEntries':len(REUSE),'recordCount':len(bindings),
 'bindingCount':sum(map(len,bindings.values())),'depictionKinds':dict(collections.Counter(e['depictionKind'] for e in entries)),
 'twoDimensionalModels':sum(bool(e['model2dPath']) for e in entries),'rotatableThreeDimensionalModels':sum(bool(e['model3dPath']) for e in entries)},
 'notes':['This is a delta registry, not a replacement for the existing registry.',
 'Existing toluene, methanol, argon, water and ethanol assets are referenced, not copied.',
 'Each model has its own atom and group indices; do not reuse 2D highlight indices for 3D.',
 'Formula-only identities, gas mixtures and apparatus supports must not be presented as measured molecular structures.']}
dump(OUT/'registry-additions.json',registry)
dump(OUT/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':binding_notes,'sourceRecordSha256':record_hashes,'unresolved':[]})
dump(OUT/'reused-references.json',{'existingRegistrySha256':sha(REGISTRY/'registry.json'),
 'entries':[{'id':id,'assetPaths':{k:old[id][k] for k in ['svgPath','model2dPath','model3dPath'] if old[id].get(k)},
 'assetHashes':old[id]['assetHashes'],'sourceUrls':old[id]['sourceUrls']} for id in REUSE]})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'missing-identities.json',{'entries':[{'id':id,'sourceMaterialId':mid,'name':name,'formula':formula,'limitation':note,'model2d':False,'model3d':False} for mid,id,name,formula,kind,note in UNRESOLVED],
 'extra_limits':['Helium has an element card only; no molecular geometry is necessary.',
 'Sodium methoxide, tetrabutylammonium bromide and potassium bromide have ionic connectivity drawings only; no 3D inter-ion geometry is assigned.']})
dump(OUT/'generation-report.json',{'status':'generated_pending_independent_and_visual_validation','rdkitVersion':rdkit.__version__,
 'seed':SEED,'summary':registry['summary'],'modelChecks':validation,'sourceCatalogSha256':sha(OUT/'source-catalog.json'),
 'registryAdditionsSha256':sha(OUT/'registry-additions.json'),'bindingsAdditionsSha256':sha(OUT/'bindings-additions.json'),
 'privateSourceRecordPaths':record_paths,'limitations':['No Site or existing asset was changed.','No paper or SI was retrieved.','Official PubChem records only were fetched for eleven explicitly named chemical identities.']})
print(json.dumps(registry['summary'],indent=2))
