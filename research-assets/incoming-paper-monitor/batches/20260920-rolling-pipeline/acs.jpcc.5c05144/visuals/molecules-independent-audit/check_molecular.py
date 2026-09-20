"""Distinct molecular/stock audit; no author scripts or outputs are executed."""
import collections,hashlib,json,math,re,sys,datetime
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).parent;J=O.parents[1];A=J/'visuals/molecules';M=J.parents[4]
sys.path[:0]=[str(M/'research-assets'),str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from sync_github_public import io_path
from rdkit import Chem,rdBase
from rdkit.Chem import rdMolDescriptors
from PIL import Image
import pymupdf
checks=[];bound={};chemistry=[]
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def read(p):bind(p);return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def ck(n,v,detail=None):checks.append({'check':n,'passed':bool(v),**({'detail':detail} if detail is not None else {})})
def ptr(v,p):
 for k in p.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def mol(d):
 r=Chem.RWMol()
 for a in d['atoms']:
  t=Chem.Atom(a['element']);t.SetIsotope(a.get('isotope',0));t.SetFormalCharge(a.get('formalCharge',0))
  if 'implicitHydrogenCount' in a:t.SetNoImplicit(True);t.SetNumExplicitHs(a['implicitHydrogenCount'])
  r.AddAtom(t)
 for b in d['bonds']:r.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']])
 m=r.GetMol();Chem.SanitizeMol(m);c=Chem.Conformer(len(d['atoms']));c.Set3D(True)
 for i,a in enumerate(d['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
 m.AddConformer(c);return m
freeze=read(A/'package-freeze.json');ck('exact frozen package',sha(A/'package-freeze.json')=='d0061aaac1876774eb8e6667ad2cec6203fdcf90cbd27b6de30c18be5c583bf8')
for p,h in freeze['bound_files'].items():ck('frozen file '+p,bind(p)==h)
inputs=read(A/'input-bindings.json')
for name,x in inputs.items():
 if isinstance(x,dict) and 'path' in x and 'sha256' in x:ck('source/canonical input '+name,bind(x['path'])==x['sha256'])
for x in inputs['snapshots']:ck('retained reference snapshot '+x['snapshot'],bind(x['snapshot'])==x['sha256'])
records={}
for p,h in inputs['canonical_records'].items():r=read(p);records[r['record_id']]=r;ck('canonical hash '+r['record_id'],sha(p)==h)
for name in ['source_audit','canonical_audit']:ck('distinct passed input audit '+name,read(inputs[name]['path'])['status']=='passed')
facts=read(inputs['source_facts']['path']);materials={x['id']:x for x in facts['materials']}
reg=read(A/'registry-additions.json');entries={e['id']:e for e in reg['entries']};ids={e['provenance']['sourceMaterialId']:e for e in reg['entries']}
qual={x['material_id']:x for x in read(A/'reference-qualification.json')['references']};prior={e['id']:e for e in read(A/'reference-snapshots/registry-base.json')['entries']}
expected={'formamidine-acetate':('C3H8N2O2','[NH2+]=C[NH2].CC(=O)[O-]',2),'oa':('C18H34O2','CCCCCCCC/C=C\\CCCCCCCC(=O)O',1),'oam':('C18H37N','CCCCCCCC/C=C\\CCCCCCCCN',1),'ode':('C18H36','C=CCCCCCCCCCCCCCCCC',1),'toluene':('C7H8','Cc1ccccc1',1),'acetonitrile':('C2H3N','CC#N',1),'nitrogen':('N2','N#N',1)}
patterns={'Formamidinium resonance group':'[NH2+]=[CH][NH2]','Acetate carboxylate':'[CX3](=[OX1])[O-]','Carboxylic acid':'[CX3](=[OX1])[OX2H1]','Cis reference alkene':'[CX3]=[CX3]','Primary amine':'[NX3;H2;+0]','Terminal alkene':'[CH2]=[CH]','Aromatic ring':'c1ccccc1','Nitrile':'[CX2]#[NX1]','Dinitrogen triple bond':'N#N'}
ck('13 exact source identities',set(ids)==set(materials) and len(ids)==13)
for mid,e in ids.items():
 ck('no premature approval '+mid,e['binding_approved'] is False and e['published'] is False and e['eligible_training'] is False)
 ck('current source provenance '+mid,e['provenance']['sourceDoi']=='10.1021/acs.jpcc.5c05144' and e['provenance']['sourceFactsSha256']==inputs['source_facts']['sha256'] and e['provenance']['sourceLocators']==materials[mid]['evidence'])
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):ck('asset hash '+e['id']+'/'+k,bind(A/e[k])==e['assetHashes'][k])
 if mid not in expected:
  ck('qualified symbol has no atom model '+mid,e['model2dPath'] is None and e['model3dPath'] is None and e['functionalGroups']==[]);continue
 formula,smiles,nfrag=expected[mid];target=Chem.MolFromSmiles(smiles);target_graph=Chem.MolToSmiles(target,isomericSmiles=False)
 for k in ['model2dPath','model3dPath']:
  if not e[k]:continue
  d=read(A/e[k]);m=mol(d);name=mid+'/'+k
  ck('validated formula '+name,rdMolDescriptors.CalcMolFormula(m)==formula and d['formula']==formula)
  ck('exact named graph '+name,Chem.MolToSmiles(Chem.RemoveHs(m),isomericSmiles=False)==target_graph)
  ck('net charge and fragments '+name,Chem.GetFormalCharge(m)==0 and len(Chem.GetMolFrags(m))==nfrag)
  ck('no training '+name,d['eligible_training'] is False)
  for i,a in enumerate(d['atoms']):ck('atom index/finite '+name+str(i),a.get('index',i)==i and all(math.isfinite(a[q]) for q in ['x','y','z']))
  for i,b in enumerate(d['bonds']):ck('bond mapping '+name+str(i),0<=b['a']<len(d['atoms']) and 0<=b['b']<len(d['atoms']) and b['a']!=b['b'] and b['order'] in [1,1.5,2,3])
  for g in d['functionalGroups']:
   matches=m.GetSubstructMatches(Chem.MolFromSmarts(patterns[g['label']]))
   ck('functional group chemistry '+name+g['label'],set(g['atomIndices']) in [set(t) for t in matches])
   groupb=[i for i,b in enumerate(d['bonds']) if b['a'] in g['atomIndices'] and b['b'] in g['atomIndices']]
   ck('functional bond indices '+name+g['label'],g['bondIndices']==groupb)
  oid=qual[mid]['provenance'].get('retainedRegistryId')
  if oid:
   cached=read(A/'reference-snapshots'/prior[oid][k]);ck('exact retained arrays '+name,d['atoms']==cached['atoms'] and d['bonds']==cached['bonds'])
  if k=='model2dPath':
   ck('2D units and geometry '+mid,d['coordinateUnits']=='arbitrary drawing units' and all(abs(a['z'])<1e-12 for a in d['atoms']) and d['allowRotation'] is False and d['has3D'] is False)
   ck('entry group mapping matches2D '+mid,e['functionalGroups']==d['functionalGroups'])
  else:
   ck('3D units/availability '+mid,d['coordinateUnits']=='angstrom' and d['has3D'] is True and d['allowRotation'] is True)
   distances=[]
   for i,b in enumerate(d['bonds']):
    length=math.dist([d['atoms'][b['a']][q] for q in ['x','y','z']],[d['atoms'][b['b']][q] for q in ['x','y','z']]);distances.append(length);ck('plausible bond '+mid+str(i),.65<length<2)
   for i,a in enumerate(d['atoms']):
    for j in range(i):ck('no duplicate/gross overlap '+mid+str((i,j)),math.dist([a[q] for q in ['x','y','z']],[d['atoms'][j][q] for q in ['x','y','z']])>.6)
   if mid in ['oa','oam']:
    Chem.AssignStereochemistryFrom3D(m);ck('explicit qualified cis geometry '+mid,Chem.MolToSmiles(Chem.RemoveHs(m))==Chem.MolToSmiles(target))
   if mid=='nitrogen':ck('chemically specific NIST nitrogen distance',abs(distances[0]-1.09768)<1e-10 and d['referenceIsotopologue']=='14N2')
   if mid in ['oa','oam','ode','toluene']:
    sd=next((A/'reference-snapshots/primary'/mid).glob('*3d.sdf'));bind(sd);raw=Chem.MolFromMolBlock(io_path(sd).read_text(encoding='utf-8'),removeHs=False)
    ck('raw PubChem atom count '+mid,raw.GetNumAtoms()==m.GetNumAtoms())
    ck('raw PubChem graph '+mid,Chem.MolToSmiles(Chem.RemoveHs(raw),isomericSmiles=False)==target_graph)
    for i,a in enumerate(d['atoms']):
     p=raw.GetConformer().GetAtomPosition(i);ck('raw PubChem atom/coordinate '+mid+str(i),raw.GetAtomWithIdx(i).GetSymbol()==a['element'] and max(abs(a[q]-getattr(p,q)) for q in ['x','y','z'])<1e-9)
   chemistry.append({'material_id':mid,'formula':formula,'atom_count':m.GetNumAtoms(),'bond_count':m.GetNumBonds(),'min_bond_angstrom':min(distances),'max_bond_angstrom':max(distances)})

slots=read(A/'material-slot-map.json')['slots'];bindings=read(A/'bindings-proposal.json');qrefs=[]
def qcheck(q):qrefs.append(q);ck('quantity leaf transport '+q['record_id']+q['json_pointer'],ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
ck('26exact complete material slots',len(slots)==26 and {(n['record_id'],n['material_id']) for n in slots}=={(rid,m['id']) for rid,r in records.items() for m in r['materials']})
for n in slots:
 r=records[n['record_id']];e=entries[n['registry_id']];key=n['record_id']+'/'+n['material_id']
 ck('exact canonical identity '+key,ptr(r,n['json_pointer'])==n['canonical_identity'])
 ck('source object exact '+key,n['source_material']==materials[n['material_id']])
 ck('exact binding and note '+key,bindings['recordBindings'][n['record_id']][n['material_id']]==n['registry_id'] and bindings['bindingNotes'][n['record_id']][n['material_id']]==n)
 ck('entry digest '+key,digest(e)==n['entry_sha256'])
 ck('role/identity no cross-source leakage '+key,e['provenance']['sourceMaterialId']==n['material_id'] and n['canonical_identity']['name']==materials[n['material_id']]['name'])
 for q in n['quantity_links']+n['grade_context_links']:qcheck(q)
 for opt in n['condition_option_links']:
  ck('complete paired condition '+key+opt['condition_option_id'],next(x for x in r['condition_options'] if x['id']==opt['condition_option_id'])==opt['condition_option']);qcheck(opt['quantity_link'])
stocks=read(A/'stock-component-map.json')['stocks'];solutions=read(A/'solution-components-proposal.json')['contexts'];sourcemap={s['id']:s for s in facts['stocks']}
ck('5complete stock instances12components',len(stocks)==5 and sum(len(s['components']) for s in stocks)==12 and {(s['record_id'],s['stock_id']) for s in stocks}=={(rid,s['id']) for rid,r in records.items() for s in r['stocks']})
for s in stocks:
 r=records[s['record_id']];cx=next(c for c in solutions if c['record_id']==s['record_id'] and c['id']==s['record_id']+'-'+s['stock_id'])
 ck('stock exact canonical payload '+s['record_id']+'/'+s['stock_id'],ptr(r,s['json_pointer'])==s['canonical_stock'])
 ck('stock source payload unchanged '+s['stock_id'],s['source_stock']==sourcemap[s['stock_id']])
 ck('stock no invented concentration '+s['stock_id'],s['concentrations']=={} and s['concentration_links']==[])
 ck('solution selector exact component IDs',[(c['material_id'],c['registry_id'],c['role']) for c in cx['components']]==[(c['material_id'],c['registry_id'],c['role']) for c in s['components']])
 for comp in s['components']:
  ck('stock component canonical quantities '+s['stock_id']+comp['material_id'],ptr(r,comp['json_pointer'])['quantities']==comp['source_quantities'] and ptr(r,comp['material_json_pointer'])['id']==comp['material_id'])
  for q in comp['quantity_links']:qcheck(q)
 for q in s['solution_quantity_links']:qcheck(q);ck('aliquot separate from fullstock',q['quantity']['value']==.51 and q['meaning']=='subsequent_prepared_stock_aliquot_not_stock_preparation_volume')
 if s['stock_id'].startswith('wash'):
  n=int(s['stock_id'].split('-')[-1]);ck('wash relative parts notvolume',[(c['material_id'],next(iter(c['source_quantities'].values()))['value'],next(iter(c['source_quantities'].values()))['unit']) for c in s['components']]==[('acetonitrile',1.0,'volume_parts'),('toluene',float(n),'volume_parts')])
 else:ck('whole stock source charges',[(c['material_id'],next(iter(c['source_quantities'].values()))['value']) for c in s['components']]==[('formamidine-acetate',.1042),('oa',.8),('ode',3.2)])
ck('74 exact typed quantity references',len(qrefs)==74)
for mid,raw in [('formamidine-acetate','99'),('oa','99'),('oam','70'),('ode','>90'),('toluene','99.8'),('acetonitrile','99.8'),('hexane','95')]:ck('source grade exact '+mid,all(n['grade_context_links'][0]['quantity']['raw_text']==raw for n in slots if n['material_id']==mid))

assets=read(A/'effective-public-assets.json')['assets'];ck('30exact approved-scope asset candidates',len(assets)==30 and len({a['public_path'] for a in assets})==30)
for a in assets:
 ck('public asset exact '+a['public_path'],bind(a['path'])==a['sha256'])
 ck('source originals notpublic '+a['public_path'],not a['whole_source_page'] and not re.search(r'source-render|reference-snapshots|\.pdf$|\.sdf$',a['public_path']))
 text=io_path(Path(a['path'])).read_text(encoding='utf-8');ck('no private filesystem path '+a['public_path'],not re.search(r'[A-Z]:[\\/]|file://',text))
for directory,preview in [('svg','previews'),('stock-svg','stock-previews')]:
 for p in (A/directory).glob('*.svg'):
  d=pymupdf.open(stream=io_path(p).read_bytes(),filetype='svg');pm=d[0].get_pixmap(alpha=False);actual=Image.open(io_path(A/preview/(p.stem+'.png'))).convert('RGB');ck('actual SVG pixel preview '+p.name,actual.size==(pm.width,pm.height) and actual.tobytes()==pm.samples)
contacts=read(A/'contact-index.json');ck('all23panels included',contacts['panel_count']==23 and sum(len(c['panels']) for c in contacts['contacts'])==23)
for p in [J/'source-render/si-03.png',J/'source-render/text/si-03.txt']:bind(p)
bind(Path(__file__));ck('all frozen inputs remain stable',all(sha(p)==h for p,h in bound.items()))
result={'status':'passed' if all(x['passed'] for x in checks) else 'findings_required','author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package_freeze_sha256':sha(A/'package-freeze.json'),'runtime':sys.executable,'rdkit_version':rdBase.rdkitVersion,'summary':{'executed':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']]},'chemistry':chemistry,'quantity_reference_count':len(qrefs),'checks':checks,'bound_files':bound}
io_path(O/'independent-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
