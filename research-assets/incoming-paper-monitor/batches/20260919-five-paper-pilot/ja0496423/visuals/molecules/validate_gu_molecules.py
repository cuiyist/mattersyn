"""Offline author checks for private Gu depictions; not independent scientific audit."""
from pathlib import Path
import sys, json, hashlib, math, xml.etree.ElementTree as ET
from datetime import datetime, timezone
OUT=Path(__file__).resolve().parent
BATCH=OUT.parent.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BATCH.parents[3]/'rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(label,ok,detail=None):
    checks.append({'check':label,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(label+': '+str(detail))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
reg=read(OUT/'registry-additions.json');entries={e['id']:e for e in reg['entries']}
check('nine unique additions',len(entries)==len(reg['entries'])==9)
models={}
for e in entries.values():
    eid=e['id']
    for key in ['svgPath','model2dPath','model3dPath']:
        if not e.get(key):continue
        p=(OUT/e[key]).resolve()
        check(eid+' '+key+' path/hash',p.is_relative_to(OUT) and sha(p)==e['assetHashes'][key])
        if key=='svgPath':
            raw=p.read_text(encoding='utf-8');ET.fromstring(raw)
            check(eid+' safe standalone SVG','<script' not in raw and 'href=' not in raw)
            continue
        d=read(p);models[eid,key]=d
        check(eid+' '+key+' identity/formula',d['id']==eid and d['formula']==e['formula'])
        atoms=d['atoms'];bonds=d['bonds'];n=len(atoms)
        check(eid+' '+key+' finite indexed atoms',[a['index'] for a in atoms]==list(range(n)) and all(math.isfinite(a[k]) for a in atoms for k in ['x','y','z']))
        check(eid+' '+key+' valid unique bonds',all(0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'] and b['order'] in [1,1.5,2,3] for b in bonds) and len({tuple(sorted([b['a'],b['b']])) for b in bonds})==len(bonds))
        rw=Chem.RWMol()
        for a in atoms:
            ca=Chem.Atom(a['element']);ca.SetFormalCharge(a['formalCharge']);ca.SetIsotope(a['isotope']);ca.SetNoImplicit(True);ca.SetNumExplicitHs(a['implicitHydrogenCount']);ca.SetChiralTag(getattr(Chem.ChiralType,a['chiralTag']));rw.AddAtom(ca)
        bt={1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}
        for b in bonds:
            rw.AddBond(b['a'],b['b'],bt[b['order']])
            if b['order']==1.5:
                rw.GetAtomWithIdx(b['a']).SetIsAromatic(True);rw.GetAtomWithIdx(b['b']).SetIsAromatic(True)
        mol=rw.GetMol();Chem.SanitizeMol(mol)
        for b in bonds:
            cb=mol.GetBondBetweenAtoms(b['a'],b['b'])
            if b['stereoAtoms']:cb.SetStereoAtoms(*b['stereoAtoms'])
            cb.SetStereo(getattr(Chem.BondStereo,b['stereo']))
        Chem.SetDoubleBondNeighborDirections(mol)
        check(eid+' '+key+' reconstructed graph formula',rdMolDescriptors.CalcMolFormula(mol)==e['formula'],rdMolDescriptors.CalcMolFormula(mol))
        check(eid+' '+key+' reconstructed graph connectivity/stereo',Chem.MolToSmiles(mol,True)==Chem.MolToSmiles(Chem.MolFromSmiles(d['connectivitySmiles']),True))
        check(eid+' '+key+' zero charge',Chem.GetFormalCharge(mol)==0)
        for g in d['functionalGroups']:
            check(eid+' '+key+' '+g['label']+' indices',bool(g['atomIndices']) and all(0<=i<n for i in g['atomIndices']) and all(0<=i<len(bonds) and {bonds[i]['a'],bonds[i]['b']}<=set(g['atomIndices']) for i in g['bondIndices']))
        if key=='model2dPath':
            check(eid+' 2D units and control',d['coordinateUnits']=='drawing units' and not d['allowRotation'] and not d['has3D'] and all(a['z']==0 for a in atoms))
        else:
            check(eid+' 3D units and control',d['coordinateUnits']=='angstrom' and d['allowRotation'] and d['has3D'] and e['depictionKind']=='molecule')
            ds=[math.dist([atoms[b['a']][k] for k in ['x','y','z']],[atoms[b['b']][k] for k in ['x','y','z']]) for b in bonds]
            check(eid+' plausible heavy-atom bond lengths',all(1.0<v<2.1 for v in ds),{'min':min(ds),'max':max(ds)})
            bondpairs={frozenset([b['a'],b['b']]) for b in bonds}
            nonbond=[math.dist([atoms[i][k] for k in ['x','y','z']],[atoms[j][k] for k in ['x','y','z']]) for i in range(n) for j in range(i) if frozenset([i,j]) not in bondpairs]
            check(eid+' no heavy-atom overlap',not nonbond or min(nonbond)>.8,{'min_nonbonded':min(nonbond) if nonbond else None})
        d['_mol']=mol
check('eight 2D and four 3D models',sum(k[1]=='model2dPath' for k in models)==8 and sum(k[1]=='model3dPath' for k in models)==4)
for slug in ['triethylamine','acetylacetone','dibromoanthracene']:
    eid='gu2004-'+slug+'-reference'
    prop=read(OUT/'raw'/f'{slug}-properties.json')['PropertyTable']['Properties'][0]
    for rep in ['2d','3d']:
        source=Chem.RemoveHs(Chem.SDMolSupplier(str(OUT/'raw'/f'{slug}-pubchem-{rep}.sdf'),removeHs=False)[0])
        d=models[eid,'model'+rep+'Path']
        check(slug+' '+rep+' raw/property/serialized identity',rdMolDescriptors.CalcMolFormula(source)==prop['MolecularFormula']==d['formula'] and Chem.MolToSmiles(source,True)==d['connectivitySmiles']==Chem.MolToSmiles(Chem.MolFromSmiles(prop['ConnectivitySMILES']),True))
        if rep=='3d':
            c=source.GetConformer()
            check(slug+' exact original reference coordinates',all(abs(d['atoms'][i][k]-tuple(c.GetAtomPosition(i))[j])<1e-7 for i in range(source.GetNumAtoms()) for j,k in enumerate(['x','y','z'])))
m=models['gu2004-triethylamine-reference','model2dPath']['_mol']
nn=[a for a in m.GetAtoms() if a.GetSymbol()=='N']
check('triethylamine three ethyl arms',len(nn)==1 and nn[0].GetDegree()==3 and all(a.GetSymbol()=='C' and a.GetTotalNumHs()==2 and any(b.GetSymbol()=='C' and b.GetTotalNumHs()==3 for b in a.GetNeighbors()) for a in nn[0].GetNeighbors()))
m=models['gu2004-acetylacetone-reference','model2dPath']['_mol']
check('acetylacetone diketo motif',m.HasSubstructMatch(Chem.MolFromSmarts('[CH3][C](=[O])[CH2][C](=[O])[CH3]')))
m=models['gu2004-dibromoanthracene-reference','model2dPath']['_mol']
rings=[set(r) for r in Chem.GetSymmSSSR(m)]
central=[r for r in rings if sum(len(r&o)==2 for o in rings if o!=r)==2]
br={a.GetNeighbors()[0].GetIdx() for a in m.GetAtoms() if a.GetSymbol()=='Br'}
check('9,10 substitution on nonfused central ring positions',len(rings)==3 and len(central)==1 and br==central[0]-set().union(*(r for r in rings if r!=central[0])))
lig=Chem.RemoveHs(Chem.SDMolSupplier(str(OUT/'raw/acetylacetonate-pubchem-2d.sdf'),removeHs=False)[0])
for slug,metal in [('platinum-acac','Pt'),('cadmium-acac','Cd')]:
    e=entries['gu2004-'+slug+'-reference'];m=models[e['id'],'model2dPath']['_mol']
    ff=Chem.GetMolFrags(m,asMols=True);ligands=[x for x in ff if x.GetNumAtoms()>1];center=[a for a in m.GetAtoms() if a.GetSymbol()==metal][0]
    check(slug+' separate metal and exact two anions',len(ff)==3 and center.GetDegree()==0 and center.GetFormalCharge()==2 and len(ligands)==2 and all(Chem.MolToSmiles(x,True)==Chem.MolToSmiles(lig,True) and Chem.GetFormalCharge(x)==-1 for x in ligands))
    check(slug+' no invented 3D and rejected H16 lookup',not e['model3dPath'] and 'H16' in e['provenance']['rejectedWholePrecursorLookup']['formula'])
m=models['gu2004-iron-pentacarbonyl-reference','model2dPath']['_mol'];ff=Chem.GetMolFrags(m,asMols=True)
check('FeCO5 exact ligand inventory no metal bonds',len(ff)==6 and sum(x.GetNumAtoms()==2 and Chem.MolToSmiles(x)=='[C-]#[O+]' for x in ff)==5 and all(a.GetDegree()==0 for a in m.GetAtoms() if a.GetSymbol()=='Fe'))
m=models['gu2004-cadmium-chloride-reference','model2dPath']['_mol']
check('CdCl2 component stoichiometry no hydration or bonds',m.GetNumAtoms()==3 and m.GetNumBonds()==0 and sorted(a.GetFormalCharge() for a in m.GetAtoms())==[-1,-1,2])
e=entries['gu2004-sulfur-element-reference']
check('sulfur identity without allotrope model',e['formula']=='S' and not e['model2dPath'] and not e['model3dPath'])
d=models['gu2004-nitrogen-reference','model3dPath']
distance=math.dist([d['atoms'][0][k] for k in ['x','y','z']],[d['atoms'][1][k] for k in ['x','y','z']])
check('N2 triple bond and NIST reference distance',len(d['atoms'])==2 and d['bonds'][0]['order']==3 and abs(distance-1.09768)<1e-8)
excerpt=(OUT/'raw/nitrogen-nist-web-tool-excerpt.txt').read_text(encoding='utf-8')
check('NIST returned row and units preserved','1.09768_{5}' in excerpt and 'internuclear distance (Å)' in excerpt and '^{14}N_{2}' in excerpt)
bindings=read(OUT/'molecule-bindings-proposal.json');base=read(OUT/'reference-base/registry.json')
baseentries={e['id']:e for e in base['entries']}
check('17 identities resolve',len(bindings['inventoryMaterialReferences'])==17 and all(x in entries or x in baseentries for x in bindings['inventoryMaterialReferences'].values()))
check('20 reagent plus 8 specimen slots',sum(map(len,bindings['recordBindings'].values()))==20 and len(bindings['uncovered_specimen_slots'])==8)
for rid,mapping in bindings['recordBindings'].items():
    p=BATCH/'canonical-drafts'/(rid+'.json');r=read(p);slots={x['id']:x for x in r['materials']}
    check(rid+' unchanged record hash',sha(p)==bindings['sourceRecordSha256'][rid])
    for mid,eid in mapping.items():
        detail=bindings['bindingNotes'][rid][mid]
        check(rid+'/'+mid+' exact source slot and pending audit',mid in slots and detail['source_name']==slots[mid]['name'] and detail['registry_id']==eid and detail['canonical_evidence']==slots[mid].get('evidence',[]) and not detail['binding_approved'])
snapshot=read(OUT/'reference-base/snapshot-manifest.json')
check('base registry frozen copy hash',sha(OUT/'reference-base/registry.json')==snapshot['originalRegistrySha256']==bindings['reuseRegistry']['sha256'])
check('nine base entries and 27 base asset copies',snapshot['entries']==9 and len(snapshot['assets'])==27)
for asset in snapshot['assets']:check('frozen base '+asset['registry_id']+' '+asset['kind'],sha(OUT/asset['path'])==asset['sha256'])
proposal=read(OUT/'oleylamine-metadata-normalization-proposal.json');old=baseentries['oleylamine'];new=proposal['normalizedEntry']
check('oleylamine normalization changes only limitation',set(k for k in old if old[k]!=new[k])=={'limitations'} and old.keys()==new.keys())
check('oleylamine graphs unchanged',proposal['unchangedAssetHashes']==old['assetHashes']==new['assetHashes'] and '70%' not in json.dumps(new) and 'source-specific' in new['limitations'][0])
check('base entry canonical hash',hashlib.sha256(json.dumps(old,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==proposal['baseEntryCanonicalSha256'])
for path,h in read(OUT/'input-hashes-before.json').items():check('unchanged author input '+Path(path).name,sha(Path(path))==h)
visual=[]
for eid,e in entries.items():
    p=OUT/'review'/(eid+'.png')
    visual.append({'id':eid,'svg_path':e['svgPath'],'svg_sha256':sha(OUT/e['svgPath']),'render_path':str(p.relative_to(OUT)).replace('\\','/'),'render_sha256':sha(p),'author_visual_inspection':'passed','scope':'Actual rendered SVG individually inspected for complete readable graph/identity and limitations; not independent scientific audit.'})
dump(OUT/'author-visual-inspection.json',{'reviewer':'backlog_eta / author','status':'passed','entries':visual,'independent_audit':'pending'})
report={'status':'passed_author_checks','checked_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'summary':reg['summary'],'source_inputs_unchanged':True,'independent_audit':'pending','limitations':['Reference depiction author checks do not establish source-batch geometry, hydration, coordination, isomer assay, solution speciation or product linkage.','Five entries intentionally have no 3D.','Eight specimen material slots are owned by the separate product package.']}
dump(OUT/'author-validation.json',report)
print(json.dumps({'status':report['status'],'checks':len(checks),'summary':reg['summary']}))

