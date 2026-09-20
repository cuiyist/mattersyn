"""Project policy and public editorial update; no source or approval changes."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent.parent
M=R/'research-assets/incoming-paper-monitor'
p=M/'public-progress-editorial.json';d=json.loads(p.read_text(encoding='utf8'))
d['estimate']['summary']='The user has set a two-month target for the existing collection, with later arrivals queued separately. This target is not yet supported by demonstrated processing capacity. Using the last measured 9,470 pending provisional scopes, completion requires about 158 closed scopes per day over 60 days, or 190 per production day if 10 days are reserved for calibration and final quality checks.'
d['estimate']['notes']=[
 'Scope closure means either an independently evidenced no-recipe exclusion or a retained contribution that passes reading, extraction, audit, website and publication checks. The recipe-bearing fraction is not yet known.',
 'At the earlier conditional planning rate of 15–20 closed scopes/day, the same backlog would take roughly 16–21 months. The short observed review window does not establish a sustained rate.',
 'A representative benchmark will measure screening, retained-paper review time, audit corrections, website generation and cost before additional processing capacity is sized. More agents alone do not guarantee a proportional speedup.',
 'The fixed-cutoff inventory is being prepared. These calculations use the last dated queue count, not a verified unique-paper total. New arrivals are outside the two-month target; changed or late SI for an included paper remains tracked as new evidence.'
]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=R/'recipe-atlas/dist/progress.mjs'
p.write_text(p.read_text(encoding='utf8').replace('Progress saved ${date(data.updated_at)}','Snapshot generated ${date(data.updated_at)}'),encoding='utf8')
skill=R/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
text=skill.read_text(encoding='utf8')
addition='''

## Fixed collection and two-month delivery target (September 20 update)

The user has set a two-month target for the existing collection and explicitly chosen to queue later arrivals separately. Use the immutable cutoff inventory under `research-assets/incoming-paper-monitor/deadline-20260920/`, once prepared, rather than allowing the deadline denominator to grow with unrelated new papers. Preserve original filenames, content hashes, stable main/SI associations and an explicit included-scope list. Late or changed SI associated with an included paper reopens its evidence review; do not silently count that paper as fully complete.

Treat the deadline as a requested target until measured capacity supports it. Use separate counts/rates for document copies, provisional scopes, audited exclusions, retained source contributions and canonical recipe records. Calibrate on a representative sample spanning recipe/non-recipe candidates, different families, short/long papers and scanned SI. Keep the same per-paper independent audit and CdSe presentation requirements; speed up through cached extraction, reusable components, parallel independent work and batched publication. Raising concurrency, paying for an API or assigning staff requires a concrete measured capacity plan and the relevant user authorization; no paid resource has been started merely by this deadline instruction. Save both the target and observed performance honestly. Preserve existing unfinished paper work.
'''
if '## Fixed collection and two-month delivery target' not in text:skill.write_text(text+addition,encoding='utf8')
print('Updated the deadline editorial, timestamp label and project workflow reference; scientific records unchanged.')
