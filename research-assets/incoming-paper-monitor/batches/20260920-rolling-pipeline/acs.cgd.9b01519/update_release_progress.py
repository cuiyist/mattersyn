"""Refresh cutoff accounting after the verified Sommer contribution."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
N=Path(__file__).resolve().parent;MON=N.parents[2];M=N.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert read(MON/'latest-publication.json')['dataset_version']=='0.29.0'
D=MON/'deadline-20260920';active=read(D/'active-cutoff.json');partpath=D/'sommer-release-scope-20260920.json'
subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(partpath)],check=True,capture_output=True)
part=read(partpath);n=part['counts']['included_pending_scopes'];ed=read(MON/'public-progress-editorial.json')
ed['workflow'].update(fixed_pending_provisional_scopes=n,scope_counts_updated_at=datetime.now(timezone.utc).isoformat(),later_arrival_groups_current=part['counts']['later_arrival_group_candidates'],later_arrival_file_candidates_current=part['counts']['later_arrival_file_candidates'])
ed['estimate']['summary']=f'The two-month target covers the fixed existing collection. {n:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly 159 closures per day over 60 days, or 190 per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
save(MON/'public-progress-editorial.json',ed)
for name in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/name)],check=True)
print(json.dumps({'cutoff_counts':part['counts'],'active_source':'Matuhina 2023 CsMnCl3: complete main/SI extraction and independent comparison in progress','science_release':'0.29.0'}))
