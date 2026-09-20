"""Save verified workflow-only delivery and refresh a bounded public checkpoint."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
HERE=Path(__file__).resolve().parent;MON=HERE.parent.parent;ROOT=MON.parent.parent
sys.path.insert(0,str(ROOT/'research-assets'));import public_projection_policy as policy
v=json.loads((ROOT/'research-assets/github-public-delivery-verification.json').read_bytes())
assert v['status']=='passed' and v['site_commit']=='f1ab48f9f9fb851321806a75c87289946ba72eba'
now=datetime.now(timezone.utc).isoformat()
for p in (ROOT/'research-assets/github-publication-checkpoint.json',MON/'latest-publication.json'):
 old=HERE/(p.stem+'-before-workflow-release.json')
 if not old.exists():old.write_bytes(p.read_bytes())
 d=json.loads(p.read_bytes());d.update(published_at=v['build']['updated_at'],recorded_at=now,
   commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],anonymous_verification=v['anonymous'],
   publication_scope='Workflow, cutoff screening and parallel-review progress only. All470scientificrecords unchanged.',
   current_active_paper_claims=2,remaining_original_pilot_papers=1,new_source_ids=[])
 d['deployment']['commit']=v['site_commit'];d['deployment']['status']='built'
 d['subsequent_project_commits_may_record_this_verification']=True
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
memory=ROOT/'MEMORY.md';t=memory.read_text(encoding='utf8')
heading='## 2026-09-20 — Screen-first workflow and progress published'
entry=f'''{heading}\n\nSaved {now}. Workflow update is LIVE at https://cuiyist.github.io/mattersyn-site/progress.html . GitHub Pages commit{v['site_commit']} built2026-09-20T04:30:39Z. Public project workflow commit{v['project_commit']} contains code, memory, skills, source-filtered screening and audits. Both public repositories,31-source READMEs and13anonymous website/data/figure requests passed verification. Root viewed the actual local and public workflow dashboard; no browser errors. Science remains dataset0.23.0/470records; no new source contribution or exact structure pair was published by this update. This final checkpoint will be included in a subsequent project-only commit.\n\nCutoff selection and rolling admission passed the distinct workflow audit (78912consistency checks, six isolated tests; the broader root suite passed44tests). Heo molecular identities and14materialslots/one stock/two components passed607independent checks using the original molecular freeze plus the one-locator effective-registry correction and binding revision2. Exact evidence is in jp0219348/visuals/molecules-independent-audit/independent-audit.json. Heo canonical v1 audit found five bounded link/path/presentation/evidence-locator issues; source quantities and SI numeric transport passed. Author canonical v2 is frozen (manifest10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a); distinct delta re-audit and molecular binding v3 dependency refresh are in progress. Preserve all prior versions. Apparatus/product/reader integration and publication still remain. Evans2010 source pairing/inventory/extraction is underway independently.\n\nThe single existing5-minuteheartbeat and project/installed MatterSyn skills now use the screen-first rolling workflow and the cutoff activation wrapper; no second automation, paid API job, new infrastructure or paper download was created. New arrivals stay separate. Three nested PDFs are retained for identity/queue reconciliation. Current cutoff/activation state: deadline-20260920/active-cutoff.json and workflow-20260920T0412/.\n\n'''
if heading not in t:memory.write_text(entry+t,encoding='utf8')
dest=ROOT.parent/'mattersyn-github-project'
files=[memory,ROOT/'research-assets/github-publication-checkpoint.json',MON/'latest-publication.json',
 ROOT/'research-assets/github-public-delivery-verification.json',ROOT/'research-assets/github-public-project-sync.json',
 MON/'deadline-20260920/active-cutoff.json',MON/'ledger.json',MON/'queue-status.json',MON/'queue-status.md',MON/'queue-status.html',
 MON/'public-progress-editorial.json']
files+=list(HERE.glob('*.py'))+list(HERE.glob('*.json'))+list(HERE.glob('*.md'))
H=MON/'batches/20260919-five-paper-pilot/jp0219348'
for rel in ('canonical-proposal/audit-v1','canonical-proposal/v2','canonical-binding-proposal','visuals/molecules-independent-audit'):
 base=H/rel
 if base.is_dir():files += [p for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
copied=[];excluded=[]
for p in sorted(set(files)):
 rel=p.relative_to(ROOT).as_posix();reason=policy.exclude_path(rel)
 if reason:excluded.append({'path':rel,'reason':reason});continue
 raw=policy.transform_bytes(rel,p.read_bytes());target=dest/rel
 if target.is_file() and target.read_bytes()==raw:continue
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 copied.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest()})
report={'at':now,'copied':copied,'excluded':excluded,'scientific_dataset_changed':False,
 'source_documents_uploaded':False,'projection_policy_applied':True,'project_commit_needed':True}
(HERE/'final-checkpoint-sync.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'checkpoint_files_changed':len(copied),'excluded':len(excluded),'verified_site_commit':v['site_commit']}))
