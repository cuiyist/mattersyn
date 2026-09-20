"""Independent checks of frozen Ghosh references, canonical slots and stocks.

Only audit outputs are written. No author builder or validator is executed.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, math, re, sys
sys.dont_write_bytecode = True
sys.path.insert(0, '[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

A = Path(__file__).resolve().parent
G = A.parent.parent
M = G / 'visuals/molecules'
checks, bound, details = [], {}, {}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p = Path(p); bound[str(p)] = sha(p)
    return json.loads(p.read_text(encoding='utf-8'))
def ck(label, value): checks.append({'check': label, 'passed': bool(value)})
def objsha(x): return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def ptr(x, p):
    for k in p.strip('/').split('/'):
        k = k.replace('~1', '/').replace('~0', '~'); x = x[int(k)] if isinstance(x, list) else x[k]
    return x
freeze = read(M/'package-freeze.json')
ck('exact original freeze', sha(M/'package-freeze.json') == 'a0a288171e559c3ebf2664cda6d312e1a9b0992888dc4435dd1cd51e860c3391')
for fn, digest in freeze['bound_files'].items():
    p = Path(fn); ck('frozen bytes '+fn, p.is_file() and sha(p) == digest)
    if p.is_file(): bound[str(p)] = sha(p)
reg = read(M/'registry-additions.json'); entries = {x['id']:x for x in reg['entries']}
slots = read(M/'material-slot-map.json')['slots']
stocks = read(M/'stock-component-map.json')['stocks']
bindings = read(M/'bindings-proposal.json')
solutions = read(M/'solution-components-proposal.json')['contexts']
rm = read(G/'canonical-proposal/v1/record-manifest.json')
records, hashes = {}, {}
for row in rm['records']:
    records[row['record_id']] = read(row['path']); hashes[row['record_id']] = sha(row['path'])
    ck('canonical exact '+row['record_id'], hashes[row['record_id']] == row['sha256'])
expected_slots = {(rid,m['id']) for rid,r in records.items() for m in r['materials']}
ck('25 unique entries', len(entries) == len(reg['entries']) == 25)
ck('88 unique complete material slots', len(slots) == len(expected_slots) == 88 and {(x['record_id'],x['material_id']) for x in slots} == expected_slots)
ck('binding record set', set(bindings['recordBindings']) == {x[0] for x in expected_slots})
for x in slots:
    rid, mid = x['record_id'], x['material_id']; label = rid+'/'+mid; e = entries[x['registry_id']]
    ck('slot snapshot '+label, ptr(records[rid],x['json_pointer']) == x['canonical_identity'])
    ck('record binding hash '+label, hashes[rid] == x['canonical_record_sha256'])
    ck('entry hash '+label, objsha(e) == x['entry_sha256'])
    ck('all and only record materials '+label, set(bindings['recordBindings'][rid]) == {m['id'] for m in records[rid]['materials']})
    ck('entry map '+label, bindings['recordBindings'][rid][mid] == x['registry_id'] == 'ghosh2012-'+mid+'-reference')
    ck('binding note exact '+label, bindings['bindingNotes'][rid][mid] == x)
    ck('canonical identity formula scope '+label, e['provenance']['canonicalIdentityFormula'] == x['canonical_identity']['formula'])
    ck('approval false '+label, x['binding_approved'] is False)
    ck('source name visible '+label, x['canonical_identity']['name'] in x['viewOverrides']['caption'])
    ck('limitation preserved '+label, all(z in x['viewOverrides']['limitations'] for z in e['limitations'] if not z.startswith('Symbolic identity only')))
quantities=[]
def walk(x):
    if isinstance(x,dict):
        if {'record_id','json_pointer','quantity'} <= x.keys():
            quantities.append(x)
            ck('exact quantity '+x['record_id']+x['json_pointer'], ptr(records[x['record_id']],x['json_pointer']) == x['quantity'])
        for v in x.values(): walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
walk(slots);walk(stocks)
ck('59 typed reference occurrences', len(quantities)==59)
expected_stocks={(rid,x['id']) for rid,r in records.items() for x in r.get('stocks',[])}
ck('all three stocks', len(stocks)==3 and {(x['record_id'],x['stock_id']) for x in stocks}==expected_stocks)
ck('all eight components', sum(len(x['components']) for x in stocks)==8)
roles={'top-se':'named_precursor_solute','ola':'ligand_cosolvent','ode':'solvent','sulfur':'named_precursor_solute','od':'solvent','cd-oleate':'named_precursor_solute','oa':'free_acid_ligand_component'}
for x in stocks:
    rid=x['record_id']; label=rid+'/'+x['stock_id']; orig=ptr(records[rid],x['json_pointer'])
    ck('stock record hash '+label, hashes[rid]==x['canonical_record_sha256'])
    for k in ['concentrations','scope','evidence']:ck('stock '+k+' '+label,x[k]==orig[k])
    ck('stock component count '+label,len(x['components'])==len(orig['components']))
    found=[s for s in solutions if s['record_id']==rid and s['id']=='ghosh2012-'+x['stock_id']]
    ck('one exact solution '+label,len(found)==1)
    sol=found[0]
    ck('selector length '+label,len(sol['components'])==len(x['components']))
    ck('stock unpublished '+label,x['binding_approved'] is False and sol['binding_approved'] is False)
    ck('whole-charge qualification '+label,'not an additional charge event' in sol['scope'])
    for i,c in enumerate(x['components']):
        origc=ptr(records[rid],c['json_pointer']); mat=ptr(records[rid],c['material_json_pointer'])
        ck('component exact identity '+label+str(i),origc['material_id']==c['material_id']==mat['id'])
        ck('component quantities '+label+str(i),origc['quantities']==c['source_quantities'])
        ck('component role '+label+str(i),c['role']==roles[c['material_id']])
        ck('component registry '+label+str(i),c['registry_id']==bindings['recordBindings'][rid][c['material_id']])
        ck('selector exact '+label+str(i),all(sol['components'][i][k]==c[k] for k in ['material_id','registry_id','role']))
        ck('component approval false '+label+str(i),c['binding_approved'] is False)
    if x['stock_id']=='top-se-injection':ck('injection concentration not inferred',x['concentrations']=={})
    else:ck('shell stock 0.2M '+label,x['concentrations']['reported_concentration']['value']==0.2 and x['concentrations']['reported_concentration']['unit']=='mol/L')

expected_smiles={
 'oa':'CCCCCCCC/C=C\\CCCCCCCC(=O)O','ode':'C=CCCCCCCCCCCCCCCCC','od':'CCCCCCCCCCCCCCCCCC',
 'ola':'CCCCCCCC/C=C\\CCCCCCCCN','doa':'CCCCCCCCNCCCCCCCC','top':'CCCCCCCCP(CCCCCCCC)CCCCCCCC',
 'topo':'CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC','top-se':'CCCCCCCCP(=[Se])(CCCCCCCC)CCCCCCCC',
 'ethanol':'CCO','hexane':'CCCCCC','toluene':'Cc1ccccc1','acetone':'CC(=O)C','liquid-nitrogen':'N#N'}
models,mols={},{}
def build_mol(d):
    rw=Chem.RWMol()
    for a in d['atoms']:
        atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
    for b in d['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);conf=Chem.Conformer(len(d['atoms']));conf.Set3D(d['coordinateUnits']=='angstrom')
    for i,a in enumerate(d['atoms']):conf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
    mol.AddConformer(conf)
    if conf.Is3D():Chem.AssignStereochemistryFrom3D(mol)
    return mol
for eid,e in entries.items():
    mid=e['provenance']['sourceMaterialId']
    ck('source-specific identity '+eid,e['provenance']['sourceDoi']=='10.1021/ja212032q')
    ck('reference not measured '+eid,e['provenance']['measuredCoordinates'] is False)
    ck('saved flags false '+eid,not any(e[k] for k in ['binding_approved','published','eligible_training']))
    for dim in ['2d','3d']:
        rel=e.get('model'+dim+'Path')
        if not rel:continue
        d=read(M/rel);models[(mid,dim)]=d;mol=build_mol(d);mols[(mid,dim)]=mol
        ref=Chem.MolFromSmiles(expected_smiles[mid])
        ck('formula '+rel,rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(ref)==d['formula']==e['formula'])
        ck('identity graph '+rel,Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False)==Chem.MolToSmiles(ref,isomericSmiles=False))
        ck('neutral free identity '+rel,Chem.GetFormalCharge(mol)==0)
        ck('atom indices '+rel,[a['index'] for a in d['atoms']]==list(range(len(d['atoms']))))
        ck('units '+rel,d['coordinateUnits']==('angstrom' if dim=='3d' else 'arbitrary drawing units'))
        pairs=set()
        for i,a in enumerate(d['atoms']):ck('finite atom '+rel+str(i),all(math.isfinite(a[k]) for k in ['x','y','z']))
        for i,b in enumerate(d['bonds']):
            pair=tuple(sorted((b['a'],b['b'])));ck('unique bond '+rel+str(i),0<=min(pair)<max(pair)<len(d['atoms']) and pair not in pairs);pairs.add(pair)
            if dim=='3d':ck('plausible bond length '+rel+str(i),0.7<math.dist([d['atoms'][b['a']][k] for k in ['x','y','z']],[d['atoms'][b['b']][k] for k in ['x','y','z']])<2.3)
        for group in d.get('functionalGroups',[]):
            label=rel+group['label'];ck('group indices '+label,all(0<=i<len(d['atoms']) for i in group['atomIndices']) and all(0<=i<len(d['bonds']) for i in group.get('bondIndices',[])))
            for i in group.get('bondIndices',[]):ck('group endpoints '+label+str(i),d['bonds'][i]['a'] in group['atomIndices'] and d['bonds'][i]['b'] in group['atomIndices'])
        if dim=='2d':ck('no 3D claim '+rel,d['has3D'] is False and d['allowRotation'] is False and all(a['z']==0 for a in d['atoms']))
        details[rel]={'formula':rdMolDescriptors.CalcMolFormula(mol),'atoms':len(d['atoms']),'bonds':len(d['bonds']),'graph':Chem.MolToSmiles(Chem.RemoveHs(mol)), 'functional_groups':d.get('functionalGroups',[])}
    if not e.get('model2dPath'):ck('symbolic no model '+eid,not e.get('model3dPath') and e['depictionKind']!='molecule')
ck('13 2D and 10 retained 3D models',sum(k[1]=='2d' for k in models)==13 and sum(k[1]=='3d' for k in models)==10)
ck('12 symbols',sum(not e.get('model2dPath') for e in entries.values())==12)
qual=read(M/'reference-qualification.json')
for q in qual['qualifications']:
    mid=q['material_id'];cid=q['cached_id'];entry=read(M/q['cached_entry_snapshot'])
    e=entries['ghosh2012-'+mid+'-reference']
    ck('cached entry hash '+mid,objsha(entry)==e['provenance']['retainedEntrySha256'])
    for dim in ['2d','3d']:
        if (mid,dim) not in models:continue
        raw=read(M/'reference-snapshots/models'/f'{cid}-{dim}.json')
        if dim=='3d':
            ck('exact cached arrays '+mid+dim,all(raw[k]==models[(mid,dim)][k] for k in ['atoms','bonds']))
            ck('qualified original model hash '+mid,sha(M/'reference-snapshots/models'/f'{cid}-{dim}.json')==q['retainedModel3dSha256'])
        else:
            cachedmol=build_mol(raw)
            ck('cached 2D graph independent of drawing layout '+mid,Chem.MolToSmiles(Chem.RemoveHs(cachedmol),isomericSmiles=False)==Chem.MolToSmiles(Chem.RemoveHs(mols[(mid,dim)]),isomericSmiles=False))
for item in qual['retained_primary_artifacts']:
    p=M/item['snapshot_path'];ck('primary hash '+str(p),sha(p)==item['sha256'])
    if p.suffix=='.sdf':
        mol=next(iter(Chem.SDMolSupplier(str(p),removeHs=False)))
        ref=Chem.MolFromSmiles(expected_smiles[item['material_id']])
        ck('primary graph '+str(p),mol is not None and Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False)==Chem.MolToSmiles(ref,isomericSmiles=False))
        ck('primary formula '+str(p),rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(ref))
for mid in ['oa','ola']:
    mol=mols[(mid,'3d')];cc=[b for b in mol.GetBonds() if b.GetBondType()==Chem.BondType.DOUBLE and b.GetBeginAtom().GetSymbol()==b.GetEndAtom().GetSymbol()=='C']
    ck('retained cis reference '+mid,len(cc)==1 and str(cc[0].GetStereo())=='STEREOZ')
n=models[('liquid-nitrogen','3d')]
ck('NIST nitrogen length',abs(math.dist([n['atoms'][0][k] for k in ['x','y','z']],[n['atoms'][1][k] for k in ['x','y','z']])-1.09768)<1e-12)
ck('NIST triple bond',len(n['bonds'])==1 and n['bonds'][0]['order']==3)
ck('TOPSe only 2D',('top-se','3d') not in models)
ck('new references only 2D',all((m,'3d') not in models for m in ['od','doa']))
doa=mols[('doa','2d')]; nitrogen=[a for a in doa.GetAtoms() if a.GetSymbol()=='N'][0]
ck('secondary amine NH',nitrogen.GetDegree()==2 and nitrogen.GetTotalNumHs()==1)
ck('linear OD skeleton',sorted(a.GetDegree() for a in mols[('od','2d')].GetAtoms())==[1,1]+[2]*16)

allow=read(M/'public-asset-proposal.json')['relative_asset_files']
expected={e[k] for e in entries.values() for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
ck('exact 48 public assets',len(allow)==48 and set(allow)==expected)
for rel,digest in allow.items():
    p=M/rel;raw=p.read_text(encoding='utf-8')
    ck('public digest '+rel,sha(p)==digest)
    ck('public safe scope '+rel,p.suffix in ['.svg','.json'] and not any(s in raw for s in ['C:/Users/','C:\\Users\\','complete-source-payloads','firstPagePreviewPrivate']))
    if p.suffix=='.svg':ck('no active SVG '+rel,not re.search(r'<script|onload=|onerror=|<foreignObject',raw,re.I))
for x in [reg,bindings,read(M/'solution-components-proposal.json')]:ck('top-level approval false',x['binding_approved'] is False)
result={'schema':'mattersyn-independent-molecular-checks/1','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(c['passed'] for c in checks) else 'findings','check_count':len(checks),'checks':checks,'failures':[c for c in checks if not c['passed']],'model_details':details,'quantity_reference_count':len(quantities),'bound_files':bound,'canonical_version_checked':1,'later_canonical_rebind':'required before final audit'}
(A/'mechanical-checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':result['failures']},ensure_ascii=False))
