from pathlib import Path
import sys,json,hashlib,math,collections
O=Path(__file__).resolve().parent; A=O.parent/'molecules';P=A.parents[1];M=P.parents[4]
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
checks=0;bound={};results=[]
def ck(v,m):
 global checks
 assert v,m
 checks+=1
def bind(p,h=None):
 p=Path(p);ck(p.is_file(),'Exists '+str(p));s=sha(p)
 if h:ck(s==h,'Hash '+str(p))
 bound[str(p.resolve())]=s
 return s
f=read(A/'package-freeze.json');bind(A/'package-freeze.json','91666cffcec1eac0851778cd5c64bd5bed2946593fe501c06bc36d8928e8856c')
for p,h in f['bound_files'].items():bind(p,h)
for n in ['effective-file-map.json','effective-public-assets.json']:
 for name,v in read(A/n).items():bind(v['path'],v['sha256'])
source=read(P/'source-facts.json');sm={m['id']:m for m in source['materials']}
for d in source['source_documents']:bind(d['source_path'],d['sha256'])
ca=P/'canonical-reader-independent-audit/independent-audit-v1.json';bind(ca,'db000b5efb8e3314b1f428112b75d50aad8fc58010ef268d3d457e494b79a16f');ck(read(ca)['status']=='passed','Canonical approval')
entries={e['id']:e for e in read(A/'registry-additions.json')['entries']}
ck(len(entries)==28,'28 unique entries');ck({e['provenance']['sourceMaterialId'] for e in entries.values()}==set(sm),'Complete source identities')
assets={}
for e in entries.values():
 mid=e['provenance']['sourceMaterialId'];ck(e['formula']==sm[mid]['source_formula_or_abbreviation'],'Source formula '+mid)
 ck(e['provenance']['sourceFactsSha256']==sha(P/'source-facts.json'),'Source facts bound')
 ck(e['provenance']['sourceLocators']==sm[mid]['evidence'],'Identity locators exact')
 ck(not any(e[k] for k in ['binding_approved','published','eligible_training']),'No approval')
 ck(not e['provenance']['measuredCoordinates'],'No source coordinate claim')
 for key in ['svgPath','model2dPath','model3dPath']:
  if e.get(key):bind(A/e[key],e['assetHashes'][key]);assets[e[key]]=e['assetHashes'][key]
 if e['depictionKind']=='symbolic_context':ck(not e['model2dPath'] and not e['model3dPath'],'Symbol has no hidden model')
 ck(not any(n in (e['name']+' '+e['caption']).lower() for n in ['ghosh','nagasaki','sommer','ribeiro','lian','norberg']),'No other paper display context')
