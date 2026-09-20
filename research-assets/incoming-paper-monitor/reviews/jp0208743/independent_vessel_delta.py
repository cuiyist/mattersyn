from pathlib import Path
from copy import deepcopy
import json,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=read(B/'canonical-records-audit.json');rows=[];changed=[]
for rid,h in prior['record_hashes'].items():
 p=B/'vessel-lineage-baseline'/(rid+'.json');before=read(p);after=read(B/'canonical-drafts'/(rid+'.json'));expected=deepcopy(before)
 assert sha(p)==h, rid+' is not the independently audited baseline'
 states=[s for s in expected['material_states'] if s['id']=='fused-matrix']
 if states:
  assert states[0]['parent_ids']==['powder-mixture','aluminum-crucible'];states[0]['parent_ids']=['powder-mixture'];changed.append(rid)
 assert expected==after,rid+' contains unexpected data change'
 rows.append({'record_id':rid,'before_sha256':h,'after_sha256':sha(B/'canonical-drafts'/(rid+'.json')),'bounded_delta_verified':True,'changed_field':'/material_states/1/parent_ids' if states else None})
assert len(changed)==7
out={'status':'passed','scope':'Independent exact comparison with previously source-audited baseline; only vessel removal from fused-glass material ancestry is permitted. All operations, conditions, measurements and source claims are unchanged.','changed_records':changed,'changed_field_count':7,'records':rows,'site_mutated':False}
(B/'vessel-lineage-independent-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Passed exact seven-field equipment-lineage delta against previously audited hashes.')
