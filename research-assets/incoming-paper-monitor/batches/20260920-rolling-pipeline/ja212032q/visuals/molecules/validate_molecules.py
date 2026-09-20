"""Persisted private molecular/slot/stock checks; does not regenerate author assets."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,math,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];C=P/'canonical-proposal/v1'
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
ck('25 exact canonical material identities',len(E)==len({m['id'] for r in R.values() for m in r['materials']})==25)
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
ck('88 exact material slots',count==88)
ck('Three stocks and eight components',len(SS)==3 and sum(len(s['components']) for s in SS)==8)
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
 ctx=next(x for x in SC if x['id']=='ghosh2012-'+stock['stock_id'])
 ck(stock['stock_id']+' exact component roles',[c['role'] for c in ctx['components']]==[c['role'] for c in stock['components']])
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
for rid, notes in B['bindingNotes'].items():
 for mid,n in notes.items():
  for kind in ['grade_context_links','formulation_context_links']:
   for q in n[kind]:quantity_count+=1;ck(rid+'/'+mid+' '+kind+' exact pointer',resolve(R[q['record_id']],q['json_pointer'])==q['quantity'])

for s in SS:
 for q in s['concentration_links']:
  quantity_count+=1;ck('Exact concentration '+s['stock_id'],resolve(R[q['record_id']],q['json_pointer'])==q['quantity'] and q['quantity']['value']==.2)
q=B['bindingNotes']['ghosh-2012-source-materials']['selenium']['grade_context_links'][0]
ck('Selenium lower bound preserved',q['quantity']['minimum']==99.999 and q['quantity']['value'] is None and q['display_value']=='≥ 99.999 %')
q=B['bindingNotes']['ghosh-2012-optimized-shell-route']['cdse-core']['quantity_links'][0]
ck('Approximate core mol preserved',q['quantity']['approximate'] and q['quantity']['value']==2e-7 and q['display_value'].startswith('≈ '))
ck('TOPSe has no promoted embedding-only 3D',EM['ghosh2012-top-se-reference']['model3dPath'] is None)
for mid in ['cdo','cd-oleate','sulfur','selenium','r6g','glass','silicon','diamond','immersion-oil','cdse-core','cdse-cds','argon']:
 e=EM['ghosh2012-'+mid+'-reference'];ck(mid+' symbolic no coordinates',e['model2dPath'] is None and e['model3dPath'] is None)
for mid in ['oa','ola']:
 e=EM['ghosh2012-'+mid+'-reference'];m=read(O/e['model2dPath']);ref=Chem.MolFromSmiles(m['connectivitySmiles']);ck(mid+' explicit cis reference',any(b.GetStereo()==Chem.BondStereo.STEREOZ for b in ref.GetBonds()))
 e3=read(O/e['model3dPath']);mol=graph(e3);c=Chem.Conformer(mol.GetNumAtoms());c.Set3D(True)
 for i,a in enumerate(e3['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
 mol.AddConformer(c);Chem.AssignStereochemistryFrom3D(mol);ck(mid+' 3D matches reference stereo',Chem.MolToSmiles(Chem.RemoveHs(mol))==Chem.MolToSmiles(ref))
m=read(O/EM['ghosh2012-liquid-nitrogen-reference']['model3dPath']);a,b=m['atoms'];ck('Qualified NIST N2 distance',abs(math.dist([a[k]for k in ['x','y','z']],[b[k]for k in ['x','y','z']])-1.09768)<1e-8)
for e in E:
 if not e['model3dPath']:continue
 m=read(O/e['model3dPath']);n=len(m['atoms']);bonds={tuple(sorted((b['a'],b['b'])))for b in m['bonds']}
 for i in range(n):
  for j in range(i+1,n):
   d=math.dist([m['atoms'][i][k]for k in ['x','y','z']],[m['atoms'][j][k]for k in ['x','y','z']]);ck(e['id']+' finite nonoverlapping pair '+str(i)+'/'+str(j),math.isfinite(d)and d>.35)
ck('No product bindings or CIF',not(O/'product-bindings.json').exists() and not list(O.rglob('*.cif')))
out={'status':'passed_author_persisted_checks','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'quantity_reference_count':quantity_count,'independent_audit':'pending','browser_validation':'not_claimed'}
(O/'persisted-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'quantity_references':quantity_count,'status':'passed'}))
