"""Independent read-only examination of the frozen Lian molecular proposal."""
from pathlib import Path
import json, hashlib, math, sys, re
from collections import Counter
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '[local path redacted]')
sys.path.insert(0, '[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

A=Path(__file__).resolve().parent
L=A.parent.parent
M=L/'visuals/molecules'
checks=[]; bound={}; details={}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p); bound[p.as_posix()]=sha(p)
    return json.loads(p.read_text(encoding='utf-8'))
def ck(name, value): checks.append({'check':name,'passed':bool(value)})
def ptr(d,p):
    for key in p.strip('/').split('/'):
        key=key.replace('~1','/').replace('~0','~');d=d[int(key)] if isinstance(d,list) else d[key]
    return d
def objsha(d): return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
freeze=read(M/'package-freeze.json')
ck('exact-author-freeze',sha(M/'package-freeze.json')=='4630547b7d44afd66a2c9ca46db39c9e90c566fbe63f6cf149c81a9ce1652321')
for fn,h in freeze['bound_files'].items():
    p=Path(fn);ck('frozen-file:'+p.name,p.is_file() and sha(p)==h)
    if p.is_file(): bound[p.as_posix()]=sha(p)
reg=read(M/'registry-additions.json'); entries={x['id']:x for x in reg['entries']}
slots=read(M/'material-slot-map.json')['slots'];stocks=read(M/'stock-component-map.json')['stocks']
bindings=read(M/'bindings-proposal.json'); solutions=read(M/'solution-components-proposal.json')['contexts']
rm=read(L/'canonical-proposal/v1/record-manifest.json')
records={};recordhash={}
for x in rm['records']:
    records[x['record_id']]=read(x['path']);recordhash[x['record_id']]=sha(x['path'])
    ck('canonical-hash:'+x['record_id'],recordhash[x['record_id']]==x['sha256'])
ck('fifteen-unique-identities',len(entries)==len(reg['entries'])==15)
expectedslots={(rid,m['id']) for rid,r in records.items() for m in r['materials']}
ck('all-and-only-45-slots',len(slots)==45 and {(x['record_id'],x['material_id']) for x in slots}==expectedslots)
ck('bindings-no-extra-records',set(bindings['recordBindings'])=={rid for rid,mid in expectedslots})
for s in slots:
    label=s['record_id']+'/'+s['material_id'];rid=s['record_id'];mid=s['material_id'];e=entries[s['registry_id']]
    ck('slot-exact:'+label,ptr(records[rid],s['json_pointer'])==s['canonical_identity'])
    ck('slot-hash:'+label,s['canonical_record_sha256']==recordhash[rid])
    ck('entry-hash:'+label,s['entry_sha256']==objsha(e))
    ck('binding-exact:'+label,bindings['recordBindings'][rid][mid]==s['registry_id'])
    ck('binding-note-exact:'+label,bindings['bindingNotes'][rid][mid]==s)
    ck('scoped-name:'+label,s['canonical_identity']['name'] in s['viewOverrides']['caption'])
    ck('slot-unapproved:'+label,s['binding_approved'] is False)
    ck('formula-scope:'+label,e['provenance']['canonicalIdentityFormula']==s['canonical_identity']['formula'])
    ck('identity-id-scope:'+label,s['registry_id']=='lian2021-'+mid+'-reference')
    ck('no-extra-slot:'+label,set(bindings['recordBindings'][rid])=={m['id'] for m in records[rid]['materials']})

quantrefs=[]
def walk(x):
    if isinstance(x,dict):
        if all(k in x for k in ('record_id','json_pointer','quantity')):
            quantrefs.append(x);ck('quantity:'+x['record_id']+x['json_pointer'],ptr(records[x['record_id']],x['json_pointer'])==x['quantity'])
        for v in x.values(): walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
