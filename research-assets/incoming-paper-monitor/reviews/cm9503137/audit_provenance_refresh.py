"""Read-only comparison of regenerated drafts with the preceding Site import."""
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'/'data'/'records'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(v):
 if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if k not in ['evidence','link_evidence']}
 if isinstance(v,list):return [normalize(x) for x in v]
 return v
def evidence(v,path=''):
 out={}
 if isinstance(v,dict):
  for k,x in v.items():
   p=path+'/'+k
   if k in ['evidence','link_evidence']:out[p]=x
   else:out.update(evidence(x,p))
 elif isinstance(v,list):
  for i,x in enumerate(v):out.update(evidence(x,path+'/'+str(i)))
 return out
fields=['material','intended_target','materials','stocks','material_states','operations','condition_options','products','measurements','lineage']
rows=[];duplicates=[];diffs=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 new=json.loads(p.read_text(encoding='utf-8'));old=json.loads((S/p.name).read_text(encoding='utf-8'))
 ne=evidence(new);oe=evidence(old)
 changed=[k for k in set(ne)|set(oe) if ne.get(k)!=oe.get(k)]
 bad=[k for k in fields if normalize(new.get(k))!=normalize(old.get(k))]
 for pointer,items in ne.items():
  keys=[json.dumps(v,sort_keys=True) for v in items]
  if len(set(keys))!=len(keys):duplicates.append({'record_id':p.stem,'json_pointer':pointer})
 if bad:diffs.append({'record_id':p.stem,'fields':bad})
 rows.append({'record_id':p.stem,'current_sha256':sha(p),'comparison_import_sha256':sha(S/p.name),'non_provenance_scientific_fields_changed':bad,'evidence_paths_changed':len(changed),'changed_evidence_pointers':sorted(changed),'current_evidence_array_count':len(ne)})
r=json.loads((B/'canonical-drafts/danek-1996-znse-overgrowth.json').read_text(encoding='utf-8'))
syn={'source_id':'danek1996','locator':'Main PDF p. 2, printed p. 174, Synthesis of CdSe/ZnSe Nanocrystals'}
mat={'source_id':'danek1996','locator':'Main PDF p. 2, printed p. 174, Materials'}
assert all(m['evidence']==[syn,mat] for m in r['materials'])
for o in r['operations']:
 expected=[syn]
 if o['id'] in ['heat','dose']:expected.append({'source_id':'danek1996','locator':'Main PDF p. 3, printed p. 175, Synthesis'})
 if o['id'] in ['exchange','store']:expected.append({'source_id':'danek1996','locator':'Main PDF p. 4, printed p. 176, Purification and storage discussion'})
 assert o['evidence']==expected,(o['id'],o['evidence'])
assert all(s['evidence']==[syn] for s in r['stocks'])
assert r['materials'][0]['quantities']['mass']['evidence']==[syn]
assert not duplicates and not diffs
assert 'records=json.loads(json.dumps(records))' in (B/'build_records.py').read_text(encoding='utf-8')
report={'status':'passed_bounded_provenance_refresh','audited_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'No new source review. Compared current private drafts with preceding read-only Site import; scientific fields match after excluding provenance arrays. Status, reader assets and publication are not certified by this check.','record_count':len(rows),'scientific_field_count_per_record':len(fields),'duplicate_evidence_arrays':duplicates,'non_provenance_scientific_differences':diffs,'overgrowth_exact_evidence_scopes':'All 11 materials have SYN+MAT exactly; heat/dose SYN+p3 exactly; exchange/store SYN+p4 exactly; all other operations and both stocks SYN only; seed mass value SYN only.','builder_fix':'JSON round-trip breaks shared evidence-list aliases before field-specific additions.','records':rows,'publication_claim':False,'review_scope':'supplied_main_only_si_unverified'}
(B/'provenance-refresh-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'records':len(rows),'changed_evidence_paths':sum(x['evidence_paths_changed'] for x in rows),'duplicate_arrays':len(duplicates),'non_provenance_scientific_differences':len(diffs)},indent=2))
