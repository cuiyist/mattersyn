"""Author checks of Pati molecular references, quantities and slot/stock mappings."""
from pathlib import Path
from collections import Counter
import json,hashlib,math,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4]
sys.dont_write_bytecode=True;sys.path[:0]=[str(M/'research-assets/rdkit-runtime')]
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def ptr(v,p):
 for k in p.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
source=read(P/'source-facts.json');sm={x['id']:x for x in source['materials']}
ck('Passed source audit',read(P/'source-independent-audit/independent-audit.json')['status']=='passed')
ck('Exact passed source audit hash',sha(P/'source-independent-audit/independent-audit.json')=='792fe4a10d755d7db21d3c8dee035591a682563bfa9e5ffce3b1a9882daa37eb')
inputs=read(O/'input-bindings.json')
for p,h in inputs['source_files'].items():ck('Source hash '+p,sha(p)==h)
ck('Canonical package unchanged',sha(inputs['canonical_package_manifest']['path'])==inputs['canonical_package_manifest']['sha256'])
ck('Canonical record manifest unchanged',sha(inputs['canonical_record_manifest']['path'])==inputs['canonical_record_manifest']['sha256'])
records={}
for p,h in inputs['canonical_records'].items():
 ck('Canonical record hash '+p,sha(p)==h);r=read(p);records[r['record_id']]=r
 ck('No training tasks '+r['record_id'],r['quality']['requested_tasks']==[])
entries={e['id']:e for e in read(O/'registry-additions.json')['entries']};em={e['provenance']['sourceMaterialId']:e for e in entries.values()}
ck('All 20 source identities exactly once',set(em)==set(sm) and len(em)==len(entries)==20)
assets={};modelPaths=set()
for e in entries.values():
 ck('False approval flags '+e['id'],e['binding_approved'] is e['published'] is e['eligible_training'] is False)
 ck('No source coordinates '+e['id'],e['provenance']['measuredCoordinates'] is False)
 ck('Source locators exact '+e['id'],e['provenance']['sourceLocators']==sm[e['provenance']['sourceMaterialId']]['evidence'])
 ck('Literal source formula preserved '+e['id'],e['sourceFormula']==sm[e['provenance']['sourceMaterialId']]['source_formula_or_abbreviation'])
 ck('No inherited other-paper display metadata '+e['id'],not any(x in (e['caption']+' '+e['name']).lower() for x in ['matuhina','ghosh','ribeiro','nagasaki','sommer','lian']))
 for key in ['svgPath','model2dPath','model3dPath']:
  if e[key]:
   p=O/e[key];ck('Asset exists/hash '+e[key],p.is_file() and sha(p)==e['assetHashes'][key]);assets[e[key]]=sha(p)
   if key!='svgPath':modelPaths.add(p)
 if e['depictionKind']=='symbolic_context':ck('Symbol has no hidden atom model '+e['id'],e['model2dPath'] is e['model3dPath'] is None)
