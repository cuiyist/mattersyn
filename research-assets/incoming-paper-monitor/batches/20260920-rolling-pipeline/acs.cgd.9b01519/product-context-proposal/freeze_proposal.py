"""Validate and freeze a completed product projection against a passed canonical audit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
O=Path(__file__).resolve().parent;P=O.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t]
 return x
assert not(O/'package-freeze.json').exists()
b=read(O/'bindings.json');audit=b['canonical_audit'];assert audit and sha(audit['path'])==audit['sha256'],'Passed exact canonical audit required.'
assert read(audit['path'])['status'].startswith('passed')
assert sha(b['canonical_manifest']['path'])==b['canonical_manifest']['sha256']
records={};checks=[]
def ck(s,v):checks.append({'check':s,'passed':bool(v)});assert v,s
for path,h in b['source_record_sha256'].items():
 ck('Canonical unchanged '+path,sha(path)==h);r=read(path);records[r['record_id']]=r
ck('Passed consumer test',read(O/'consumer-execution-checks.json')['status']=='passed_author_consumer_execution')
ctx=read(O/'product-contexts-additions.json');reg=read(O/'registry-additions.json');entries={e['id']:e for e in reg['entries']};sf=read(P/'source-facts.json')
seen=[]
for rid,rows in ctx['recordContexts'].items():
 for row in rows:
  key=rid+'/'+row['sample_id']+'/'+row['registry_id'];seen.append(key);product=ptr(records[rid],row['canonical_product_pointer']);claim=ptr(records[row['canonical_claim_link']['record_id']],row['canonical_claim_link']['json_pointer']);fact=ptr(sf,row['source_fact_pointer'])
  ck(key+' unchanged exact product',row['canonical_product_snapshot']==product and product['sample_id']==row['sample_id'])
  ck(key+' no nominal composition promoted',product['composition']['value']is None)
  ck(key+' exact claim',claim==row['canonical_claim_link']['canonical_measurement']and claim['value']['value']==fact['claim'])
  ck(key+' phase note qualification',row['phase']['note'].startswith(b['source_phase_specifications'][row['sample_id']]['scope_note']))
  ck(key+' exact component formula',entries[row['registry_id']]['formula']==row['phase_component_formula'])
  ck(key+' pure symbol',entries[row['registry_id']]['depictionKind']=='symbolic_context'and not entries[row['registry_id']]['model3dPath']and not entries[row['registry_id']]['model2dPath'])
  ck(key+' task and atomic flags',not row['training_eligible']and not row['atomic_model']and not row['binding_approved'])
ck('Unique component selection keys',len(seen)==len(set(seen))==77)
for row in b['excluded_contexts']:ck(row['record_id']+'/'+row['sample_id']+' untouched exclusion',ptr(records[row['record_id']],row['canonical_product_pointer'])==row['canonical_product']and not any(x['sample_id']==row['sample_id']for x in ctx['recordContexts'].get(row['record_id'],[])))
for e in entries.values():ck(e['id']+' SVG hash',sha(O/e['svgPath'])==e['assetHashes']['svgPath'])
review={'status':'passed_author_visual_review','author':'/root/peng1998_reader_assets','method':'Actually viewed all three complete symbolic cards in the contact image; exact formula labels, phase-component qualification, readability and absence of geometric claims checked. Source pages 4–6 were newly reread and viewed for phase/outcome assignments; previously read/viewed source contexts remain listed in author-validation.','preview_hashes':{str(p.relative_to(O)):sha(p)for p in sorted((O/'previews').glob('*.png'))},'not_claimed':['Independent phase/source mapping audit','Mounted browser test','Product-coordinate or training approval']};save('author-visual-review.json',review)
val=read(O/'author-validation.json');val['visual_card_inspection']='passed_actual_author_views';val['transport_checks']=checks;val['transport_check_count']=len(checks);val['canonical_audit_provided']=True;save('author-validation.json',val)
save('public-asset-proposal.json',{'status':'private_unapproved_candidates','assets':[{'path':e['svgPath'],'sha256':e['assetHashes']['svgPath']}for e in entries.values()],'no_atomic_models':True,'source_pages_remain_private':True})
external={p:h for p,h in b['source_record_sha256'].items()};external[b['canonical_manifest']['path']]=b['canonical_manifest']['sha256'];external[audit['path']]=audit['sha256']
for n in ['source-facts.json','source-inventory.json','package-freeze.json','source-independent-audit/independent-audit-v2.json']:external[str(P/n)]=sha(P/n)
files={str(p):sha(p)for p in sorted(O.rglob('*'))if p.is_file()and p.name!='package-freeze.json'and '__pycache__'not in p.parts};files.update(external)
freeze={'schema':'mattersyn-product-component-proposal/1','author':'/root/peng1998_reader_assets','source_id':'sommer2020','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_frozen_pending_independent_product_context_audit','counts':val['counts'],'canonical_manifest':b['canonical_manifest'],'canonical_audit':audit,'bound_files':files,'training_eligible':False,'atomic_model':False,'binding_approved':False,'published':False,'no_canonical_fields_changed':True,'consumer_changes_required':False}
save('package-freeze.json',freeze);print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'files':len(files),'counts':val['counts'],'transport_checks':len(checks)}))
