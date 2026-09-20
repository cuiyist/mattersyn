"""Independent read-only check of Peng's frozen Sommer chemical proposal.
Writes only this auditor directory; does not import or run author builders.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json, hashlib, math, sys, xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
O = Path(__file__).resolve().parent
P = O.parent / 'molecules'
R = O.parents[1]
M = R.parents[4]
sys.path.insert(0, str(M / 'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x): return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def ptr(x, path):
    for k in path.strip('/').split('/'):
        k = k.replace('~1', '/').replace('~0', '~')
        x = x[int(k)] if isinstance(x, list) else x[k]
    return x
checks = []
bound = {}
def ck(label, value): checks.append({'check': label, 'passed': bool(value)})
def bind(p):
    p = Path(p).resolve(); bound[str(p)] = sha(p); return p

freeze = read(bind(P/'package-freeze.json'))
ck('Exact initial frozen package', sha(P/'package-freeze.json') == '27436ab4627bd5efe80cc7aa6a226579ba0337735768e45740ca5e6ee23e4b13')
for p, h in freeze['bound_files'].items():
    ck('Frozen bytes '+p, sha(bind(p)) == h)
reg = read(P/'registry-additions.json')
entries = {e['id']: e for e in reg['entries']}
slots = read(P/'material-slot-map.json')['slots']
stocks = read(P/'stock-component-map.json')['stocks']
solutions = read(P/'solution-components-proposal.json')['contexts']
bindings = read(P/'bindings-proposal.json')
manifest = read(bind(R/'canonical-proposal/v1/record-manifest.json'))
records = {}; recordpaths = {}
for row in manifest['records']:
    p = bind(row['path']); ck('Record hash '+row['record_id'], sha(p) == row['sha256'])
    records[row['record_id']] = read(p); recordpaths[row['record_id']] = p
source = read(bind(R/'source-facts.json'))
source_mats = {m['id']: m for m in source['materials']}
source_stocks = {s['id']: s for s in source['stocks']}
ck('Complete source identity set', len(entries) == 28 and set(source_mats) == {e['provenance']['sourceMaterialId'] for e in entries.values()})
expected_slots = {(rid, m['id']) for rid, r in records.items() for m in r['materials']}
ck('Every material slot exactly once', len(slots) == len(expected_slots) == 62 and {(s['record_id'],s['material_id']) for s in slots} == expected_slots)
ck('Every stock exactly once', len(stocks) == 7 and {(s['record_id'],s['stock_id']) for s in stocks} == {(rid,s['id']) for rid,r in records.items() for s in r['stocks']})
ck('23 components and 7 selectors', sum(len(s['components']) for s in stocks) == 23 and len(solutions) == 7)

# Expected stoichiometry/connectivity supplied independently from the named chemicals.
expected = {
 'water': ('O', 'H2O', 1, 0),
 'ethanol': ('CCO', 'C2H6O', 1, 0),
 'zn-nitrate': ('[Zn+2].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O.O.O.O.O.O', 'H12N2O12Zn', 9, 0),
 'al-nitrate': ('[Al+3].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O.O.O.O.O.O.O.O.O', 'H18AlN3O18', 13, 0),
 'naoh': ('[Na+].[OH-]', 'HNaO', 2, 0),
 'nitrate-context': ('O=[N+]([O-])[O-]', 'NO3-', 1, -1)
}
model_results = []
for path in sorted((P/'models').glob('*.json')):
    d = read(bind(path)); key = path.stem.removeprefix('sommer2020-').removesuffix('-2d').removesuffix('-3d')
    smi, formula, fragment_count, charge = expected[key]
    atoms = d['atoms']; bonds = d['bonds']; rw = Chem.RWMol()
    for i,a in enumerate(atoms):
        ck(path.name+' index '+str(i), a['index'] == i)
        ck(path.name+' finite coordinate '+str(i), all(isinstance(a[k],(int,float)) and math.isfinite(a[k]) for k in ['x','y','z']))
        ca = Chem.Atom(a['element']); ca.SetFormalCharge(a.get('formalCharge',0)); ca.SetNoImplicit(True); ca.SetNumExplicitHs(a.get('implicitHydrogenCount',0)); ca.SetIsotope(a.get('isotope',0)); rw.AddAtom(ca)
    seen = set(); lengths=[]
    for i,b in enumerate(bonds):
        pair=tuple(sorted((b['a'],b['b'])))
        ck(path.name+' unique valid edge '+str(i), 0 <= pair[0] < pair[1] < len(atoms) and pair not in seen); seen.add(pair)
        rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']])
        length=math.dist([atoms[b['a']][k] for k in ['x','y','z']],[atoms[b['b']][k] for k in ['x','y','z']]); lengths.append(length)
        if d['representation']=='3d': ck(path.name+' physical bond length '+str(i), .7 < length < 1.7)
    mol=rw.GetMol(); Chem.SanitizeMol(mol)
    canonical = Chem.MolToSmiles(Chem.RemoveHs(mol)); expected_mol=Chem.MolFromSmiles(smi)
    ck(path.name+' independent named graph',canonical == Chem.MolToSmiles(expected_mol))
    ck(path.name+' exact formula',rdMolDescriptors.CalcMolFormula(mol) == formula == d['formula'])
    ck(path.name+' component count', len(Chem.GetMolFrags(mol)) == fragment_count)
    ck(path.name+' charge', sum(a.GetFormalCharge() for a in mol.GetAtoms()) == charge)
    ck(path.name+' no stereochemical invention', not Chem.FindMolChiralCenters(mol,includeUnassigned=True))
    for gi,g in enumerate(d['functionalGroups']):
        aset=set(g['atomIndices']); bset=set(g['bondIndices'])
        ck(path.name+' functional atom mapping '+str(gi),len(aset)==len(g['atomIndices']) and all(0<=a<len(atoms) for a in aset))
        ck(path.name+' functional edge mapping '+str(gi),len(bset)==len(g['bondIndices']) and all(0<=b<len(bonds) and {bonds[b]['a'],bonds[b]['b']}<=aset for b in bset))
        if 'Nitrate' in g['label']: ck(path.name+' nitrate highlight chemistry '+str(gi),Counter(atoms[a]['element'] for a in aset)=={'N':1,'O':3} and len(bset)==3)
    if d['representation']=='2d':
        ck(path.name+' honest drawing units',d['has3D'] is False and d['allowRotation'] is False and d['coordinateUnits']=='arbitrary drawing units' and all(a['z']==0 for a in atoms))
    else:
        ck(path.name+' angstrom and illustrative labels',d['coordinateUnits']=='angstrom' and 'illustrative' in d['caption'].lower() and 'not measured' in d['caption'].lower())
        original=read(bind(P/'reference-snapshots/models'/f'{key}-3d.json'))
        for field in ['atoms','bonds','functionalGroups','method','conformerGeneration']:
            ck(path.name+' cached '+field+' identical',d[field]==original[field])
        for i,a in enumerate(atoms):
            for j,b in enumerate(atoms[:i]): ck(path.name+f' no atomic collision {i}/{j}',math.dist([a[k] for k in ['x','y','z']],[b[k] for k in ['x','y','z']])>.6)
    if key in ['water','ethanol','zn-nitrate']:
        original_key={'zn-nitrate':'zinc-nitrate-hexahydrate'}.get(key,key)
        sdf=bind(P/'reference-snapshots/primary'/f'{original_key}-pubchem-2d.sdf')
        ref=Chem.SDMolSupplier(str(sdf),removeHs=False)[0]
        ck(path.name+' primary cached SDF graph',ref is not None and Chem.MolToSmiles(Chem.RemoveHs(ref)) == canonical)
    if key in ['zn-nitrate','al-nitrate']:
        fr=Counter(Chem.MolToSmiles(x) for x in Chem.GetMolFrags(mol,asMols=True)); n=2 if key=='zn-nitrate' else 3
        ck(path.name+' hydrate water count',fr['O']==(6 if n==2 else 9))
        ck(path.name+' nitrate count',fr['O=[N+]([O-])[O-]']==n)
        ck(path.name+' no coordination bonds',all(atoms[b['a']]['element'] not in ['Zn','Al'] and atoms[b['b']]['element'] not in ['Zn','Al'] for b in bonds))
    model_results.append({'path':str(path),'key':key,'formula':formula,'canonical_smiles':canonical,'components':fragment_count,'charge':charge,'representation':d['representation'],'bond_length_range': [min(lengths),max(lengths)] if lengths else None})

asset_set=set()
for eid,e in entries.items():
    mid=e['provenance']['sourceMaterialId']; src=source_mats[mid]
    ck(eid+' source identity and formula',e['name']==src['name'] and e['formula']==src['source_formula_or_abbreviation'])
    ck(eid+' source locators',e['provenance']['sourceLocators']==src['evidence'])
    ck(eid+' no training/published/approval',e['eligible_training'] is False and e['published'] is False and e['binding_approved'] is False)
    for k in ['svgPath','model2dPath','model3dPath']:
        if e.get(k):
            p=bind(P/e[k]); asset_set.add(e[k]); ck(eid+' '+k+' digest',sha(p)==e['assetHashes'][k])
    if not e['model2dPath']:ck(eid+' no hidden geometry',e['model3dPath'] is None and e['depictionKind']=='symbolic_context')
    svg=ET.parse(P/e['svgPath']).getroot(); ck(eid+' SVG readable canvas',svg.attrib.get('viewBox')=='0 0 1100 700')
    ck(eid+' no script or foreign-object in source artwork',not any(el.tag.rsplit('}',1)[-1] in ['script','foreignObject'] for el in svg.iter()))

def qcheck(q,label):
    ck(label+' exact canonical quantity',ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
    raw=q['quantity'].get('raw_text'); unit=q['quantity'].get('unit')
    if raw: ck(label+' literal numeric/bound display',q['display_value']==raw+(' '+unit if unit and unit!='ratio_parts' else ''))

for s in slots:
    rid=s['record_id']; mid=s['material_id']; key=rid+'/'+mid
    ck(key+' canonical identity transport',ptr(records[rid],s['json_pointer'])==s['canonical_identity'])
    ck(key+' exact original record bytes',sha(recordpaths[rid])==s['canonical_record_sha256'])
    ck(key+' exact source material transport',s['source_material']==source_mats[mid])
    e=entries[s['registry_id']]; ck(key+' exact registry entry',jsha(e)==s['entry_sha256'] and e['provenance']['sourceMaterialId']==mid)
    ck(key+' dispatch',bindings['recordBindings'][rid][mid]==s['registry_id'] and bindings['bindingNotes'][rid][mid]==s)
    ck(key+' approval remains false',s['binding_approved'] is False)
    for i,q in enumerate(s['quantity_links']+s['grade_context_links']):qcheck(q,key+' quantity '+str(i))
    for q in s['grade_context_links']:
        if mid in ['zn-nitrate','al-nitrate','naoh']:ck(key+' grade lower bound',q['quantity']['minimum']=={'zn-nitrate':99,'al-nitrate':98,'naoh':97}[mid] and q['quantity'].get('minimum_exclusive') is False and q['quantity']['value'] is None)
        if mid=='zno-feed':ck(key+' purchased size approximate',q['quantity']['approximate'] is True and q['quantity']['value']==30)

for s in stocks:
    rid=s['record_id']; sid=s['stock_id']; key=rid+'/'+sid
    canonical=ptr(records[rid],s['json_pointer'])
    ck(key+' complete canonical stock equality',canonical==s['canonical_stock'])
    ck(key+' original source stock equality',source_stocks[sid]==s['source_stock'])
    ck(key+' exact original record hash',sha(recordpaths[rid])==s['canonical_record_sha256'])
    ctx=next(x for x in solutions if x['record_id']==rid and x['id']=='sommer2020-'+sid)
    ck(key+' component selector matches',[(x['material_id'],x['registry_id']) for x in ctx['components']]==[(x['material_id'],x['registry_id']) for x in s['components']])
    for c in s['components']:
        data=ptr(records[rid],c['json_pointer']); mid=c['material_id']
        ck(key+'/'+mid+' exact constituent quantities',data['material_id']==mid and data['quantities']==c['source_quantities'])
        ck(key+'/'+mid+' exact material pointer',ptr(records[rid],c['material_json_pointer'])['id']==mid)
        for i,q in enumerate(c['quantity_links']): qcheck(q,key+'/'+mid+' quantity '+str(i))
    for i,q in enumerate(s['concentration_links']+s['solution_quantity_links']):qcheck(q,key+' solution quantity '+str(i))
    if sid in ['mw-low-base','mw-middle-base','mw-high-base']:
        ck(key+' inherited charges not re-added',all(not c['source_quantities'] for c in s['components']) and 'inherited' in s['display_limit'] and 'alternatives' in s['display_limit'])
    if sid=='mw-nitrate-stock':ck(key+' water charge not final volume', '20 mL water charge, not asserted final solution volume' in s['display_limit'])
    if sid=='insitu-nitrate-stock':ck(key+' solution volume not water charge',len(s['solution_quantity_links'])==1 and s['solution_quantity_links'][0]['quantity']['value']==30 and s['solution_quantity_links'][0]['meaning']=='stock_solution_volume_not_water_charge')
    if sid=='insitu-base-solutions':ck(key+' only delivered aliquot no mixed metals',not s['concentrations'] and all(not c['source_quantities'] for c in s['components']) and len(s['solution_quantity_links'])==1 and s['solution_quantity_links'][0]['quantity']['value']==1 and 'final mixed Zn/Al concentrations are excluded' in s['display_limit'])

allow=read(P/'public-asset-proposal.json')['assets']
ck('Exact public asset set',len(allow)==len(asset_set)==36 and {x['path'] for x in allow}==asset_set)
for x in allow:
    ck('Public file '+x['path'],sha(P/x['path'])==x['sha256'] and Path(x['path']).parts[0] in ['models','svg'])
    txt=(P/x['path']).read_text(encoding='utf8'); ck('No private path or complete payload '+x['path'],not any(t in txt for t in ['C:\\Users','C:/Users','source-render/','source-facts.json','complete-source']))
for p in [R/'source-render'/f'main-{i:02}.png' for i in [2,7,8]]:bind(p)
for p in (P/'contacts').glob('*.png'):bind(p)
result={'schema':'mattersyn-independent-molecule-checks/1','reviewer':'/root/backlog_eta','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_mechanical_checks' if all(x['passed'] for x in checks) else 'failed','check_count':len(checks),'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'models':model_results,'bound_files':bound,'scope':'Initial canonical v1 transport only; canonical scientific audit belongs to Norberg. Final approval awaits bounded source-specific SCF caption correction and canonical v2 rebind.'}
(O/'checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:result[k] for k in ['status','check_count','failed_checks']}))
