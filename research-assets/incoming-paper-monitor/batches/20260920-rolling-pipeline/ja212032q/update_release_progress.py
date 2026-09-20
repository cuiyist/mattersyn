"""Refresh fixed-cutoff accounting after verified closure, without rescanning sources."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
G=Path(__file__).resolve().parent;MON=G.parents[2];M=G.parents[4];O=G/'site-integration-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert read(MON/'latest-publication.json')['dataset_version']=='0.28.0'
D=MON/'deadline-20260920';active=read(D/'active-cutoff.json');partpath=D/'ghosh-release-scope-20260920.json'
subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(partpath)],check=True,capture_output=True)
part=read(partpath);n=part['counts']['included_pending_scopes'];e=read(MON/'public-progress-editorial.json');now=datetime.now(timezone.utc).isoformat()
e['workflow'].update(fixed_pending_provisional_scopes=n,scope_counts_updated_at=now,later_arrival_groups_current=part['counts']['later_arrival_group_candidates'],later_arrival_file_candidates_current=part['counts']['later_arrival_file_candidates'])
e['estimate']['summary']=f'The two-month target covers the fixed existing collection. {n:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly 159 closures per day over 60 days, or 190 per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
save(MON/'public-progress-editorial.json',e)
for name in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/name)],check=True)
print(json.dumps({'cutoff_counts':part['counts'],'active_source':'Sommer 2020; complete source extraction and independent comparison pending','science_release':'0.28.0','public_progress_prepared':True}))
