"""Bounded field-level role patch manifest; no Site writes."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'cd2':'metal_precursor','hg2':'metal_precursor','h2s':'chalcogen_precursor','h2s-aqueous':'precursor_stock'}
changed=[];unchanged=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 q=B/'role-delta-audit-baseline'/p.name
 old=json.loads(q.read_text(encoding='utf8'));new=json.loads(p.read_text(encoding='utf8'))
 if old==new:unchanged.append({'record_id':p.stem,'sha256':sha(p)});continue
 assert old['record_type']=='literature_protocol' and p.stem in {'braun-2001-system-i','braun-2001-system-ii','braun-2001-system-iii'}
 patches=[];restored=json.loads(json.dumps(new))
 for idx,(a,b) in enumerate(zip(old['materials'],new['materials'])):
  if a==b:continue
  assert a['id']==b['id'] and b['id'] in expected
  assert b['role']==expected[b['id']]
  assert b['notes']==a['notes']+['Source-specific role: '+a['role']]
  for field in ['role','notes']:
   patches.append({'material_id':b['id'],'path':f'/materials/{idx}/{field}','before':a[field],'after':b[field]})
   restored['materials'][idx][field]=a[field]
 assert restored==old,'Unexpected changes outside role/notes: '+p.stem
 assert old['operations']==new['operations'] and old['measurements']==new['measurements']
 changed.append({'record_id':p.stem,'file':p.name,'before_sha256':sha(q),'after_sha256':sha(p),'patches':patches})
assert len(changed)==3 and len(unchanged)==6
report={'status':'passed','scope':'Only three route records; four material role fields per route normalized, with original role descriptions preserved verbatim in appended notes. All45 operations,75 measurements, numeric/status/bound/evidence fields, stocks, sample associations and unknown identities are byte-equivalent as parsed data. No source role semantics were removed.','changed_record_count':3,'unchanged_record_count':6,'changed_field_count':sum(len(r['patches']) for r in changed),'patch_policy':'Apply by record_id and material_id. Validate the before field value; preserve independent integration metadata elsewhere. Notes patch appends the exact new note without replacing existing integration notes.','changed_records':changed,'unchanged_records':unchanged}
(B/'role-normalization-delta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['changed_records','unchanged_records','patch_policy']}))
