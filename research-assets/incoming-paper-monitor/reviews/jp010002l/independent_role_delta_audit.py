"""Bounded re-audit after controlled precursor-role normalization; no source re-review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;BASE=B/'role-delta-audit-baseline'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=read(BASE/'canonical-records-audit.json');C=[];changes=[];after_hashes={}
def ck(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
roles={'cd2':'metal_precursor','hg2':'metal_precursor','h2s':'chalcogen_precursor','h2s-aqueous':'precursor_stock'}
for rid,oldhash in prior['record_hashes'].items():
 beforepath=BASE/(rid+'.json');afterpath=B/'canonical-drafts'/(rid+'.json');before=read(beforepath);after=read(afterpath)
 ck(rid+'/baseline hash',sha(beforepath)==oldhash);after_hashes[rid]=sha(afterpath)
 if rid in {'braun-2001-system-'+x for x in ('i','ii','iii')}:
  stripped=json.loads(json.dumps(after))
  for j,(old,new) in enumerate(zip(before['materials'],after['materials'])):
   ck(rid+'/'+str(j)+'/material identity order',old['id']==new['id'])
   if old['id'] in roles:
    ck(rid+'/'+old['id']+'/controlled role',new['role']==roles[old['id']])
    ck(rid+'/'+old['id']+'/prior context verbatim in notes',new['notes']==old['notes']+['Source-specific role: '+old['role']])
    changes.append({'record_id':rid,'material_id':old['id'],'role_path':f'/materials/{j}/role','before_role':old['role'],'after_role':new['role'],'notes_path':f'/materials/{j}/notes','before_notes':old['notes'],'after_notes':new['notes']})
    stripped['materials'][j]['role']=old['role'];stripped['materials'][j]['notes']=old['notes']
  ck(rid+'/all other JSON nodes exactly unchanged',stripped==before)
  for section in ['operations','stocks','products','measurements','material_states','intended_target','quality','sources','lineage','structure_assets']:ck(rid+'/'+section+'/identical',before[section]==after[section])
 else:ck(rid+'/entire file unchanged',sha(afterpath)==oldhash)
ck('exactly twelve role-normalized material entries',len(changes)==12)
ck('exactly three route files changed',sum(after_hashes[r]!=h for r,h in prior['record_hashes'].items())==3)
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/new manifest hash',row['sha256']==after_hashes[row['id']])
bindings=read(B/'visuals/bindings-additions.json')
ck('binding metadata tracks exact normalized record hashes',bindings['sourceRecordSha256']==after_hashes)
ck('scientific reader bytes unchanged',sha(B/'public-review-proposal/braun2001.json')==read(BASE/'reader-source-audit.json')['reader_sha256'])
ck('molecular registry bytes unchanged',sha(B/'visuals/registry-additions.json')==read(BASE/'molecular-source-audit.json')['registry_sha256'])
ck('source inventory bytes unchanged',sha(B/'source-audit.json')==prior['source_inventory_sha256'])
fail=[c for c in C if not c['passed']]
report={'status':'passed' if not fail else 'failed','scope':'Delta-only independent review of role normalization against preserved exact previously audited bytes. Previous source, quantity, operation, sample/measurement and visual reviews remain valid because all corresponding JSON nodes and assets are unchanged.','audited_utc':datetime.now(timezone.utc).isoformat(),'source_id':'braun2001','baseline_audit_sha256':sha(BASE/'canonical-records-audit.json'),'before_record_hashes':prior['record_hashes'],'record_hashes':after_hashes,'bindings_sha256':sha(B/'visuals/bindings-additions.json'),'reader_sha256':sha(B/'public-review-proposal/braun2001.json'),'canonical_measurement_coverage_sha256':sha(B/'public-review-proposal/canonical-measurement-coverage.json'),'changed_material_roles':changes,'check_count':len(C),'checks':C,'failures':fail,'scientific_assessment':'Cd2+ and Hg2+ are source-reported metal precursors; H2S is the sulfur precursor. H2S/water remains its delivery stock, not a duplicate molecular precursor. Original stage-specific chemical roles remain in notes. No missing salt, stock concentration, dose, stage assignment or synthesis completion inferred.','site_mutated':False}
(B/'role-normalization-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'role-normalization-source-audit.md').write_text('# Braun 2001 role-normalization delta audit\n\n'+report['status']+f'; {len(C)} checks, {len(fail)} failures. Twelve role entries across three routes were normalized; every other canonical JSON field is unchanged.\n\n'+report['scientific_assessment']+'\n\nThe original source/operation/measurement audit is retained. New exact record hashes are recorded in the JSON report.\n',encoding='utf8')
if not fail:
 current=read(B/'canonical-records-audit.json');current['record_hashes']=after_hashes;current['canonical_manifest_sha256']=sha(B/'canonical-record-manifest.json')
 for r in current['records']:r['sha256']=after_hashes[r['record_id']]
 current['role_normalization_delta']={'status':'passed','report':'role-normalization-source-audit.json','sha256':sha(B/'role-normalization-source-audit.json'),'scope':report['scope'],'check_count':len(C)}
 (B/'canonical-records-audit.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 md=B/'canonical-records-audit.md';body=md.read_text(encoding='utf8');marker='\n## Controlled role normalization\n'
 if marker in body:body=body.split(marker)[0]
 md.write_text(body+marker+'\nA bounded independent delta audit confirms twelve role changes across three routes, preserving all prior role descriptions in notes. Every operation, measurement, stock, state, product, target and source field remains unchanged. Current hashes are updated; see role-normalization-source-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'check_count':len(C),'failures':fail}))