allow=read(A/'effective-public-assets.json');ck(set(assets)==set(allow) and len(allow)==44,'Exact 44 asset allowlist')
ck(all(p.startswith(('models/','svg/')) and p.endswith(('.json','.svg')) for p in allow),'No source documents public')
expected={'cs-carbonate':'[Cs+].[Cs+].[O-]C([O-])=O','oa':'CCCCCCCC/C=C\\CCCCCCCC(=O)O','olam':'CCCCCCCC/C=C\\CCCCCCCCN','mncl2':'[Cl-].[Cl-].[Mn+2]','meoac':'CC(=O)OC','ipa':'CC(O)C','etoac':'CC(=O)OCC','water':'O','hno3':'O[N+](=O)[O-]','heavy-water':'[2H]O[2H]'}
qual={x['reference_key']:x for x in read(A/'reference-qualification.json')['models']}
def mol_from_model(m):
 rw=Chem.RWMol();cf=Chem.Conformer(len(m['atoms']));cf.Set3D(True) # allow stereochemistry inference from even planar drawing coordinates; not a model classification
 for i,a in enumerate(m['atoms']):
  ck(a['index']==i,'Atom index');ck(all(math.isfinite(a[k]) for k in ['x','y','z']),'Finite coordinates')
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:atom.SetNoImplicit(True);atom.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(atom);cf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
 seen=set()
 for b in m['bonds']:
  a,c=b['a'],b['b'];pair=tuple(sorted((a,c)));ck(0<=a<len(m['atoms']) and 0<=c<len(m['atoms']) and a!=c and pair not in seen,'Unique valid bond');seen.add(pair)
  rw.AddBond(a,c,{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);mol.AddConformer(cf);Chem.AssignStereochemistryFrom3D(mol)
 return mol
model_count=0;group_count=0
for key,qs in qual.items():
 ref=Chem.MolFromSmiles(expected[key]);ck(ref is not None,'Expected identity valid')
 for rel in [qs['model2dPath'],qs['model3dPath']]:
  if not rel:continue
  m=read(A/rel);mol=mol_from_model(m);model_count+=1
  canon=lambda v,stereo:Chem.MolToSmiles(Chem.RemoveHs(v),isomericSmiles=stereo)
  ck(canon(mol,False)==canon(ref,False),'Independent expected connectivity '+rel)
  ck(rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(ref),'Independent formula '+rel)
  ck(Chem.GetFormalCharge(mol)==0,'Neutral formula total')
  if key in ['oa','olam']:ck(canon(mol,True)==canon(ref,True),'Cis reference from coordinates')
  for g in m['functionalGroups']:
   group_count+=1; ai=g['atomIndices'];bi=g['bondIndices'];ck(len(ai)==len(set(ai)) and all(0<=i<len(m['atoms']) for i in ai),'Group atoms')
   ck(all(0<=i<len(m['bonds']) and m['bonds'][i]['a'] in ai and m['bonds'][i]['b'] in ai for i in bi),'Group bond membership')
   elems=collections.Counter(m['atoms'][i]['element'] for i in ai)
   if 'Carboxylic' in g['label']:ck(elems=={'C':1,'O':2},'Carboxylic acid group')
   if 'Alkene' in g['label']:ck(elems=={'C':2} and len(bi)==1 and m['bonds'][bi[0]]['order']==2,'Alkene group')
   if 'amine' in g['label'].lower():ck(elems['N']==1 and elems['C']==1,'Amine functional group')
  if key in ['cs-carbonate','mncl2']:
   ck(len(Chem.GetMolFrags(mol))==3 and not m['has3D'],'Formal salt fragments')
   ck(not any(m['atoms'][b['a']]['element'] in ['Cs','Mn'] or m['atoms'][b['b']]['element'] in ['Cs','Mn'] for b in m['bonds']),'No metal coordination')
  if key=='heavy-water':ck(collections.Counter((a['element'],a.get('isotope',0)) for a in m['atoms'])=={('O',0):1,('H',2):2},'Two deuteria')
  if m['has3D']:
   old=read(A/'reference-snapshots/models'/f"{qs['cached_identity']}-3d.json")
   ck(m['atoms']==old['atoms'] and m['bonds']==old['bonds'],'Cached arrays exact')
   if m['functionalGroups']!=old['functionalGroups']:
    ck(key in ['olam','water','hno3'],'Only qualified highlight metadata changes')
    if key=='olam':ck(m['functionalGroups'][0]['atomIndices']==[0,17] and m['functionalGroups'][0]['bondIndices']==[0],'Primary amine includes bonded carbon')
    if key=='water':ck(m['functionalGroups'][0]['atomIndices']==[0,1,2] and m['functionalGroups'][0]['bondIndices']==[0,1],'Complete water highlight')
    if key=='hno3':ck(m['functionalGroups'][0]['atomIndices']==old['functionalGroups'][0]['atomIndices'] and m['functionalGroups'][0]['bondIndices']==old['functionalGroups'][0]['bondIndices'],'Nitric group label only')
   ck(m['coordinateUnits']=='angstrom' and m['allowRotation'],'3D units and rotation')
   for b in m['bonds']:
    dist=math.dist([m['atoms'][b['a']][k] for k in ['x','y','z']],[m['atoms'][b['b']][k] for k in ['x','y','z']]);ck(.65<dist<1.95,'Reference covalent distance')
   for i,a in enumerate(m['atoms']):
    for b in m['atoms'][i+1:]:ck(math.dist([a[k] for k in ['x','y','z']],[b[k] for k in ['x','y','z']])>.45,'No gross coordinate overlap')
  else:ck(not m['allowRotation'] and m['coordinateUnits']=='arbitrary drawing units' and all(a['z']==0 for a in m['atoms']),'2D drawing limits')
  results.append({'asset':rel,'formula':rdMolDescriptors.CalcMolFormula(mol),'expected_graph_match':True,'fragments':len(Chem.GetMolFrags(mol)),'cached_3d_arrays_unchanged':True if m['has3D'] else None})
ck(model_count==16,'Ten graphs and six conformers')
# Verify retained primary SDF graphs, and 3D coordinates where an external conformer is claimed.
raws={'cs-carbonate':'cesium-carbonate-pubchem-2d.sdf','oa':'oleic-acid-pubchem-445639-3d.sdf','olam':'oleylamine-pubchem-5356789-3d.sdf','ipa':'2-propanol-pubchem-3776-3d.sdf','etoac':'ethyl-acetate-pubchem-2d.sdf','water':'water-pubchem-2d.sdf','hno3':'nitric-acid-pubchem-2d.sdf'}
for key,name in raws.items():
 raw=A/'reference-snapshots/raw'/name;bind(raw);m=Chem.MolFromMolFile(str(raw),removeHs=False);ck(m is not None,'Primary SDF valid '+name)
 ck(canon(m,False)==canon(Chem.MolFromSmiles(expected[key]),False),'Primary graph '+key)
 if key in ['oa','olam','ipa']:
  out=read(A/qual[key]['model3dPath']);cf=m.GetConformer();ck(len(out['atoms'])==m.GetNumAtoms(),'Primary conformer atom count')
  for i,a in enumerate(out['atoms']):ck(a['element']==m.GetAtomWithIdx(i).GetSymbol() and all(abs(a[k]-getattr(cf.GetAtomPosition(i),k))<1e-6 for k in ['x','y','z']),'Primary conformer positions')
hraw=M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/jp0473669/visuals/molecules/raw/nitric-acid-pubchem-3d.sdf'
hout=read(A/'models/matuhina2023-hno3-3d.json');bind(hraw,hout['rawSourceSha256']);hm=Chem.MolFromMolFile(str(hraw));ck(hm is not None,'Nitric primary conformer valid')
ck(hm.GetNumAtoms()==len(hout['atoms']),'Nitric conformer heavy atoms');cf=hm.GetConformer()
for i,a in enumerate(hout['atoms']):ck(a['element']==hm.GetAtomWithIdx(i).GetSymbol() and all(abs(a[k]-getattr(cf.GetAtomPosition(i),k))<1e-6 for k in ['x','y','z']),'Nitric primary conformer positions')
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)] if isinstance(x,list) else x[t.replace('~1','/').replace('~0','~')]
 return x
