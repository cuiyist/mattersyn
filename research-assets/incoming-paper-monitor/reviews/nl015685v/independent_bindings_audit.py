from pathlib import Path
import json,hashlib,collections,math
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def ck(n,v,d=''):C.append({'check':n,'passed':bool(v),'detail':d})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json')
new={e['id']:e for e in read(V/'registry-additions.json')['entries']};old={e['id']:e for e in read(S/'registry.json')['entries']}
R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};audited=read(B/'canonical-records-audit.json')['record_hashes']
expected={'cadmium-nitrate':'cadmium-nitrate-hydration-unspecified','water':'water','ammonia':'ammonia','sodium-citrate':'identity-besson-citrate','copolymer-host':'identity-besson-copolymer-host','ctab-host':'identity-besson-empty-film','h2s':'hydrogen-sulfide','cadmium-stock':'identity-besson-loading-solution','teos':'tetraethyl-orthosilicate','acidified-water':'identity-besson-acidified-water','ethanol':'ethanol','ctab':'cetyltrimethylammonium-bromide','pyrex':'identity-besson-pyrex','air':'identity-besson-air','ctab-loaded':'identity-besson-ctab-cds-film','copolymer-loaded':'identity-besson-copolymer-cds-film','cds-colloid':'identity-besson-cds-colloid','silicon':'identity-besson-silicon','mesoporous-film':'identity-besson-pl-host','cadmium-adsorbed-film':'identity-besson-cd-loaded-film'}
equiv={('Si(OC2H5)4','C8H20O4Si'),('Cd(NO3)2','CdN2O6'),('NH3','H3N'),(None,'H2O')}
ck('All 12 record groups',set(bind['recordBindings'])==set(R));ck('41 material slots',sum(len(v) for v in bind['recordBindings'].values())==41)
for rid,r in R.items():
 ck(rid+'/audited bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid])
 row=bind['recordBindings'][rid];ck(rid+'/complete material slots',set(row)=={m['id'] for m in r['materials']})
 for m in r['materials']:
  e=new.get(row[m['id']]) or old[row[m['id']]];ck(rid+'/'+m['id']+'/correct source identity',row[m['id']]==expected[m['id']])
  ck(rid+'/'+m['id']+'/formula identity or explicit solvent scope',m['formula']==e['formula'] or (m['formula'],e['formula']) in equiv)
  if m['id']=='acidified-water':ck(rid+'/acid unresolved','acid' in e['caption'].lower() and 'H2O'==e['formula'])
 ck(rid+'/reference-only note','no measured solution or crystal coordinates' in bind['bindingNotes'][rid])
ck('Three route-specific product references',prod['recordBindings']=={'besson-2002-copolymer-cds-loading':'identity-besson-copolymer-cds-film','besson-2002-ctab-cds-loading':'identity-besson-ctab-cds-film','besson-2002-ctab-silica-host':'identity-besson-empty-film'})
ck('Mesoscopic, not atomic products','Mesoscopic' in prod['scope'] and 'no supplied atomic CIF' in prod['scope'])
for rid,eid in prod['recordBindings'].items():ck(rid+'/schematic only',new[eid]['model2dPath'] is None and new[eid]['model3dPath'] is None)
ck('Four generic molecular references only',set(reuse['entries'])=={'water','ethanol','ammonia','hydrogen-sulfide'})
ah={};formula={'water':{'H':2,'O':1},'ethanol':{'C':2,'H':6,'O':1},'ammonia':{'H':3,'N':1},'hydrogen-sulfide':{'H':2,'S':1}}
for rid,row in reuse['entries'].items():
 e=row['entry'];ck(rid+'/existing metadata exact',e==old[rid]);ck(rid+'/reference caption','reference' in e['caption'].lower() or 'no solution speciation' in e['caption'].lower())
 for k,h in row['assetHashes'].items():ah[e[k]]=sha(S/e[k]);ck(rid+'/'+k+'/asset hash',ah[e[k]]==h==e['assetHashes'][k])
 for dim in ('2d','3d'):
  m=read(S/e['model'+dim+'Path']);aa=m['atoms'];bb=m['bonds'];atoms=collections.Counter(a['element'] for a in aa);atoms['H']+=sum(a.get('implicitHydrogenCount',0) for a in aa)
  ck(rid+'/'+dim+'/atom formula',atoms==formula[rid]);ck(rid+'/'+dim+'/finite neutral atoms',all(a['formalCharge']==0 and all(math.isfinite(a[k]) for k in ('x','y','z')) for a in aa))
  ck(rid+'/'+dim+'/rotation semantics',m['has3D']==(dim=='3d') and m['allowRotation']==(dim=='3d'))
  ck(rid+'/'+dim+'/reference geometry scope','not measured' in m['caption'] or 'no solution speciation' in m['caption'].lower())
  for a in aa:
   val=sum(b['order'] for b in bb if a['index'] in (b['a'],b['b']))+a.get('implicitHydrogenCount',0)
   ck(rid+'/'+dim+'/valence '+str(a['index']),val=={'H':1,'C':4,'O':2,'N':3,'S':2}[a['element']])
  if rid=='ethanol':ck(rid+'/'+dim+'/O-C-C connectivity',{(min(b['a'],b['b']),max(b['a'],b['b'])) for b in bb if aa[b['a']]['element']!='H' and aa[b['b']]['element']!='H'}=={(0,1),(1,2)})
for k in ('ctab','copolymer'):
 r=R['besson-2002-'+k+'-cds-loading'];host=next(m for m in r['materials'] if m['id']==k+'-host');ck(k+'/host role and target distinguished',host['role']=='host_matrix' and r['intended_target']['host']['value']==host['name'])
manual=['All 41 record/material choices and three product cards were independently source-compared. Empty silica, Cd-adsorbed pre-H2S film and CdS-filled film are distinct, including both SIMS and XRD inputs.','CTAB and unknown triblock matrices retain separate host targets. Neither a generic SiO2 formula nor shared CdS/SiO2 descriptor makes their recipes identical.','Silicon-wafer PL host is not automatically a CTAB-host specimen. The reverse-micelle colloid is an optical comparator, not a new pore-confined sample.','Acidified-water H2O denotes solvent only; unspecified acid, citrate salt form, cadmium hydration and copolymer chemistry remain unresolved. TEOS and nitrate condensed versus expanded formulas are chemically equivalent identity representations.','Reused water, ethanol, ammonia and H2S metadata, all 12 file hashes and eight model graphs were inspected. Their generic coordinates are reference depictions only; prior source provenance is retained without importing an earlier recipe or assigning present solution speciation.','No Site edits, new external database lookups or browser rendering verification were performed. New molecular contact-sheet inspection is recorded in molecular-source-audit.json.']
fail=[x for x in C if not x['passed']]
out={'status':'passed' if not fail else 'failed','source_id':'besson2002','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':ah,'record_count':12,'material_binding_count':41,'product_binding_count':3,'reused_reference_count':4,'check_count':len(C),'checks':C,'failures':fail,'manual_review':manual,'site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'bindings-source-audit.md').write_text('# Besson 2002 binding source audit\n\n'+out['status']+f'; {len(C)} checks, {len(fail)} failures. 12 records, 41 material slots, three products and four reused references.\n\n'+'\n\n'.join(manual)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'check_count':len(C),'failures':fail}))
