"""Author chemistry, geometry, pointer and source-scope checks; not peer approval."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,math,sys,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
inp=read(O/'input-bindings.json');reg=read(O/'registry-additions.json');entries={e['id']:e for e in reg['entries']};slots=read(O/'material-slot-map.json')['slots'];stocks=read(O/'stock-component-map.json')['stocks'];bindings=read(O/'bindings-proposal.json');source=read(P/'source-facts.json');sm={m['id']:m for m in source['materials']};records={}
for p,h in inp['canonical_records'].items():ck('Exact canonical '+p,sha(p)==h);r=read(p);records[r['record_id']]=r
for p,h in inp['inputs'].items():ck('Exact cached/source input '+p,sha(p)==h)
for name in['canonical_record_manifest','canonical_package_manifest','source_audit']:ck('Input manifest '+name,sha(inp[name]['path'])==inp[name]['sha256'])
ck('28 source identities',set(e['provenance']['sourceMaterialId']for e in entries.values())==set(sm))
ck('All55slots',len(slots)==sum(len(r['materials'])for r in records.values())==55)
ck('All5stocks15components',len(stocks)==5 and sum(len(s['components'])for s in stocks)==15)
assets={}
for eid,e in entries.items():
 mid=e['provenance']['sourceMaterialId'];ck(eid+' formula',e['formula']==sm[mid]['source_formula_or_abbreviation']);ck(eid+' no approval',not e['binding_approved']and not e['published']and not e['eligible_training'])
 ck(eid+' display is Matuhina-scoped',not any(x in json.dumps({k:e[k]for k in['name','caption','limitations']}).lower()for x in['ghosh','morrison','nagasaki','norberg','sommer','ribeiro']))
 for k in['svgPath','model2dPath','model3dPath']:
  if e.get(k):ck(eid+' asset '+k,sha(O/e[k])==e['assetHashes'][k]);assets[e[k]]=e['assetHashes'][k]
 if e['depictionKind']=='symbolic_context':ck(eid+' symbol has no hidden coordinates',not e['model2dPath']and not e['model3dPath'])
 root=ET.parse(O/e['svgPath']).getroot();ck(eid+' valid SVG canvas',root.attrib.get('viewBox')=='0 0 1100 700')
qual={q['reference_key']:q for q in read(O/'reference-qualification.json')['models']}
for rel,h in sorted(assets.items()):
 if not rel.endswith('.json'):continue
 m=read(O/rel);key=rel.removeprefix('models/matuhina2023-').removesuffix('-2d.json').removesuffix('-3d.json');rw=Chem.RWMol();cf=Chem.Conformer(len(m['atoms']));cf.Set3D(True)
 for i,a in enumerate(m['atoms']):
  ck(rel+' atom index '+str(i),a['index']==i);ck(rel+' finite coordinates '+str(i),all(isinstance(a[k],(int,float))and math.isfinite(a[k])for k in['x','y','z']));at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount'in a:at.SetNoImplicit(True);at.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(at);cf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
 seen=set()
 for bi,b in enumerate(m['bonds']):
  pair=tuple(sorted((b['a'],b['b'])));ck(rel+' bond endpoint '+str(bi),0<=pair[0]<pair[1]<len(m['atoms'])and pair not in seen);seen.add(pair);rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
  if m['has3D']:ck(rel+' reference bond length '+str(bi),.6<math.dist([m['atoms'][b['a']][k]for k in['x','y','z']],[m['atoms'][b['b']][k]for k in['x','y','z']])<1.95)
 mol=rw.GetMol();Chem.SanitizeMol(mol);mol.AddConformer(cf);Chem.AssignStereochemistryFrom3D(mol);exp=Chem.MolFromSmiles(m['connectivitySmiles']);ck(rel+' complete graph',Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False)==Chem.MolToSmiles(Chem.RemoveHs(exp),isomericSmiles=False));ck(rel+' formula count',rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(exp))
 if key in['oa','olam']:ck(rel+' cis reference geometry',Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True)==Chem.MolToSmiles(Chem.RemoveHs(exp),isomericSmiles=True))
 for gi,g in enumerate(m['functionalGroups']):
  ck(rel+' group atom indices '+str(gi),len(g['atomIndices'])==len(set(g['atomIndices']))and all(0<=i<len(m['atoms'])for i in g['atomIndices']));ck(rel+' group bond indices '+str(gi),all(0<=i<len(m['bonds'])and m['bonds'][i]['a']in g['atomIndices']and m['bonds'][i]['b']in g['atomIndices']for i in g['bondIndices']))
 if key in['cs-carbonate','mncl2']:
  ck(rel+' formal neutral salt',sum(a.GetFormalCharge()for a in mol.GetAtoms())==0);ck(rel+' three disconnected formula fragments',len(Chem.GetMolFrags(mol))==3);ck(rel+' no metal bonds',not any(m['atoms'][b['a']]['element']in['Cs','Mn']or m['atoms'][b['b']]['element']in['Cs','Mn']for b in m['bonds']));ck(rel+' no salt3D',not m['has3D'])
 if key=='heavy-water':ck('D2O exact isotope counts',Counter((a['element'],a.get('isotope',0))for a in m['atoms'])==Counter({('H',2):2,('O',0):1})and not m['has3D'])
 if m['has3D']:
  cached=qual[key]['cached_identity'];old=read(O/'reference-snapshots/models'/(cached+'-3d.json'));ck(rel+' exact cached arrays',m['atoms']==old['atoms']and m['bonds']==old['bonds']);ck(rel+' Angstrom units',m['coordinateUnits'].lower()in['angstrom','angstroms','å']);ck(rel+' no other-paper source type',not any(x in m.get('sourceType','').lower()for x in['ghosh','norberg','lian','ribeiro','sommer']))
  for i,a in enumerate(m['atoms']):
   for j,b in enumerate(m['atoms'][i+1:],i+1):ck(rel+' gross overlap '+str(i)+'/'+str(j),math.dist([a[k]for k in['x','y','z']],[b[k]for k in['x','y','z']])>.45)
 else:ck(rel+' 2Dunitsandrotation',m['coordinateUnits']=='arbitrary drawing units'and not m['allowRotation']and all(a['z']==0 for a in m['atoms']))
def refs(qs,label):
 for i,q in enumerate(qs):ck(label+' exact quantity '+str(i),ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
for row in slots:
 rid=row['record_id'];mid=row['material_id'];e=entries[row['registry_id']];ck(rid+'/'+mid+' material pointer',ptr(records[rid],row['json_pointer'])==row['canonical_identity']);ck(rid+'/'+mid+' source object',row['source_material']==sm[mid]);ck(rid+'/'+mid+' entry SHA',jsha(e)==row['entry_sha256']);ck(rid+'/'+mid+' dispatch',bindings['recordBindings'][rid][mid]==e['id']and bindings['bindingNotes'][rid][mid]==row);refs(row['quantity_links']+row['grade_context_links'],rid+'/'+mid)
for st in stocks:
 ck(st['stock_id']+' exact stock',ptr(records[st['record_id']],st['json_pointer'])==st['canonical_stock']);refs(st['concentration_links']+st['solution_quantity_links'],st['stock_id'])
 for co in st['components']:ck(st['stock_id']+'/'+co['material_id']+' component',ptr(records[st['record_id']],co['json_pointer'])['quantities']==co['source_quantities']);refs(co['quantity_links'],st['stock_id']+'/'+co['material_id'])
ck('No ODE or hexane isomer assignment',all(entries['matuhina2023-'+mid+'-reference']['depictionKind']=='symbolic_context'for mid in['ode','hexane']))
ck('Heavy water optical medium',entries['matuhina2023-heavy-water-reference']['provenance']['sourceMaterialId']=='heavy-water'and'not the NC dispersion solvent'in entries['matuhina2023-heavy-water-reference']['caption'])
ck('Water roles not merged',entries['matuhina2023-quench-water-reference']['caption']!=entries['matuhina2023-milliq-reference']['caption'])
allow={'schema':'mattersyn-molecule-public-allowlist/1','source_id':'matuhina2023','status':'private_unapproved_candidates','assets':[{'path':p,'sha256':h}for p,h in sorted(assets.items())],'exclusions':['reference-snapshots/**','contacts/**','previews/**','conformer-previews/**','stock-previews/**','source/canonical raw provenance and whole pages'],'binding_approved':False};(O/'public-asset-proposal.json').write_text(json.dumps(allow,indent=2)+'\n',encoding='utf8')
fails=[c for c in checks if not c['passed']];report={'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_checks'if not fails else'failed','check_count':len(checks),'checks':checks,'open_findings':fails,'counts':{'identities':28,'slots':55,'stocks':5,'components':15,'public_assets':len(assets),'models2d':10,'models3d':6},'independent_approval':False,'browser_approval':False};(O/'author-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:report[k]for k in['status','check_count','counts','open_findings']}));assert not fails
