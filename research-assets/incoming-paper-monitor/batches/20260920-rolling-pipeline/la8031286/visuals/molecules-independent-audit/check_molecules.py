from pathlib import Path
import sys,json,hashlib,collections,math,re
A=Path(__file__).resolve().parent;V=A.parent/'molecules';N=A.parents[1];M=N.parents[4];C=N/'canonical-proposal/v2'
sys.dont_write_bytecode=True;sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import pymupdf
from PIL import Image
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text('utf8'))
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)})
def ptr(x,p):
 for k in p.strip('/').split('/')if p else []:x=x[int(k)]if isinstance(x,list)else x[k.replace('~1','/').replace('~0','~')]
 return x
f=read(V/'package-freeze.json');ck('Exact requested freeze',sha(V/'package-freeze.json')=='8b5724b9a7008dfb74cdc8f5cea7fdfcd47939a26b89d85916aebc77fed7c202')
for name,h in f['bound_files'].items():bound[name]=sha(name);ck('Frozen byte '+name,sha(name)==h)
ca=read(N/'canonical-reader-independent-audit/independent-audit-v2.json');ck('Distinct current canonical audit',ca['status']=='passed'and ca['auditor']=='/root/norberg2004_extract')
records={p.stem:read(p)for p in C.glob('pati-2009-*.json')};source=read(N/'source-facts.json');materials={x['id']:x for x in source['materials']};stocks={x['id']:x for x in source['stocks']}
for rid in records:ck('Exact canonical v1 to v2 byte bridge '+rid,sha(C/(rid+'.json'))==sha(N/'canonical-proposal/v1'/(rid+'.json')))
registry=read(V/'registry-additions.json');entries={e['id']:e for e in registry['entries']};slots=read(V/'material-slot-map.json')['slots'];components=read(V/'stock-component-map.json')['stocks'];bindings=read(V/'bindings-proposal.json');solutions=read(V/'solution-components-proposal.json')['contexts'];qual=read(V/'reference-qualification.json')
ck('20 exact source identities',set(entries)=={'pati2009-'+x+'-reference'for x in materials})
ck('Exact 45 material slots',{(x['record_id'],x['material_id'])for x in slots}=={(rid,m['id'])for rid,r in records.items()for m in r['materials']} and len(slots)==45)
for x in slots:
 rid=x['record_id'];m=ptr(records[rid],x['json_pointer']);e=entries[x['registry_id']];label=rid+'/'+m['id']
 ck('Exact material snapshot '+label,m==x['canonical_identity']);ck('Exact source identity '+label,materials[m['id']]==x['source_material']);ck('Exact record hash '+label,sha(C/(rid+'.json'))==x['canonical_record_sha256']);ck('Exact registry snapshot '+label,jsha(e)==x['entry_sha256'])
 ck('Exact identity assignment '+label,x['registry_id']=='pati2009-'+m['id']+'-reference'==bindings['recordBindings'][rid][m['id']]);ck('Binding pending '+label,x['binding_approved']is False)
 ck('Scoped overrides exact '+label,x['viewOverrides']==bindings['bindingNotes'][rid][m['id']]['viewOverrides'])
 for q in x['quantity_links']+x['grade_context_links']:
  ck('Exact quantity '+label+q['json_pointer'],ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
ck('Six exact stocks',{(s['record_id'],s['stock_id'])for s in components}=={(rid,s['id'])for rid,r in records.items()for s in r['stocks']}and len(components)==6)
for s in components:
 rid=s['record_id'];stock=ptr(records[rid],s['json_pointer']);context=next(c for c in solutions if c['id']=='pati2009-'+s['stock_id']);ck('Exact stock snapshot '+s['stock_id'],stock==s['canonical_stock']);ck('Exact source stock '+s['stock_id'],stocks[s['stock_id']]==s['source_stock']);ck('Only solute and matching solvent '+s['stock_id'],len(s['components'])==len(context['components'])==2)
 for c,view in zip(s['components'],context['components']):
  cm=ptr(records[rid],c['json_pointer']);ck('Component amount unchanged '+s['stock_id']+c['material_id'],cm=={'material_id':c['material_id'],'quantities':c['source_quantities']});ck('Exact source-qualified reference '+s['stock_id']+c['material_id'],view['registry_id']==c['registry_id']=='pati2009-'+c['material_id']+'-reference');ck('No geometry override '+s['stock_id']+c['material_id'],set(view['viewOverrides'])<= {'caption','limitations','name'})
 for q in s['concentration_links']+s['solution_quantity_links']:ck('Stock/transfer quantity '+s['stock_id']+q['json_pointer'],ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
 ck('Stock preparation volume remains unknown '+s['stock_id'],'not reported' in context['scope']and'100 mL' in context['scope']and'portion' in context['scope'])
expected={'cerium-nitrate':('[Ce+3].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O.O.O.O.O.O','H12CeN3O15',10),'tea':('OCCN(CCO)CCO','C6H15NO3',1),'ethanol':('CCO','C2H6O',1),'propanol':('OCCC','C3H8O',1),'butanol':('OCCCC','C4H10O',1),'acetone':('CC(C)=O','C3H6O',1),'nitrogen-bet':('N#N','N2',1),'hydrate-water':('O','H2O',1)}
def reconstruct(model):
 rw=Chem.RWMol()
 for a in model['atoms']:
  aa=Chem.Atom(a['element']);aa.SetFormalCharge(a.get('formalCharge',0));aa.SetIsotope(a.get('isotope',0));aa.SetNoImplicit(True);aa.SetNumExplicitHs(a.get('implicitHydrogenCount',0));rw.AddAtom(aa)
 for b in model['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
geometry=[]
for q in qual['models']:
 mid=q['source_material_id'];e=entries['pati2009-'+mid+'-reference'];model=read(V/e['model2dPath']);mol=reconstruct(model);smiles,formula,fragments=expected[mid];ck('Graph is independently expected identity '+mid,Chem.MolToSmiles(Chem.RemoveHs(mol))==Chem.MolToSmiles(Chem.MolFromSmiles(smiles)));ck('Element/H formula '+mid,rdMolDescriptors.CalcMolFormula(mol)==formula);ck('Disconnected component count '+mid,len(Chem.GetMolFrags(mol))==fragments);ck('Overall neutral reference '+mid,Chem.GetFormalCharge(mol)==0)
 ck('Registry/model group consistency '+mid,e['functionalGroups']==model['functionalGroups']);ck('Source literal formula remains separate '+mid,e['sourceFormula']==materials[mid]['source_formula_or_abbreviation'])
 for fg in model['functionalGroups']:
  ids=fg['atomIndices'];atoms=[mol.GetAtomWithIdx(i)for i in ids]
  ck('Functional indices valid '+mid+fg['label'],all(0<=i<len(model['atoms'])for i in ids)and all(0<=i<len(model['bonds'])for i in fg['bondIndices']))
  if fg['label']=='Tertiary amine nitrogen':ck('Tertiary amine chemical qualification '+mid,all(a.GetSymbol()=='N'and a.GetFormalCharge()==0 and a.GetDegree()==3 and all(n.GetSymbol()=='C' for n in a.GetNeighbors())for a in atoms))
  if fg['label']=='Alcohol group':ck('Alcohol group chemistry '+mid,sorted(a.GetSymbol()for a in atoms)==['C','O'] and any(a.GetSymbol()=='O'and a.GetTotalNumHs()==1 for a in atoms))
  if fg['label']=='Nitrate resonance group':ck('Nitrate chemistry '+mid,collections.Counter(a.GetSymbol()for a in atoms)=={'N':1,'O':3} and sum(a.GetFormalCharge()for a in atoms)==-1)
 if e['model3dPath']:
  m3=read(V/e['model3dPath']);cached=read(V/'reference-snapshots/models'/(q['cached_identity']+'-3d.json'));ck('Retained exact atoms '+mid,m3['atoms']==cached['atoms']);ck('Retained exact bonds '+mid,m3['bonds']==cached['bonds']);ck('3D same chemical graph '+mid,Chem.MolToSmiles(Chem.RemoveHs(reconstruct(m3)))==Chem.MolToSmiles(Chem.MolFromSmiles(smiles)))
  ds=[]
  for b in m3['bonds']:
   a,z=[m3['atoms'][i]for i in[b['a'],b['b']]];d=math.dist([a[k]for k in['x','y','z']],[z[k]for k in['x','y','z']]);ds.append(d);ck('Plausible covalent distance '+mid,0.8<d<1.8)
  if mid=='nitrogen-bet':ck('Retained NIST nitrogen distance',abs(ds[0]-1.09768)<1e-9)
  geometry.append({'id':mid,'atom_count':len(m3['atoms']),'bond_count':len(m3['bonds']),'minimum_bond_length':min(ds),'maximum_bond_length':max(ds)})
for e in entries.values():
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):bound[str(V/e[k])]=sha(V/e[k]);ck('Exact asset digest '+e['id']+'/'+k,sha(V/e[k])==e['assetHashes'][k])
 if e['id'].removeprefix('pati2009-').removesuffix('-reference')not in expected:ck('Symbolic identity has no fabricated graph '+e['id'],e['model2dPath'] is None and e['model3dPath']is None and not e['functionalGroups'])
 svg=V/e['svgPath'];png=V/'previews'/(e['id']+'.png');d=pymupdf.open(stream=svg.read_bytes(),filetype='svg');pix=d[0].get_pixmap(alpha=False);im=Image.open(png).convert('RGB');ck('Original SVG/preview pixel equality '+e['id'],im.size==(pix.width,pix.height)and im.tobytes()==pix.samples);d.close()
effective=read(V/'effective-public-assets.json');ck('34 public chemical assets',len(effective)==34)
for rel,x in effective.items():ck('Public allowlist only SVG/JSON '+rel,rel.startswith(('svg/','models/')) and Path(rel).suffix in ['.svg','.json']);ck('Public asset actual hash '+rel,sha(x['path'])==x['sha256'])
for x in qual['snapshots']:ck('Retained source-neutral snapshot '+x['snapshot'],sha(V/x['snapshot'])==x['sha256'])
for name in ['contact-01.png','contact-02.png','contact-03.png','contact-04.png','contact-05.png','contact-06.png']:bound[str(V/'contacts'/name)]=sha(V/'contacts'/name)
bound[str(Path(__file__))]=sha(Path(__file__))
out={'schema':'mattersyn-independent-molecule-checks/1','reviewer':'/root/norberg2004_extract','author':'/root/peng1998_reader_assets','check_count':len(checks),'checks':checks,'failures':[x for x in checks if not x['passed']],'geometry':geometry,'bound_files':bound}
(A/'scientific-checks-v1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'checks':len(checks),'failures':out['failures'],'geometry':geometry}))
