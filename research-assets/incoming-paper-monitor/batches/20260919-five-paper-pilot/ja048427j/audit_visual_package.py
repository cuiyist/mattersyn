"""Independent read-only checks; writes only auditor-owned reports in this paper directory."""
import json, pathlib, hashlib, math, sys, collections, re, datetime
sys.path.insert(0, r'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
P=pathlib.Path(__file__).resolve().parent
V=P/'visuals'
R=P.parents[3]
CHECKS=[]; BOUND={}; DETAILS=[]
def ck(label, condition, detail=None):
    CHECKS.append({'label':label,'passed':bool(condition),'detail':detail})
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def bind(p,expected=None):
    p=pathlib.Path(p); h=sha(p); BOUND[str(p)] = h
    if expected:ck('Hash '+str(p),h==expected)
    return h
def read(p):
    p=pathlib.Path(p);bind(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ptr(d,p):
    for x in p.strip('/').split('/'):
        d=d[int(x)] if isinstance(d,list) else d[x.replace('~1','/').replace('~0','~')]
    return d
def graph(d):
    m=Chem.RWMol()
    for a in d['atoms']:
        x=Chem.Atom(a['element']);x.SetFormalCharge(a.get('formalCharge',0));x.SetIsotope(a.get('isotope',0));x.SetNoImplicit(True);x.SetNumExplicitHs(a.get('implicitHydrogenCount',0));m.AddAtom(x)
    for b in d['bonds']:
        bt={1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']]
        m.AddBond(b['a'],b['b'],bt)
        if b['order']==1.5:
            m.GetAtomWithIdx(b['a']).SetIsAromatic(True);m.GetAtomWithIdx(b['b']).SetIsAromatic(True)
    m=m.GetMol();Chem.SanitizeMol(m);return m
def smi(m):return Chem.MolToSmiles(Chem.RemoveHs(m))
def checkmodel(path,expected_smiles,entry=None):
    d=read(path); title=path.name;m=graph(d);expected=Chem.MolFromSmiles(expected_smiles)
    ck(title+' graph',smi(m)==smi(expected),{'actual':smi(m),'expected':smi(expected)})
    ck(title+' formula',rdMolDescriptors.CalcMolFormula(m)==d['formula'],rdMolDescriptors.CalcMolFormula(m))
    ck(title+' zero-based atoms',[a['index'] for a in d['atoms']]==list(range(len(d['atoms']))))
    ck(title+' bond uniqueness',len({tuple(sorted((b['a'],b['b']))) for b in d['bonds']})==len(d['bonds']))
    for i,a in enumerate(d['atoms']):ck(title+f' finite atom {i}',all(math.isfinite(a[c]) for c in ['x','y','z']))
    for i,b in enumerate(d['bonds']):ck(title+f' endpoints {i}',0<=b['a']<len(d['atoms']) and 0<=b['b']<len(d['atoms']) and b['a']!=b['b'])
    for i,g in enumerate(d.get('functionalGroups',[])):
        inds=g['atomIndices']; bis=g.get('bondIndices',[])
        ck(title+f' group {i} atom indices',all(0<=n<len(d['atoms']) for n in inds))
        ck(title+f' group {i} bond indices',all(0<=n<len(d['bonds']) for n in bis))
        ck(title+f' group {i} endpoints',all(d['bonds'][j]['a'] in inds and d['bonds'][j]['b'] in inds for j in bis))
    if d['representation']=='2d':
        ck(title+' honest 2D',d['has3D'] is False and d['allowRotation'] is False and d['coordinateUnits']=='drawing units')
        ck(title+' planar drawing',all(a['z']==0 for a in d['atoms']))
    else:
        ck(title+' angstrom 3D',d['has3D'] is True and d['coordinateUnits']=='angstrom')
        lengths=[math.dist([d['atoms'][b['a']][c] for c in ['x','y','z']],[d['atoms'][b['b']][c] for c in ['x','y','z']]) for b in d['bonds']]
        ck(title+' broad physical bond envelope',all(.8<x<2.3 for x in lengths),[min(lengths),max(lengths)])
        ck(title+' no coincident atoms',all(math.dist([a[c] for c in ['x','y','z']],[b[c] for c in ['x','y','z']])>.6 for i,a in enumerate(d['atoms']) for b in d['atoms'][i+1:]))
    DETAILS.append({'model':str(path),'formula':rdMolDescriptors.CalcMolFormula(m),'canonical_smiles':smi(m),'components':len(Chem.GetMolFrags(m)),'atoms':len(d['atoms']),'bonds':len(d['bonds'])})
    return d,m

cm=read(P/'canonical-record-manifest.json');sa=read(P/'source-scientific-audit.json');ca=read(P/'canonical-records-audit.json')
for x in cm['original_sources']:bind(pathlib.Path(x['path']),x['sha256'])
for f,k in [('source-facts.json','source_facts_sha256'),('source-inventory.json','source_inventory_sha256'),('page-coverage.json','page_coverage_sha256')]:bind(P/f,cm[k])
records={}
for x in cm['records']:
    f=P/'canonical-drafts'/f"{x['record_id']}.json";bind(f,x['sha256']);records[x['record_id']]=read(f)
sm=read(V/'apparatus/scene-manifest.json');rv=read(V/'apparatus/render-validation.json')
bind(V/'apparatus'/sm['module'],sm['module_sha256']);bind(P/'canonical-record-manifest.json',sm['canonical_manifest_sha256']);bind(P/'canonical-records-audit.json',sm['canonical_audit_sha256']);bind(P/'source-facts.json',sm['source_facts_sha256'])
reader=next((P/'public-review-proposal').glob('norberg2004.json'));bind(reader,sm['reader_sha256'])
expected_ops={(r['record_id'],o['id']) for r in records.values() for o in r.get('operations',[])}
ck('All 47 operations have exactly one scene',len(sm['scenes'])==47 and {(s['record_id'],s['operation_id']) for s in sm['scenes']}==expected_ops)
for s in sm['scenes']:
    r=records[s['record_id']];o=ptr(r,s['operation_pointer']);ck(s['operation_id']+' pointer',o['id']==s['operation_id'])
    for k in ['inputs','outputs','retained_fraction','parameters','environment','stage']:ck(s['operation_id']+' exact '+k,s[k]==o.get(k))
    ck(s['operation_id']+' evidence',s['source_evidence']==o['evidence']);bind(V/'apparatus'/s['svg_file'],s['svg_sha256'])
for s in rv['scenes']:
    for typ in ['svg','png']:bind(V/'apparatus'/s[typ+'_file'],s[typ+'_sha256'])
for s in rv['contact_sheets']:bind(V/'apparatus'/s['file'],s['sha256'])
conf=read(V/'apparatus/scene-config.json')['configs']
ck('LiOH visible dropwise correction','dropwise' in json.dumps(conf['norberg-2004-surface-control-op-3']).lower())
ck('No D–F invented operation',not any(s['record_id']=='norberg-2004-films-d-f' for s in sm['scenes']))

reuse=read(V/'molecules/reuse-qualification.json');new=read(V/'molecules/registry-additions.json')['entries'];prod=read(V/'products/product-registry-additions.json')['entries']
entries={e['id']:e for e in new+prod}; expected={
'zinc-acetate-dihydrate':'[Zn+2].CC(=O)[O-].CC(=O)[O-].O.O',
'tetramethylammonium-hydroxide-pentahydrate':'C[N+](C)(C)C.[OH-].O.O.O.O.O',
'dodecylamine':'CCCCCCCCCCCCN','dimethyl-sulfoxide':'CS(C)=O','ethanol':'CCO','ethyl-acetate':'CCOC(C)=O','heptane':'CCCCCCC','toluene':'Cc1ccccc1','gu2004-nitrogen-reference':'N#N','topo':'CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC',
'norberg2004-manganese-acetate-tetrahydrate':'[Mn+2].CC(=O)[O-].CC(=O)[O-].O.O.O.O',
'norberg2004-manganese-nitrate-hydrate':'[Mn+2].[O-][N+](=O)[O-].[O-][N+](=O)[O-]',
'norberg2004-lithium-hydroxide':'[Li+].[OH-]','norberg2004-sodium-acetate':'[Na+].CC(=O)[O-]',
'norberg2004-topo-component':'CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC','norberg2004-nitrogen-reference':'N#N'}
models={}
for row in reuse['entries']:
    e=row['registry_entry'];entries[e['id']]=e
    for a in row['assets']:
        bind(a['private_path'],a['private_sha256']);bind(a['source_path'],a['source_sha256'])
        ck(e['id']+' unmodified copied asset '+a['key'],a['source_sha256']==a['private_sha256'])
        if a['key'].startswith('model'):
            models[(e['id'],a['key'])]=checkmodel(pathlib.Path(a['private_path']),expected[e['id']],e)
    prov=e.get('provenance',{})
    if prov.get('sourcePropertiesSha256'):
        for f,key in [(R/'quality-20260918/molecules/raw'/f"{e['id']}-properties.json",'sourcePropertiesSha256'),(R/'quality-20260918/molecules/raw'/f"{e['id']}-pubchem-2d.sdf",'source2dSha256')]:bind(f,prov[key])
        sdf=R/'quality-20260918/molecules/raw'/f"{e['id']}-pubchem-2d.sdf";mol=Chem.MolFromMolFile(str(sdf),removeHs=False)
        ck(e['id']+' retained primary SDF graph',smi(mol)==smi(Chem.MolFromSmiles(expected[e['id']])))
for e in new+prod:
    folder=V/('products' if e in prod else 'molecules')
    for key,h in e['assetHashes'].items():
        f=folder/e[key];bind(f,h)
        if key.startswith('model'):models[(e['id'],key)]=checkmodel(f,expected[e['id']],e)
    if e in prod:ck(e['id']+' no invented product coordinates',not e.get('model2dPath') and not e.get('model3dPath') and e['provenance']['measuredCoordinates'] is False)
for eid in expected:
    if (eid,'model2dPath') in models and (eid,'model3dPath') in models:ck(eid+' 2D/3D identical connectivity',smi(models[(eid,'model2dPath')][1])==smi(models[(eid,'model3dPath')][1]))
n2=models[('norberg2004-nitrogen-reference','model3dPath')][0]
ck('N2 corrected scalar distance',abs(math.dist([n2['atoms'][0][c] for c in ['x','y','z']],[n2['atoms'][1][c] for c in ['x','y','z']])-1.09768)<1e-8)
ck('N2 no current Gu storage metadata','Gu' not in json.dumps(n2) and 'stated for storage' not in json.dumps(n2))
for f in (V/'molecules/raw').glob('*'):bind(f)
ck('NIST ground-state evidence retained','1.09768' in (V/'molecules/raw/nitrogen-nist-web-tool-excerpt.txt').read_text(encoding='utf-8'))
bindings=read(V/'molecules/bindings-additions.json');cov=read(V/'molecules/material-slot-coverage.json')
expectedslots={(rid,m['id']) for rid,r in records.items() for m in r.get('materials',[])}
actualslots={(rid,mid) for rid,bs in bindings['recordBindings'].items() for mid in bs}
ck('All 73 material slots exactly once',len(expectedslots)==73 and actualslots==expectedslots and len(cov['slots'])==73)
for row in cov['slots']:
    rid=row['record_id'];mid=row['material_id'];r=records[rid];m=ptr(r,row['pointer']);eid=bindings['recordBindings'][rid][mid];n=bindings['bindingNotes'][rid][mid]
    ck(rid+'/'+mid+' exact pointer',m['id']==mid and row['registry_id']==eid and n['canonical_pointer']==row['pointer'])
    ck(rid+'/'+mid+' known reference',eid in entries)
    ck(rid+'/'+mid+' evidence',bool(n['source_evidence']) and n['source_evidence']==row['source_evidence'])
    ck(rid+'/'+mid+' pending consumption',n['binding_approved'] is False)
    bind(P/'canonical-drafts'/f'{rid}.json',bindings['sourceRecordSha256'][rid])
ck('No wrong base identity',all('tetrabutyl' not in x for x in entries))
ck('30 source/context cards',len(prod)==30)
for e in prod:
    if e['id']=='norberg2004-cleaned-final-colloids':ck('No complete coating claim','Complete coating' not in e['caption'])
pb=read(V/'products/product-reference-proposal.json')
ck('All product targets exist',all(r in records and e in entries for r,e in pb['recordBindings'].items()))

cp=read(V/'products/crystal-reference-proposal.json');unit=read(V/'products/models/norberg-undoped-zno-unit-cell.json');finite=read(V/'products/models/norberg-undoped-zno-finite-reference.json')
cif=V/'products/downloads/norberg-undoped-zno-cod9004178.cif';bind(cif,'dbc92c19b101d4fabb5594cc89f2a31629a0e8adab6539edd248c40c585649a1')
ck('COD reference cell and space group',unit['cell']=={'a':3.2494,'b':3.2494,'c':5.2038,'alpha':90.,'beta':90.,'gamma':120.} and unit['spaceGroupNumber']==186)
ck('Unit model honest current scope','Fu2007' not in json.dumps(unit) and unit['measured_sample_structure'] is False and unit['training_eligible'] is False)
ck('Four unit sites and 192 finite atoms',len(unit['atoms'])==4 and len(finite['atoms'])==192)
ck('No Mn or other invented elements',collections.Counter(a['element'] for a in finite['atoms'])=={'Zn':96,'O':96})
ck('Finite external not measured or training',finite['periodic'] is False and finite['training_eligible'] is False and finite['measured_sample_structure'] is False)
for a in unit['atoms']:
    xyz=[sum(a['fractional'][i]*unit['cellVectors'][i][j] for i in range(3)) for j in range(3)]
    ck('CIF fractional/cartesian '+a['site'],math.dist(xyz,[a[c] for c in ['x','y','z']])<1e-7)
    targetz=0 if a['element']=='Zn' else .3821
    ck('CIF symmetry-expanded '+a['site'],any(max(abs(a['fractional'][i]-f[i]) for i in range(3))<3e-5 for f in [[1/3,2/3,targetz],[2/3,1/3,(targetz+.5)%1]]))
pred=[]
for i in range(4):
 for j in range(4):
  for k in range(3):
   for a in unit['atoms']:
    xyz=[a[c]+sum([i,j,k][q]*unit['cellVectors'][q][t] for q in range(3)) for t,c in enumerate(['x','y','z'])];pred.append((a['element'],xyz))
centroid=[sum(xyz[t] for _,xyz in pred)/len(pred) for t in range(3)]
for n,((el,xyz),a) in enumerate(zip(pred,finite['atoms'])):
    ck(f'Finite exact centered translation {n}',el==a['element'] and math.dist([xyz[t]-centroid[t] for t in range(3)],[a[c] for c in ['x','y','z']])<1e-7)
    for j in a.get('bonds',[]):
        b=finite['atoms'][j];dist=math.dist([a[c] for c in ['x','y','z']],[b[c] for c in ['x','y','z']]);ck(f'Finite cutoff link {n}:{j}',a['element']!=b['element'] and 1.7<=dist<=2.2 and n in b['bonds'])
xyz=(V/'products/downloads/norberg-undoped-zno-finite-reference.xyz');bind(xyz);lines=xyz.read_text().splitlines();ck('XYZ 192 atoms',int(lines[0])==192 and len(lines[2:])==192)
for i,(line,a) in enumerate(zip(lines[2:],finite['atoms'])):
    x=line.split();ck(f'XYZ exact row {i}',x[0]==a['element'] and math.dist(list(map(float,x[1:4])),[a[c] for c in ['x','y','z']])<1e-5)
rp=read(V/'reference-preview-manifest.json')
for o in rp['outputs']:
    for k in ['svg','png']:bind(o[k],o[k+'_sha256'])
for c in rp['contacts']:bind(c['file'],c['sha256'])
for f in [V/'README.md',V/'author_reference_assets.py',V/'finalize_visual_package.py',V/'apparatus/author_norberg_scenes.py',V/'apparatus/module-template.mjs',V/'apparatus/diagram-selection.json']:bind(f)
report={'schema':'mattersyn.independent-visual-mechanical-checks.v1','auditor':'/root/backlog_eta','author':'/root/norberg2004_extract','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':CHECKS,'check_count':len(CHECKS),'failures':[x for x in CHECKS if not x['passed']],'model_details':DETAILS,'bound_files':BOUND,'status':'passed' if all(x['passed'] for x in CHECKS) else 'correction_required'}
(P/'visual-independent-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(CHECKS),'bound_files':len(BOUND),'model_files':len(DETAILS),'failures':report['failures']},ensure_ascii=False))
