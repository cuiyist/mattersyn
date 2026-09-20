"""Author checks against raw chemical references and frozen canonical inputs."""
import json, hashlib, math, collections, re, datetime
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(ok,label):checks.append({'passed':bool(ok),'check':label})
def formula(m):
 c=collections.Counter(a['element'] for a in m['atoms']);c['H']+=sum(a.get('implicitHydrogenCount',0) for a in m['atoms']);return {e:n for e,n in c.items() if n}
def raw_sdf(p):
 lines=p.read_text().splitlines();n,k=int(lines[3][:3]),int(lines[3][3:6]);atoms=[]
 for line in lines[4:4+n]:atoms.append({'element':line[31:34].strip(),'x':float(line[:10]),'y':float(line[10:20]),'z':float(line[20:30]),'formalCharge':{0:0,1:3,2:2,3:1,5:-1,6:-2,7:-3}[int(line[36:39])]})
 bonds=[{'a':int(l[:3])-1,'b':int(l[3:6])-1,'order':int(l[6:9])} for l in lines[4+n:4+n+k]]
 for line in lines[4+n+k:]:
  if line.startswith('M  CHG'):
   ns=list(map(int,line[6:].split()))
   for i in range(ns[0]):atoms[ns[1+i*2]-1]['formalCharge']=ns[2+i*2]
 return {'atoms':atoms,'bonds':bonds}
def signature(m):
 ids=[i for i,a in enumerate(m['atoms']) if a['element']!='H'];imap={x:i for i,x in enumerate(ids)};h={i:m['atoms'][i].get('implicitHydrogenCount',0) for i in ids};edges=[]
 for b in m['bonds']:
  a,z=b['a'],b['b']
  if a in imap and z in imap:edges.append((*sorted((imap[a],imap[z])),b['order']))
  elif a in imap:h[a]+=1
  elif z in imap:h[z]+=1
 return ([(m['atoms'][i]['element'],m['atoms'][i]['formalCharge'],h[i]) for i in ids],sorted(edges))
def pointer(x,ptr):
 for p in ptr.lstrip('/').split('/'):x=x[int(p)] if isinstance(x,list) else x[p]
 return x
g=read(O/'generation-manifest.json');plan=read(B/'visual-preparation-plan.json');entries={e['id']:e for e in read(O/'registry-additions.json')['entries']}
for p,d in g['input_hashes'].items():ck(sha(Path(p))==d,'Immutable input '+p)
for p,d in g['files'].items():ck(sha(O/p)==d,'Generated file bound '+p)
geometry={}
for eid,slug,expected in [('reference-tin-ii-chloride-dihydrate','tin-dihydrate-ionic',{'Sn':1,'Cl':2,'O':2,'H':4}),('reference-nitric-acid','nitric-acid',{'H':1,'N':1,'O':3}),('reference-tetrabutylammonium-hydroxide','tbaoh',{'C':16,'H':37,'N':1,'O':1})]:
 e=entries[eid];raw=raw_sdf(O/'raw'/f'{slug}-pubchem-2d.sdf')
 for rep in ['2d','3d']:
  key='model'+rep+'Path'
  if not e.get(key):continue
  m=read(O/e[key]);a=m['atoms'];b=m['bonds'];tag=eid+' '+rep
  ck(formula(m)==expected,tag+' exact component formula including implicit H')
  ck(signature(m)==signature(raw),tag+' raw-SDF graph/charge/hydrogen agreement')
  ck(sum(x['formalCharge'] for x in a)==0,tag+' neutral complete formula unit')
  ck([x['index'] for x in a]==list(range(len(a))),tag+' index order')
  for x in a:ck(all(math.isfinite(x[k]) for k in ['x','y','z']),tag+f' finite atom {x["index"]}')
  for i,x in enumerate(b):ck(0<=x['a']<len(a) and 0<=x['b']<len(a) and x['a']!=x['b'] and x['order'] in [1,2],tag+f' valid bond {i}')
  for gg in m['functionalGroups']:
   ck(all(0<=i<len(a) for i in gg['atomIndices']) and all(0<=i<len(b) for i in gg['bondIndices']),tag+' functional-group bounds '+gg['label'])
  ck(m['functionalGroups']==e['functionalGroups'],tag+' registry groups equal model groups')
  if rep=='2d':ck(m['coordinateUnits']=='drawing units' and not m['has3D'] and not m['allowRotation'] and all(x['z']==0 for x in a),tag+' 2D semantics')
  else:
   rr=raw_sdf(O/'raw'/f'{slug}-pubchem-3d.sdf');heavy=[x for x in rr['atoms'] if x['element']!='H']
   ck(signature(m)==signature(rr),tag+' raw 3D connectivity')
   ck(len(heavy)==len(a) and all(abs(x[k]-y[k])<1e-7 for x,y in zip(a,heavy) for k in ['x','y','z']),tag+' exact original PubChem heavy-atom coordinates')
   ck(m['coordinateUnits']=='angstrom' and m['has3D'] and 'not measured' in m['caption'],tag+' computed reference scope')
   lengths=[math.dist([a[x['a']][k] for k in ['x','y','z']],[a[x['b']][k] for k in ['x','y','z']]) for x in b]
   ck(all(1.0<d<1.7 for d in lengths),tag+' plausible N-O reference lengths')
   ck(all(math.dist([a[i][k] for k in ['x','y','z']],[a[j][k] for k in ['x','y','z']])>.5 for i in range(len(a)) for j in range(i)),tag+' no gross atomic overlap')
   geometry[eid]={'bond_lengths_angstrom':lengths,'scope':'Recalculated from exact retained PubChem3D heavy-atom coordinates; no measured geometry claim.'}
 tin=eid.endswith('dihydrate')
 if tin:
  m=read(O/e['model2dPath']);ck(not m['bonds'] and sorted(x['element'] for x in m['atoms'])==['Cl','Cl','O','O','Sn'],'Hydrate has 5 disconnected heavy components')
  ck(sorted((x['element'],x['formalCharge'],x['implicitHydrogenCount']) for x in m['atoms'])==[('Cl',-1,0),('Cl',-1,0),('O',0,2),('O',0,2),('Sn',2,0)],'Hydrate valence/charge and both waters retained')
 if slug=='tbaoh':
  m=read(O/e['model2dPath']);a=m['atoms'];n=next(x['index'] for x in a if x['element']=='N');oh=next(x for x in a if x['element']=='O');adj={i:set() for i in range(len(a))}
  for x in m['bonds']:adj[x['a']].add(x['b']);adj[x['b']].add(x['a'])
  ck(oh['formalCharge']==-1 and oh['implicitHydrogenCount']==1 and not adj[oh['index']] and all(x['element']!='Br' for x in a),'OH− not Br−, disconnected hydroxide component')
  ck(len(adj[n])==4 and a[n]['formalCharge']==1,'TBA quaternary N+')
  sizes=[]
  for start in adj[n]:
   seen={n};todo=[start];chain=[]
   while todo:
    i=todo.pop()
    if i in seen:continue
    seen.add(i);chain.append(i);todo.extend(adj[i]-seen)
   ck(all(a[i]['element']=='C' and len(adj[i])<=2 for i in chain),'TBA straight saturated carbon branch')
   sizes.append(len(chain))
  ck(sizes==[4]*4,'Four n-butyl chains exactly')
  ck(not e.get('model3dPath'),'No invented salt/solvent 3D')
