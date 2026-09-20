from pathlib import Path
import sys,json,hashlib,math,collections,io,re
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]');sys.path.insert(0,r'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;V=R/'visuals';M=V/'molecules';A=V/'apparatus';O=R/'visual-audit-assets';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[];bound={};geometries=[]
def ck(ok,label):
 checks.append({'passed':bool(ok),'label':label})
 if not ok:raise AssertionError(label)
def bind(p,h=None):
 p=Path(p);v=sha(p);ck(h is None or v==h,'Exact input '+str(p));bound[str(p)]=v
mf=read(V/'visual-author-manifest.json');bind(V/'visual-author-manifest.json','48d30537615d2333b56fb17b850bda0150a6ea360ad1119face3781d24dbf3c2')
for f,h in mf['files'].items():bind(R/f,h)
for f,h in mf['source_inputs'].items():
 # The immutable registry snapshot is the relevant input; live Site may receive unrelated integration.
 if 'recipe-atlas'in f:bind(M/'reference-base/registry.json',h)
 else:bind(f,h)
cm=read(R/'canonical-record-manifest.json')
for f,h in cm['source_pdf_hashes'].items():bind(f,h)
records={p.stem:read(p)for p in sorted((R/'canonical-drafts').glob('*.json'))}
for i in range(1,7):bind(R/f'main-{i:02}.txt')
for i in [2,3]:bind(R/f'main-{i}.png')
entries=read(M/'registry-additions.json')['entries'];reg={x['id']:x for x in entries};base={x['id']:x for x in read(M/'reference-base/registry.json')['entries']}
def graph(model):
 rw=Chem.RWMol()
 for a in model['atoms']:
  q=Chem.Atom(a.get('element',a.get('elem')));q.SetFormalCharge(a.get('formalCharge',0));q.SetIsotope(a.get('isotope',0));rw.AddAtom(q)
 for b in model['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def canon(m):return Chem.MolToSmiles(Chem.RemoveHs(m))
def formula_counts(s):return {e:int(n or 1)for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)}
def molecular(e,folder,expected):
 models=[]
 for key in ['model2dPath','model3dPath']:
  if not e.get(key):continue
  p=folder/e[key];bind(p,e['assetHashes'][key]);model=read(p);mol=graph(model);ck(canon(mol)==canon(Chem.MolFromSmiles(expected)),'Independently reconstructed graph '+e['id']+'/'+key);ck(formula_counts(rdMolDescriptors.CalcMolFormula(mol))==formula_counts(e['formula']),'Formula elemental counts '+e['id']+'/'+key);ck(Chem.GetFormalCharge(mol)==0,'Net charge '+e['id']+'/'+key)
  for a in model['atoms']:ck(all(math.isfinite(a[q])for q in ['x','y','z']),'Finite coordinate '+e['id']+'/'+str(a['index']))
  for g in model.get('functionalGroups',e.get('functionalGroups',[])):ck(all(0<=i<len(model['atoms'])for i in g['atomIndices']) and all(0<=i<len(model['bonds'])for i in g.get('bondIndices',[])),'Functional group indices '+e['id']+'/'+g['label'])
  if key=='model3dPath':
   lengths=[math.dist([model['atoms'][b['a']][q]for q in ['x','y','z']],[model['atoms'][b['b']][q]for q in ['x','y','z']])for b in model['bonds']];ck(all(.65<x<1.7 for x in lengths),'Bond lengths plausible for O/N/C/H reference '+e['id']);geometries.append({'id':e['id'],'model_sha256':sha(p),'bond_lengths_angstrom':lengths,'source_type':model.get('sourceType',model.get('modelType'))});models.append((e['id'],model))
  if 'reference2d'in e.get('provenance',{}):
   raw=folder/e['provenance']['reference2d']['path'];ref=Chem.SDMolSupplier(str(raw),removeHs=False)[0];ck(canon(ref)==canon(mol),'Cached SDF connectivity '+e['id']+'/'+key)
  if model.get('rawSourcePath'):
   raw=folder/model['rawSourcePath'];bind(raw,model['rawSourceSha256']);ref=Chem.SDMolSupplier(str(raw),removeHs=True)[0];ck(len(model['atoms'])==ref.GetNumAtoms(),'Cached 3D reference atom count '+e['id']);conf=ref.GetConformer();ck(all(max(abs(model['atoms'][i][q]-list(conf.GetAtomPosition(i))[j])for j,q in enumerate(['x','y','z']))<1e-6 for i in range(ref.GetNumAtoms())),'Exact cached PubChem heavy-atom coordinates '+e['id'])
 return models
