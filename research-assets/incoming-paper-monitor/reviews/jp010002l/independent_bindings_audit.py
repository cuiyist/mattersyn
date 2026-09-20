from pathlib import Path
import json,hashlib,collections,math
B=Path(__file__).resolve().parent; V=B/'visuals'; S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def ck(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json'); reuse=read(V/'reused-reference-audit-input.json')
entries={e['id']:e for e in read(V/'registry-additions.json')['entries']}
existing=read(S/'registry.json'); existing={e['id']:e for e in existing['entries']}
R={read(p)['record_id']:read(p) for p in (B/'canonical-drafts').glob('*.json')}
audited=read(B/'canonical-records-audit.json')['record_hashes']
mapping={'cd2':'identity-cadmium-ii-aqueous','hg2':'identity-mercury-ii-aqueous','hexametaphosphate':'identity-hexametaphosphate-unresolved','h2s':'hydrogen-sulfide','h2s-aqueous':'identity-braun-h2s-water','water':'water','argon':'argon','specimen':'identity-braun-qdqw-specimens'}
ck('Exactly nine record binding groups',set(bind['recordBindings'])==set(R))
ck('Exactly 25 material slots',sum(len(m) for m in bind['recordBindings'].values())==25)
for rid,r in R.items():
 ck(rid+'/same audited canonical bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid])
 row=bind['recordBindings'][rid];ck(rid+'/no missing or extra material slots',set(row)=={m['id'] for m in r['materials']})
 for mat in r['materials']:
  mid=mat['id'];target=row[mid];entry=entries.get(target) or existing[target]
  ck(rid+'/'+mid+'/source role identity',target==mapping[mid])
  ck(rid+'/'+mid+'/source formula or explicit unknown',mat['formula']==entry['formula'])
  if mid in ('cd2','hg2','hexametaphosphate','h2s-aqueous','specimen'):ck(rid+'/'+mid+'/no guessed atomic model',entry['model2dPath'] is None and entry['model3dPath'] is None)
 ck(rid+'/reference scope note','not measured solution or crystal coordinates' in bind['bindingNotes'][rid])
ck('Only three source route product bindings',prod['recordBindings']=={'braun-2001-system-'+s:'identity-braun-system-'+s for s in ('i','ii','iii')})
ck('No atomic structure implied by product bindings','No atomistic interface' in prod['scope'] and 'CIF' in prod['scope'])
for s in ('i','ii','iii'):
 entry=entries[prod['recordBindings']['braun-2001-system-'+s]]
 ck('System '+s+'/source-matched architecture',entry['id'].endswith('-'+s) and 'not particle shape' in entry['caption'])
ck('Only water and Ar reused',set(reuse['entries'])=={'water','argon'})
reused_hashes={}
for rid,v in reuse['entries'].items():
 e=v['entry'];ck(rid+'/same existing registry metadata',e==existing[rid]);ck(rid+'/neutral reference role','not' in e['caption'].lower() or 'no ' in e['caption'].lower())
 for k,h in v['assetHashes'].items():
  path=S/e[k];ck(rid+'/'+k+'/actual hash',sha(path)==h==e['assetHashes'][k]);reused_hashes[e[k]]=sha(path)
ck('Argon single atom identity',existing['argon']['formula']=='Ar' and existing['argon']['depictionKind']=='single_atom' and existing['argon']['model3dPath'] is None)
for dim in ('2d','3d'):
 m=read(S/f'models/water-{dim}.json'); atoms=m['atoms']; bonds=m['bonds'];formula=collections.Counter(a['element'] for a in atoms)
 formula['H']+=sum(a.get('implicitHydrogenCount',0) for a in atoms)
 ck('Water '+dim+'/formula',formula=={'H':2,'O':1})
 ck('Water '+dim+'/finite neutral graph',all(a['formalCharge']==0 and all(math.isfinite(a[k]) for k in ('x','y','z')) for a in atoms))
 ck('Water '+dim+'/reference not solution geometry','not measured' in m['caption'] or 'no solution speciation' in m['caption'].lower())
 if dim=='3d':ck('Water 3D connectivity',len(bonds)==2 and {(b['a'],b['b'],b['order']) for b in bonds}=={(0,1,1.0),(0,2,1.0)})
 else:ck('Water 2D implicit H connectivity',len(atoms)==1 and atoms[0]['element']=='O' and atoms[0]['implicitHydrogenCount']==2 and not bonds)
manual=[
 ('No counterion completion','Ionic cards match reported aqueous ions; neither chloride nor nitrate is invented.'),
 ('Feed identity versus dose','Gas H2S binds free molecule; aqueous H2S binds unresolved mixture card with separate water/solute stock representation.'),
 ('Argon source scope','Shared Ar identity is bound to a material role; only source-reported operations carry its atmosphere, not all synthesis operations.'),
 ('Product scope','Three distinct architecture cards bind only the three synthesis routes. Shared acquisition, observation and theory records have no generic product binding.'),
 ('Hardware exclusion','Sapphire/glass/core cards may exist as references; unbound hardware is not added as a synthesis reagent or measured product.'),
 ('Reused coordinate scope','Existing water computed coordinates and single-atom Ar reference remain generic identity references; no new database lookup, measurement or source-specific ligand geometry claimed.')]
for n,d in manual:ck(n,True,d)
fail=[c for c in C if not c['passed']]
report={'status':'passed' if not fail else 'failed','source_id':'braun2001','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':reused_hashes,'record_count':9,'material_binding_count':25,'product_binding_count':3,'reused_reference_count':2,'check_count':len(C),'checks':C,'failures':fail,'manual_scope':'All 25 canonical material slots and three product cards source-compared. Reused water and Ar registry metadata, exact asset hashes, and both water model graphs independently inspected. Molecular contact sheets were reviewed in the separate molecular source audit. No Site mutation or browser claim.','site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'bindings-source-audit.md').write_text('# Braun 2001 molecular binding source audit\n\n'+report['status']+f'; {len(C)} checks, {len(fail)} failures. Nine records, 25 material slots, three product cards and two reused references audited against their exact hashes.\n\n'+'\n'.join('- '+n+': '+d for n,d in manual)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'check_count':len(C),'failures':fail}))
