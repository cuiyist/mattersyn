"""Freeze the author proposal after actual static inspection; never imply self-audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parents[1]
assert not(O/'package-freeze.json').exists()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for k in p.strip('/').split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
checks=[]
def ck(label,v):
 checks.append({'check':label,'passed':bool(v)})
 assert v,label
b=read(O/'bindings.json');r=read(O/'registry-additions.json');p=read(O/'product-contexts-additions.json');u=read(O/'public-product-contexts-proposal.json')
v=read(O/'author-validation.json');c=read(O/'consumer-execution-checks.json');renders=read(O/'render-receipt.json');assets=read(O/'public-asset-proposal.json');inputs=read(O/'input-bindings.json')
for path,h in inputs['files'].items():ck('unchanged bound input '+path,sha(path)==h)
for path,h in inputs['source_originals'].items():ck('original PDF unchanged '+path,sha(path)==h)
manifest=read(b['canonical_manifest']['path']);records={x['record_id']:read(x['path']) for x in manifest['records']}
for x in manifest['records']:ck(x['record_id']+' original hash',sha(x['path'])==x['sha256'])
actual={(rid,i,prod['sample_id']) for rid,rec in records.items() for i,prod in enumerate(rec['products'])};account=set()
for row in b['bindings']+b['excluded_contexts']:
 rid=row['record_id'];pp=row['canonical_product_pointer'];prod=ptr(records[rid],pp);key=(rid,int(pp.split('/')[-1]),row['sample_id'])
 ck('unique slot '+str(key),key not in account);account.add(key)
 ck('exact product snapshot '+str(key),prod==row['canonical_product_snapshot'] and jsha(prod)==row['canonical_product_sha256'])
ck('every slot accounted',account==actual and len(actual)==252)
for row in b['bindings']:
 rid=row['record_id'];sid=row['sample_id'];ctx=next(x for x in p['recordContexts'][rid] if x['sample_id']==sid)
 ck(rid+'/'+sid+' product preserved',ctx['canonical_product_snapshot']==row['canonical_product_snapshot'])
 for x in ctx['canonical_claim_links']+ctx['canonical_quantity_links']:
  ck(rid+'/'+sid+'/'+x['measurement_id']+' exact source value',ptr(records[x['record_id']],x['json_pointer'])==x['canonical_measurement'])
 public=next(x for x in u['recordContexts'][rid] if x['sample_id']==sid)
 ck(rid+'/'+sid+' unchanged public subset',all(public[k]==ctx[k] for k in public))
 ck(rid+'/'+sid+' no admissions',all(ctx[k] is False for k in ['training_eligible','atomic_model','binding_approved','same_physical_batch_asserted']))
ck('public path-free','C:\\' not in json.dumps(u) and 'C:/' not in json.dumps(u) and 'source-render' not in json.dumps(u))
ck('public notices exact',u['sourceNotices']==p['sourceNotices'])
ck('actual consumer tests pass',c['status']=='passed_author_consumer_execution' and all(x['passed'] for x in c['checks']))
ck('tested consumer exact',sha(c['consumer_path'])==c['consumer_sha256']==read(O/'consumer-snapshot/provenance.json')['sha256'])
for e in r['entries']:
 ck(e['id']+' no atomic claims',e['formula']=='' and e['model2dPath'] is None and e['model3dPath'] is None and e['functionalGroups']==[])
 ck(e['id']+' exact SVG',sha(O/e['svgPath'])==e['assetHashes']['svgPath'])
 rr=next(x for x in renders['rows'] if Path(x['svg'])==O/e['svgPath'])
 ck(e['id']+' current preview',rr['svg_sha256']==e['assetHashes']['svgPath'] and sha(rr['png'])==rr['png_sha256'])
 aa=next(x for x in assets['assets'] if x['entry_id']==e['id'])
 ck(e['id']+' allowlist exact',aa['sha256']==rr['svg_sha256'] and Path(aa['path'])==O/e['svgPath'])
ck('only 14 public SVGs',len(assets['assets'])==14 and all(Path(x['path']).suffix=='.svg' for x in assets['assets']))
manual=[
 'All fourteen final static symbol previews were actually inspected in five contact sheets. Text, source qualifiers and headings are readable; no atoms, particle envelopes or invented structural shapes are drawn.',
 'Original retained main PDF pages 4 and 5 and SI PDF page 10 were actually reopened visually for phase-component assignments, TEM versus Scherrer scope, and the 130 °C noncrystalline / 30 h versus 72 h / oleate versus myristate tensions. Full source reading remains the earlier extraction and distinct audit scope.',
 'All eighty-eight context captions were authored against the exact source-v2 facts and matched canonical pointers. Optical/additive conditions are not promoted to pure InP specimens. Only the explicitly mapped diffraction/TEM contexts carry source-qualified phase text.',
 'The isolated labelled acid is a separate upstream molecular preparation. Natural-abundance and labelled MSC references, their exchange solutions, and the myristic-acid optical control retain separate labels.',
 'The 250 °C 2.6 ± 0.5 nm TEM statistic is limited to its supported specimen; SD/SE is not inferred. Scherrer domains retain their separate peak-fit/prose conflicts. The extended TEM images have no invented individual ages.',
 'Prior cluster coordinates and mechanistic monomer/fragment models are not current product coordinates. Complete whole-product formulas, current CIFs, atomic models and training eligibility are not added.',
 'The actual current productIdentity consumer function was executed from a retained snapshot using the public projection for every mapped option and enlarge callback. This is a function test, not mounted-browser approval.'
]
save('author-visual-review.json',{'author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_static_review_complete','static_previews_actually_viewed':14,'contact_sheets_actually_viewed':5,'manual_scopes':manual,'final_svg_hashes':{str(O/e['svgPath']):e['assetHashes']['svgPath'] for e in r['entries']},'mounted_browser_checked':False,'independent_review':False})
v['status']='passed_author_checks_pending_distinct_audit';v['checks']+=checks;v['check_count']=len(v['checks']);v['consumer_function_checks']=c['check_count'];v['manual_scopes']=manual;save('author-validation.json',v)
b['status']='frozen_author_proposal_pending_distinct_review';save('bindings.json',b)
deps=[Path(x) for x in inputs['files']]+[Path(x) for x in inputs['source_originals']]+[F/'source-preparation.json']
deps += [F/'source-render'/n for n in ['main-04.png','main-05.png','si-10.png']]
own=[x for x in O.rglob('*') if x.is_file() and '__pycache__' not in x.parts]
freeze={'schema':'mattersyn-private-product-context-freeze/1','source_id':'friedfeld2019','author':'/root/peng1998_reader_assets','version':1,'created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_pending_distinct_product_context_audit','canonical_package_sha256':b['canonical_package']['sha256'],'canonical_record_manifest_sha256':b['canonical_manifest']['sha256'],'source_package_sha256':b['source_freeze']['sha256'],'source_audit_sha256':b['source_audit']['sha256'],'counts':v['counts'],'author_checks':v['check_count'],'consumer_function_checks':c['check_count'],'bound_files':{str(x.resolve()):sha(x) for x in sorted(set(own+deps))},'public_asset_allowlist_sha256':sha(O/'public-asset-proposal.json'),'public_context_projection_sha256':sha(O/'public-product-contexts-proposal.json'),'canonical_status':'draft-v2 frozen; distinct canonical review is a separate gate. Later changes require preserved revalidation.','independent_review_approved':False,'atomic_structure_approved':False,'training_eligible':False,'published':False,'later_gates':['distinct product mapping audit','canonical audit or bounded revision receipt','root integration transport','mounted browser validation']}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'public_contexts_sha256':sha(O/'public-product-contexts-proposal.json'),'registry_sha256':sha(O/'registry-additions.json'),'counts':v['counts'],'author_checks':v['check_count'],'consumer_function_checks':c['check_count'],'bound_files':len(freeze['bound_files'])},indent=2))