models=[]
for e,s in [(reg['reference-tin-ii-chloride-dihydrate'],'[Sn+2].[Cl-].[Cl-].O.O'),(reg['reference-nitric-acid'],'O=[N+]([O-])O'),(reg['reference-tetrabutylammonium-hydroxide'],'CCCC[N+](CCCC)(CCCC)CCCC.[OH-]')]:models+=molecular(e,M,s)
for rid,s in [('ethanol','CCO'),('water','O')]:models+=molecular(base[rid],M/'reference-base',s)
tin=read(M/reg['reference-tin-ii-chloride-dihydrate']['model2dPath']);ck(len(Chem.GetMolFrags(graph(tin)))==5 and len(tin['bonds'])==0,'SnCl2 two chloride and two water components without coordination')
tba=graph(read(M/reg['reference-tetrabutylammonium-hydroxide']['model2dPath']));ck(len(Chem.GetMolFrags(tba))==2 and not any(a.GetSymbol()=='Br'for a in tba.GetAtoms()),'TBAOH two ionic components, no bromide')
for e in entries[3:]:ck(e['model2dPath']is None and e['model3dPath']is None and e['eligible_training']is False,'Context-only non-atomic entry '+e['id'])
b=read(M/'molecule-bindings-proposal.json');slottexts=[];slots=0
for rid,r in records.items():
 ck(set(b['recordBindings'][rid])=={m['id']for m in r['materials']},'All and only canonical materials '+rid)
 for i,m in enumerate(r['materials']):
  n=b['bindingNotes'][rid][m['id']];ck(n['registry_id']==b['recordBindings'][rid][m['id']] and n['registry_id']in reg|base,'Existing target '+rid+'/'+m['id']);ck(n['json_pointer']==f'/materials/{i}' and n['canonical_sha256']==sha(R/'canonical-drafts'/f'{rid}.json'),'Exact material pointer/hash '+rid+'/'+m['id'])
  ck(n['canonical_evidence']==m['evidence'] and n['canonical_quantities']==m['quantities'] and n['source_name']==m['name'] and n['source_role']==m['role'] and n['source_stage']==m['stage'],'Unchanged material source fields '+rid+'/'+m['id']);ck(n['binding_approved']is False,'Separate approval gate '+rid+'/'+m['id']);slots+=1;slottexts.append({'record':rid,'material':m['id'],'scope':n['display_scope']})
ck(slots==13,'13 unique material slots')
c=read(M/'component-view-proposal.json');ck(len(c['components'])==3 and c['no_new_canonical_stocks_created']is True,'Three component contexts only')
for x in c['components']:
 r=records[x['canonical_record_id']];ptr=x.get('canonical_stock_pointer',x.get('canonical_material_pointer'));q=r
 for k in ptr.split('/')[1:]:q=q[int(k)]if isinstance(q,list)else q[k]
 ck(q is not None,'Real canonical component parent '+x['context']);ck(all(v['registry_id']in reg|base for v in x['components']),'Known component references '+x['context'])
replay=read(R/'visual-scene-independent-replay.json');bind(R/'visual-scene-independent-replay.json');ck(all(x['passed']for x in replay['checks']),'Independent scene replay passed')
for row in replay['rows']:
 if row['pointer']:
  q=records[row['record_id']]
  for k in row['pointer'].split('/')[1:]:q=q[int(k)]if isinstance(q,list)else q[k]
  ck(q==row['canonical_quantity'],'Exact scene displayed-quantity input '+row['operation_id']+'/'+row['label'])
tiles=[]
for rid,model in models:
 # Independent coordinate projection; geometry comes only from the actual submitted model.
 im=Image.new('RGB',(700,470),'white');d=ImageDraw.Draw(im);d.text((16,14),rid+' | actual model coordinates',fill='#234c5d');at=model['atoms'];pts=[(.82*a['x']-.45*a['y'],.36*a['x']+.35*a['y']-.8*a['z'])for a in at];xmin=min(p[0]for p in pts);xmax=max(p[0]for p in pts);ymin=min(p[1]for p in pts);ymax=max(p[1]for p in pts);scale=min(510/max(xmax-xmin,.1),290/max(ymax-ymin,.1));pts=[(350+(x-(xmin+xmax)/2)*scale,235+(y-(ymin+ymax)/2)*scale)for x,y in pts]
 for bond in model['bonds']:d.line([pts[bond['a']],pts[bond['b']]],fill='#93a9b4',width=5)
 for a,(x,y)in zip(at,pts):
  col={'O':'#c26b71','N':'#6b84b6','C':'#657887','H':'#c1c8cb'}.get(a['element'],'gray');d.ellipse((x-10,y-10,x+10,y+10),fill=col);d.text((x+12,y-4),a['element']+('H'+str(a.get('implicitHydrogenCount'))if a.get('implicitHydrogenCount')else''),fill='#234c5d')
 d.text((16,435),'Reference projection; no source-solution structure or browser claim.',fill='#234c5d');p=O/(rid+'-projection.png');im.save(p);tiles.append((p,im));bound[str(p)]=sha(p)
contact=Image.new('RGB',(1400,940),'#e8f0f3')
for i,(p,im)in enumerate(tiles):contact.paste(im,((i%2)*700,(i//2)*470))
contact.save(O/'reference-coordinate-contact.png')
out={'status':'programmatic_checks_passed_manual_scope_closure_pending','author_manifest_sha256':sha(V/'visual-author-manifest.json'),'checks':checks,'bound_files':bound,'geometries':geometries,'material_scope_texts':slottexts,'scene_rows':replay['rows'],'counts':{'checks':len(checks),'replay_checks':len(replay['checks']),'material_slots':slots,'new_entries':6,'new_models':4,'reused_entries':2,'operation_scenes':13,'component_contexts':3},'scope':'Independent read-only source/graph/coordinate/field checks; author builders were not run.'}
dump(R/'visual-source-audit-checks.json',out);print(json.dumps({'checks':len(checks),'bound_files':len(bound),'slots':slottexts,'geometry':geometries},ensure_ascii=False))
