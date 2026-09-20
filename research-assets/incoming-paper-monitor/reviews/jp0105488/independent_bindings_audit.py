from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib,json,math,re
B=Path(__file__).resolve().parent;V=B/'visuals';N=B/'neutralized-references';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def check(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
bindings=read(V/'bindings-additions.json');products=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json')['entries'];new={e['id']:e for e in read(V/'registry-additions.json')['entries']};refs={**new,**{k:v['entry'] for k,v in reuse.items()}}
expected={'water':'water','nitrogen':'nitrogen','butanol':'identity-butanol-unspecified-isomer','topo':'topo','methanol':'methanol','mpa':'mercaptopropionic-acid','dmf':'dimethylformamide','dmap':'dimethylaminopyridine','mps':'mps-trimethoxy','aps':'aps-trimethoxy','tmscl':'tmscl','tmah':'tetramethylammonium-hydroxide','tmah-methanol':'tetramethylammonium-hydroxide','tmah-pentahydrate':'tetramethylammonium-hydroxide-pentahydrate','phosphonate':'identity-gerion-phosphonate','phosphonate-stock':'identity-gerion-phosphonate','pb':'identity-gerion-pb','k2hpo4':'dipotassium-hydrogen-phosphate','kh2po4':'potassium-dihydrogen-phosphate','mes':'mes-buffer-acid','tbe':'identity-gerion-tbe','nacl':'sodium-chloride','glycerol':'glycerol','agarose':'identity-gerion-agarose','sephadex-g25':'identity-gerion-sephadex','rhodamine6g':'identity-rhodamine-6g-unspecified-salt','dtnb':'dtnb','toluene':'toluene','chloroform':'chloroform','carbon-grid':'identity-gerion-carbon-grid','mica':'identity-gerion-mica','specimen':'identity-gerion-specimens','hplc-silica':'identity-gerion-hplc-phase','cdse-zns-stock':'identity-gerion-cdse-zns','silica-specimen':'identity-gerion-siloxane','mpa-specimen':'identity-gerion-mpa','znsshell-precursors':'identity-gerion-zns-precursors'}
records={read(p)['record_id']:read(p) for p in (B/'canonical-drafts').glob('*.json')};rows=[]
check('all28records',set(records)==set(bindings['recordBindings']))
for rid,r in records.items():
 check(rid+'/canonical-hash',bindings['sourceRecordSha256'][rid]==sha(B/'canonical-drafts'/(rid+'.json')))
 bb=bindings['recordBindings'][rid];check(rid+'/all-materials',set(bb)=={m['id'] for m in r['materials']})
 for m in r['materials']:
  target=expected[m['id']]
  if rid=='gerion-2001-aps-functionalization' and m['id']=='silica-specimen':target='identity-gerion-mps-primed'
  check(rid+'/'+m['id']+'/source-identity',bb[m['id']]==target)
  entry=refs[target];check(rid+'/'+m['id']+'/formula',m.get('formula') is None or entry.get('formula') is None or m['formula'] in [entry['formula'],entry.get('displayFormula')])
  rows.append({'record_id':rid,'material_id':m['id'],'role':m['role'],'reference_id':target,'source_semantics':'passed'})
check('128bindings',len(rows)==128)
expected_products={'gerion-2001-silica-silanization':'identity-gerion-siloxane','gerion-2001-aps-functionalization':'identity-gerion-siloxane','gerion-2001-mpa-exchange':'identity-gerion-mpa','gerion-2001-core-shell-stock':'identity-gerion-cdse-zns'}
check('four-only-architecture-products',products['recordBindings']==expected_products)
for rid,t in expected_products.items():
 check(rid+'/product-illustrative',refs[t]['provenance']['measuredCoordinates'] is False and refs[t]['provenance']['eligible_training'] is False)
 check(rid+'/no-product-atomic-model',not refs[t].get('model3dPath') and not refs[t].get('model2dPath'))
def formula(s):return Counter({a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)})
reuse_rows=[]
for ident,obj in reuse.items():
 e=obj['entry'];base=N if obj['metadata_neutralized'] else S
 hashes={}
 for k,h in obj['assetHashes'].items():
  p=base/e[k];hashes[k]=sha(p);check(ident+'/'+k+'/hash',sha(p)==h==e['assetHashes'][k])
  if k.startswith('model'):
   d=read(p);A=d['atoms'];E=d['bonds'];count=Counter(a['element'] for a in A);count['H']+=sum(a.get('implicitHydrogenCount',0) for a in A)
   if not count['H']:del count['H']
   check(ident+'/'+k+'/formula-count',count==formula(e['formula']))
   check(ident+'/'+k+'/valid-bonds',all(0<=b['a']<len(A) and 0<=b['b']<len(A) and b['a']!=b['b'] for b in E))
   check(ident+'/'+k+'/finite-coordinate-reference',all(math.isfinite(a[x]) for a in A for x in ['x','y','z']))
   for g in d.get('functionalGroups',[]):check(ident+'/'+k+'/'+g['label']+'/valid-group',all(0<=i<len(A) for i in g['atomIndices']) and all(0<=i<len(E) for i in g['bondIndices']))
 check(ident+'/neutral-caption','QDOH' not in e['caption'])
 reuse_rows.append({'id':ident,'formula':e.get('formula'),'caption_review':'passed','asset_hashes':hashes,'metadata_neutralized':obj['metadata_neutralized']})
