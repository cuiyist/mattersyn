"""Independent, read-only candidate checks; outputs are confined to this audit directory."""
import json, hashlib, math, sys, itertools, collections
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0, r'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
A=Path(__file__).resolve().parent; M=A.parent/'molecules'; N=A.parents[1]
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
checks=[]; failures=[]; bound={}; graphs=[]
def ck(ok,label):
    checks.append(label)
    if not ok: failures.append(label)
def bind(p):
    p=Path(p); bound[str(p.resolve())]=sha(p); return p
def ptr(x,p):
    for k in p.split('/')[1:]:
        k=k.replace('~1','/').replace('~0','~'); x=x[int(k)] if isinstance(x,list) else x[k]
    return x
freeze=read(bind(M/'package-freeze.json'))
ck(sha(M/'package-freeze.json')=='79747e889a10786599a2ed4638cab8d3ba30f37df7f71f68bed990f42c0db848','exact author freeze')
for p,h in freeze['bound_files'].items():
    ck(Path(p).is_file(),f'exists:{p}')
    if Path(p).is_file():ck(sha(bind(p))==h,f'freeze hash:{p}')
for k in ['binding_approved','site_imported','published','browser_approved','training_approved']:ck(freeze[k] is False,f'pending {k}')
manifest=read(bind(N/'canonical-proposal/v2/record-manifest.json'))
records={}; rh={}
for v in manifest['records']:
    r=read(bind(v['path']));records[v['record_id']]=r;rh[v['record_id']]=sha(v['path']);ck(rh[v['record_id']]==v['sha256'],'canonical hash:'+v['record_id'])
entries=read(M/'registry-additions.json')['entries']; byid={e['id']:e for e in entries}
slots=read(M/'material-slot-map.json')['slots']; stocks=read(M/'stock-component-map.json')['stocks']; bindings=read(M/'bindings-proposal.json'); contexts=read(M/'solution-components-proposal.json')['contexts']
ck(len(entries)==29 and len(byid)==29,'29 distinct entries');ck(len(slots)==64,'64 slots');ck(len(stocks)==5,'5 stocks')
expected={(rid,m['id']) for rid,r in records.items() for m in r['materials']}
ck(expected=={(s['record_id'],s['material_id']) for s in slots},'complete exact material slot set')
def quantities(s,rid):
    for l in s:
        ck(l['record_id']==rid,'quantity record');q=ptr(records[rid],l['json_pointer']);ck(q==l['quantity'],'exact quantity:'+rid+l['json_pointer'])
        if 'operation_id' in l:
            ck(ptr(records[rid],'/'.join(l['json_pointer'].split('/')[:3]))['id']==l['operation_id'],'quantity operation scope')
for s in slots:
    rid=s['record_id'];mid=s['material_id'];e=byid[s['registry_id']]
    ck(s['canonical_record_sha256']==rh[rid],'slot canonical hash:'+rid+'/'+mid)
    ck(ptr(records[rid],s['json_pointer'])==s['canonical_identity'],'exact slot:'+rid+'/'+mid)
    ck(s['canonical_identity']['id']==mid,'slot id')
    ck(e['provenance']['sourceMaterialId']==mid,'entry identity join')
    ck(s['entry_sha256']==jsha(e),'entry structural hash')
    ck(bindings['recordBindings'][rid][mid]==e['id'],'runtime binding')
    ck(bindings['bindingNotes'][rid][mid]==s,'binding notes exact')
    ck(s['binding_approved'] is False,'slot not self-approved')
    ck(set(s['viewOverrides'])<=set(['name','caption','limitations']),'safe scoped override keys')
    quantities(s['quantity_links'],rid)
stockset={(rid,s['id']) for rid,r in records.items() for s in r.get('stocks',[])}
ck(stockset=={(s['record_id'],s['stock_id']) for s in stocks},'complete stock set')
cc=0
for s in stocks:
    rid=s['record_id'];raw=ptr(records[rid],s['json_pointer']);ck(raw['id']==s['stock_id'],'stock id')
    ck(s['canonical_record_sha256']==rh[rid],'stock canonical hash')
    for k in ['scope','concentrations','evidence']:ck(s[k]==raw[k],'stock '+k)
    ck(len(s['components'])==len(raw['components']),'stock component count')
    ctx=next(c for c in contexts if c['record_id']==rid and c['id']=='morrison2017-'+s['stock_id'])
    ck(len(ctx['components'])==len(s['components']),'runtime component count')
    for c,rt in zip(s['components'],ctx['components']):
        cc+=1;rc=ptr(records[rid],c['json_pointer']);mat=ptr(records[rid],c['material_json_pointer'])
        ck(rc['material_id']==mat['id']==c['material_id'],'component identity exact')
        ck(rc['quantities']==c['source_quantities'],'component quantities exact')
        ck(c['registry_id']==rt['registry_id']==bindings['recordBindings'][rid][c['material_id']],'stock runtime entry')
        quantities(c['quantity_links'],rid)
    quantities(s['solution_quantity_links'],rid)
ck(cc==10,'10 components')
expected_graph={
 'cdcl2':'[Cl-].[Cd+2].[Cl-]', 'water':'O','ethanol':'CCO','thf':'O1CCCC1',
 'dmso-d6':'[2H]C([2H])([2H])S(=O)C([2H])([2H])[2H]','dmso':'CS(=O)C','toluene':'c1ccccc1C',
 'dmf':'O=CN(C)C','methanol':'CO','chloroform':'C(Cl)(Cl)Cl',
 'nh4ptc':'[NH4+].c1ccccc1NC(=S)[S-]', 'thf-d8':'O1C([2H])([2H])C([2H])([2H])C([2H])([2H])C1([2H])[2H]',
 'n-octylamine':'NCCCCCCCC','aniline':'c1ccccc1N','phenylisothiocyanate':'c1ccccc1N=C=S',
 'carbon-disulfide':'S=C=S','diphenylthiourea':'c1ccccc1NC(=S)Nc2ccccc2','dichloromethane':'ClCCl'}
