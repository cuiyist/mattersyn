"""Root independent product/sample mapping review; never executes author builder."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
O=Path(__file__).resolve().parent;F=O.parent;P=F/'visuals/product-context';C=F/'canonical-proposal/draft-v2'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
checks=[]
def ck(name,value):checks.append({'check':name,'passed':bool(value)});assert value,name
def pointer(obj,p):
 for part in p.strip('/').split('/'):
  part=part.replace('~1','/').replace('~0','~');obj=obj[int(part)] if isinstance(obj,list) else obj[part]
 return obj
freeze=read(P/'package-freeze.json');ck('Expected immutable product author freeze',sha(P/'package-freeze.json')=='2cf90a066290057de245baf60b231f70c5ef8159ca6251e639aba804fc3530e6')
for path,h in freeze['bound_files'].items():ck('Bound file '+path,sha(Path(path))==h)
ck('Distinct source audit passed',read(F/'source-independent-audit/independent-audit.json')['overall_pass'])
records={p.stem:read(p) for p in (C/'records').glob('*.json')};ck('30 exact canonical drafts',len(records)==30)
coverage=read(P/'slot-coverage.json');rows=coverage['rows'];bindings=read(P/'bindings.json')['bindings'];public=read(P/'public-product-contexts-proposal.json');registry=read(P/'registry-additions.json')['entries'];entries={e['id']:e for e in registry}
facts={x['id']:x for x in read(F/'source-extraction-revision-2/source-facts.json')['facts']}
slots={(rid,'/products/'+str(i),p['sample_id']) for rid,r in records.items() for i,p in enumerate(r['products'])}
got={(r['record_id'],r['pointer'],r['sample_id']) for r in rows};ck('Complete nonduplicated slot coverage',slots==got and len(rows)==len(got)==252)
mapped=[x for x in rows if x['disposition']=='mapped'];excluded=[x for x in rows if x['disposition']=='excluded']
ck('88 mapped / 164 excluded',len(mapped)==88 and len(excluded)==164 and len(bindings)==88)
for x in excluded:ck('Reason for excluded slot '+x['record_id']+x['pointer'],bool(x.get('reason')) and x.get('registry_id') is None)
phase_expect={'xrd-context':'diffraction','temp-150-tem':'tem-agglomerates','temp-250-tem':'tem-spheres'}
seen=[];manual_review=[]
for b in bindings:
 rid=b['record_id'];sid=b['sample_id'];p=pointer(records[rid],b['canonical_product_pointer']);tag=rid+'/'+sid
 ck('Exact product snapshot '+tag,p==b['canonical_product_snapshot'] and p['sample_id']==sid)
 ck('Exact canonical byte binding '+tag,sha(C/'records'/(rid+'.json'))==b['canonical_record_sha256'])
 ck('Registry ID '+tag,b['registry_id'] in entries)
 views=[x for x in public['recordContexts'][rid] if x['sample_id']==sid];ck('Unique view '+tag,len(views)==1);view=views[0]
 ck('Same selected registry '+tag,view['registry_id']==b['registry_id'])
 ck('All source facts exist '+tag,bool(b['source_fact_ids']) and all(f in facts for f in b['source_fact_ids']))
 ck('Source fact links transported '+tag,set(view['source_fact_ids'])==set(b['source_fact_ids']))
 ck('No training / atomic / replicate claim '+tag,view['training_eligible'] is False and view['atomic_model'] is False and view['same_physical_batch_asserted'] is False)
 ck('Current integration approval withheld '+tag,view['binding_approved'] is False)
 ck('Morphology remains canonical '+tag,view['morphology']==p['morphology'])
 phase=view['phase']['value']
 if phase is not None:ck('Phase belongs only to local structure evidence '+tag,sid in phase_expect and b['symbol_key']==phase_expect[sid] and bool(view['phase']['evidence']))
 else:ck('All other phase fields remain unknown '+tag,sid not in phase_expect)
 caption=view['caption']
 if sid=='temp-250-tem':ck('TEM scope and undefined uncertainty',all(t in caption for t in ['2.6 ± 0.5','315','not define','not assigned to all']))
 if sid=='temp-150-tem':ck('FFT is not SAED',all(t in caption for t in ['FFT','not an independently reported SAED','Local crystallinity']))
 if (sid.startswith('c-') or '-eq' in sid) and b['symbol_key']=='conversion':ck('Optical condition not product phase '+tag,phase is None and 'not a new verified physical replicate' in caption)
 if sid in {'acid-150','acid-250','indium-150','indium-200','indium-250'}:ck('Additive series is not pooled '+tag,phase is None and 'not pooled' in caption)
 if sid=='xrd-context':ck('Mixture and aliquot qualification',all(t in caption for t in ['In2O3','not a pooled specimen','reference','unspecified']))
 if sid=='pretreat-xrd':ck('Reference sticks not measured phase',phase is None and all(t in caption for t in ['oleate','myristate','30 h / 72 h','do not establish']))
 if sid=='pretreat72-conversion':ck('Sequential pretreatment/conversion kept distinct',phase is None and 'subsequent optical experiment is distinct' in caption)
 seen.append((rid,sid));manual_review.append({'record':rid,'sample':sid,'symbol':b['symbol_key'],'source_fact_ids':b['source_fact_ids'],'phase':phase,'canonical_pointer':b['canonical_product_pointer']})
ck('Every published mapping individually checked',len(seen)==88 and len(set(seen))==88 and len(public['recordContexts'])==12)
for e in registry:
 ck(e['id']+' no coordinate model',e['model2dPath'] is None and e['model3dPath'] is None and not e['formula'] and e['eligible_training'] is False)
 p=P/e['svgPath'];ck(e['id']+' exact SVG hash',sha(p)==e['assetHashes']['svgPath'])
 s=p.read_text('utf8');ck(e['id']+' symbolic disclaimer', 'Symbolic source context only' in s and 'No atom positions' in s)
ck('14 symbolic cards',len(registry)==14)
assets=read(P/'public-asset-proposal.json')['assets']
ck('Explicit 14 SVG allowlist',len(assets)==14)
for a in assets:
 ck(a['entry_id']+' public asset hash',sha(Path(a['path']))==a['sha256'])
 ck(a['entry_id']+' public path bound',a['public_path'].startswith('assets/chemical-registry/friedfeld2019-products/') and a['public_path'].endswith('.svg') and '..' not in a['public_path'])
ck('Path-free public map',not re.search(r'[A-Za-z]:[\\/]|file://',json.dumps(public)))
save(O/'mechanical-checks.json',{'author':'/root','check_count':len(checks),'checks':checks,'author_builder_executed':False})
save(O/'mapping-review.json',{'reviewer':'/root','reviewed_mappings':manual_review,'excluded_count':164,'coverage':'Every252canonicalproductslot independently enumerated; excluded classifications inspected in nine reason groups.'})
report={'schema':'mattersyn-independent-product-context-audit/1','source_id':'friedfeld2019','author':'/root/peng1998_reader_assets','auditor':'/root','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','overall_pass':True,'findings':[],
 'manual_scope':['Read all context_data source-specific display prose and scientific boundary explanations.','Inspected every one of the14symbolic cards across five rendered contact sheets.','Read every record/sample mapping group and all exclusion reason groups; checked all88exact mappings mechanically against frozen canonical products.','Compared structural/TEM/FFT/pretreatment prose with effective audited source facts and root’s earlier visual reading of main2–7 andSI1/2/8/9.'],
 'scientific_conclusions':['Optical condition sets are not phase-pure products or replicated batches.','LocalTEM, powder mixture assignments, source-calculated coherent domains and pretreatment intermediates remain distinct.','No copied prior cluster coordinates, fake SAED, physical-aliquot joins or exact atomic training pair.'],
 'limits':['This audit approves only the symbolic product-context proposal at the exact frozen canonical version.','Separate full canonical/reader review, visual integration, actual browser and publication checks remain pending.','No new complete33page reading or curve digitization claimed by root.'],
 'counts':{'mapped':88,'excluded':164,'canonical_slots':252,'symbols':14,'atomic_models':0,'supporting_checks':len(checks)},
 'inputs':{'product_freeze':{'path':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json')},'canonical_freeze':{'path':str(C/'package-freeze.json'),'sha256':sha(C/'package-freeze.json')},'source_audit':{'path':str(F/'source-independent-audit/independent-audit.json'),'sha256':sha(F/'source-independent-audit/independent-audit.json')}},
 'bound_outputs':{str(p):sha(p) for p in [O/'mechanical-checks.json',O/'mapping-review.json',Path(__file__)]}}
save(O/'independent-audit.json',report)
print(json.dumps({'status':'passed','checks':len(checks),'sha256':sha(O/'independent-audit.json'),'canonical_approval':False,'publication_approval':False}))
