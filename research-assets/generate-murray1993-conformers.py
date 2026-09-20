"""Generate illustrative 3D coordinates from verified PubChem connectivity.

Only workspace-local RDKit is imported. Official 2D assets remain untouched.
"""
import copy, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'rdkit-runtime'))
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

SEED=19930922
source=json.loads((ROOT/'murray1993-molecular-structures.json').read_text(encoding='utf-8'))
results=copy.deepcopy(source)
reports=[]
pending_sdfs=[]
for entry in results:
    if entry['id'] not in {'top','topse','topo'}: continue
    raw_file=entry['assetFile']
    raw_url=entry['sdfUrl']
    mol=Chem.MolFromMolFile(str(ROOT/raw_file),sanitize=True,removeHs=False,strictParsing=True)
    assert mol is not None,entry['id']
    assert mol.GetNumAtoms()==len(entry['atoms'])
    assert rdMolDescriptors.CalcMolFormula(mol)==entry['formula']
    assert [a.GetSymbol() for a in mol.GetAtoms()]==[a['element'] for a in entry['atoms']]
    assert mol.GetNumBonds()==len(entry['bonds'])
    for rb,b in zip(mol.GetBonds(),entry['bonds']):
        assert {rb.GetBeginAtomIdx(),rb.GetEndAtomIdx()}=={b['a'],b['b']}
        assert rb.GetBondTypeAsDouble()==b['order']
    for group in entry['functionalGroups']:
        assert all(0<=i<mol.GetNumAtoms() for i in group['atomIndices'])
        assert all(set([entry['bonds'][i]['a'],entry['bonds'][i]['b']])<=set(group['atomIndices']) for i in group['bondIndices'])
    connectivity=Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True)
    mol.RemoveAllConformers()
    params=AllChem.ETKDGv3()
    params.randomSeed=SEED
    params.numThreads=1
    params.maxIterations=2000
    status=AllChem.EmbedMolecule(mol,params)
    assert status==0,(entry['id'],'embedding failed',status)
    mmff=AllChem.MMFFHasAllMoleculeParams(mol)
    uff=AllChem.UFFHasAllMoleculeParams(mol)
    ff_name=None
    ff=None
    if mmff:
        ff_name='MMFF94s'
        props=AllChem.MMFFGetMoleculeProperties(mol,mmffVariant=ff_name)
        ff=AllChem.MMFFGetMoleculeForceField(mol,props)
    elif uff:
        ff_name='UFF'
        ff=AllChem.UFFGetMoleculeForceField(mol)
    initial_energy=final_energy=min_status=None
    minimization_status='not performed: no fully parameterized MMFF/UFF force field'
    if ff is not None:
        initial_energy=ff.CalcEnergy()
        min_status=ff.Minimize(maxIts=2000,forceTol=1e-4,energyTol=1e-6)
        final_energy=ff.CalcEnergy()
        assert min_status==0,(entry['id'],'minimization did not converge',min_status)
        assert math.isfinite(final_energy) and final_energy<=initial_energy+1e-6
        minimization_status='converged'
    conf=mol.GetConformer()
    coords=[list(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]
    assert all(math.isfinite(v) for point in coords for v in point)
    assert max(p[2] for p in coords)-min(p[2] for p in coords)>0.1
    # Chemistry-aware sanity bounds, not an experimental validation.
    ranges={('C','H'):(.85,1.30),('C','C'):(1.20,1.75),('C','P'):(1.60,2.10),
            ('O','P'):(1.25,1.90),('P','Se'):(1.80,2.60)}
    distances=defaultdict(list)
    for bond in entry['bonds']:
        i,j=bond['a'],bond['b']
        pair=tuple(sorted([entry['atoms'][i]['element'],entry['atoms'][j]['element']]))
        d=math.dist(coords[i],coords[j])
        assert pair in ranges, pair
        lower,upper=ranges[pair]
        assert lower<=d<=upper,(entry['id'],pair,d)
        distances['-'.join(pair)].append(d)
    # Check gross nonbonded overlap for atoms separated by >=3 graph bonds.
    topology=Chem.GetDistanceMatrix(mol)
    pt=Chem.GetPeriodicTable()
    closest_ratio=100.0
    for i in range(mol.GetNumAtoms()):
        for j in range(i):
            if topology[i,j]<3: continue
            radii=pt.GetRvdw(mol.GetAtomWithIdx(i).GetAtomicNum())+pt.GetRvdw(mol.GetAtomWithIdx(j).GetAtomicNum())
            ratio=math.dist(coords[i],coords[j])/radii
            closest_ratio=min(closest_ratio,ratio)
            assert ratio>.55,(entry['id'],'gross nonbonded overlap',i,j,ratio)
    center=[sum(p[k] for p in coords)/len(coords) for k in range(3)]
    for atom,p in zip(entry['atoms'],coords):
        for k,key in enumerate(['x','y','z']): atom[key]=round(p[k]-center[k],7)
    out_file=f"{entry['id']}-rdkit-etkdgv3-{ff_name.lower() if ff_name else 'unminimized'}-illustrative-3d.sdf"
    generation={'software':'RDKit','version':rdkit.__version__,'embeddingMethod':'ETKDGv3',
                'randomSeed':SEED,'numThreads':1,'embeddingStatus':'success',
                'forceField':ff_name,'MMFFHasAllMoleculeParams':bool(mmff),'UFFHasAllMoleculeParams':bool(uff),
                'maxMinimizationIterations':2000 if ff else None,'minimizationReturnCode':min_status,
                'minimizationStatus':minimization_status,'initialEnergy':initial_energy,'finalEnergy':final_energy,
                'energyUnits':'kcal/mol' if ff else None,'energyMeaning':'Classical force-field potential energy for one conformer, not experimental energy or a global-minimum claim.' if ff else 'No energy was calculated: MMFF and UFF lack complete parameters.'}
    entry.update({'representation':'3d','has3D':True,'allowRotation':True,'coordinateUnits':'angstrom',
                  'assetFile':out_file,'sdfUrl':None,'sourceConnectivitySdfFile':raw_file,'sourceConnectivitySdfUrl':raw_url,
                  'sourceType':'PubChem connectivity with locally computed coordinates','coordinateSource':'local-rdkit',
                  'computedBy':f'RDKit {rdkit.__version__}',
                  'method':f'ETKDGv3 with fixed seed; {ff_name} local minimization' if ff else 'ETKDGv3 with fixed seed; no subsequent molecular force-field minimization',
                  'modelType':'Locally computed illustrative 3D conformer from PubChem connectivity',
                  'caption':'Computed illustrative conformer · RDKit; not measured or PubChem3D.' if ff else 'Computed illustrative conformer · RDKit ETKDG; unminimized; not measured or PubChem3D.',
                  'connectivitySmiles':connectivity,'conformerGeneration':generation,
                  'minimizationStatus':minimization_status,
                  'energy':{'value':final_energy,'unit':'kcal/mol','method':ff_name,'meaning':'Classical force-field energy of this local conformer'} if ff else None,
                  'atomIndexMapping':{'type':'identity','description':'Computed atom indices and bond indices match the official 2D SDF and existing functional-group selections; no atom reordering.'},
                  'notes':['PubChem supplies molecular connectivity only for this asset; all displayed 3D coordinates were generated locally.',
                           'One illustrative conformer; not measured, not a PubChem3D conformer, not an exhaustive conformer search, and not a solvent- or surface-specific geometry.',
                           'Official PubChem 2D SDF and original molecular JSON are retained unchanged.']})
    if entry['id']=='topse':
        entry['notes'].append('This is the named TOPSe compound; it does not establish a unique selenium-stock speciation or a reaction intermediate.')
    if ff is None:
        entry['notes'].append('ETKDG distance-geometry embedding only: subsequent molecular force-field minimization was not performed because MMFF/UFF lack complete parameters for this connectivity. Head-group geometry is illustrative; no energy is reported.')
    mol.SetProp('_Name',entry['name']+' - locally computed illustrative conformer')
    mol.SetProp('COORDINATE_PROVENANCE','RDKit ETKDGv3'+(' + '+ff_name if ff else '; no molecular force-field minimization')+'; not PubChem3D or experimental')
    mol.SetProp('SOURCE_CONNECTIVITY_PUBCHEM_CID',str(entry['pubchemCid']))
    mol.SetProp('COMPUTATION_METADATA',json.dumps(generation))
    pending_sdfs.append((out_file,mol))
    report={'id':entry['id'],'formula':entry['formula'],'atomCount':len(entry['atoms']),
            'bondCount':len(entry['bonds']),'formulaVerified':True,'sourceConnectivityVerified':True,
            'atomAndBondIndexOrderPreserved':True,'functionalGroupsVerified':True,
            'bondRangesAngstrom':{k:{'min':min(v),'max':max(v),'count':len(v)} for k,v in distances.items()},
            'minimumNonbondedDistanceOverVdwSum':closest_ratio,'generation':generation}
    reports.append(report)
    print(entry['id'],ff_name,minimization_status,'energy',round(final_energy,6) if final_energy is not None else None,
          {k:(round(min(v),4),round(max(v),4)) for k,v in distances.items()},flush=True)

assert len(reports)==3
# Publish the new JSON only once all requested molecules pass checks.
for file,mol in pending_sdfs:
    with Chem.SDWriter(str(ROOT/file)) as writer: writer.write(mol)
(ROOT/'murray1993-conformer-validation.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
(ROOT/'murray1993-molecular-structures-3d.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print('Saved all 3 computed conformers and the 6-entry collection.',flush=True)