walk(slots);walk(stocks)
ck('all-sixty-quantity-context-references',len(quantrefs)==60)
expectedstocks={(rid,s['id']) for rid,r in records.items() for s in r.get('stocks',[])}
ck('all-five-stocks',len(stocks)==5 and {(s['record_id'],s['stock_id']) for s in stocks}==expectedstocks)
ck('fourteen-components',sum(len(s['components']) for s in stocks)==14)
for s in stocks:
    rid=s['record_id'];label=rid+'/'+s['stock_id'];c=ptr(records[rid],s['json_pointer'])
    ck('stock-hash:'+label,s['canonical_record_sha256']==recordhash[rid])
    ck('stock-component-count:'+label,len(s['components'])==len(c['components']))
    for k in ['concentrations','scope','evidence']: ck('stock-'+k+':'+label,s[k]==c[k])
    matching=[x for x in solutions if x['record_id']==rid and x['id']=='lian2021-'+s['stock_id']]
    ck('one-solution-context:'+label,len(matching)==1)
    sol=matching[0]
    ck('solution-component-count:'+label,len(sol['components'])==len(s['components']))
    for i,x in enumerate(s['components']):
        cc=ptr(records[rid],x['json_pointer']);mm=ptr(records[rid],x['material_json_pointer'])
        ck('component-id:'+label+str(i),cc['material_id']==x['material_id']==mm['id'])
        ck('component-role:'+label+str(i),cc['role']==x['role'])
        ck('component-source-quantities:'+label+str(i),cc['quantities']==x['source_quantities'])
        ck('component-binding:'+label+str(i),bindings['recordBindings'][rid][x['material_id']]==x['registry_id'])
        ck('selector-binding:'+label+str(i),all(sol['components'][i][k]==x[k] for k in ['material_id','registry_id','role']))
        ck('component-unapproved:'+label+str(i),x['binding_approved'] is False and sol['binding_approved'] is False)
    ck('stock-no-inferred-concentration:'+label,s['concentrations']=={})

