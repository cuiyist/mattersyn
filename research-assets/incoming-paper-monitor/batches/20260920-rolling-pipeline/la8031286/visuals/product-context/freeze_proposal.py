"""Freeze reviewed private author assets, without claiming independent approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (O/'package-freeze.json').exists()
b=read(O/'bindings.json');reg=read(O/'registry-additions.json');ctx=read(O/'product-contexts-additions.json');pub=read(O/'public-product-contexts-proposal.json');v=read(O/'author-validation.json');a=read(O/'public-asset-proposal.json');c=read(O/'consumer-execution-checks.json');renders=read(O/'render-receipt.json');m=read(b['canonical_manifest']['path'])
checks=[]
def ck(k,yes):checks.append({'check':k,'passed':bool(yes)});assert yes,k
def ptr(obj,s):
 for k in s.strip('/').split('/'):obj=obj[int(k)] if isinstance(obj,list) else obj[k.replace('~1','/').replace('~0','~')]
 return obj
ck('source record manifest exact',sha(b['canonical_manifest']['path'])==b['canonical_manifest']['sha256']=='8f420a118681abde88dc2c9019e44b91e621692fc15ce31131762673f6a43149')
ck('canonical package exact',sha(b['canonical_package']['path'])==b['canonical_package']['sha256']=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281')
ck('source freeze exact',sha(b['source_freeze']['path'])==b['source_freeze']['sha256'])
ck('source audit exact',sha(b['source_audit']['path'])==b['source_audit']['sha256'])
ck('source facts exact',sha(P/'source-facts.json')==b['source_facts_sha256']==read(b['source_audit']['path'])['source_facts_sha256'])
records={}
for x in m['records']:ck('unchanged record '+x['record_id'],sha(x['path'])==x['sha256']);records[x['record_id']]=read(x['path'])
actual=set((rid,i,p['sample_id']) for rid,r in records.items() for i,p in enumerate(r['products']))
account=set()
for row in b['bindings']+b['excluded_contexts']:
 k=(row['record_id'],int(row.get('product_pointer',row.get('canonical_product_pointer')).split('/')[-1]),row['sample_id'])
 ck('unique accounting '+str(k),k not in account);account.add(k)
ck('every canonical context has exactly one disposition',account==actual and len(actual)==156)
for row in b['bindings']:
 rid=row['record_id'];p=ptr(records[rid],row['product_pointer']);cr=next(x for x in ctx['recordContexts'][rid] if x['sample_id']==row['sample_id'])
 ck(rid+'/'+row['sample_id']+' product preserved',jsha(p)==row['product_sha256'] and p==cr['canonical_product_snapshot'])
 ck(rid+'/'+row['sample_id']+' no admissions',all(cr[k] is False for k in ['training_eligible','atomic_model','binding_approved','same_physical_batch_asserted']))
 for x in cr['canonical_measurement_links']:ck(rid+'/'+row['sample_id']+' measurement '+x['measurement_id'],ptr(records[x['record_id']],x['json_pointer'])==x['canonical_measurement'])
 public=next(x for x in pub['recordContexts'][rid] if x['sample_id']==row['sample_id'])
 ck(rid+'/'+row['sample_id']+' public scientific display preserved',all(public[k]==cr[k] for k in public))
for row in b['excluded_contexts']:ck('exclusion snapshot '+row['record_id']+'/'+row['sample_id'],ptr(records[row['record_id']],row['canonical_product_pointer'])==row['canonical_product_snapshot'])
ck('public data has no local paths','C:\\' not in json.dumps(pub) and 'C:/' not in json.dumps(pub) and 'source-render' not in json.dumps(pub))
ck('public and private notices identical',pub['sourceNotices']==ctx['sourceNotices'])
ck('actual consumer checks pass',c['status']=='passed_author_consumer_execution' and all(x['passed'] for x in c['checks']))
ck('consumer snapshot exact',sha(c['consumer_path'])==c['consumer_sha256'])
provenance=read(O/'consumer-snapshot/provenance.json')
ck('tested consumer snapshot matches retained input',provenance['sha256']==c['consumer_sha256'])
for e in reg['entries']:
 ck(e['id']+' no atomic model',e['model2dPath'] is None and e['model3dPath'] is None and e['functionalGroups']==[])
 ck(e['id']+' SVG exact',sha(O/e['svgPath'])==e['assetHashes']['svgPath'])
 rr=next(x for x in renders['rows'] if Path(x['svg'])==O/e['svgPath'])
 ck(e['id']+' final preview exact',rr['svg_sha256']==e['assetHashes']['svgPath'] and sha(rr['png'])==rr['png_sha256'])
 ck(e['id']+' allowlist exact',len([x for x in a['assets'] if x['sha256']==rr['svg_sha256'] and x['entry_id']==e['id']])==1)
ck('only eleven SVG assets',len(a['assets'])==11 and all(Path(x['path']).suffix=='.svg' for x in a['assets']))
ck('all symbols used',set(x['id'] for x in reg['entries'])==set(x['registry_id'] for x in b['bindings']))
ck('XPS formulas not inferred',all(not e['formula'] for e in reg['entries'] if 'xps-' in e['id']))
manual=['Actually viewed all eleven final symbolic cards using four full-size contact sheets; all headings, uncertainty statements and source qualifications are readable.',
 'Actually reopened selected original Figure1, Figure2, Figure3, FigureS1, asprep-phase, asprep-phase-continuation and xps-results crops for the specific mappings in this pass.',
 'Three named as-prepared solvent variants keep null whole-composition identity. Local fringe/SAED assignments are explicitly local, not bulk purity.',
 'Source calcined cubic CeO2 assignment is kept distinct from a full elemental or occupancy determination, with unknown physical cross-technique aliquots.',
 'DLS radius-versus-diameter conflict stays unresolved; no factor-of-two correction or equation with TEM crystallite size.',
 'All four XPS history cards distinguish as-prepared/calcined and short/long exposure. Main less-than15min and SI approximately15min remain separate; no exact zero CeIV, unreported55% complement or inferred oxygen stoichiometry.',
 'TGA heating and DSC transition interpretations do not create additional synthesis products; theoretical/cited/bibliographic/combined contexts receive scoped exclusions.',
 'Actual current consumer function was executed from a retained snapshot for every mapped option and enlarge callback. No mounted-browser or independent audit approval is claimed.']
save('author-visual-review.json',{'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_visual_review_complete','static_previews_actually_viewed':11,'contact_sheets_actually_viewed':4,'manual_scopes':manual,'final_svg_hashes':{str(O/e['svgPath']):e['assetHashes']['svgPath'] for e in reg['entries']},'mounted_browser_checked':False,'independent_review':False})
v['status']='passed_author_checks_pending_distinct_audit';v['checks']+=checks;v['check_count']=len(v['checks']);v['consumer_checks']=c['check_count'];v['manual_scopes']=manual;save('author-validation.json',v)
b['status']='frozen_author_proposal_pending_distinct_review';save('bindings.json',b)
deps=[Path(b[k]['path']) for k in ['canonical_manifest','canonical_package','source_freeze','source_audit']]+[P/'source-facts.json',P/'source-inventory.json',P/'source-preparation.json',P/'root-preview-reading.md']+[Path(x['path']) for x in m['records']]
for n in ['figure-1.png','figure-2.png','figure-3.png','figure-s1.png','asprep-phase.png','asprep-phase-continuation.png','xps-results.png']:deps.append(P/'reader-assets'/n)
for d in read(P/'source-preparation.json')['documents']:
 ck('original source '+d['role'],sha(d['source_path'])==d['sha256']);deps.append(Path(d['source_path']))
own=[p for p in O.rglob('*') if p.is_file()]
freeze={'schema':'mattersyn-private-product-context-freeze/1','source_id':'pati2009','author':'/root/backlog_eta','version':1,'created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_pending_distinct_product_context_audit','canonical_package_sha256':b['canonical_package']['sha256'],'canonical_record_manifest_sha256':b['canonical_manifest']['sha256'],'source_package_sha256':b['source_freeze']['sha256'],'source_audit_sha256':b['source_audit']['sha256'],'counts':v['counts'],'author_checks':v['check_count'],'consumer_function_checks':c['check_count'],'bound_files':{str(p.resolve()):sha(p) for p in sorted(set(own+deps))},'public_asset_allowlist_sha256':sha(O/'public-asset-proposal.json'),'public_context_projection_sha256':sha(O/'public-product-contexts-proposal.json'),'canonical_status':'v1 independently under review; any later package-only metadata revision requires an unchanged-record receipt; scientific changes require revalidation','independent_review_approved':False,'atomic_structure_approved':False,'training_eligible':False,'published':False,'later_gates':['distinct product mapping audit','canonical approval or bounded revision receipt','root integration transport','mounted browser validation']}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':v['counts'],'author_checks':v['check_count'],'consumer_function_checks':c['check_count'],'bound_files':len(freeze['bound_files'])},indent=2))
