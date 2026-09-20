import copy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'rdkit-runtime'))
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem,rdMolDescriptors
entries=json.loads((ROOT/'new-molecular-structures.json').read_text(encoding='utf-8'))
entry=next(e for e in entries if e['id']=='tms2se')
sourcefile=entry['assetFile'];sourceurl=entry['sdfUrl']
mol=Chem.MolFromMolFile(str(ROOT/sourcefile),removeHs=False,sanitize=True)
assert mol is not None and rdMolDescriptors.CalcMolFormula(mol)==entry['formula']
assert [a.GetSymbol() for a in mol.GetAtoms()]==[a['element'] for a in entry['atoms']]
assert mol.GetNumBonds()==len(entry['bonds'])
for rb,b in zip(mol.GetBonds(),entry['bonds']):
    assert {rb.GetBeginAtomIdx(),rb.GetEndAtomIdx()}=={b['a'],b['b']} and rb.GetBondTypeAsDouble()==b['order']
mol.RemoveAllConformers();params=AllChem.ETKDGv3();params.randomSeed=19930922;params.numThreads=1;params.maxIterations=2000
status=AllChem.EmbedMolecule(mol,params);assert status==0
mmff=AllChem.MMFFHasAllMoleculeParams(mol);uff=AllChem.UFFHasAllMoleculeParams(mol)
ff=ffname=None
if mmff:
    ffname='MMFF94s';ff=AllChem.MMFFGetMoleculeForceField(mol,AllChem.MMFFGetMoleculeProperties(mol,mmffVariant=ffname))
elif uff:ffname='UFF';ff=AllChem.UFFGetMoleculeForceField(mol)
initial=final=code=None
if ff:
    initial=ff.CalcEnergy();code=ff.Minimize(maxIts=2000,forceTol=1e-4,energyTol=1e-6);final=ff.CalcEnergy()
    assert code==0 and math.isfinite(final) and final<=initial+1e-6
conf=mol.GetConformer();coords=[list(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]
assert all(math.isfinite(v) for p in coords for v in p) and max(p[2] for p in coords)-min(p[2] for p in coords)>.1
ranges={('C','H'):(.85,1.30),('C','Si'):(1.65,2.10),('Se','Si'):(2.0,2.80)};distances=[]
for b in entry['bonds']:
    i,j=b['a'],b['b'];pair=tuple(sorted([entry['atoms'][i]['element'],entry['atoms'][j]['element']]))
    dist=math.dist(coords[i],coords[j]);lo,hi=ranges[pair];assert lo<=dist<=hi,(pair,dist)
    distances.append({'a':i,'b':j,'elements':list(pair),'angstrom':dist})
topology=Chem.GetDistanceMatrix(mol);pt=Chem.GetPeriodicTable();lowest=100
for i in range(mol.GetNumAtoms()):
    for j in range(i):
        if topology[i,j]<3:continue
        ratio=math.dist(coords[i],coords[j])/(pt.GetRvdw(mol.GetAtomWithIdx(i).GetAtomicNum())+pt.GetRvdw(mol.GetAtomWithIdx(j).GetAtomicNum()))
        lowest=min(lowest,ratio);assert ratio>.55
center=[sum(p[k] for p in coords)/len(coords) for k in range(3)]
for a,p in zip(entry['atoms'],coords):
    for k,key in enumerate(['x','y','z']):a[key]=round(p[k]-center[k],8)
minstatus='converged' if ff else 'not performed: MMFF/UFF lack complete parameters'
generation={'software':'RDKit','version':rdkit.__version__,'embeddingMethod':'ETKDGv3','randomSeed':19930922,'numThreads':1,'embeddingStatus':'success',
 'forceField':ffname,'MMFFHasAllMoleculeParams':mmff,'UFFHasAllMoleculeParams':uff,'minimizationStatus':minstatus,'minimizationReturnCode':code,
 'initialEnergy':initial,'finalEnergy':final,'energyUnits':'kcal/mol' if ff else None}
file='new-molecular-assets/tms2se-rdkit-etkdgv3-illustrative-3d.sdf'
entry.update({'representation':'3d','has3D':True,'allowRotation':True,'coordinateUnits':'angstrom','coordinateSource':'local-rdkit',
 'sourceType':'PubChem connectivity with locally computed coordinates','sourceConnectivitySdfFile':sourcefile,'sourceConnectivitySdfUrl':sourceurl,'assetFile':file,'sdfUrl':None,
 'modelType':'Locally computed illustrative 3D conformer from PubChem connectivity','computedBy':f'RDKit {rdkit.__version__}',
 'method':'ETKDGv3 fixed seed'+('; '+ffname+' local minimization' if ff else '; no subsequent molecular force-field minimization'),
 'caption':'Computed illustrative conformer · RDKit; not measured or PubChem3D.' if ff else 'Computed illustrative conformer · RDKit ETKDG; unminimized; not measured or PubChem3D.',
 'minimizationStatus':minstatus,'conformerGeneration':generation,'energy':{'value':final,'unit':'kcal/mol','method':ffname} if ff else None,
 'atomIndexMapping':{'type':'identity','description':'Original PubChem 2D atom/bond order and functional group indices preserved.'},
 'notes':['The 3D coordinates were generated locally from verified PubChem connectivity; the original 2D SDF and new-molecular-structures.json remain unchanged.',
 'One illustrative conformer, not a measured geometry, a PubChem3D record, an exhaustive conformer search or a solvated/surface-bound species.',
 'Molecular force-field minimization '+('converged with all atoms parameterized.' if ff else 'was unavailable because MMFF/UFF lack complete parameters; no energy is reported.')]})
mol.SetProp('_Name','Bis(trimethylsilyl)selenide - locally computed illustrative conformer')
mol.SetProp('COORDINATE_PROVENANCE','RDKit ETKDGv3 '+(ffname or 'unminimized')+'; not measured or PubChem3D')
mol.SetProp('SOURCE_CONNECTIVITY_PUBCHEM_CID',str(entry['pubchemCid']))
mol.SetProp('COMPUTATION_METADATA',json.dumps(generation))
with Chem.SDWriter(str(ROOT/file)) as w:w.write(mol)
(ROOT/'new-molecular-structures-3d.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
report={'id':'tms2se','formulaVerified':True,'connectivityVerified':True,'atomAndBondOrderPreserved':True,'functionalGroupsPreserved':True,
 'generation':generation,'bondLengths':distances,'minimumNonbondedDistanceOverVdwSum':lowest}
(ROOT/'tms2se-conformer-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'saved','generation':generation,'SiSeBondLengths':[x['angstrom'] for x in distances if x['elements']==['Se','Si']],'minimumNonbondedDistanceOverVdwSum':lowest},indent=2))