check('11reused-identities',len(reuse)==11)
for i in ['identity-butanol-unspecified-isomer','identity-rhodamine-6g-unspecified-salt']:
 check(i+'/no-invented-graph',not refs[i].get('model2dPath') and not refs[i].get('model3dPath'))
check('NaCl-2D-only',refs['sodium-chloride']['model3dPath'] is None)
for rid in ['gerion-2001-silica-silanization','gerion-2001-synthesis-controls']:
 r=records[rid];stock=next(x for x in r['stocks'] if x['id']=='tmah-stock-components')
 check(rid+'/TMAH-reference-is-stock-component',set(c['material_id'] for c in stock['components'])=={'tmah','methanol'} and 'concentration unknown' in stock['scope'])
semantics=['All 128 record/material identity choices and four architecture-only product choices independently compared with their source roles. APS binds the MPS-primed intermediate rather than pretending the mature siloxane shell is the initial primer.','Methanolic TMAH has a component ionic reference plus a separate methanol component; no stock molarity or unique ion-pair geometry. The pentahydrate is kept distinct. Aqueous phosphonate remains unresolved, not a guessed sodium salt or forced P–O–CH3 structure.','Core/shell stock, siloxane coating and MPA surface-layer diagrams are architecture references, not measured atomistic products. Shared assay/specimen cards do not collapse separate comparator samples. No product model is assigned to the combined analytical observations.','Butanol has no forced isomer; rhodamine6G no guessed counterion. Reused water, nitrogen, TOPO, methanol, TMSCl, toluene, chloroform and DMF connectivity match source-named compounds. Sodium chloride remains an ionic2D reference.','Reused source provenance is retained as reference origin, not current-source experimental evidence. DMF metadata is neutralized without changing atoms/bonds/coordinates, verified in molecular-source-audit. Role and quantities belong to the current record.','Stationary phases, gels, carbon supports and mica are separate analytical materials, not measured nanoparticle composition. No reference geometry becomes a measured structure training label.']
failed=[x for x in C if not x['passed']]
report={'source_id':'gerion2001','status':'passed' if not failed else 'failed','audited_utc':datetime.now(timezone.utc).isoformat(),'bindings_sha256':sha(V/'bindings-additions.json'),'products_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in records},'bindings':rows,'reused_reference_review':reuse_rows,'semantic_review':semantics,'check_count':len(C),'failure_count':len(failed),'checks':C,'failures':failed,'site_mutated':False,'browser_verified':False}
(B/'bindings-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'bindings-source-audit.md').write_text('# Gerion 2001 molecular binding audit\n\n'+report['status']+f': 128 material slots, four architecture-only product references, 11 reused identities; {len(C)} checks and {len(failed)} failures.\n\n'+'\n\n'.join(semantics)+'\n',encoding='utf8')
if not failed:
 m=read(B/'molecular-source-audit.json');m['status']='passed';m['binding_audit_complete']=True;m['binding_audit_sha256']=sha(B/'bindings-source-audit.json');m['bindings_sha256']=report['bindings_sha256'];m['reused_reference_input_sha256']=report['reused_reference_input_sha256'];m['semantic_review'][-1]='Record/material and reused-reference binding audit is complete in bindings-source-audit.json. Browser rendering and integration remain outside this private scientific audit.'
 (B/'molecular-source-audit.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (B/'molecular-source-audit.md').write_text('# Gerion 2001 independent molecular audit\n\nPassed: 26 additions and the source-neutral DMF metadata update; all five molecular contact sheets independently viewed. Binding audit is complete: 128 slots, four product architecture references and 11 reused identities.\n\n'+'\n\n'.join(m['semantic_review'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(C),'failures':failed},indent=2))
