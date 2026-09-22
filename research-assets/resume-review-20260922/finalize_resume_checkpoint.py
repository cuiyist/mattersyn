"""Bind restart memory and publication state to the verified progress release."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
delivery=read(OUT/'live-progress-delivery.json')
assert delivery['passed']
checkpoint=read(MON/'latest-publication.json')
checkpoint.update(commit_sha=delivery['site_commit'],published_at=delivery['verified_at'],recorded_at=datetime.now(timezone.utc).isoformat(),
                  publication_scope='Verified progress-only publication: fixed-cutoff corpus review resumed; no new scientific records.',
                  current_release_receipt={'path':str(OUT/'live-progress-delivery.json'),'sha256':hashlib.sha256((OUT/'live-progress-delivery.json').read_bytes()).hexdigest()},
                  anonymous_verification={'authenticated':False,'cookies_used':False,'checks':delivery['checks']})
checkpoint['deployment']={'provider':'github_pages','status':'built','commit':delivery['site_commit'],'pages_run':delivery['pages_runs'][0]['id']}
write(MON/'latest-publication.json',checkpoint)
control=read(MON/'review-control.json')
control['remaining_time_estimate']='Conditional same-depth extrapolation: about19months at continuous observed cadence or28months at16equivalent hours/day; unknown duplicate/exclusion yield and downtime prevent a validated date.'
control['eta_report']=str(OUT/'eta-proposal/eta-proposal.json')
write(MON/'review-control.json',control)
memory=ROOT/'MEMORY.md'
text=memory.read_text(encoding='utf8')
note='\n\n## 2026-09-22 — Resumed review progress published\n\nThe restarted queue and qualified ETA are live at https://cuiyist.github.io/mattersyn-site/progress.html. Progress-only site commit e6bd054661508958502bcd6a8f18058adae3caaf passed GitHub Pages run35792508592; four anonymous public artifacts match the isolated checkout. Browser verification displayed both active paper cards and the completion scenarios. Scientific counts remain675records/123routes/50hubs; no new source has yet passed all publication gates. Existing recurrence is ACTIVE, not a guarantee of uninterrupted24/7 execution.\n\nChen2018 source extraction is assigned to all_page_coverage and its separate scientific audit to backlog_eta; Saini2023 extraction is assigned to morphology_evidence and requires a distinct audit after freeze. Continue from the per-paper checkpoints and notify at meaningful milestones. Full-page renders/text in research-assets/**/private/** are explicitly excluded by public projection policy2026-09-22.1; a focused check verified all40then-present private files were excluded. Preserve source paths for audit provenance. Current projection omits both unfrozen source packages; only status, reproducible ETA evidence, memory, skills and workflow code were synchronized. No original papers or SI were uploaded.\n'
if '## 2026-09-22 — Resumed review progress published' not in text:
    memory.write_text(text+note,encoding='utf8')
print(json.dumps({'site_commit':delivery['site_commit'],'scientific_records_added':0,'control':control['status']}))
