"""Independent read-only Heo molecular checks; writes only this audit directory."""
from pathlib import Path
import json, hashlib, math, collections, ast, datetime
HERE=Path(__file__).resolve().parent
P=HERE.parent/'molecules'
H=P.parent.parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(label, ok, detail=None):
    checks.append({'check':label,'pass':bool(ok),'detail':detail})
F=read(P/'package-freeze.json')
for section in ['bound_files','bound_source_and_baseline_inputs']:
    for path,expected in F[section].items():
        exists=Path(path).is_file()
        actual=sha(path) if exists else None
        ck('freeze:'+section+':'+path,actual==expected,{'expected':expected,'actual':actual})
G=read(P/'generation-manifest.json')
for x in G['provenance_snapshots']:
    ck('immutable reuse snapshot:'+x['snapshot_path'],sha(P/x['snapshot_path'])==x['snapshot_sha256']==x['original_sha256'])
for rel,expected in G['files'].items():
    ck('generation:'+rel,sha(P/rel)==expected)
new=read(P/'registry-additions.json')
if isinstance(new,dict): new=new.get('entries',new)
if isinstance(new,dict): new=list(new.values())
ck('eight new entries',len(new)==8)
ck('eight unique identities',len({x['id'] for x in new})==8)
for e in new:
    ck(e['id']+' no measured coordinates',e.get('measuredCoordinates',e.get('provenance',{}).get('measuredCoordinates')) is False)
    ck(e['id']+' no new 3D',e.get('model3dPath') is None)
    ck(e['id']+' not approved',e.get('binding_approved') is False)
    ck(e['id']+' not published',e.get('published') is False)
    ck(e['id']+' not training',e.get('eligible_training') is False)
    ck(e['id']+' source hash',e['provenance']['sourceSha256']=='03e6f3be5375a0e2023a6850c1c6931904be8e3c85c37e0c30effdf6ecf73c01')
    for field,expected in e['assetHashes'].items():
        ck(e['id']+' asset '+field,sha(P/e[field])==expected)
    if e['id']!='heo2003-thallous-acetate':
        ck(e['id']+' symbolic no 2D coordinates',e['model2dPath'] is None)
expected_formulas={'heo2003-thallous-acetate':'C2H3O2Tl','identity-heo2003-na-x':'Na92Si100Al92O384','identity-heo2003-tl-x':'Tl92Si100Al92O384','identity-heo2003-in87-x':'In87Si100Al92O384','identity-heo2003-in66-x':'In66Si100Al92O384','identity-heo2003-indium-metal':'In','identity-heo2003-pyrex':None,'identity-heo2003-surface-residue':None}
for e in new: ck(e['id']+' source-qualified nominal formula',e['formula']==expected_formulas[e['id']])
reuse=read(P/'reused-references.json')['entries']
ck('three reused entries',len(reuse)==3)
for e in reuse:
    ck(e['id']+' unchanged baseline entry',e==read(P/'reference-base/entries'/f"{e['id']}.json"))
    for field,expected in e['assetHashes'].items():
        rel=Path(e[field]); dest=P/'reused'/rel
        ck(e['id']+' copied reference asset '+field,sha(dest)==expected)
