from pathlib import Path
from collections import Counter
import json,hashlib,math
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json')
new={e['id']:e for e in read(V/'registry-additions.json')['entries']};old={e['id']:e for e in read(S/'registry.json')['entries']}
R={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')};audited=read(B/'canonical-records-audit.json')['record_hashes']
ck('All18record groups',set(bind['recordBindings'])==set(R));ck('57materialslots',sum(len(v)for v in bind['recordBindings'].values())==57)
for rid,r in R.items():
 ck(rid+'/audited bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid]);row=bind['recordBindings'][rid];ck(rid+'/all slots',set(row)=={m['id']for m in r['materials']})
 for m in r['materials']:
  eid=row[m['id']];e=new.get(eid)or old[eid];ck(rid+'/'+m['id']+'/identity',eid==('water'if m['id']=='water'else'identity-yi-'+m['id']));ck(rid+'/'+m['id']+'/formula',m['formula']==e['formula'])
  if m['id']=='nanocrystal-specimen':ck(rid+'/no assumed800 sample','exact annealing condition or individual batch link is unassigned' in e['caption'])
 ck(rid+'/scope note',bool(bind['bindingNotes'][rid]))
expected={'yi-2002-anneal-'+str(t):'identity-yi-anneal-'+str(t)+'-specimen'for t in [600,700,800,900,1000]};expected['yi-2002-bulk']='identity-yi-bulk-specimen'
ck('Only six route product references',prod['recordBindings']==expected)
for rid,eid in expected.items():ck(rid+'/schematic only',new[eid]['model2dPath'] is None and new[eid]['model3dPath'] is None and new[eid]['provenance']['eligible_training'] is False)
ck('Exactly one reused water',set(reuse['entries'])=={'water'});e=reuse['entries']['water']['entry'];ck('Water metadata exact',e==old['water']);ck('Water source-neutral','no solution speciation' in e['caption'])
ah={}
for k,h in reuse['entries']['water']['assetHashes'].items():ah[e[k]]=sha(S/e[k]);ck('Water/'+k+'/hash',ah[e[k]]==h==e['assetHashes'][k])
d=read(S/e['model2dPath']);m=read(S/e['model3dPath']);a=m['atoms'];bb=m['bonds']
ck('2D implicit H2O',len(d['atoms'])==1 and d['atoms'][0]['element']=='O' and d['atoms'][0]['implicitHydrogenCount']==2 and d['bonds']==[])
ck('3D exact H2O',Counter(x['element']for x in a)=={'H':2,'O':1});ck('3D neutral',all(x['formalCharge']==0 for x in a));ck('Two OH bonds',{(x['a'],x['b'],x['order'])for x in bb}=={(0,1,1.0),(0,2,1.0)})
ck('Finite coordinates',all(all(math.isfinite(x[k])for k in ['x','y','z'])for x in a));ck('Computed not measured','Computed illustrative conformer, not measured' in m['caption'] and m['coordinateSource']=='local-rdkit')
dist=lambda i,j:math.sqrt(sum((a[i][k]-a[j][k])**2 for k in ['x','y','z']))
ck('Plausible OH reference lengths',all(.9<dist(0,i)<1.1 for i in [1,2]));ck('Not linear H2O',dist(1,2)<dist(0,1)+dist(0,2)-.05)
manual=['All57 material slots independently matched to source identities and actual record quantities. The four rare-earth/molybdate precursor inventories point to literal formula cards, not guessed aqueous species. Nitric acid and added deionized water remain separate; no source-specific role leaks through shared water.','Six product references bind only five anneal endpoints and the distinct1200 °C bulk route. Generic characterization uses the explicit thermal-unassigned nanocrystal reference. Stock solutions, grinding and comparison records have no fabricated product lattice or exact800 °C sample join.','The18 new references were independently visually and chemically audited in molecular-source-audit.json. Source nominal host formula does not establish measured dopant occupancy or phase purity for all samples.','Reused water metadata and all actual SVG/2D/3D hashes match. 2D oxygen has two implicit hydrogens; computed3D has neutral O and two H with exactly two OH bonds and finite bent coordinates. It is explicitly a local illustrative conformer, not measured geometry or a source hydrothermal configuration. Actual SVG was rendered and viewed in visuals/review/reused-water.png.','No Site edits, new downloads or browser verification performed.']
fail=[x for x in C if not x['passed']]
out={'status':'passed'if not fail else'failed','source_id':'yi2002','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':ah,'record_count':18,'material_binding_count':57,'product_binding_count':6,'reused_reference_count':1,'check_count':len(C),'checks':C,'failures':fail,'manual_review':manual,'site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'bindings-source-audit.md').write_text('# Yi2002 binding source audit\n\n'+out['status']+f'; {len(C)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail}))
