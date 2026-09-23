from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,tomllib

HERE=Path(__file__).resolve().parent
PAIR=HERE.parent
ROOT=PAIR.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
config=tomllib.loads(Path(r'[local path redacted]').read_text(encoding='utf8'))
request=json.loads((HERE/'daily-automation-update-receipt.json').read_bytes())
assert config['rrule']==request['prior_verified_schedule']
assert config['prompt']==request['prompt'] and config['status']=='ACTIVE'
at=datetime.now(timezone.utc).isoformat()
verification={'at':at,'automation_id':config['id'],'schedule_preserved':True,'status':config['status'],
    'rrule':config['rrule'],'prompt_sha256':hashlib.sha256(config['prompt'].encode()).hexdigest(),
    'user_requested_daily':True}
(HERE/'daily-schedule-verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf8')
memory=ROOT/'MEMORY.md'
heading='## 2026-09-22 — User changed MatterSyn automation to daily'
assert heading not in memory.read_text(encoding='utf8')
entry=f'''{heading}

The user explicitly rescheduled MatterSyn evidence review from every5minutes to daily. Preserve this user choice; do not restore the older interval. The existing automation remains ACTIVE with its current daily schedule. Updated only the workflow prompt while preserving the freshly read schedule, then verified both from the saved automation state at{at}. Receipt: research-assets/pair-priority-screen-20260922/methods-first/daily-schedule-verification.json. Daily scheduler wakeups are separate from in-page progress refresh and do not imply continuous unattended execution.

Latest screening checkpoints: atomic shortlist batch01 independently passed its bounded source-role audit (8articles,10scopes,63targeted original pages); this is not complete scientific curation and approves no training pairs. Batch02 is author-screened only:8studies/10scopes, two studies with local printed experimental target-coordinate tables (Wagner SSZ-48 and Lim host/guest); three structural states across two preparation families, with required qualifications and independent audit pending. Do not convert these into three certified pairs. Original papers, full text and page images remain local. Root visual source notes cover14PDFs/38full pages with explicit partial coverage and no source closure. Word97 prototype is frozen/parked with three recovered text candidates and audit pending.

'''
memory.write_text(entry+memory.read_text(encoding='utf8'),encoding='utf8')
editorial_path=MON/'public-progress-editorial.json'
editorial=json.loads(editorial_path.read_bytes())
editorial['workflow']['scheduled_review_frequency']='Daily, as set by the user. Published milestone snapshots remain separate from scheduler wakeups.'
editorial['recent_milestones'].insert(0,{'at':at,'text':'Daily review schedule preserved. First eight shortlisted articles passed a separate bounded synthesis/structure screening audit. A second eight-study batch identified two studies with printed product-coordinate candidates; independent audit and training admission remain pending.'})
editorial_path.write_text(json.dumps(editorial,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
skill=ROOT/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
skill.write_text(skill.read_text(encoding='utf8')+'\nThe user changed the MatterSyn review automation to daily on September22. Preserve that schedule when editing its prompt; do not restore the historical five-minute interval.\n',encoding='utf8')
print(json.dumps({'schedule_preserved':True,'active':True,'science_changed':False}))
