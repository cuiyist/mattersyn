"""Record observed progress-only delivery, preserving scientific release identity."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
R=Path(__file__).resolve().parents[2];M=R.parents[1];assets=M/'research-assets'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v=read(assets/'github-public-delivery-verification.json')
assert v['status']=='passed' and v['site_commit']=='2db973487f0d2f1749763ed86fba7af2e56f482d'
now=datetime.now(timezone.utc).isoformat()
d=read(R/'latest-publication.json')
d.update(recorded_at=now,published_at=v['build']['updated_at'],commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=2,publication_scope='Progress-only update: Evans source/canonical/molecular/apparatus audits passed; Morrison complete source extraction frozen for independent audit. Scientific dataset0.24.0 unchanged.',progress_only_update=True)
d['deployment'].update(status='built',commit=v['site_commit'])
d['anonymous_verification']=v['anonymous']
for p in [R/'latest-publication.json',assets/'github-publication-checkpoint.json']:save(p,d)
save(Path(__file__).parent/'progress-publication-verification.json',v)
memory=f'''## 2026-09-20 — Parallel-review progress published and verified

Saved {now}. Public progress https://cuiyist.github.io/mattersyn-site/progress.html is LIVE at site commit {v['site_commit']}, Pages built {v['build']['updated_at']}. All24anonymous page/data/model checks, both32-citation READMEs and source-page exclusions passed. Root inspected the actual public dashboard with Evans ready for integration and Morrison in independent source review/canonical drafting. No new scientific records were published; dataset0.24.0 remains480records/98routes/44hubs. The scientific dataset publication date/commit are retained separately from this progress-only deployment.

Current public project verification bound {v['project_commit']}; a subsequent project commit saves these exact verification artifacts and final memory. Project and installed skills include the reviewed lessons on retained distillation fractions, quantity-bound captions and precursor/product structure separation. Temporary root preview servers5193/5194 are stopped; the live progress tab remains open. The existing heartbeat reads this current memory and ledger, so its older Evans-v2 narrative must not supersede passed v3/visual audits. No paid API processing or source download was started. Next root work is Evans shared-site integration with a distinct integration audit and browser/release checks; Morrison source audit and unapproved canonical drafting proceed independently.

'''
p=M/'MEMORY.md';p.write_text(memory+p.read_text(encoding='utf8'),encoding='utf8')
print(json.dumps({'site_commit':v['site_commit'],'verified_anonymous_requests':len(v['anonymous']['checks']),'science_changed':False}))
