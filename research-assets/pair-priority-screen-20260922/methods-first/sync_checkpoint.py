"""Explicit public-safe methods-first checkpoint projection; no source files."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
PAIR=HERE.parent
ROOT=PAIR.parents[1]
sys.path.insert(0,str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT=r'C:\Program Files\Git\cmd\git.exe'
prefix=PAIR.relative_to(ROOT).as_posix()+'/'
local=['save_methods_first_policy.py','save_eta_yield_scenarios.py','eta-yield-scenarios.json',
 'methods-first/decision.json','methods-first/policy-change-receipt.json',
 'methods-first/daily-automation-update-receipt.json','methods-first/daily-schedule-verification.json',
 'methods-first/save_daily_checkpoint.py','methods-first/sync_checkpoint.py',
 'atomic-shortlist-review/batch-01/batch-summary.json','atomic-shortlist-review/batch-01/batch-summary.md',
 'atomic-shortlist-review/batch-01/author-freeze.json',
 'atomic-shortlist-review/batch-01-independent-audit/independent-audit.json',
 'atomic-shortlist-review/batch-01-independent-audit/independent-audit.md',
 'atomic-shortlist-review/batch-01-independent-audit/reusable-synthesis-screening-criteria.json',
 'atomic-shortlist-review/batch-02/batch-summary.json','atomic-shortlist-review/batch-02/batch-summary.md',
 'atomic-shortlist-review/batch-02/author-freeze.json',
 'atomic-shortlist-review/batch-02/fast-triage-proposal.json','atomic-shortlist-review/batch-02/fast-triage-proposal.md',
 'manual-recovery-proposal/doc-family-extension/candidate-batch-plan.json',
 'manual-recovery-proposal/doc-family-extension/author-freeze.json',
 'manual-recovery-audit/doc-family-extension/independent-extension-audit.json',
 'manual-recovery-proposal/word97-proposal/README.md','manual-recovery-proposal/word97-proposal/author-freeze.json']
for optional in ['methods-first/delivery-receipt.json','methods-first/record_delivery.py']:
    if(PAIR/optional).exists():local.append(optional)
files=['MEMORY.md','skills/mattersyn-paper-to-site/references/incoming-corpus.md',
 'research-assets/incoming-paper-monitor/review-control.json',
 'research-assets/incoming-paper-monitor/public-progress-editorial.json',
 'research-assets/incoming-paper-monitor/latest-publication.json',
 'recipe-atlas/dist/index.html','recipe-atlas/dist/data/review-progress.json']+[prefix+x for x in local]
assert len(files)==len(set(files))
for rel in files:
    assert(ROOT/rel).is_file(),rel
    assert policy.exclude_path(rel) is None,rel
    assert(ROOT/rel).stat().st_size<3_000_000,rel
receipts=[]
for kind,dest,name in [('project',ROOT.parent/'mattersyn-github-project','mattersyn'),
                       ('site',ROOT.parent/'mattersyn-github-public-clean/mattersyn-site','mattersyn-site')]:
    cmd=[GIT,'-c','safe.directory='+dest.as_posix(),'-C',str(dest)]
    origin=subprocess.check_output(cmd+['remote','get-url','origin'],text=True).strip()
    assert origin=='https://github.com/cuiyist/'+name+'.git'
    selected=files if kind=='project' else ['recipe-atlas/dist/index.html','recipe-atlas/dist/data/review-progress.json']
    for rel in selected:
        raw,stats=policy.project_bytes(rel,(ROOT/rel).read_bytes())
        outrel=rel if kind=='project' else rel.removeprefix('recipe-atlas/dist/')
        target=dest/outrel
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or target.read_bytes()!=raw:target.write_bytes(raw)
        receipts.append({'kind':kind,'path':outrel,'sha256':hashlib.sha256(raw).hexdigest(),'projection':stats})
    subprocess.run(cmd+['-c','core.whitespace=cr-at-eol','diff','--check'],check=True)
report={'at':datetime.now(timezone.utc).isoformat(),'files':receipts,'policy_version':policy.POLICY_VERSION,
        'raw_sources_published':False,'science_added':0,'schedule':'existing_daily_preserved'}
(HERE/'projection-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'project_files':len(files),'site_files':2,'science_added':0,'raw_sources_published':False}))