for eid in ['identity-ribeiro-carbon-copper-grid','identity-ribeiro-proposed-tin-hydroxide','identity-ribeiro-sno2-colloid']:
 e=entries[eid];ck(not e['model2dPath'] and not e['model3dPath'] and not e['functionalGroups'],eid+' no fabricated molecule or coordinates');ck(e['sourceUrls']==['https://doi.org/10.1021/jp0473669'],eid+' own source provenance')
bindings=read(O/'molecule-bindings-proposal.json');slots=bindings['slots']
ck(len(slots)==13 and len({(x['record_id'],x['json_pointer']) for x in slots})==13,'13 unique source slot proposals')
for x in slots:
 r=read(B/'canonical-drafts'/f'{x["record_id"]}.json');m=pointer(r,x['json_pointer'])
 ck(m['id']==x['source_material_id'] and m['name']==x['source_name'] and m['evidence']==x['canonical_evidence'] and m['quantities']==x['canonical_quantities'],'Source exact '+x['record_id']+x['json_pointer'])
 ck(not x['binding_approved'] and x['independent_scientific_audit']=='pending','Separate audit gate '+x['record_id']+x['json_pointer'])
 ck(x['registry_id'] in entries or x['registry_id'] in ['ethanol','water'],'Known registry proposal '+x['source_material_id'])
ck({x['registry_id'] for x in slots if x['source_material_id']=='sno2-colloid'}=={'identity-ribeiro-sno2-colloid'} and len([x for x in slots if x['source_material_id']=='sno2-colloid'])==5,'Shared composition icon keeps five distinct slot bindings')
waters=[x for x in slots if x['registry_id']=='water'];ck(len(waters)==2 and len({x['source_material_id'] for x in waters})==2,'Separate hydrolysis and dialysis water roles')
ck('grade is unreported' in next(x for x in waters if x['source_material_id']=='hydrolysis-water')['display_scope'],'Hydrolysis water no grade inheritance')
c=read(O/'component-view-proposal.json');ck(len(c['components'])==3 and c['no_new_canonical_stocks_created'] is True,'Three separate component contexts; no invented stock records')
for ctx in c['components']:
 r=read(B/'canonical-drafts'/f'{ctx["canonical_record_id"]}.json');ptr=ctx.get('canonical_stock_pointer') or ctx['canonical_material_pointer'];ck(bool(pointer(r,ptr)),ctx['context']+' resolves to canonical context')
 ck(all(x['registry_id'] in entries or x['registry_id'] in ['water','ethanol'] for x in ctx['components']),ctx['context']+' valid component identities')
ck(not any(x['binding_approved'] for x in slots),'No final source bindings approved')
for p,d in g['input_hashes'].items():ck(sha(Path(p))==d,'Input unchanged at end '+p)
fail=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-visual-author-validation/1','source_id':'ribeiro2004','author':'/root/backlog_eta','status':'passed_author_checks' if not fail else 'failed','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'failures':fail,'counts':{'checks':len(checks),'failures':len(fail),'new_entries':6,'new_models':4,'new_svg_previews':6,'material_slots':13,'component_contexts':3},'geometry_checks':geometry,'actual_visual_inspection':{'inspected_all_six_previews':True,'tin_initial_overlap_corrected':'Initial automatic disconnected layout made water labels touch. Final component-card SVG and model coordinate spacing separate all five components. The corrected final tin preview was actually inspected.','scope':'Author inspection, not independent audit or browser testing.'},'generation_manifest_sha256':sha(O/'generation-manifest.json'),'checker_sha256':sha(Path(__file__)),'independent_scientific_audit':'pending','site_modified':False}
(O/'author-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'checks':len(checks),'failures':fail,'sha256':sha(O/'author-validation.json')},indent=2));raise SystemExit(bool(fail))
