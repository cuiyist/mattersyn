"""Persisted private author checks, not an independent scientific audit."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,math,sys,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4]
sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t]
 return x
checks=[]
def ck(label,value):checks.append({'check':label,'passed':bool(value)})
inp=read(O/'input-bindings.json');reg=read(O/'registry-additions.json');ents={e['id']:e for e in reg['entries']};slots=read(O/'material-slot-map.json')['slots'];stocks=read(O/'stock-component-map.json')['stocks'];bindings=read(O/'bindings-proposal.json')
records={}
for p,h in inp.get('canonical_records',{}).items():ck('Canonical immutable '+p,sha(p)==h);r=read(p);records[r['record_id']]=r
for p,h in inp['inputs'].items():ck('Input immutable '+p,sha(p)==h)
sf=read(P/'source-facts.json');source_mats={m['id']:m for m in sf['materials']}
ck('Identity inventory',set(e['provenance']['sourceMaterialId']for e in ents.values())==set(source_mats))
ck('Exact canonical slots',len(slots)==sum(len(r['materials'])for r in records.values())==62)
ck('Exact seven stocks/23 components',len(stocks)==7 and sum(len(s['components'])for s in stocks)==23)
asset_paths={}
for eid,e in ents.items():
 ck(eid+' all approval flags false',not e['binding_approved']and not e['published']and not e['eligible_training'])
 ck(eid+' source-bound formula',e['formula']==source_mats[e['provenance']['sourceMaterialId']]['source_formula_or_abbreviation'])
 ck(eid+' source-neutral display',not any(x in e['caption'].lower()for x in ['ghosh','lian','gu2004','70% oleylamine']))
 for k in ['svgPath','model2dPath','model3dPath']:
  if not e.get(k):continue
  p=O/e[k];ck(eid+' asset hash '+k,p.exists()and sha(p)==e['assetHashes'][k]);asset_paths[e[k]]=sha(p)
 if not e['model2dPath']:ck(eid+' symbolic no hidden3D',e['depictionKind']=='symbolic_context'and not e['model3dPath'])
 root=ET.parse(O/e['svgPath']).getroot();ck(eid+' SVG dimensions',root.attrib.get('viewBox')=='0 0 1100 700')
for rel,h in sorted(asset_paths.items()):
 if not rel.endswith('.json'):continue
 m=read(O/rel);rw=Chem.RWMol()
 for i,a in enumerate(m['atoms']):
  ck(rel+' atom index '+str(i),a['index']==i);ck(rel+' finite coordinate '+str(i),all(isinstance(a[x],(int,float))and math.isfinite(a[x])for x in ['x','y','z']))
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));atom.SetNoImplicit(True);atom.SetNumExplicitHs(a.get('implicitHydrogenCount',0));rw.AddAtom(atom)
 seen=set()
 for i,b in enumerate(m['bonds']):
  key=tuple(sorted((b['a'],b['b'])));valid=0<=key[0]<key[1]<len(m['atoms'])and key not in seen;ck(rel+' bond indices '+str(i),valid);seen.add(key)
  rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
  if m.get('has3D'):ck(rel+' reasonable reference bond '+str(i),.6<math.dist([m['atoms'][b['a']][k]for k in ['x','y','z']],[m['atoms'][b['b']][k]for k in ['x','y','z']])<1.8)
 mol=rw.GetMol();Chem.SanitizeMol(mol);expected=Chem.MolFromSmiles(m['connectivitySmiles']);ck(rel+' graph identity',Chem.MolToSmiles(Chem.RemoveHs(mol))==Chem.MolToSmiles(Chem.RemoveHs(expected)))
 ck(rel+' formula',rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(expected))
 for gi,g in enumerate(m['functionalGroups']):
  ck(rel+' group atoms '+str(gi),len(g['atomIndices'])==len(set(g['atomIndices']))and all(0<=i<len(m['atoms'])for i in g['atomIndices']))
  ck(rel+' group bonds '+str(gi),all(0<=i<len(m['bonds'])and m['bonds'][i]['a']in g['atomIndices']and m['bonds'][i]['b']in g['atomIndices']for i in g['bondIndices']))
 if 'zn-nitrate' in rel or 'al-nitrate' in rel:
  iszn='zn-nitrate'in rel;frags=Chem.GetMolFrags(mol,asMols=True);fs=Counter(Chem.MolToSmiles(f)for f in frags)
  ck(rel+' hydrate waters',fs['O']==(6 if iszn else 9));ck(rel+' nitrate stoichiometry',fs['O=[N+]([O-])[O-]']==(2 if iszn else 3));ck(rel+' net neutral',sum(a.GetFormalCharge()for a in mol.GetAtoms())==0)
  ck(rel+' no invented metal-ligand bonds',not any(m['atoms'][b['a']]['element']in ['Zn','Al']or m['atoms'][b['b']]['element']in ['Zn','Al']for b in m['bonds']))
 if m.get('has3D'):
  key='water'if'water'in rel else'ethanol';old=read(O/'reference-snapshots/models'/f'{key}-3d.json');ck(rel+' exact cached3D arrays',m['atoms']==old['atoms']and m['bonds']==old['bonds']);ck(rel+' retained computation provenance',m['conformerGeneration']==old['conformerGeneration']and m['method']==old['method'])
def refs_check(refs,label):
 for j,q in enumerate(refs):ck(label+' exact quantity '+str(j),ptr(records[q['record_id']],q['json_pointer'])==q['quantity'])
for row in slots:
 rid=row['record_id'];mid=row['material_id'];e=ents[row['registry_id']];key=rid+'/'+mid
 ck(key+' exact material',ptr(records[rid],row['json_pointer'])==row['canonical_identity']);ck(key+' source identity',row['source_material']==source_mats[mid]);ck(key+' registry entry hash',jsha(e)==row['entry_sha256']);ck(key+' dispatch',bindings['recordBindings'][rid][mid]==e['id']and bindings['bindingNotes'][rid][mid]==row)
 refs_check(row['quantity_links']+row['grade_context_links'],key)
for row in stocks:
 rid=row['record_id'];key=rid+'/'+row['stock_id'];ck(key+' exact stock',ptr(records[rid],row['json_pointer'])==row['canonical_stock'])
 refs_check(row['concentration_links']+row['solution_quantity_links'],key)
 for c in row['components']:
  ck(key+'/'+c['material_id']+' component pointer',ptr(records[rid],c['json_pointer'])['quantities']==c['source_quantities']);ck(key+'/'+c['material_id']+' material pointer',ptr(records[rid],c['material_json_pointer'])['id']==c['material_id']);refs_check(c['quantity_links'],key+'/'+c['material_id'])
 if row['stock_id']=='insitu-base-solutions':
  ck(key+' no postmix stock concentration',not row['concentrations']and len(row['solution_quantity_links'])==1 and row['solution_quantity_links'][0]['json_pointer'].endswith('naoh_solution_aliquot'))
 if row['stock_id']in ['mw-low-base','mw-middle-base','mw-high-base']:ck(key+' no repeated parent charges',all(not c['source_quantities']for c in row['components']))
allow={'schema':'mattersyn-molecule-public-allowlist/1','status':'private_unapproved_candidates','source_id':'sommer2020','assets':[{'path':k,'sha256':v}for k,v in sorted(asset_paths.items())],'exclusions':['Source PDFs, whole-page/text caches and all reference-snapshots remain private.','Stock previews, contact sheets, tests and source/canonical snapshots are private review aids.'],'binding_approved':False}
(O/'public-asset-proposal.json').write_text(json.dumps(allow,indent=2)+'\n',encoding='utf8')
fail=[x for x in checks if not x['passed']];report={'status':'passed_author_checks'if not fail else'failed','created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','check_count':len(checks),'checks':checks,'open_findings':fail,'counts':{'identities':len(ents),'slots':len(slots),'stocks':7,'stock_components':23,'public_assets':len(asset_paths)},'scope':'Author reference chemistry, pointers and immutable cached-array checks. Independent source/molecular and mounted-browser approval are not asserted.','independent_approval':False}
(O/'author-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:report[k]for k in ['status','check_count','counts','open_findings']}));assert not fail
