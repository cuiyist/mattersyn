"""Persisted private molecular/slot/stock checks; does not regenerate author assets."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,math,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];C=P/'canonical-proposal/v2'
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(x,p):
 for t in p.strip('/').split('/') if p else []:x=x[int(t)] if isinstance(x,list) else x[t.replace('~1','/').replace('~0','~')]
 return x
checks=[]
def ck(label,value):
 checks.append({'check':label,'passed':bool(value)});assert value,label
def graph(raw):
 rw=Chem.RWMol()
 for a in raw['atoms']:
  z=Chem.Atom(a['element']);z.SetFormalCharge(a.get('formalCharge',0));z.SetIsotope(a.get('isotope',0));rw.AddAtom(z)
 for b in raw['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 m=rw.GetMol();Chem.SanitizeMol(m);return m
R={x['record_id']:read(x['path']) for x in read(C/'record-manifest.json')['records']}
E=read(O/'registry-additions.json')['entries'];EM={e['id']:e for e in E};B=read(O/'bindings-proposal.json');SS=read(O/'stock-component-map.json')['stocks'];SC=read(O/'solution-components-proposal.json')['contexts']
ck('29 exact canonical material identities',len(E)==len({m['id'] for r in R.values() for m in r['materials']})==29)
count=0;quantity_count=0
for rid,r in R.items():
 ck(rid+' exact slot membership',set(B['recordBindings'].get(rid,{}))=={m['id'] for m in r['materials']})
 for i,m in enumerate(r['materials']):
  count+=1;note=B['bindingNotes'][rid][m['id']];entry=EM[note['registry_id']]
  ck(rid+'/'+m['id']+' material transport',note['json_pointer']==f'/materials/{i}' and note['canonical_identity']==m)
  ck(rid+'/'+m['id']+' exact record hash',note['canonical_record_sha256']==sha(C/(rid+'.json')))
  ck(rid+'/'+m['id']+' audit gate pending',note['binding_approved'] is False and entry['binding_approved'] is False)
  ck(rid+'/'+m['id']+' reference mapping',B['recordBindings'][rid][m['id']]==entry['id'])
  for q in note['quantity_links']:
   quantity_count+=1;ck(rid+q['json_pointer']+' quantity exact',resolve(r,q['json_pointer'])==q['quantity'] and q['record_id']==rid)
ck('64 exact material slots',count==64)
ck('Five stocks and ten components',len(SS)==5 and sum(len(s['components']) for s in SS)==10)
for stock in SS:
 r=R[stock['record_id']];original=resolve(r,stock['json_pointer'])
 ck(stock['stock_id']+' exact stock concentrations',stock['concentrations']==original['concentrations'])
 ck(stock['stock_id']+' exact scope',stock['scope']==original['scope'])
 ck(stock['stock_id']+' components exact',[(c['material_id'],c['source_quantities']) for c in stock['components']]==[(c['material_id'],c['quantities']) for c in original['components']])
 for c in stock['components']:
  ck(stock['stock_id']+'/'+c['material_id']+' component pointer',resolve(r,c['json_pointer'])['material_id']==c['material_id'] and resolve(r,c['material_json_pointer'])['id']==c['material_id'])
  ck(stock['stock_id']+'/'+c['material_id']+' identity exact',EM[c['registry_id']]['provenance']['sourceMaterialId']==c['material_id'])
  for q in c['quantity_links']:quantity_count+=1;ck(stock['stock_id']+q['json_pointer']+' quantity exact',resolve(r,q['json_pointer'])==q['quantity'])
 for q in stock['solution_quantity_links']:quantity_count+=1;ck(stock['stock_id']+' solution volume exact',resolve(r,q['json_pointer'])==q['quantity'])
 ctx=next(x for x in SC if x['id']=='morrison2017-'+stock['stock_id'])
 ck(stock['stock_id']+' selector has two scoped roles',[c['role'] for c in ctx['components']]==['solute','solvent'])
 ck(stock['stock_id']+' selector matching identities',[c['registry_id'] for c in ctx['components']]==[c['registry_id'] for c in stock['components']])
 ck(stock['stock_id']+' selector pending gate',ctx['binding_approved'] is False)
for e in E:
 ck(e['id']+' paths relative and scoped',all(not Path(e[k]).is_absolute() and '..' not in Path(e[k]).parts for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)))
 for k,h in e['assetHashes'].items():ck(e['id']+k+' current asset hash',sha(O/e[k])==h)
 ck(e['id']+' no source-local path in exported entry',not re.search(r'[A-Z]:[\\/]|/Users/',json.dumps(e)))
 ck(e['id']+' no independent/training/publication claim',e['independentScientificAudit']=='pending' and not e['published'] and not e['eligible_training'])
 if e['depictionKind']=='symbolic_context':
  ck(e['id']+' no fabricated graph or coordinates',e['model2dPath'] is None and e['model3dPath'] is None);continue
 models=[]
 for k in ['model2dPath','model3dPath']:
  if not e[k]:continue
  m=read(O/e[k]);mol=graph(m);models.append(mol)
  ck(e['id']+k+' graph formula',rdMolDescriptors.CalcMolFormula(mol,separateIsotopes=True,abbreviateHIsotopes=True)==e['formula'])
  ck(e['id']+k+' finite coordinates',all(math.isfinite(a[x]) for a in m['atoms'] for x in ['x','y','z']))
  ck(e['id']+k+' zero net charge',sum(a.get('formalCharge',0) for a in m['atoms'])==0)
  ck(e['id']+k+' zero-based atom indices',[a.get('index',i) for i,a in enumerate(m['atoms'])]==list(range(len(m['atoms']))))
  for g in m['functionalGroups']:
   ck(e['id']+k+g['label']+' valid atom indices',all(0<=i<len(m['atoms']) for i in g['atomIndices']))
   ck(e['id']+k+g['label']+' valid bond indices',all(0<=i<len(m['bonds']) for i in g.get('bondIndices',[])))
  if k=='model2dPath':ck(e['id']+' 2D units and mode',m['coordinateUnits']=='arbitrary drawing units' and m['has3D'] is False and all(a['z']==0 for a in m['atoms']))
  else:ck(e['id']+' 3D Å units',m['coordinateUnits'].lower() in ['angstrom','angstroms','å'])
 if len(models)==2:ck(e['id']+' same 2D/3D connectivity',Chem.MolToSmiles(Chem.RemoveHs(models[0]))==Chem.MolToSmiles(Chem.RemoveHs(models[1])))
for q in read(O/'reference-qualification.json')['qualifications']:
 e=next(e for e in E if e['provenance']['sourceMaterialId']==q['material_id']);old=read(O/q['cached_entry_snapshot'])
 for key in ['svgPath','model2dPath','model3dPath']:
  if old.get(key):ck(q['material_id']+key+' immutable cached asset',sha(O/'reference-snapshots'/old[key])==old['assetHashes'][key])
 if e['model3dPath']:
  a=read(O/'reference-snapshots'/old['model3dPath']);b=read(O/e['model3dPath'])
  ck(q['material_id']+' original atom/coordinate arrays unchanged',a['atoms']==b['atoms'])
  ck(q['material_id']+' original bonds unchanged',a['bonds']==b['bonds'])
for x in read(O/'reference-snapshots/manifest.json')['snapshots']:ck('snapshot '+x['snapshot_path'],sha(O/x['snapshot_path'])==x['sha256'])
for path,h in read(O/'input-bindings.json').items():ck('bound input unchanged '+str(Path(path).name),sha(path)==h)
rt=next(s for s in SS if s['stock_id']=='cdptc-dmso-excess');ck('Approximate 40 mM preserved',rt['concentrations']['solute_concentration']['approximate'] is True)
cs=next(s for s in SS if s['stock_id']=='cdptc-thf-crystal-feed');ck('No concentration invented for ambiguous 20 mmol',cs['concentrations']=={} and '20 mM' in cs['display_limit'])
hot=B['bindingNotes']['morrison-2017-excess-precursor-hot'];ck('40 mM not assigned to heated branch',all(not n['quantity_links'] for n in hot.values()))
ck('Dispersion mass explicitly distinguished','not dry CdSe mass' in B['bindingNotes']['morrison-2017-monolayer-shell']['cdse-qb']['viewOverrides']['caption'])
out={'status':'passed_author_persisted_checks','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'quantity_reference_count':quantity_count,'independent_audit':'pending','browser_validation':'not_claimed'}
(O/'persisted-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'quantity_references':quantity_count,'status':'passed'}))
