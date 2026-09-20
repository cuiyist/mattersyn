"""Preserved, bounded revision: keep distillation pot residue separate from cuts."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import hashlib, json, shutil, sys
sys.dont_write_bytecode = True
B=Path(__file__).resolve().parent
C0=B/'canonical-proposal/v2'; R0=B/'public-review-proposal/v2'
C=B/'canonical-proposal/v3'; R=B/'public-review-proposal/v3'
T=B/'proposal-contract-check/v3'; S=Path(r'[local path redacted]')
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ptr(x,p):
 if not p or p=='/':return x
 for t in p.strip('/').split('/'):
  t=t.replace('~1','/').replace('~0','~'); x=x[int(t)] if isinstance(x,list) else x[t]
 return x
def diff(a,b,p=''):
 if type(a)!=type(b): return [{'path':p,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   q=p+'/'+k.replace('~','~0').replace('/','~1')
   if k not in a: out.append({'path':q,'added':b[k]})
   elif k not in b: out.append({'path':q,'removed':a[k]})
   else: out+=diff(a[k],b[k],q)
  return out
 if isinstance(a,list):
  if len(a)!=len(b): return [{'path':p,'before':a,'after':b}]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [{'path':p,'before':a,'after':b}]
assert not (B/'proposal-freeze-v3.json').exists(), 'Do not mutate frozen v3.'
f2=B/'proposal-freeze-v2.json'; assert sha(f2)=='ad7f6c9d2daf67477b256f481a9d113a8d34294b7196f9176ca32a013f29fa4e'
frozen=read(f2)['bound_files'];checks=0
for b in frozen: assert sha(b['path'])==b['sha256'];checks+=1
C.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
for old,new in [(C0,C),(R0,R)]:
 for p in old.glob('*.json'):shutil.copyfile(p,new/p.name)
rid='evans-2010-topse-distillation';rec=read(C/(rid+'.json'));oldrec=deepcopy(rec)
pot=rid+'-op-2-pot-state'
rec['revision']=2
rec['material_states'].append({'id':pot,'name':'Residual TOPSe mixture remaining in the distillation pot after collecting the three cuts','kind':'fraction','parent_ids':[rid+'-op-1-state']})
rec['material_states'][2]['parent_ids']=[pot]
rec['operations'][1]['outputs'].append(pot)
rec['operations'][1]['description']+=' The separate residual-pot output remains in the original flask and supplies residue C; it is not pooled with the distillate cuts.'
rec['operations'][2]['inputs']=[pot]
assert rec['operations'][2]['depends_on']==[rid+'-op-2']
save(C/(rid+'.json'),rec)
review=read(R/'evans2010.json');oldreview=deepcopy(review)
items={i['id']:i for s in review['reader_sections'] for i in s['items']}
i2=items['operation-'+rid+'-op-2'];i3=items['operation-'+rid+'-op-3']
name=rec['material_states'][-1]['name']
i2['text']+=' The material remaining in the distillation pot is a separate output and supplies residue C.'
i2['notes'][1]+=' Separate pot output: '+name+'.'
i2['operation_context']['outputs'].append(pot)
i2['operation_context']['material_flow_labels'][pot]=name
i3['notes'][0]='Inputs: '+name+'.'
i3['operation_context']['inputs']=[pot]
del i3['operation_context']['material_flow_labels'][rid+'-op-2-state']
i3['operation_context']['material_flow_labels'][pot]=name
save(R/'evans2010.json',review)
cd=diff(oldrec,rec);rd=diff(oldreview,review)
assert {x['path'] for x in cd}=={'/revision','/material_states','/operations/1/outputs','/operations/1/description','/operations/2/inputs/0'}
assert len(rd)==8,rd
assert oldrec['materials']==rec['materials'] and oldrec['stocks']==rec['stocks'] and oldrec['measurements']==rec['measurements'] and oldrec['products']==rec['products'];checks+=4
for p in C0.glob('evans-*.json'):
 if p.name!=rid+'.json':assert sha(p)==sha(C/p.name);checks+=1
# Revalidate all canonical records and every existing exact reader field; no source value changes.
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
import build_paper_reviews
records={p.stem:read(p) for p in C.glob('evans-*.json')};errs=[]
for r in records.values():errs+=validate_record(r);assert all(not e['eligible'] for e in eligibility(r).values());checks+=1
assert not errs,errs
assert len(set(build_groups(list(records.values())).values()))==1;checks+=1
for i in items.values():
 for q in i.get('facts',[]):
  if 'canonical_quantity' in q: assert ptr(records[q['canonical_record_id']],q['json_pointer'])==q['canonical_quantity'];checks+=1
 for link in i.get('canonical_links',[]):ptr(records[link['record_id']],link['json_pointer']);checks+=1
 if 'operation_context' in i:
  oc=i['operation_context'];op=ptr(records[oc['record_id']],oc['json_pointer'])
  for k in ['inputs','outputs','depends_on','retained_fraction']:assert oc[k]==op[k];checks+=1
for r in records.values():
 p=T/'data/records'/(r['record_id']+'.json');p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/p.name,p)
binding=read(R/'reader-bindings-proposal.json');binding['reader_sha256']=sha(R/'evans2010.json');save(R/'reader-bindings-proposal.json',binding)
for a in binding['original_assets']:
 p=T/'dist'/a['public_asset'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_path'],p)
build_paper_reviews.ROOT=T;reader_errors=build_paper_reviews.validate(review);assert not reader_errors,reader_errors
report={'status':'passed_bounded_author_revision_and_current_contract_checks','checks':checks,'finding':'Collected distillates incorrectly parented residue C in v2.','resolution':'New explicit residual-pot output of distillation feeds residue C; the three physically separate cuts remain a different output. depends_on preserves chronology.','canonical_deltas':cd,'reader_deltas':rd,'unchanged_record_count':31,'all_source_quantities_unchanged':True,'all_materials_stocks_measurements_products_unchanged':True,'schema_errors':errs,'reader_errors':reader_errors,'version2_preserved':True,'independent_audit':'pending','training_rows':0,'exact_qd_structure_pairs':0}
save(B/'proposal-lineage-correction-v3.json',report)
for folder,old in [(C,C0),(R,R0)]:
 prior=read(old/'author-validation.json')
 val={'status':'passed_bounded_v3_author_revision_checks','this_revision_checks':checks,'prior_validation':{'path':str(old/'author-validation.json'),'sha256':sha(old/'author-validation.json')},'counts':prior['counts'],'correction_report':{'path':str(B/'proposal-lineage-correction-v3.json'),'sha256':sha(B/'proposal-lineage-correction-v3.json')},'independent_scientific_audit':'pending','browser_publication':'pending'}
 save(folder/'author-validation.json',val)
cm=read(C/'record-manifest.json');cm['version']=3;cm['created_at']=datetime.now(timezone.utc).isoformat();cm['author_script_sha256']=sha(__file__)
for r in cm['records']:r['path']=str(C/Path(r['path']).name);r['sha256']=sha(r['path'])
cm['validation_sha256']=sha(C/'author-validation.json');save(C/'record-manifest.json',cm)
cov=read(R/'source-item-coverage.json');cov['private_canonical_manifest_sha256']=sha(C/'record-manifest.json');save(R/'source-item-coverage.json',cov)
rm=read(R/'reader-manifest.json');rm['version']=3;rm['created_at']=cm['created_at'];rm['author_script_sha256']=sha(__file__)
inputs={}
for p,h in rm['input_hashes'].items():
 q=Path(p)
 if q.parent==C0:q=C/q.name
 inputs[str(q)]=sha(q)
rm['input_hashes']=inputs
rm['outputs']={n:sha(R/n) for n in rm['outputs']};save(R/'reader-manifest.json',rm)
for b in frozen:assert sha(b['path'])==b['sha256'];checks+=1
bound={str(p):sha(p) for p in [f2,Path(__file__),B/'proposal-lineage-correction-v3.json',B/'source-scientific-audit.json',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',S/'scripts/build_paper_reviews.py']+list(C.glob('*.json'))+list(R.glob('*.json'))}
for a in binding['original_assets']:bound[a['private_path']]=sha(a['private_path'])
save(B/'proposal-freeze-v3.json',{'schema':'mattersyn-private-paper-proposals-freeze/1','source_id':'evans2010','version':3,'author':'/root/norberg2004_extract','created_at':cm['created_at'],'status':'bounded_lineage_correction_frozen_for_independent_review','canonical_manifest':{'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},'reader_manifest':{'path':str(R/'reader-manifest.json'),'sha256':sha(R/'reader-manifest.json')},'reader':{'path':str(R/'evans2010.json'),'sha256':sha(R/'evans2010.json')},'correction_report':{'path':str(B/'proposal-lineage-correction-v3.json'),'sha256':sha(B/'proposal-lineage-correction-v3.json')},'bound_files':[{'path':p,'sha256':h} for p,h in bound.items()],'source_audit_sha256':sha(B/'source-scientific-audit.json'),'published':False,'training_eligible':False})
print(json.dumps({'freeze':sha(B/'proposal-freeze-v3.json'),'delta':sha(B/'proposal-lineage-correction-v3.json'),'canonical':sha(C/'record-manifest.json'),'reader_manifest':sha(R/'reader-manifest.json'),'reader':sha(R/'evans2010.json'),'checks':checks,'canonical_delta_count':len(cd),'reader_delta_count':len(rd)}))