def buildmol(d):
    rw=Chem.RWMol()
    for a in d['atoms']:
        at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0));rw.AddAtom(at)
    for b in d['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);conf=Chem.Conformer(len(d['atoms']));conf.Set3D(d.get('coordinateUnits')=='angstrom')
    for i,a in enumerate(d['atoms']):conf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
    mol.AddConformer(conf)
    if conf.Is3D():Chem.AssignStereochemistryFrom3D(mol)
    else:Chem.AssignStereochemistry(mol,cleanIt=True,force=True)
    return mol
models={};modelmols={}
expectedformula={'tpa-cl':'C12H28ClN','sbcl3':'Cl3Sb','dmf':'C3H7NO','toluene':'C7H8','oleic-acid':'C18H34O2','nitrogen':'N2','liquid-nitrogen':'N2'}
for eid,e in entries.items():
    ck('entry-unapproved:'+eid,e.get('binding_approved') is False)
    ck('entry-source:'+eid,e['provenance']['sourceDoi']=='10.1021/acsami.1c18038')
    for dim in ['2d','3d']:
        rel=e.get('model'+dim+'Path')
        if not rel: continue
        d=read(M/rel);models[(eid,dim)]=d;mol=buildmol(d);modelmols[(eid,dim)]=mol
        mid=eid.removeprefix('lian2021-').removesuffix('-reference')
        ck('formula:'+rel,rdMolDescriptors.CalcMolFormula(mol)==expectedformula[mid]==d['formula']==e['formula'])
        ck('net-charge:'+rel,Chem.GetFormalCharge(mol)==0)
        ck('coordinate-units:'+rel,d['coordinateUnits']==('angstrom' if dim=='3d' else 'arbitrary drawing units'))
        ck('atom-indices:'+rel,[a['index'] for a in d['atoms']]==list(range(len(d['atoms']))))
        for i,a in enumerate(d['atoms']):ck('finite:'+rel+str(i),all(math.isfinite(a[k]) for k in ['x','y','z']))
        seen=set()
        for i,b in enumerate(d['bonds']):
            pair=tuple(sorted((b['a'],b['b'])));ck('bond-index:'+rel+str(i),b['a']!=b['b'] and min(pair)>=0 and max(pair)<len(d['atoms']) and pair not in seen);seen.add(pair)
            if dim=='3d':ck('bond-distance:'+rel+str(i),0.7<math.dist([d['atoms'][b['a']][k] for k in ['x','y','z']],[d['atoms'][b['b']][k] for k in ['x','y','z']])<2.1)
        for g in d.get('functionalGroups',[]):
            ck('group-indices:'+rel+g['label'],all(0<=a<len(d['atoms']) for a in g['atomIndices']) and all(0<=b<len(d['bonds']) for b in g.get('bondIndices',[])))
            for bi in g.get('bondIndices',[]):ck('group-bond-membership:'+rel+g['label']+str(bi),d['bonds'][bi]['a'] in g['atomIndices'] and d['bonds'][bi]['b'] in g['atomIndices'])
        if dim=='2d':ck('2d-no-rotation:'+rel,d['has3D'] is False and d['allowRotation'] is False and all(a['z']==0 for a in d['atoms']))
        details[rel]={'formula':rdMolDescriptors.CalcMolFormula(mol),'atoms':mol.GetNumAtoms(),'bonds':mol.GetNumBonds(),'smiles':Chem.MolToSmiles(Chem.RemoveHs(mol))}
    if not e.get('model2dPath'):ck('symbol-no-coordinates:'+eid,not e.get('model3dPath') and e['depictionKind']!='molecule')
ck('seven-2d-five-3d-models',sum(k[1]=='2d' for k in models)==7 and sum(k[1]=='3d' for k in models)==5)
tpa=modelmols[('lian2021-tpa-cl-reference','2d')]
ck('tpa-exact-n-propyl-connectivity',Chem.MolToSmiles(tpa)==Chem.MolToSmiles(Chem.MolFromSmiles('CCC[N+](CCC)(CCC)CCC.[Cl-]')))
sb=modelmols[('lian2021-sbcl3-reference','2d')]
ck('sb-formal-ions-no-coordination',sb.GetNumBonds()==0 and sorted(a.GetFormalCharge() for a in sb.GetAtoms())==[-1,-1,-1,3])
qual=read(M/'reference-qualification.json')
for q in qual['qualifications']:
    eid='lian2021-'+q['material_id']+'-reference';cached=q['cached_id']
    original=read(M/'reference-snapshots/models'/f'{cached}-3d.json');d=models[(eid,'3d')]
    ck('unchanged-3d-arrays:'+eid,all(d[k]==original[k] for k in ['atoms','bonds']))
    ck('reference-model-hash:'+eid,sha(M/'reference-snapshots/models'/f'{cached}-3d.json')==q['retainedModel3dSha256'])
    for g in d.get('functionalGroups',[]):details.setdefault('functional_groups',{})[eid+'-'+g['label']]=[d['atoms'][i]['element'] for i in g['atomIndices']]
for a in qual['retained_primary_artifacts']:ck('primary-artifact:'+a['snapshot_path'],sha(M/a['snapshot_path'])==a['sha256'])
for mid,cached in [('dmf','dimethylformamide-computed-illustrative-3d.sdf'),('toluene','toluene-pubchem-1140-3d.sdf'),('oleic-acid','oleic-acid-pubchem-445639-3d.sdf')]:
    p=M/'reference-snapshots/primary'/mid/cached;rawmol=next(iter(Chem.SDMolSupplier(str(p),removeHs=False)));eid='lian2021-'+mid+'-reference';mol=modelmols[(eid,'3d')];d=models[(eid,'3d')]
    ck('raw-sdf-identity:'+mid,Chem.MolToSmiles(Chem.RemoveHs(rawmol))==Chem.MolToSmiles(Chem.RemoveHs(mol)))
    ck('raw-sdf-atom-count:'+mid,rawmol.GetNumAtoms()==len(d['atoms']))
    for i,a in enumerate(d['atoms']):
        pos=rawmol.GetConformer().GetAtomPosition(i)
        ck('raw-sdf-coordinate:'+mid+str(i),a['element']==rawmol.GetAtomWithIdx(i).GetSymbol() and max(abs(v-a[k]) for k,v in zip(['x','y','z'],[pos.x,pos.y,pos.z]))<0.000051)
oa=modelmols[('lian2021-oleic-acid-reference','3d')]
ccdouble=[b for b in oa.GetBonds() if b.GetBondType()==Chem.BondType.DOUBLE and b.GetBeginAtom().GetSymbol()==b.GetEndAtom().GetSymbol()=='C']
ck('oa-one-Z-carbon-double-bond',len(ccdouble)==1 and str(ccdouble[0].GetStereo())=='STEREOZ')
for mid in ['nitrogen','liquid-nitrogen']:
    d=models[('lian2021-'+mid+'-reference','3d')]
    ck('NIST-distance:'+mid,abs(math.dist([d['atoms'][0][k] for k in ['x','y','z']],[d['atoms'][1][k] for k in ['x','y','z']])-1.09768)<1e-12)
    ck('N2-triple:'+mid,len(d['bonds'])==1 and d['bonds'][0]['order']==3)

allow=read(M/'public-asset-proposal.json')['relative_asset_files'];expectedassets={e[k] for e in entries.values() for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
ck('public-exact-27-assets',len(allow)==27 and set(allow)==expectedassets)
for rel,h in allow.items():
    p=M/rel;raw=p.read_text(encoding='utf-8');ck('public-asset-hash:'+rel,sha(p)==h)
    ck('public-no-private-source-payload:'+rel,p.suffix in ['.json','.svg'] and not any(s in raw for s in ['C:/Users/','C:\\Users\\','firstPagePreviewPrivate','complete-source-payloads']))
    if p.suffix=='.svg':ck('no-active-svg:'+rel,not re.search(r'<script|onload=|onerror=|<foreignObject',raw,re.I))
for x in [reg,bindings,read(M/'solution-components-proposal.json')]:ck('no-premature-approval',x['binding_approved'] is False)
details['quantity_reference_count']=len(quantrefs)
result={'schema':'mattersyn-independent-molecular-checks/1','generated_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(x['passed'] for x in checks) else 'findings','checks':checks,'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'details':details,'bound_files':bound}
(A/'mechanical-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':result['failures']},ensure_ascii=False))