records={}
for item in read(P/'canonical-proposal/v1/record-manifest.json')['records']:
 bind(item['path'],item['sha256']);r=read(item['path']);records[r['record_id']]=r
slots=read(A/'material-slot-map.json')['slots'];binds=read(A/'bindings-proposal.json');stockmap=read(A/'stock-component-map.json')['stocks'];solutions=read(A/'solution-components-proposal.json')['contexts']
expectedslots={(rid,m['id']) for rid,r in records.items() for m in r['materials']};ck({(s['record_id'],s['material_id']) for s in slots}==expectedslots and len(slots)==55,'All exact slots covered once')
qlinks=0
def qcheck(items):
 global qlinks
 for q in items:ck(ptr(records[q['record_id']],q['json_pointer'])==q['quantity'],'Exact quantitative link');qlinks+=1
for s in slots:
 rid=s['record_id'];mid=s['material_id'];r=records[rid];entry=entries[s['registry_id']]
 ck(ptr(r,s['json_pointer'])==s['canonical_identity'],'Material snapshot exact');ck(s['source_material']==sm[mid],'Source identity exact')
 ck(entry['provenance']['sourceMaterialId']==mid,'Exact identity mapping');ck(s['entry_sha256']==jsha(entry),'Entry binding digest');ck(binds['recordBindings'][rid][mid]==entry['id'] and binds['bindingNotes'][rid][mid]==s,'Consumer bindings exact')
 qcheck(s['quantity_links']+s['grade_context_links']);ck(s['binding_approved'] is False,'Slot pending independent promotion')
ck({(s['record_id'],s['stock_id']) for s in stockmap}=={(rid,s['id']) for rid,r in records.items() for s in r['stocks']},'Every stock covered')
components=0
for s in stockmap:
 rid=s['record_id'];r=records[rid];actual=ptr(r,s['json_pointer']);ck(actual==s['canonical_stock'],'Stock snapshot')
 ck(s['source_stock']==next(x for x in source['stocks'] if x['id']==s['stock_id']),'Source stock exact')
 qcheck(s['concentration_links']+s['solution_quantity_links']);ctx=next(x for x in solutions if x['record_id']==rid and x['id']=='matuhina2023-'+s['stock_id']);ck(len(ctx['components'])==len(s['components']),'Solution component count')
 for c,display in zip(s['components'],ctx['components']):
  components+=1;act=ptr(r,c['json_pointer']);ck(act['material_id']==c['material_id'] and act['quantities']==c['source_quantities'],'Exact stock component');ck(ptr(r,c['material_json_pointer'])['id']==c['material_id'],'Exact material reference');ck(entries[c['registry_id']]['provenance']['sourceMaterialId']==c['material_id'],'Component graph identity');qcheck(c['quantity_links']);ck(display['registry_id']==c['registry_id'] and display['material_id']==c['material_id'],'UI component mapping')
ck(len(stockmap)==5 and components==15,'5 stocks / 15 components')
for n in ['main-02.png','main-03.png','si-13.png']:bind(P/'source-render'/n)
bind(Path(__file__))
out={'schema':'mattersyn-independent-molecular-checks/1','reviewer':'/root/peng1998_reader_assets','status':'passed','checks':checks,'quantity_links':qlinks,'model_count':model_count,'functional_groups':group_count,'models':results,'counts':{'identities':28,'slots':55,'stocks':5,'components':15,'assets':44},'bound_files':bound}
(O/'mechanical-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'status':'passed','checks':checks,'quantity_links':qlinks,'bound_files':len(bound)}))
