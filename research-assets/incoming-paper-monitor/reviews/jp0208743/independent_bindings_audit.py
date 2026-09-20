from pathlib import Path
from collections import Counter
import json,hashlib,math
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def ck(n,v,d=''):C.append({'check':n,'passed':bool(v),'detail':d})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json')
new={e['id']:e for e in read(V/'registry-additions.json')['entries']};old={e['id']:e for e in read(S/'registry.json')['entries']}
R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};audited=read(B/'canonical-records-audit.json')['record_hashes']
expected={k:'identity-dantas-'+k for k in ['silica','zinc-oxide','alumina','lead-dioxide','boron-oxide','sulfur-source','aluminum-crucible','glass-host']+[x+'-specimen' for x in ['sg1','sg2','sg3','sg4','afm1','afm2']]};expected['sodium-carbonate']='sodium-carbonate'
ck('All 16 record groups',set(bind['recordBindings'])==set(R));ck('77 material slots',sum(len(v) for v in bind['recordBindings'].values())==77)
for rid,r in R.items():
 ck(rid+'/audited bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid])
 row=bind['recordBindings'][rid];ck(rid+'/complete material slots',set(row)=={m['id'] for m in r['materials']})
 for m in r['materials']:
  e=new.get(row[m['id']]) or old[row[m['id']]];ck(rid+'/'+m['id']+'/identity',row[m['id']]==expected[m['id']]);ck(rid+'/'+m['id']+'/formula',m['formula']==e['formula'] or (m['formula'],e['formula'])==('Na2CO3','CNa2O3'))
  if m['id']=='aluminum-crucible':ck(rid+'/equipment role not precursor',m['role']=='vessel')
  if m['id']=='sulfur-source':ck(rid+'/unknown sulfur identity',e['formula'] is None and e['model2dPath'] is None and e['model3dPath'] is None)
  if m['id']=='glass-host':ck(rid+'/multicomponent identity unresolved',e['formula'] is None)
 ck(rid+'/reference-only note',bool(bind['bindingNotes'][rid]))
expected_products={'dantas-2002-'+x:'identity-dantas-'+x+'-specimen' for x in ['sg1','sg2','sg3','sg4','afm1','afm2']}
ck('Six only source-specific products',prod['recordBindings']==expected_products)
for rid,eid in prod['recordBindings'].items():ck(rid+'/architecture not atomic',new[eid]['model2dPath'] is None and new[eid]['model3dPath'] is None and new[eid]['formula']=='PbS/glass')
ck('One reused reference',set(reuse['entries'])=={'sodium-carbonate'});entry=reuse['entries']['sodium-carbonate']['entry'];ck('Reused metadata exact',entry==old['sodium-carbonate']);ck('No inherited source recipe','not crystal packing, hydration coordination or solution speciation' in entry['caption'])
ah={}
for k,h in reuse['entries']['sodium-carbonate']['assetHashes'].items():ah[entry[k]]=sha(S/entry[k]);ck('sodium-carbonate/'+k+'/hash',ah[entry[k]]==h==entry['assetHashes'][k])
model=read(S/entry['model2dPath']);a=model['atoms'];bb=model['bonds']
ck('Carbonate 2D only',entry['model3dPath'] is None and not model['has3D'] and not model['allowRotation'])
ck('Carbonate counts',Counter(x['element'] for x in a)=={'Na':2,'C':1,'O':3})
ck('Carbonate total neutral charge',sum(x['formalCharge'] for x in a)==0)
ck('Two unbonded Na+',[(x['element'],x['formalCharge']) for x in a[:2]]==[('Na',1),('Na',1)] and not any(x['a']<2 or x['b']<2 for x in bb))
ck('Carbonate C(O−)2=O connectivity',{(x['a'],x['b'],x['order']) for x in bb}=={(2,5,1),(3,5,1),(4,5,2)})
ck('O charge pattern',[a[i]['formalCharge'] for i in [2,3,4]]==[-1,-1,0]);ck('Finite 2D coordinates',all(x['z']==0 and all(math.isfinite(x[k]) for k in ['x','y','z']) for x in a))
ck('Carbonate highlight exact',model['functionalGroups']==[{'label':'Carbonate','atomIndices':[2,3,4,5],'bondIndices':[0,1,2]}])
ck('Reused SVG is actual content','<svg' in (S/entry['svgPath']).read_text(encoding='utf8'))
manual=['All 77 material slots were independently matched to literal powder identities, unresolved sulfur input, source-described vessel or explicit SG/AFM specimens. PbO2 is not substituted by PbO; the precursor list is not exact final glass speciation.','Seven aluminum-crucible bindings remain vessel context, and the independently checked canonical delta removes the vessel from fused-glass material ancestry. No crucible incorporation or validation of literal aluminum at 1400 °C is implied.','Six product cards bind only the six named growth endpoints. Optical, microscopy and theoretical records receive no guessed generic measured-product structure. Architecture glyphs are illustrative and contain no measured atomic positions.','The reused sodium-carbonate entry is source-neutral and describes 2D ionic components only. Exact Na2CO3 atom counts, carbonate connectivity, net charge, two disconnected Na+ ions and carbonate highlighting were checked from actual model data. Existing file hashes and metadata match; no previous recipe conditions or solution speciation are imported.','New molecular visuals were independently inspected in molecular-source-audit.json. No Site mutation, external database lookup or browser verification is claimed.']
manual.append('The actual reused sodium-carbonate SVG was locally rasterized and visually inspected at visuals/review/reused-sodium-carbonate.png. Both Na+ labels are disconnected; both singly bonded O− labels and the double-bonded neutral oxygen are legible; carbonate-only coloring matches the graph. No 3D or lattice is implied.')
fail=[x for x in C if not x['passed']]
out={'status':'passed' if not fail else 'failed','source_id':'dantas2002','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':ah,'record_count':16,'material_binding_count':77,'product_binding_count':6,'reused_reference_count':1,'check_count':len(C),'checks':C,'failures':fail,'manual_review':manual,'site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'bindings-source-audit.md').write_text('# Dantas 2002 binding source audit\n\n'+out['status']+f'; {len(C)} checks, {len(fail)} failures. 16 records, 77 materials, six product cards and one reused reference.\n\n'+'\n\n'.join(manual)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail}))