ck('34 explicit public asset candidates',len(assets)==34)
qual=read(O/'reference-qualification.json');qm={x['source_material_id']:x for x in qual['models']}
for s in qual['snapshots']:ck('Immutable snapshot '+s['snapshot'],sha(O/s['snapshot'])==s['sha256'])
def reconstruct(m):
 rw=Chem.RWMol()
 for i,a in enumerate(m['atoms']):
  ck('Atom index',a['index']==i);ck('Finite coordinates',all(math.isfinite(a[k]) for k in ['x','y','z']))
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:atom.SetNoImplicit(True);atom.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(atom)
 seen=set()
 for b in m['bonds']:
  ij=tuple(sorted([b['a'],b['b']]));ck('Unique valid bond',0<=ij[0]<ij[1]<len(m['atoms']) and ij not in seen);seen.add(ij)
  rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
  a,c=m['atoms'][b['a']],m['atoms'][b['b']];d=math.dist([a[k] for k in ['x','y','z']],[c[k] for k in ['x','y','z']])
  ck('Plausible reference/drawing bond length',.7<d<2.2)
 for i,a in enumerate(m['atoms']):
  for b in m['atoms'][i+1:]:ck('No gross atom overlap',math.dist([a[k] for k in ['x','y','z']],[b[k] for k in ['x','y','z']])>.15)
 for g in m['functionalGroups']:
  ck('Valid nonempty group atoms',len(g['atomIndices'])>0 and len(set(g['atomIndices']))==len(g['atomIndices']) and all(0<=i<len(m['atoms']) for i in g['atomIndices']))
  for i in g['bondIndices']:
   ck('Valid group bond',0<=i<len(m['bonds']));b=m['bonds'][i];ck('Group endpoints included',b['a'] in g['atomIndices'] and b['b'] in g['atomIndices'])
 ck('Functional groups present',bool(m['functionalGroups']))
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
for mid,q in qm.items():
 expected=Chem.MolFromSmiles(q['reference_smiles']);m2=read(O/q['model2dPath']);mol=reconstruct(m2)
 ck(mid+' full reference connectivity',Chem.MolToSmiles(mol)==Chem.MolToSmiles(expected))
 ck(mid+' formula',rdMolDescriptors.CalcMolFormula(mol)==q['reference_formula'])
 ck(mid+' 2D restriction',m2['representation']=='2d' and not m2['has3D'] and not m2['allowRotation'] and all(a['z']==0 for a in m2['atoms']))
 ck(mid+' fragment count',len(Chem.GetMolFrags(mol))==q['fragment_count'])
 if q['model3dPath']:
  m3=read(O/q['model3dPath']);mol3=reconstruct(m3)
  ck(mid+' retained3D graph',Chem.MolToSmiles(Chem.RemoveHs(mol3))==Chem.MolToSmiles(expected))
  ck(mid+' 3D formula',rdMolDescriptors.CalcMolFormula(mol3)==q['reference_formula'])
  entry=read(O/'reference-snapshots/entries'/(q['cached_identity']+'.json'));old=read(O/'reference-snapshots'/entry['model3dPath'])
  ck(mid+' atom/bond arrays unchanged',m3['atoms']==old['atoms'] and m3['bonds']==old['bonds'])
  for key in ['method','conformerGeneration','coordinateUnits','referenceDistanceAngstrom','construction']:
   if key in old:ck(mid+' retained model methodology '+key,m3[key]==old[key])
  if mid=='nitrogen-bet':
   a,b=m3['atoms'];ck('NIST 14N2 distance exact',abs(math.dist([a[k] for k in ['x','y','z']],[b[k] for k in ['x','y','z']])-1.09768)<1e-10)
  if mid=='butanol':
   raw=Chem.MolFromMolFile(str(O/'reference-snapshots/raw/1-butanol-pubchem-263-3d.sdf'),removeHs=False);ck('Butanol source SDF graph',Chem.MolToSmiles(Chem.RemoveHs(raw))==Chem.MolToSmiles(expected));cf=raw.GetConformer()
   ck('Butanol exact primary coordinates',len(m3['atoms'])==raw.GetNumAtoms() and all(abs(a[k]-getattr(cf.GetAtomPosition(i),k))<1e-9 for i,a in enumerate(m3['atoms']) for k in ['x','y','z']))
 if q['cached_identity'] and mid!='nitrogen-bet':
  file=O/'reference-snapshots/raw'/(q['cached_identity']+'-pubchem-2d.sdf')
  ck(mid+' cached primary 2D available',file.is_file());raw=Chem.MolFromMolFile(str(file),removeHs=False)
  ck(mid+' primary graph',Chem.MolToSmiles(Chem.RemoveHs(raw))==Chem.MolToSmiles(expected))
ce=read(O/qm['cerium-nitrate']['model2dPath']);cemol=reconstruct(ce)
ck('Ce hydrate has ten disconnected formula components',len(Chem.GetMolFrags(cemol))==10)
ck('Ce hydrate literal element counts',Counter(a['element'] for a in ce['atoms'])=={'Ce':1,'N':3,'O':15})
ck('Ce hydrate neutral total charge',sum(a['formalCharge'] for a in ce['atoms'])==0)
ck('No invented Ce bonds',all(ce['atoms'][b[k]]['element']!='Ce' for b in ce['bonds'] for k in ['a','b']))
tea=em['tea'];ck('TEA reference/literal split',tea['formula']=='C6H15NO3' and tea['sourceFormula']=='(C2H5OH)3N' and '(C2H5OH)3N' in tea['caption'])
ck('Protonated formula not silently graph-corrected',em['protonated-tea']['depictionKind']=='symbolic_context' and em['protonated-tea']['sourceFormula']=='(C2H5OH)3NH+')
bindings=read(O/'bindings-proposal.json');slots=read(O/'material-slot-map.json')['slots'];stocks=read(O/'stock-component-map.json')['stocks'];contexts=read(O/'solution-components-proposal.json')['contexts']
ck('All exact material slots',len(slots)==45 and {(x['record_id'],x['material_id']) for x in slots}=={(rid,m['id']) for rid,r in records.items() for m in r['materials']})
qlinks=0
def qcheck(refs):
 global qlinks
 for q in refs:ck('Exact canonical quantity '+q['json_pointer'],ptr(records[q['record_id']],q['json_pointer'])==q['quantity']);qlinks+=1
