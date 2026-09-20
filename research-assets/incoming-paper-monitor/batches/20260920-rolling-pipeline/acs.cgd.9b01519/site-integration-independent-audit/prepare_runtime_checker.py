"""Prepare the established actual-module DOM harness with Sommer's audited interface."""
from pathlib import Path
A=Path(__file__).resolve().parent
s=(A.parent.parent/'ja212032q/site-integration-independent-audit/check_actual_dispatch.mjs').read_text(encoding='utf8')
for old,new in [('ghosh2012','sommer2020'),('Ghosh2012','Sommer2020'),('stages===33','stages===31'),('33 actual stages','31 actual stages'),('rows===183','rows===168'),('183 exact rows','168 exact rows'),('parameters===70','parameters===50'),('70 parameters','50 parameters'),("check(alternatives===10,'10 schedule alternatives');",''),('slots===88','slots===62'),('88 actual material bindings','62 actual material bindings')]:
 assert old in s,old;s=s.replace(old,new)
s=s.replace("alternatives+=scene.rows.filter(x=>x.kind==='alternative_schedule_parameter').length", "alternatives+=scene.rows.filter(x=>x.kind==='alternative_schedule_group').reduce((n,x)=>n+x.quantities.length,0)")
s=s.replace("check(slots===62,'62 actual material bindings');", "check(slots===62,'62 actual material bindings');check(alternatives===155,'155 exact grouped schedule quantities');")
(A/'check_actual_dispatch.mjs').write_text(s,encoding='utf8')
print('Prepared Sommer actual installed dispatch checker.')
