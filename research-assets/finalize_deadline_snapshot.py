"""Bind the public deadline note to the immutable local inventory."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,shutil
R=Path(__file__).resolve().parent.parent;M=R/'research-assets/incoming-paper-monitor'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
ref=read(M/'deadline-20260920/active-cutoff.json');bound=ref['cutoff_manifest']
assert hashlib.sha256(Path(bound['path']).read_bytes()).hexdigest()==bound['sha256']
p=M/'public-progress-editorial.json';d=read(p)
d['estimate']['notes'][-1]='The fixed inventory was captured on 20 September 2026 at 03:34 UTC: 13,831 top-level document copies, 9,470 known pending provisional scopes, 45 files awaiting grouping and three nested document candidates held for scope review. The required-rate calculations use the known queue, not a verified unique-paper total. Later new papers are queued separately; late or changed SI for an included paper remains an evidence update.'
d['estimate']['notes'].append('A cost-and-capacity pilot proposal has been requested. No paid API processing has started; expanded capacity and the two-month finish remain unverified.')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=M/'two-month-decision.json';d=read(p);d.update(cutoff_at=ref['cutoff_at'],target_at_utc=ref['target_at_utc'],cutoff_manifest=bound,cutoff_document_copies=13831,cutoff_unmapped_files=45,cutoff_nested_candidates_held=3,pilot_proposal_authorized=True,paid_pilot_authorized=False)
p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
cfg=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'automations/mattersyn-sequential-paper-review/automation.toml'
if cfg.exists():shutil.copyfile(cfg,R/'research-assets/mattersyn-review-automation.toml')
print(json.dumps({'cutoff_at':ref['cutoff_at'],'manifest_sha256':bound['sha256'],'paid_api_calls':0}))