for s in slots:
 rid=s['record_id'];mid=s['material_id'];r=records[rid];e=entries[s['registry_id']]
 ck('Exact source/canonical material',ptr(r,s['json_pointer'])==s['canonical_identity'] and s['source_material']==sm[mid])
 ck('Exact consumer identity',bindings['recordBindings'][rid][mid]==e['id'] and e['provenance']['sourceMaterialId']==mid)
 ck('Exact consumer note',bindings['bindingNotes'][rid][mid]==s);ck('Entry digest',jsha(e)==s['entry_sha256']);qcheck(s['quantity_links']+s['grade_context_links'])
 ck('Only safe display override keys',set(s['viewOverrides'])=={'name','caption','limitations'})
 if rid.endswith('-route'):ck('Only selected route alcohol',set(r['materials'][i]['id'] for i in range(len(r['materials'])))&{'ethanol','propanol','butanol'}=={rid.split('-')[-2]})
ck('All exact stocks',len(stocks)==6 and {(s['record_id'],s['stock_id']) for s in stocks}=={(rid,s['id']) for rid,r in records.items() for s in r['stocks']})
components=0
for s in stocks:
 r=records[s['record_id']];ck('Exact stock snapshot',ptr(r,s['json_pointer'])==s['canonical_stock']);ck('Exact source stock',s['source_stock']==next(x for x in source['stocks'] if x['id']==s['stock_id']))
 qcheck(s['concentration_links']+s['solution_quantity_links']);ctx=next(c for c in contexts if c['record_id']==r['record_id'] and c['id']=='pati2009-'+s['stock_id'])
 ck('Stock scope displayed',s['display_limit'] in ctx['scope']);ck('Stock concentration displayed',s['concentration_links'][0]['display_value'] in ctx['scope'])
 ck('100 mL transfer not final volume',s['solution_quantity_links'][0]['quantity']['value']==100 and 'not_total_stock_preparation_volume' in s['solution_quantity_links'][0]['meaning'])
 for c,dc in zip(s['components'],ctx['components']):
  components+=1;raw=ptr(r,c['json_pointer']);ck('Exact component data',raw['material_id']==c['material_id'] and raw['quantities']==c['source_quantities']);ck('No invented component charge',c['source_quantities']=={})
  ck('Exact selected stock graph',dc['registry_id']==c['registry_id'] and entries[c['registry_id']]['provenance']['sourceMaterialId']==c['material_id']);ck('Exact source stock role',dc['role']==next(x['role'] for x in s['source_stock']['components'] if x['material_id']==c['material_id']))
  ck('Component caption preserves reference conflict',entries[c['registry_id']]['caption'] in dc['viewOverrides']['caption']);qcheck(c['quantity_links'])
ck('12 component slots',components==12)
diag=next(s for s in slots if s['record_id']=='pati-2009-filtrate-diagnostic');ck('10mL is not ammonia charge',diag['quantity_links'][0]['quantity']['value']==10 and 'not_ammonium_hydroxide_charge' in diag['quantity_links'][0]['meaning'])
ck('Air not attached to calcination',all(s['record_id'] in ['pati-2009-tga','pati-2009-source-materials'] for s in slots if s['material_id']=='air'))
ck('Hydrate water is mechanism only',all(s['record_id']=='pati-2009-source-materials' for s in slots if s['material_id']=='hydrate-water'))
save={'schema':'mattersyn-author-molecular-validation/1','author':'/root/peng1998_reader_assets','status':'passed_author_checks','check_count':len(checks),'checks':checks,'counts':{'identities':20,'slots':45,'stocks':6,'components':12,'model2d':8,'retained3d':6,'public_assets':34,'quantity_links':qlinks},'independent_approval':False,'browser_approval':False}
(O/'author-validation.json').write_text(json.dumps(save,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'checks':len(checks),'counts':save['counts']}))