def smiles(model):
    rw=Chem.RWMol()
    for a in model['atoms']:
        at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0));at.SetNoImplicit(True);at.SetNumExplicitHs(a.get('implicitHydrogenCount',0));rw.AddAtom(at)
    types={1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}
    for b in model['bonds']:rw.AddBond(b['a'],b['b'],types[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);return Chem.MolToSmiles(Chem.RemoveHs(mol)),mol
for e in entries:
    mid=e['provenance']['sourceMaterialId'];ck(e['provenance']['measuredCoordinates'] is False,'not measured '+mid)
    ck(e['binding_approved'] is False and e['eligible_training'] is False and e['published'] is False,'entry gates '+mid)
    for k,h in e['assetHashes'].items():ck(sha(M/e[k])==h,'asset hash '+mid+k)
    if mid not in expected_graph:
        ck(e['depictionKind']=='symbolic_context' and not e.get('model2dPath') and not e.get('model3dPath'),'unresolved remains symbolic '+mid);continue
    exp=Chem.MolToSmiles(Chem.MolFromSmiles(expected_graph[mid]))
    for key in ['model2dPath','model3dPath']:
        if not e.get(key):continue
        model=read(M/e[key]);g,mol=smiles(model);ck(g==exp,'named connectivity '+mid+' '+key)
        ats=model['atoms'];bs=model['bonds'];ck([a['index'] for a in ats]==list(range(len(ats))),'zero based '+mid+key)
        for a in ats:
            for d in ['x','y','z']:ck(isinstance(a[d],(int,float)) and math.isfinite(a[d]),'finite coordinate')
        counts=collections.Counter()
        for a in ats:counts['D' if a['element']=='H' and a.get('isotope')==2 else a['element']]+=1;counts['H']+=a.get('implicitHydrogenCount',0)
        formula=''.join(el+(str(counts[el]) if counts[el]!=1 else '') for el in sorted([x for x in counts if counts[x]],key=lambda x:(0 if x=='C' else 1 if x=='H' else 2,x)))
        ck(formula==e['formula'],'element/isotope formula '+mid+key)
        fg=model.get('functionalGroups',[])
        for gr in fg:
            ai=gr.get('atomIndices',[]);bi=gr.get('bondIndices',[])
            ck(all(type(i)==int and 0<=i<len(ats) for i in ai),'group atom indices')
            ck(all(type(i)==int and 0<=i<len(bs) for i in bi),'group bond indices')
            ck(all(bs[i]['a'] in ai and bs[i]['b'] in ai for i in bi),'group bonds contained')
        if key=='model2dPath':ck(e['functionalGroups']==fg,'entry groups equal 2d')
        lengths=[];minimum=999
        for i,j in itertools.combinations(range(len(ats)),2):
            d=math.dist([ats[i][x] for x in ['x','y','z']],[ats[j][x] for x in ['x','y','z']]);minimum=min(minimum,d);ck(d>0.15,'no coincident atoms')
        if key=='model3dPath':
            ck(model['coordinateUnits']=='angstrom','3d units');ck(model.get('has3D') is True,'3d enabled')
            for b in bs:
                a,c=ats[b['a']],ats[b['b']];d=math.dist([a[x] for x in ['x','y','z']],[c[x] for x in ['x','y','z']]);lengths.append(d)
                ck(0.85<d<2.05,'plausible free molecule bond '+mid)
            ck('not a measured' in model['caption'],'3d measurement caveat '+mid)
        rid=e['provenance'].get('retainedRegistryId')
        if rid:
            old=read(M/'reference-snapshots/models'/f'{rid}-{ "2d" if key=="model2dPath" else "3d"}.json')
            for f in ['atoms','bonds','functionalGroups']:ck(model.get(f)==old.get(f),'cached '+f+' unchanged '+mid+key)
        graphs.append({'material':mid,'representation':key,'canonical_smiles':g,'formula':formula,'atoms':len(ats),'bonds':len(bs),'groups':len(fg),'minimum_pair_distance':minimum,'bond_length_range':([min(lengths),max(lengths)] if lengths else None)})
snap=read(M/'reference-snapshots/manifest.json')
for s in snap['snapshots']:ck(sha(M/s['snapshot_path'])==s['sha256'],'retained provenance artifact '+s['snapshot_path'])
allow=read(M/'public-asset-proposal.json')['relative_asset_files']
ck(len(allow)==56,'56 public assets')
expectedfiles={e[k] for e in entries for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
ck(set(allow)==expectedfiles,'public allowlist exact registry asset set')
for p,h in allow.items():
    ck(sha(M/p)==h,'public hash '+p);ck(p.startswith(('svg/','models/')) and Path(p).suffix in ['.svg','.json'] and '..' not in Path(p).parts,'public path scope '+p)
result={'status':'passed' if not failures else 'findings','check_count':len(checks),'failures':failures,'counts':{'entries':29,'slots':64,'stocks':5,'components':cc,'models':len(graphs),'public_assets':len(allow)},'graphs':graphs,'bound_files':bound}
(A/'mechanical-checks.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','check_count','failures','counts']},ensure_ascii=False))
