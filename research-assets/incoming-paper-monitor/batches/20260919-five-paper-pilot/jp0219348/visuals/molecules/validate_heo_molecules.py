"""Author checks only; source and registry inputs are read-only. Writes this package's report."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import ast, hashlib, json, math, re, struct, xml.etree.ElementTree as ET

O=Path(__file__).resolve().parent
H=O.parents[1]
if (O/'package-freeze.json').exists():raise SystemExit('Frozen package: preserve a revision before writing a new author report.')
def load(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v): Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(scope, statement, ok, detail=None):
    checks.append({'scope':scope,'statement':statement,'passed':bool(ok),'detail':detail})

g=load(O/'generation-manifest.json')
new=load(O/'registry-additions.json')['entries']
refs=load(O/'reused-references.json')
old={x['id']:x for x in load(O/'reference-base/registry.json')['entries']}
bind=load(O/'molecule-binding-plan.json')
stock=load(O/'component-view-proposal.json')
facts=load(H/'source-facts.json')
fm={x['id']:x for x in facts['facts']}
inv=load(H/'source-inventory.json')
for p,h in g['input_hashes'].items():
    ck('input identity',p,Path(p).is_file() and sha(p)==h)
for p,h in g['files'].items():
    ck('generated identity',p,(O/p).is_file() and sha(O/p)==h)
for s in refs['immutable_snapshots']:
    ck('immutable reference',s['snapshot_path'],sha(O/s['snapshot_path'])==s['snapshot_sha256']==s['original_sha256'])
ck('inventory','Eight new and three exact reused entries',len(new)==8 and len(refs['entries'])==3)
ck('inventory','New IDs unique and absent from old registry',len({e['id'] for e in new})==8 and all(e['id'] not in old for e in new))
ck('privacy','New registry/model metadata contains no local absolute paths',not re.search(r'[A-Z]:[\\/]|file://|/Users/',json.dumps(new)+ (O/'models/heo2003-thallous-acetate-2d.json').read_text(encoding='utf-8')))

def elements(model):
    c=Counter(a['element'] for a in model['atoms'])
    c['H']+=sum(a.get('implicitHydrogenCount',0) for a in model['atoms'])
    return +c
def molecular_check(p,expected):
    m=load(p); atoms=m['atoms']; bonds=m['bonds']; n=len(atoms)
    ck(p.name,'Formula from explicit atoms plus implicit H',elements(m)==Counter(expected),dict(elements(m)))
    ck(p.name,'Zero net formal charge',sum(a.get('formalCharge',0) for a in atoms)==0)
    ck(p.name,'Contiguous zero-based atom indices',[a['index'] for a in atoms]==list(range(n)) and m['indexConvention']=='zero-based')
    for a in atoms:
        ck(p.name,f"Atom {a['index']} has finite Cartesian/drawing coordinates",all(isinstance(a[k],(int,float)) and math.isfinite(a[k]) for k in ('x','y','z')))
    seen=set()
    for i,b in enumerate(bonds):
        ck(p.name,f'Bond {i} endpoints/order valid',0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'] and b['order'] in (1,1.5,2,3))
        pair=tuple(sorted((b['a'],b['b'])))
        ck(p.name,f'Bond {i} not duplicated',pair not in seen);seen.add(pair)
    for f in m.get('functionalGroups',[]):
        ck(p.name,f"{f['label']} valid atom indices",all(0<=i<n for i in f['atomIndices']))
        ck(p.name,f"{f['label']} valid and contained bond indices",all(0<=i<len(bonds) and {bonds[i]['a'],bonds[i]['b']}<=set(f['atomIndices']) for i in f['bondIndices']))
    if m['representation']=='2d':
        ck(p.name,'2D drawing units and no rotation/3D claim',m['coordinateUnits']=='drawing units' and m['has3D'] is False and m['allowRotation'] is False and all(a['z']==0 for a in atoms))
    else:
        ck(p.name,'Illustrative 3D in angstrom, explicit hydrogens',m['coordinateUnits']=='angstrom' and m['has3D'] and m['allowRotation'] and all(a.get('implicitHydrogenCount',0)==0 for a in atoms))
    return m

for e in new:
    for k,h in e['assetHashes'].items(): ck(e['id'],f'{k} exact bytes',sha(O/e[k])==h)
    ck(e['id'],'No independent approval/publication/training claim',not e['binding_approved'] and not e['published'] and not e['eligible_training'] and e['independentScientificAudit']=='pending')
    ck(e['id'],'No fabricated external CID',e['pubchemCid'] is None)
    ck(e['id'],'Source DOI and exact main hash',e['provenance']['sourceDoi']=='10.1021/jp0219348' and e['provenance']['sourceSha256']==facts['source_sha256'])
    root=ET.parse(O/e['svgPath']).getroot()
    ck(e['id'],'SVG accessible title and description',root.find('{http://www.w3.org/2000/svg}title') is not None and root.find('{http://www.w3.org/2000/svg}desc') is not None)
    if e['id']!='heo2003-thallous-acetate':
        ck(e['id'],'Symbolic identity has no atom model or functional groups',e['model2dPath'] is None and e['model3dPath'] is None and e['functionalGroups']==[] and not e['provenance']['measuredCoordinates'])
tl=molecular_check(O/'models/heo2003-thallous-acetate-2d.json',{'C':2,'H':3,'O':2,'Tl':1})
prior=load(O/'reference-base/models/norberg2004-sodium-acetate-2d.json')
ck('Tl acetate','All acetate atoms identical to qualified local fragment',tl['atoms'][1:]==prior['atoms'][1:])
ck('Tl acetate','All acetate bonds identical to qualified local fragment',tl['bonds']==prior['bonds'])
ck('Tl acetate','Isolated +1 Tl; no Tl–O or Tl–C bond',tl['atoms'][0]['element']=='Tl' and tl['atoms'][0]['formalCharge']==1 and all(0 not in (b['a'],b['b']) for b in tl['bonds']))
adj={i:set() for i in range(len(tl['atoms']))}
for b in tl['bonds']:adj[b['a']].add(b['b']);adj[b['b']].add(b['a'])
todo=set(adj);components=[]
while todo:
    component={next(iter(todo))};front=list(component)
    while front:
        for j in adj[front.pop()]-component:component.add(j);front.append(j)
    todo-=component;components.append(sorted(component))
ck('Tl acetate','Exactly Tl and acetate disconnected components',sorted(components)==[[0],[1,2,3,4]],components)
ck('Tl acetate','Formal carboxylate valence and negative O',tl['atoms'][4]['formalCharge']==-1 and [(b['a'],b['b'],b['order']) for b in tl['bonds']]==[(1,2,1),(2,3,2),(2,4,1)])
ck('Tl acetate','Formula normalization agrees with audited source inventory',next(x for x in inv['materials'] if x['id']=='heo2003-tl-acetate')['formula']=='TlC2H3O2' and tl['formula']=='C2H3O2Tl')
ck('Tl acetate','No water hydrate, 3D salt, stereochemistry or speciation invented','hydrate' in tl['caption'] and 'resonance' in tl['caption'] and 'dissolved speciation' in tl['caption'] and not tl['has3D'])
models={}
for e in refs['entries']:
    ck(e['id'],'Exact reference registry entry snapshot',e==old[e['id']]==load(O/'reference-base/entries'/f"{e['id']}.json"))
    for k,h in e['assetHashes'].items():ck(e['id'],f'{k} byte-identical reuse',sha(O/'reused'/e[k])==h==sha(O/'reference-base'/e[k]))
    if e['id']=='argon':
        ck('argon','Element identity only; no pseudo-3D',e['formula']=='Ar' and not e.get('model2dPath') and not e.get('model3dPath'))
    else:
        for dim in (2,3):
            p=O/'reused'/e[f'model{dim}dPath']
            models[(e['id'],dim)]=molecular_check(p,{'H':2,'O' if e['id']=='water' else 'S':1})
        m=models[(e['id'],3)]
        ck(e['id'],'3D remains computed illustration, never source measurement','comput' in json.dumps(m).lower() and 'illustrat' in json.dumps(m).lower())
        ck(e['id'],'Two single bonds and no stereoisomer assignment',len(m['bonds'])==2 and all(b['order']==1 and b.get('stereo','STEREONONE')=='STEREONONE' for b in m['bonds']))
geometry=[]
for eid in ('water','hydrogen-sulfide'):
    m=models[(eid,3)];a=m['atoms'];c=next(i for i,x in enumerate(a) if x['element'] not in ('H',));hs=[i for i,x in enumerate(a) if x['element']=='H']
    vectors=[[a[j][k]-a[c][k] for k in ('x','y','z')] for j in hs]
    lengths=[math.sqrt(sum(x*x for x in v)) for v in vectors]
    angle=math.degrees(math.acos(sum(x*y for x,y in zip(*vectors))/math.prod(lengths)))
    geometry.append({'id':eid,'bond_lengths_angstrom':lengths,'angle_degrees':angle,'meaning':'Sanity check on retained computed illustrative coordinates; not a measured Heo value or gas-phase benchmark'})
    ck(eid,'Finite noncollapsed bent geometry',all(.5<d<2.5 for d in lengths) and 50<angle<150,geometry[-1])
waterprop=load(O/'reference-base/raw/water-properties.json')['PropertyTable']['Properties'][0]
arprop=load(O/'reference-base/raw/argon-properties.json')['PropertyTable']['Properties'][0]
ck('cached primary provenance','Water CID/formula/connectivity',waterprop['CID']==962 and waterprop['MolecularFormula']=='H2O' and waterprop['SMILES']=='O')
ck('cached primary provenance','Argon CID/formula',arprop['CID']==23968 and arprop['MolecularFormula']=='Ar')
water_entry=old['water'];argon_entry=old['argon']
for eid,entry,rawname in [('water',water_entry,'water-properties.json'),('argon',argon_entry,'argon-properties.json')]:
    ck('cached primary provenance',f'{eid} property hash retained',sha(O/'reference-base/raw'/rawname) in json.dumps(entry))
ck('cached primary provenance','Water 2D SDF exact original hash retained',sha(O/'reference-base/raw/water-pubchem-2d.sdf') in json.dumps(water_entry))
cached_builder=(O/'reference-base/audits/build_molecular_assets.py').read_text(encoding='utf-8')
definition_assignment=next(n for n in ast.parse(cached_builder).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='definitions' for t in n.targets))
definitions=ast.literal_eval(definition_assignment.value)
ck('local reference provenance','H2S builder explicitly defines SMILES S/formula H2S and ETKDG/UFF',any(row[:4]==('hydrogen-sulfide','Hydrogen sulfide','S','H2S') for row in definitions) and 'AllChem.ETKDGv3()' in cached_builder and 'AllChem.UFFOptimizeMolecule' in cached_builder)

expected={'na-x','tl-acetate','feed-water','wash-water','in-metal','h2s','pyrex','final-crystal','parent-reference','indium-reference','argon'}
slots={s['source_material_id']:s for s in bind['slots']}
ck('source slots','All eleven announced slots unique and covered',len(bind['slots'])==11 and set(slots)==expected)
for s in slots.values():
    ck('source slots',s['source_material_id']+' remains pending exact canonical binding',s['json_pointer'] is None and s['canonical_sha256'] is None and s['binding_approved'] is False)
ck('source slots','Both water roles reuse one identity with distinct source captions',slots['feed-water']['registry_id']==slots['wash-water']['registry_id']=='water' and slots['feed-water']['display_scope']!=slots['wash-water']['display_scope'])
ck('source slots','Unspecified feed grade distinct from explicit deionized wash','grade is unspecified' in slots['feed-water']['display_scope'] and 'Explicitly deionized' in slots['wash-water']['display_scope'])
ck('source slots','Argon is analytical sputtering, not synthesis atmosphere','XPS ion sputtering' in slots['argon']['display_scope'] and 'not reported as the synthesis atmosphere' in slots['argon']['display_scope'])
ck('source slots','Parent reference does not borrow final coordinates','no parent atomic structure' in slots['parent-reference']['display_scope'])
ck('source slots','Final nominal/average and measurement states remain distinct',all(t in slots['final-crystal']['display_scope'] for t in ['Si100Al92','Si96Al96','Sealed diffraction','atmosphere-exposed EDS','sputtered XPS','cannot establish sample joins']))
ck('stock','Salt and aqueous solvent separately selectable',[(x['registry_id'],x['material_id']) for x in stock['components']]==[('heo2003-thallous-acetate','tl-acetate'),('water','feed-water')])
ck('stock','Stock remains pending with no invented preparation',stock['stock_id']=='tl-acetate-feed' and stock['stock_json_pointer'] is None and stock['canonical_sha256'] is None and not stock['source_stock_preparation_created'] and not stock['binding_approved'])
ck('stock','Concentration/pH match audited facts',fm['heo2003-exchange-stock']['value']==.1 and fm['heo2003-exchange-stock']['unit']=='mol/L' and fm['heo2003-exchange-ph']['value']==6.4 and '.1 mol/L' in stock['scope'] and '6.4' in stock['scope'])
ck('stock','Volume basis unresolved, no salt:water count','basis is unresolved' in stock['scope'] and 'No fixed salt:water count' in stock['scope'])
for fid,value,unit in [('heo2003-wash-volume',10,'mL'),('heo2003-wash-time',1,'day'),('heo2003-h2s-pressure',.5,'atm'),('heo2003-h2s-t',673,'K'),('heo2003-h2s-time',12,'h')]:
    ck('reported quantities',fid,fm[fid]['value']==value and fm[fid]['unit']==unit)
ck('source scope','Dryer recipe and gas quantity remain unreported','Drying medium identity and procedure, gas quantity and flow are unreported' in slots['h2s']['display_scope'])
for eid,fid in [('identity-heo2003-na-x','heo2003-parent-host'),('identity-heo2003-in87-x','heo2003-washed-parent'),('identity-heo2003-in66-x','heo2003-product-formula')]:
    ck('source identity',eid,next(e for e in new if e['id']==eid)['formula']==fm[fid]['value'])
ck('source identity','Residue and glass formula unresolved',all(e['formula'] is None for e in new if e['id'] in ['identity-heo2003-surface-residue','identity-heo2003-pyrex']))
page=(O/'component-preview.html').read_text(encoding='utf-8')
ck('selector contract','Two explicit controls and mapped local image paths',page.count('type="button"')==2 and 'data-key="salt"' in page and 'data-key="water"' in page and "select('salt')" in page)
ck('selector contract','No external scripts or asset requests','<script src=' not in page and 'https://' not in page)

manual=[]
descriptions={
'heo2003-thallous-acetate':'Tl+ isolated in left panel; acetate single/double bonds and minus charge correct; carboxylate highlighted; no Tl–O bond; all labels readable.',
'identity-heo2003-na-x':'Nominal Na92Si100Al92O384, identity-only host and no parent lattice.',
'identity-heo2003-tl-x':'Nominal Tl92Si100Al92O384, exchange intermediate without coordinates.',
'identity-heo2003-in87-x':'Parent/control In87 identity, explicit no borrowed In66 coordinates.',
'identity-heo2003-in66-x':'Nominal Si100Al92 versus average Si96Al96 shown distinctly; symbolic final context only.',
'identity-heo2003-indium-metal':'Element In symbol only, explicit no lattice/particle-size/coordinate model.',
'identity-heo2003-pyrex':'Generic capillary outline, dimensions/composition unreported.',
'identity-heo2003-surface-residue':'Unidentified gray residue, no confirmed formula or phase.',
'reused-water':'H2O formula depiction, neutral and no source-specific grade label.',
'reused-hydrogen-sulfide':'S linked once to each H; arbitrary bent 2D connectivity depiction, not measured angle.',
'reused-argon':'Ar element reference panel; no synthesis-atmosphere label.'}
for stem,note in descriptions.items():
    p=O/'review'/f'{stem}.png';b=p.read_bytes();width,height=struct.unpack('>II',b[16:24])
    ck('preview files',stem,b[:8]==b'\x89PNG\r\n\x1a\n' and width>=800 and height>=300)
    manual.append({'path':str(p),'sha256':sha(p),'pixels':[width,height],'actually_viewed':True,'reviewer':'/root/backlog_eta','method':'Actual individual rendered PNG inspection via view_image in this author turn','finding':note})
fail=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-private-molecular-author-validation/1','source_id':'heo2003','author':'/root/backlog_eta','reviewer':'/root/backlog_eta','independent_audit':False,'at':datetime.now(timezone.utc).isoformat(),'status':'author_checks_passed_pending_distinct_audit_and_canonical_binding' if not fail else 'author_checks_failed','counts':g['counts'],'mechanical_checks':{'total':len(checks),'passed':len(checks)-len(fail),'failed':len(fail)},'checks':checks,'manual_preview_scope':manual,'computed_geometry_sanity':geometry,'bound_inputs':g['input_hashes'],'bound_package_files':{str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name not in ('author-validation.json','package-freeze.json')},'remaining_gates':['Distinct independent chemical/source-scope audit','Actual frozen canonical record IDs, JSON pointers and hashes; final approved material bindings not created','Reader integration, viewer/runtime consumption and browser quality assurance','Separate average crystal candidate integration; no host/parent lattice inferred here'],'scope_limit':'This author validation checks local reference chemistry, source labels and generated identity depictions. It is not a repeated full-paper/SI scientific audit, final binding approval, or publication approval.'}
dump(O/'author-validation.json',out)
print(json.dumps({'checks':len(checks),'failed':len(fail),'findings':fail,'geometry':geometry},ensure_ascii=False))
raise SystemExit(1 if fail else 0)
