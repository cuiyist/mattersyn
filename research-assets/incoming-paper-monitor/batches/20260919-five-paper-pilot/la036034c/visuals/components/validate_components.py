"""Author checks only; distinct scientific and binding audit is still required."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent.parent;R=B.parents[3]
sys.path.insert(0,str(R/'rdkit-runtime'));sys.path.insert(0,str(R/'corpus-20260917/runtime'))
import json,hashlib,math,re,datetime,xml.etree.ElementTree as ET,collections
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from PIL import Image,ImageDraw,ImageFont
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(ok,label):checks.append({'passed':bool(ok),'check':label})
def ptr(o,p):
 for b in p.strip('/').split('/'):o=o[int(b)] if isinstance(o,list) else o[b.replace('~1','/').replace('~0','~')]
 return o
def formula_counts(f):return collections.Counter({a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',f)})
registry=read(O/'registry-additions.json');entries=registry['entries'];emap={e['id']:e for e in entries};slots=read(O/'source-slot-mapping.json')['slots'];bindings=read(O/'molecule-bindings-proposal.json');stocks=read(O/'stock-component-selectors.json')['stocks'];plan=read(B/'visual-reuse-plan.json')
check(len(entries)==len(emap)==42,'Exactly 42 distinct identity references');check(len(slots)==61,'Exactly 61 source slots');check(len(stocks)==2,'Exactly two canonical stock selectors')
for p,digest in read(O/'input-hashes-before.json').items():check(sha(p)==digest,'Unchanged frozen input: '+p)
check(set((s['record_id'],s['material_id']) for s in slots)==set((s['record_id'],s['material_id']) for s in plan['material_slots']),'Slot coverage equals frozen plan; no formula-based expansion')
for row in read(O/'candidate-reuse-inputs.json'):
 for a in row['asset_checks']:check(sha(a['path'])==a['sha256']==sha(a['snapshot']),'Unchanged current and snapshotted reuse asset: '+a['path'])
for e in entries:
 check(not e['binding_approved'] and not e['published'] and not e['eligible_training'] and e['independentScientificAudit']=='pending',e['id']+' remains unapproved/private')
 check(e['provenance']['sourceSpecificIdentity'] in plan['identity_plans'],e['id']+' explicit source identity')
 for field,digest in e['assetHashes'].items():check(sha(O/e[field])==digest,e['id']+' asset hash '+field)
 svg=(O/e['svgPath']).read_text(encoding='utf-8');root=ET.fromstring(svg);check(root.attrib['viewBox']=='0 0 960 470',e['id']+' SVG geometry')
 check('<script' not in svg and 'http://' not in svg.replace('http://www.w3.org/2000/svg',''),e['id']+' self-contained SVG without remote resources')
 check(bool(root.find('{http://www.w3.org/2000/svg}title').text),e['id']+' accessible SVG title')
 for forbidden in ['Veinot','Gu et','80.5%','Fisher','ES-OMCVD','Milli-Q']:
  check(forbidden not in svg and forbidden not in e['caption'],e['id']+' no inherited displayed '+forbidden)
 cat=plan['identity_plans'][e['provenance']['sourceSpecificIdentity']]['category']
 if cat in ['polymer_identity_schematic_needed','cds_specimen_identity_needed','protein_or_conjugate_identity_needed','support_depiction_needed','support_template_candidate','unknown_identity_placeholder'] or e['provenance']['sourceSpecificIdentity'] in ['hcl','potassium-naphthalene']:
  check(not e['model2dPath'] and not e['model3dPath'],e['id']+' no unsupported atomistic model')
 for field,dim in [('model2dPath',2),('model3dPath',3)]:
  if not e.get(field):continue
  m=read(O/e[field]);aa=m['atoms'];bb=m['bonds'];n=len(aa)
  check(m['id']==e['id'] and m['has3D']==(dim==3) and m['allowRotation']==(dim==3),e['id']+f' {dim}D identity/dimension')
  check(m['coordinateUnits']==('angstrom' if dim==3 else 'drawing units'),e['id']+f' {dim}D coordinate units')
  check(all(a.get('index',i)==i for i,a in enumerate(aa)),e['id']+f' {dim}D zero-based atom indices')
  count=collections.Counter()
  for i,a in enumerate(aa):
   count[a.get('element',a.get('elem'))]+=1;count['H']+=a.get('implicitHydrogenCount',0)
   check(all(isinstance(a[k],(int,float)) and math.isfinite(a[k]) for k in ['x','y','z']),e['id']+f' {dim}D finite atom {i}')
   if dim==2:check(a['z']==0,e['id']+f' planar atom {i}')
  check(+count==+formula_counts(e['formula']),e['id']+f' {dim}D formula atom/H counts')
  seen=set()
  for i,b in enumerate(bb):
   pair=tuple(sorted([b['a'],b['b']]))
   check(0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'] and pair not in seen,e['id']+f' {dim}D valid unique bond {i}');seen.add(pair)
   check(b['order'] in [1,1.5,2,3],e['id']+f' {dim}D bond order {i}')
   if dim==3:
    d=math.dist([aa[b['a']][k] for k in ['x','y','z']],[aa[b['b']][k] for k in ['x','y','z']]);ish=aa[b['a']].get('element')=='H' or aa[b['b']].get('element')=='H';lo,hi=(.65,1.6) if ish else (.9,2.1)
    check(lo<d<hi,e['id']+f' 3D plausible bond {i} ({d:.3f} Å)')
  for g in m.get('functionalGroups',[]):
   check(all(isinstance(a,int) and 0<=a<n for a in g['atomIndices']),e['id']+f' {dim}D group atom indices: '+g['label'])
   check(all(isinstance(b,int) and 0<=b<len(bb) and bb[b]['a'] in g['atomIndices'] and bb[b]['b'] in g['atomIndices'] for b in g['bondIndices']),e['id']+f' {dim}D group bonds: '+g['label'])
  if dim==3:
   for a in range(n):
    for b in range(a+1,n):
     if (a,b) in seen:continue
     d=math.dist([aa[a][k] for k in ['x','y','z']],[aa[b][k] for k in ['x','y','z']]);check(d>.55,e['id']+f' no gross 3D atom overlap {a}/{b}')
   if 'reusedRegistryId' not in e['provenance']:
    stem=Path(e['provenance']['source2dPath']).name.replace('-2d.sdf','');raw=Chem.MolFromMolFile(str(O/'raw'/f'{stem}-3d.sdf'),removeHs=False)
    check(raw.GetNumAtoms()==n,e['id']+' fresh 3D atom count matches retained authoritative SDF')
    c=raw.GetConformer()
    check(all(math.dist((a['x'],a['y'],a['z']),tuple(c.GetAtomPosition(i)))<1e-12 for i,a in enumerate(aa)),e['id']+' fresh 3D coordinates exactly match authoritative SDF')
  if 'reusedRegistryId' in e['provenance']:
   old=read(O/'reference-base'/f'{e["provenance"]["reusedRegistryId"]}-entry.json');before=read(O/'reference-base'/Path(old[field]).name)
   check(m['atoms']==before['atoms'] and m['bonds']==before['bonds'],e['id']+f' {dim}D reused graph/coordinates unchanged')
   for key in ['method','conformerGeneration','coordinateSource','computedBy']:
    if key in before:check(m[key]==before[key],e['id']+f' {dim}D retained computation provenance '+key)
# Chemistry-specific identity boundaries.
for mid,charge_counts,atoms,bond_count in [('na2s',[-2,1,1],{'S':1,'Na':2},0),('cdcl2',[-1,-1,2],{'Cd':1,'Cl':2},0),('nacl',[-1,1],{'Na':1,'Cl':1},0)]:
 m=read(O/emap['nagasaki2004-'+mid+'-reference']['model2dPath']);check(sorted(a.get('formalCharge',0) for a in m['atoms'])==charge_counts,mid+' exact formal charges');check(dict(collections.Counter(a['element'] for a in m['atoms']))==atoms and len(m['bonds'])==bond_count,mid+' stoichiometry, no hydrate or metal-ion bond')
m=read(O/emap['nagasaki2004-nabh4-reference']['model2dPath']);check(sorted(a['formalCharge'] for a in m['atoms'])==[-1,0,0,0,0,1] and len(m['bonds'])==4,'Borohydride: four B–H bonds plus disconnected Na+');check(all(m['atoms'][b['a']]['element']!='Na' and m['atoms'][b['b']]['element']!='Na' for b in m['bonds']),'No invented Na–B bond')
pdp=read(O/emap['nagasaki2004-pdp-reference']['model2dPath']);check(sum(a['formalCharge'] for a in pdp['atoms'])==0 and not emap['nagasaki2004-pdp-reference']['model3dPath'],'PDP formal stoichiometry and no ion-pair 3D')
for stem in ['ethylene-oxide','ama','pdp-alcohol','biocytin-hydrazide']:
 props=read(O/'raw'/f'{stem}-properties.json')['PropertyTable']['Properties'][0];m2=Chem.MolFromMolFile(str(O/'raw'/f'{stem}-2d.sdf'),removeHs=True);m3=Chem.MolFromMolFile(str(O/'raw'/f'{stem}-3d.sdf'),removeHs=True);target=Chem.MolFromSmiles(props['SMILES']);check(Chem.MolToSmiles(m2,True)==Chem.MolToSmiles(target,True)==Chem.MolToSmiles(m3,True),stem+' cached 2D/3D isomeric connectivity agrees with properties')
 if stem=='biocytin-hydrazide':check(len(Chem.FindMolChiralCenters(target,includeUnassigned=True))==4,'Biocytin hydrazide reference retains four specified stereocenters')
for s in slots:
 rec=read(B/'canonical-drafts'/f'{s["record_id"]}.json');m=ptr(rec,s['canonical_material_pointer']);check(m==s['canonical_material'],s['record_id']+'/'+s['material_id']+' exact canonical material snapshot');check(sha(B/'canonical-drafts'/f'{s["record_id"]}.json')==s['canonical_record_sha256'],s['record_id']+'/'+s['material_id']+' bound canonical hash')
 e=emap[s['registry_id']];note=bindings['bindingNotes'][s['record_id']][s['material_id']];check(bindings['recordBindings'][s['record_id']][s['material_id']]==e['id'],s['record_id']+'/'+s['material_id']+' explicit resolved binding');check(note['canonical_evidence']==m.get('evidence',[]) and note['source_name']==m['name'] and note['source_formula']==m.get('formula'),s['record_id']+'/'+s['material_id']+' source identity/evidence preserved');check(not note['binding_approved'],s['record_id']+'/'+s['material_id']+' binding audit pending')
for stock in stocks:
 r=read(B/'canonical-drafts'/f'{stock["record_id"]}.json');original=ptr(r,stock['canonical_pointer']);check(original['concentrations']==stock['concentrations'] and original['scope']==stock['scope'],stock['stock_id']+' exact concentration and scope');check([c['canonical_component'] for c in stock['components']]==original['components'],stock['stock_id']+' exact component quantities');check(all(c['registry_id'] in emap for c in stock['components']),stock['stock_id']+' all selectors resolve')
aqueous=next(s for s in stocks if s['stock_id']=='aqueous-polymer-stock');cq=aqueous['concentrations']['amine_group_concentration'];check(cq['value']==.000308 and cq['unit']=='mol/L of amine groups' and 'Not whole-polymer-chain molarity' in cq['qualifier'],'Amine concentration basis is not relabeled polymer-chain molarity')
# Preserve raw chemical-reference files and produce explicit 3D projection previews.
for row in read(O/'reference-retrieval.json'):
 if row['status']=='retrieved':check(sha(row['path'])==row['sha256'],'Cached primary chemical reference hash: '+row['name']+'/'+row['kind'])
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);colors={'C':'#606f78','H':'#c4cbd0','O':'#be5d66','N':'#557bc7','S':'#ba922b'}
for e in entries:
 if not e['model3dPath']:continue
 m=read(O/e['model3dPath']);img=Image.new('RGB',(1200,450),'white');d=ImageDraw.Draw(img)
 for vi,axes in enumerate([('x','y'),('x','z'),('y','z')]):
  xs=[a[axes[0]] for a in m['atoms']];ys=[a[axes[1]] for a in m['atoms']];sc=min(330/max(max(xs)-min(xs),1),285/max(max(ys)-min(ys),1));cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
  pts=[(vi*400+200+(a[axes[0]]-cx)*sc,220-(a[axes[1]]-cy)*sc) for a in m['atoms']]
  d.text((vi*400+18,20),e['name'],font=font,fill='#264a5f');d.text((vi*400+18,47),'Reference projection '+''.join(axes).upper(),font=font,fill='#617583')
  for b in m['bonds']:d.line([pts[b['a']],pts[b['b']]],fill='#71818b',width=4)
  for i,a in enumerate(m['atoms']):
   x,y=pts[i];r=5 if a['element']=='H' else 9;d.ellipse((x-r,y-r,x+r,y+r),fill=colors[a['element']],outline='#5d7480')
  d.text((vi*400+18,417),'Not a measured solution conformation',font=font,fill='#617583')
 img.save(O/'review'/f'{e["id"]}-3d-projections.png')
failed=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-component-author-validation/1','status':'passed' if not failed else 'failed','scope':'Author consistency checks only; not independent scientific, binding, integration or browser approval.','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':{'entries':len(entries),'slots':len(slots),'stocks':len(stocks),'checks':len(checks),'failures':len(failed)},'failures':failed,'checks':checks,'bound_files':{str(p):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['author-validation.json','package-freeze.json']},'all_downstream_approval_flags_false':True}
write(O/'author-validation.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failed},ensure_ascii=False,indent=2));sys.exit(bool(failed))
