"""Finalize this author package after actual preview inspection. No independent approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def jsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
assert not(O/'package-freeze.json').exists()
b=read(O/'bindings.json');r=read(O/'registry-additions.json');v=read(O/'author-validation.json');c=read(O/'consumer-execution-checks.json');renders=read(O/'render-receipt.json');a=read(O/'public-asset-proposal.json');m=read(b['canonical_manifest']['path']);contexts=read(O/'product-contexts-additions.json')
checks=[]
def ck(k,yes):checks.append({'check':k,'passed':bool(yes)});assert yes,k
ck('exact final record manifest',sha(b['canonical_manifest']['path'])==b['canonical_manifest']['sha256']=='9daced82e9f63aeaea8acd83838bd4560818287ddaf26cf1b39ca9651868db6e')
package=P/'canonical-proposal/v1/package-manifest.json'
ck('canonical author freeze',sha(package)=='958771dbb0d0f001e345a78f91da7f7d76d87fed90388f6c9e0b0dc65c5515a3')
ck('actual consumer execution passed',c['status']=='passed_author_consumer_execution' and all(x['passed'] for x in c['checks']))
ck('actual Site consumer unchanged',sha(c['consumer_path'])==c['consumer_sha256'])
ck('source freeze unchanged',sha(b['source_freeze']['path'])==b['source_freeze']['sha256'])
ck('source audit unchanged',sha(b['source_audit']['path'])==b['source_audit']['sha256'])
ck('source facts unchanged',sha(P/'source-facts.json')==b['source_facts_sha256'])
for meta in m['records']:
 ck(meta['record_id']+' canonical unchanged',sha(meta['path'])==meta['sha256'])
for e in r['entries']:
 ck(e['id']+' SVG unchanged',sha(O/e['svgPath'])==e['assetHashes']['svgPath'])
 rr=next(x for x in renders['rows'] if Path(x['svg'])==O/e['svgPath'])
 ck(e['id']+' preview represents final SVG',rr['svg_sha256']==e['assetHashes']['svgPath'] and sha(rr['png'])==rr['png_sha256'])
 ck(e['id']+' exact public allowlist',len([x for x in a['assets'] if x['entry_id']==e['id'] and x['sha256']==rr['svg_sha256']])==1)
 ck(e['id']+' no coordinate files',e['model2dPath'] is None and e['model3dPath'] is None and e['eligible_training'] is False)
for row in b['bindings']:
 rec=read(row['canonical_record_path']);prod=rec['products'][int(row['product_pointer'].split('/')[-1])]
 ck(row['record_id']+'/'+row['sample_id']+' exact snapshot',jsha(prod)==row['product_sha256'] and prod['sample_id']==row['sample_id'])
 con=next(x for x in contexts['recordContexts'][row['record_id']] if x['sample_id']==row['sample_id'] and x['registry_id']==row['registry_id'])
 ck(row['record_id']+'/'+row['sample_id']+' exact canonical copy',con['canonical_product_snapshot']==prod)
 ck(row['record_id']+'/'+row['sample_id']+' no scientific admissions',con['training_eligible'] is False and con['atomic_model'] is False and con['same_physical_batch_asserted'] is False)
manual=[
 'Actually read/viewed original main pages3,4,5,8,9,10 and SI6,7,13 for product/phase, device, film/dispersion and aged-component scopes.',
 'All seven final SVG-derived PNG previews actually viewed using three contact sheets; headings, formulas and limiting captions are readable without clipping.',
 'Five source preparation labels are mapped explicitly; precursor-loading ratios are not measured composition values.',
 'Diffraction assignment on analytical contexts is qualified as the source preparation context; no same-aliquot or dissolved-species claim.',
 'Low-temperature film on silica remains distinct from optical dispersion and unencapsulated LSC film on glass.',
 'Aged150 maps only to separate CsCl/Cs3MnCl5/CsMn4Cl9 component cards; no target-CsMnCl3 purity imposed on the aged mixture.',
 'Atomic TableS2 content is acknowledged with unresolved occupancy/site-setting issues; no atomic reconstruction or missing-coordinates claim.',
 'DFT, combined contexts and unresolved controls have explicit exclusions. No curve digitization, atomistic structure, geometry or training approval.'
]
save('author-visual-review.json',{'author':'/root/peng1998_reader_assets','status':'author_visual_review_complete','created_at':datetime.now(timezone.utc).isoformat(),'actual_static_previews_viewed':7,'contact_sheets_viewed':3,'manual_scopes':manual,'final_svg_hashes':{str(O/e['svgPath']):e['assetHashes']['svgPath'] for e in r['entries']},'mounted_browser_checked':False,'independent_scientific_review':False})
v['status']='passed_author_checks_pending_distinct_audit';v['checks']+=checks;v['check_count']=len(v['checks']);v['consumer_checks']=c['check_count'];v['actual_static_previews_viewed']=7;v['manual_scopes']=manual
save('author-validation.json',v)
b['status']='frozen_author_proposal_pending_distinct_review';b['canonical_package']={'path':str(package),'sha256':sha(package)};b['canonical_independent_audit_status']='pending separately at author freeze; any scientific revision requires a bounded rebind';save('bindings.json',b)
prep=read(P/'source-preparation.json');deps=[Path(b['canonical_manifest']['path']),package,Path(b['source_freeze']['path']),Path(b['source_audit']['path']),P/'source-facts.json',P/'source-inventory.json',P/'source-preparation.json',Path(c['consumer_path'])]+[Path(x['path']) for x in m['records']]
for doc in prep['documents']:
 ck(doc['role']+' original hash',sha(doc['source_path'])==doc['sha256']);deps.append(Path(doc['source_path']))
 for page in doc['pages']:
  if page['pdf_page'] in v['targeted_source_pages_actually_read_and_viewed'][doc['role']]:deps += [Path(page['image_path']),Path(page['text_path'])]
own=[p for p in O.rglob('*') if p.is_file()]
bound={str(p.resolve()):sha(p) for p in sorted(set(own+deps))}
freeze={'schema':'mattersyn-private-product-context-freeze/1','source_id':'matuhina2023','author':'/root/peng1998_reader_assets','version':1,'created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_pending_distinct_product_context_review','canonical_package_sha256':sha(package),'canonical_record_manifest_sha256':sha(b['canonical_manifest']['path']),'source_package_sha256':sha(P/'package-freeze.json'),'source_audit_sha256':sha(b['source_audit']['path']),'counts':v['counts'],'author_checks':v['check_count'],'consumer_function_checks':c['check_count'],'bound_files':bound,'public_asset_allowlist_sha256':sha(O/'public-asset-proposal.json'),'canonical_status':'frozen author v1; distinct audit pending','independent_review_approved':False,'atomic_structure_approved':False,'training_eligible':False,'published':False,'later_gates':['distinct product/source mapping audit','canonical review or bounded rebind','root integration transport','actual mounted browser checks']}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'registry_sha256':sha(O/'registry-additions.json'),'contexts_sha256':sha(O/'product-contexts-additions.json'),'bindings_sha256':sha(O/'bindings.json'),'counts':v['counts'],'checks':v['check_count'],'consumer_checks':c['check_count'],'bound_files':len(bound)},indent=2))