models={}
for rel in ['models/heo2003-thallous-acetate-2d.json','reused/models/water-2d.json','reused/models/water-3d.json','reused/models/hydrogen-sulfide-2d.json','reused/models/hydrogen-sulfide-3d.json']:
    m=read(P/rel);models[rel]=m
    atoms=m['atoms'];bonds=m['bonds']; inds=[a['index'] for a in atoms]
    ck(rel+' indices contiguous',inds==list(range(len(atoms))))
    ck(rel+' finite coordinates',all(math.isfinite(a[k]) for a in atoms for k in ['x','y','z']))
    ck(rel+' valid bond graph',all(b['a'] in inds and b['b'] in inds and b['a']!=b['b'] and b['order'] in [1,1.0,2,2.0] for b in bonds))
    ck(rel+' no duplicate bond',len({tuple(sorted([b['a'],b['b']])) for b in bonds})==len(bonds))
    counts=collections.Counter(a['element'] for a in atoms);counts['H']+=sum(a.get('implicitHydrogenCount',0) for a in atoms)
    expected={'C':2,'H':3,'O':2,'Tl':1} if 'acetate' in rel else ({'H':2,'O':1} if 'water-' in rel else {'H':2,'S':1})
    counts=+counts
    ck(rel+' stoichiometry',dict(counts)==expected,dict(counts))
    ck(rel+' neutral total formal charge',sum(a.get('formalCharge',0) for a in atoms)==0)
    if 'reused/' in rel:
        ck(rel+' exact baseline model',sha(P/rel)==sha(P/'reference-base/models'/Path(rel).name))
    if m['representation']=='3d':
        cen=atoms[0];vectors=[[a[k]-cen[k] for k in ['x','y','z']] for a in atoms[1:]]
        lengths=[math.sqrt(sum(vv*vv for vv in v)) for v in vectors]
        angle=math.degrees(math.acos(sum(x*y for x,y in zip(*vectors))/(lengths[0]*lengths[1])))
        # Broad computed-conformer sanity bounds, explicitly not a gas-phase metrology validation.
        lo,hi=(.85,1.1) if 'water' in rel else (1.2,1.55)
        ck(rel+' nondegenerate computed geometry',all(lo<x<hi for x in lengths) and 80<angle<120,{'bond_lengths_angstrom':lengths,'bond_angle_degrees':angle,'basis':'broad sanity only; no measured-geometry claim'})
        ck(rel+' illustrative caption','computed' in (m.get('modelType','')+m.get('caption','')).lower() and ('not measured' in m.get('caption','') or 'not measured' in m.get('modelType','')))
a=models['models/heo2003-thallous-acetate-2d.json'];old=read(P/'reference-base/models/norberg2004-sodium-acetate-2d.json')
ck('acetate atoms retained exactly',a['atoms'][1:]==old['atoms'][1:])
ck('acetate bonds retained exactly',a['bonds']==old['bonds'])
ck('Tl formal +1 isolated',a['atoms'][0]['element']=='Tl' and a['atoms'][0]['formalCharge']==1 and all(0 not in [b['a'],b['b']] for b in a['bonds']))
ck('acetate -1 localized charge',sum(x['formalCharge'] for x in a['atoms'][1:])==-1)
ck('three explicit acetate bonds',len(a['bonds'])==3)
for group in a['functionalGroups']:
    ck('functional group indices:'+group['label'],all(i in range(5) for i in group['atomIndices']) and all(i in range(3) for i in group['bondIndices']))
ck('carboxylate indices',[g for g in a['functionalGroups'] if 'Carboxylate' in g['label']][0]['atomIndices']==[2,3,4])
for name,cid,formula,smi in [('water',962,'H2O','O'),('argon',23968,'Ar','[Ar]')]:
    raw=read(P/f'reference-base/raw/{name}-properties.json')['PropertyTable']['Properties'][0]
    ck(name+' retained primary identity',raw['CID']==cid and raw['MolecularFormula']==formula and raw['SMILES']==smi)
tree=ast.parse((P/'reference-base/audits/build_molecular_assets.py').read_text('utf-8-sig'))
defs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='definitions' for t in n.targets))
ck('H2S retained source-named SMILES',[d[2:4] for d in defs if d[0]=='hydrogen-sulfide']==[('S','H2S')])
comp=read(P/'component-view-proposal.json')
ck('two feed components',len(comp['components'])==2)
ck('feed component IDs',[c['registry_id'] for c in comp['components']]==['heo2003-thallous-acetate','water'])
ck('feed water grade not inferred','grade is unspecified' in comp['components'][1]['viewOverrides']['caption'])
ck('no stock preparation claimed',comp['source_stock_preparation_created'] is False)
ck('original source and SI distinct immutable hashes',F['bound_source_and_baseline_inputs'][str(Path('[local path redacted]'))]=='03e6f3be5375a0e2023a6850c1c6931904be8e3c85c37e0c30effdf6ecf73c01' and F['bound_source_and_baseline_inputs'][str(Path('[local path redacted]'))]=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6')
out={'schema':'mattersyn-independent-molecule-checks/1','reviewer':'/root/norberg2004_extract','author':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package_freeze_sha256':sha(P/'package-freeze.json'),'checks_count':len(checks),'failures':[c for c in checks if not c['pass']],'checks':checks,'note':'Independent arithmetic/graph/hash checks supplement actual manual source and all 11 preview inspection; these do not certify mounted browser or canonical bindings.'}
(HERE/'mechanical-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'check_count':len(checks),'failures':out['failures']},ensure_ascii=False,indent=2))
